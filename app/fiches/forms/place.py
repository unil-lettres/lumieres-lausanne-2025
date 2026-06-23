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

"""Forms for the place fiche (Lieu): the main form and its note form."""

from django import forms

from fiches.forms.base import NoteFormBase
from fiches.models.misc import NotePlace, PlaceRecord


# ===============================
# Place fiche forms (Lieux)
# ===============================
class NoteFormPlace(NoteFormBase):
    """Form for a NotePlace (rich-text note attached to a place fiche)."""

    # Virtual field for note_formset.html template compatibility (cf. NoteFormBiblio).
    rte_type = forms.CharField(initial="CKE", widget=forms.HiddenInput(), required=False)

    class Meta(NoteFormBase.Meta):
        model = NotePlace
        fields = "__all__"


class PlaceRecordForm(forms.ModelForm):
    """Main form for creating/editing a place fiche (Lieu).

    Like the biblio and biography fiche forms, this exposes only the fiche's
    own content fields. A place fiche is publicly readable; access control is
    carried by its notes, not by the fiche, so no access field is shown here
    and ``access_owner`` is set programmatically to the current editor.
    """

    class Meta:
        model = PlaceRecord
        fields = ["name", "category", "related_places"]

    def __init__(self, *args, **kwargs):
        """Make related places optional and exclude the fiche from its own choices."""
        super().__init__(*args, **kwargs)
        self.fields["related_places"].required = False
        # A place cannot be associated with itself.
        if self.instance and self.instance.pk:
            self.fields["related_places"].queryset = PlaceRecord.objects.exclude(pk=self.instance.pk)
