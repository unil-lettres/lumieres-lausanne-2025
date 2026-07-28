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

from contextlib import nullcontext

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from fiches.models.core.user_profile import UserProfile
from fiches.models.documents.document_file import DocumentFile
from fiches.models.misc.object_collection import ObjectCollection
from fiches.models.misc.place import PlaceRecord
from fiches.models.person.person import Person


class Command(BaseCommand):
    help = (
        "Synchronise Lumières status groups with the latest permission policy:\n"
        " - doctorants gain the ability to manage bibliography attachments\n"
        " - directeurs may reassign collection owners\n"
        " - directeurs may manage user profile extra information\n"
        " - directeurs may create person & place fiches (named-entity tagging)\n"
        " - every status group gets its Fiche lieu access from the status matrix\n"
        " - assistants status is retired\n"
        "Run without --apply for a dry-run preview."
    )

    DOCFILE_PERMS = ("add_documentfile", "change_documentfile", "delete_documentfile")
    DIRECTOR_USER_PROFILE_PERMS = (
        "add_userprofile",
        "change_userprofile",
        "delete_userprofile",
        "view_userprofile",
    )
    #: Fiche lieu access per status, from the client's "LL détail des STATUTS
    #: revus 2026.07". The matrix grants "modifier"/"supprimer" either fully or
    #: only on one's own fiches; the latter is expressed by withholding the
    #: matching "_any_" permission, which views.place.may_change / may_delete
    #: then read as "own fiches only" (same convention as Biblio).
    BASE_PLACE_PERMS = (
        "view_placerecord",
        "add_placerecord",
        "change_placerecord",
        "delete_placerecord",
    )
    PLACE_PERMS_BY_GROUP = {
        # Étudiant: modifier + supprimer seulement ses propres fiches.
        "étudiants": BASE_PLACE_PERMS,
        # Chercheur / Doctorant LL: modifier toutes, supprimer seulement les leurs.
        "chercheurs": (*BASE_PLACE_PERMS, "change_any_placerecord"),
        "doctorants": (*BASE_PLACE_PERMS, "change_any_placerecord"),
        # Directeur LL: tout, sans restriction de propriété, plus la création
        # depuis la barre de tag (hors matrice: demande client du 2026-07-15).
        "directeurs": (
            *BASE_PLACE_PERMS,
            "change_any_placerecord",
            "delete_any_placerecord",
            "add_placerecord_inline",
        ),
    }
    ASSISTANT_NAMES = ("assistants", "assistant")
    DOCTORANT_NAME = "doctorants"
    DIRECTEUR_NAME = "directeurs"
    COLLECTION_OWNER_PERM = "change_collection_owner"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            dest="apply",
            help="Persist the changes to the database. Omit for a dry-run preview.",
        )

    def handle(self, *args, **options):
        apply_changes = options.get("apply", False)
        mode = "APPLY" if apply_changes else "DRY-RUN"
        self.stdout.write(self.style.NOTICE(f"Synchronising status roles ({mode})"))

        context_manager = transaction.atomic if apply_changes else nullcontext
        with context_manager():
            docfile_perms = self._ensure_docfile_permissions()
            self._update_doctorant_permissions(docfile_perms, apply_changes)
            collection_owner_perm = self._ensure_collection_owner_permission(apply_changes)
            if collection_owner_perm is not None:
                self._update_director_permissions([collection_owner_perm], apply_changes)
            user_profile_perms = self._ensure_user_profile_permissions()
            self._update_director_permissions(user_profile_perms, apply_changes)
            fiche_creation_perms = self._ensure_fiche_creation_permissions()
            self._update_director_permissions(fiche_creation_perms, apply_changes)
            self._sync_place_permissions(apply_changes)
            self._retire_assistant_group(apply_changes)

        self.stdout.write(self.style.SUCCESS("Status synchronisation complete."))

    # ------------------------------------------------------------------ helpers --

    def _get_group(self, name):
        """Return the first group matching the supplied name (case-insensitive)."""
        return Group.objects.filter(name__iexact=name).first()

    def _ensure_docfile_permissions(self):
        """Fetch DocumentFile permissions required for attachment management."""
        ct = ContentType.objects.get_for_model(DocumentFile)
        perms = {
            perm.codename: perm for perm in Permission.objects.filter(content_type=ct, codename__in=self.DOCFILE_PERMS)
        }
        missing = sorted(set(self.DOCFILE_PERMS) - set(perms))
        if missing:
            warning = (
                "Missing DocumentFile permissions: "
                f"{', '.join(missing)}. Please run migrations before applying changes."
            )
            self.stdout.write(self.style.WARNING(warning))
        return perms

    def _ensure_user_profile_permissions(self):
        """Fetch UserProfile permissions required by the user admin inline."""
        ct = ContentType.objects.get_for_model(UserProfile)
        perms = {
            perm.codename: perm
            for perm in Permission.objects.filter(
                content_type=ct,
                codename__in=self.DIRECTOR_USER_PROFILE_PERMS,
            )
        }
        missing = sorted(set(self.DIRECTOR_USER_PROFILE_PERMS) - set(perms))
        if missing:
            warning = (
                "Missing UserProfile permissions: "
                f"{', '.join(missing)}. Please run migrations before applying changes."
            )
            self.stdout.write(self.style.WARNING(warning))
        return [perms[codename] for codename in self.DIRECTOR_USER_PROFILE_PERMS if codename in perms]

    def _update_doctorant_permissions(self, docfile_perms, apply_changes):
        """Grant document-file management to doctorants."""
        group = self._get_group(self.DOCTORANT_NAME)
        if not group:
            message = f"Group '{self.DOCTORANT_NAME}' not found."
            if apply_changes:
                group = Group.objects.create(name=self.DOCTORANT_NAME)
                self.stdout.write(self.style.SUCCESS(f"{message} Created new group."))
            else:
                self.stdout.write(self.style.WARNING(f"{message} Would create it in apply mode."))
                return

        missing_perms = [
            docfile_perms[codename]
            for codename in self.DOCFILE_PERMS
            if codename in docfile_perms and docfile_perms[codename] not in group.permissions.all()
        ]
        if missing_perms:
            perm_labels = ", ".join(p.codename for p in missing_perms)
            if apply_changes:
                group.permissions.add(*missing_perms)
                self.stdout.write(
                    self.style.SUCCESS(f"Granted document attachment permissions to '{group.name}': {perm_labels}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Would grant document attachment permissions to '{group.name}': {perm_labels}")
                )
        else:
            self.stdout.write(self.style.SUCCESS(f"'{group.name}' already has document attachment permissions."))

    def _ensure_collection_owner_permission(self, apply_changes):
        """Create the custom permission for changing collection owners."""
        ct = ContentType.objects.get_for_model(ObjectCollection)
        try:
            perm = Permission.objects.get(content_type=ct, codename=self.COLLECTION_OWNER_PERM)
            if not apply_changes:
                self.stdout.write(
                    self.style.SUCCESS("Custom permission 'fiches.change_collection_owner' already exists.")
                )
            return perm
        except Permission.DoesNotExist:
            if apply_changes:
                perm = Permission.objects.create(
                    content_type=ct,
                    codename=self.COLLECTION_OWNER_PERM,
                    name="Can change collection owner",
                )
                self.stdout.write(self.style.SUCCESS("Created custom permission 'fiches.change_collection_owner'."))
                return perm
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "Permission 'fiches.change_collection_owner' is missing. Would create it in apply mode."
                    )
                )
                return None

    def _ensure_fiche_creation_permissions(self):
        """Fetch the person/place 'add' permissions used to create fiches while tagging."""
        permissions = []
        for model, codename in ((Person, "add_person"), (PlaceRecord, "add_placerecord")):
            ct = ContentType.objects.get_for_model(model)
            perm = Permission.objects.filter(content_type=ct, codename=codename).first()
            if perm:
                permissions.append(perm)
            else:
                self.stdout.write(
                    self.style.WARNING(f"Missing permission '{codename}'. Please run migrations before applying.")
                )
        return permissions

    def _sync_place_permissions(self, apply_changes):
        """Align every status group with the Fiche lieu column of the status matrix."""
        ct = ContentType.objects.get_for_model(PlaceRecord)
        available = {perm.codename: perm for perm in Permission.objects.filter(content_type=ct)}
        for group_name, codenames in self.PLACE_PERMS_BY_GROUP.items():
            missing = sorted(set(codenames) - set(available))
            if missing:
                warning = (
                    f"Missing PlaceRecord permissions: {', '.join(missing)}. "
                    "Please run migrations before applying changes."
                )
                self.stdout.write(self.style.WARNING(warning))
            perms = [available[codename] for codename in codenames if codename in available]
            self._update_group_permissions(group_name, perms, apply_changes)

    def _update_group_permissions(self, group_name, permissions, apply_changes):
        """Grant the supplied permissions to that status group, creating it if needed."""
        group = self._get_group(group_name)
        if not group:
            message = f"Group '{group_name}' not found."
            if apply_changes:
                group = Group.objects.create(name=group_name)
                self.stdout.write(self.style.SUCCESS(f"{message} Created new group."))
            else:
                self.stdout.write(self.style.WARNING(f"{message} Would create it in apply mode."))
                return

        existing_ids = set(group.permissions.values_list("id", flat=True))
        missing = [permission for permission in permissions if permission.id not in existing_ids]
        if not missing:
            self.stdout.write(self.style.SUCCESS(f"'{group.name}' already holds its place fiche permissions."))
            return

        labels = ", ".join(permission.codename for permission in missing)
        if apply_changes:
            group.permissions.add(*missing)
            self.stdout.write(self.style.SUCCESS(f"Granted place fiche permissions to '{group.name}': {labels}"))
        else:
            self.stdout.write(self.style.WARNING(f"Would grant place fiche permissions to '{group.name}': {labels}"))

    def _update_director_permissions(self, permissions, apply_changes):
        """Ensure directors hold the required administrative permissions."""
        group = self._get_group(self.DIRECTEUR_NAME)
        if not group:
            message = f"Group '{self.DIRECTEUR_NAME}' not found."
            if apply_changes:
                group = Group.objects.create(name=self.DIRECTEUR_NAME)
                self.stdout.write(self.style.SUCCESS(f"{message} Created new group."))
            else:
                self.stdout.write(self.style.WARNING(f"{message} Would create it in apply mode."))
                return

        existing_ids = set(group.permissions.values_list("id", flat=True))
        missing_permissions = [permission for permission in permissions if permission.id not in existing_ids]

        if not missing_permissions:
            self.stdout.write(self.style.SUCCESS(f"'{group.name}' already holds required director permissions."))
            return

        perm_labels = ", ".join(permission.codename for permission in missing_permissions)
        if apply_changes:
            group.permissions.add(*missing_permissions)
            self.stdout.write(self.style.SUCCESS(f"Granted director permissions to '{group.name}': {perm_labels}"))
        else:
            self.stdout.write(self.style.WARNING(f"Would grant director permissions to '{group.name}': {perm_labels}"))

    def _retire_assistant_group(self, apply_changes):
        """Remove the assistant status group entirely."""
        queries = [Q(name__iexact=name) for name in self.ASSISTANT_NAMES]
        if queries:
            combined_query = queries[0]
            for extra in queries[1:]:
                combined_query |= extra
            groups = Group.objects.filter(combined_query)
        else:
            groups = Group.objects.none()
        if not groups.exists():
            self.stdout.write(self.style.SUCCESS("No assistant group found; nothing to remove."))
            return

        total_users = sum(g.user_set.count() for g in groups)
        label = ", ".join(sorted(groups.values_list("name", flat=True)))
        if apply_changes:
            groups.delete()
            note = f"Removed assistant group(s) ({label})."
            if total_users:
                note += f" {total_users} user(s) lost that status."
            self.stdout.write(self.style.SUCCESS(note))
        else:
            note = f"Would remove assistant group(s) ({label}). {total_users} associated user(s) currently assigned."
            self.stdout.write(self.style.WARNING(note))
