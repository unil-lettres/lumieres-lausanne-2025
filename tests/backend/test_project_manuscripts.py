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

"""Project manuscripts are bibliographies even without a transcription."""
from django.contrib.auth.models import Permission, User
from tempfile import TemporaryDirectory
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from fiches.models import Biblio, DocumentLanguage, DocumentType, Project, Transcription, DocumentFile, UserGroup


class ProjectManuscriptsTests(TestCase):
    def setUp(self):
        DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)
        kind = DocumentType.objects.create(id=5, name="Manuscrit", code=5)
        self.owner = User.objects.create_user("owner")
        self.other = User.objects.create_user("other")
        self.project = Project.objects.create(name="Projet témoin", url="temoin", owner=self.owner, publish=True)
        self.ref = Biblio.objects.create(title="Manuscrit sans transcription", document_type=kind, litterature_type="p", creator=self.owner)
        self.secondary = Biblio.objects.create(title="Secondaire témoin", document_type=kind, litterature_type="s", creator=self.owner)
        self.project.bibliographies.add(self.ref, self.secondary)

    def get(self, name, **query):
        return self.client.get(reverse(name, args=[self.project.pk]), query)

    def test_primary_list_includes_manuscript_without_transcription(self):
        response = self.get("project-littprim-list")
        self.assertContains(response, self.ref.title)
        self.assertContains(response, reverse("display-bibliography", args=[self.ref.pk]))
        self.assertNotContains(response, self.secondary.title)

    def test_bibliography_page_allows_missing_creator(self):
        Biblio.objects.filter(pk=self.ref.pk).update(creator=None)
        response = self.client.get(reverse("display-bibliography", args=[self.ref.pk]))
        self.assertContains(response, self.ref.title)
        self.assertContains(response, "Auteur de la fiche")

    def test_bibliography_creator_name_and_login_fallback(self):
        url = reverse("display-bibliography", args=[self.ref.pk])
        self.assertContains(self.client.get(url), ">owner</div>", html=False)
        self.owner.first_name = "Camille"
        self.owner.last_name = "Témoin"
        self.owner.save()
        self.assertContains(self.client.get(url), "Camille Témoin")

    def test_secondary_list_preserved(self):
        response = self.get("project-littsec-list")
        self.assertContains(response, self.secondary.title)
        self.assertNotContains(response, self.ref.title)

    def test_full_page_and_description_offer_primary_section(self):
        for name in ["project-display-id", "project-description"]:
            self.assertContains(self.get(name), "Littérature primaire")

    def test_print_includes_manuscript(self):
        self.assertContains(self.get("project-display-id", print=1), self.ref.title)

    def test_pagination_and_sort_do_not_lose_manuscripts(self):
        extra = Biblio.objects.create(title="Z autre manuscrit", document_type=self.ref.document_type, litterature_type="p", creator=self.owner)
        self.project.bibliographies.add(extra)
        first = self.get("project-littprim-list", nbitem=1, page=1, orderby="a")
        second = self.get("project-littprim-list", nbitem=1, page=2, orderby="a")
        self.assertContains(first, self.ref.title)
        self.assertNotContains(first, extra.title)
        self.assertContains(second, extra.title)

    def test_public_transcription_and_bibliography_both_remain(self):
        trans = Transcription.objects.create(manuscript_b=self.ref, author=self.owner, access_public=True, access_private=False)
        self.assertContains(self.get("project-transcription-list"), self.ref.title)
        self.assertContains(self.get("project-littprim-list"), reverse("transcription-display", args=[trans.pk]))
        self.assertContains(self.get("project-littprim-list"), reverse("display-bibliography", args=[self.ref.pk]))

    def test_private_transcription_does_not_gain_public_link(self):
        trans = Transcription.objects.create(manuscript_b=self.ref, author=self.owner, access_private=True, access_public=False)
        for response in [self.get("project-littprim-list"), self.get("project-display-id", print=1)]:
            self.assertContains(response, self.ref.title)
            self.assertNotContains(response, f'id="Transcription__{trans.pk}"')
        self.assertNotContains(self.get("project-transcription-list"), self.ref.title)

    def test_unpublished_project_hidden_in_every_read_route(self):
        self.project.publish = False
        self.project.save()
        routes = ["project-display-id", "project-description", "project-littprim-list", "project-littsec-list", "project-transcription-list"]
        for user in [None, self.other]:
            if user:
                self.client.force_login(user)
            for name in routes:
                self.assertEqual(self.get(name).status_code, 403)
        self.client.force_login(self.owner)
        for name in routes:
            self.assertEqual(self.get(name).status_code, 200)

    def test_owner_can_attach_without_transcription_but_other_cannot(self):
        self.project.bibliographies.remove(self.ref)
        permission = Permission.objects.get(codename="change_project")
        payload = {"item_type": "Biblio", "item_id": self.ref.pk, "proj_id": self.project.pk}
        self.other.user_permissions.add(permission)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("project-add-object"), payload).status_code, 400)
        self.assertFalse(self.project.bibliographies.filter(pk=self.ref.pk).exists())
        self.owner.user_permissions.add(permission)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(reverse("project-add-object"), payload).status_code, 200)
        self.assertTrue(self.project.bibliographies.filter(pk=self.ref.pk).exists())

    def test_pdf_route_preserves_public_and_group_permissions(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            pdf = DocumentFile.objects.create(title="PDF témoin", slug="pdf-temoin", access_public=True, access_owner=self.owner)
            pdf.file.save("temoin.pdf", ContentFile(b"%PDF-1.4\n%%EOF"))
            self.ref.documentfiles.add(pdf)
            response = self.client.get(pdf.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/pdf")
            response.close()
            pdf.access_public = False
            pdf.save()
            readers = UserGroup.objects.create(name="Lecteurs PDF", sort=1)
            pdf.access_groups.add(readers)
            self.assertEqual(self.client.get(pdf.get_absolute_url()).status_code, 403)
            self.client.force_login(self.other)
            self.assertEqual(self.client.get(pdf.get_absolute_url()).status_code, 403)
            readers.users.add(self.other)
            response = self.client.get(pdf.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            response.close()
