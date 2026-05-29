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

"""Unit tests for the DB-free helpers in fiches.utils."""

import pytest
from django.contrib.auth.models import AnonymousUser
from fiches.utils import (
    remove_object_index,
    supprime_accent,
    update_object_index,
    user_can_change_documentfile,
    user_can_delete_documentfile,
)


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
