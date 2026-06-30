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

from django.urls import path

from fiches.views.search import (
    biblio_extended_search,
    do_search,
    filter_builder,
    list_persons,
    list_places,
    quick_search,  # ← add this
    relations,
    req_search_view,  # keep temporarily for compatibility
    save_settings,
    transcriptions_change_access,
)

urlpatterns = [
    path("", quick_search, name="search-index"),  # 🔍 header search
    path("person/", filter_builder, {"model_name": "Person"}, name="search-person"),
    path("person/list", list_persons, name="list-person"),
    path("place/list", list_places, name="list-place"),
    path("bibliographie/", biblio_extended_search, name="search-biblio"),  # 🔍➕ advanced
    path("do/", do_search, name="do-search"),
    path("display_settings/save/", save_settings, name="save-settings"),
    path("person/relations/", relations, name="search-relations"),
    path("actions/changer-acces-transcriptions/", transcriptions_change_access, name="trans-change-access"),
    # Optional: keep a fallback endpoint if anything still links to the old placeholder
    path("disabled/", req_search_view, name="search-disabled"),
]
