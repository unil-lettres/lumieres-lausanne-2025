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

from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse


class PersonListSearchTemplateTest(TestCase):
    def test_person_list_keeps_inherited_menu_javascript(self):
        response = self.client.get(reverse("list-person"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dropdown menu functionality")
        self.assertContains(response, "jquery-1.8.2.min.js")

    def test_biographical_autoload_tolerates_pages_without_search_model_name(self):
        search_script = Path(finders.find("js/search.js")).read_text(encoding="utf-8")

        self.assertIn("typeof search_model_name !== 'undefined'", search_script)
