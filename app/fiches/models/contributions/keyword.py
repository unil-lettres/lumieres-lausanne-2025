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

# fiches/models/keyword.py

from django.db import models
from django.utils.translation import gettext_lazy as _


class PrimaryKeyword(models.Model):
    """Primary keyword model for categorizing content."""

    word = models.CharField(_("Mot"), max_length=100, unique=True)

    def __str__(self):
        """Return string representation of the primary keyword."""
        return self.word

    class Meta:
        """Meta configuration for PrimaryKeyword model."""

        verbose_name = _("Mot clé principal")
        verbose_name_plural = _("Mots clés principaux")
        ordering = ("word",)


class SecondaryKeyword(models.Model):
    """Secondary keyword model that belongs to a primary keyword."""

    word = models.CharField(_("Mot"), max_length=100, unique=True)
    primary_keyword = models.ForeignKey(
        PrimaryKeyword,
        on_delete=models.CASCADE,
        db_column="parent_id",
        related_name="secondary_keywords",
        verbose_name=_("Mot clé principal"),
    )

    def __str__(self):
        """Return string representation of the secondary keyword."""
        return f"{self.word} ({self.primary_keyword})"

    class Meta:
        """Meta configuration for SecondaryKeyword model."""

        verbose_name = _("Mot clé secondaire")
        verbose_name_plural = _("Mots clés secondaires")
        managed = False
        db_table = "fiches_secondarykeyword"
        ordering = ("primary_keyword__word", "word")
