"""
Copyright (C) 2025 Lumières.Lausanne
See docs/copyright.md
"""

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from fiches.models.documents.document import (
    Biblio,
    ContributionDoc,
    DocumentLanguage,
    DocumentType,
)
from fiches.models.person.person import Person


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
