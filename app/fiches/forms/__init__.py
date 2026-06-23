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

"""Forms for the fiches app; this package re-exports every form class."""

from fiches.forms.base import NoteFormBase
from fiches.forms.biblio import (
    BiblioForm,
    ContributionDocForm,
    ContributionDocSecForm,
    ContributionManForm,
    DocumentFileForm,
    ManuscriptForm,
)
from fiches.forms.collections import ObjectCollectionForm
from fiches.forms.notes import NoteFormBiblio, NoteFormTranscription
from fiches.forms.place import NoteFormPlace, PlaceRecordForm
from fiches.forms.projects import ProjectForm
from fiches.forms.search import FichesSearchForm
from fiches.forms.transcription import TranscriptionForm

__all__ = [
    "BiblioForm",
    "ContributionDocForm",
    "ContributionDocSecForm",
    "ContributionManForm",
    "DocumentFileForm",
    "FichesSearchForm",
    "ManuscriptForm",
    "NoteFormBase",
    "NoteFormBiblio",
    "NoteFormPlace",
    "NoteFormTranscription",
    "ObjectCollectionForm",
    "PlaceRecordForm",
    "ProjectForm",
    "TranscriptionForm",
]
