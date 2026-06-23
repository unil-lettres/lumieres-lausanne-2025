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

"""Form for editing a transcription."""

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from fiches.fields import MultipleUserField
from fiches.models.documents import (
    TRANSCRIPTION_CHOICES,
    Biblio,
    Manuscript,
    Transcription,
)
from fiches.models.documents.document import TranscriptionReviewer
from fiches.utils import get_default_publisher_user
from fiches.widgets import DynamicList


class TranscriptionForm(forms.ModelForm):
    """Form for editing a transcription."""

    manuscript = forms.CharField(widget=forms.HiddenInput(), required=False)
    manuscript_b = forms.CharField(widget=forms.HiddenInput(), required=False)
    author = forms.ModelChoiceField(queryset=User.objects.all().order_by("username"))
    author2 = forms.ModelChoiceField(queryset=User.objects.all().order_by("username"), required=False)
    reviewers = MultipleUserField(
        queryset=User.objects.all().order_by("username"),
        widget=DynamicList(
            rel=TranscriptionReviewer.user,
            add_title="Ajouter un relecteur",
            placeholder="nom d'utilisateur",
        ),
        required=False,
    )
    status = forms.IntegerField(
        widget=forms.RadioSelect(choices=TRANSCRIPTION_CHOICES["status"]),
        label=_("État"),
        initial=0,
    )
    scope = forms.IntegerField(
        widget=forms.RadioSelect(choices=TRANSCRIPTION_CHOICES["scope"]),
        label=_("Transcription"),
        initial=0,
    )
    published_date = forms.DateTimeField(
        label=_("Date de mise en ligne"),
        required=False,
        input_formats=["%d/%m/%Y, %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={
                "type": "text",
                "placeholder": "jj/mm/aaaa",
                "class": "datetimepicker-fr",
            },
            format="%d/%m/%Y, %H:%M",
        ),
    )
    published_by = forms.ModelChoiceField(
        queryset=User.objects.all().order_by("username"),
        label=_("Mis en ligne par"),
        required=False,
    )

    class Meta:
        model = Transcription
        exclude = ("modified_by",)

    def __init__(self, *args, **kwargs):
        """Prefill reviewers and the default publisher for legacy transcriptions."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and not self.is_bound:
            reviewer_ids = list(
                TranscriptionReviewer.objects.filter(transcription_id=self.instance.pk).values_list(
                    "user_id", flat=True
                )
            )
            self.initial.setdefault("reviewers", reviewer_ids)

            # Legacy rows can be public and dated but still miss "published_by".
            # Prefill with the default publisher in the form UI without mutating DB.
            if self.instance.access_public and self.instance.published_date and not self.instance.published_by_id:
                default_publisher = get_default_publisher_user()
                if default_publisher and not self.initial.get("published_by"):
                    self.initial["published_by"] = default_publisher.pk

        if (
            not self.is_bound
            and not self.initial.get("published_by")
            and not getattr(self.instance, "published_by_id", None)
        ):
            default_publisher = get_default_publisher_user()
            if default_publisher:
                self.initial["published_by"] = default_publisher.pk

    def save_reviewers(self, transcription):
        """Persist the explicit reviewers selection in the through table."""
        selected_reviewers = self.cleaned_data.get("reviewers")
        if selected_reviewers is None:
            return

        selected_ids = set(selected_reviewers.values_list("id", flat=True))
        TranscriptionReviewer.objects.filter(transcription=transcription).exclude(user_id__in=selected_ids).delete()
        existing_ids = set(
            TranscriptionReviewer.objects.filter(transcription=transcription).values_list("user_id", flat=True)
        )
        missing_ids = selected_ids - existing_ids
        TranscriptionReviewer.objects.bulk_create(
            [TranscriptionReviewer(transcription=transcription, user_id=user_id) for user_id in missing_ids]
        )

    def clean(self):
        """Validate the form and resolve the linked manuscript."""
        cleaned_data = super().clean()

        manuscript_id = cleaned_data.get("manuscript")
        manuscript_b_id = cleaned_data.get("manuscript_b")

        if manuscript_id:
            try:
                cleaned_data["manuscript"] = Manuscript.objects.get(pk=manuscript_id)
            except Manuscript.DoesNotExist:
                self.add_error("manuscript", _("Manuscript does not exist."))
                del cleaned_data["manuscript"]
        else:
            del cleaned_data["manuscript"]

        if manuscript_b_id:
            try:
                cleaned_data["manuscript_b"] = Biblio.objects.get(pk=manuscript_b_id)
            except Biblio.DoesNotExist:
                self.add_error("manuscript_b", _("Bibliography does not exist."))
                del cleaned_data["manuscript_b"]
        else:
            del cleaned_data["manuscript_b"]

        return cleaned_data
