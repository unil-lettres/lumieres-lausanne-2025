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

"""General place results and pagination, independent of Solr availability."""
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase

from fiches.models.search.search import QuickSearchForm


class PlaceResultRenderingTests(SimpleTestCase):
    def render_results(self, count=1, per_page=30, page_number=1):
        request = RequestFactory().get("/chercher/", {"q": "beaulieu", "t": "place"})
        request.user = AnonymousUser()
        results = [SimpleNamespace(
            model_name="placerecord", object=SimpleNamespace(id=i+1, name=f"Beaulieu {i+1}", category="Domaine")
        ) for i in range(count)]
        page = Paginator(results, per_page).page(page_number)
        return render_to_string("fiches/search/search_general.html", {
            "query": "beaulieu", "form": QuickSearchForm(request.GET), "page": page,
            "page_obj": page, "paginator": page.paginator, "qs": "q=beaulieu&t=place",
            "counts": {"place": count}, "selected_types": {"place"},
        }, request=request)

    def test_place_has_visible_link_category_and_filter(self):
        body = self.render_results()
        self.assertIn('href="/fiches/lieu/1/"', body)
        self.assertIn('Beaulieu 1</a>', body)
        self.assertIn('(Domaine)', body)
        self.assertIn('Lieux (1)', body)
        self.assertLess(body.index('value="person"'), body.index('value="place"'))
        self.assertRegex(body, r'value="place"\s+checked')
        self.assertNotRegex(body, r'value="person"\s+checked')

    def test_single_page_count_appears_once(self):
        body = self.render_results()
        self.assertEqual(body.count('1 fiche trouvée'), 1)
        self.assertNotIn('class="results-footer"', body)

    def test_multiple_pages_keep_bottom_navigation_and_query(self):
        body = self.render_results(count=3, per_page=2, page_number=2)
        self.assertIn('Beaulieu 3</a>', body)
        self.assertNotIn('Beaulieu 1</a>', body)
        self.assertIn('class="results-footer"', body)
        self.assertIn('q=beaulieu&amp;t=place', body)

    def test_empty_result_is_explicit(self):
        body = self.render_results(count=0)
        self.assertIn('Pas de résultats trouvés', body)
        self.assertNotIn('class="results-footer"', body)
