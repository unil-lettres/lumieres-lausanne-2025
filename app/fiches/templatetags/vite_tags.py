# Copyright (C) 2010-2025 Université de Lausanne, RISET
# <https://www.unil.ch/riset/>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lumières.Lausanne is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# This copyright notice MUST APPEAR in all copies of the file.

"""
Vite asset management template tags for Django.
"""

import json
from pathlib import Path
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()


def get_manifest():
    """
    Read and parse the Vite manifest.json file.
    Returns a dict mapping source files to built files.
    """
    manifest_path = Path(settings.BASE_DIR).parent / "static" / "dist" / ".vite" / "manifest.json"

    if not manifest_path.exists():
        return {}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


@register.simple_tag
def vite_asset(path, asset_type=None):
    """
    Get the built asset URL for a given source path.

    Usage:
        {% load vite_tags %}
        <link rel="stylesheet" href="{% vite_asset 'css/main.css' 'css' %}">
        <script type="module" src="{% vite_asset 'js/main.js' 'js' %}"></script>

    Args:
        path: Source file path (e.g., 'js/main.js')
        asset_type: Type of asset ('css' or 'js') - optional, inferred from path

    Returns:
        Static URL to the built asset
    """
    if settings.DEBUG:
        # In development mode with Vite dev server
        vite_dev_server = getattr(settings, "VITE_DEV_SERVER", "http://localhost:3000")
        return f"{vite_dev_server}/{path}"

    # Production mode: read from manifest
    manifest = get_manifest()

    # Get entry from manifest
    entry = manifest.get(path)
    if not entry:
        # Fallback to source path if not in manifest
        return static(f"dist/{path}")

    # Get the built file path
    built_file = entry.get("file", path)

    return static(f"dist/{built_file}")


@register.simple_tag
def vite_css(path):
    """
    Get CSS asset URL and return as link tag.

    Usage:
        {% load vite_tags %}
        {% vite_css 'css/main.css' %}

    Returns:
        Safe HTML link tag
    """
    url = vite_asset(path, "css")
    return mark_safe(f'<link rel="stylesheet" href="{url}">')


@register.simple_tag
def vite_js(path):
    """
    Get JS asset URL and return as script tag.

    Usage:
        {% load vite_tags %}
        {% vite_js 'js/main.js' %}

    Returns:
        Safe HTML script tag
    """
    url = vite_asset(path, "js")
    return mark_safe(f'<script type="module" src="{url}"></script>')


@register.simple_tag
def vite_hmr():
    """
    Include Vite HMR client in development mode.

    Usage:
        {% load vite_tags %}
        {% vite_hmr %}

    Returns:
        Safe HTML script tag for HMR client in dev, empty string in production
    """
    if settings.DEBUG:
        vite_dev_server = getattr(settings, "VITE_DEV_SERVER", "http://localhost:3000")
        return mark_safe(f'<script type="module" src="{vite_dev_server}/@vite/client"></script>')
    return ""
