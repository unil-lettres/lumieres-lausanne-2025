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

"""Unit tests for the helpers in fiches.utils (DB-free and DB-backed)."""

import pytest
from django.apps import apps
from django.contrib.auth.models import AnonymousUser, User
from fiches.utils import (
    get_default_publisher_user,
    get_last_model_activity,
    log_model_activity,
    query_fiche,
    remove_object_index,
    supprime_accent,
    update_object_index,
    user_can_change_documentfile,
    user_can_delete_documentfile,
)
from fiches.models.person.person import Person


class _DocFile:
    """Minimal docfile stand-in for user_access permission helpers."""

    def __init__(self, access_owner_id=None, user_access_result=True):
        self.access_owner_id = access_owner_id
        self._user_access_result = user_access_result

    def user_access(self, user, any_login=False):
        return self._user_access_result


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Genève", "Geneve"), ("éàùôî", "eauoi"), ("Crousaz", "Crousaz"), ("", "")],
)
def test_supprime_accent(raw, expected):
    assert supprime_accent(raw) == expected


def test_object_index_stubs_return_false():
    assert update_object_index(object()) is False
    assert remove_object_index(object()) is False


def test_documentfile_permissions_deny_anonymous():
    anon = AnonymousUser()
    assert user_can_change_documentfile(anon, None) is False
    assert user_can_delete_documentfile(anon, None) is False


# ---------------------------------------------------------------------------
# user_can_change/delete_documentfile — authenticated branches
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_user_can_change_owner_match():
    user = User.objects.create_user(username="util_owner", password="x")
    assert user_can_change_documentfile(user, _DocFile(access_owner_id=user.id)) is True


@pytest.mark.django_db
def test_user_can_change_superuser_skips_owner_check():
    user = User.objects.create_user(username="util_super", password="x", is_superuser=True)
    assert user_can_change_documentfile(user, _DocFile(access_owner_id=None, user_access_result=False)) is True


@pytest.mark.django_db
def test_user_can_change_user_access_denied():
    user = User.objects.create_user(username="util_noaccess", password="x")
    assert user_can_change_documentfile(user, _DocFile(access_owner_id=None, user_access_result=False)) is False


@pytest.mark.django_db
def test_user_can_change_user_access_ok_no_perm():
    user = User.objects.create_user(username="util_noperm", password="x")
    assert user_can_change_documentfile(user, _DocFile(access_owner_id=None, user_access_result=True)) is False


@pytest.mark.django_db
def test_user_can_delete_owner_match():
    user = User.objects.create_user(username="util_del_owner", password="x")
    assert user_can_delete_documentfile(user, _DocFile(access_owner_id=user.id)) is True


@pytest.mark.django_db
def test_user_can_delete_user_access_denied():
    user = User.objects.create_user(username="util_del_noaccess", password="x")
    assert user_can_delete_documentfile(user, _DocFile(access_owner_id=None, user_access_result=False)) is False


@pytest.mark.django_db
def test_user_can_delete_superuser_skips_owner_check():
    user = User.objects.create_user(username="util_del_super", password="x", is_superuser=True)
    assert user_can_delete_documentfile(user, _DocFile(access_owner_id=None, user_access_result=False)) is True


# ---------------------------------------------------------------------------
# log_model_activity / get_last_model_activity
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_log_model_activity_creates_entry():
    ActivityLog = apps.get_model("fiches", "ActivityLog")
    person = Person.objects.create(name="Moliére, Jean-Baptiste")
    user = User.objects.create_user(username="log_user", password="x")
    before = ActivityLog.objects.count()
    log_model_activity(person, user)
    assert ActivityLog.objects.count() == before + 1


@pytest.mark.django_db
def test_get_last_model_activity_none_when_empty():
    person = Person.objects.create(name="Corneille, Pierre")
    assert get_last_model_activity(person) is None


@pytest.mark.django_db
def test_get_last_model_activity_returns_entry():
    person = Person.objects.create(name="Racine, Jean")
    user = User.objects.create_user(username="act_user", password="x")
    log_model_activity(person, user)
    act = get_last_model_activity(person)
    assert act is not None
    assert act.object_id == person.pk


# ---------------------------------------------------------------------------
# query_fiche — construct_search prefix variants
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_query_fiche_default_icontains():
    Person.objects.create(name="Buffon, Georges-Louis")
    qs = query_fiche([{"f": "name", "v": "Buffon"}], "Person")
    assert qs.filter(name__icontains="Buffon").exists()


@pytest.mark.django_db
def test_query_fiche_caret_istartswith():
    Person.objects.create(name="Helvetius, Claude")
    qs = query_fiche([{"f": "^name", "v": "Helvetius"}], "Person")
    assert qs.exists()


@pytest.mark.django_db
def test_query_fiche_at_icontains():
    Person.objects.create(name="Condillac, Étienne")
    qs = query_fiche([{"f": "@name", "v": "Condillac"}], "Person")
    assert qs.exists()


@pytest.mark.django_db
def test_query_fiche_dollar_iendswith():
    Person.objects.create(name="Turgot, Anne-Robert")
    qs = query_fiche([{"f": "$name", "v": "Anne-Robert"}], "Person")
    assert qs.exists()


@pytest.mark.django_db
def test_query_fiche_eq_iexact():
    p = Person.objects.create(name="Quesnay, François")
    qs = query_fiche([{"f": "=name", "v": "Quesnay, François"}], "Person")
    assert p in qs


@pytest.mark.django_db
def test_query_fiche_double_eq_exact():
    p = Person.objects.create(name="Mably, Gabriel")
    qs = query_fiche([{"f": "==name", "v": "Mably, Gabriel"}], "Person")
    assert p in qs


@pytest.mark.django_db
def test_query_fiche_null_prefix():
    Person.objects.create(name="Raynal, Guillaume", modern=None)
    qs = query_fiche([{"f": "_null_modern", "v": "true"}], "Person")
    assert qs.exists()


@pytest.mark.django_db
def test_query_fiche_with_existing_qs():
    p = Person.objects.create(name="Diderot, Denis")
    base_qs = Person.objects.all()
    result = query_fiche([{"f": "name", "v": "Diderot"}], "Person", qs=base_qs)
    assert p in result


# ---------------------------------------------------------------------------
# get_default_publisher_user
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_default_publisher_user_returns_none_when_absent():
    assert get_default_publisher_user() is None


@pytest.mark.django_db
def test_get_default_publisher_user_finds_blovis():
    blovis = User.objects.create_user(username="blovis", password="x")
    assert get_default_publisher_user() == blovis


@pytest.mark.django_db
def test_get_default_publisher_user_fallback_to_bea():
    bea = User.objects.create_user(username="beaviewers", first_name="Beatrice", password="x")
    assert get_default_publisher_user() == bea
