# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lumières.Lausanne is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# This copyright notice MUST APPEAR in all copies of the file.

"""Smoke tests: no parameterless route may blow up on a bare GET.

The view layer is where the bugs reported by the client actually surface
("Internal Server Error" when creating a fiche, a page that will not open),
yet it is by far the least covered part of the codebase. These tests walk the
URLconf itself, so a route added later is exercised automatically without
anyone having to remember to add a test for it.

The bar is deliberately low — *do not raise, do not 5xx* — because that is
exactly the class of regression that reaches the client. Redirects (302),
permission denials (403), not-found (404) and method-not-allowed (405) are all
acceptable outcomes here; a traceback is not.
"""

from __future__ import annotations

import re

import pytest
from django.urls import URLPattern, URLResolver, get_resolver

#: Namespaces we do not own: Django's admin and the CKEditor uploader.
EXCLUDED_PREFIXES = ("admin/", "ckeditor/")

#: Routes that cannot be exercised by a bare GET in the test environment.
#: Keep this list short and always say why — an entry here is a coverage hole.
EXPECTED_UNTESTABLE: dict[str, str] = {
    # Renders on purpose to verify the 500 template; see test_error_views.py.
    "test-debug": "deliberately raises to exercise the 500 handler",
}


def _walk(resolver, prefix: str = ""):
    for entry in resolver.url_patterns:
        if isinstance(entry, URLResolver):
            yield from _walk(entry, prefix + str(entry.pattern))
        elif isinstance(entry, URLPattern):
            yield prefix + str(entry.pattern), entry.name


def _parameterless_routes() -> list[tuple[str, str]]:
    """Return ``(url, route_name)`` for every route that takes no argument."""
    found: set[tuple[str, str]] = set()
    for pattern, name in _walk(get_resolver()):
        if "<" in pattern or "(?P" in pattern:
            continue
        if pattern.startswith(EXCLUDED_PREFIXES):
            continue
        if name in EXPECTED_UNTESTABLE:
            continue
        # ``path()`` yields a plain route, ``re_path()`` a regex: normalise both.
        url = "/" + pattern.replace("^", "").replace("$", "")
        found.add((url, name or url))
    return sorted(found)


ROUTES = _parameterless_routes()
ROUTE_IDS = [name for _, name in ROUTES]

#: A primary key that cannot exist. Detail routes must answer 404 for it —
#: an unguarded ``.get()`` or a template assuming the object is there shows up
#: here as a 500, which is what the client sees as "Internal Server Error".
MISSING_ID = "999999999"

_PATH_INT_PARAM = re.compile(r"<int:\w+>")
_RE_INT_PARAM = re.compile(r"\(\?P<\w+>\\d\+\)")
#: Anything still regex-ish after substitution means we could not build a
#: concrete URL (optional groups, slugs, multiple captures): skip it.
_LEFTOVER_REGEX = re.compile(r"[<>()\[\]?*+\\]")


def _detail_routes() -> list[tuple[str, str]]:
    """Return ``(url, route_name)`` for detail routes, pointing at a missing object."""
    found: set[tuple[str, str]] = set()
    for pattern, name in _walk(get_resolver()):
        if pattern.startswith(EXCLUDED_PREFIXES) or name in EXPECTED_UNTESTABLE:
            continue
        url = _RE_INT_PARAM.sub(MISSING_ID, _PATH_INT_PARAM.sub(MISSING_ID, pattern))
        url = url.replace("^", "").replace("$", "")
        if MISSING_ID not in url or _LEFTOVER_REGEX.search(url):
            continue
        found.add(("/" + url, name or url))
    return sorted(found)


DETAIL_ROUTES = _detail_routes()
DETAIL_ROUTE_IDS = [name for _, name in DETAIL_ROUTES]


@pytest.fixture
def superuser(db, django_user_model):
    return django_user_model.objects.create_superuser(
        username="smoke-admin",
        email="smoke-admin@example.org",
        password="pw",
    )


def test_route_discovery_is_not_empty():
    """Guard the guard: a broken walker would silently pass every smoke test."""
    assert len(ROUTES) > 40, f"only discovered {len(ROUTES)} routes — URL walking is broken"
    assert len(DETAIL_ROUTES) > 20, f"only discovered {len(DETAIL_ROUTES)} detail routes — URL walking is broken"


@pytest.mark.django_db
@pytest.mark.parametrize(("url", "name"), ROUTES, ids=ROUTE_IDS)
def test_route_does_not_error_for_anonymous(client, url, name):
    response = client.get(url)

    assert response.status_code < 500, f"{name} ({url}) returned {response.status_code}"


@pytest.mark.django_db
@pytest.mark.parametrize(("url", "name"), ROUTES, ids=ROUTE_IDS)
def test_route_does_not_error_for_superuser(client, superuser, url, name):
    client.force_login(superuser)

    response = client.get(url)

    assert response.status_code < 500, f"{name} ({url}) returned {response.status_code}"


@pytest.mark.django_db
@pytest.mark.parametrize(("url", "name"), DETAIL_ROUTES, ids=DETAIL_ROUTE_IDS)
def test_detail_route_does_not_error_for_missing_object(client, superuser, url, name):
    """A fiche that does not exist must be a 404, never a traceback."""
    client.force_login(superuser)

    response = client.get(url)

    assert response.status_code < 500, f"{name} ({url}) returned {response.status_code}"
