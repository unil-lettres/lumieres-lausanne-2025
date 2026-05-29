from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from fiches.forms import TranscriptionForm
from fiches.models.documents.document import Transcription


class TranscriptionFormDefaultsTest(SimpleTestCase):
    def test_published_by_defaults_to_configured_user_when_empty(self):
        instance = Transcription()
        with patch("fiches.forms.get_default_publisher_user", return_value=SimpleNamespace(pk=12)):
            form = TranscriptionForm(instance=instance)
        self.assertEqual(form.initial.get("published_by"), 12)
