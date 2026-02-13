from django.urls import path
from fiches.views.search import (
    quick_search,                 # ← add this
    filter_builder,
    list_persons,
    do_search,
    save_settings,
    relations,
    transcriptions_change_access,
    biblio_extended_search,
    req_search_view,              # keep temporarily for compatibility
)

urlpatterns = [
    path('', quick_search, name="search-index"),               # 🔍 header search
    path('person/', filter_builder, {'model_name': 'Person'}, name="search-person"),
    path('person/list', list_persons, name="list-person"),
    path('bibliographie/', biblio_extended_search, name="search-biblio"),  # 🔍➕ advanced
    path('do/', do_search, name="do-search"),
    path('display_settings/save/', save_settings, name="save-settings"),
    path('person/relations/', relations, name="search-relations"),
    path('actions/changer-acces-transcriptions/', transcriptions_change_access, name="trans-change-access"),

    # Optional: keep a fallback endpoint if anything still links to the old placeholder
    path('disabled/', req_search_view, name="search-disabled"),
]
