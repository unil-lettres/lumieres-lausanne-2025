"""
Copyright (C) 2025 Lumières.Lausanne
See docs/copyright.md
"""

from django.test import TestCase
from django.urls import reverse
from fiches.models.documents.document import Biblio, ContributionDoc
from fiches.models.person.person import Person
from django.contrib.auth.models import User

class ContributionFormsetRenderingTest(TestCase):
    """Test the rendering of the author field in the bibliography edit form."""
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.person = Person.objects.create(name="Barbeyrac, Jean")
        self.biblio = Biblio.objects.create(title="Test Biblio", litterature_type="p", document_type_id=1)
        self.contribution = ContributionDoc.objects.create(person=self.person, document=self.biblio)

    def test_author_field_renders_name_span(self):
        response = self.client.get(reverse("biblio-edit", args=[self.biblio.id]))
        self.assertContains(response, '<span class="name">Barbeyrac, Jean</span>', html=True)
        self.assertContains(response, f'<input type="hidden" name="contributiondoc_set-0-person" value="{self.person.id}">', html=True)
