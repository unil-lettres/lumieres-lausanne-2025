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

"""Shared reference-site link form field/widget (référentiels).

Both the place fiche and the biography fiche let an editor attach permalinks on
external reference sites (Wikidata, GeoNames, IdRef…). The widget and field live
here — outside the ``forms`` package and with model imports kept lazy — so the
biography form, which is declared in the models module, can reuse them without a
circular import.

A référentiel is scoped to the kind of fiche it makes sense on (the
``applies_to_person`` / ``applies_to_place`` flags on :class:`ReferenceSite`):
pass ``applies="person"`` or ``applies="place"`` to only offer the relevant ones.
"""

from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe

# Map the caller-facing scope to the ReferenceSite applicability flag.
_APPLIES_FLAG = {"person": "applies_to_person", "place": "applies_to_place"}


class ReferenceLinkWidget(forms.Widget):
    """Render reference-site links as chips with a derived permalink.

    Existing links show as a chip (référentiel + identifier + clickable permalink
    + delete button); a new link is added from a référentiel dropdown + an
    identifier input. The permalink is built client-side from the référentiel's
    ``base_url`` (carried on each option as ``data-base-url``).

    ``applies`` ("person" / "place" / ``None``) restricts the *add* dropdown to
    the référentiels relevant for that fiche; already-saved links always render,
    whatever their site's current scope.
    """

    def __init__(self, applies=None, attrs=None):
        """Store the applicability scope and build the base widget."""
        self.applies = applies
        super().__init__(attrs)

    def value_from_datadict(self, data, files, name):
        """Return the list of "siteId|identifier" payload entries (QueryDict or dict)."""
        if hasattr(data, "getlist"):
            return data.getlist(name)
        value = data.get(name)
        if value is None:
            return []
        return list(value) if isinstance(value, (list, tuple)) else [value]

    def render(self, name, value, attrs=None, renderer=None):
        """Render the existing reference chips plus the référentiel add box."""
        from fiches.models import ReferenceSite

        # All sites render existing chips; only in-scope ones can be added.
        site_by_id = {str(site.id): site for site in ReferenceSite.objects.all()}
        flag = _APPLIES_FLAG.get(self.applies)
        add_sites = ReferenceSite.objects.filter(**{flag: True}) if flag else ReferenceSite.objects.all()

        out = ['<div class="reflist_container dynamiclist_container">', '<div class="dynamiclist_values">']
        for item in value or []:
            text = str(item)
            if "|" not in text:
                continue
            site_id, identifier = (part.strip() for part in text.split("|", 1))
            site = site_by_id.get(site_id)
            if not site or not identifier:
                continue
            url = site.build_url(identifier)
            out.append(
                '<span class="reflist_value_entry dynamiclist_value_entry">'
                f'<span class="reflist_value_label">{escape(site.name)} {escape(identifier)}</span> '
                f'<a class="reflist_value_link" href="{escape(url)}" target="_blank" rel="noopener">{escape(url)}</a>'
                f'<input type="hidden" name="{name}" value="{escape(text)}" /></span>'
            )
        out.append("</div>")
        out.append('<span class="dynamiclist_addbox"><select class="reflist_site_select">')
        out.append('<option value="">[ choisir un référentiel ]</option>')
        for site in add_sites:
            out.append(
                f'<option value="{site.id}" data-base-url="{escape(site.base_url)}">{escape(site.name)}</option>'
            )
        out.append('</select> <input type="text" class="reflist_id_input" placeholder="identifiant" /> ')
        out.append(
            f'<button type="button" class="reflist_addbut dynamiclist_helper_addbut helper_addbut" '
            f"onclick=\"refLinkWidget.addToList(this, '{name}'); return false;\">"
            "<span>Ajouter un site de référence</span></button>"
        )
        out.append("</span></div>")
        return mark_safe("".join(out))


class ReferenceLinkField(forms.Field):
    """Clean the reference widget payload into ``(site_id, identifier)`` pairs.

    Keeps at most one link per référentiel (matching the model's uniqueness
    constraint) and drops entries pointing to an unknown or out-of-scope
    référentiel.
    """

    def __init__(self, applies=None, **kwargs):
        """Build the field with an applicability-scoped widget."""
        self.applies = applies
        kwargs.setdefault("widget", ReferenceLinkWidget(applies=applies))
        super().__init__(**kwargs)

    def clean(self, value):
        """Return a list of ``(site_id, identifier)`` tuples, one per référentiel."""
        from fiches.models import ReferenceSite

        flag = _APPLIES_FLAG.get(self.applies)
        sites = ReferenceSite.objects.filter(**{flag: True}) if flag else ReferenceSite.objects.all()
        valid_ids = set(sites.values_list("id", flat=True))
        pairs, seen = [], set()
        for item in value or []:
            text = str(item).strip()
            if "|" not in text:
                continue
            site_id, identifier = (part.strip() for part in text.split("|", 1))
            if not site_id.isdigit() or not identifier:
                continue
            site_id = int(site_id)
            if site_id not in valid_ids or site_id in seen:
                continue
            seen.add(site_id)
            pairs.append((site_id, identifier))
        return pairs
