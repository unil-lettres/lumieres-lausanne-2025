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

# fiches/models/relation.py

from django.db import models
from django.utils.translation import gettext_lazy as _


# ===============================================================================
# RELATIONS
# ===============================================================================
class RelationType(models.Model):
    name = models.CharField(max_length=256)
    reverse_name = models.CharField(max_length=256)
    sorting = models.IntegerField(editable=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Type de relation"
        verbose_name_plural = "Types de relation"
        app_label = "fiches"
        ordering = ["sorting"]


class Relation(models.Model):
    """
    Pour obtenir les relations d'une personne p:
    rs = Relation.objects.filter(bio__person=p).extra(where=["1 GROUP BY related_person_id,relation_type_id"])
    """

    bio = models.ForeignKey("fiches.Biography", on_delete=models.CASCADE)
    related_person = models.ForeignKey(
        "fiches.Person",
        verbose_name=_("Personne"),
        limit_choices_to={"modern": False},
        related_name="person_back",
        on_delete=models.CASCADE,
    )
    relation_type = models.ForeignKey(
        "fiches.RelationType",  # <--- String reference (no import needed)
        verbose_name=_("Type de relation"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        display_str = f"{self.related_person} ({self.relation_type})"
        # If `bio.valid` is a boolean that indicates validity:
        if not self.bio.valid:
            display_str += "*"
        return display_str

    def reverse_str(self):
        # Replaces old `self.person_to` with `self.related_person`
        # If `relation_type.reverse_name` exists on `RelationType`, we display it
        return f"{self.related_person} ({self.relation_type.reverse_name})"

    class Meta:
        app_label = "fiches"
        ordering = ("relation_type__sorting",)
