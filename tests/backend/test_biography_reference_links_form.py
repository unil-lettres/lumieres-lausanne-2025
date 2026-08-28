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

"""Tests for the « Sites de référence » field on the biography form (§2.1 brick C).

The field reuses the shared reference-link widget, scoped to person-applicable
référentiels, and round-trips through the BiographyReferenceSite pivot.
"""

from __future__ import annotations

import pytest
from fiches.models import BiographyReferenceSite, ReferenceSite
from fiches.models.person.biography import Biography, BiographyForm
from fiches.models.person.person import Person


@pytest.fixture
def idref(db):
    # Person-applicable référentiel.
    return ReferenceSite.objects.create(
        name="IdRef",
        code="idref",
        base_url="https://www.idref.fr/{id}",
        applies_to_person=True,
        applies_to_place=False,
    )


@pytest.fixture
def geonames(db):
    # Place-only référentiel: must not be offered on a biography.
    return ReferenceSite.objects.create(
        name="GeoNames",
        code="geonames",
        base_url="https://www.geonames.org/{id}",
        applies_to_person=False,
        applies_to_place=True,
    )


@pytest.fixture
def voltaire(db):
    person = Person.objects.create(name="Voltaire, François")
    return Biography.objects.create(person=person, version=0, valid=False)


@pytest.mark.django_db
def test_reference_links_field_is_person_scoped(idref, geonames):
    form = BiographyForm()
    assert form.fields["reference_links"].applies == "person"
    html = form.fields["reference_links"].widget.render("reference_links", [])
    # The add dropdown offers the person référentiel, not the place-only one.
    assert "IdRef" in html
    assert "GeoNames" not in html


@pytest.mark.django_db
def test_reference_links_clean_drops_non_person_sites(idref, geonames):
    field = BiographyForm().fields["reference_links"]
    pairs = field.clean([f"{idref.id}|026745135", f"{geonames.id}|2660718"])
    assert pairs == [(idref.id, "026745135")]


@pytest.mark.django_db
def test_reference_links_clean_keeps_one_link_per_site(idref):
    field = BiographyForm().fields["reference_links"]
    pairs = field.clean([f"{idref.id}|026745135", f"{idref.id}|999999"])
    assert pairs == [(idref.id, "026745135")]


@pytest.mark.django_db
def test_reference_links_initial_preloaded_from_instance(idref, voltaire):
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")
    form = BiographyForm(instance=voltaire)
    assert form.initial["reference_links"] == [f"{idref.id}|026745135"]


@pytest.mark.django_db
def test_widget_renders_existing_link_chip_with_permalink(idref, voltaire):
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")
    form = BiographyForm(instance=voltaire)
    html = str(form["reference_links"])
    assert "https://www.idref.fr/026745135" in html


@pytest.mark.django_db
def test_widget_stacks_saved_links_one_per_line(idref, geonames, voltaire):
    """Client request 2026-07-15: saved links must not flow into one wrapped line.

    They were <span>s, so several référentiels ran together and became
    unreadable; DynamicList uses a <div> per entry, and so must this widget.
    """
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")

    html = str(BiographyForm(instance=voltaire)["reference_links"])

    assert '<div class="reflist_value_entry dynamiclist_value_entry">' in html
    assert '<span class="reflist_value_entry' not in html


@pytest.mark.django_db
def test_widget_exposes_the_identifier_as_an_editable_input(idref, voltaire):
    """Same request: correcting a typo should not mean deleting and retyping.

    The input carries the référentiel id and base URL so the widget's JS can
    resync the submitted payload and the permalink as the editor types.
    """
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")

    html = str(BiographyForm(instance=voltaire)["reference_links"])

    assert 'class="reflist_value_id" value="026745135"' in html
    assert f'data-site-id="{idref.id}"' in html
    assert 'data-base-url="https://www.idref.fr/{id}"' in html
    # The label no longer repeats the identifier: the input holds it now.
    assert f'<span class="reflist_value_label">{idref.name}</span>' in html


@pytest.mark.django_db
def test_clearing_an_identifier_drops_the_link(idref):
    """Emptying the input removes the link on save, via the field's own cleaning."""
    field = BiographyForm().fields["reference_links"]

    assert field.clean([f"{idref.id}|"]) == []
