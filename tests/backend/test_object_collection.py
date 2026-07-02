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

"""Unit tests for ObjectCollection (slug generation, M2M helpers) and ACModel.user_access."""

import pytest
from django.contrib.auth.models import AnonymousUser, User
from fiches.models.misc.object_collection import ObjectCollection
from fiches.models.person.person import Person


@pytest.fixture
def owner(db):
    return User.objects.create_user(username="coll_owner", password="x")


@pytest.fixture
def other(db):
    return User.objects.create_user(username="coll_other", password="x")


@pytest.fixture
def coll(owner):
    return ObjectCollection.objects.create(
        name="Ma Collection", owner=owner, access_owner=owner, access_private=False
    )


@pytest.fixture
def person(db):
    return Person.objects.create(name="Voltaire, François")


# ---------------------------------------------------------------------------
# __str__ / slug
# ---------------------------------------------------------------------------


def test_str(coll):
    assert str(coll) == "Ma Collection"


def test_save_generates_slug(coll):
    assert coll.slug == "ma-collection"


def test_save_updates_slug_only_once(coll):
    coll.slug = "custom-slug"
    coll.save()
    assert coll.slug == "custom-slug"


# ---------------------------------------------------------------------------
# get_object_field / add_object / remove_object
# ---------------------------------------------------------------------------


def test_get_object_field_returns_persons_m2m(coll, person):
    field = coll.get_object_field(person)
    assert field is not None
    assert field.model == Person


def test_get_object_field_unknown_type_returns_none(coll):
    result = coll.get_object_field(object())
    assert result is None


def test_add_object_person(coll, person):
    coll.add_object(person)
    assert person in coll.persons.all()


def test_remove_object_person(coll, person):
    coll.persons.add(person)
    coll.remove_object(person)
    assert person not in coll.persons.all()


# ---------------------------------------------------------------------------
# ACModel.user_access (exercised via ObjectCollection)
# ---------------------------------------------------------------------------


def test_user_access_unsaved_object_grants_access(owner):
    unsaved = ObjectCollection(name="New", owner=owner, access_owner=owner)
    assert unsaved.user_access(owner) is True


def test_user_access_private_grants_only_owner(owner, other):
    priv = ObjectCollection.objects.create(
        name="Privée", owner=owner, access_owner=owner, access_private=True
    )
    assert priv.user_access(owner) is True
    assert priv.user_access(other) is False


def test_user_access_anonymous_public_object(coll):
    coll.access_public = True
    assert coll.user_access(AnonymousUser()) is True


def test_user_access_anonymous_private_object(coll):
    coll.access_public = False
    assert coll.user_access(AnonymousUser()) is False


def test_user_access_public_grants_any_authenticated(coll, other):
    coll.access_public = True
    assert coll.user_access(other) is True


def test_user_access_owner_granted_without_public(coll, owner, other):
    coll.access_public = False
    coll.access_owner = owner
    assert coll.user_access(owner) is True
    assert coll.user_access(other) is False


def test_user_access_any_login_no_groups(coll, other):
    coll.access_public = False
    coll.access_owner = None
    assert coll.user_access(other, any_login=True) is True


def test_user_access_any_login_false_no_groups(coll, other):
    coll.access_public = False
    coll.access_owner = None
    assert coll.user_access(other, any_login=False) is False
