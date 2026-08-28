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

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from fiches.models.contributions.keyword import PrimaryKeyword, SecondaryKeyword
from fiches.models.documents.document import Biblio, DocumentLanguage, DocumentType, Transcription


class AdvancedSearchKeywordBooleanTest(TestCase):
    def setUp(self):
        DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)
        self.document_type = DocumentType.objects.create(name="Livre", code=1)
        self.religion = PrimaryKeyword.objects.create(word="Religion")
        self.history = PrimaryKeyword.objects.create(word="Histoire")
        self.protestantism = SecondaryKeyword.objects.create(
            word="Protestantisme",
            primary_keyword=self.religion,
        )

        self.title_only = self._biblio("Voltaire seul")
        self.religion_only = self._biblio("Traité religieux", primary=self.religion)
        self.history_only = self._biblio("Traité historique", primary=self.history)
        self.both_keywords = self._biblio("Religion et histoire", primary=self.religion)
        self.both_keywords.subj_primary_kw.add(self.history)
        self.secondary_only = self._biblio("Étude protestante", secondary=self.protestantism)
        self.unrelated = self._biblio("Sans rapport")

    def _biblio(self, title, primary=None, secondary=None):
        biblio = Biblio.objects.create(
            title=title,
            litterature_type="p",
            document_type=self.document_type,
        )
        if primary is not None:
            biblio.subj_primary_kw.add(primary)
        if secondary is not None:
            biblio.subj_secondary_kw.add(secondary)
        return biblio

    def _search_ids(self, **params):
        response = self.client.get(reverse("search-biblio"), params)
        self.assertEqual(response.status_code, 200)
        return {biblio.pk for biblio in response.context["page"].object_list}

    def test_standalone_or_filters_instead_of_returning_every_bibliography(self):
        self.assertEqual(
            self._search_ids(kw0_op="or", kw0_p=self.religion.pk),
            {self.religion_only.pk, self.both_keywords.pk},
        )

    def test_keyword_or_broadens_an_existing_text_filter(self):
        self.assertEqual(
            self._search_ids(
                x0_fld="title",
                x0_val="Voltaire",
                kw0_op="or",
                kw0_p=self.religion.pk,
            ),
            {self.title_only.pk, self.religion_only.pk, self.both_keywords.pk},
        )

    def test_or_between_primary_keywords_returns_the_union(self):
        self.assertEqual(
            self._search_ids(
                kw0_op="and",
                kw0_p=self.religion.pk,
                kw1_op="or",
                kw1_p=self.history.pk,
            ),
            {self.religion_only.pk, self.history_only.pk, self.both_keywords.pk},
        )

    def test_or_works_for_a_secondary_keyword(self):
        self.assertEqual(
            self._search_ids(
                x0_fld="title",
                x0_val="Voltaire",
                kw0_op="or",
                kw0_s=self.protestantism.pk,
            ),
            {self.title_only.pk, self.secondary_only.pk},
        )

    def test_and_and_not_keep_narrowing_the_current_results(self):
        self.assertEqual(
            self._search_ids(
                kw0_op="and",
                kw0_p=self.religion.pk,
                kw1_op="and",
                kw1_p=self.history.pk,
            ),
            {self.both_keywords.pk},
        )
        self.assertEqual(
            self._search_ids(kw0_op="not", kw0_p=self.religion.pk),
            {
                self.title_only.pk,
                self.history_only.pk,
                self.secondary_only.pk,
                self.unrelated.pk,
            },
        )


class AdvancedSearchBulkAccessVisibilityTest(TestCase):
    def _user_with_permissions(self, username, *codenames):
        user = get_user_model().objects.create_user(username=username, password="pw")
        user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="fiches",
                codename__in=codenames,
            )
        )
        return user

    def _manuscript(self, title):
        language = DocumentLanguage.objects.create(
            name="Français",
            code="fr",
            ordering=1,
        )
        manuscript_type = DocumentType.objects.create(name="Manuscrit", code=5)
        return Biblio.objects.create(
            title=title,
            document_type=manuscript_type,
            language=language,
            litterature_type="p",
        )

    def test_bulk_transcription_access_button_is_hidden_even_from_superusers(self):
        user = get_user_model().objects.create_superuser(
            username="director",
            email="director@example.test",
            password="pw",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("search-biblio"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Changer accès trans.")
        self.assertNotContains(response, "search_action=trans_access")

    def test_civiliste_permissions_cannot_open_bulk_access_action(self):
        user = self._user_with_permissions("civiliste", "change_any_transcription")
        self.client.force_login(user)

        response = self.client.get(reverse("search-biblio"), {"search_action": "trans_access"})

        self.assertEqual(response.status_code, 403)

    def test_civiliste_permissions_cannot_publish_through_bulk_endpoint(self):
        user = self._user_with_permissions("civiliste", "change_any_transcription")
        manuscript = self._manuscript("Manuscrit privé")
        transcription = Transcription.objects.create(
            manuscript_b=manuscript,
            author=user,
            access_owner=user,
            access_private=True,
            access_public=False,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("trans-change-access"),
            {"transcriptions": [manuscript.pk], "access_public": "on"},
        )

        self.assertEqual(response.status_code, 403)
        transcription.refresh_from_db()
        self.assertFalse(transcription.access_public)
        self.assertTrue(transcription.access_private)
        self.assertIsNone(transcription.published_date)
        self.assertIsNone(transcription.published_by)

    def test_publisher_with_global_change_permission_can_use_bulk_endpoint(self):
        user = self._user_with_permissions(
            "director",
            "change_any_transcription",
            "publish_transcription",
        )
        manuscript = self._manuscript("Manuscrit à publier")
        transcription = Transcription.objects.create(
            manuscript_b=manuscript,
            author=user,
            access_owner=user,
            access_private=True,
            access_public=False,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("trans-change-access"),
            {"transcriptions": [manuscript.pk], "access_public": "on"},
        )

        self.assertEqual(response.status_code, 302)
        transcription.refresh_from_db()
        self.assertTrue(transcription.access_public)
        self.assertFalse(transcription.access_private)
        self.assertIsNotNone(transcription.published_date)
        self.assertEqual(transcription.published_by, user)
