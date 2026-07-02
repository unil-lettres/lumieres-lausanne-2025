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

"""Admin tests for the PlaceRecord fiche (issue #118).

The place fiches must be browsable, searchable and editable from the
``fiches_admin`` site without knowing their id.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from fiches.admin import fiches_admin
from fiches.models import PlaceCategory, PlaceRecord


@pytest.fixture
def category(db):
    return PlaceCategory.objects.create(name="Ville/Village")


@pytest.fixture
def lausanne(category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    place.variants.create(name="Losanna")
    return place


@pytest.fixture
def admin_user(db, django_user_model):
    return django_user_model.objects.create_superuser(username="boss", password="pw", email="boss@example.org")


def test_place_record_is_registered_in_fiches_admin():
    # The lookup table was already there; the fiche itself must be too (#118).
    registered = {model._meta.model_name for model in fiches_admin._registry}
    assert "placerecord" in registered
    assert "placecategory" in registered


@pytest.mark.django_db
def test_changelist_lists_existing_places(client, admin_user, lausanne):
    client.force_login(admin_user)
    response = client.get(reverse("fiches_admin:fiches_placerecord_changelist"))
    assert response.status_code == 200
    assert "Lausanne" in response.content.decode()


@pytest.mark.django_db
def test_changelist_search_finds_place_by_name(client, admin_user, lausanne):
    PlaceRecord.objects.create(name="Genève", category=lausanne.category)
    client.force_login(admin_user)
    response = client.get(reverse("fiches_admin:fiches_placerecord_changelist"), {"q": "Lausanne"})
    assert response.status_code == 200
    body = response.content.decode()
    assert "Lausanne" in body
    assert "Genève" not in body


@pytest.mark.django_db
def test_changelist_search_finds_place_by_variant(client, admin_user, lausanne):
    # A reviewer searching an alternate spelling must still reach the fiche.
    client.force_login(admin_user)
    response = client.get(reverse("fiches_admin:fiches_placerecord_changelist"), {"q": "Losanna"})
    assert response.status_code == 200
    assert "Lausanne" in response.content.decode()


@pytest.mark.django_db
def test_change_form_opens_for_existing_place(client, admin_user, lausanne):
    client.force_login(admin_user)
    response = client.get(reverse("fiches_admin:fiches_placerecord_change", args=[lausanne.pk]))
    assert response.status_code == 200
