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

"""Tests for the ``paginate`` template tag windowing logic.

Migrated from the legacy doctest in ``pagination/tests.py`` (Python 2 era).
Only the deterministic ``paginate()`` page-window cases are ported; the old
``InfinitePaginator`` / ``FinitePaginator`` doctests are dropped because those
classes are incompatible with the current Django Paginator (they delete
private attributes that no longer exist).
"""

import pytest
from django.core.paginator import Paginator
from django.template import TemplateSyntaxError
from pagination.templatetags.pagination_tags import do_autopaginate, paginate


def _pages(total, per_page, orphans=0):
    paginator = Paginator(range(total), per_page, orphans)
    return paginate({"paginator": paginator, "page_obj": paginator.page(1)})["pages"]


@pytest.mark.parametrize(
    "total,expected",
    [
        (15, [1, 2, 3, 4, 5, 6, 7, 8]),
        (17, [1, 2, 3, 4, 5, 6, 7, 8, 9]),
        (19, [1, 2, 3, 4, None, 7, 8, 9, 10]),
        (21, [1, 2, 3, 4, None, 8, 9, 10, 11]),
    ],
)
def test_paginate_windows(total, expected):
    assert _pages(total, 2) == expected


@pytest.mark.parametrize(
    "total,expected",
    [
        (5, [1, 2]),
        (21, [1, 2, 3, 4, None, 7, 8, 9, 10]),
    ],
)
def test_paginate_windows_with_orphans(total, expected):
    assert _pages(total, 2, orphans=1) == expected


class _Token:
    """Minimal template Token stand-in (only ``split_contents`` is used)."""

    def __init__(self, contents):
        self.contents = contents

    def split_contents(self):
        return self.contents.split()


def test_do_autopaginate_too_many_args_raises_syntax_error():
    # Regression (ruff F507): the error branch formatted its message with a
    # misplaced ``%`` on a placeholder-less string, raising TypeError instead
    # of TemplateSyntaxError.
    with pytest.raises(TemplateSyntaxError):
        do_autopaginate(None, _Token("autopaginate a b c d"))


def test_do_autopaginate_as_without_varname_raises_syntax_error():
    # Same F507 regression on the ``… as <missing-var>`` branch.
    with pytest.raises(TemplateSyntaxError):
        do_autopaginate(None, _Token("autopaginate items as"))
