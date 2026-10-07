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

import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

if "ckeditor" in settings.INSTALLED_APPS:
    # Confirm CKEDITOR_UPLOAD_PATH setting has been specified.
    if not hasattr(settings, "CKEDITOR_UPLOAD_PATH"):
        raise ImproperlyConfigured(
            "django-ckeditor requires CKEDITOR_UPLOAD_PATH, relative to MEDIA_ROOT for ckeditor_uploader."
        )

    # Legacy absolute paths must already exist. Storage creates relative upload
    # directories on first use; do not require or create them at import time.
    upload_path = getattr(settings, "CKEDITOR_UPLOAD_PATH", None)
    if upload_path and os.path.isabs(upload_path) and not os.path.exists(upload_path):
        raise ImproperlyConfigured(
            "django-ckeditor CKEDITOR_UPLOAD_PATH setting error, no such file or directory: '%s'"
            % settings.CKEDITOR_UPLOAD_PATH
        )
