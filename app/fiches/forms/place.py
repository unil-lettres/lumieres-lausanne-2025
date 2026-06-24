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

"""Forms for the place fiche (Lieu): the main form and its note form."""

from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe

from fiches.forms.base import NoteFormBase
from fiches.models.misc import NotePlace, PlaceRecord
from fiches.widgets import DynamicList


# ===============================
# Place fiche forms (Lieux)
# ===============================
class ReferenceLinkWidget(forms.Widget):
    """Render a place's reference-site links as chips with a derived permalink.

    Existing links show as a chip (référentiel + identifier + clickable permalink
    + delete button); a new link is added from a référentiel dropdown + an
    identifier input. The permalink is built client-side from the référentiel's
    ``base_url`` (carried on each option as ``data-base-url``).
    """

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

        sites = list(ReferenceSite.objects.all())
        site_by_id = {str(site.id): site for site in sites}
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
                f'<span class="reflist_value_label">{escape(site.name)} {escape(identifier)}</span> '
                f'<a class="reflist_value_link" href="{escape(url)}" target="_blank" rel="noopener">{escape(url)}</a>'
                f'<input type="hidden" name="{name}" value="{escape(text)}" /></span>'
            )
        out.append("</div>")
        out.append('<span class="dynamiclist_addbox"><select class="reflist_site_select">')
        out.append('<option value="">[ choisir un référentiel ]</option>')
        for site in sites:
            out.append(
                f'<option value="{site.id}" data-base-url="{escape(site.base_url)}">{escape(site.name)}</option>'
            )
        out.append('</select> <input type="text" class="reflist_id_input" placeholder="identifiant" /> ')
        out.append(
            f'<button type="button" class="reflist_addbut dynamiclist_helper_addbut helper_addbut" '
            f"onclick=\"placeRefWidget.addToList(this, '{name}'); return false;\">"
            "<span>Ajouter un site de référence</span></button>"
        )
        out.append("</span></div>")
        return mark_safe("".join(out))


class ReferenceLinkField(forms.Field):
    """Clean the reference widget payload into ``(site_id, identifier)`` pairs.

    Keeps at most one link per référentiel (matching the model's uniqueness
    constraint) and drops entries pointing to an unknown référentiel.
    """

    widget = ReferenceLinkWidget

    def clean(self, value):
        """Return a list of ``(site_id, identifier)`` tuples, one per référentiel."""
        from fiches.models import ReferenceSite

        valid_ids = set(ReferenceSite.objects.values_list("id", flat=True))
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


class VariantTagField(forms.Field):
    """Free-text tag field for place variants.

    Renders with the project's ``DynamicList`` widget (chips + add input, like
    the biography "Personne" field) and cleans the ``"id|label"`` / ``"|label"``
    payload down to a de-duplicated list of variant names.
    """

    def clean(self, value):
        """Return a de-duplicated list of variant names from the widget payload."""
        names, seen = [], set()
        for item in value or []:
            text = str(item).strip()
            if "|" in text:
                text = text.split("|", 1)[1]
            text = text.strip()
            if text and text not in seen:
                seen.add(text)
                names.append(text)
        return names


class MultiplePlaceField(forms.ModelMultipleChoiceField):
    """Accept the DynamicList payload ("id|label" or a bare id) for related places.

    Only existing places can be associated (no inline creation: a place requires
    a category), so unknown entries are rejected by the parent queryset.
    """

    def clean(self, value):
        """Normalise the widget payload to primary keys, then validate."""
        if not value:
            return super().clean(value)
        normalized = []
        for item in value:
            text = str(item).strip()
            if "|" in text:
                text = text.split("|", 1)[0].strip()
            if text:
                normalized.append(text)
        return super().clean(normalized)


class NoteFormPlace(NoteFormBase):
    """Form for a NotePlace (rich-text note attached to a place fiche)."""

    # Virtual field for note_formset.html template compatibility (cf. NoteFormBiblio).
    rte_type = forms.CharField(initial="CKE", widget=forms.HiddenInput(), required=False)

    class Meta(NoteFormBase.Meta):
        model = NotePlace
        fields = "__all__"


class PlaceRecordForm(forms.ModelForm):
    """Main form for creating/editing a place fiche (Lieu).

    Like the biblio and biography fiche forms, this exposes only the fiche's
    own content fields. A place fiche is publicly readable; access control is
    carried by its notes, not by the fiche, so no access field is shown here
    and ``access_owner`` is set programmatically to the current editor.
    """

    variants = VariantTagField(
        required=False,
        label="Variantes",
        widget=DynamicList(add_title="Ajouter une variante", placeholder="nom de la variante"),
    )
    reference_links = ReferenceLinkField(required=False, label="Sites de référence")
    related_places = MultiplePlaceField(
        queryset=PlaceRecord.objects.all(),
        required=False,
        label="Lieux associés",
        widget=DynamicList(
            rel=PlaceRecord.related_places,
            add_title="Ajouter un lieu",
            placeholder="rechercher un lieu…",
        ),
    )

    class Meta:
        model = PlaceRecord
        fields = ["name", "category", "related_places"]

    def __init__(self, *args, **kwargs):
        """Exclude self from related places and preload variants and reference links."""
        super().__init__(*args, **kwargs)
        # A place cannot be associated with itself.
        if self.instance and self.instance.pk:
            self.fields["related_places"].queryset = PlaceRecord.objects.exclude(pk=self.instance.pk)
            self.initial.setdefault("variants", list(self.instance.variants.values_list("name", flat=True)))
            self.initial.setdefault(
                "reference_links",
                [f"{link.reference_site_id}|{link.identifier}" for link in self.instance.reference_links.all()],
            )
