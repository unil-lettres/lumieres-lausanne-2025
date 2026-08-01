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

"""Tests for the transcription tagging inline-create endpoints (Directeurs only)."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from fiches.models import PlaceCategory, PlaceRecord
from fiches.models.person.person import Person


@pytest.fixture
def category(db):
    return PlaceCategory.objects.create(name="Ville/Village")


@pytest.fixture
def director(db, django_user_model):
    user = django_user_model.objects.create_user(username="director", password="pw")
    user.user_permissions.set(
        Permission.objects.filter(
            codename__in=["add_person", "add_person_inline", "add_placerecord", "add_placerecord_inline"],
        )
    )
    return user


@pytest.fixture
def plain_user(db, django_user_model):
    return django_user_model.objects.create_user(username="plain", password="pw")


# -- categories ---------------------------------------------------------------


@pytest.mark.django_db
def test_place_categories_lists_categories(client, category):
    response = client.get(reverse("tagging-place-categories"))
    assert response.status_code == 200
    names = [c["name"] for c in response.json()["categories"]]
    assert "Ville/Village" in names


# -- place creation -----------------------------------------------------------


@pytest.mark.django_db
def test_create_place_refuses_the_plain_add_permission(client, category, django_user_model):
    """Client request 2026-07-15: inline creation while tagging is director-only.

    Every status may create a place fiche the normal way (add_placerecord), but
    that must not open the tagging toolbar shortcut, which needs the narrower
    add_placerecord_inline.
    """
    user = django_user_model.objects.create_user(username="editor-only", password="pw")
    user.user_permissions.set(Permission.objects.filter(codename="add_placerecord"))
    client.force_login(user)

    response = client.post(reverse("tagging-place-create"), {"name": "Yverdon", "category": category.pk})

    assert response.status_code == 403
    assert not PlaceRecord.objects.filter(name="Yverdon").exists()


@pytest.mark.django_db
def test_create_place_requires_permission(client, plain_user, category):
    assert (
        client.post(reverse("tagging-place-create"), {"name": "Lausanne", "category": category.pk}).status_code == 403
    )
    client.login(username="plain", password="pw")
    response = client.post(reverse("tagging-place-create"), {"name": "Lausanne", "category": category.pk})
    assert response.status_code == 403
    assert not PlaceRecord.objects.filter(name="Lausanne").exists()


@pytest.mark.django_db
def test_create_place_succeeds_for_director(client, director, category):
    client.login(username="director", password="pw")
    response = client.post(reverse("tagging-place-create"), {"name": "Lausanne", "category": category.pk})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] and body["created"]
    place = PlaceRecord.objects.get(name="Lausanne", category=category)
    assert body["id"] == place.pk
    assert body["label"] == "Lausanne (Ville/Village)"
    assert place.access_owner == director


@pytest.mark.django_db
def test_create_place_reuses_existing(client, director, category):
    client.login(username="director", password="pw")
    first = client.post(reverse("tagging-place-create"), {"name": "Berne", "category": category.pk}).json()
    second = client.post(reverse("tagging-place-create"), {"name": "Berne", "category": category.pk}).json()
    assert first["id"] == second["id"]
    assert second["created"] is False
    assert PlaceRecord.objects.filter(name="Berne", category=category).count() == 1


@pytest.mark.django_db
def test_create_place_requires_name_and_category(client, director, category):
    client.login(username="director", password="pw")
    assert client.post(reverse("tagging-place-create"), {"name": "", "category": category.pk}).status_code == 400
    assert client.post(reverse("tagging-place-create"), {"name": "Nyon"}).status_code == 400


# -- person creation ----------------------------------------------------------


@pytest.mark.django_db
def test_create_person_refuses_the_plain_add_permission(client, django_user_model):
    """Ordinary Personne creation must not open the tagging shortcut."""
    user = django_user_model.objects.create_user(username="person-editor-only", password="pw")
    user.user_permissions.set(Permission.objects.filter(codename="add_person"))
    client.force_login(user)

    response = client.post(reverse("tagging-person-create"), {"name": "Barbeyrac, Jean"})

    assert response.status_code == 403
    assert not Person.objects.filter(name="Barbeyrac, Jean").exists()


@pytest.mark.django_db
def test_create_person_requires_permission(client, plain_user):
    assert client.post(reverse("tagging-person-create"), {"name": "Barbeyrac, Jean"}).status_code == 403
    client.login(username="plain", password="pw")
    response = client.post(reverse("tagging-person-create"), {"name": "Barbeyrac, Jean"})
    assert response.status_code == 403
    assert not Person.objects.filter(name="Barbeyrac, Jean").exists()


@pytest.mark.django_db
def test_create_person_succeeds_for_director(client, director):
    client.login(username="director", password="pw")
    response = client.post(reverse("tagging-person-create"), {"name": "Barbeyrac, Jean"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] and body["created"]
    person = Person.objects.get(name="Barbeyrac, Jean")
    assert body["id"] == person.pk
    assert body["label"] == "Barbeyrac, Jean"


@pytest.mark.django_db
def test_person_tagging_search_only_returns_historical_people(client):
    historical = Person.objects.create(name="Barbeyrac, Jean", modern=False)
    Person.objects.create(name="Barbeyrac, Jean", modern=True)
    Person.objects.create(name="Barbeyrac, Jacques", modern=False)

    response = client.get(reverse("tagging-person-search"), {"q": "Jean Barbeyrac"})

    assert response.status_code == 200
    assert response.content.decode().splitlines() == [historical.format_for_ajax_search()]


@pytest.mark.django_db
def test_person_tagging_search_disambiguates_identical_historical_labels(client):
    first = Person.objects.create(name="Martin, Jean", modern=False)
    second = Person.objects.create(name="Martin, Jean", modern=False)

    response = client.get(reverse("tagging-person-search"), {"q": "Martin Jean"})

    assert response.content.decode().splitlines() == [
        f"Martin, Jean — fiche #{first.pk}|{first.pk}",
        f"Martin, Jean — fiche #{second.pk}|{second.pk}",
    ]


@pytest.mark.django_db
def test_create_person_does_not_reuse_modern_author(client, director):
    modern = Person.objects.create(name="Barbeyrac, Jean", modern=True)
    client.force_login(director)

    response = client.post(reverse("tagging-person-create"), {"name": "Barbeyrac, Jean"})

    assert response.status_code == 200
    assert response.json()["created"] is True
    assert response.json()["id"] != modern.pk
    assert Person.objects.get(pk=response.json()["id"]).modern is False


@pytest.mark.django_db
def test_create_person_refuses_to_choose_between_historical_homonyms(client, director):
    first = Person.objects.create(name="Martin, Jean", modern=False)
    second = Person.objects.create(name="Martin, Jean", modern=False)
    client.force_login(director)

    response = client.post(reverse("tagging-person-create"), {"name": "Martin, Jean"})

    assert response.status_code == 409
    assert response.json()["error"] == "ambiguous_name"
    assert {candidate["id"] for candidate in response.json()["candidates"]} == {first.pk, second.pk}
    assert Person.objects.filter(name="Martin, Jean", modern=False).count() == 2


@pytest.mark.django_db
def test_create_person_requires_name(client, director):
    client.login(username="director", password="pw")
    assert client.post(reverse("tagging-person-create"), {"name": ""}).status_code == 400


# -- bio display for a person without a biography yet --------------------------


@pytest.mark.django_db
def test_bio_display_without_biography_shows_dedicated_page(client):
    # A person created from the tagging window has no biography yet: the fiche
    # link must show a consultable explanatory page (HTTP 200), not a 404.
    person = Person.objects.create(name="Barbeyrac, Jean", modern=False)
    response = client.get(reverse("biography-display", args=[person.id]))
    assert response.status_code == 200
    assert "n'a pas encore été rédigée" in response.content.decode()
    assert person.name in response.content.decode()


@pytest.mark.django_db
def test_bio_display_unknown_person_is_plain_404(client):
    response = client.get(reverse("biography-display", args=[999999]))
    assert response.status_code == 404
    assert "n'a pas encore été rédigée" not in response.content.decode()
