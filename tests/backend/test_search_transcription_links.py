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

    def test_public_home_and_latest_pages_link_to_readable_transcription(self):
        from django.utils import timezone
        trans = self.transcription(access_public=True, access_private=False, published_date=timezone.now())
        for path in ['/', '/publications/dernieres-transcriptions/']:
            response = self.client.get(path)
            self.assertContains(response, self.ref.title)
            self.assertContains(response, f'id="Transcription__{trans.pk}"')

    def test_missing_context_resolves_access_instead_of_hiding_every_link(self):
        private = self.transcription(access_private=True, access_owner=self.owner)
        public = self.transcription(access_private=False, access_public=True)
        for user, expected in [(AnonymousUser(), public), (self.owner, private), (self.other, public)]:
            body = render_to_string('fiches/bibliography_references/biblio_template.html', {'ref': self.ref, 'user': user})
            self.assertIn(f'id="Transcription__{expected.pk}"', body)

    def test_missing_user_is_anonymous_and_explicit_empty_map_stays_authoritative(self):
        private = self.transcription(access_private=True)
        public = self.transcription(access_private=False, access_public=True)
        for extra, expected in [({}, public), ({'search_transcription_links': {}}, None), ({'nolink': True}, None)]:
            body = render_to_string('fiches/bibliography_references/biblio_template.html', {'ref': self.ref, **extra})
            self.assertNotIn(f'id="Transcription__{private.pk}"', body)
            self.assertEqual(f'id="Transcription__{public.pk}"' in body, expected is not None)

    def test_legacy_allow_list_cannot_authorize_private_transcription(self):
        private = self.transcription(access_private=True)
        public = self.transcription(access_private=False, access_public=True)
        body = render_to_string('fiches/bibliography_references/biblio_template.html', {
            'ref': self.ref, 'user_accessible_trans': [self.ref.pk], 'user': AnonymousUser(),
        })
        self.assertNotIn(f'id="Transcription__{private.pk}"', body)
        self.assertIn(f'id="Transcription__{public.pk}"', body)

    def test_biblioref_never_reuses_another_readers_or_render_modes_html(self):
        from django.core.cache import cache
        from django.template import Context, Template
        cache.clear()
        trans = self.transcription(access_private=True, access_owner=self.owner)
        template = Template('{% load fiches_extras %}{% biblioref %}')
        for user, extra, expected in [
            (self.owner, {}, True), (AnonymousUser(), {}, False),
            (self.owner, {'nolink': True}, False), (self.owner, {}, True),
            (self.other, {}, False),
        ]:
            body = template.render(Context({'ref': self.ref, 'user': user, **extra}))
            self.assertEqual(f'id="Transcription__{trans.pk}"' in body, expected)
        trans.access_private = False
        trans.access_public = True
        trans.save()
        self.assertIn(f'id="Transcription__{trans.pk}"', template.render(Context({'ref': self.ref})))
        trans.access_private = True
        trans.save()
        self.assertNotIn(f'id="Transcription__{trans.pk}"', template.render(Context({'ref': self.ref})))

    def test_person_and_collection_references_follow_readers_access(self):
        from types import SimpleNamespace
        trans = self.transcription(access_private=True, access_owner=self.owner)
        collection = SimpleNamespace(name='Validation', bibliographies=SimpleNamespace(all=[self.ref]))
        for template, context in [
            ('fiches/display/person_bibliography.html', {'litt_prim': [self.ref]}),
            ('fiches/collections/details.html', {'coll': collection, 'coll_access': True, 'in_popup': True}),
        ]:
            for user, expected in [(self.owner, True), (AnonymousUser(), False), (self.owner, True)]:
                body = render_to_string(template, {**context, 'user': user})
                self.assertIn(self.ref.title, body)
                self.assertEqual(f'id="Transcription__{trans.pk}"' in body, expected)

    def test_project_print_keeps_public_transcription_link(self):
        from fiches.models import Project
        project = Project.objects.create(name='Validation', url='validation', owner=self.owner, publish=True)
        project.bibliographies.add(self.ref)
        trans = self.transcription(access_private=False, access_public=True)
        response = self.client.get(reverse('project-display-id', args=[project.pk]), {'print': 1})
        self.assertContains(response, f'id="Transcription__{trans.pk}"')

    def test_request_user_is_used_when_context_user_is_absent(self):
        from types import SimpleNamespace
        trans = self.transcription(access_private=True, access_owner=self.owner)
        body = render_to_string('fiches/bibliography_references/biblio_template.html', {
            'ref': self.ref, 'request': SimpleNamespace(user=self.owner),
        })
        self.assertIn(f'id="Transcription__{trans.pk}"', body)

    def test_place_references_forward_reader_through_isolated_includes(self):
        from django.core.paginator import Paginator
        from fiches.models import PlaceCategory, PlaceRecord
        category = PlaceCategory.objects.create(name='Ville/Village')
        place = PlaceRecord.objects.create(name='Validation', category=category)
        trans = self.transcription(access_private=True, access_owner=self.owner)
        for user, expected in [(self.owner, True), (AnonymousUser(), False)]:
            body = render_to_string('fiches/display/place.html', {
                'place': place, 'user': user, 'user_accessible_trans': [self.ref.pk],
                'tagged_writing': Paginator([self.ref], 20).page(1),
            })
            self.assertIn(self.ref.title, body)
            self.assertEqual(f'id="Transcription__{trans.pk}"' in body, expected)
