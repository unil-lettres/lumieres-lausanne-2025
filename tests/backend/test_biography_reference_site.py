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

"""Unit tests for the BiographyReferenceSite pivot (biography ↔ référentiel)."""

from __future__ import annotations

import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError
from fiches.models import Biography, BiographyReferenceSite, Person, ReferenceSite


@pytest.fixture
def voltaire(db):
    person = Person.objects.create(name="Voltaire, François")
    return Biography.objects.create(person=person, version=0, valid=False)


@pytest.fixture
def idref(db):
    return ReferenceSite.objects.create(name="IdRef", code="idref", base_url="https://www.idref.fr/{id}")


@pytest.mark.django_db
def test_url_is_derived_from_reference_site(voltaire, idref):
    link = BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")
    assert link.url == "https://www.idref.fr/026745135"
    assert str(link) == "IdRef: 026745135"


@pytest.mark.django_db
def test_several_reference_sites_allowed(voltaire, idref):
    viaf = ReferenceSite.objects.create(name="VIAF", code="viaf", base_url="https://viaf.org/viaf/{id}")
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=viaf, identifier="36925746")
    assert voltaire.reference_links.count() == 2


@pytest.mark.django_db
def test_one_link_per_reference_site(voltaire, idref):
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")
    with pytest.raises(IntegrityError):
        BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="111")


@pytest.mark.django_db
def test_links_cascade_on_biography_delete(voltaire, idref):
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")
    voltaire.delete()
    assert BiographyReferenceSite.objects.count() == 0


@pytest.mark.django_db
def test_reference_site_protected_while_linked(voltaire, idref):
    BiographyReferenceSite.objects.create(biography=voltaire, reference_site=idref, identifier="026745135")
    with pytest.raises(ProtectedError):
        idref.delete()
