from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from fiches.models.documents.document import Biblio, Transcription


class TranscriptionCreateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("editor", password="secret")
        add_perm = Permission.objects.get(
            content_type__app_label="fiches",
            content_type__model="transcription",
            codename="add_transcription",
        )
        change_perm = Permission.objects.get(
            content_type__app_label="fiches",
            content_type__model="transcription",
            codename="change_transcription",
        )
        self.user.user_permissions.add(add_perm, change_perm)
        self.biblio = Biblio.objects.create(
            title="Manuscript with transcription",
            litterature_type="p",
            document_type_id=5,
            creator=self.user,
        )
        self.client.force_login(self.user)

    def test_biblio_edit_page_does_not_render_nested_transcription_form(self):
        for codename in ("change_biblio", "add_transcription"):
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label="fiches",
                    codename=codename,
                )
            )

        response = self.client.get(reverse("bibliography-edit", args=[self.biblio.id]))

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        main_form_start = html.index('id="biblio-form-id"')
        main_form_end = html.index("</form>", main_form_start)
        main_form = html[main_form_start:main_form_end]
        self.assertNotIn("<form", main_form)
        self.assertIn(reverse("transcription-b-add", args=[self.biblio.id]), main_form)

    def test_get_create_url_does_not_create_transcription(self):
        response = self.client.get(reverse("transcription-b-add", args=[self.biblio.id]))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Transcription.objects.count(), 0)

    def test_post_create_url_creates_one_transcription_and_redirects_to_edit(self):
        response = self.client.post(reverse("transcription-b-add", args=[self.biblio.id]))

        self.assertEqual(Transcription.objects.count(), 1)
        transcription = Transcription.objects.get()
        self.assertEqual(transcription.manuscript_b, self.biblio)
        self.assertEqual(transcription.author, self.user)
        self.assertEqual(transcription.access_owner, self.user)
        self.assertRedirects(
            response,
            reverse("transcription-edit", args=[transcription.id]),
            fetch_redirect_response=False,
        )
