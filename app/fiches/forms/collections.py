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

"""Form for editing object collections."""

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from fiches.models.misc import ObjectCollection


class ObjectCollectionForm(forms.ModelForm):
    """
    Form for the ObjectCollection model.
    """

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("user", None)
        self.can_edit_details = kwargs.pop("can_edit_details", True)
        super().__init__(*args, **kwargs)

        can_change_owner = bool(self.request_user and self.request_user.has_perm("fiches.change_collection_owner"))

        if can_change_owner:
            owner_queryset = User.objects.order_by("last_name", "first_name", "username")
            self.fields["owner"] = forms.ModelChoiceField(
                queryset=owner_queryset,
                label=_("Propriétaire"),
                help_text=_("L'utilisateur qui possédera cette collection."),
                required=True,
            )
            if self.instance and self.instance.pk:
                self.initial.setdefault("owner", self.instance.owner_id)
            elif self.request_user:
                self.initial.setdefault("owner", self.request_user.pk)
            self.order_fields(["owner"] + [f for f in self.fields if f != "owner"])
        else:
            self.fields.pop("owner", None)

        if not self.can_edit_details:
            for field_name, field in self.fields.items():
                if field_name == "owner":
                    continue
                field.disabled = True

    class Meta:
        model = ObjectCollection
        # Exclude the owner field so it won't be rendered or expected in POST data.
        exclude = ["owner", "persons", "bibliographies", "transcriptions"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("Enter collection name")}),
            # Add other widgets as needed
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        collection = super().save(commit=False)

        can_change_owner = (
            hasattr(self, "request_user")
            and self.request_user
            and self.request_user.has_perm("fiches.change_collection_owner")
            and "owner" in self.cleaned_data
        )
        if can_change_owner:
            new_owner = self.cleaned_data["owner"]
            if new_owner:
                collection.owner = new_owner
                if hasattr(collection, "access_owner"):
                    collection.access_owner = new_owner

        if commit:
            collection.save()
            self.save_m2m()
        return collection
