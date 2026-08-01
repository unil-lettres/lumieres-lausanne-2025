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

"""AJAX endpoints backing the « Pers » / « Lieu » transcription tagging plugin.

Person searching and inline fiche creation live here; place searching reuses
``place_autocomplete``. Creation uses dedicated inline permissions so that the
« Directeurs » role may create a fiche from the tagging window without
conflating that responsibility with ordinary fiche creation or technical admin.
"""

from collections import Counter

from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from fiches.models import PlaceCategory, PlaceRecord
from fiches.models.person.person import Person


@require_GET
def search_person(request):
    """Search historical person authorities for transcription tagging.

    ``Person`` also stores modern secondary-literature contributors.  Those
    records are not valid named entities in a historical transcription, so the
    tagging picker deliberately searches only ``modern=False`` records.
    Multiple words are combined with AND to avoid the overly broad generic
    autocomplete behaviour.
    """
    query = (request.GET.get("q") or "").strip()
    persons = Person.objects.filter(modern=False)
    for word in query.split():
        persons = persons.filter(Q(name__icontains=word))
    results = []
    for person in persons.order_by("name", "pk")[:50]:
        label, person_id = person.format_for_ajax_search().rsplit("|", 1)
        results.append((label, person_id))
    label_counts = Counter(label.casefold() for label, _person_id in results)
    lines = [
        f"{label}{f' — fiche #{person_id}' if label_counts[label.casefold()] > 1 else ''}|{person_id}"
        for label, person_id in results
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_GET
def place_categories(request):
    """Return the place categories, for the inline-create category dropdown."""
    categories = [{"id": category.id, "name": category.name} for category in PlaceCategory.objects.order_by("name")]
    return JsonResponse({"categories": categories})


@require_POST
def create_person(request):
    """Create (or reuse) a Person from tagging — gated ``add_person_inline``."""
    if not request.user.has_perm("fiches.add_person_inline"):
        return JsonResponse({"success": False, "error": "forbidden"}, status=403)
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"success": False, "error": "empty_name"}, status=400)

    matches = list(Person.objects.filter(name__iexact=name, modern=False).order_by("pk")[:2])
    if len(matches) > 1:
        return JsonResponse(
            {
                "success": False,
                "error": "ambiguous_name",
                "candidates": [
                    {"id": person.pk, "label": person.format_for_ajax_search().rsplit("|", 1)[0]}
                    for person in matches
                ],
            },
            status=409,
        )

    created = not matches
    person = matches[0] if matches else Person.objects.create(name=name, modern=False)
    return JsonResponse({"success": True, "id": person.id, "label": person.name, "created": created})


@require_POST
def create_place(request):
    """Create (or reuse) a PlaceRecord from the tagging window.

    Gated on ``add_placerecord_inline`` rather than ``add_placerecord``: the
    latter is held by every status that may create a place fiche the normal way,
    while creating one inline while tagging is reserved for directors (client
    request 2026-07-15, to avoid a trail of half-filled fiches).
    """
    if not request.user.has_perm("fiches.add_placerecord_inline"):
        return JsonResponse({"success": False, "error": "forbidden"}, status=403)
    name = (request.POST.get("name") or "").strip()
    category_id = (request.POST.get("category") or "").strip()
    if not name:
        return JsonResponse({"success": False, "error": "empty_name"}, status=400)
    if not category_id.isdigit():
        return JsonResponse({"success": False, "error": "category_required"}, status=400)
    category = PlaceCategory.objects.filter(pk=int(category_id)).first()
    if category is None:
        return JsonResponse({"success": False, "error": "category_unknown"}, status=400)

    place, created = PlaceRecord.objects.get_or_create(
        name=name, category=category, defaults={"access_owner": request.user}
    )
    return JsonResponse(
        {"success": True, "id": place.id, "label": f"{place.name} ({place.category})", "created": created}
    )
