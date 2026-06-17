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

"""Unit tests for the PlaceRecord model (fiche lieu)."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from fiches.models import PlaceCategory, PlaceRecord


@pytest.fixture
def category_city(db):
    return PlaceCategory.objects.create(name="Ville/Village")


@pytest.fixture
def category_country(db):
    return PlaceCategory.objects.create(name="Pays")


@pytest.fixture
def lausanne(category_city):
    return PlaceRecord.objects.create(name="Lausanne", category=category_city)


# Data entry / read paths


@pytest.mark.django_db
def test_create_place_record(category_city):
    place = PlaceRecord.objects.create(name="Lausanne", category=category_city)
    assert place.pk is not None
    assert place.name == "Lausanne"
    assert place.category == category_city
    assert place.created_at is not None
    assert place.updated_at is not None


@pytest.mark.django_db
def test_str_representation(lausanne):
    assert str(lausanne) == "Lausanne (Ville/Village)"


@pytest.mark.django_db
def test_default_ordering_by_name(category_city):
    PlaceRecord.objects.create(name="Zurich", category=category_city)
    PlaceRecord.objects.create(name="Aarau", category=category_city)
    PlaceRecord.objects.create(name="Bern", category=category_city)
    names = list(PlaceRecord.objects.values_list("name", flat=True))
    assert names == ["Aarau", "Bern", "Zurich"]


@pytest.mark.django_db
def test_filter_by_category(category_city, category_country):
    PlaceRecord.objects.create(name="Lausanne", category=category_city)
    PlaceRecord.objects.create(name="Suisse", category=category_country)
    PlaceRecord.objects.create(name="France", category=category_country)
    assert PlaceRecord.objects.filter(category=category_country).count() == 2
    assert PlaceRecord.objects.filter(category=category_city).count() == 1


# Constraints


@pytest.mark.django_db
def test_name_required_at_validation(category_city):
    with pytest.raises(ValidationError):
        PlaceRecord(name="", category=category_city).full_clean()


@pytest.mark.django_db
def test_category_required_at_validation():
    with pytest.raises(ValidationError):
        PlaceRecord(name="Orphan").full_clean()


@pytest.mark.django_db
def test_category_required_at_db_level():
    with pytest.raises(IntegrityError):
        PlaceRecord.objects.create(name="Orphan")


@pytest.mark.django_db
def test_name_unique_per_category(category_city):
    PlaceRecord.objects.create(name="Lausanne", category=category_city)
    with pytest.raises(IntegrityError):
        PlaceRecord.objects.create(name="Lausanne", category=category_city)


@pytest.mark.django_db
def test_same_name_allowed_in_different_categories(category_city, category_country):
    PlaceRecord.objects.create(name="Genève", category=category_city)
    PlaceRecord.objects.create(name="Genève", category=category_country)
    assert PlaceRecord.objects.filter(name="Genève").count() == 2


@pytest.mark.django_db
def test_category_protected_while_in_use(category_city, lausanne):
    with pytest.raises(ProtectedError):
        category_city.delete()


@pytest.mark.django_db
def test_related_places_symmetric(category_city, category_country):
    paris = PlaceRecord.objects.create(name="Paris", category=category_city)
    france = PlaceRecord.objects.create(name="France", category=category_country)
    paris.related_places.add(france)
    assert france in paris.related_places.all()
    assert paris in france.related_places.all()
