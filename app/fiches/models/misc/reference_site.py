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

"""Catalog of external reference sites (référentiels).

A ``ReferenceSite`` is an external authority base — GeoNames, Wikidata, DHS,
VIAF, IdRef, GND, ... — that fiches can link to. This is a shared lookup
table: the per-fiche association (its external identifier and permalink) is
carried by a dedicated pivot on each owning model (e.g. the place-to-référentiel
pivot for place fiches).

``base_url`` holds the provider's URL template so the full permalink can be
generated from a stored identifier (see :meth:`ReferenceSite.build_url`).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReferenceSite(models.Model):
    """Admin-managed catalog of external reference providers (référentiels)."""

    name = models.CharField(_("Nom du référentiel"), max_length=64, unique=True)
    code = models.SlugField(
        _("Code"),
        max_length=32,
        unique=True,
        help_text=_("Identifiant court, ex: geonames, wikidata, dhs, viaf, idref"),
    )
    base_url = models.URLField(
        _("Gabarit d'URL"),
        blank=True,
        help_text=_(
            "Gabarit avec le marqueur {id} pour générer le permalien à partir de "
            "l'identifiant (ex: https://www.geonames.org/{id}). Sans {id}, traité "
            "comme préfixe."
        ),
    )
    is_active = models.BooleanField(_("Actif"), default=True)

    class Meta:
        app_label = "fiches"
        verbose_name = _("Site de référence")
        verbose_name_plural = _("Sites de référence")
        ordering = ("name",)

    def __str__(self):
        return self.name

    def build_url(self, identifier):
        """Build the full permalink for an external identifier in this référentiel.

        ``base_url`` is a template containing ``{id}`` (e.g.
        ``https://www.geonames.org/{id}``); without the placeholder it is treated
        as a prefix. Returns ``""`` when there is no identifier or no base URL.
        """
        if not identifier or not self.base_url:
            return ""
        if "{id}" in self.base_url:
            return self.base_url.replace("{id}", identifier)
        return self.base_url.rstrip("/") + "/" + identifier.lstrip("/")
