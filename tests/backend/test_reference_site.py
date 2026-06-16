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

"""Unit tests for the ReferenceSite catalog, its URL builder and its seed."""

from __future__ import annotations

import importlib

import pytest
from django.apps import apps as django_apps
from django.db import IntegrityError
from fiches.models import ReferenceSite


def _seed_module():
    # The migration module name starts with a digit, so it can only be
    # imported dynamically.
    return importlib.import_module("fiches.migrations.0008_referencesite")


@pytest.fixture
def geonames(db):
    return ReferenceSite.objects.create(name="GeoNames", code="geonames", base_url="https://www.geonames.org/{id}")


@pytest.mark.django_db
def test_create_reference_site():
    site = ReferenceSite.objects.create(name="Wikidata", code="wikidata", base_url="https://www.wikidata.org/wiki/{id}")
    assert site.pk is not None
    assert site.is_active is True


@pytest.mark.django_db
def test_str_representation(geonames):
    assert str(geonames) == "GeoNames"


@pytest.mark.django_db
def test_name_unique(geonames):
    with pytest.raises(IntegrityError):
        ReferenceSite.objects.create(name="GeoNames", code="geonames-2")


@pytest.mark.django_db
def test_code_unique(geonames):
    with pytest.raises(IntegrityError):
        ReferenceSite.objects.create(name="GeoNames Bis", code="geonames")


@pytest.mark.django_db
def test_listed_alphabetically():
    ReferenceSite.objects.create(name="Wikidata", code="wikidata")
    ReferenceSite.objects.create(name="DHS", code="dhs")
    ReferenceSite.objects.create(name="GeoNames", code="geonames")
    names = list(ReferenceSite.objects.values_list("name", flat=True))
    assert names == ["DHS", "GeoNames", "Wikidata"]


# build_url


@pytest.mark.django_db
def test_build_url_with_id_template(geonames):
    assert geonames.build_url("2659811") == "https://www.geonames.org/2659811"


@pytest.mark.django_db
def test_build_url_with_path_template():
    wikidata = ReferenceSite.objects.create(
        name="Wikidata", code="wikidata", base_url="https://www.wikidata.org/wiki/{id}"
    )
    assert wikidata.build_url("Q72") == "https://www.wikidata.org/wiki/Q72"


@pytest.mark.django_db
def test_build_url_prefix_fallback():
    dhs = ReferenceSite.objects.create(name="DHS", code="dhs", base_url="https://hls-dhs-dss.ch/fr/articles/")
    assert dhs.build_url("007379") == "https://hls-dhs-dss.ch/fr/articles/007379"


@pytest.mark.django_db
def test_build_url_empty_without_identifier(geonames):
    assert geonames.build_url("") == ""


@pytest.mark.django_db
def test_build_url_empty_without_base_url():
    site = ReferenceSite.objects.create(name="No URL", code="no-url", base_url="")
    assert site.build_url("123") == ""


# Migration 0007 seeds the catalog. pytest runs with --no-migrations, so data
# migrations are not replayed; we import the module and call the seed directly.


@pytest.mark.django_db
def test_seed_populates_and_is_idempotent():
    seed = _seed_module()
    seed.seed_reference_sites(django_apps, schema_editor=None)
    seed.seed_reference_sites(django_apps, schema_editor=None)  # second run must not duplicate
    assert ReferenceSite.objects.count() == len(seed.REFERENCE_SITES)
    assert sorted(ReferenceSite.objects.values_list("code", flat=True)) == sorted(
        site["code"] for site in seed.REFERENCE_SITES
    )


@pytest.mark.django_db
def test_seed_every_site_carries_an_id_template():
    _seed_module().seed_reference_sites(django_apps, schema_editor=None)
    for base_url in ReferenceSite.objects.values_list("base_url", flat=True):
        assert "{id}" in base_url


@pytest.mark.django_db
def test_seed_produces_the_six_referentiels():
    # Pin the canonical codes explicitly so a drift in the seed is caught here.
    _seed_module().seed_reference_sites(django_apps, schema_editor=None)
    assert sorted(ReferenceSite.objects.values_list("code", flat=True)) == sorted(
        ["geonames", "wikidata", "dhs", "viaf", "idref", "gnd"]
    )


@pytest.mark.django_db
def test_seed_reverse_removes_default_sites():
    seed = _seed_module()
    seed.seed_reference_sites(django_apps, schema_editor=None)
    seed.unseed_reference_sites(django_apps, schema_editor=None)
    assert ReferenceSite.objects.count() == 0
