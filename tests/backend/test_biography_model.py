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

"""Unit tests for biography.py models: Nationality, Religion, Biography,
NoteBiography, Profession, SocietyMembership."""

import datetime

import pytest
from fiches.models.misc.society import Society
from fiches.models.person.biography import (
    Biography,
    Nationality,
    NoteBiography,
    Profession,
    Religion,
    SocietyMembership,
)
from fiches.models.person.person import Person


@pytest.fixture
def person(db):
    return Person.objects.create(name="Voltaire, François")


@pytest.fixture
def bio(person):
    return Biography.objects.create(person=person, version=0, valid=False)


# ---------------------------------------------------------------------------
# Nationality / Religion __str__ (lines 44, 61) — DB-free
# ---------------------------------------------------------------------------


def test_nationality_str():
    assert str(Nationality(name="Française")) == "Française"


def test_religion_str():
    assert str(Religion(name="Catholique", sorting=1)) == "Catholique"


# ---------------------------------------------------------------------------
# Biography.person_name() (lines 113-123) — DB-free
# ---------------------------------------------------------------------------


def test_person_name_no_dates():
    bio = Biography(person=Person(name="Diderot, Denis"))
    assert bio.person_name() == "Diderot, Denis"


def test_person_name_with_both_dates():
    bio = Biography(
        person=Person(name="Rousseau, Jean-Jacques"),
        birth_date=datetime.date(1712, 6, 28),
        death_date=datetime.date(1778, 7, 2),
    )
    result = bio.person_name()
    assert "1712" in result
    assert "1778" in result
    assert "(" in result


def test_person_name_birth_approx():
    bio = Biography(
        person=Person(name="X"),
        birth_date=datetime.date(1700, 1, 1),
        death_date=datetime.date(1770, 1, 1),
        birth_date_approx=True,
    )
    assert "v. 1700" in bio.person_name()


def test_person_name_death_approx():
    bio = Biography(
        person=Person(name="X"),
        birth_date=datetime.date(1700, 1, 1),
        death_date=datetime.date(1770, 1, 1),
        death_date_approx=True,
    )
    assert "v. 1770" in bio.person_name()


# ---------------------------------------------------------------------------
# Biography.relations / reverse_relations / __str__ (lines 126, 130, 133) — DB
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_biography_relations_returns_empty_qs(bio):
    assert list(bio.relations()) == []


@pytest.mark.django_db
def test_biography_reverse_relations_returns_empty_qs(bio):
    assert list(bio.reverse_relations()) == []


@pytest.mark.django_db
def test_biography_str_equals_person_name(bio, person):
    assert str(bio) == person.name


# ---------------------------------------------------------------------------
# NoteBiography.rte_type (line 196) — DB-free
# ---------------------------------------------------------------------------


def test_note_biography_rte_type():
    note = NoteBiography.__new__(NoteBiography)
    assert note.rte_type == "CKE"


# ---------------------------------------------------------------------------
# Profession.get_formatted_dates / __str__ (lines 281-297, 300) — DB-free
# ---------------------------------------------------------------------------


def test_profession_no_dates_returns_question_marks():
    prof = Profession(position="Écrivain", place="Paris", begin_date_f="", end_date_f="")
    assert prof.get_formatted_dates() == ("?", "?")


def test_profession_begin_date_only():
    prof = Profession(
        position="Poète",
        place="Lyon",
        begin_date=datetime.date(1750, 3, 10),
        begin_date_f="dY",
        end_date_f="",
    )
    begin, end = prof.get_formatted_dates()
    assert "1750" in begin
    assert end == "?"


def test_profession_both_dates():
    prof = Profession(
        position="Philosophe",
        place="Paris",
        begin_date=datetime.date(1750, 3, 10),
        begin_date_f="Y",
        end_date=datetime.date(1780, 5, 20),
        end_date_f="Y",
    )
    begin, end = prof.get_formatted_dates()
    assert "1750" in begin
    assert "1780" in end


def test_profession_begin_approx():
    prof = Profession(
        position="Libraire",
        place="Genève",
        begin_date=datetime.date(1760, 1, 1),
        begin_date_f="Y",
        begin_date_approx=True,
        end_date_f="",
    )
    begin, _ = prof.get_formatted_dates()
    assert begin.startswith("v. ")


def test_profession_end_approx():
    prof = Profession(
        position="Éditeur",
        place="Lausanne",
        begin_date_f="",
        end_date=datetime.date(1800, 6, 1),
        end_date_f="Y",
        end_date_approx=True,
    )
    _, end = prof.get_formatted_dates()
    assert end.startswith("v. ")


def test_profession_str_contains_position():
    prof = Profession(
        position="Diplomate",
        place="Berne",
        begin_date=datetime.date(1770, 1, 1),
        begin_date_f="Y",
        end_date=datetime.date(1790, 1, 1),
        end_date_f="Y",
    )
    result = str(prof)
    assert "Diplomate" in result
    assert "Berne" in result


# ---------------------------------------------------------------------------
# SocietyMembership.get_formatted_dates / __str__ (lines 344-358, 361-365)
# ---------------------------------------------------------------------------


def test_society_membership_no_dates_returns_none():
    soc = Society(name="Académie française")
    sm = SocietyMembership(society=soc, begin_date_f="", end_date_f="")
    assert sm.get_formatted_dates() is None


def test_society_membership_str_no_dates_returns_society_name():
    soc = Society(name="Académie française")
    sm = SocietyMembership(society=soc, begin_date_f="", end_date_f="")
    assert str(sm) == "Académie française"


def test_society_membership_with_dates():
    soc = Society(name="Académie de Berlin")
    sm = SocietyMembership(
        society=soc,
        begin_date=datetime.date(1746, 1, 1),
        begin_date_f="Y",
        end_date=datetime.date(1766, 1, 1),
        end_date_f="Y",
    )
    dates = sm.get_formatted_dates()
    assert dates is not None
    assert "1746" in dates[0]
    assert "1766" in dates[1]


def test_society_membership_str_with_dates():
    soc = Society(name="Académie de Berlin")
    sm = SocietyMembership(
        society=soc,
        begin_date=datetime.date(1746, 1, 1),
        begin_date_f="Y",
        end_date=datetime.date(1766, 1, 1),
        end_date_f="Y",
    )
    result = str(sm)
    assert "Académie de Berlin" in result
    assert "1746" in result


def test_society_membership_begin_approx():
    soc = Society(name="Académie royale")
    sm = SocietyMembership(
        society=soc,
        begin_date=datetime.date(1750, 1, 1),
        begin_date_f="Y",
        begin_date_approx=True,
        end_date=datetime.date(1760, 1, 1),
        end_date_f="Y",
    )
    dates = sm.get_formatted_dates()
    assert dates[0].startswith("v. ")


def test_society_membership_end_approx():
    soc = Society(name="Société des arts")
    sm = SocietyMembership(
        society=soc,
        begin_date=datetime.date(1750, 1, 1),
        begin_date_f="Y",
        end_date=datetime.date(1780, 1, 1),
        end_date_f="Y",
        end_date_approx=True,
    )
    dates = sm.get_formatted_dates()
    assert dates[1].startswith("v. ")
