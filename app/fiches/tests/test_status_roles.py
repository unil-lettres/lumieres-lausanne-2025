from io import StringIO

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import RequestFactory, TestCase

from fiches.admin import CustomUserAdmin


class SyncStatusRolesTest(TestCase):
    def setUp(self):
        self.directeurs = Group.objects.create(name="directeurs")
        self.doctorants = Group.objects.create(name="doctorants")

    def _director_permission_codenames(self):
        return set(self.directeurs.permissions.values_list("codename", flat=True))

    def _doctorant_permission_codenames(self):
        return set(self.doctorants.permissions.values_list("codename", flat=True))

    def test_apply_grants_user_profile_permissions_to_directors(self):
        out = StringIO()

        call_command("sync_status_roles", apply=True, stdout=out)
        self.directeurs.refresh_from_db()

        self.assertTrue(
            {
                "add_userprofile",
                "change_userprofile",
                "delete_userprofile",
                "view_userprofile",
                "change_collection_owner",
            }.issubset(self._director_permission_codenames())
        )

    def test_dry_run_does_not_grant_user_profile_permissions_to_directors(self):
        out = StringIO()

        call_command("sync_status_roles", stdout=out)
        self.directeurs.refresh_from_db()

        self.assertFalse(
            {
                "add_userprofile",
                "change_userprofile",
                "delete_userprofile",
                "view_userprofile",
            }
            & self._director_permission_codenames()
        )

    def test_apply_grants_transcription_permissions_to_doctorants(self):
        out = StringIO()

        call_command("sync_status_roles", apply=True, stdout=out)
        self.doctorants.refresh_from_db()

        self.assertTrue(
            {
                "add_documentfile",
                "change_documentfile",
                "delete_documentfile",
                "access_unpublished_transcription",
                "change_any_transcription",
            }.issubset(self._doctorant_permission_codenames())
        )

    def test_dry_run_does_not_grant_transcription_permissions_to_doctorants(self):
        out = StringIO()

        call_command("sync_status_roles", stdout=out)
        self.doctorants.refresh_from_db()

        self.assertFalse(
            {
                "access_unpublished_transcription",
                "change_any_transcription",
            }
            & self._doctorant_permission_codenames()
        )

    def test_user_profile_inline_is_available_to_directors_after_sync(self):
        user = User.objects.create_user("director", is_staff=True)
        user.groups.add(self.directeurs)
        request = RequestFactory().get("/fiches_admin/auth/user/1/change/")
        admin_obj = CustomUserAdmin(User, AdminSite())

        request.user = User.objects.get(pk=user.pk)
        self.assertNotIn(
            "UserProfileInline",
            [inline.__class__.__name__ for inline in admin_obj.get_inline_instances(request)],
        )

        call_command("sync_status_roles", apply=True, stdout=StringIO())

        request.user = User.objects.get(pk=user.pk)
        self.assertIn(
            "UserProfileInline",
            [inline.__class__.__name__ for inline in admin_obj.get_inline_instances(request)],
        )
