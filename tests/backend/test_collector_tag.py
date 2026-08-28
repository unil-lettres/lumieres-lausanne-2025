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

"""Unit tests for fiches.templatetags.collector (editable_projects filter)."""

import pytest
from django import template
from django.contrib.auth.models import AnonymousUser, User
from fiches.templatetags.collector import editable_projects


def test_non_user_raises_syntax_error():
    with pytest.raises(template.TemplateSyntaxError):
        editable_projects("not a user")


def test_none_raises_syntax_error():
    with pytest.raises(template.TemplateSyntaxError):
        editable_projects(None)


def test_anonymous_user_returns_empty_set():
    assert editable_projects(AnonymousUser()) == set()


@pytest.mark.django_db
def test_user_without_profile_returns_empty_set():
    user = User.objects.create_user(username="testcollector", password="x")
    assert editable_projects(user) == set()
