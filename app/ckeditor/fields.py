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

from django import forms
from django.db import models

from ckeditor.widgets import CKEditorWidget


class RichTextField(models.TextField):
    def __init__(self, config_name="default", *args, **kwargs):
        self.config_name = config_name
        super(RichTextField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            "form_class": RichTextFormField,
            "config_name": self.config_name,
        }
        defaults.update(kwargs)
        return super(RichTextField, self).formfield(**defaults)


try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], [r"^ckeditor\.fields\.RichTextField"])
except:
    pass


class RichTextFormField(forms.fields.Field):
    def __init__(self, config_name="default", *args, **kwargs):
        # Remove `max_length` if it's in kwargs
        kwargs.pop("max_length", None)
        kwargs.update({"widget": CKEditorWidget(config_name=config_name)})
        super(RichTextFormField, self).__init__(*args, **kwargs)
