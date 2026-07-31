# Copyright (C) 2010-2026 Université de Lausanne, SIER

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from fiches.forms.biblio import BiblioForm
from fiches.models import (
    Biblio,
    DocumentFile,
    DocumentLanguage,
    DocumentType,
    ObjectCollection,
    Transcription,
)


def grant(user, model, *codenames):
    user.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="fiches",
            content_type__model=model,
            codename__in=codenames,
        )
    )


@pytest.fixture
def manuscript_type(db):
    DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)
    return DocumentType.objects.create(name="Manuscript permission test", code=501)


def make_biblio(owner, manuscript_type, title="Bibliography"):
    return Biblio.objects.create(
        title=title,
        litterature_type="p",
        document_type=manuscript_type,
        creator=owner,
    )


@pytest.mark.django_db
def test_standard_biblio_delete_permission_is_limited_to_owner(
    client, django_user_model, manuscript_type, monkeypatch
):
    owner = django_user_model.objects.create_user("biblio-owner")
    actor = django_user_model.objects.create_user("biblio-actor")
    grant(actor, "biblio", "delete_biblio")
    biblio = make_biblio(owner, manuscript_type)
    deleted = []
    monkeypatch.setattr(Biblio, "delete", lambda self, *args, **kwargs: deleted.append(self.pk))
    client.force_login(actor)

    response = client.post(reverse("bibliography-delete", args=[biblio.pk]))

    assert response.status_code == 403
    assert deleted == []


@pytest.mark.django_db
def test_delete_any_biblio_permission_allows_director_override(
    client, django_user_model, manuscript_type, monkeypatch
):
    owner = django_user_model.objects.create_user("biblio-any-owner")
    director = django_user_model.objects.create_user("biblio-director")
    grant(director, "biblio", "delete_biblio", "delete_any_biblio")
    biblio = make_biblio(owner, manuscript_type)
    deleted = []
    monkeypatch.setattr(Biblio, "delete", lambda self, *args, **kwargs: deleted.append(self.pk))
    client.force_login(director)

    response = client.post(reverse("bibliography-delete", args=[biblio.pk]))

    assert response.status_code == 302
    assert deleted == [biblio.pk]


@pytest.mark.django_db
def test_standard_transcription_delete_permission_is_limited_to_owner(client, django_user_model, manuscript_type):
    owner = django_user_model.objects.create_user("trans-owner")
    actor = django_user_model.objects.create_user("trans-actor")
    grant(actor, "transcription", "delete_transcription")
    biblio = make_biblio(owner, manuscript_type)
    transcription = Transcription.objects.create(manuscript_b=biblio, author=owner, access_owner=owner)
    client.force_login(actor)

    response = client.post(reverse("transcription-delete", args=[transcription.pk]))

    assert response.status_code == 403
    assert Transcription.objects.filter(pk=transcription.pk).exists()


@pytest.mark.django_db
def test_documentfile_create_and_list_require_permission(client, django_user_model):
    actor = django_user_model.objects.create_user("file-unauthorised")
    client.force_login(actor)

    create_response = client.post(
        reverse("docfile-frame-create"),
        {
            "title": "Forbidden attachment",
            "slug": "forbidden-attachment",
            "url": "https://example.org/forbidden.pdf",
        },
    )
    list_response = client.get(reverse("docfile-frame-list"))

    assert create_response.status_code == 403
    assert list_response.status_code == 403
    assert not DocumentFile.objects.filter(slug="forbidden-attachment").exists()


@pytest.mark.django_db
def test_authorised_documentfile_creation_assigns_the_actor_as_owner(client, django_user_model):
    actor = django_user_model.objects.create_user("file-authorised")
    grant(actor, "documentfile", "add_documentfile")
    client.force_login(actor)

    response = client.post(
        reverse("docfile-frame-create"),
        {
            "title": "Owned attachment",
            "slug": "owned-attachment",
            "url": "https://example.org/owned.pdf",
        },
    )

    assert response.status_code == 302
    assert DocumentFile.objects.get(slug="owned-attachment").access_owner == actor


@pytest.mark.django_db
def test_standard_documentfile_permissions_cannot_unlink_or_delete_another_owners_file(
    client, django_user_model, manuscript_type
):
    owner = django_user_model.objects.create_user("file-owner")
    actor = django_user_model.objects.create_user("file-actor")
    grant(actor, "documentfile", "change_documentfile", "delete_documentfile")
    biblio = make_biblio(owner, manuscript_type)
    docfile = DocumentFile.objects.create(
        title="Other file",
        slug="other-file",
        url="https://example.org/other.pdf",
        access_owner=owner,
    )
    biblio.documentfiles.add(docfile)
    client.force_login(actor)

    response = client.post(
        reverse("bibliography-documentfile-remove", args=[biblio.pk, docfile.pk]),
        {"doc_id": str(biblio.pk), "docfile_id": str(docfile.pk), "docfile_delete": "on"},
    )

    assert response.status_code == 403
    assert DocumentFile.objects.filter(pk=docfile.pk).exists()
    assert biblio.documentfiles.filter(pk=docfile.pk).exists()


@pytest.mark.django_db
def test_private_collection_is_visible_only_to_its_owner(client, django_user_model):
    owner = django_user_model.objects.create_user("collection-owner")
    actor = django_user_model.objects.create_user("collection-actor")
    collection = ObjectCollection.objects.create(
        name="Private collection",
        owner=owner,
        access_owner=owner,
        access_private=True,
    )
    client.force_login(actor)

    assert client.get(reverse("collection-display", args=[collection.pk])).status_code == 403

    client.force_login(owner)
    assert client.get(reverse("collection-display", args=[collection.pk])).status_code == 200


@pytest.mark.django_db
def test_bibliography_owner_field_requires_explicit_ownership_permission(django_user_model, manuscript_type):
    ordinary = django_user_model.objects.create_user("ordinary-editor")
    director = django_user_model.objects.create_user("ownership-director")
    grant(director, "biblio", "change_biblio_ownership")
    biblio = make_biblio(ordinary, manuscript_type)

    assert BiblioForm(instance=biblio, user=ordinary).fields["creator"].disabled is True
    assert BiblioForm(instance=biblio, user=director).fields["creator"].disabled is False
