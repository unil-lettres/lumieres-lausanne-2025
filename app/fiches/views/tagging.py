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

Only fiche *creation* lives here; searching reuses ``ajax_search`` (persons) and
``place_autocomplete`` (places). Creation is gated on ``add_person`` /
``add_placerecord`` so that only the « Directeurs » role may create a fiche from
the tagging window — every other role can solely select an existing fiche.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from fiches.models import PlaceCategory, PlaceRecord
from fiches.models.person.person import Person


@require_GET
def place_categories(request):
    """Return the place categories, for the inline-create category dropdown."""
    categories = [{"id": category.id, "name": category.name} for category in PlaceCategory.objects.order_by("name")]
    return JsonResponse({"categories": categories})


@require_POST
def create_person(request):
    """Create (or reuse) a Person from the tagging window — gated ``add_person``."""
    if not request.user.has_perm("fiches.add_person"):
        return JsonResponse({"success": False, "error": "forbidden"}, status=403)
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"success": False, "error": "empty_name"}, status=400)

    person = Person.objects.filter(name__iexact=name).first()
    created = False
    if person is None:
        person, created = Person.objects.get_or_create(name=name, defaults={"modern": False})
    return JsonResponse({"success": True, "id": person.id, "label": person.name, "created": created})


@require_POST
def create_place(request):
    """Create (or reuse) a PlaceRecord from the tagging window — gated ``add_placerecord``."""
    if not request.user.has_perm("fiches.add_placerecord"):
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
