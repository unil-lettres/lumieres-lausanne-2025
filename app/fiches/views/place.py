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

"""Views for the place fiche (Lieu): public read view and the create/edit form."""

from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from fiches.forms import NoteFormPlace, PlaceRecordForm
from fiches.models import NotePlace, PlaceRecord, PlaceReferenceSite, PlaceVariant

# Inline formsets for the satellite tables edited alongside a place fiche.
PlaceVariantFormSet = inlineformset_factory(PlaceRecord, PlaceVariant, fields=["name"], extra=1, can_delete=True)
PlaceReferenceSiteFormSet = inlineformset_factory(
    PlaceRecord, PlaceReferenceSite, fields=["reference_site", "identifier"], extra=1, can_delete=True
)
NotePlaceFormSet = inlineformset_factory(PlaceRecord, NotePlace, form=NoteFormPlace, extra=0, can_delete=True)


def get_place_form_def(form):
    """Build the fieldset/formset layout consumed by ``edition/place.html``.

    Each entry is either a named form field or a formset partial template,
    following the same convention as the biography edit form.
    """
    formdef = {
        "fieldsets": (
            {"title": None, "fields": ({"name": "name"}, {"name": "category"})},
            {
                "title": "Variantes",
                "fields": ({"name": None, "template": "fiches/edition/place/variant_formset.html"},),
            },
            {"title": "Lieux associés", "fields": ({"name": "related_places"},)},
            {
                "title": "Sites de référence",
                "fields": ({"name": None, "template": "fiches/edition/place/reference_formset.html"},),
            },
            {"title": "Notes", "fields": ({"name": None, "template": "fiches/edition/note_formset.html"},)},
        )
    }
    visible = {f.html_name: f for f in form.visible_fields()}
    for fieldset in formdef["fieldsets"]:
        for field in fieldset["fields"]:
            if field["name"] and field["name"] in visible:
                field["field"] = visible[field["name"]]
    return formdef


def _visible_notes(place, user):
    """Return the place notes the user is allowed to edit (access-filtered)."""
    if not getattr(place, "pk", None):
        return NotePlace.objects.none()
    notes = NotePlace.objects.filter(owner_id=place.pk)
    if not user.is_staff:
        notes = notes.filter(
            Q(access_owner=user) | Q(access_groups__isnull=True) | Q(access_groups__in=user.usergroup_set.all())
        ).distinct()
    if not user.has_perm("fiches.can_publish_note"):
        notes = notes.filter(~Q(access_public=True)).distinct()
    return notes


def _save_place(form, formsets, user):
    """Persist the place and its inline formsets; set the owner on creation."""
    place = form.save(commit=False)
    if not place.access_owner_id:
        place.access_owner = user
    place.save()
    form.save_m2m()
    for formset in formsets:
        formset.instance = place
        formset.save()
    return place


def display(request, place_id):
    """Public read view for a place fiche (visitors may consult it via tags)."""
    place = get_object_or_404(PlaceRecord, pk=place_id)
    return render(request, "fiches/display/place.html", {"place": place})


@never_cache
def edit(request, place_id=None, create_place=False):
    """Create or edit a place fiche with its variant, reference and note inlines."""
    required_perm = "fiches.add_placerecord" if create_place else "fiches.change_placerecord"
    if not request.user.has_perm(required_perm):
        return HttpResponseForbidden("Accès non autorisé")

    place = PlaceRecord() if create_place else get_object_or_404(PlaceRecord, pk=place_id)
    posted = (request.POST,) if request.method == "POST" else ()
    form = PlaceRecordForm(*posted, instance=place)
    variant_formset = PlaceVariantFormSet(*posted, instance=place)
    reference_formset = PlaceReferenceSiteFormSet(*posted, instance=place)
    note_formset = NotePlaceFormSet(*posted, instance=place, queryset=_visible_notes(place, request.user))
    formsets = (variant_formset, reference_formset, note_formset)

    if request.method == "POST" and all([form.is_valid(), *[fs.is_valid() for fs in formsets]]):
        place = _save_place(form, formsets, request.user)
        target = "place-edit" if request.POST.get("__continue") == "on" else "place-display"
        return redirect(target, place_id=place.pk)

    public_notes = None
    if getattr(place, "pk", None) and not request.user.has_perm("fiches.can_publish_note"):
        public_notes = NotePlace.objects.filter(owner_id=place.pk, access_public=True)

    context = {
        "edition": True,
        "ext_template": "fiches/edition/edit_base2.html",
        "form": form,
        "model": PlaceRecord,
        "new_object": create_place,
        "place_formdef": get_place_form_def(form),
        "variantFormset": variant_formset,
        "referenceFormset": reference_formset,
        "noteFormset": note_formset,
        "publicNotes": public_notes,
        "prev_url": request.META.get("HTTP_REFERER", None),
    }
    return render(request, "fiches/edition/place.html", context)


def create(request):
    """Entry point for creating a new place fiche (blank edit form)."""
    return edit(request, place_id=None, create_place=True)


def delete(request, place_id):
    """Delete a place fiche (Admin only)."""
    if not request.user.has_perm("fiches.delete_placerecord"):
        return HttpResponseForbidden("Accès non autorisé")
    place = get_object_or_404(PlaceRecord, pk=place_id)
    place.delete()
    return redirect("workspace-main")
