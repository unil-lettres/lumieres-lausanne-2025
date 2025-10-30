from contextlib import nullcontext

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from fiches.models.documents.document_file import DocumentFile
from fiches.models.misc.object_collection import ObjectCollection


class Command(BaseCommand):
    help = (
        "Synchronise Lumières status groups with the latest permission policy:\n"
        " - doctorants gain the ability to manage bibliography attachments\n"
        " - directeurs may reassign collection owners\n"
        " - assistants status is retired\n"
        "Run without --apply for a dry-run preview."
    )

    DOCFILE_PERMS = ("add_documentfile", "change_documentfile", "delete_documentfile")
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
                self._update_director_permissions(collection_owner_perm, apply_changes)
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
            perm.codename: perm
            for perm in Permission.objects.filter(content_type=ct, codename__in=self.DOCFILE_PERMS)
        }
        missing = sorted(set(self.DOCFILE_PERMS) - set(perms))
        if missing:
            warning = (
                "Missing DocumentFile permissions: "
                f"{', '.join(missing)}. Please run migrations before applying changes."
            )
            self.stdout.write(self.style.WARNING(warning))
        return perms

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
                    self.style.SUCCESS(
                        f"Granted document attachment permissions to '{group.name}': {perm_labels}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Would grant document attachment permissions to '{group.name}': {perm_labels}"
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"'{group.name}' already has document attachment permissions.")
            )

    def _ensure_collection_owner_permission(self, apply_changes):
        """Create the custom permission for changing collection owners."""
        ct = ContentType.objects.get_for_model(ObjectCollection)
        try:
            perm = Permission.objects.get(content_type=ct, codename=self.COLLECTION_OWNER_PERM)
            if not apply_changes:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Custom permission 'fiches.change_collection_owner' already exists."
                    )
                )
            return perm
        except Permission.DoesNotExist:
            if apply_changes:
                perm = Permission.objects.create(
                    content_type=ct,
                    codename=self.COLLECTION_OWNER_PERM,
                    name="Can change collection owner",
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        "Created custom permission 'fiches.change_collection_owner'."
                    )
                )
                return perm
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "Permission 'fiches.change_collection_owner' is missing. "
                        "Would create it in apply mode."
                    )
                )
                return None

    def _update_director_permissions(self, permission, apply_changes):
        """Ensure directors can change collection ownership."""
        group = self._get_group(self.DIRECTEUR_NAME)
        if not group:
            message = f"Group '{self.DIRECTEUR_NAME}' not found."
            if apply_changes:
                group = Group.objects.create(name=self.DIRECTEUR_NAME)
                self.stdout.write(self.style.SUCCESS(f"{message} Created new group."))
            else:
                self.stdout.write(self.style.WARNING(f"{message} Would create it in apply mode."))
                return

        if permission in group.permissions.all():
            self.stdout.write(
                self.style.SUCCESS(
                    f"'{group.name}' already holds permission '{permission.codename}'."
                )
            )
            return

        if apply_changes:
            group.permissions.add(permission)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Granted '{permission.codename}' permission to '{group.name}'."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Would grant '{permission.codename}' permission to '{group.name}'."
                )
            )

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
            note = (
                f"Would remove assistant group(s) ({label}). "
                f"{total_users} associated user(s) currently assigned."
            )
            self.stdout.write(self.style.WARNING(note))
