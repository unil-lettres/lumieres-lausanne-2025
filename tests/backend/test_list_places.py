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

"""Tests for the "Liste des lieux" advanced-search tab (§5)."""

import pytest
from django.urls import reverse
from fiches.models import PlaceCategory, PlaceRecord


@pytest.fixture
def places(db):
    # Distinctive names that do not appear in the page chrome (the site brand
    # "Lumières.Lausanne" would otherwise foil a whole-page index() check).
    category = PlaceCategory.objects.create(name="Ville/Village")
    return [
        PlaceRecord.objects.create(name="Aarberg", category=category),
        PlaceRecord.objects.create(name="Grandson", category=category),
        PlaceRecord.objects.create(name="Zofingue", category=category),
    ]


@pytest.mark.django_db
def test_list_places_lists_all_alphabetically(client, places):
    response = client.get(reverse("list-place"))
    assert response.status_code == 200
    body = response.content.decode()
    assert body.index("Aarberg") < body.index("Grandson") < body.index("Zofingue")
    # Each place links to its public fiche.
    assert reverse("place-display", args=[places[1].id]) in body


@pytest.mark.django_db
def test_first_letter_filter(client, places):
    body = client.get(reverse("list-place"), {"q": "G"}).content.decode()
    assert "Grandson" in body
    assert "Aarberg" not in body
    assert "Zofingue" not in body


@pytest.mark.django_db
def test_tab_links_to_places_list_from_persons_list(client, db):
    body = client.get(reverse("list-person")).content.decode()
    assert reverse("list-place") in body
    assert "Liste des lieux" in body
