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

"""Note forms for the biblio and transcription fiches."""

from django import forms

from fiches.forms.base import NoteFormBase
from fiches.models.documents import (
    NoteBiblio,
    NoteTranscription,
)


# ===============================
# NoteFormBiblio Definition
# ===============================
class NoteFormBiblio(NoteFormBase):
    """
    Form for editing the NoteBiblio model (notes referencing a Biblio).
    It should NOT contain fields that belong to Biblio, like subj_person, etc.
    """

    # Add virtual rte_type field for template compatibility
    rte_type = forms.CharField(initial="CKE", widget=forms.HiddenInput(), required=False)

    class Meta(NoteFormBase.Meta):
        model = NoteBiblio
        fields = "__all__"  # Or just ['text', 'owner'] if that's all you need


# ===============================
# NoteFormTranscription Definition
# ===============================
class NoteFormTranscription(NoteFormBase):
    """
    Form for editing the NoteTranscription model (notes referencing a Transcription).
    """

    class Meta(NoteFormBase.Meta):
        model = NoteTranscription
        fields = "__all__"  # Or just ['text', 'owner'] if that's all you need
