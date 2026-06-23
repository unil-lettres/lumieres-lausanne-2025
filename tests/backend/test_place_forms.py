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

"""Unit tests for the place fiche forms (PlaceRecordForm, NoteFormPlace)."""

from __future__ import annotations

import pytest
from fiches.forms import NoteFormPlace, PlaceRecordForm
from fiches.models import PlaceCategory, PlaceRecord


@pytest.fixture
def category(db):
    return PlaceCategory.objects.create(name="Ville/Village")


@pytest.mark.django_db
def test_place_form_valid_with_name_and_category(category):
    form = PlaceRecordForm(data={"name": "Lausanne", "category": category.pk})
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_place_form_requires_name(category):
    form = PlaceRecordForm(data={"name": "", "category": category.pk})
    assert not form.is_valid()
    assert "name" in form.errors


@pytest.mark.django_db
def test_place_form_requires_category():
    form = PlaceRecordForm(data={"name": "Lausanne"})
    assert not form.is_valid()
    assert "category" in form.errors


@pytest.mark.django_db
def test_related_places_is_optional(category):
    form = PlaceRecordForm(data={"name": "Lausanne", "category": category.pk})
    assert form.is_valid(), form.errors
    assert form.fields["related_places"].required is False


@pytest.mark.django_db
def test_related_places_excludes_self(category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    other = PlaceRecord.objects.create(name="Genève", category=category)
    form = PlaceRecordForm(instance=place)
    queryset = form.fields["related_places"].queryset
    assert other in queryset
    assert place not in queryset


@pytest.mark.django_db
def test_note_form_place_has_rte_type_and_text():
    form = NoteFormPlace()
    assert form.fields["rte_type"].initial == "CKE"
    assert "text" in form.fields
