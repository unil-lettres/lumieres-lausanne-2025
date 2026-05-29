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

import json

from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms.utils import flatatt
from django.urls import reverse
from django.utils.encoding import force_str  # ✅ FIXED
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

json_encode = json.JSONEncoder().encode

DEFAULT_CONFIG = {
    "skin": "kama",
    "toolbar": "Full",
    "height": 291,
    "width": 618,
    "filebrowserWindowWidth": 940,
    "filebrowserWindowHeight": 747,
}


class CKEditorWidget(forms.Textarea):
    """
    Widget providing CKEditor for Rich Text Editing.
    Supports direct image uploads and embed.
    """

    class Media:
        try:
            js = (
                settings.STATIC_URL + "ckeditor/ckeditor/ckeditor.js",
                settings.STATIC_URL + "ckeditor/ckeditor/config.js",
            )
        except AttributeError:
            raise ImproperlyConfigured(
                "django-ckeditor requires STATIC_URL setting. "
                "This setting specifies a URL prefix to the CKEditor JS and CSS media."
            ) from None

    def __init__(self, config_name="default", *args, **kwargs):
        super().__init__(*args, **kwargs)  # ✅ Python 3 style super()
        self.config = DEFAULT_CONFIG.copy()

        # Get config from settings.py
        configs = getattr(settings, "CKEDITOR_CONFIGS", {})
        if not isinstance(configs, dict):
            raise ImproperlyConfigured("CKEDITOR_CONFIGS must be a dictionary.")

        if config_name in configs:
            if not isinstance(configs[config_name], dict):
                raise ImproperlyConfigured(f'CKEDITOR_CONFIGS["{config_name}"] must be a dictionary.')
            self.config.update(configs[config_name])  # Merge with defaults
        else:
            raise ImproperlyConfigured(f"CKEDITOR_CONFIGS missing configuration named '{config_name}'.")

    def render(self, name, value, attrs=None, renderer=None):  # ✅ FIXED
        """
        Render the CKEditor widget.
        """
        value = value or ""
        attrs = attrs or {}
        attrs["name"] = name  # Ensure 'name' is in the attrs dictionary

        self.config["filebrowserUploadUrl"] = reverse("ckeditor_upload")
        self.config["filebrowserBrowseUrl"] = reverse("ckeditor_browse")

        return mark_safe(f'''
        <textarea {flatatt(attrs)}>{conditional_escape(force_str(value))}</textarea>
        <script type="text/javascript">
            CKEDITOR.replace("{attrs.get("id", name)}", {json_encode(self.config)});
        </script>
        ''')
