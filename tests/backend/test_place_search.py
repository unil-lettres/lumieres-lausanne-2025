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

"""Unit tests for the place search index and the variant re-index signals."""

from __future__ import annotations

import pytest
from django.apps import apps
from fiches.models import PlaceCategory, PlaceRecord, PlaceVariant
from fiches.search_indexes import PlaceRecordIndex


@pytest.fixture
def lausanne(db):
    category = PlaceCategory.objects.create(name="Ville/Village")
    return PlaceRecord.objects.create(name="Lausanne", category=category)


@pytest.mark.django_db
def test_index_text_includes_name_category_and_variants(lausanne):
    PlaceVariant.objects.create(place=lausanne, name="Losanna")
    PlaceVariant.objects.create(place=lausanne, name="Lausanna")
    text = PlaceRecordIndex().prepare(lausanne)["text"]
    assert "Lausanne" in text
    assert "Ville/Village" in text
    assert "Losanna" in text
    assert "Lausanna" in text


@pytest.mark.django_db
def test_index_model_queryset_and_modelsort(lausanne):
    index = PlaceRecordIndex()
    assert index.get_model() is PlaceRecord
    assert lausanne in index.index_queryset()
    assert index.prepare_modelSort(lausanne) == "D00"


@pytest.mark.django_db
def test_variant_create_reindexes_parent_place(lausanne, monkeypatch):
    calls = []
    monkeypatch.setattr(
        apps.get_app_config("haystack").signal_processor,
        "handle_save",
        lambda sender, instance, **kw: calls.append(instance),
    )
    PlaceVariant.objects.create(place=lausanne, name="Losanna")
    assert calls == [lausanne]


@pytest.mark.django_db
def test_variant_delete_reindexes_parent_place(lausanne, monkeypatch):
    variant = PlaceVariant.objects.create(place=lausanne, name="Losanna")
    calls = []
    monkeypatch.setattr(
        apps.get_app_config("haystack").signal_processor,
        "handle_save",
        lambda sender, instance, **kw: calls.append(instance),
    )
    variant.delete()
    assert calls == [lausanne]


@pytest.mark.django_db
def test_place_delete_cascade_is_safe(lausanne, monkeypatch):
    PlaceVariant.objects.create(place=lausanne, name="Losanna")
    monkeypatch.setattr(
        apps.get_app_config("haystack").signal_processor,
        "handle_save",
        lambda sender, instance, **kw: None,
    )
    lausanne.delete()  # cascade deletes variants → receiver must not raise
    assert PlaceRecord.objects.count() == 0
    assert PlaceVariant.objects.count() == 0
