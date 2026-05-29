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

"""Regression tests for runtime bugs surfaced by the ruff lint pass.

Each test exercises a code path that previously raised at runtime (NameError
from a missing/mis-scoped import) before the F821 fixes.
"""

import pytest


@pytest.mark.django_db
def test_biography_get_absolute_url_resolves():
    """`reverse` was imported in the class body, so undefined in the method (F821)."""
    from fiches.models.person.biography import Biography
    from fiches.models.person.person import Person

    person = Person.objects.create(name="Test, Person")
    bio = Biography.objects.create(person=person)

    url = bio.get_absolute_url()
    assert str(person.pk) in url


def test_fiches_search_form_get_models_uses_haystack_connection():
    """`connections` was used in get_models() without being imported (F821)."""
    from fiches.forms import FichesSearchForm

    # With no selected models the form falls back to the Haystack unified index;
    # that branch referenced the undefined `connections` name before the fix.
    assert isinstance(FichesSearchForm().get_models(), list)
