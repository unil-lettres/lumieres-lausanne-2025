# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Reference integrity helpers for place tags and structured place links."""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.db.models import Q
from django.urls import reverse
from django.utils.html import strip_tags

from fiches.models import Biography, PlaceRecord
from fiches.models.documents.document import Biblio, Transcription
from fiches.models.person.biography import Profession

PLACE_TAG_RE = re.compile(r"\bdata-place\s*=\s*['\"](?P<place_id>\d+)['\"]", re.IGNORECASE)

# Every model field in which the place-tagging widgets persist an HTML anchor.
# Keep this registry shared by deletion protection and the integrity audit so
# a new tagging surface cannot silently drift between the two mechanisms.
PLACE_TAG_SOURCES = (
    (Transcription, ("text",), "Transcriptions"),
    (Biography, ("birth_place", "death_place", "origin"), "Biographies"),
    (Profession, ("place",), "Professions"),
    (Biblio, ("place", "place2", "destination"), "Bibliographies — champs de lieu"),
)


@dataclass(frozen=True)
class OrphanPlaceLink:
    """A stored place reference whose target fiche no longer exists."""

    source: str
    object_pk: int
    place_id: int
    field: str


def place_tag_needle(place_id):
    """Return the canonical substring emitted by the place-tagging widgets."""
    return f'data-place="{place_id}"'


def _tagged_queryset(model, fields, place_id):
    candidate_query = Q()
    for field in fields:
        candidate_query |= Q(**{f"{field}__contains": "data-place"})

    matching_ids = set()
    for row in model._default_manager.filter(candidate_query).values_list("pk", *fields).iterator():
        object_pk, values = row[0], row[1:]
        if any(
            int(match.group("place_id")) == place_id
            for value in values
            for match in PLACE_TAG_RE.finditer(value or "")
        ):
            matching_ids.add(object_pk)
    return model._default_manager.filter(pk__in=matching_ids)


def _reference_item(model, obj):
    """Build a stable display link for one referencing editorial object."""
    if model is Transcription:
        label = str(obj)
        return {"label": label if label != "---" else f"Transcription {obj.pk}", "url": reverse("transcription-display", args=[obj.pk])}
    if model is Biography:
        return {
            "label": f"{obj.person.name} — version {obj.version}",
            "url": reverse("biography-display", kwargs={"person_id": obj.person_id, "version": obj.version}),
        }
    if model is Profession:
        return {
            "label": f"{obj.bio.person.name} — {obj.position}",
            "url": reverse(
                "biography-display",
                kwargs={"person_id": obj.bio.person_id, "version": obj.bio.version},
            ),
        }
    return {"label": strip_tags(obj.title), "url": reverse("display-bibliography", args=[obj.pk])}


def _reference_group(model, fields, label, place_id):
    queryset = _tagged_queryset(model, fields, place_id).order_by("pk")
    if model is Biography:
        queryset = queryset.select_related("person")
    elif model is Profession:
        queryset = queryset.select_related("bio__person")
    objects = list(queryset)
    if not objects:
        return None
    return {
        "label": label,
        "count": len(objects),
        "items": [_reference_item(model, obj) for obj in objects],
        "objects": objects,
    }


def place_reference_groups(place):
    """Return non-empty reference groups that make a place unsafe to delete."""
    groups = []
    for model, fields, label in PLACE_TAG_SOURCES:
        group = _reference_group(model, fields, label, place.pk)
        if group:
            groups.append(group)

    subject_biblios = list(
        Biblio.objects.filter(subj_place=place).distinct().order_by("pk")  # ty: ignore[unresolved-attribute]
    )
    if subject_biblios:
        groups.append(
            {
                "label": "Bibliographies — sujets lieux",
                "count": len(subject_biblios),
                "items": [_reference_item(Biblio, biblio) for biblio in subject_biblios],
                "objects": subject_biblios,
            }
        )
    return groups


def find_orphan_place_links():
    """Find broken HTML tags and structured bibliography-place relations."""
    valid_ids = set(PlaceRecord.objects.values_list("pk", flat=True))  # ty: ignore[unresolved-attribute]
    orphans = []
    for model, fields, _label in PLACE_TAG_SOURCES:
        for field in fields:
            rows = model._default_manager.filter(**{f"{field}__contains": "data-place="}).values_list("pk", field)
            for object_pk, value in rows.iterator():
                for match in PLACE_TAG_RE.finditer(value or ""):
                    place_id = int(match.group("place_id"))
                    if place_id not in valid_ids:
                        orphans.append(
                            OrphanPlaceLink(
                                model._meta.label,  # ty: ignore[unresolved-attribute]
                                object_pk,
                                place_id,
                                field,
                            )
                        )

    through = Biblio.subj_place.through  # ty: ignore[unresolved-attribute]
    for object_pk, biblio_id, place_id in through.objects.exclude(placerecord_id__in=valid_ids).values_list(
        "pk", "biblio_id", "placerecord_id"
    ):
        orphans.append(
            OrphanPlaceLink(
                source=through._meta.label,
                object_pk=object_pk,
                place_id=place_id,
                field=f"biblio_id={biblio_id}",
            )
        )
    return orphans
