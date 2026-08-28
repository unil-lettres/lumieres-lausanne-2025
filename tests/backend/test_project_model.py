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

"""Unit tests for fiches.models.misc.project.Project."""

import pytest
from django.contrib.auth.models import AnonymousUser, User
from fiches.models.core.user_group import UserGroup
from fiches.models.misc.project import Project
from fiches.models.person.person import Person


@pytest.fixture
def owner(db):
    return User.objects.create_user(username="proj_owner", password="x")


@pytest.fixture
def member(db):
    return User.objects.create_user(username="proj_member", password="x")


@pytest.fixture
def other(db):
    return User.objects.create_user(username="proj_other", password="x")


@pytest.fixture
def proj(owner):
    return Project.objects.create(name="Lumières Project", url="lumieres-proj", owner=owner)


@pytest.fixture
def person(db):
    return Person.objects.create(name="Diderot, Denis")


# ---------------------------------------------------------------------------
# __str__
# ---------------------------------------------------------------------------


def test_str(proj):
    assert str(proj) == "Lumières Project"


# ---------------------------------------------------------------------------
# is_editable
# ---------------------------------------------------------------------------


def test_is_editable_owner(proj, owner):
    assert proj.is_editable(owner) is True


def test_is_editable_member(proj, member):
    proj.members.add(member)
    assert proj.is_editable(member) is True


def test_is_editable_other_false(proj, other):
    assert proj.is_editable(other) is False


def test_is_editable_via_usergroup_direct_user(proj, other):
    ug = UserGroup.objects.create(name="Test Group", sort=1)
    ug.users.add(other)
    proj.access_groups.add(ug)
    assert proj.is_editable(other) is True


# ---------------------------------------------------------------------------
# get_object_field / add_object / remove_object
# ---------------------------------------------------------------------------


def test_get_object_field_for_person(proj, person):
    field = proj.get_object_field(person)
    assert field is not None
    assert field.model == Person


def test_get_object_field_unknown_returns_none(proj):
    result = proj.get_object_field(object())
    assert result is None


def test_add_object_person(proj, person):
    proj.add_object(person)
    assert person in proj.persons.all()


def test_remove_object_person(proj, person):
    proj.persons.add(person)
    proj.remove_object(person)
    assert person not in proj.persons.all()


# ---------------------------------------------------------------------------
# get_transcriptions (no Transcription objects → empty queryset)
# ---------------------------------------------------------------------------


def test_get_transcriptions_anonymous_returns_queryset(proj):
    qs = proj.get_transcriptions(AnonymousUser())
    assert list(qs) == []


def test_get_transcriptions_authenticated_no_perm_returns_queryset(proj, other):
    qs = proj.get_transcriptions(other)
    assert list(qs) == []


def test_get_transcriptions_owner_returns_queryset(proj, owner):
    qs = proj.get_transcriptions(owner)
    assert list(qs) == []
