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

from django.apps import apps


# Lazy loading of ContributionDoc and ContributionMan to prevent circular imports
def get_contribution_doc_model():
    return apps.get_model("fiches", "ContributionDoc")


def get_contribution_man_model():
    return apps.get_model("fiches", "ContributionMan")


# Direct imports for models that are not causing circular import issues
from .keyword import PrimaryKeyword, SecondaryKeyword

__all__ = ["get_contribution_doc_model", "get_contribution_man_model", "PrimaryKeyword", "SecondaryKeyword"]
