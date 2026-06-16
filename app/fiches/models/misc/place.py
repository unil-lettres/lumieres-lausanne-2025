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

"""Named-entity models for places (Lieux).

Data layer for the place fiches, built incrementally. This module currently
provides the admin-managed category lookup (:class:`PlaceCategory`); the
place record itself and its satellite tables (variants, reference-site
pivot, notes) are added in later steps.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class PlaceCategory(models.Model):
    """Admin-managed list of place categories (catégories de lieux).

    Seeded by migration ``0006`` with seven default categories — Pays,
    Canton/Département, Région, Ville/Village, Domaine, Maison de campagne,
    Quartier — which admins can edit afterwards.
    """

    name = models.CharField(_("Nom"), max_length=128, unique=True)

    class Meta:
        app_label = "fiches"
        verbose_name = _("Catégorie de lieu")
        verbose_name_plural = _("Catégories de lieux")
        ordering = ("name",)

    def __str__(self):
        return self.name
