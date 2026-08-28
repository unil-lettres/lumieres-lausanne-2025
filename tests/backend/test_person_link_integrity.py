# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Deletion guards and orphan audits for person named entities."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from fiches.models import Person, Transcription


def tag(person, quote='"'):
    return (
        f"<a class={quote}ll-tag ll-tag-person{quote} "
        f"data-person={quote}{person.pk}{quote} "
        f"href={quote}/fiches/bio/{person.pk}/{quote}>{person.name}</a>"
    )


@pytest.mark.django_db
def test_transcription_tag_blocks_person_hard_deletion():
    person = Person.objects.create(name="Barbeyrac, Jean", modern=False)
    transcription = Transcription.objects.create(text=tag(person))

    with pytest.raises(ProtectedError, match="Transcriptions: 1"):
        with transaction.atomic():
            person.delete()

    assert Person.objects.filter(pk=person.pk).exists()
    assert f'data-person="{person.pk}"' in Transcription.objects.get(pk=transcription.pk).text


@pytest.mark.django_db
def test_legacy_single_quoted_tag_blocks_person_hard_deletion():
    person = Person.objects.create(name="Barbeyrac, Jean", modern=False)
    Transcription.objects.create(text=tag(person, quote="'"))

    with pytest.raises(ProtectedError):
        with transaction.atomic():
            person.delete()


@pytest.mark.django_db
def test_unreferenced_person_can_be_deleted():
    person = Person.objects.create(name="Sans référence", modern=False)
    person_id = person.pk

    person.delete()

    assert not Person.objects.filter(pk=person_id).exists()


@pytest.mark.django_db
def test_person_link_audit_passes_with_valid_tags():
    person = Person.objects.create(name="Barbeyrac, Jean", modern=False)
    Transcription.objects.create(text=tag(person))
    stdout = StringIO()

    call_command("audit_person_links", stdout=stdout)

    assert "no orphan references" in stdout.getvalue()


@pytest.mark.django_db
def test_person_link_audit_reports_orphan_html_tags():
    Transcription.objects.create(
        text='<a class="ll-tag ll-tag-person" data-person="987654" href="/fiches/bio/987654/">Perdu</a>'
    )
    stdout = StringIO()

    with pytest.raises(CommandError, match="1 orphan reference"):
        call_command("audit_person_links", stdout=stdout)

    assert "fiches.Transcription" in stdout.getvalue()
    assert "missing person 987654" in stdout.getvalue()
