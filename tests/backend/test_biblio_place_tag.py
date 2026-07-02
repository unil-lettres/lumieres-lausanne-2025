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

"""Tests for place tagging on the biblio location fields (§4.1 / §4.2)."""

import importlib

from django.http import QueryDict
from django.test import TestCase
from fiches.forms import BiblioForm
from fiches.models.contributions import PrimaryKeyword
from fiches.models.documents import Biblio, DocumentLanguage
from fiches.models.documents.document import DocumentType
from fiches.place_tag import PlaceTagWidget

# The migration module name starts with a digit, so it cannot be imported with the
# usual statement; load it explicitly to reach its data-migration helpers.
_migration = importlib.import_module("fiches.migrations.0016_biblio_place_tagging")


def _place_tag(place_id, label):
    return (
        f'<a class="ll-tag ll-tag-place" data-place="{place_id}" '
        f'href="/fiches/lieu/{place_id}/" title="{label}">{label}</a>'
    )


class BiblioPlaceTagFormTest(TestCase):
    def setUp(self):
        self.doctype = DocumentType.objects.create(id=1, name="Test type", code=1)
        self.keyword = PrimaryKeyword.objects.create(word="Test keyword")
        self.language = DocumentLanguage.objects.create(name="Français", ordering=1)

    def _post_data(self, **extra):
        data = QueryDict("", mutable=True)
        data.update(
            {
                "title": "Test Biblio",
                "document_type": str(self.doctype.pk),
                "litterature_type": "p",
                "language": str(self.language.pk),
                "subj_primary_kw": str(self.keyword.pk),
            }
        )
        data.update(extra)
        return data

    def test_location_fields_use_the_place_tag_widget(self):
        form = BiblioForm(instance=Biblio())
        for name in ("place", "place2", "destination"):
            self.assertIsInstance(form.fields[name].widget, PlaceTagWidget, name)

    def test_place_tag_round_trips_through_the_form(self):
        tag = _place_tag(42, "Lausanne")
        form = BiblioForm(data=self._post_data(place=tag), instance=Biblio())
        self.assertTrue(form.is_valid(), form.errors)
        biblio = form.save()
        self.assertEqual(biblio.place, tag)

    def test_destination_round_trips_through_the_form(self):
        tag = _place_tag(7, "Genève")
        form = BiblioForm(data=self._post_data(destination=tag), instance=Biblio())
        self.assertTrue(form.is_valid(), form.errors)
        biblio = form.save()
        self.assertEqual(biblio.destination, tag)


class _FakeApps:
    """Minimal apps registry returning the real DocumentType for the data migration."""

    def get_model(self, app_label, model_name):  # noqa: ARG002
        return DocumentType


class BiblioDestinationExclusiveFieldsTest(TestCase):
    """The data migration attaches "destination" to the manuscript document type only."""

    def test_add_is_idempotent_and_scoped_then_reversible(self):
        manuscript = DocumentType.objects.create(name="Manuscrit", code=2, exclusive_fields="depot,cote")
        other = DocumentType.objects.create(name="Livre", code=3, exclusive_fields="publisher")

        _migration.add_destination_exclusive(_FakeApps(), None)
        _migration.add_destination_exclusive(_FakeApps(), None)  # idempotent
        manuscript.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(manuscript.exclusive_fields.split(",").count("destination"), 1)
        self.assertNotIn("destination", other.exclusive_fields.split(","))

        _migration.remove_destination_exclusive(_FakeApps(), None)
        manuscript.refresh_from_db()
        self.assertNotIn("destination", manuscript.exclusive_fields.split(","))
        self.assertIn("depot", manuscript.exclusive_fields.split(","))
