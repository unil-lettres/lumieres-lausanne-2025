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

from io import StringIO

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from fiches.admin import CustomUserAdmin


class SyncStatusRolesTest(TestCase):
    def setUp(self):
        self.directeurs = Group.objects.create(name="directeurs")

    def _director_permission_codenames(self):
        return set(self.directeurs.permissions.values_list("codename", flat=True))

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
