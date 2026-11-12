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

"""Search query contracts without a running Solr or database."""

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from haystack.backends.solr_backend import SolrSearchQuery
from haystack.query import SearchQuerySet
from haystack.utils.loading import ConnectionHandler

from fiches.views.search import _apply_term_filters


class QuickSearchPhraseTests(SimpleTestCase):
    def query(self, text):
        configuration = {
            "default": {"ENGINE": "haystack.backends.solr_backend.SolrEngine", "URL": "http://127.0.0.1:9/solr/test"}
        }
        with override_settings(HAYSTACK_CONNECTIONS=configuration), patch(
            "haystack.connections", ConnectionHandler(configuration)
        ), patch(
            "pysolr.Solr._send_request", side_effect=AssertionError("Query construction must not use the network")
        ):
            return str(_apply_term_filters(SearchQuerySet(query=SolrSearchQuery()), text).query)

    def test_quoted_hyphenated_place_is_one_phrase(self):
        self.assertEqual(self.query('"Valeyres-sous-Rances"'), '("Valeyres\\-sous\\-Rances")')

    def test_phrase_and_other_term_are_both_required(self):
        self.assertEqual(self.query('"Valeyres sous Rances" Lettre'),
                         '(("Valeyres sous Rances") AND (Lettre))')

    def test_two_phrases_are_both_required(self):
        self.assertEqual(self.query('"Valeyres sous Rances" "Gabriel Mingard"'),
                         '(("Valeyres sous Rances") AND ("Gabriel Mingard"))')

    def test_unquoted_words_remain_conjunctive(self):
        self.assertEqual(self.query('Valeyres Rances'), '((Valeyres) AND (Rances))')

    def test_apostrophe_does_not_merge_other_terms(self):
        self.assertEqual(self.query("lettre d'un auteur"), "((lettre) AND (d'un) AND (auteur))")

    def test_unclosed_quote_is_escaped_without_error(self):
        self.assertEqual(self.query('"Valeyres'), '(\\"Valeyres)')

    def test_excluded_term_is_preserved(self):
        self.assertEqual(self.query('Lettre -Lausanne'), '((Lettre) AND (NOT Lausanne))')

    def test_whitespace_only_keeps_empty_query(self):
        self.assertEqual(self.query('  \t '), '*:*')
