# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Reference-integrity helpers for person tags and structured person links."""

from __future__ import annotations

import re
from dataclasses import dataclass

from fiches.models import Person, Transcription

PERSON_TAG_RE = re.compile(r"\bdata-person\s*=\s*['\"](?P<person_id>\d+)['\"]", re.IGNORECASE)


@dataclass(frozen=True)
class OrphanPersonLink:
    """A stored person tag whose target authority no longer exists."""

    source: str
    object_pk: int
    person_id: int
    field: str


def tagged_transcriptions(person_id):
    """Return transcriptions containing a robustly parsed tag for a person."""
    matching_ids = set()
    rows = Transcription.objects.filter(text__contains="data-person").values_list("pk", "text")
    for transcription_id, text in rows.iterator():
        if any(int(match.group("person_id")) == person_id for match in PERSON_TAG_RE.finditer(text or "")):
            matching_ids.add(transcription_id)
    return Transcription.objects.filter(pk__in=matching_ids)


def person_reference_groups(person):
    """Return external references whose removal would lose editorial links."""
    sources = (
        ("Transcriptions", tagged_transcriptions(person.pk)),
        ("Bibliographies — sujets personnes", person.biblio_set.all()),
        ("Contributions bibliographiques", person.contribution_biblio.all()),
        ("Contributions manuscrites", person.contribution_mans.all()),
        ("Relations depuis d’autres biographies", person.person_back.all()),
        ("Projets", person.projects.all()),
        ("Collections", person.objectcollections.all()),
    )
    groups = []
    for label, queryset in sources:
        objects = list(queryset)
        if objects:
            groups.append({"label": label, "count": len(objects), "objects": objects})
    return groups


def find_orphan_person_links():
    """Find persisted HTML tags targeting a missing ``Person`` authority."""
    valid_ids = set(Person.objects.values_list("pk", flat=True))
    orphans = []
    rows = Transcription.objects.filter(text__contains="data-person").values_list("pk", "text")
    for transcription_id, text in rows.iterator():
        for match in PERSON_TAG_RE.finditer(text or ""):
            person_id = int(match.group("person_id"))
            if person_id not in valid_ids:
                orphans.append(
                    OrphanPersonLink(
                        source=Transcription._meta.label,
                        object_pk=transcription_id,
                        person_id=person_id,
                        field="text",
                    )
                )
    return orphans
