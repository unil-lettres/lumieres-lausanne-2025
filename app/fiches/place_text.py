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

"""Plain-text projection of rich place fields for citations and exports."""

from html.parser import HTMLParser

_BREAK_TAGS = frozenset(
    {
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "li",
        "ol",
        "p",
        "pre",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
)


class _PlaceTextParser(HTMLParser):
    """Retain inline text and structural separators, excluding script/style data."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored_element = None

    def handle_starttag(self, tag, attrs):
        """Separate blocks without inserting spaces around inline place links."""
        if tag in {"script", "style"}:
            self.ignored_element = tag
        if tag in _BREAK_TAGS and self.ignored_element is None:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        """Close ignored elements and preserve the boundary after a block."""
        if tag == self.ignored_element:
            self.ignored_element = None
        if tag in _BREAK_TAGS and self.ignored_element is None:
            self.parts.append(" ")

    def handle_data(self, data):
        """Keep text; HTMLParser decodes references once without reparsing them."""
        if self.ignored_element is None:
            self.parts.append(data)


def place_plaintext(value):
    """Convert place HTML to one line of ordinary text, without altering storage.

    HTMLParser decodes entities in text exactly once. Encoded literal markup
    therefore remains text rather than being parsed a second time. The result
    is never marked safe: HTML callers must retain escaping; text exports use
    it directly. Missing-place defaults belong to the caller.
    """
    parser = _PlaceTextParser()
    parser.feed(value or "")
    parser.close()
    return " ".join("".join(parser.parts).split())
