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

from django import forms
from django.contrib.auth.models import User

from .models.person import Person


class MultiplePersonField(forms.ModelMultipleChoiceField):
    """
    A custom field for handling multiple person-related data.
    """

    def __init__(self, *args, **kwargs):
        # Ensure you pass the queryset here, assuming you want to use the Person model
        if "queryset" not in kwargs:
            kwargs["queryset"] = Person.objects.all()
        kwargs.setdefault("widget", forms.CheckboxSelectMultiple)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        """
        Accept legacy DynamicList payload entries like ``\"123|Doe, John\"`` and
        free-text entries like ``\"|Doe, John\"``. The latter are resolved by
        form-specific cleaning, where request-user permissions are available.
        The widget stores this format in hidden inputs, while ModelMultipleChoiceField
        expects plain primary-key values.
        """
        if not value:
            return super().clean(value)

        normalized = []
        unresolved = []
        for item in value:
            if isinstance(item, Person):
                normalized.append(str(item.pk))
                continue

            text = str(item).strip()
            if not text:
                continue
            if "|" in text:
                pk_text, label = text.split("|", 1)
                text = pk_text.strip()
                label = label.strip().lstrip("|").strip()
                if not text and label:
                    unresolved.append(f"|{label}")
                    continue
            normalized.append(text)

        cleaned = list(super().clean(normalized)) if normalized else []
        cleaned.extend(unresolved)
        return cleaned


class MultipleUserField(forms.ModelMultipleChoiceField):
    """
    Accept regular user PKs and legacy DynamicList payload entries (\"id|label\").
    """

    def __init__(self, *args, **kwargs):
        if "queryset" not in kwargs:
            kwargs["queryset"] = User.objects.all()
        kwargs.setdefault("widget", forms.SelectMultiple)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            return super().clean(value)

        normalized = []
        for item in value:
            if isinstance(item, User):
                normalized.append(str(item.pk))
                continue

            text = str(item).strip()
            if not text:
                continue
            if "|" in text:
                text = text.split("|", 1)[0].strip()
            normalized.append(text)

        return super().clean(normalized)
