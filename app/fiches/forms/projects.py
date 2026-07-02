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

"""Form for editing projects."""

from django import forms
from django.utils.translation import gettext_lazy as _

from fiches.models.misc.project import Project


# ===============================
# ProjectForm Definition
# ===============================
class ProjectForm(forms.ModelForm):
    """Form for editing a project."""

    url = forms.SlugField(
        label=_("Url"),
        help_text=_(
            "ATTENTION, doit être unique. Uniquement caractères non-accentués, "
            "tiret et chiffres. Pas d'espaces ni de ponctuation."
        ),
        required=True,
        widget=forms.TextInput(
            attrs={
                "size": 40,
                "style": "width: 60%;",
                "data-slug-source": "name",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = Project
        fields = "__all__"

    class Media:
        js = (
            "js/lib/urlify.js",
            "js/admin/project_url_tools.js",
        )
