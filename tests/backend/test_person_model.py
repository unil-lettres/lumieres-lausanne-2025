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

"""Unit tests for fiches.models.person.Person — managers, name helpers, biography lookups."""

import datetime

import pytest
from fiches.models.person.biography import Biography
from fiches.models.person.person import Person


@pytest.fixture
def person(db):
    return Person.objects.create(name="Rousseau, Jean-Jacques")


@pytest.fixture
def bio(person):
    return Biography.objects.create(person=person, version=0, valid=False)


@pytest.fixture
def valid_bio(person):
    return Biography.objects.create(person=person, version=1, valid=True)


# ---------------------------------------------------------------------------
# Managers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modern_people_manager_filters(db):
    Person.objects.create(name="Modern One", modern=True)
    Person.objects.create(name="Past One", modern=False)
    names = list(Person.modern_people.values_list("name", flat=True))
    assert "Modern One" in names
    assert "Past One" not in names


@pytest.mark.django_db
def test_past_people_manager_filters(db):
    Person.objects.create(name="Past Two", modern=False)
    Person.objects.create(name="Modern Two", modern=True)
    names = list(Person.past_people.values_list("name", flat=True))
    assert "Past Two" in names
    assert "Modern Two" not in names


# ---------------------------------------------------------------------------
# Name helpers
# ---------------------------------------------------------------------------


def test_get_name_parts_first(person):
    assert person.get_first_name() == "Rousseau"


def test_get_name_parts_last(person):
    assert person.get_last_name() == "Jean-Jacques"


def test_get_name_parts_no_comma():
    p = Person(name="Mononym")
    assert p.get_first_name() == "Mononym"
    assert p.get_last_name() == ""


def test_get_name_parts_invalid_raises():
    p = Person(name="Doe, John")
    with pytest.raises(ValueError):
        p._get_name_parts("invalid")


# ---------------------------------------------------------------------------
# has_biography / get_absolute_url
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_has_biography_false(person):
    assert person.has_biography() is False


@pytest.mark.django_db
def test_has_biography_true(person, bio):
    assert person.has_biography() is True


@pytest.mark.django_db
def test_get_absolute_url_contains_pk(person):
    url = person.get_absolute_url()
    assert str(person.pk) in url


# ---------------------------------------------------------------------------
# get_biography
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_biography_returns_version_0(person, bio):
    assert person.get_biography() == bio


@pytest.mark.django_db
def test_get_biography_version_none_defaults_to_0(person, bio):
    assert person.get_biography(version=None) == bio


@pytest.mark.django_db
def test_get_biography_invalid_string_defaults_to_0(person, bio):
    assert person.get_biography(version="abc") == bio


@pytest.mark.django_db
def test_get_biography_fallback_to_latest_when_version_missing(person):
    b1 = Biography.objects.create(person=person, version=2, valid=False)
    b2 = Biography.objects.create(person=person, version=3, valid=False)
    result = person.get_biography(version=0)
    assert result == b2 or result == b1


@pytest.mark.django_db
def test_get_biography_no_bio_returns_none(person):
    assert person.get_biography() is None


# ---------------------------------------------------------------------------
# get_valid_biography
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_valid_biography_returns_last_valid(person, valid_bio):
    assert person.get_valid_biography() == valid_bio


@pytest.mark.django_db
def test_get_valid_biography_no_valid_returns_none(person, bio):
    assert person.get_valid_biography() is None


# ---------------------------------------------------------------------------
# renum_bio
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_renum_bio_assigns_correct_versions(person):
    b1 = Biography.objects.create(person=person, version=99, valid=False)
    b2 = Biography.objects.create(person=person, version=99, valid=False)
    person.renum_bio()
    b1.refresh_from_db()
    b2.refresh_from_db()
    # oldest id gets highest version (nb_bio - 1 = 1), latest id gets version 0
    assert b1.version == 1
    assert b2.version == 0


@pytest.mark.django_db
def test_renum_bio_dry_run_does_not_save(person):
    b = Biography.objects.create(person=person, version=99, valid=False)
    person.renum_bio(dry_run=True)
    b.refresh_from_db()
    assert b.version == 99


# ---------------------------------------------------------------------------
# format_for_ajax_search
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_format_for_ajax_search_no_biography(person):
    out = person.format_for_ajax_search()
    assert out == f"{person.name}|{person.pk}"


@pytest.mark.django_db
def test_format_for_ajax_search_with_both_dates(person):
    Biography.objects.create(
        person=person,
        version=0,
        valid=False,
        birth_date=datetime.date(1712, 6, 28),
        death_date=datetime.date(1778, 7, 2),
    )
    out = person.format_for_ajax_search()
    assert "1712" in out
    assert "1778" in out
    assert f"|{person.pk}" in out


@pytest.mark.django_db
def test_format_for_ajax_search_birth_only(person):
    Biography.objects.create(person=person, version=0, valid=False, birth_date=datetime.date(1712, 6, 28))
    out = person.format_for_ajax_search()
    assert "1712" in out
    assert "-" in out


# ---------------------------------------------------------------------------
# get_relations / get_reverse_relations / has_relations (empty cases)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_relations_empty_returns_list(person, bio):
    assert person.get_relations() == []


@pytest.mark.django_db
def test_get_reverse_relations_empty_returns_list(person, bio):
    assert person.get_reverse_relations() == []


@pytest.mark.django_db
def test_has_relations_false_when_none(person, bio):
    assert person.has_relations() is False
