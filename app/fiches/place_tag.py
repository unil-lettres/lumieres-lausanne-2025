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

"""Place-tagging form widget for the biography place fields (§2.2).

The biography place fields (birth/death place, origin, profession place) can be
tagged with a place fiche, exactly like the transcription "Lieu" button: the
tagged text becomes an ``<a class="ll-tag ll-tag-place" …>`` link that is
clickable in read mode. Because a plain ``<input>`` cannot show such a link,
this widget renders a compact ``contenteditable`` holding the field HTML plus a
"Lieu" button; the contenteditable's HTML is mirrored into a hidden input, which
is what the form submits. The button reuses the place search/create back-end.

The widget lives outside the ``forms`` package, with no model import, so the
biography form (declared in the models module) can use it without a circular
import.
"""

from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe


class PlaceTagWidget(forms.Widget):
    """Compact contenteditable + "Lieu" button producing place-tag HTML.

    The stored/submitted value is editor-entered HTML (a place tag or plain
    text), rendered raw into the contenteditable so a tag shows as a link — the
    same trust model as the transcription fields, which also round-trip HTML.
    """

    def render(self, name, value, attrs=None, renderer=None):
        """Render the contenteditable, the mirrored hidden input and the button."""
        value = value or ""
        attrs = attrs or {}
        field_id = attrs.get("id") or f"id_{name}"
        return mark_safe(
            f'<div class="placetag" data-name="{escape(name)}">'
            f'<div id="{escape(field_id)}" class="placetag_editable" contenteditable="true">{value}</div>'
            f'<input type="hidden" name="{escape(name)}" class="placetag_value" value="{escape(value)}" />'
            f'<button type="button" class="placetag_button" title="Lier un lieu" tabindex="-1">Lieu</button>'
            f"</div>"
        )
