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

# models/notes.py

from ckeditor.fields import RichTextField
from django.contrib.auth.models import Group
from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from fiches.models.contributions.ac_model import ACModel


class NoteBase(ACModel):
    """
    Abstract base model for notes.
    """

    text = RichTextField(verbose_name=_("Note"), config_name="note_ckeditor", blank=True)
    groups = models.ManyToManyField(Group, blank=True, verbose_name=_("Visible pour"))

    class Meta:
        abstract = True
        permissions = (
            ("can_see_note", "Can see Note"),
            ("can_publish_note", "Can publish note"),
        )

    def __str__(self):
        return strip_tags(self.text[:30])
