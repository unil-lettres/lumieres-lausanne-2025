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

"""Readable manuscript title links, independently of transcription primary keys."""
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from fiches.models import Biblio, DocumentLanguage, DocumentType, Transcription, UserGroup
from fiches.views.search import _search_transcription_links

class SearchTranscriptionLinksTests(TestCase):
    def setUp(self):
        DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)
        kind = DocumentType.objects.create(id=5, name="Manuscrit", code=5)
        self.ref = Biblio.objects.create(id=101, title="Validation couleur", document_type=kind, litterature_type="p")
        self.owner = User.objects.create_user("owner")
        self.other = User.objects.create_user("other")

    def transcription(self, **kwargs):
        return Transcription.objects.create(manuscript_b=self.ref, author=self.owner, **kwargs)

    def rendered(self, user, **extra):
        return render_to_string("fiches/bibliography_references/biblio_template.html", {
            "ref": self.ref,
            "search_transcription_links": _search_transcription_links(user, [self.ref.pk]),
            **extra,
        })

    def test_public_link_uses_transcription_not_manuscript_id(self):
        trans = self.transcription(access_public=True, access_private=False)
        self.assertNotEqual(trans.pk, self.ref.pk)
        self.assertIn(reverse("transcription-display", args=[trans.pk]), self.rendered(AnonymousUser()))

    def test_no_transcription_keeps_title_and_bibliography_link(self):
        body = self.rendered(AnonymousUser())
        self.assertIn("Validation couleur", body)
        self.assertNotIn('id="Transcription__', body)
        self.assertIn(reverse("display-bibliography", args=[self.ref.pk]), body)

    def test_private_is_not_linked_for_anonymous_or_unrelated_user(self):
        self.transcription(access_private=True, access_public=True, access_owner=self.owner)
        for user in [AnonymousUser(), self.other]:
            self.assertNotIn('id="Transcription__', self.rendered(user))

    def test_private_owner_gets_link(self):
        trans = self.transcription(access_private=True, access_owner=self.owner)
        self.assertIn(f'id="Transcription__{trans.pk}"', self.rendered(self.owner))

    def test_author_without_access_is_not_enough(self):
        self.transcription(access_private=True)
        self.assertNotIn('id="Transcription__', self.rendered(self.owner))

    def test_full_access_permissions_match_display(self):
        trans = self.transcription(access_private=True)
        for codename in ["change_any_transcription", "access_unpublished_transcription"]:
            user = User.objects.create_user(codename)
            user.user_permissions.add(Permission.objects.get(codename=codename))
            self.assertIn(f'id="Transcription__{trans.pk}"', self.rendered(user))

    def test_group_access_direct_and_indirect(self):
        trans = self.transcription(access_private=False)
        group = UserGroup.objects.create(name="Readers", sort=1)
        trans.access_groups.add(group)
        group.users.add(self.other)
        self.assertIn(f'id="Transcription__{trans.pk}"', self.rendered(self.other))
        group.users.clear()
        django_group = Group.objects.create(name="Readers")
        group.groups.add(django_group)
        self.other.groups.add(django_group)
        self.assertIn(f'id="Transcription__{trans.pk}"', self.rendered(self.other))

    def test_private_first_public_second_in_both_title_formats(self):
        private = self.transcription(access_private=True)
        public = self.transcription(access_private=False, access_public=True)
        for book_title in ["", "Recueil"]:
            self.ref.book_title = book_title
            body = self.rendered(AnonymousUser())
            self.assertIn(f'id="Transcription__{public.pk}"', body)
            self.assertNotIn(f'id="Transcription__{private.pk}"', body)

    def test_nolink_suppresses_transcription_link(self):
        self.transcription(access_private=False, access_public=True)
        self.assertNotIn('id="Transcription__', self.rendered(AnonymousUser(), nolink=True))

    def test_nonsearch_context_preserves_manuscript_id_contract(self):
        trans = self.transcription(access_private=False, access_public=True)
        for allowed, expected in [([self.ref.pk], True), ([], False), (None, False), (True, True)]:
            body = render_to_string("fiches/bibliography_references/biblio_template.html", {
                "ref": self.ref, "user_accessible_trans": allowed,
            })
            self.assertEqual(f'id="Transcription__{trans.pk}"' in body, expected)

    def test_advanced_search_renders_exact_readable_link(self):
        private = self.transcription(access_private=True)
        public = self.transcription(access_private=False, access_public=True)
        for query in [{}, {"dtT": "1"}]:
            response = self.client.get("/chercher/bibliographie/", {
                "x0_fld": "title", "x0_val": "Validation couleur", **query,
            })
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'id="Transcription__{public.pk}"')
            self.assertNotContains(response, f'id="Transcription__{private.pk}"')
