# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Audit persisted person tags without modifying editorial content."""

from django.core.management.base import BaseCommand, CommandError

from fiches.person_references import find_orphan_person_links


class Command(BaseCommand):
    """Fail when an HTML person tag targets a missing authority."""

    help = "Audit person tags and fail if any target Person is missing."

    def handle(self, *args, **options):
        """Report every orphan and return a failing command status when found."""
        orphans = find_orphan_person_links()
        if not orphans:
            self.stdout.write(self.style.SUCCESS("Person-link audit passed: no orphan references."))
            return

        for orphan in orphans:
            self.stdout.write(
                self.style.ERROR(
                    f"{orphan.source} pk={orphan.object_pk} field={orphan.field} "
                    f"references missing person {orphan.person_id}"
                )
            )
        raise CommandError(f"Person-link audit failed: {len(orphans)} orphan reference(s).")
