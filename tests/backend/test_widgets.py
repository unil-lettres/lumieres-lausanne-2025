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

"""Unit tests for fiches.widgets — PersonWidget, StaticList, DynamicList."""

import pytest
from fiches.models.person.person import Person
from fiches.widgets import DynamicList, PersonWidget, StaticList


class _BadField:
    """Fake FK field whose related_model raises AttributeError."""

    name = "person"

    @property
    def related_model(self):
        raise AttributeError("no model")


# ---------------------------------------------------------------------------
# PersonWidget.__init__  (lines 60-61, 64)
# ---------------------------------------------------------------------------


def test_person_widget_init_bad_field_does_not_raise():
    # AttributeError on fk_field.related_model is caught → prints, continues
    widget = PersonWidget(fk_field=_BadField())
    assert widget.lookup_class == ""  # fallback to empty


def test_person_widget_init_attrs_none_defaults_to_empty_dict():
    widget = PersonWidget(fk_field=None, attrs=None)
    assert "ContributionDoc_person" in widget.attrs.get("class", "")


# ---------------------------------------------------------------------------
# PersonWidget.format_value  (lines 75-89)
# ---------------------------------------------------------------------------


def test_format_value_none_returns_empty():
    assert PersonWidget().format_value(None) == ""


def test_format_value_empty_string_returns_empty():
    assert PersonWidget().format_value("") == ""


@pytest.mark.django_db
def test_format_value_person_instance_returns_str():
    person = Person.objects.create(name="Rousseau, Jean-Jacques")
    widget = PersonWidget()
    assert widget.format_value(person) == str(person)


@pytest.mark.django_db
def test_format_value_pk_returns_str():
    person = Person.objects.create(name="Voltaire, François")
    widget = PersonWidget()
    assert widget.format_value(person.pk) == str(person)


@pytest.mark.django_db
def test_format_value_unknown_pk_returns_str_of_value():
    widget = PersonWidget()
    result = widget.format_value(999999)
    assert result == "999999"


# ---------------------------------------------------------------------------
# PersonWidget.render  (lines 96-100, 109)
# ---------------------------------------------------------------------------


def test_render_with_value_produces_inputs():
    widget = PersonWidget()
    html = widget.render("person", "42|Voltaire")
    assert 'type="hidden"' in html
    assert 'type="text"' in html


def test_render_no_value_produces_empty_inputs():
    widget = PersonWidget()
    html = widget.render("person", None)
    assert 'value=""' in html


def test_render_attrs_class_included():
    widget = PersonWidget()
    html = widget.render("person", "1|Name", attrs={"class": "custom"})
    assert "custom" in html


# ---------------------------------------------------------------------------
# StaticList  (lines 135, 137, 153, 159-160, 171-173, 207-209)
# ---------------------------------------------------------------------------


def test_static_list_render_none_value():
    widget = StaticList(choices=[(1, "Option A")])
    html = widget.render("field", None)
    assert "staticlist" in html


def test_static_list_render_no_attrs():
    widget = StaticList(choices=[(1, "Option A")])
    html = widget.render("field", [], attrs=None)
    assert "staticlist" in html


def test_static_list_render_selected_value_appears():
    widget = StaticList(choices=[(1, "Option A"), (2, "Option B")])
    html = widget.render("field", [1])
    assert "Option A" in html


def test_static_list_render_empty_label_in_select():
    widget = StaticList(choices=[(1, "Option A")], empty_label="-- choisir --")
    html = widget.render("field", [])
    assert "-- choisir --" in html


def test_static_list_render_option_list_selected_has_attribute():
    widget = StaticList(choices=[(1, "Option A"), (2, "Option B")])
    html = widget.render_option_list(["1"], [(1, "Option A"), (2, "Option B")])
    assert 'selected="selected"' in html


def test_static_list_render_option_list_not_selected():
    widget = StaticList(choices=[(1, "Option A")])
    html = widget.render_option_list(["99"], [(1, "Option A")])
    assert 'selected="selected"' not in html


# ---------------------------------------------------------------------------
# DynamicList.__init__  (lines 224-226)
# ---------------------------------------------------------------------------


def test_dynamic_list_init_non_fk_rel_sets_rel_none():
    widget = DynamicList(rel=object())
    assert widget.rel is None


def test_dynamic_list_init_no_rel():
    widget = DynamicList()
    assert widget.rel is None


# ---------------------------------------------------------------------------
# DynamicList.render  (lines 243, 247, 268-277, 283, 287-288, 299)
# ---------------------------------------------------------------------------


def test_dynamic_list_render_none_value():
    widget = DynamicList()
    html = widget.render("field", None)
    assert "dynamiclist" in html


def test_dynamic_list_render_no_attrs():
    widget = DynamicList()
    html = widget.render("field", [], attrs=None)
    assert "dynamiclist" in html


def test_dynamic_list_render_string_with_pipe():
    # "42|Name" → id_value path (lines 270-273)
    widget = DynamicList()
    html = widget.render("field", ["42|Voltaire"])
    assert "dynamiclist" in html


def test_dynamic_list_render_plain_string():
    # "plain" → name_value path (lines 274-275) → rendered in output (line 299)
    widget = DynamicList()
    html = widget.render("field", ["Voltaire"])
    assert "Voltaire" in html


def test_dynamic_list_render_integer_value():
    # 42 → else id_value path (lines 276-277)
    widget = DynamicList()
    html = widget.render("field", [42])
    assert "dynamiclist" in html


def test_dynamic_list_render_person_instance():
    # Person → isinstance branch (lines 268-269)
    widget = DynamicList()
    person = Person(name="Diderot, Denis", pk=77)
    html = widget.render("field", [person])
    assert "dynamiclist" in html


def test_dynamic_list_render_no_rel_objs_empty(db):
    # self.rel=None → objs=[] (line 283), loop skipped
    widget = DynamicList(rel=None)
    html = widget.render("field", [1])
    assert "dynamiclist_container" in html


@pytest.mark.django_db
def test_dynamic_list_render_with_rel_renders_db_objects():
    # self.rel=Person → DB query → object rendered (lines 287-288)
    from django.db import models as django_models

    person = Person.objects.create(name="Condorcet, Marie-Jean")

    class _FakeField:
        field = None

    # Build a simple FK-like field pointing to Person
    class _FakeFK(django_models.ForeignKey):
        pass

    widget = DynamicList()
    widget.rel = Person  # bypass __init__, set rel directly
    html = widget.render("field", [person.pk])
    assert str(person) in html
