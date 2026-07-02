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

"""Tests for the manuscript "Nature du document" field (admin-managed dropdown)."""

import importlib

from django.http import QueryDict
from django.test import TestCase
from fiches.forms import BiblioForm
from fiches.models.contributions import PrimaryKeyword
from fiches.models.documents import Biblio, DocumentLanguage, DocumentNature
from fiches.models.documents.document import DocumentType, ManuscriptType

_migration = importlib.import_module("fiches.migrations.0019_document_nature")

DOCTYPE_MANUSCRIPT = 5


class BiblioDocumentNatureFormTest(TestCase):
    def setUp(self):
        self.doctype = DocumentType.objects.create(id=DOCTYPE_MANUSCRIPT, name="Manuscrit", code=2)
        self.keyword = PrimaryKeyword.objects.create(word="Test keyword")
        self.language = DocumentLanguage.objects.create(name="Français", ordering=1)
        self.nature = DocumentNature.objects.create(name="Lettre autographe", sorting=1)
        self.manuscript_type = ManuscriptType.objects.create(name="Lettre", sorting=1)

    def _post_data(self, **extra):
        data = QueryDict("", mutable=True)
        data.update(
            {
                "title": "Test Biblio",
                "document_type": str(self.doctype.pk),
                "litterature_type": "p",
                "language": str(self.language.pk),
                "subj_primary_kw": str(self.keyword.pk),
                "manuscript_type": str(self.manuscript_type.pk),
            }
        )
        data.update(extra)
        return data

    def test_form_exposes_document_nature_choice(self):
        form = BiblioForm(instance=Biblio())
        self.assertIn("document_nature", form.fields)
        self.assertIn(self.nature, form.fields["document_nature"].queryset)

    def test_manuscript_saves_its_document_nature(self):
        form = BiblioForm(data=self._post_data(document_nature=str(self.nature.pk)), instance=Biblio())
        self.assertTrue(form.is_valid(), form.errors)
        biblio = form.save()
        self.assertEqual(biblio.document_nature, self.nature)


class _FakeApps:
    def get_model(self, app_label, model_name):  # noqa: ARG002
        return DocumentType


class DocumentNatureExclusiveFieldsTest(TestCase):
    """The data migration attaches "document_nature" to the manuscript document type only."""

    def test_add_is_idempotent_and_scoped_then_reversible(self):
        manuscript = DocumentType.objects.create(name="Manuscrit", code=2, exclusive_fields="depot,cote")
        other = DocumentType.objects.create(name="Livre", code=3, exclusive_fields="publisher")

        _migration.add_nature_exclusive(_FakeApps(), None)
        _migration.add_nature_exclusive(_FakeApps(), None)  # idempotent
        manuscript.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(manuscript.exclusive_fields.split(",").count("document_nature"), 1)
        self.assertNotIn("document_nature", other.exclusive_fields.split(","))

        _migration.remove_nature_exclusive(_FakeApps(), None)
        manuscript.refresh_from_db()
        self.assertNotIn("document_nature", manuscript.exclusive_fields.split(","))
        self.assertIn("depot", manuscript.exclusive_fields.split(","))
