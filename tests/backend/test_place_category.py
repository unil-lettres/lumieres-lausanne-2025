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

"""Unit tests for the place-category lookup (PlaceCategory) and its seed."""

from __future__ import annotations

import importlib

import pytest
from django.apps import apps as django_apps
from django.db import IntegrityError
from fiches.models import PlaceCategory


def _seed_module():
    # The migration module name starts with a digit, so it can only be
    # imported dynamically.
    return importlib.import_module("fiches.migrations.0007_placecategory")


@pytest.mark.django_db
def test_create_category():
    category = PlaceCategory.objects.create(name="Ville/Village")
    assert category.pk is not None
    assert category.name == "Ville/Village"


@pytest.mark.django_db
def test_str_representation():
    assert str(PlaceCategory.objects.create(name="Pays")) == "Pays"


@pytest.mark.django_db
def test_name_unique():
    PlaceCategory.objects.create(name="Pays")
    with pytest.raises(IntegrityError):
        PlaceCategory.objects.create(name="Pays")


@pytest.mark.django_db
def test_listed_alphabetically():
    PlaceCategory.objects.create(name="Région")
    PlaceCategory.objects.create(name="Pays")
    PlaceCategory.objects.create(name="Ville/Village")
    names = list(PlaceCategory.objects.values_list("name", flat=True))
    assert names == ["Pays", "Région", "Ville/Village"]


# Migration 0006 seeds the lookup. pytest runs with --no-migrations, so data
# migrations are not replayed; we import the module and call the seed directly.


@pytest.mark.django_db
def test_seed_populates_and_is_idempotent():
    seed = _seed_module()
    seed.seed_categories(django_apps, schema_editor=None)
    seed.seed_categories(django_apps, schema_editor=None)  # second run must not duplicate
    assert PlaceCategory.objects.count() == len(seed.INITIAL_CATEGORIES)
    assert sorted(PlaceCategory.objects.values_list("name", flat=True)) == sorted(seed.INITIAL_CATEGORIES)


@pytest.mark.django_db
def test_seed_produces_the_seven_default_categories():
    # Pin the canonical list explicitly so a drift in the seed is caught here,
    # not silently against INITIAL_CATEGORIES itself.
    _seed_module().seed_categories(django_apps, schema_editor=None)
    assert sorted(PlaceCategory.objects.values_list("name", flat=True)) == sorted(
        [
            "Pays",
            "Canton/Département",
            "Région",
            "Ville/Village",
            "Domaine",
            "Maison de campagne",
            "Quartier",
        ]
    )


@pytest.mark.django_db
def test_seed_reverse_removes_default_categories():
    seed = _seed_module()
    seed.seed_categories(django_apps, schema_editor=None)
    seed.unseed_categories(django_apps, schema_editor=None)
    assert PlaceCategory.objects.count() == 0
