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

"""Unit tests for document.py models — __str__, get_absolute_url, manager
methods and simple business logic (DB-free where possible)."""

import pytest
from django.contrib.auth.models import User
from fiches.models.documents.document import (
    Biblio,
    ContributionDoc,
    ContributionMan,
    Depot,
    Document,
    DocumentLanguage,
    DocumentType,
    Manuscript,
    ManuscriptType,
    Transcription,
    TranscriptionManager,
)


# ---------------------------------------------------------------------------
# DB-free __str__ helpers
# ---------------------------------------------------------------------------


def test_depot_str():
    assert str(Depot(name="Bibliothèque nationale")) == "Bibliothèque nationale"


def test_manuscript_type_str():
    assert str(ManuscriptType(name="Autographe")) == "Autographe"


def test_biblio_str():
    b = Biblio.__new__(Biblio)
    b.title = "Émile ou De l'éducation"
    assert str(b) == "Émile ou De l'éducation"


def test_document_str_with_title():
    doc = Document()
    doc.title = "Mon fichier"
    assert str(doc) == "Mon fichier"


def test_document_str_no_title_uses_basename():
    doc = Document()
    doc.title = ""
    doc.file.name = "files/2024/01/rapport.pdf"
    assert str(doc) == "rapport.pdf"


def test_contribution_doc_str_none_person_and_type():
    contrib = ContributionDoc(person=None, contribution_type=None)
    result = str(contrib)
    assert "Aucun contributeur" in result
    assert "Aucun type" in result


def test_contribution_man_str():
    result = str(ContributionMan(person=None, contribution_type=None))
    assert result == "None (None)"


def test_transcription_str_no_manuscript():
    t = Transcription()
    t.manuscript = None
    t.manuscript_b = None
    assert str(t) == "---"


def test_transcription_cite_authors_empty():
    t = Transcription(cite_author=False, cite_author2=False)
    assert t.cite_authors() == ""


# ---------------------------------------------------------------------------
# Biblio fixtures & DB tests
# ---------------------------------------------------------------------------


@pytest.fixture
def doc_type(db):
    return DocumentType.objects.create(name="Livre", code=1)


@pytest.fixture
def lang(db):
    return DocumentLanguage.objects.create(name="Français", ordering=1)


@pytest.fixture
def biblio(doc_type, lang):
    return Biblio.objects.create(
        title="Le Contrat social", litterature_type="p", document_type=doc_type, language=lang
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(username="doc_user", password="x")


# ---------------------------------------------------------------------------
# Biblio DB tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_biblio_get_document_types_returns_queryset(doc_type):
    qs = Biblio.getDocumentTypes()
    assert doc_type in qs


@pytest.mark.django_db
def test_biblio_get_absolute_url_contains_pk(biblio):
    url = biblio.get_absolute_url()
    assert str(biblio.pk) in url


@pytest.mark.django_db
def test_biblio_update_first_author_no_contribs_clears_field(biblio):
    biblio.updateFirstAuthor()
    biblio.refresh_from_db()
    assert biblio.first_author is None
    assert biblio.first_author_name == ""


# ---------------------------------------------------------------------------
# Manuscript DB tests
# ---------------------------------------------------------------------------


def test_manuscript_str():
    # DB-free: __str__ only accesses self.title
    m = Manuscript.__new__(Manuscript)
    m.title = "Lettre à d'Alembert"
    assert str(m) == "Lettre à d'Alembert"


def test_manuscript_get_absolute_url_bug_raises_no_reverse():
    # Manuscript.get_absolute_url() passes kwargs={"pk": …} but the URL pattern
    # expects man_id — pre-existing mismatch. Documents current (broken) behaviour.
    from django.urls import NoReverseMatch

    m = Manuscript.__new__(Manuscript)
    m.id = 42
    with pytest.raises(NoReverseMatch):
        m.get_absolute_url()


def test_manuscript_get_first_author_name_bug_raises_attribute_error():
    # Manuscript.getFirstAuthorName() references contributionman_set but the
    # related_name is contribution_mans_documents — pre-existing bug in the code.
    # This test documents the current (broken) behaviour.
    m = Manuscript.__new__(Manuscript)
    m.id = None
    with pytest.raises(AttributeError):
        m.getFirstAuthorName()


# ---------------------------------------------------------------------------
# TranscriptionManager
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_transcription_manager_latest_published_by_date_returns_queryset():
    qs = Transcription.objects.latest_published_by_date(count=5)
    assert list(qs) == []


# ---------------------------------------------------------------------------
# Transcription DB tests
# ---------------------------------------------------------------------------


@pytest.fixture
def transcription(user):
    return Transcription.objects.create(access_owner=user)


@pytest.mark.django_db
def test_transcription_get_absolute_url_contains_pk(transcription):
    url = transcription.get_absolute_url()
    assert str(transcription.pk) in url


@pytest.mark.django_db
def test_transcription_reviewers_empty(transcription):
    assert list(transcription.reviewers) == []


@pytest.mark.django_db
def test_transcription_cite_authors_with_author(user):
    user.first_name = "Jean-Jacques"
    user.last_name = "Rousseau"
    user.save()
    t = Transcription.objects.create(access_owner=user, author=user, cite_author=True)
    result = t.cite_authors()
    assert "Jean-Jacques Rousseau" in result
    assert "pour" in result


@pytest.mark.django_db
def test_transcription_cite_authors_not_cited(user):
    t = Transcription.objects.create(access_owner=user, author=user, cite_author=False)
    assert t.cite_authors() == ""
