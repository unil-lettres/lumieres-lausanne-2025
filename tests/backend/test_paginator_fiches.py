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

"""Unit tests for fiches.templatetags.paginator (context-window computation, DB-free)."""

import pytest
from fiches.templatetags.paginator import paginator


def _ctx(page, pages, **extra):
    ctx = {
        "page": page,
        "pages": pages,
        "page_obj": object(),
        "paginator": object(),
        "hits": pages * 10,
        "results_per_page": 10,
        "next": page + 1 if page < pages else None,
        "previous": page - 1 if page > 1 else None,
        "has_next": page < pages,
        "has_previous": page > 1,
    }
    ctx.update(extra)
    return ctx


@pytest.mark.parametrize(
    "page,pages,expected",
    [
        # startPage ≤ 3 → clamps to 1; endPage short of end
        (2, 10, [1, 2, 3, 4]),
        # full small range (endPage expands to pages+1)
        (1, 3, [1, 2, 3]),
        # middle: startPage > 3, endPage short of end
        (6, 15, [4, 5, 6, 7, 8]),
        # near end: endPage expands past pages → capped at pages
        (9, 10, [7, 8, 9, 10]),
    ],
)
def test_paginator_page_numbers(page, pages, expected):
    result = paginator(_ctx(page, pages))
    assert result["page_numbers"] == expected


@pytest.mark.parametrize(
    "page,pages,show_first,show_last",
    [
        (1, 3, False, False),   # all pages visible
        (2, 10, False, True),   # first visible, last not
        (6, 15, True, True),    # middle: both hidden
        (9, 10, True, False),   # last visible, first not
    ],
)
def test_paginator_show_flags(page, pages, show_first, show_last):
    result = paginator(_ctx(page, pages))
    assert result["show_first"] is show_first
    assert result["show_last"] is show_last


def test_paginator_passthrough_context_values():
    ctx = _ctx(3, 5)
    result = paginator(ctx)
    assert result["page"] == 3
    assert result["pages"] == 5
    assert result["hits"] == 50
    assert result["results_per_page"] == 10
    assert result["has_next"] is True
    assert result["has_previous"] is True
    assert result["page_obj"] is ctx["page_obj"]
    assert result["paginator"] is ctx["paginator"]


def test_paginator_query_vars_builds_qs():
    ctx = _ctx(1, 5, sort="name", q="test")
    result = paginator(ctx, query_vars_str="sort,q")
    assert "sort=name" in result["qs"]
    assert "q=test" in result["qs"]
    assert result["qs"].startswith("&")


def test_paginator_query_vars_missing_keys_gives_empty_qs():
    ctx = _ctx(1, 5)
    result = paginator(ctx, query_vars_str="sort")
    assert result["qs"] == ""


def test_paginator_no_query_vars_empty_qs():
    result = paginator(_ctx(1, 5))
    assert result["qs"] == ""
