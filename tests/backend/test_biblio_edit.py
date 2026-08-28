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

"""Regression tests for bibliographic fiche editing."""

import datetime

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from fiches.models import ActivityLog
from fiches.models.contributions import PrimaryKeyword
from fiches.models.documents.document import (
    Biblio,
    ContributionDoc,
    DocumentLanguage,
    DocumentType,
)
from fiches.models.person.person import Person
from fiches.views.search import _activity_log_object_ids_for_date_range


class ContributionFormsetRenderingTest(TestCase):
    """Test the rendering of the author field in the bibliography edit form."""

    def setUp(self):
        # Lookup rows the Biblio model assumes exist: DocumentType pk=1
        # and a DocumentLanguage named "Français" (get_default_language).
        self.doc_type = DocumentType.objects.create(id=1, name="Test type", code=1)
        DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)

        self.user = User.objects.create(username="testuser")
        self.user.user_permissions.add(
            Permission.objects.get(codename="change_biblio"),
            Permission.objects.get(codename="change_any_biblio"),
        )
        self.client.force_login(self.user)

        self.person = Person.objects.create(name="Barbeyrac, Jean")
        self.biblio = Biblio.objects.create(
            title="Test Biblio",
            litterature_type="p",
            document_type=self.doc_type,
        )
        self.contribution = ContributionDoc.objects.create(person=self.person, document=self.biblio)

    def test_author_field_renders_name_span(self):
        response = self.client.get(reverse("bibliography-edit", args=[self.biblio.id]))
        self.assertContains(response, '<span class="name">Barbeyrac, Jean</span>', html=True)
        self.assertContains(
            response,
            f'<input type="hidden" name="contributiondoc_set-0-person" value="{self.person.id}">',
            html=True,
        )


class BiblioCreateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("editor", password="secret")
        for codename in ("add_biblio", "change_biblio"):
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label="fiches",
                    content_type__model="biblio",
                    codename=codename,
                )
            )
        self.language = DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)
        self.document_type = DocumentType.objects.create(id=3, name="Article de revue", code=3)
        self.keyword = PrimaryKeyword.objects.create(word="Test keyword")
        self.client.force_login(self.user)

    def _article_payload(self):
        return {
            "document_type": "3",
            "litterature_type": "s",
            "title": "Test article",
            "journal_title": "Test journal",
            "language": str(self.language.id),
            "creator": str(self.user.id),
            "subj_primary_kw": [str(self.keyword.id)],
            "notes-TOTAL_FORMS": "0",
            "notes-INITIAL_FORMS": "0",
            "notes-MIN_NUM_FORMS": "0",
            "notes-MAX_NUM_FORMS": "1000",
            "contributiondoc_set-TOTAL_FORMS": "0",
            "contributiondoc_set-INITIAL_FORMS": "0",
            "contributiondoc_set-MIN_NUM_FORMS": "0",
            "contributiondoc_set-MAX_NUM_FORMS": "1000",
        }

    def test_get_create_url_does_not_create_blank_biblio(self):
        response = self.client.get(reverse("bibliography-create", kwargs={"doctype": "3"}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Biblio.objects.count(), 0)

    def test_post_create_url_creates_one_biblio(self):
        response = self.client.post(
            reverse("bibliography-create", kwargs={"doctype": "3"}),
            self._article_payload(),
        )

        self.assertEqual(Biblio.objects.count(), 1)
        biblio = Biblio.objects.get()
        self.assertEqual(biblio.title, "Test article")
        self.assertEqual(biblio.litterature_type, "s")
        self.assertEqual(biblio.document_type_id, 3)
        self.assertEqual(biblio.creator, self.user)
        self.assertRedirects(
            response,
            reverse("display-bibliography", args=[biblio.id]),
            fetch_redirect_response=False,
        )


class BiblioActivityLogDateTest(TestCase):
    def test_registration_date_filter_includes_whole_end_day(self):
        user = User.objects.create_user("editor")
        activity = ActivityLog.objects.create(model_name="Biblio", object_id=42, user=user)
        ActivityLog.objects.filter(pk=activity.pk).update(
            date=timezone.make_aware(datetime.datetime(2026, 7, 3, 16, 31))
        )

        object_ids = _activity_log_object_ids_for_date_range(
            "Biblio",
            datetime.date(2026, 7, 3),
            datetime.date(2026, 7, 3),
        )

        self.assertEqual(list(object_ids), [42])
