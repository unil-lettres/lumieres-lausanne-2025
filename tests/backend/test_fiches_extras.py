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

"""Unit tests for the pure (DB-free) template filters in ``fiches.templatetags.fiches_extras``."""

import collections

import pytest
from fiches.templatetags import fiches_extras as fx


@pytest.mark.parametrize(
    ("string", "needle", "expected"),
    [("hello", "he", True), ("hello", "lo", False), ("", "", True)],
)
def test_startswith(string, needle, expected):
    assert fx.startswith(string, needle) == expected


@pytest.mark.parametrize("bad", [None, 5, object()])
def test_startswith_bad_input_returns_empty(bad):
    assert fx.startswith(bad, "x") == ""


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("&#65;", "A"),
        ("&#233;", "é"),
        ("&amp;", "&"),
        ("a&#66;c", "aBc"),
        ("plain text", "plain text"),
    ],
)
def test_decode_html_entities(raw, expected):
    assert fx.decodeHtmlEntities(raw) == expected


def test_substract():
    assert fx.substract("10", "3") == 7
    assert fx.substract(5, 2) == 3


def test_split_with_token():
    assert fx.split("a,b,c", ",") == ["a", "b", "c"]


def test_split_without_token_returns_value():
    assert fx.split("a,b,c", "") == "a,b,c"


def test_split_coerces_to_str():
    assert fx.split(123, "2") == ["1", "3"]


def test_attr_extracts_attribute():
    point = collections.namedtuple("Point", "name")
    assert fx.attr([point("a"), point("b")], "name") == ["a", "b"]


def test_attr_without_token_returns_value():
    assert fx.attr([1, 2], "") == [1, 2]


def test_truncatechars_truncates_with_ellipsis():
    assert fx.truncatechars("hello world", "8") == "hello..."


def test_truncatechars_short_unchanged():
    assert fx.truncatechars("hi", "8") == "hi"


def test_truncate_chars_breaks_on_word_boundary():
    # s[:12] == "the quick br" -> drop the partial last word -> "the quick" + ellipsis
    assert fx.truncate_chars("the quick brown fox", 12) == "the quick ..."


def test_truncate_chars_short_unchanged():
    assert fx.truncate_chars("short", 50) == "short"


def test_field_verbose_name():
    from fiches.models.person.person import Person

    assert str(fx.field_verbose_name(Person, "name")) == "Nom"


def test_field_verbose_name_missing_field_returns_empty():
    from fiches.models.person.person import Person

    assert fx.field_verbose_name(Person, "does_not_exist") == ""


def test_meta_returns_meta_attribute():
    from fiches.models.person.person import Person

    assert fx.meta(Person(), "verbose_name") == "Personne"


def test_meta_missing_returns_empty():
    assert fx.meta(object(), "anything") == ""
