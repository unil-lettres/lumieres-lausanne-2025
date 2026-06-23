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

"""End-to-end tests for the place fiche views (display + create/edit/delete)."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from fiches.models import PlaceCategory, PlaceRecord, ReferenceSite


@pytest.fixture
def category(db):
    return PlaceCategory.objects.create(name="Ville/Village")


@pytest.fixture
def geonames(db):
    return ReferenceSite.objects.create(name="GeoNames", code="geonames", base_url="https://www.geonames.org/{id}")


@pytest.fixture
def editor(db, django_user_model):
    user = django_user_model.objects.create_user(username="editor", password="pw")
    user.user_permissions.set(
        Permission.objects.filter(codename__in=["add_placerecord", "change_placerecord", "delete_placerecord"])
    )
    return user


def _management(prefix, total=0):
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def _empty_formsets():
    data = {}
    for prefix in ("variants", "reference_links", "notes"):
        data.update(_management(prefix))
    return data


@pytest.mark.django_db
def test_display_renders(client, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    response = client.get(reverse("place-display", args=[place.pk]))
    assert response.status_code == 200
    assert b"Lausanne" in response.content


@pytest.mark.django_db
def test_create_requires_permission(client, django_user_model):
    assert client.get(reverse("place-create")).status_code == 403  # anonymous
    django_user_model.objects.create_user(username="nobody", password="pw")
    client.login(username="nobody", password="pw")
    assert client.get(reverse("place-create")).status_code == 403  # logged in, no perm


@pytest.mark.django_db
def test_create_get_renders_form(client, editor):
    client.force_login(editor)
    assert client.get(reverse("place-create")).status_code == 200


@pytest.mark.django_db
def test_create_post_sets_owner_and_redirects(client, editor, category):
    client.force_login(editor)
    data = {"name": "Lausanne", "category": category.pk, **_empty_formsets()}
    response = client.post(reverse("place-create"), data)
    place = PlaceRecord.objects.get(name="Lausanne")
    assert response.status_code == 302
    assert response.url == reverse("place-display", args=[place.pk])
    assert place.access_owner == editor


@pytest.mark.django_db
def test_create_post_saves_inlines(client, editor, category, geonames):
    client.force_login(editor)
    data = {"name": "Lausanne", "category": category.pk, **_empty_formsets()}
    data.update(_management("variants", 1))
    data["variants-0-name"] = "Losanna"
    data.update(_management("reference_links", 1))
    data["reference_links-0-reference_site"] = geonames.pk
    data["reference_links-0-identifier"] = "2659994"
    data.update(_management("notes", 1))
    data["notes-0-text"] = "<p>capitale vaudoise</p>"
    response = client.post(reverse("place-create"), data)
    assert response.status_code == 302
    place = PlaceRecord.objects.get(name="Lausanne")
    assert place.variants.get().name == "Losanna"
    assert place.reference_links.get().identifier == "2659994"
    assert place.notes.get().text == "<p>capitale vaudoise</p>"


@pytest.mark.django_db
def test_edit_updates_place(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    client.force_login(editor)
    data = {"name": "Lausanne-Ville", "category": category.pk, **_empty_formsets()}
    response = client.post(reverse("place-edit", args=[place.pk]), data)
    assert response.status_code == 302
    place.refresh_from_db()
    assert place.name == "Lausanne-Ville"


@pytest.mark.django_db
def test_delete_place(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    client.force_login(editor)
    response = client.post(reverse("place-delete", args=[place.pk]))
    assert response.status_code == 302
    assert not PlaceRecord.objects.filter(pk=place.pk).exists()


@pytest.mark.django_db
def test_workspace_shows_place_creation_for_admin(client, editor):
    client.force_login(editor)
    response = client.get(reverse("workspace-main"))
    assert response.status_code == 200
    assert "Créer une fiche lieu".encode() in response.content
    assert reverse("place-create").encode() in response.content


@pytest.mark.django_db
def test_workspace_hides_place_creation_without_perm(client, django_user_model):
    user = django_user_model.objects.create_user(username="plain", password="pw")
    client.force_login(user)
    response = client.get(reverse("workspace-main"))
    assert response.status_code == 200
    assert "Créer une fiche lieu".encode() not in response.content


@pytest.mark.django_db
def test_display_shows_create_button_for_admin(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    client.force_login(editor)
    response = client.get(reverse("place-display", args=[place.pk]))
    assert reverse("place-create").encode() in response.content


@pytest.mark.django_db
def test_display_hides_create_button_for_anonymous(client, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    response = client.get(reverse("place-display", args=[place.pk]))
    assert reverse("place-create").encode() not in response.content
