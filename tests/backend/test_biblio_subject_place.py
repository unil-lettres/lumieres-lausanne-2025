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

"""Tests for the "Lieu(x)" subject field on the biblio fiche (§4.3)."""

from django.http import QueryDict
from django.test import TestCase
from fiches.forms import BiblioForm
from fiches.models.contributions import PrimaryKeyword
from fiches.models.documents import Biblio, DocumentLanguage
from fiches.models.documents.document import DocumentType
from fiches.models.misc import PlaceCategory, PlaceRecord


class BiblioSubjectPlaceFormTest(TestCase):
    def setUp(self):
        self.doctype = DocumentType.objects.create(id=1, name="Test type", code=1)
        self.keyword = PrimaryKeyword.objects.create(word="Test keyword")
        self.language = DocumentLanguage.objects.create(name="Français", ordering=1)
        category = PlaceCategory.objects.create(name="Ville/Village")
        self.place = PlaceRecord.objects.create(name="Lausanne", category=category)

    def _post_data(self, subj_place):
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
        # subj_place is a multi-value field (one hidden input per chip).
        data.setlist("subj_place", subj_place if isinstance(subj_place, list) else [subj_place])
        return data

    def test_selecting_a_place_by_id_links_it(self):
        form = BiblioForm(data=self._post_data(str(self.place.pk)), instance=Biblio())
        self.assertTrue(form.is_valid(), form.errors)
        biblio = form.save()
        biblio.subj_place.set(form.cleaned_data["subj_place"])
        self.assertEqual(list(biblio.subj_place.all()), [self.place])

    def test_accepts_the_id_label_chip_payload(self):
        # The DynamicList renders pre-existing entries as "id|label" on edit.
        form = BiblioForm(data=self._post_data(f"{self.place.pk}|Lausanne (Ville/Village)"), instance=Biblio())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn(self.place, form.cleaned_data["subj_place"])

    def test_unknown_place_is_rejected(self):
        form = BiblioForm(data=self._post_data("999999"), instance=Biblio())
        self.assertFalse(form.is_valid())
        self.assertIn("subj_place", form.errors)
