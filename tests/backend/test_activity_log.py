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

"""Unit tests for ActivityLog model and ObjectActivities manager (40% → coverage+)."""

import types

import pytest
from django.apps import apps
from django.contrib.auth.models import User
from fiches.models.person.person import Person


@pytest.fixture
def user(db):
    return User.objects.create_user(username="actlog_u", password="x")


@pytest.fixture
def person(db):
    return Person.objects.create(name="Montesquieu, Charles")


@pytest.fixture
def activity(user, person):
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    return ActivityLog.objects.create(model_name="Person", object_id=person.pk, user=user)


# ---------------------------------------------------------------------------
# __str__ (lines 97-98)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_str_contains_user_name(activity, user):
    assert user.username in str(activity)


@pytest.mark.django_db
def test_str_contains_date(activity):
    assert "T" in str(activity) or "-" in str(activity)


# ---------------------------------------------------------------------------
# ObjectActivities.activities() (lines 35-42)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_activities_no_object_kwarg_returns_all(activity):
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    assert activity in ActivityLog.objects.activities()


@pytest.mark.django_db
def test_activities_with_object_filters_by_model_and_pk(activity, person):
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    qs = ActivityLog.objects.activities(object=person)
    assert activity in qs


@pytest.mark.django_db
def test_activities_object_without_id_returns_empty_qs(activity):
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    bad = types.SimpleNamespace()  # no .id → AttributeError → except → qs.none()
    assert list(ActivityLog.objects.activities(object=bad)) == []


# ---------------------------------------------------------------------------
# object_info property (lines 56-63)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_object_info_valid_returns_dict(activity, person):
    info = activity.object_info
    assert info is not None
    assert info["object"] == person
    assert "model_name" in info
    assert "object_name" in info


@pytest.mark.django_db
def test_object_info_bad_model_name_returns_none(user):
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    act = ActivityLog.objects.create(model_name="NoSuchModel", object_id=1, user=user)
    assert act.object_info is None


@pytest.mark.django_db
def test_object_info_missing_pk_returns_none(user):
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    act = ActivityLog.objects.create(model_name="Person", object_id=999999, user=user)
    assert act.object_info is None


# ---------------------------------------------------------------------------
# get_object() (lines 66-70)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_object_returns_instance(activity, person):
    assert activity.get_object() == person


@pytest.mark.django_db
def test_get_object_missing_pk_returns_none(user):
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    act = ActivityLog.objects.create(model_name="Person", object_id=999999, user=user)
    assert act.get_object() is None


@pytest.mark.django_db
def test_get_object_bad_model_returns_none(user):
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    act = ActivityLog.objects.create(model_name="NoSuchModel", object_id=1, user=user)
    assert act.get_object() is None
