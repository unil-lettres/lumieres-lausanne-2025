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

"""Unit tests for the PlaceReferenceSite pivot (place ↔ référentiel)."""

from __future__ import annotations

import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError
from fiches.models import PlaceCategory, PlaceRecord, PlaceReferenceSite, ReferenceSite


@pytest.fixture
def lausanne(db):
    category = PlaceCategory.objects.create(name="Ville/Village")
    return PlaceRecord.objects.create(name="Lausanne", category=category)


@pytest.fixture
def geonames(db):
    return ReferenceSite.objects.create(
        name="GeoNames",
        code="geonames",
        base_url="https://www.geonames.org/{id}",
    )


@pytest.mark.django_db
def test_url_is_derived_from_reference_site(lausanne, geonames):
    link = PlaceReferenceSite.objects.create(place=lausanne, reference_site=geonames, identifier="2659994")
    assert link.url == "https://www.geonames.org/2659994"
    assert str(link) == "GeoNames: 2659994"


@pytest.mark.django_db
def test_several_reference_sites_allowed(lausanne, geonames):
    wikidata = ReferenceSite.objects.create(
        name="Wikidata", code="wikidata", base_url="https://www.wikidata.org/wiki/{id}"
    )
    PlaceReferenceSite.objects.create(place=lausanne, reference_site=geonames, identifier="2659994")
    PlaceReferenceSite.objects.create(place=lausanne, reference_site=wikidata, identifier="Q807")
    assert lausanne.reference_links.count() == 2


@pytest.mark.django_db
def test_one_link_per_reference_site(lausanne, geonames):
    PlaceReferenceSite.objects.create(place=lausanne, reference_site=geonames, identifier="2659994")
    with pytest.raises(IntegrityError):
        PlaceReferenceSite.objects.create(place=lausanne, reference_site=geonames, identifier="111")


@pytest.mark.django_db
def test_links_cascade_on_place_delete(lausanne, geonames):
    PlaceReferenceSite.objects.create(place=lausanne, reference_site=geonames, identifier="2659994")
    lausanne.delete()
    assert PlaceReferenceSite.objects.count() == 0


@pytest.mark.django_db
def test_reference_site_protected_while_linked(lausanne, geonames):
    PlaceReferenceSite.objects.create(place=lausanne, reference_site=geonames, identifier="2659994")
    with pytest.raises(ProtectedError):
        geonames.delete()
