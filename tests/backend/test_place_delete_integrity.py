# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Deletion guards and orphan audits for place named entities."""

from __future__ import annotations

from io import StringIO

import pytest
from django.contrib.auth.models import Permission
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory
from django.urls import reverse
from fiches.admin import PlaceRecordAdmin, fiches_admin
from fiches.place_references import find_orphan_place_links

from fiches.models import Biography, PlaceCategory, PlaceRecord
from fiches.models.documents.document import Biblio, DocumentLanguage, DocumentType, Transcription
from fiches.models.person.biography import Profession
from fiches.models.person.person import Person


@pytest.fixture
def place(db, django_user_model):
    user = django_user_model.objects.create_user("place-owner")
    user.user_permissions.add(Permission.objects.get(codename="delete_placerecord"))
    category = PlaceCategory.objects.create(name="Ville/Village")
    return PlaceRecord.objects.create(name="Lausanne", category=category, creator=user)


def tag(place):
    return (
        f'<a class="ll-tag ll-tag-place" data-place="{place.pk}" '
        f'href="/fiches/lieu/{place.pk}/">{place.name}</a>'
    )


def make_biblio(**kwargs):
    DocumentLanguage.objects.get_or_create(name="Français", defaults={"ordering": 1})
    document_type, _created = DocumentType.objects.get_or_create(
        id=1,
        defaults={"name": "Livre", "code": 1},
    )
    return Biblio.objects.create(
        title="Publication test",
        litterature_type="p",
        document_type=document_type,
        **kwargs,
    )


def assert_delete_blocked(client, place, expected_label):
    client.force_login(place.creator)
    response = client.post(reverse("place-delete", args=[place.pk]))
    assert response.status_code == 409
    assert expected_label in response.content.decode()
    assert PlaceRecord.objects.filter(pk=place.pk).exists()
    return response


@pytest.mark.django_db
def test_transcription_tag_blocks_place_deletion(client, place):
    transcription = Transcription.objects.create(text=tag(place))

    response = assert_delete_blocked(client, place, "Transcriptions")
    assert reverse("transcription-display", args=[transcription.pk]) in response.content.decode()
    assert f'data-place="{place.pk}"' in Transcription.objects.get(pk=transcription.pk).text


@pytest.mark.django_db
def test_legacy_single_quoted_tag_blocks_place_deletion(client, place):
    Transcription.objects.create(
        text=f"<a class='ll-tag-place' data-place = '{place.pk}' href='/fiches/lieu/{place.pk}/'>Lausanne</a>"
    )

    assert_delete_blocked(client, place, "Transcriptions")


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["birth_place", "death_place", "origin"])
def test_every_biography_tag_field_blocks_place_deletion(client, place, field):
    biography = Biography.objects.create(
        person=Person.objects.create(name="Personne test"),
        version=0,
        **{field: tag(place)},
    )

    response = assert_delete_blocked(client, place, "Biographies")
    expected_url = reverse(
        "biography-display",
        kwargs={"person_id": biography.person_id, "version": biography.version},
    )
    assert expected_url in response.content.decode()


@pytest.mark.django_db
def test_profession_tag_blocks_place_deletion(client, place):
    biography = Biography.objects.create(person=Person.objects.create(name="Personne test"), version=0)
    Profession.objects.create(bio=biography, position="Syndic", place=tag(place))

    response = assert_delete_blocked(client, place, "Professions")
    expected_url = reverse(
        "biography-display",
        kwargs={"person_id": biography.person_id, "version": biography.version},
    )
    assert expected_url in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["place", "place2", "destination"])
def test_every_bibliography_tag_field_blocks_place_deletion(client, place, field):
    biblio = make_biblio(**{field: tag(place)})

    response = assert_delete_blocked(client, place, "Bibliographies — champs de lieu")
    assert reverse("display-bibliography", args=[biblio.pk]) in response.content.decode()


@pytest.mark.django_db
def test_structured_bibliography_subject_blocks_place_deletion(client, place):
    biblio = make_biblio()
    biblio.subj_place.add(place)

    response = assert_delete_blocked(client, place, "Bibliographies — sujets lieux")
    assert reverse("display-bibliography", args=[biblio.pk]) in response.content.decode()
    assert biblio.subj_place.filter(pk=place.pk).exists()


@pytest.mark.django_db
def test_model_delete_cannot_bypass_place_reference_guard(place):
    Transcription.objects.create(text=tag(place))
    place_id = place.pk

    with pytest.raises(ProtectedError, match="Transcriptions: 1"):
        with transaction.atomic():
            place.delete()

    assert PlaceRecord.objects.filter(pk=place_id).exists()


@pytest.mark.django_db
def test_bulk_delete_is_atomic_when_one_place_is_referenced(place):
    other = PlaceRecord.objects.create(name="Genève", category=place.category, creator=place.creator)
    Transcription.objects.create(text=tag(place))

    with pytest.raises(ProtectedError):
        with transaction.atomic():
            PlaceRecord.objects.filter(pk__in=[place.pk, other.pk]).delete()

    assert set(PlaceRecord.objects.filter(pk__in=[place.pk, other.pk]).values_list("pk", flat=True)) == {
        place.pk,
        other.pk,
    }


@pytest.mark.django_db
def test_admin_delete_preview_lists_non_relational_place_references(place, django_user_model):
    Transcription.objects.create(text=tag(place))
    admin_user = django_user_model.objects.create_superuser("place-admin", "admin@example.org", "pw")
    request = RequestFactory().get("/")
    request.user = admin_user

    _deleted, _counts, _missing_permissions, protected = PlaceRecordAdmin(
        PlaceRecord,
        fiches_admin,
    ).get_deleted_objects(PlaceRecord.objects.filter(pk=place.pk), request)

    assert any("Lausanne — Transcriptions (1)" in str(item) for item in protected)


@pytest.mark.django_db
def test_unreferenced_place_can_still_be_deleted(place):
    place_id = place.pk

    place.delete()

    assert not PlaceRecord.objects.filter(pk=place_id).exists()


@pytest.mark.django_db
def test_place_link_audit_passes_with_valid_links(place):
    Transcription.objects.create(text=tag(place))
    stdout = StringIO()

    call_command("audit_place_links", stdout=stdout)

    assert "no orphan references" in stdout.getvalue()


@pytest.mark.django_db
def test_place_link_audit_reports_orphan_html_tags():
    Transcription.objects.create(
        text='<a class="ll-tag ll-tag-place" data-place="987654" href="/fiches/lieu/987654/">Perdu</a>'
    )
    stdout = StringIO()

    with pytest.raises(CommandError, match="1 orphan reference"):
        call_command("audit_place_links", stdout=stdout)

    assert "fiches.Transcription" in stdout.getvalue()
    assert "missing place 987654" in stdout.getvalue()


@pytest.mark.django_db
def test_place_link_audit_reports_orphan_structured_subject():
    biblio = make_biblio()
    through = Biblio.subj_place.through
    through.objects.create(biblio_id=biblio.pk, placerecord_id=987654)

    orphans = find_orphan_place_links()

    assert [(orphan.object_pk, orphan.place_id) for orphan in orphans] == [
        (through.objects.get().pk, 987654),
    ]
