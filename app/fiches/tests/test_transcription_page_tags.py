"""
Copyright (C) 2025 Lumières.Lausanne
See docs/copyright.md
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from fiches.models.documents.document import Biblio, Transcription, DocumentType


class TranscriptionPageTagTest(TestCase):
    """Test the page tag functionality in transcription display."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        # Create a document type for testing
        self.doc_type = DocumentType.objects.create(
            type="manuscrit",
            verbose_name="Manuscrit"
        )
        
        # Create a bibliography entry
        self.biblio = Biblio.objects.create(
            title="Test Manuscript",
            litterature_type="p",
            document_type=self.doc_type
        )
        
        # Create a transcription with page tags
        self.transcription = Transcription.objects.create(
            manuscript_b=self.biblio,
            text="<p>This is page 1 content.</p><<5>><p>This is page 5 content.</p><<10>><p>This is page 10.</p>",
            author=self.user,
            access_public=True
        )

    def test_transcription_display_includes_page_tag_script(self):
        """Test that the transcription display template includes the page tag processing script."""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.get(
            reverse("transcription-display", args=[self.transcription.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that the page tag processing function is included
        self.assertContains(response, "processPageTags")
        self.assertContains(response, "syncToPage")
        
    def test_transcription_display_includes_css(self):
        """Test that the transcription display template includes page tag CSS."""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.get(
            reverse("transcription-display", args=[self.transcription.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that the CSS file is included
        self.assertContains(response, "tinyMCE_transcripts.css")

    def test_transcription_field_template_renders(self):
        """Test that the transcription_field template renders without errors."""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.get(
            reverse("transcription-display", args=[self.transcription.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that the transcription data is included
        self.assertContains(response, "transcription-data")
        
        # Check that the page tag content is present (as raw HTML)
        self.assertContains(response, "This is page 1 content")
        self.assertContains(response, "This is page 5 content")
