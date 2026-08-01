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

"""A person tagged inside a transcription must surface on that person's fiche.

Client report (Béatrice, 2026-07-15): indexing a name from the manuscript's
biblio fiche lists the manuscript under « Littérature primaire », but tagging
the same name inside the transcription text showed nothing at all.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fiches.models import Biblio, Person
from fiches.models.documents import DocumentLanguage
from fiches.models.documents.document import DocumentType, Transcription
from fiches.views.biography import build_person_biblio_dict, manuscripts_tagging_person

MANUSCRIT = 5


class Reader:
    """Stand-in for a visitor who may not read unpublished transcriptions."""

    def __init__(self, privileged=False):
        self.privileged = privileged

    def has_perm(self, *args, **kwargs):
        return self.privileged


@pytest.fixture
def person(db):
    return Person.objects.create(name="Charrière de Sévery, Catherine de")


def make_manuscript(title):
    DocumentLanguage.objects.get_or_create(name="Français", defaults={"ordering": 1})
    doctype, _ = DocumentType.objects.get_or_create(id=MANUSCRIT, defaults={"name": "Manuscrit", "code": MANUSCRIT})
    return Biblio.objects.create(title=title, litterature_type="p", document_type=doctype)


def tag(person):
    return (
        f'<a class="ll-tag ll-tag-person" data-person="{person.pk}" '
        f'href="/fiches/bio/{person.pk}/" title="{person.name}">M Poinlou</a>'
    )


@pytest.mark.django_db
def test_manuscript_of_a_tagged_transcription_is_returned(person):
    manuscript = make_manuscript("Lettre à Pierre Desmaizeaux")
    Transcription.objects.create(
        text=f"<p>au citoyen {tag(person)} salut</p>",
        manuscript_b=manuscript,
        published_date=datetime(2020, 1, 1, tzinfo=UTC),
    )

    assert list(manuscripts_tagging_person(person, Reader())) == [manuscript.id]


@pytest.mark.django_db
def test_legacy_single_quoted_person_tag_is_returned(person):
    manuscript = make_manuscript("Lettre ancienne")
    Transcription.objects.create(
        text=f"<p><a class='ll-tag-person' data-person = '{person.pk}'>Barbeyrac</a></p>",
        manuscript_b=manuscript,
        published_date=datetime(2020, 1, 1, tzinfo=UTC),
    )

    assert list(manuscripts_tagging_person(person, Reader())) == [manuscript.id]


@pytest.mark.django_db
def test_a_transcription_tagging_someone_else_is_ignored(person):
    other = Person.objects.create(name="Girard, Grégoire")
    Transcription.objects.create(
        text=f"<p>{tag(other)}</p>",
        manuscript_b=make_manuscript("Lettre au Père Girard"),
        published_date=datetime(2020, 1, 1, tzinfo=UTC),
    )

    assert list(manuscripts_tagging_person(person, Reader())) == []


@pytest.mark.django_db
def test_unpublished_transcription_is_hidden_from_a_plain_reader(person):
    Transcription.objects.create(text=f"<p>{tag(person)}</p>", manuscript_b=make_manuscript("Brouillon"))

    assert list(manuscripts_tagging_person(person, Reader())) == []


@pytest.mark.django_db
def test_unpublished_transcription_is_visible_to_a_privileged_reader(person):
    manuscript = make_manuscript("Brouillon")
    Transcription.objects.create(text=f"<p>{tag(person)}</p>", manuscript_b=manuscript)

    assert list(manuscripts_tagging_person(person, Reader(privileged=True))) == [manuscript.id]


@pytest.mark.django_db
def test_tagged_manuscript_lands_in_the_primary_literature_listing(person):
    """The end of the chain: what the fiche actually renders."""
    manuscript = make_manuscript("Lettre à Pierre Desmaizeaux")
    Transcription.objects.create(
        text=f"<p>{tag(person)}</p>",
        manuscript_b=manuscript,
        published_date=datetime(2020, 1, 1, tzinfo=UTC),
    )

    litt_prim = build_person_biblio_dict(person, Reader())["litt_prim"]

    assert [b.id for b in litt_prim] == [manuscript.id]


@pytest.mark.django_db
def test_a_manuscript_indexed_both_ways_is_listed_once(person):
    """subj_person and a text tag must not produce a duplicate row."""
    manuscript = make_manuscript("Lettre à Pierre Desmaizeaux")
    manuscript.subj_person.add(person)
    Transcription.objects.create(
        text=f"<p>{tag(person)}</p>",
        manuscript_b=manuscript,
        published_date=datetime(2020, 1, 1, tzinfo=UTC),
    )

    litt_prim = build_person_biblio_dict(person, Reader())["litt_prim"]

    assert [b.id for b in litt_prim] == [manuscript.id]
