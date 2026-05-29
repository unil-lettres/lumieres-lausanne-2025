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

from django.contrib.auth.models import Permission, User
from django.http import QueryDict
from django.test import TestCase

from fiches.forms import BiblioForm
from fiches.models.contributions import PrimaryKeyword
from fiches.models.documents import Biblio, DocumentLanguage
from fiches.models.documents.document import DocumentType
from fiches.models.person import Person


class BiblioSubjectPersonFormTest(TestCase):
    def setUp(self):
        DocumentType.objects.create(id=1, name="Test type", code=1)
        self.keyword = PrimaryKeyword.objects.create(word="Test keyword")
        self.language = DocumentLanguage.objects.create(name="Français", ordering=1)

    def _post_data(self, subj_person, litterature_type="p"):
        # BiblioForm.__init__ calls self.data.copy().getlist(...), so the
        # form expects a QueryDict (request.POST-style) — not a plain dict.
        data = QueryDict("", mutable=True)
        data.update(
            {
                "title": "Test Biblio",
                "document_type": "1",
                "litterature_type": litterature_type,
                "language": str(self.language.pk),
                "subj_primary_kw": str(self.keyword.pk),
                "subj_person": subj_person,
            }
        )
        return data

    def test_new_subject_person_is_created_for_listitem_users(self):
        user = User.objects.create_user("editor")
        user.user_permissions.add(Permission.objects.get(codename="can_add_listitem"))
        form = BiblioForm(
            data=self._post_data("|ZZZ Test Personne Inconnue 20260507"),
            instance=Biblio(),
            user=user,
        )

        self.assertTrue(form.is_valid(), form.errors)

        person = Person.objects.get(name="ZZZ Test Personne Inconnue 20260507")
        self.assertIn(person, form.cleaned_data["subj_person"])
        self.assertFalse(person.modern)
        self.assertFalse(person.may_have_biography)

    def test_new_subject_person_is_not_secondary_for_secondary_literature(self):
        user = User.objects.create_user("editor")
        user.user_permissions.add(Permission.objects.get(codename="can_add_listitem"))
        form = BiblioForm(
            data=self._post_data(
                "|ZZZ Test Sujet Non Secondaire 20260507",
                litterature_type="s",
            ),
            instance=Biblio(),
            user=user,
        )

        self.assertTrue(form.is_valid(), form.errors)

        person = Person.objects.get(name="ZZZ Test Sujet Non Secondaire 20260507")
        self.assertIn(person, form.cleaned_data["subj_person"])
        self.assertFalse(person.modern)
        self.assertFalse(person.may_have_biography)

    def test_new_subject_person_is_rejected_without_permission(self):
        user = User.objects.create_user("viewer")
        form = BiblioForm(
            data=self._post_data("|ZZZ Test Personne Refusee"),
            instance=Biblio(),
            user=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("ZZZ Test Personne Refusee", str(form.errors["subj_person"]))

    def test_double_pipe_subject_person_is_normalized(self):
        user = User.objects.create_user("editor")
        user.user_permissions.add(Permission.objects.get(codename="can_add_listitem"))
        form = BiblioForm(
            data=self._post_data("||ZZZ Test Personne Double Pipe"),
            instance=Biblio(),
            user=user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(Person.objects.filter(name="ZZZ Test Personne Double Pipe").exists())
        self.assertFalse(Person.objects.filter(name="|ZZZ Test Personne Double Pipe").exists())
