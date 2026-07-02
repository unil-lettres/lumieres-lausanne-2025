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

from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, SimpleTestCase
from fiches.admin import ImageInlineForm, NewsAdmin
from fiches.models.content.news import News


class ImageInlineFormTest(SimpleTestCase):
    def test_legend_is_optional(self):
        self.assertIn("legend", ImageInlineForm.base_fields)
        self.assertFalse(ImageInlineForm.base_fields["legend"].required)


class NewsAdminSaveModelTest(SimpleTestCase):
    def test_initial_data_defaults_author_to_request_user(self):
        class UserStub:
            id = 42

        request = RequestFactory().get("/fiches_admin/fiches/news/add/")
        request.user = UserStub()

        admin_obj = NewsAdmin(News, AdminSite())
        initial = admin_obj.get_changeform_initial_data(request)

        self.assertEqual(initial.get("author"), 42)

    def test_save_model_sets_author_from_request_user_when_missing(self):
        class UserStub:
            id = 42

        user = UserStub()
        request = RequestFactory().post("/fiches_admin/fiches/news/add/")
        request.user = user

        obj = News(title="Admin save test", published=False, content="<p>content</p>")
        admin_obj = NewsAdmin(News, AdminSite())
        with patch("django.contrib.admin.options.ModelAdmin.save_model") as super_save:
            admin_obj.save_model(request, obj, form=None, change=False)
            super_save.assert_called_once_with(request, obj, None, False)
        self.assertEqual(obj.author_id, user.id)
