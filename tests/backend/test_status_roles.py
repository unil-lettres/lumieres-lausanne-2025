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
from django.urls import reverse

from fiches.admin import CustomUserAdmin
from fiches.models import PlaceCategory, PlaceRecord
from fiches.views.place import may_change, may_delete


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

    def test_apply_grants_fiche_creation_permissions_to_directors(self):
        # §1: only Directeurs may create person/place fiches while tagging.
        out = StringIO()

        call_command("sync_status_roles", apply=True, stdout=out)
        self.directeurs.refresh_from_db()

        self.assertTrue({"add_person", "add_placerecord"}.issubset(self._director_permission_codenames()))

    def test_dry_run_does_not_grant_fiche_creation_permissions_to_directors(self):
        out = StringIO()

        call_command("sync_status_roles", stdout=out)
        self.directeurs.refresh_from_db()

        self.assertFalse({"add_person", "add_placerecord"} & self._director_permission_codenames())

    def test_apply_grants_place_management_permissions_to_directors(self):
        out = StringIO()

        call_command("sync_status_roles", apply=True, stdout=out)
        self.directeurs.refresh_from_db()

        self.assertTrue(
            {"change_placerecord", "delete_placerecord", "view_placerecord"}.issubset(
                self._director_permission_codenames()
            )
        )

    def test_dry_run_does_not_grant_place_management_permissions_to_directors(self):
        out = StringIO()

        call_command("sync_status_roles", stdout=out)
        self.directeurs.refresh_from_db()

        self.assertFalse(
            {"change_placerecord", "delete_placerecord", "view_placerecord"} & self._director_permission_codenames()
        )

    def test_apply_follows_the_place_status_matrix(self):
        """ "LL détail des STATUTS revus 2026.07": who may edit/delete whose fiche."""
        etudiants = Group.objects.create(name="étudiants")
        chercheurs = Group.objects.create(name="chercheurs")

        call_command("sync_status_roles", apply=True, stdout=StringIO())

        def codenames(group):
            return set(group.permissions.values_list("codename", flat=True))

        # Étudiant: may edit and delete, but only their own fiches.
        self.assertIn("change_placerecord", codenames(etudiants))
        self.assertNotIn("change_any_placerecord", codenames(etudiants))
        self.assertNotIn("delete_any_placerecord", codenames(etudiants))
        # Chercheur: edits every fiche, deletes only their own.
        self.assertIn("change_any_placerecord", codenames(chercheurs))
        self.assertNotIn("delete_any_placerecord", codenames(chercheurs))
        # Directeur LL: no ownership restriction at all.
        self.assertIn("delete_any_placerecord", self._director_permission_codenames())

    def test_place_status_matrix_is_enforced_from_user_to_director(self):
        """Redundant behavioural pass over every row in Béatrice's XLS matrix."""
        groups = {
            "utilisateurs": Group.objects.create(name="utilisateurs"),
            "étudiants": Group.objects.create(name="étudiants"),
            "chercheurs": Group.objects.create(name="chercheurs"),
            "doctorants": self.doctorants,
            "directeurs": self.directeurs,
        }
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        category = PlaceCategory.objects.create(name="Ville")
        other = User.objects.create_user("place-other", password="pw")
        expectations = {
            # group: (may add, change own, change other, delete own, delete other)
            "utilisateurs": (False, False, False, False, False),
            "étudiants": (True, True, False, True, False),
            "chercheurs": (True, True, True, True, False),
            "doctorants": (True, True, True, True, False),
            "directeurs": (True, True, True, True, True),
        }

        for group_name, expected in expectations.items():
            user = User.objects.create_user(f"matrix-{group_name}", password="pw")
            user.groups.add(groups[group_name])
            own_place = PlaceRecord.objects.create(name=f"Own {group_name}", category=category, creator=user)
            other_place = PlaceRecord.objects.create(name=f"Other {group_name}", category=category, creator=other)
            observed = (
                user.has_perm("fiches.add_placerecord"),
                may_change(user, own_place),
                may_change(user, other_place),
                may_delete(user, own_place),
                may_delete(user, other_place),
            )
            with self.subTest(group=group_name):
                self.assertEqual(observed, expected)

    def test_only_directors_may_create_a_place_while_tagging(self):
        """Inline creation from the tagging toolbar is narrower than add_placerecord."""
        chercheurs = Group.objects.create(name="chercheurs")

        call_command("sync_status_roles", apply=True, stdout=StringIO())

        self.assertIn("add_placerecord_inline", self._director_permission_codenames())
        self.assertNotIn(
            "add_placerecord_inline",
            set(chercheurs.permissions.values_list("codename", flat=True)),
        )

    def test_director_can_reopen_a_place_fiche_for_editing_after_sync(self):
        """Client report 2026-07-15: a director could create a place fiche but
        saving it, or reopening it later, answered "Accès non autorisé" — they
        only ever received add_placerecord, never change_placerecord."""
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        director = User.objects.create_user("director-place", password="pw")
        director.groups.add(self.directeurs)
        place = PlaceRecord.objects.create(name="Lausanne", category=PlaceCategory.objects.create(name="Ville"))
        self.client.force_login(director)

        response = self.client.get(reverse("place-edit", args=[place.pk]))

        self.assertEqual(response.status_code, 200)

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
