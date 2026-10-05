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

"""Place HTML must become escaped citation text without changing editorial data."""

import re
from datetime import UTC, date, datetime
from html.parser import HTMLParser

import pytest
from django.contrib.auth.models import User
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import SafeData, mark_safe
from fiches.models import ContributionType, PlaceCategory, PlaceRecord
from fiches.models.documents.document import Biblio, ContributionDoc, DocumentLanguage, DocumentType, Transcription
from fiches.models.person.person import Person
from fiches.place_text import place_plaintext
from fiches.views.place import tagged_biblios_writing

BREDA = (
    '<a class="ll-tag ll-tag-place" data-place="10" href="/fiches/lieu/10/" '
    'data-cke-saved-href="/fiches/lieu/10/" title="Breda (Ville/Village)">Breda</a>'
)


class RenderedText(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.feed(source)

    def handle_data(self, data):
        self.parts.append(data)


def visible_text(source):
    return " ".join("".join(RenderedText(source).parts).split())


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (None, ""),
        ("", ""),
        (" \n\t", ""),
        ("<p><br></p>", ""),
        ("<div>&nbsp;&#160;</div>", ""),
        ("Breda", "Breda"),
        (BREDA, "Breda"),
        (f"[{BREDA}]", "[Breda]"),
        (f"{BREDA} et <a>Lausanne</a>", "Breda et Lausanne"),
        ("Berlin [i.e. Lausanne]", "Berlin [i.e. Lausanne]"),
        ("Genève & Lausanne", "Genève & Lausanne"),
        ("L'Isle-sur-la-Sorgue", "L'Isle-sur-la-Sorgue"),
        ("<a>Bâle&nbsp;&amp;&nbsp;Genève</a>", "Bâle & Genève"),
        ("Gen&#232;ve &#x26; Lausanne", "Genève & Lausanne"),
        ("&amp;amp;", "&amp;"),
        ("&lt;Lausanne&gt;", "<Lausanne>"),
        ("Yverdon-<em>les</em>-Bains", "Yverdon-les-Bains"),
        ("<div>Breda</div><div>Lausanne</div>", "Breda Lausanne"),
        ("Breda<br>Lausanne<br/>Genève<br />Berne", "Breda Lausanne Genève Berne"),
        ('<a title="A > B"><strong>Breda</strong></a>', "Breda"),
        ("Breda<!-- editor comment -->", "Breda"),
        ("<script>alert(1)</script><style>.x{}</style>Breda", "Breda"),
        ("<a>Breda", "Breda"),
        ("Breda <", "Breda <"),
    ],
)
def test_place_plaintext(source, expected):
    assert place_plaintext(source) == expected


@pytest.mark.parametrize("safe_input", [False, True])
@pytest.mark.parametrize("source", ["&lt;img src=x onerror=alert(1)&gt;", "&lt;script&gt;alert(1)&lt;/script&gt;"])
def test_decoded_text_stays_escaped_even_for_safe_input(source, safe_input):
    value = mark_safe(source) if safe_input else source
    result = place_plaintext(value)
    assert not isinstance(result, SafeData)
    template = Template("{% load fiches_extras %}{{ value|place_plaintext }}")
    rendered = template.render(Context({"value": value}))
    assert rendered == escape(result)
    assert visible_text(rendered) == result
    assert "<img" not in rendered and "<script" not in rendered


@pytest.fixture
def manuscript(db):
    DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)
    doc_type = DocumentType.objects.create(id=5, name="Manuscrit", code=5)
    return Biblio.objects.create(
        title="Lettre à Isaac van Schinne",
        litterature_type="p",
        document_type=doc_type,
        creator=User.objects.create(username="owner"),
        place=BREDA,
        date=date(1762, 6, 30),
        date_f="%d %m %Y",
        cote="NL-HaNA, 1.10.75.01, inv.nr. 25",
    )


def citation_block(body):
    return re.search(r'class="field_group cite_as".*?class="field_value">(.*?)</div>', body, re.S).group(1)


@pytest.mark.django_db
def test_transcription_citation_and_linked_place_are_preserved(client, manuscript):
    author = Person.objects.create(name="Mingard [-van Schinne], Everdina Henriette")
    contribution_type = ContributionType.objects.create(name="Auteur", type="doc", code=0)
    ContributionDoc.objects.create(document=manuscript, person=author, contribution_type=contribution_type)
    editor = User.objects.create(username="kees", first_name="Kees", last_name="van Strien")
    trans = Transcription.objects.create(
        manuscript_b=manuscript,
        access_public=True,
        access_private=False,
        author=editor,
        cite_author=True,
        published_date=datetime(2026, 10, 2, 12, tzinfo=UTC),
        modified_date=datetime(2026, 10, 3, 12, tzinfo=UTC),
    )
    response = client.get(reverse("transcription-display", args=[trans.pk]), secure=True)
    assert response.status_code == 200
    citation = citation_block(response.content.decode())
    assert visible_text(citation) == (
        "Mingard [-van Schinne], Everdina Henriette, Lettre à Isaac van Schinne, Breda, 30 juin 1762, "
        "cote NL-HaNA, 1.10.75.01, inv.nr. 25. Selon la transcription établie par Kees van Strien pour "
        "Lumières.Lausanne (Université de Lausanne), mise en ligne le 02.10.2026, version du 03.10.2026, "
        f"url: https://testserver/fiches/trans/{trans.pk}/."
    )
    assert "<em>Lettre à Isaac van Schinne</em>" in citation
    assert "ll-tag-place" not in citation
    detail = client.get(reverse("display-bibliography", args=[manuscript.pk]))
    assert detail.status_code == 200
    assert BREDA in detail.content.decode()
    category = PlaceCategory.objects.create(name="Ville/Village")
    place = PlaceRecord.objects.create(id=10, name="Breda", category=category)
    assert manuscript in tagged_biblios_writing(place)
    manuscript.refresh_from_db()
    assert manuscript.place == BREDA


@pytest.mark.django_db
@pytest.mark.parametrize("place", ["", "<p>&nbsp;</p>", "<div><br></div>"])
def test_transcription_citation_defaults_after_normalization(client, manuscript, place):
    manuscript.place = place
    manuscript.save()
    trans = Transcription.objects.create(manuscript_b=manuscript, access_public=True, access_private=False)
    response = client.get(reverse("transcription-display", args=[trans.pk]))
    assert response.status_code == 200
    assert "[s.l.], 30 juin 1762" in visible_text(citation_block(response.content.decode()))


@pytest.mark.django_db
@pytest.mark.parametrize("doc_type_id", [1, 5])
@pytest.mark.parametrize(
    "place,expected",
    [(BREDA, "Breda"), ("<a>Bâle&nbsp;&amp;&nbsp;Genève</a>", "Bâle & Genève"), ("<div>&nbsp;</div>", "[s.l.]")],
)
def test_shared_citations_normalize_manuscripts_and_books(manuscript, doc_type_id, place, expected):
    manuscript.document_type, _ = DocumentType.objects.get_or_create(
        id=doc_type_id, defaults={"name": "Livre", "code": 1}
    )
    manuscript.place = place
    rendered = render_to_string(
        "fiches/bibliography_references/biblio_template.html",
        {"ref": manuscript, "nolink": True, "noManBiblioLink": True},
    )
    assert expected in visible_text(rendered)
    assert "ll-tag-place" not in rendered
    assert "&amp;nbsp;" not in rendered


@pytest.mark.django_db
@pytest.mark.parametrize("place2,expected", [("<p>&nbsp;</p>", ""), ("<a>Genève &amp; Bâle</a>", "Genève & Bâle")])
def test_second_place_has_no_markup_or_empty_separator(manuscript, place2, expected):
    manuscript.document_type = DocumentType.objects.create(id=1, name="Livre", code=1)
    manuscript.place2 = place2
    rendered = render_to_string(
        "fiches/bibliography_references/biblio_template.html", {"ref": manuscript, "nolink": True}
    )
    places = re.findall(r'<span class="place">(.*?)</span>', rendered, re.S)
    assert [visible_text(p) for p in places] == ([", Breda", f"; {expected}"] if expected else [", Breda"])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "place,expected",
    [
        (BREDA, "Breda"),
        ("<a>Bâle&nbsp;&amp;&nbsp;Genève</a>", "Bâle & Genève"),
        ("<p>Breda</p><p>Lausanne</p>\nGenève", "Breda Lausanne Genève"),
        ("<p>&nbsp;</p>", ""),
    ],
)
def test_endnote_exports_one_plain_place_line(client, manuscript, place, expected):
    manuscript.place = place
    manuscript.save()
    response = client.get(reverse("endnote-biblio-one", args=[manuscript.pk]))
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    lines = response.content.decode().splitlines()
    assert [line for line in lines if line.startswith("LI-")] == [f"LI- {expected}"]
    assert "TI- Lettre à Isaac van Schinne" in lines
    assert "DA- 1762-06-30" in lines
    manuscript.refresh_from_db()
    assert manuscript.place == place
