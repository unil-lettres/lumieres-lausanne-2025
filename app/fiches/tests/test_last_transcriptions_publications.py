"""
Tests for /publications/dernieres-transcriptions/ ordering and limit.
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from fiches.models.documents.document import Biblio, Transcription


class LastTranscriptionsPublicationsTest(TestCase):
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

        ordered_ids = list(
            Transcription.objects.latest_published_by_date(10).values_list("id", flat=True)
        )
        self.assertEqual(ordered_ids, [t2.id, t3.id, t1.id])

    def test_last_transcriptions_page_uses_50_items_max(self):
        now = timezone.now()
        for i in range(60):
            self._create_public_transcription(i, now - timedelta(minutes=i))

        response = self.client.get(reverse("last-transcriptions"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["last_transcriptions"]), 50)
