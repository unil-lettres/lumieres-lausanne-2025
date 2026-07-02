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

# fiches/models/contributiontype.py

from django.db import models
from django.utils.translation import gettext_lazy as _


class ContributionType(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    code = models.IntegerField(_("Code"), unique=True)
    type = models.CharField(_("Type"), max_length=10)  # e.g., 'doc', 'any'

    def __str__(self):
        return self.name

    # Define constants for easier reference
    PUBLISHER_ID = 4
    TRANSLATOR_ID = 3
    DIRECTOR_ID = 7
    AUTHOR_CODE = 0
