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

"""Unit tests for utils.fields.DictField pickle (de)serialisation (DB-free)."""

import pickle

from utils.fields import DictField

FIELD = DictField()


def test_to_python_empty_string_is_none():
    assert FIELD.to_python("") is None


def test_to_python_dict_passthrough():
    assert FIELD.to_python({"a": 1}) == {"a": 1}


def test_to_python_none_is_none():
    assert FIELD.to_python(None) is None


def test_to_python_non_string_value_passthrough():
    assert FIELD.to_python(42) == 42


def test_from_db_value_none_is_none():
    assert FIELD.from_db_value(None, None, None) is None


def test_from_db_value_round_trip():
    stored = pickle.dumps({"x": 5, "y": [1, 2]}).decode("latin1")
    assert FIELD.from_db_value(stored, None, None) == {"x": 5, "y": [1, 2]}


def test_from_db_value_invalid_pickle_passthrough():
    assert FIELD.from_db_value("not a pickle", None, None) == "not a pickle"


def test_get_db_prep_save_non_dict_is_none():
    assert FIELD.get_db_prep_save("nope", None) is None


def test_get_db_prep_save_dict_returns_pickled_bytes():
    # Covers the dict branch (lines 62, 66): pickle.dumps + super().get_db_prep_save
    result = FIELD.get_db_prep_save({"k": 42}, None)
    assert isinstance(result, bytes)
    assert pickle.loads(result) == {"k": 42}


def test_to_python_str_raises_type_error():
    # Bug (Python 3): to_python() calls pickle.loads(smart_str(value)) when
    # value is a non-empty string. smart_str() returns str, but pickle.loads()
    # requires bytes in Python 3 → TypeError propagates uncaught (line 53).
    # Lines 54-55 (except ValueError/UnpicklingError) are dead code in Python 3
    # because pickle.loads(str) always raises TypeError, never ValueError.
    import pytest
    with pytest.raises(TypeError):
        FIELD.to_python("non-empty-string-that-is-not-a-pickle")
