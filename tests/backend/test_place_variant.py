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

"""Unit tests for the PlaceVariant model (alternate place names)."""

from __future__ import annotations

import pytest
from django.db import IntegrityError
from fiches.models import PlaceCategory, PlaceRecord, PlaceVariant


@pytest.fixture
def lausanne(db):
    category = PlaceCategory.objects.create(name="Ville/Village")
    return PlaceRecord.objects.create(name="Lausanne", category=category)


@pytest.mark.django_db
def test_create_variant(lausanne):
    variant = PlaceVariant.objects.create(place=lausanne, name="Losanna")
    assert variant.pk is not None
    assert variant.place == lausanne
    assert str(variant) == "Losanna"


@pytest.mark.django_db
def test_multiple_variants_per_place(lausanne):
    PlaceVariant.objects.create(place=lausanne, name="Losanna")
    PlaceVariant.objects.create(place=lausanne, name="Lausanna")
    assert lausanne.variants.count() == 2


@pytest.mark.django_db
def test_variants_ordered_by_name(lausanne):
    PlaceVariant.objects.create(place=lausanne, name="Losanna")
    PlaceVariant.objects.create(place=lausanne, name="Lausanna")
    names = list(lausanne.variants.values_list("name", flat=True))
    assert names == ["Lausanna", "Losanna"]


@pytest.mark.django_db
def test_variant_unique_per_place(lausanne):
    PlaceVariant.objects.create(place=lausanne, name="Losanna")
    with pytest.raises(IntegrityError):
        PlaceVariant.objects.create(place=lausanne, name="Losanna")


@pytest.mark.django_db
def test_same_variant_allowed_for_different_places(lausanne):
    other = PlaceRecord.objects.create(name="Genève", category=lausanne.category)
    PlaceVariant.objects.create(place=lausanne, name="Lutèce")
    PlaceVariant.objects.create(place=other, name="Lutèce")
    assert PlaceVariant.objects.filter(name="Lutèce").count() == 2


@pytest.mark.django_db
def test_variants_cascade_on_place_delete(lausanne):
    PlaceVariant.objects.create(place=lausanne, name="Losanna")
    PlaceVariant.objects.create(place=lausanne, name="Lausanna")
    lausanne.delete()
    assert PlaceVariant.objects.count() == 0
