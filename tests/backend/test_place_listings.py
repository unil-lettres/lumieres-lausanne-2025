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

"""Tests for the automatic listings on a place fiche (§3.4.1 / §3.4.3)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from django.urls import reverse
from fiches.models import Biography, PlaceCategory, PlaceRecord
from fiches.models.documents import Biblio, DocumentLanguage
from fiches.models.documents.document import DocumentType, Transcription
from fiches.models.person.biography import Profession
from fiches.models.person.person import Person
from fiches.views.place import (
    tagged_biblios_printing,
    tagged_biblios_subject,
    tagged_biblios_writing,
    tagged_persons,
    tagged_transcriptions,
)


@pytest.fixture
def place(db):
    category = PlaceCategory.objects.create(name="Ville/Village")
    return PlaceRecord.objects.create(name="Lausanne", category=category)


def tag(place, label="Lausanne"):
    pid = place.id
    return f'<a class="ll-tag ll-tag-place" data-place="{pid}" href="/fiches/lieu/{pid}/" title="{label}">{label}</a>'


def make_person(name, **bio_kwargs):
    person = Person.objects.create(name=name)
    bio_kwargs.setdefault("valid", True)
    bio_kwargs.setdefault("version", 0)
    bio = Biography.objects.create(person=person, **bio_kwargs)
    return person, bio


# -- §3.4.1 persons -----------------------------------------------------------


@pytest.mark.django_db
def test_persons_lists_birth_death_and_profession_tags(place):
    p_birth, _ = make_person("Montolieu, Louis de", birth_place=tag(place), birth_date=date(1743, 1, 1))
    p_death, _ = make_person("Crousaz, Jean de", death_place=tag(place), death_date=date(1800, 1, 1))
    p_prof, bio = make_person("Voltaire, François")
    Profession.objects.create(bio=bio, position="Syndic", place=tag(place))

    names = [e["name"] for e in tagged_persons(place)]
    assert names == ["Crousaz, Jean de", "Montolieu, Louis de", "Voltaire, François"]  # alpha order


@pytest.mark.django_db
def test_persons_excludes_origin_superseded_and_untagged(place):
    make_person("Origin, Only", origin=tag(place))  # origin is excluded by spec
    make_person("Old, Superseded", birth_place=tag(place), valid=False, version=2)  # not current, not valid
    make_person("Plain, Text", birth_place="Lausanne")  # plain text, no tag
    other = PlaceRecord.objects.create(name="Berne", category=place.category)
    make_person("Other, Place", birth_place=tag(other))  # tagged with a different place

    assert tagged_persons(place) == []


@pytest.mark.django_db
def test_persons_includes_current_unvalidated_bio(place):
    # A freshly tagged biography is version 0 but not yet validated; it must show
    # (valid OR version 0 — the codebase convention).
    make_person("Fresh, Draft", birth_place=tag(place), valid=False, version=0)
    assert [e["name"] for e in tagged_persons(place)] == ["Fresh, Draft"]


@pytest.mark.django_db
def test_person_detail_formats_place_and_year(place):
    make_person("Montolieu, Louis de", birth_place=tag(place), birth_date=date(1743, 1, 1),
                death_place=tag(place, "Berne"), death_date=date(1805, 1, 1))
    entry = tagged_persons(place)[0]
    assert entry["detail"] == "Lausanne, 1743 – Berne, 1805"


@pytest.mark.django_db
def test_person_detail_omits_unknown_place(place):
    # No place known, only years -> "1733 – 1800" (spec example Crousaz, Isabelle).
    make_person("Crousaz, Isabelle de", birth_place=tag(place), birth_date=date(1733, 1, 1),
                death_date=date(1800, 1, 1))
    assert tagged_persons(place)[0]["detail"] == "Lausanne, 1733 – 1800"


# -- §3.4.3 transcriptions ----------------------------------------------------


@pytest.mark.django_db
def test_transcriptions_lists_published_with_tag_only(place):
    published = Transcription.objects.create(text=tag(place), published_date=datetime(2020, 1, 1, tzinfo=UTC))
    Transcription.objects.create(text=tag(place))  # unpublished
    Transcription.objects.create(text="no tag here", published_date=datetime(2020, 1, 1, tzinfo=UTC))

    class Anon:
        def has_perm(self, *a, **k):
            return False

    visible = list(tagged_transcriptions(place, Anon()))
    assert visible == [published]


# -- §3.4.2 bibliographic listings --------------------------------------------

LIVRE, MANUSCRIT = 1, 5  # DOCTYPE ids


def make_biblio(doctype_id, title, litt="p", **kwargs):
    # Biblio.language defaults to a "Français" DocumentLanguage created on the fly;
    # seed it with a valid ordering so the default lookup doesn't hit a NOT NULL error.
    DocumentLanguage.objects.get_or_create(name="Français", defaults={"ordering": 1})
    doctype, _ = DocumentType.objects.get_or_create(
        id=doctype_id, defaults={"name": f"type{doctype_id}", "code": doctype_id}
    )
    return Biblio.objects.create(title=title, litterature_type=litt, document_type=doctype, **kwargs)


@pytest.mark.django_db
def test_printing_lists_primary_books_tagging_lieu_or_lieu2(place):
    make_biblio(LIVRE, "Imprimé Lieu", place=tag(place))
    make_biblio(LIVRE, "Imprimé Lieu2", place2=tag(place))
    other = PlaceRecord.objects.create(name="Berne", category=place.category)
    make_biblio(LIVRE, "Autre lieu", place=tag(other))  # different place
    make_biblio(LIVRE, "Secondaire", litt="s", place=tag(place))  # secondary literature excluded
    make_biblio(MANUSCRIT, "Manuscrit", place=tag(place))  # manuscript belongs to "Lieu de rédaction"

    assert sorted(b.title for b in tagged_biblios_printing(place)) == ["Imprimé Lieu", "Imprimé Lieu2"]


@pytest.mark.django_db
def test_writing_lists_primary_manuscripts_only(place):
    make_biblio(MANUSCRIT, "Manuscrit primaire", place=tag(place))
    make_biblio(MANUSCRIT, "Manuscrit secondaire", litt="s", place=tag(place))  # secondary excluded
    make_biblio(LIVRE, "Livre", place=tag(place))  # not a manuscript

    assert [b.title for b in tagged_biblios_writing(place)] == ["Manuscrit primaire"]


@pytest.mark.django_db
def test_subject_lists_biblios_indexing_the_place(place):
    indexed = make_biblio(LIVRE, "Indexé")
    indexed.subj_place.set([place])
    make_biblio(LIVRE, "Non indexé")

    assert [b.title for b in tagged_biblios_subject(place)] == ["Indexé"]


# -- read view integration ----------------------------------------------------


@pytest.mark.django_db
def test_place_page_renders_persons_listing(client, place):
    make_person("Montolieu, Louis de", birth_place=tag(place), birth_date=date(1743, 1, 1))
    response = client.get(reverse("place-display", args=[place.id]))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Personnes" in body
    assert "Montolieu, Louis de" in body


@pytest.mark.django_db
def test_place_page_renders_book_citation(client, place):
    # Option C (#117): clickable title + full citation rendered for each entry.
    make_biblio(LIVRE, "Mon Livre", place=tag(place), date=date(1770, 1, 1))
    response = client.get(reverse("place-display", args=[place.id]))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Lieu d'impression" in body
    assert "Mon Livre" in body
    assert "biblioref-item" in body  # the full citation block is rendered
    # The place field holds tag HTML (§4.2); the citation must show the place name
    # as text, never the raw tag markup.
    assert "data-place=" not in body
    assert "ll-tag-place" not in body


@pytest.mark.django_db
def test_place_page_renders_manuscript_citation_without_error(client, place):
    # Manuscript citations exercise the user_accessible_trans branch, which the
    # nolink / noManBiblioLink flags must short-circuit (no 500).
    make_biblio(MANUSCRIT, "Mon Manuscrit", place=tag(place), date=date(1765, 1, 1))
    response = client.get(reverse("place-display", args=[place.id]))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Lieu de rédaction" in body
    assert "biblioref-item" in body
