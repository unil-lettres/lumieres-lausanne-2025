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

# models/user_group.py

from django.contrib.auth.models import Group, User
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserGroup(models.Model):
    name = models.CharField(_("Nom"), max_length=125)
    description = models.TextField(_("Description"), blank=True)
    users = models.ManyToManyField(User, verbose_name=_("Utilisateurs"), blank=True)
    groups = models.ManyToManyField(Group, verbose_name=_("Groupes"), blank=True)
    sort = models.IntegerField(_("ordre de tri"), blank=True)

    class Meta:
        verbose_name = _("Groupe d'utilisateurs")
        verbose_name_plural = _("Groupes d'utilisateurs")
        ordering = ["sort"]
        app_label = "fiches"

    def __str__(self):
        return str(self.name)
