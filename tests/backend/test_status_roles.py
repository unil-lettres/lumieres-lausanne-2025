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
from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse

from fiches.admin import CustomUserAdmin
from fiches.management.commands.sync_status_roles import Command
from fiches.models import DocumentNature, PlaceCategory, PlaceRecord
from fiches.utils import (
    user_can_change_documentfile,
    user_can_delete_biblio,
    user_can_delete_documentfile,
    user_can_delete_transcription,
)
from fiches.views.place import may_change, may_delete


class SyncStatusRolesTest(TestCase):
    def setUp(self):
        self.directeurs = Group.objects.create(name="directeurs")
        self.doctorants = Group.objects.create(name="doctorants")
        self.civilistes = Group.objects.create(name="civilistes")

    def _director_permission_codenames(self):
        return set(self.directeurs.permissions.values_list("codename", flat=True))

    def _doctorant_permission_codenames(self):
        return set(self.doctorants.permissions.values_list("codename", flat=True))

    def _civiliste_permission_specs(self):
        return set(
            self.civilistes.permissions.values_list(
                "content_type__app_label", "content_type__model", "codename"
            )
        )

    def test_apply_reconciles_civilistes_to_the_exact_editorial_policy(self):
        forbidden = Permission.objects.get(
            content_type__app_label="fiches",
            content_type__model="transcription",
            codename="publish_transcription",
        )
        self.civilistes.permissions.add(forbidden)

        call_command("sync_status_roles", apply=True, stdout=StringIO())
        self.civilistes.refresh_from_db()

        self.assertEqual(self._civiliste_permission_specs(), set(Command.CIVILISTE_PERMISSION_SPECS))

    def test_dry_run_reports_but_does_not_reconcile_civilistes(self):
        forbidden = Permission.objects.get(
            content_type__app_label="fiches",
            content_type__model="biblio",
            codename="delete_any_biblio",
        )
        self.civilistes.permissions.add(forbidden)
        before = self._civiliste_permission_specs()
        out = StringIO()

        call_command("sync_status_roles", stdout=out)

        self.assertEqual(self._civiliste_permission_specs(), before)
        self.assertIn("Would grant Civiliste permissions", out.getvalue())
        self.assertIn("Would revoke out-of-policy Civiliste permissions", out.getvalue())

    def test_civiliste_can_work_on_assigned_content_but_not_publish_or_administer(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        user = User.objects.create_user("civiliste", password="pw")
        user.groups.add(self.civilistes)

        allowed = {
            "fiches.add_biblio",
            "fiches.change_any_biblio",
            "fiches.add_transcription",
            "fiches.change_any_transcription",
            "fiches.access_unpublished_transcription",
            "fiches.add_documentfile",
            "fiches.change_any_documentfile",
        }
        forbidden = {
            "fiches.change_biblio_ownership",
            "fiches.delete_any_biblio",
            "fiches.change_transcription_ownership",
            "fiches.delete_any_transcription",
            "fiches.publish_transcription",
            "fiches.delete_any_documentfile",
            "fiches.add_person_inline",
            "fiches.add_placerecord_inline",
            "fiches.can_see_note",
            "fiches.can_publish_note",
            "auth.change_user",
            "auth.change_group",
        }

        self.assertTrue(all(user.has_perm(name) for name in allowed))
        self.assertFalse(any(user.has_perm(name) for name in forbidden))
        self.assertFalse(user.is_staff)

    def test_civiliste_deletion_is_owner_scoped_while_attachment_editing_is_not(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        user = User.objects.create_user("civiliste-owner", password="pw")
        other = User.objects.create_user("civiliste-other", password="pw")
        user.groups.add(self.civilistes)

        own = SimpleNamespace(creator_id=user.id, access_owner_id=user.id, author_id=user.id)
        foreign = SimpleNamespace(creator_id=other.id, access_owner_id=other.id, author_id=other.id)

        self.assertTrue(user_can_delete_biblio(user, own))
        self.assertFalse(user_can_delete_biblio(user, foreign))
        self.assertTrue(user_can_delete_transcription(user, own))
        self.assertFalse(user_can_delete_transcription(user, foreign))
        self.assertTrue(user_can_change_documentfile(user, foreign))
        self.assertTrue(user_can_delete_documentfile(user, own))
        self.assertFalse(user_can_delete_documentfile(user, foreign))

    def test_civiliste_cannot_create_named_entities_from_tagging(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        user = User.objects.create_user("civiliste-tagging", password="pw")
        user.groups.add(self.civilistes)
        category = PlaceCategory.objects.create(name="Ville civiliste")
        self.client.force_login(user)

        person_response = self.client.post(reverse("tagging-person-create"), {"name": "Nouvelle personne"})
        place_response = self.client.post(
            reverse("tagging-place-create"),
            {"name": "Nouveau lieu", "category": category.pk},
        )

        self.assertEqual(person_response.status_code, 403)
        self.assertEqual(place_response.status_code, 403)

    def test_civiliste_only_sees_the_transcription_delete_button_for_owned_records(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        user = User.objects.create_user("civiliste-delete-button", password="pw")
        owner = User.objects.create_user("civiliste-delete-button-owner", password="pw")
        user.groups.add(self.civilistes)
        request = RequestFactory().get("/fiches/biblio/edit/1/")
        request.user = user

        def render(transcription):
            doc = SimpleNamespace(id=1, transcription_set=SimpleNamespace(all=lambda: [transcription]))
            return render_to_string(
                "fiches/edition/document/transcription_b_set.html",
                {"doc": doc},
                request=request,
            )

        foreign = SimpleNamespace(id=101, author=owner, access_owner=owner, access_public=False)
        own = SimpleNamespace(id=102, author=owner, access_owner=user, access_public=False)
        published = SimpleNamespace(id=103, author=owner, access_owner=owner, access_public=True)

        self.assertNotIn(reverse("transcription-delete", args=[foreign.id]), render(foreign))
        self.assertIn(reverse("transcription-edit", args=[foreign.id]), render(foreign))
        self.assertIn(reverse("transcription-delete", args=[own.id]), render(own))
        self.assertNotIn(reverse("transcription-edit", args=[published.id]), render(published))

    def test_sync_warns_about_civilistes_with_elevated_access_without_changing_memberships(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        user = User.objects.create_user("civiliste-conflict", is_staff=False)
        user.groups.add(self.civilistes, self.directeurs)
        out = StringIO()

        call_command("sync_status_roles", stdout=out)

        self.assertIn("Civiliste account conflict(s) detected", out.getvalue())
        self.assertIn("civiliste-conflict (directeurs)", out.getvalue())
        self.assertEqual(
            set(user.groups.values_list("name", flat=True)),
            {"civilistes", "directeurs"},
        )

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
                "change_any_documentfile",
                "access_unpublished_transcription",
                "change_any_transcription",
            }.issubset(self._doctorant_permission_codenames())
        )

    def test_apply_keeps_attachment_deletion_owner_scoped_for_doctorants(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())

        self.assertNotIn("delete_any_documentfile", self._doctorant_permission_codenames())

    def test_apply_grants_attachment_and_note_oversight_to_directors(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())

        director_permissions = self._director_permission_codenames()
        self.assertTrue(
            {
                "add_documentfile",
                "change_documentfile",
                "delete_documentfile",
                "change_any_documentfile",
                "delete_any_documentfile",
                "can_see_note",
                "can_publish_note",
            }.issubset(director_permissions)
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

        self.assertTrue(
            {
                "add_person",
                "add_person_inline",
                "add_placerecord",
                "add_placerecord_inline",
            }.issubset(self._director_permission_codenames())
        )

    def test_dry_run_does_not_grant_fiche_creation_permissions_to_directors(self):
        out = StringIO()

        call_command("sync_status_roles", stdout=out)
        self.directeurs.refresh_from_db()

        self.assertFalse(
            {"add_person", "add_person_inline", "add_placerecord", "add_placerecord_inline"}
            & self._director_permission_codenames()
        )

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

    def test_apply_grants_place_category_admin_permissions_to_directors(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        self.directeurs.refresh_from_db()

        self.assertTrue(
            {
                "view_placecategory",
                "add_placecategory",
                "change_placecategory",
                "delete_placecategory",
            }.issubset(self._director_permission_codenames())
        )

    def test_dry_run_does_not_grant_place_category_admin_permissions_to_directors(self):
        call_command("sync_status_roles", stdout=StringIO())
        self.directeurs.refresh_from_db()

        self.assertFalse(set(Command.DIRECTOR_PLACE_CATEGORY_PERMS) & self._director_permission_codenames())

    def test_apply_grants_document_nature_admin_permissions_to_directors(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        self.directeurs.refresh_from_db()

        self.assertTrue(
            set(Command.DIRECTOR_DOCUMENT_NATURE_PERMS).issubset(self._director_permission_codenames())
        )

    def test_dry_run_does_not_grant_document_nature_admin_permissions_to_directors(self):
        call_command("sync_status_roles", stdout=StringIO())
        self.directeurs.refresh_from_db()

        self.assertFalse(set(Command.DIRECTOR_DOCUMENT_NATURE_PERMS) & self._director_permission_codenames())

    def test_director_can_manage_document_natures_in_the_admin_after_sync(self):
        call_command("sync_status_roles", apply=True, stdout=StringIO())
        director = User.objects.create_user("director-document-nature", password="pw", is_staff=True)
        director.groups.add(self.directeurs)
        DocumentNature.objects.create(name="Lettre autographe", sorting=1)
        self.client.force_login(director)

        changelist = self.client.get(reverse("fiches_admin:fiches_documentnature_changelist"))
        add_form = self.client.get(reverse("fiches_admin:fiches_documentnature_add"))

        self.assertEqual(changelist.status_code, 200)
        self.assertContains(changelist, "Lettre autographe")
        self.assertEqual(add_form.status_code, 200)

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

    def test_only_directors_may_create_named_entities_while_tagging(self):
        """Inline creation from tagging is narrower than ordinary fiche creation."""
        chercheurs = Group.objects.create(name="chercheurs")

        call_command("sync_status_roles", apply=True, stdout=StringIO())

        self.assertTrue(
            {"add_person_inline", "add_placerecord_inline"}.issubset(self._director_permission_codenames())
        )
        self.assertFalse(
            {"add_person_inline", "add_placerecord_inline"}
            & set(chercheurs.permissions.values_list("codename", flat=True))
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
