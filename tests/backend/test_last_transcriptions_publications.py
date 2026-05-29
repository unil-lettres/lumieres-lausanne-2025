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

"""
Tests for /publications/dernieres-transcriptions/ ordering and limit.
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from fiches.models.documents.document import (
    Biblio,
    DocumentLanguage,
    DocumentType,
    Transcription,
)


class LastTranscriptionsPublicationsTest(TestCase):
    def setUp(self):
        # Biblio.document_type FK + get_default_language() lookup
        DocumentType.objects.create(id=1, name="Test type", code=1)
        DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)

    def _create_public_transcription(self, index, published_date):
        biblio = Biblio.objects.create(
            title=f"Published {index:03d}",
            litterature_type="p",
            document_type_id=1,
        )
        return Transcription.objects.create(
            manuscript_b=biblio,
            access_public=True,
            access_private=False,
            published_date=published_date,
        )

    def test_latest_published_by_date_orders_descending(self):
        now = timezone.now()
        t1 = self._create_public_transcription(1, now - timedelta(days=3))
        t2 = self._create_public_transcription(2, now - timedelta(days=1))
        t3 = self._create_public_transcription(3, now - timedelta(days=2))
        self._create_public_transcription(4, None)

        ordered_ids = list(Transcription.objects.latest_published_by_date(10).values_list("id", flat=True))
        self.assertEqual(ordered_ids, [t2.id, t3.id, t1.id])

    def test_last_transcriptions_page_uses_50_items_max(self):
        now = timezone.now()
        for i in range(60):
            self._create_public_transcription(i, now - timedelta(minutes=i))

        response = self.client.get(reverse("last-transcriptions"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["last_transcriptions"]), 50)
