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

"""Unit tests for fiches.templatetags.fiches_extras (filters, tags, access helpers)."""

import collections
import datetime
import types

import pytest
from django import template
from django.contrib.auth.models import AnonymousUser, User
from django.template import TemplateSyntaxError
from fiches.templatetags import fiches_extras as fx


class _Token:
    """Minimal template Token stand-in."""

    def __init__(self, contents):
        self.contents = contents

    def split_contents(self):
        return self.contents.split()


class _ACObj:
    """Minimal object with user_access()."""

    def __init__(self, result=True):
        self._result = result

    def user_access(self, user, any_login=False):
        return self._result


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


# ---------------------------------------------------------------------------
# decodeHtmlEntities — edge cases (lines 82-83, 90)
# ---------------------------------------------------------------------------


def test_decode_html_entities_invalid_numeric_returns_raw():
    # &#abc; → group(1)="#", group(2)="abc" via \w branch → int("abc") raises ValueError
    assert fx.decodeHtmlEntities("&#abc;") == "&#abc;"


def test_decode_html_entities_unknown_named_returns_raw():
    # &unknownentity; → name not in name2codepoint → cp is None → return match.group()
    assert fx.decodeHtmlEntities("&unknownentity;") == "&unknownentity;"


# ---------------------------------------------------------------------------
# date_f (lines 115-141)
# ---------------------------------------------------------------------------


def test_date_f_missing_field_returns_error1():
    assert fx.date_f(types.SimpleNamespace(), "birth_date") == "error 1"


def test_date_f_none_field_returns_empty():
    m = types.SimpleNamespace(birth_date=None, birth_date_f="")
    assert fx.date_f(m, "birth_date") == ""


def test_date_f_no_format_in_param_uses_defaults():
    m = types.SimpleNamespace(birth_date=datetime.date(1712, 6, 28), birth_date_f="")
    result = fx.date_f(m, "birth_date")
    assert "1712" in result


def test_date_f_with_format_string():
    m = types.SimpleNamespace(birth_date=datetime.date(1712, 6, 28), birth_date_f="dY")
    result = fx.date_f(m, "birth_date|dY|.")
    assert "28" in result
    assert "1712" in result


def test_date_f_format_filters_by_field_format():
    # format_str="dmY", field_format="Y" → only Y in user_format
    m = types.SimpleNamespace(birth_date=datetime.date(1712, 6, 28), birth_date_f="Y")
    result = fx.date_f(m, "birth_date|dmY|.")
    assert result == "1712"


# ---------------------------------------------------------------------------
# date_biblio (lines 148-149, 156)
# ---------------------------------------------------------------------------


def test_date_biblio_missing_field_returns_sd():
    assert fx.date_biblio(types.SimpleNamespace(), "date") == "[s.d.]"


def test_date_biblio_none_field_returns_sd():
    m = types.SimpleNamespace(date=None, date_f="")
    assert fx.date_biblio(m, "date") == "[s.d.]"


def test_date_biblio_with_format_string():
    m = types.SimpleNamespace(date=datetime.date(1762, 3, 15), date_f="dY")
    result = fx.date_biblio(m, "date")
    assert "1762" in str(result)


def test_date_biblio_no_format_returns_raw_field():
    m = types.SimpleNamespace(date=datetime.date(1762, 3, 15), date_f="")
    result = fx.date_biblio(m, "date")
    assert result == datetime.date(1762, 3, 15)


# ---------------------------------------------------------------------------
# sort_biblio (lines 187-250)
# ---------------------------------------------------------------------------


def _sr(pk=1, sort1="", sort2=None, obj=None):
    r = types.SimpleNamespace()
    r.pk = pk
    r.stored_fields = {"sort1": sort1, "sort2": sort2}
    r.object = obj
    return r


def test_sort_biblio_unknown_label_returns_unchanged():
    items = [_sr(1), _sr(2)]
    assert fx.sort_biblio(items, "unknown") is items


def test_sort_biblio_none_label_returns_unchanged():
    items = [_sr(1)]
    assert fx.sort_biblio(items, None) is items


def test_sort_biblio_type_error_returns_unchanged():
    sentinel = object()
    result = fx.sort_biblio(sentinel, "livre")
    assert result is sentinel


def test_sort_biblio_livre_sorts_by_author():
    a = _sr(1, sort1="Zola")
    b = _sr(2, sort1="Balzac")
    result = fx.sort_biblio([a, b], "livre")
    assert result == [b, a]


def test_sort_biblio_livre_sorts_by_date_when_same_author():
    a = _sr(1, sort1="Hugo", sort2=datetime.date(1880, 1, 1))
    b = _sr(2, sort1="Hugo", sort2=datetime.date(1862, 1, 1))
    result = fx.sort_biblio([a, b], "livre")
    assert result == [b, a]


def test_sort_biblio_date_as_string():
    a = _sr(1, sort1="A", sort2="1900")
    b = _sr(2, sort1="A", sort2="1800")
    result = fx.sort_biblio([a, b], "livre")
    assert result == [b, a]


def test_sort_biblio_date_as_int():
    a = _sr(1, sort1="A", sort2=1900)
    b = _sr(2, sort1="A", sort2=1800)
    result = fx.sort_biblio([a, b], "livre")
    assert result == [b, a]


def test_sort_biblio_date_as_datetime():
    a = _sr(1, sort1="A", sort2=datetime.datetime(1900, 1, 1))
    b = _sr(2, sort1="A", sort2=datetime.datetime(1800, 1, 1))
    result = fx.sort_biblio([a, b], "livre")
    assert result == [b, a]


def test_sort_biblio_transcription_label():
    a = _sr(1, sort1="Z")
    b = _sr(2, sort1="A")
    result = fx.sort_biblio([a, b], "transcription")
    assert result == [b, a]


# ---------------------------------------------------------------------------
# urlizename (lines 258-259)
# ---------------------------------------------------------------------------


def test_urlizename_wraps_url():
    result = fx.urlizename("http://example.com", "click")
    assert "click" in result
    assert "http://example.com" in result


def test_urlizename_default_link_text():
    result = fx.urlizename("http://example.com")
    assert "link" in result


# ---------------------------------------------------------------------------
# access_strict / access_lazy / df_access (lines 335-338, 347, 358)
# ---------------------------------------------------------------------------


def test_access_strict_non_user_raises():
    with pytest.raises(TemplateSyntaxError):
        fx.access_strict(_ACObj(), "not_a_user")


def test_access_strict_anonymous_user_access_true():
    assert fx.access_strict(_ACObj(result=True), AnonymousUser()) is True


def test_access_strict_anonymous_user_access_false():
    assert fx.access_strict(_ACObj(result=False), AnonymousUser()) is False


def test_access_lazy_passes_any_login_true():
    # access_lazy calls access_strict(..., any_login=True)
    # _ACObj always returns True regardless of any_login, so just check it delegates
    assert fx.access_lazy(_ACObj(result=True), AnonymousUser()) is True


def test_df_access_delegates_to_lazy():
    assert fx.df_access(_ACObj(result=False), AnonymousUser()) is False


# ---------------------------------------------------------------------------
# TooltipLinkNode (line 364, 373-374)
# ---------------------------------------------------------------------------


def test_tooltip_link_node_literal_id():
    node = fx.TooltipLinkNode('"my-tooltip"')
    assert node.id == "my-tooltip"
    result = node.render({})
    assert 'href="#my-tooltip"' in result


def test_tooltip_link_node_variable_id_resolves():
    node = fx.TooltipLinkNode("varname")
    assert node.id is None  # variable path
    ctx = template.Context({"varname": "resolved-id"})
    result = node.render(ctx)
    assert 'href="#resolved-id"' in result


def test_tooltip_link_node_missing_variable_returns_empty():
    node = fx.TooltipLinkNode("missing_var")
    ctx = template.Context({})
    assert node.render(ctx) == ""


# ---------------------------------------------------------------------------
# tooltiplink tag — ValueError path (lines 381-382)
# ---------------------------------------------------------------------------


def test_tooltiplink_no_arg_raises_syntax_error():
    with pytest.raises(TemplateSyntaxError):
        fx.tooltiplink(None, _Token("tooltiplink"))


# ---------------------------------------------------------------------------
# TimestampNode + timstamp tag (lines 389, 397)
# ---------------------------------------------------------------------------


def test_timestamp_node_render_returns_empty():
    node = fx.TimestampNode("whatever")
    assert node.render({}) == ""


def test_timstamp_tag_returns_node():
    node = fx.timstamp(None, _Token("timestamp myvar"))
    assert isinstance(node, fx.TimestampNode)


# ---------------------------------------------------------------------------
# do_ac_check / ACCheckNode (lines 436-438, 441-446, 451-466)
# ---------------------------------------------------------------------------


def test_do_ac_check_no_arg_raises():
    with pytest.raises(TemplateSyntaxError):
        fx.do_ac_check(None, _Token("ac_check"))


def test_do_ac_check_invalid_args_raises():
    with pytest.raises(TemplateSyntaxError):
        fx.do_ac_check(None, _Token("ac_check ???"))


def test_do_ac_check_simple_returns_node():
    node = fx.do_ac_check(None, _Token("ac_check myobj myuser"))
    assert isinstance(node, fx.ACCheckNode)
    assert node.var_name is None


def test_do_ac_check_as_syntax_sets_var_name():
    node = fx.do_ac_check(None, _Token("ac_check myobj myuser as result"))
    assert isinstance(node, fx.ACCheckNode)
    assert node.var_name == "result"


def test_ac_check_node_render_returns_access():
    node = fx.ACCheckNode("myobj", "myuser")
    ctx = template.Context({"myobj": _ACObj(result=True), "myuser": AnonymousUser()})
    assert node.render(ctx) is True


def test_ac_check_node_render_stores_in_var():
    node = fx.ACCheckNode("myobj", "myuser", "can_see")
    ctx = template.Context({"myobj": _ACObj(result=True), "myuser": AnonymousUser()})
    assert node.render(ctx) == ""
    assert ctx["can_see"] is True


# ---------------------------------------------------------------------------
# do_captureas — ValueError path (lines 473-474)
# ---------------------------------------------------------------------------


def test_do_captureas_no_arg_raises():
    with pytest.raises(template.TemplateSyntaxError):
        fx.do_captureas(None, _Token("captureas"))


# ---------------------------------------------------------------------------
# in_group2 (lines 59-60) — DB
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_in_group2_user_in_group():
    from django.contrib.auth.models import Group

    user = User.objects.create_user(username="g2_in", password="x")
    grp = Group.objects.create(name="Editors2")
    user.groups.add(grp)
    assert fx.in_group2(user, "Editors2") is True


@pytest.mark.django_db
def test_in_group2_user_not_in_group():
    user = User.objects.create_user(username="g2_out", password="x")
    assert fx.in_group2(user, "Editors2") is False


# ---------------------------------------------------------------------------
# access_grouplist as_id path (line 322) — DB
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_access_grouplist_as_id_returns_id_list():
    from fiches.models import UserGroup

    user = User.objects.create_user(username="agl_user", password="x")
    ug = UserGroup.objects.create(name="GroupAGL", sort=1)
    ug.users.add(user)
    result = fx.access_grouplist(user, "as_id")
    assert ug.id in result


@pytest.mark.django_db
def test_access_grouplist_user_no_groups_returns_empty():
    user = User.objects.create_user(username="agl_empty", password="x")
    assert fx.access_grouplist(user) == []
