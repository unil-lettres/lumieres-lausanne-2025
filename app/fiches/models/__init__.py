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

# fiches/models/__init__.py

# Content Models
from .content import FreeContent, Image, News, Publication

# Finding Models
from .content.finding import Finding

# Contributions Models
from .contributions.ac_model import ACModel
from .contributions.keyword import PrimaryKeyword, SecondaryKeyword
from .core.user_group import UserGroup

# Core Models
from .core.user_profile import UserProfile

# Document Models
from .documents.document import (
    Biblio,
    ContributionDoc,
    ContributionMan,
    ContributionType,
    Depot,
    Document,
    DocumentLanguage,
    DocumentType,
    Manuscript,
    ManuscriptType,
    Transcription,
)
from .documents.document_file import DocumentFile

# Logging Models
from .logging.activity_log import ActivityLog

# Notes Models
from .misc.notes import NoteBase

# Miscellaneous Models
from .misc.object_collection import ObjectCollection
from .misc.place import PlaceCategory, PlaceRecord, PlaceVariant
from .misc.project import Project
from .misc.reference_site import ReferenceSite
from .misc.society import Society
from .person.biography import Biography, Nationality, Relation, RelationType, Religion

# Person Models
from .person.person import Person

# Search Models
from .search.search import JournaltitleView, PlaceView

# Add any additional imports as needed

__all__ = [
    "FreeContent",
    "Image",
    "News",
    "Publication",
    "ACModel",
    "PrimaryKeyword",
    "SecondaryKeyword",
    "UserProfile",
    "UserGroup",
    "Document",
    "DocumentType",
    "DocumentLanguage",
    "Biblio",
    "Manuscript",
    "Transcription",
    "ContributionDoc",
    "ContributionMan",
    "ManuscriptType",
    "ContributionType",
    "DocumentFile",
    "Finding",
    "ActivityLog",
    "ObjectCollection",
    "Project",
    "Society",
    "NoteBase",
    "Person",
    "Biography",
    "RelationType",
    "Relation",
    "Nationality",
    "Religion",
    "PlaceView",
    "JournaltitleView",
    "Depot",
    "PlaceCategory",
    "PlaceRecord",
    "PlaceVariant",
    "ReferenceSite",
    # Add any additional models here
]
