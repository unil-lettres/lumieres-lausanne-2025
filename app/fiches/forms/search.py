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

"""Haystack search form for the fiches."""

from django.db.models import Q
from haystack import connections
from haystack.forms import ModelSearchForm
from haystack.query import RelatedSearchQuerySet

from fiches.models.documents import (
    Biblio,
    Transcription,
)
from fiches.models.person import Person


class FichesSearchForm(ModelSearchForm):
    """Haystack search form scoping results by indexed model and user access."""

    def __init__(self, *args, **kwargs):
        """Initialize the Haystack model search form."""
        super().__init__(*args, **kwargs)

    def get_models(self):
        """Return an alphabetical list of model classes in the index."""
        search_models = super().get_models()
        if not search_models:
            # If no models are found, retrieve them from the Haystack unified index
            search_models = connections["default"].get_unified_index().get_indexed_models()
        return search_models

    def search(self):
        """Run the search, restricting results to what the user may access."""
        if not self.is_valid():
            return self.no_query_found()

        query = self.cleaned_data.get("q")
        if not query:
            return self.no_query_found()

        # Restrict results based on user permissions and access
        if self.request and self.request.user.is_authenticated:
            if not self.request.user.has_perm("fiches.access_unpublished_transcription"):
                self.searchqueryset = RelatedSearchQuerySet().load_all_queryset(
                    Transcription,
                    Transcription.objects.filter(
                        Q(access_public=True)
                        | Q(author=self.request.user)
                        | Q(author2=self.request.user)
                        | Q(access_groups__users=self.request.user)
                        | Q(access_groups__groups__user=self.request.user)
                        | Q(project__members=self.request.user)
                        | Q(
                            access_public=False,
                            access_private=False,
                            access_groups__isnull=True,
                        )
                    ),
                )
        else:
            self.searchqueryset = RelatedSearchQuerySet()

        # Apply the search query
        sqs = self.searchqueryset.auto_query(query)

        if self.load_all:
            sqs = sqs.load_all()

        # Filter and order results based on models
        models = self.get_models()
        ordered_models = [m for m in (Person, Biblio, Transcription) if m in models]

        result_list = []
        for model in ordered_models:
            model_results = sqs.models(model)
            result_list.extend(list(model_results))

        return result_list
