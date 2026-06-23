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

"""Forms for the bibliographic and document fiches (Biblio, Manuscript, contributions, files)."""

from ckeditor.widgets import CKEditorWidget
from django import forms
from django.forms.widgets import RadioSelect
from django.utils.translation import gettext_lazy as _

from fiches.constants import DATE_DISPLAY_FORMAT, DATE_INPUT_FORMATS
from fiches.fields import MultiplePersonField
from fiches.models.contributions import PrimaryKeyword, SecondaryKeyword
from fiches.models.contributiontype import ContributionType
from fiches.models.documents import (
    Biblio,
    ContributionDoc,
    ContributionMan,
    DocumentFile,
    Manuscript,
    ManuscriptType,
)
from fiches.models.misc import Society
from fiches.models.person import Person
from fiches.widgets import DynamicList, PersonWidget, StaticList


# ===============================
# BiblioForm Definition
# ===============================
class BiblioForm(forms.ModelForm):
    """Form for editing the Biblio model (the main bibliographic record)."""

    title = forms.CharField(
        label=Biblio._meta.get_field("title").verbose_name,
        widget=forms.Textarea(attrs={"cols": "64", "rows": "3"}),
    )
    # Add the "Personne" dynamic M2M field
    subj_person = MultiplePersonField(
        widget=DynamicList(
            rel=Biblio.subj_person,
            add_title="Ajouter une personne",
            placeholder="nom, prénom",
        ),
        label=_("Personne"),
        required=False,
    )

    # Add this override
    subj_society = forms.ModelMultipleChoiceField(
        queryset=Society.objects.all(),
        widget=StaticList(
            add_title="Ajouter une société",
            empty_label="[ choisir une société ou académie ]",
        ),
        required=False,
        label=_("Société/Académie"),
    )

    abstract = forms.CharField(
        label=_("Résumé"),
        widget=CKEditorWidget(config_name="note_ckeditor"),
        required=False,
    )

    documentfiles = forms.ModelMultipleChoiceField(
        queryset=DocumentFile.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Documents"),
    )

    class Meta:
        model = Biblio
        fields = "__all__"  # or list them explicitly
        widgets = {
            "short_title": forms.Textarea(attrs={"cols": "64", "rows": "1"}),
            "litterature_type": RadioSelect,
            # optionally override any other Biblio fields
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # When the "volume" field is rendered twice in the edit form (Recueil block + general block),
        # the browser posts two values. Django keeps the last one, which is often empty, causing the
        # saved value to be wiped. Normalise the POST data to keep the first non-empty entry instead.
        if self.data:
            data_copy = self.data.copy()
            volume_values = data_copy.getlist("volume")
            if len(volume_values) > 1:
                value = ""
                for item in volume_values:
                    if str(item).strip():
                        value = item
                        break
                data_copy.setlist("volume", [value])
                self.data = data_copy

        # Example: make "litterature_type" required
        self.fields["litterature_type"].required = True

        # Remove any blank choice inserted by Django for the litterature_type
        choices_without_blank = [choice for choice in self.fields["litterature_type"].choices if choice[0] != ""]
        self.fields["litterature_type"].choices = choices_without_blank

        # Force date format for initial value
        date_val = self.initial.get("date") or self.data.get("date")
        if date_val:
            import datetime

            if isinstance(date_val, datetime.date):
                self.initial["date"] = date_val.strftime("%d/%m/%Y")
            else:
                # Try to parse string with known formats
                for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"]:
                    try:
                        d = datetime.datetime.strptime(date_val, fmt)
                        self.initial["date"] = d.strftime("%d/%m/%Y")
                        break
                    except Exception:
                        continue

        # Same logic for date2 (date de fin)
        date2_val = self.initial.get("date2") or self.data.get("date2")
        if date2_val:
            import datetime

            if isinstance(date2_val, datetime.date):
                self.initial["date2"] = date2_val.strftime("%d/%m/%Y")
            else:
                # Try to parse string with known formats
                for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"]:
                    try:
                        d = datetime.datetime.strptime(date2_val, fmt)
                        self.initial["date2"] = d.strftime("%d/%m/%Y")
                        break
                    except Exception:
                        continue

    def clean(self):
        cleaned_data = super().clean()
        doctype = cleaned_data.get("document_type")
        book_title = cleaned_data.get("book_title")
        journal_title = cleaned_data.get("journal_title")
        dictionary_title = cleaned_data.get("dictionary_title")
        manuscript_type = cleaned_data.get("manuscript_type")

        msg = _("Ce champ est obligatoire.")
        if doctype:
            # Example logic from your old code:
            if doctype.id == 2 and not book_title:
                self.add_error("book_title", msg)
            elif doctype.id == 3 and not journal_title:
                self.add_error("journal_title", msg)
            elif doctype.id == 4 and not dictionary_title:
                self.add_error("dictionary_title", msg)
            elif doctype.id == 5 and not manuscript_type:
                self.add_error("manuscript_type", msg)

        primary_kw_msg = _("Au moins un mot-clé primaire est obligatoire.")
        if not cleaned_data.get("subj_primary_kw"):
            self.add_error("subj_primary_kw", primary_kw_msg)

        return cleaned_data

    def clean_subj_person(self):
        """
        Accepts a list of person PKs, legacy 'pk|label' strings, or '|label'
        strings submitted by the DynamicList widget for newly typed people.
        Returns a list of Person instances for the M2M field.
        """
        raw_list = self.data.getlist("subj_person")
        persons = []
        for item in raw_list:
            item = item.strip()
            if not item:
                continue
            if "|" in item:
                pk_str, label = item.split("|", 1)
                pk_str = pk_str.strip()
                label = label.strip().lstrip("|").strip()
            else:
                pk_str = item
                label = ""

            if not pk_str and label:
                if not (self.user and self.user.has_perm("fiches.can_add_listitem")):
                    raise forms.ValidationError(f"La personne «{label}» n'existe pas dans la base.")
                person, _created = Person.objects.get_or_create(
                    name=label,
                    defaults={
                        "modern": False,
                        "may_have_biography": False,
                    },
                )
                persons.append(person)
                continue

            try:
                pk = int(pk_str)
                p = Person.objects.get(pk=pk)
                persons.append(p)
            except (ValueError, Person.DoesNotExist):
                label = label or item
                raise forms.ValidationError(f"La personne «{label}» n'existe pas dans la base.") from None
        return persons


# ===============================
# Other Form Definitions
# ===============================
class ManuscriptForm(forms.ModelForm):
    title = forms.CharField(
        label=Manuscript._meta.get_field("title").verbose_name,
        widget=forms.Textarea(attrs={"cols": "64", "rows": "3"}),
    )
    manuscript_type = forms.ModelChoiceField(
        label=Manuscript._meta.get_field("manuscript_type").verbose_name,
        queryset=ManuscriptType.objects.all(),
        initial="1",
    )
    date = forms.DateField(
        widget=forms.DateInput(format=DATE_DISPLAY_FORMAT),
        input_formats=DATE_INPUT_FORMATS,
        label=_("Date"),
        required=False,
    )
    date_f = forms.CharField(widget=forms.HiddenInput(attrs={"class": "vardateformat"}), required=False)
    subj_primary_kw = forms.ModelMultipleChoiceField(
        queryset=PrimaryKeyword.objects.all(),
        widget=StaticList(),
        required=False,
        label=Manuscript._meta.get_field("subj_primary_kw").verbose_name,
    )
    subj_secondary_kw = forms.ModelMultipleChoiceField(
        queryset=SecondaryKeyword.objects.all(),
        widget=StaticList(),
        required=False,
        label=Manuscript._meta.get_field("subj_secondary_kw").verbose_name,
    )
    subj_society = forms.ModelMultipleChoiceField(
        queryset=Society.objects.all(),
        widget=StaticList(),
        required=False,
        label=Manuscript._meta.get_field("subj_society").verbose_name,
    )
    access_date = forms.DateField(
        label=Manuscript._meta.get_field("access_date").verbose_name,
        required=False,
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.DateInput(format="%d/%m/%Y"),
    )

    class Meta:
        model = Manuscript
        exclude = (
            "urls",
            "biblio_man",
        )  # Ensure these fields exist and are correctly excluded


class ContributionManForm(forms.ModelForm):
    person = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        widget=PersonWidget(
            fk_field=ContributionMan._meta.get_field("person"),
            attrs={"placeholder": "nom, prénom"},
        ),
        label="",
        required=False,
    )
    contribution_type = forms.ModelChoiceField(
        queryset=ContributionType.objects.filter(type__in=("man", "any")),
        empty_label=None,
    )

    class Meta:
        model = ContributionMan
        fields = "__all__"


class ContributionDocForm(forms.ModelForm):
    # 1) Use a simple CharField, not ModelChoiceField
    person = forms.CharField(
        widget=PersonWidget(
            fk_field=ContributionDoc._meta.get_field("person"),
            attrs={"class": "ContributionDoc_person", "placeholder": "nom, prénom"},
        ),
        required=False,
    )
    contribution_type = forms.ModelChoiceField(
        queryset=ContributionType.objects.filter(type__in=("doc", "any")),
        empty_label=None,
        required=False,
    )

    class Meta:
        model = ContributionDoc
        fields = "__all__"

    def __init__(self, *args, litterature_type=None, **kwargs):
        self.litterature_type = litterature_type
        super().__init__(*args, **kwargs)
        if not self.litterature_type and getattr(self.instance, "document_id", None):
            self.litterature_type = getattr(self.instance.document, "litterature_type", None)
        self._person_was_created = False

    #
    # 2) Parse out pk from “123|Name” in clean_person()
    #
    def clean_person(self):
        raw_value = self.cleaned_data.get("person", "")
        if not raw_value.strip():
            return None

        raw_value = raw_value.strip()
        self._person_was_created = False

        if "|" in raw_value:
            pk_str, _ = raw_value.split("|", 1)
            try:
                pk = int(pk_str)
                person = Person.objects.get(pk=pk)
                return person
            except (ValueError, Person.DoesNotExist):
                raise forms.ValidationError("Cette personne est introuvable dans la base.") from None

        # If user typed an ID directly
        if raw_value.isdigit():
            try:
                person = Person.objects.get(pk=int(raw_value))
                return person
            except Person.DoesNotExist:
                pass

        # Otherwise treat as a name and create if needed
        person, created = Person.objects.get_or_create(name=raw_value)
        if created:
            self._person_was_created = True
            self._apply_person_defaults(person)
        return person

    def _apply_person_defaults(self, person):
        """
        Ensure a freshly created Person mirrors the bibliography type:
        - Secondary literature => modern=True
        - Primary literature (default) => modern=False
        In both cases, keep them without biography by default.
        """
        litterature = (self.litterature_type or "").lower()
        desired_modern = litterature == "s"

        fields_to_update = []
        if person.modern is None or person.modern != desired_modern:
            person.modern = desired_modern
            fields_to_update.append("modern")
        if person.may_have_biography:
            person.may_have_biography = False
            fields_to_update.append("may_have_biography")
        if fields_to_update:
            person.save(update_fields=fields_to_update)

    #
    # 3) Optionally skip entire row if no person was set
    #
    def clean(self):
        cleaned_data = super().clean()
        person = cleaned_data.get("person")
        # On retire la ligne seulement si aucun auteur n'est renseigné
        if not person:
            cleaned_data.pop("person", None)
            cleaned_data.pop("contribution_type", None)
        # Sinon, on conserve le type de contribution tel que saisi
        return cleaned_data


class DocumentFileForm(forms.ModelForm):
    """Form for creating and editing DocumentFile instances."""

    class Meta:
        """Meta options for DocumentFileForm."""

        model = DocumentFile
        fields = ["title", "slug", "file", "url", "access_public", "access_groups"]
        widgets = {
            "title": forms.TextInput(attrs={"maxlength": 255, "placeholder": _("Title")}),
            "slug": forms.TextInput(attrs={"maxlength": 255, "placeholder": _("Slug")}),
            "file": forms.ClearableFileInput(),
            "url": forms.URLInput(attrs={"placeholder": _("URL")}),
        }


class ContributionDocSecForm(ContributionDocForm):
    """Form for secondary literature contributions (modern persons only)."""

    def __init__(self, *args, **kwargs):
        """Initialize the form and filter for modern persons if possible."""
        super().__init__(*args, **kwargs)
        # If the Person model has a 'modern' field, filter the queryset for modern persons
        if hasattr(Person, "modern"):
            self.fields["person"].widget.attrs["data-modern"] = "true"
        # Optionally, you could add logic here to filter choices if using a ModelChoiceField
