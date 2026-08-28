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

"""Unit tests for the NotePlace model (access-controlled place notes)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from fiches.models import NotePlace, PlaceCategory, PlaceRecord


@pytest.fixture
def lausanne(db):
    category = PlaceCategory.objects.create(name="Ville/Village")
    return PlaceRecord.objects.create(name="Lausanne", category=category)


@pytest.mark.django_db
def test_create_note_rich_text(lausanne):
    note = NotePlace.objects.create(owner=lausanne, text="<p>Capitale vaudoise</p>")
    assert note.pk is not None
    assert note.owner == lausanne
    assert note.rte_type == "CKE"
    assert str(note) == "Capitale vaudoise"


@pytest.mark.django_db
def test_notes_accessible_via_place(lausanne):
    NotePlace.objects.create(owner=lausanne, text="<p>note</p>")
    assert lausanne.notes.get().text == "<p>note</p>"


@pytest.mark.django_db
def test_multiple_notes_per_place(lausanne):
    NotePlace.objects.create(owner=lausanne, text="<p>first</p>")
    NotePlace.objects.create(owner=lausanne, text="<p>second</p>")
    assert lausanne.notes.count() == 2


@pytest.mark.django_db
def test_note_not_public_by_default(lausanne):
    note = NotePlace.objects.create(owner=lausanne, text="<p>private</p>")
    assert note.access_public is False


@pytest.mark.django_db
def test_note_cascades_on_place_delete(lausanne):
    NotePlace.objects.create(owner=lausanne, text="<p>note</p>")
    lausanne.delete()
    assert NotePlace.objects.count() == 0


# -- read view: which notes a visitor actually sees ---------------------------


@pytest.mark.django_db
def test_note_for_logged_in_users_is_visible_in_read_mode(client, lausanne, django_user_model):
    """Client report 2026-07-15: a note set to « Utilisateurs » never showed.

    That state is "not public, no groups", which ACModel.user_access only grants
    when any_login=True — as the shared access_lazy filter does. The place view
    called user_access() bare, so the note was filtered out for everyone.
    """
    NotePlace.objects.create(owner=lausanne, text="<p>note utilisateurs</p>")
    reader = django_user_model.objects.create_user(username="reader", password="pw")
    client.force_login(reader)

    body = client.get(reverse("place-display", args=[lausanne.pk])).content.decode()

    assert "note utilisateurs" in body


@pytest.mark.django_db
def test_note_for_logged_in_users_stays_hidden_from_anonymous(client, lausanne):
    """The same note must not leak to visitors without a login."""
    NotePlace.objects.create(owner=lausanne, text="<p>note utilisateurs</p>")

    body = client.get(reverse("place-display", args=[lausanne.pk])).content.decode()

    assert "note utilisateurs" not in body


@pytest.mark.django_db
def test_public_note_is_visible_to_anonymous(client, lausanne):
    NotePlace.objects.create(owner=lausanne, text="<p>note publique</p>", access_public=True)

    body = client.get(reverse("place-display", args=[lausanne.pk])).content.decode()

    assert "note publique" in body


@pytest.mark.django_db
def test_read_view_shows_each_note_access_level(client, lausanne, django_user_model):
    """The access badge lets an editor check a note's visibility at a glance."""
    NotePlace.objects.create(owner=lausanne, text="<p>note utilisateurs</p>")
    reader = django_user_model.objects.create_user(username="reader", password="pw")
    client.force_login(reader)

    body = client.get(reverse("place-display", args=[lausanne.pk])).content.decode()

    assert "access_status-user" in body
