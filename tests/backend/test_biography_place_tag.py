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

"""Tests for the place-tagging widget on the biography place fields (§2.2)."""

from __future__ import annotations

from fiches.models.person.biography import Biography, BiographyForm, Profession, ProfessionForm
from fiches.place_tag import PlaceTagWidget

PLACE_TAG = '<a class="ll-tag ll-tag-place" data-place="3" href="/fiches/lieu/3/" title="Lausanne">Lausanne</a>'


def test_biography_place_fields_use_the_place_tag_widget():
    form = BiographyForm()
    for name in ("birth_place", "death_place", "origin"):
        assert isinstance(form.fields[name].widget, PlaceTagWidget), name


def test_profession_place_field_uses_the_place_tag_widget():
    # ProfessionForm's model is supplied by inlineformset_factory, so inspect the
    # declared field directly rather than instantiating the bare ModelForm.
    assert isinstance(ProfessionForm.base_fields["place"].widget, PlaceTagWidget)


def test_place_fields_are_textfields_to_hold_tagged_html():
    # CharField(256) could not hold the tag markup; the fields are TextField.
    assert Biography._meta.get_field("birth_place").get_internal_type() == "TextField"
    assert Biography._meta.get_field("origin").get_internal_type() == "TextField"
    assert Profession._meta.get_field("place").get_internal_type() == "TextField"


def test_widget_renders_contenteditable_hidden_and_button():
    html = PlaceTagWidget().render("birth_place", PLACE_TAG)
    assert 'contenteditable="true"' in html
    assert 'name="birth_place"' in html  # the mirrored hidden input
    assert "placetag_button" in html
    # An existing tag is rendered raw so it shows as a link in the editable area.
    assert PLACE_TAG in html


def test_field_round_trips_tagged_html():
    cleaned = BiographyForm().fields["birth_place"].clean(PLACE_TAG)
    assert cleaned == PLACE_TAG
