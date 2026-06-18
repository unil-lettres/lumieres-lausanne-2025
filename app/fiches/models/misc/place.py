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

Data layer for the place fiches, built incrementally. This module provides the
admin-managed category lookup (:class:`PlaceCategory`) and the place record
itself (:class:`PlaceRecord`); the satellite tables (variants, reference-site
pivot, notes) are added in later steps.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from fiches.models.contributions.ac_model import ACModel

# The legacy auth_user / fiches_usergroup tables use INT primary keys, while
# these new tables use BIGINT — MySQL cannot create a cross-type FK constraint.
# FKs that target those legacy tables therefore set db_constraint=False;
# referential integrity then stays at the ORM level, as it already does across
# the legacy schema. FKs between the new place tables keep their DB constraint.


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


class PlaceRecord(ACModel):
    """A named-entity record for a place (fiche lieu)."""

    # Override the ACModel access relations to the legacy INT-PK tables
    # (see module note): keep the relation at the ORM level, without a DB FK.
    access_owner = models.ForeignKey(
        User,
        verbose_name=_("Propriétaire"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
    )
    access_groups = models.ManyToManyField(
        "fiches.UserGroup",
        verbose_name=_("Groupes d'accès"),
        blank=True,
        db_constraint=False,
    )

    name = models.CharField(_("Nom"), max_length=255)
    category = models.ForeignKey(
        PlaceCategory,
        verbose_name=_("Catégorie"),
        on_delete=models.PROTECT,
        related_name="places",
    )
    related_places = models.ManyToManyField(
        "self",
        verbose_name=_("Lieux associés"),
        blank=True,
        symmetrical=True,
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = "fiches"
        verbose_name = _("Fiche lieu")
        verbose_name_plural = _("Fiches lieux")
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["name", "category"],
                name="unique_place_name_per_category",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"


class PlaceVariant(models.Model):
    """Alternate spelling or translation of a place name (one entry per row)."""

    place = models.ForeignKey(
        PlaceRecord,
        verbose_name=_("Lieu"),
        on_delete=models.CASCADE,
        related_name="variants",
    )
    name = models.CharField(_("Variante"), max_length=255)

    class Meta:
        app_label = "fiches"
        verbose_name = _("Variante de lieu")
        verbose_name_plural = _("Variantes de lieu")
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["place", "name"],
                name="unique_variant_per_place",
            ),
        ]

    def __str__(self):
        return self.name


class PlaceReferenceSite(models.Model):
    """A place's permalink on an external reference site (référentiel)."""

    place = models.ForeignKey(
        PlaceRecord,
        verbose_name=_("Lieu"),
        on_delete=models.CASCADE,
        related_name="reference_links",
    )
    reference_site = models.ForeignKey(
        "fiches.ReferenceSite",
        verbose_name=_("Site de référence"),
        on_delete=models.PROTECT,
        related_name="place_links",
    )
    identifier = models.CharField(_("Identifiant"), max_length=255)

    class Meta:
        app_label = "fiches"
        verbose_name = _("Site de référence du lieu")
        verbose_name_plural = _("Sites de référence du lieu")
        ordering = ("reference_site__name",)
        constraints = [
            models.UniqueConstraint(
                fields=["place", "reference_site"],
                name="unique_reference_site_per_place",
            ),
        ]

    def __str__(self):
        return f"{self.reference_site}: {self.identifier}"

    @property
    def url(self):
        """Return the permalink built from the reference site and identifier."""
        return self.reference_site.build_url(self.identifier)
