# Copyright (C) 2010-2025 Université de Lausanne, RISET
# See docs/copyright.md

from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import RadioSelect
from django.utils.translation import gettext_lazy as _
from fiches.models.misc.project import Project

from .constants import DATE_DISPLAY_FORMAT, DATE_INPUT_FORMATS
from .fields import MultiplePersonField
from .models.contributions import PrimaryKeyword, SecondaryKeyword
from .models.contributiontype import ContributionType
from .models.documents import (
    TRANSCRIPTION_CHOICES,
    Biblio,
    ContributionDoc,
    ContributionMan,
    DocumentFile,
    DocumentLanguage,
    Manuscript,
    ManuscriptType,
    NoteBiblio,
    NoteTranscription,
    Transcription,
)
from .models.misc import ObjectCollection, Society
from .models.person import Person
from .widgets import DynamicList, PersonWidget, StaticList


# ===============================
# Base Form for Notes
# ===============================
class NoteFormBase(forms.ModelForm):
    def clean_text(self):
        data = self.cleaned_data.get('text', '')
        return data

    class Meta:
        # "abstract" might be omitted, etc.
        fields = []  # or define shared fields here if you want

# ===============================
# BiblioForm Definition
# ===============================
class BiblioForm(forms.ModelForm):
    """Form for editing the Biblio model (the main bibliographic record)."""
    title = forms.CharField(
        label=Biblio._meta.get_field("title").verbose_name,
        widget=forms.Textarea(attrs={"cols": "64", "rows": "3"})
    )
    # Add the "Personne" dynamic M2M field
    subj_person = MultiplePersonField(
        widget=DynamicList(
            rel=Biblio.subj_person,
            add_title="Ajouter une personne",
            placeholder="nom, prénom"
        ),
        label=_("Personne"),
        required=False
    )

        # Add this override
    subj_society = forms.ModelMultipleChoiceField(
        queryset=Society.objects.all(),
        widget=StaticList(
            add_title="Ajouter une société",
            empty_label="[ choisir une société ou académie ]"
        ),
        required=False,
        label=_("Société/Académie")
    )

    abstract = forms.CharField(
        label=_("Résumé"),
        widget=CKEditorWidget(config_name='note_ckeditor'),
        required=False
    )

    documentfiles = forms.ModelMultipleChoiceField(
        queryset=DocumentFile.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Documents")
    )

    class Meta:
        model = Biblio
        fields = '__all__'  # or list them explicitly
        widgets = {
            'short_title': forms.Textarea(attrs={"cols": "64", "rows": "1"}),
            'litterature_type': RadioSelect,
            # optionally override any other Biblio fields
        }

    def __init__(self, *args, **kwargs):
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
        self.fields['litterature_type'].required = True

        # Remove any blank choice inserted by Django for the litterature_type
        choices_without_blank = [
            choice for choice in self.fields['litterature_type'].choices
            if choice[0] != ''
        ]
        self.fields['litterature_type'].choices = choices_without_blank

        # Force date format for initial value
        date_val = self.initial.get('date') or self.data.get('date')
        if date_val:
            import datetime
            if isinstance(date_val, datetime.date):
                self.initial['date'] = date_val.strftime('%d/%m/%Y')
            else:
                # Try to parse string with known formats
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y']:
                    try:
                        d = datetime.datetime.strptime(date_val, fmt)
                        self.initial['date'] = d.strftime('%d/%m/%Y')
                        break
                    except Exception:
                        continue

        # Same logic for date2 (date de fin)
        date2_val = self.initial.get('date2') or self.data.get('date2')
        if date2_val:
            import datetime
            if isinstance(date2_val, datetime.date):
                self.initial['date2'] = date2_val.strftime('%d/%m/%Y')
            else:
                # Try to parse string with known formats
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y']:
                    try:
                        d = datetime.datetime.strptime(date2_val, fmt)
                        self.initial['date2'] = d.strftime('%d/%m/%Y')
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
        if not cleaned_data.get('subj_primary_kw'):
            self.add_error("subj_primary_kw", primary_kw_msg)

        return cleaned_data
    
    def clean_subj_person(self):
        """
        Accepts a list of person PKs (as strings or ints) or legacy 'pk|label' strings.
        Returns a list of Person instances for the M2M field.
        """
        raw_list = self.data.getlist('subj_person')
        persons = []
        for item in raw_list:
            item = item.strip()
            if not item:
                continue
            if '|' in item:
                pk_str, _ = item.split('|', 1)
            else:
                pk_str = item
            try:
                pk = int(pk_str)
                p = Person.objects.get(pk=pk)
                persons.append(p)
            except (ValueError, Person.DoesNotExist):
                raise forms.ValidationError(
                    f"La personne «{item}» n'existe pas dans la base."
                )
        return persons



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
        fields = '__all__'  # Or just ['text', 'owner'] if that's all you need

    # If your NoteBiblio model has its own fields, define them or custom widgets here.
    # e.g.
    # text = forms.CharField(widget=forms.Textarea, label="Contenu de la note", required=True)
    #
    # def clean_text(self):
    #     # do any special validation
    #     return super().clean_text()



# ===============================
# NoteFormTranscription Definition
# ===============================
class NoteFormTranscription(NoteFormBase):
    """
    Form for editing the NoteTranscription model (notes referencing a Transcription).
    """

    class Meta(NoteFormBase.Meta):
        model = NoteTranscription
        fields = '__all__'  # Or just ['text', 'owner'] if that's all you need

    # If your NoteTranscription model has its own fields, define them or custom widgets here.
    # e.g.
    # text = forms.CharField(widget=forms.Textarea, label="Contenu de la note", required=True)
    #
    # def clean_text(self):
    #     # do any special validation
    #     return super().clean_text()

# ===============================
# Other Form Definitions
# ===============================
class ManuscriptForm(forms.ModelForm):
    title = forms.CharField(
        label=Manuscript._meta.get_field("title").verbose_name,
        widget=forms.Textarea(attrs={"cols": "64", "rows": "3"})
    )
    manuscript_type = forms.ModelChoiceField(
        label=Manuscript._meta.get_field("manuscript_type").verbose_name,
        queryset=ManuscriptType.objects.all(),
        initial='1'
    )
    date = forms.DateField(
        widget=forms.DateInput(format=DATE_DISPLAY_FORMAT),
        input_formats=DATE_INPUT_FORMATS,
        label=_("Date"),
        required=False
    )
    date_f = forms.CharField(
        widget=forms.HiddenInput(attrs={'class': 'vardateformat'}),
        required=False
    )
    subj_primary_kw = forms.ModelMultipleChoiceField(
        queryset=PrimaryKeyword.objects.all(),
        widget=StaticList(),
        required=False,
        label=Manuscript._meta.get_field("subj_primary_kw").verbose_name
    )
    subj_secondary_kw = forms.ModelMultipleChoiceField(
        queryset=SecondaryKeyword.objects.all(),
        widget=StaticList(),
        required=False,
        label=Manuscript._meta.get_field("subj_secondary_kw").verbose_name
    )
    subj_society = forms.ModelMultipleChoiceField(
        queryset=Society.objects.all(),
        widget=StaticList(),
        required=False,
        label=Manuscript._meta.get_field("subj_society").verbose_name
    )
    access_date = forms.DateField(
        label=Manuscript._meta.get_field("access_date").verbose_name,
        required=False,
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.DateInput(format="%d/%m/%Y")
    )

    class Meta:
        model = Manuscript
        exclude = ('urls', 'biblio_man')  # Ensure these fields exist and are correctly excluded


class TranscriptionForm(forms.ModelForm):
    manuscript = forms.CharField(widget=forms.HiddenInput(), required=False)
    manuscript_b = forms.CharField(widget=forms.HiddenInput(), required=False)
    author = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'))
    author2 = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'), required=False)
    reviewers = forms.ModelMultipleChoiceField(queryset=User.objects.all().order_by('username'), required=False)
    status = forms.IntegerField(
        widget=forms.RadioSelect(choices=TRANSCRIPTION_CHOICES['status']),
        label=_("État"),
        initial=0
    )
    scope = forms.IntegerField(
        widget=forms.RadioSelect(choices=TRANSCRIPTION_CHOICES['scope']),
        label=_("Transcription"),
        initial=0
    )

    class Meta:
        model = Transcription
        fields = '__all__'
        widgets = {
            'facsimile_iiif_url': forms.URLInput(attrs={'style': 'width: 400px;'}),
        }

    def clean_facsimile_iiif_url(self):
        """Validate that the IIIF manifest URL points to valid JSON."""
        url = self.cleaned_data.get('facsimile_iiif_url')
        if url:
            try:
                import requests
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                import json
                json.loads(response.text)
            except (requests.RequestException, json.JSONDecodeError, ImportError):
                raise forms.ValidationError(
                    _("Invalid IIIF manifest URL. Must point to valid JSON.")
                )
        return url

    def clean(self):
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


class ContributionManForm(forms.ModelForm):
    person = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        widget=PersonWidget(
            fk_field=ContributionMan._meta.get_field('person'),
            attrs={'placeholder': 'nom, prénom'}
        ),
        label='',
        required=False
    )
    contribution_type = forms.ModelChoiceField(
        queryset=ContributionType.objects.filter(type__in=('man', 'any')),
        empty_label=None
    )

    class Meta:
        model = ContributionMan
        fields = '__all__'


class ObjectCollectionForm(forms.ModelForm):
    """
    Form for the ObjectCollection model.
    """
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("user", None)
        self.can_edit_details = kwargs.pop("can_edit_details", True)
        super().__init__(*args, **kwargs)

        can_change_owner = bool(
            self.request_user and self.request_user.has_perm("fiches.change_collection_owner")
        )

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
        exclude = ['owner', 'persons', 'bibliographies', 'transcriptions']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('Enter collection name')}),
            # Add other widgets as needed
        }
    def clean(self):
        cleaned_data = super().clean()
        # Remove or update the following if not needed:
        # person = cleaned_data.get("person")
        # contribution_type = cleaned_data.get("contribution_type")
        # if person is None:
        #     cleaned_data["contribution_type"] = None
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



from fiches.models import Biblio, Person, Transcription
from haystack.forms import ModelSearchForm
from haystack.query import RelatedSearchQuerySet


class FichesSearchForm(ModelSearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_models(self):
        """Return an alphabetical list of model classes in the index."""
        search_models = super().get_models()
        if not search_models:
            # If no models are found, retrieve them from the Haystack unified index
            search_models = connections['default'].get_unified_index().get_indexed_models()
        return search_models

    def search(self):
        if not self.is_valid():
            return self.no_query_found()

        query = self.cleaned_data.get('q')
        if not query:
            return self.no_query_found()

        # Restrict results based on user permissions and access
        if self.request and self.request.user.is_authenticated:
            if not self.request.user.has_perm('fiches.access_unpublished_transcription'):
                self.searchqueryset = RelatedSearchQuerySet().load_all_queryset(
                    Transcription,
                    Transcription.objects.filter(
                        Q(access_public=True) |
                        Q(author=self.request.user) |
                        Q(author2=self.request.user) |
                        Q(access_groups__users=self.request.user) |
                        Q(access_groups__groups__user=self.request.user) |
                        Q(project__members=self.request.user) |
                        Q(access_public=False, access_private=False, access_groups__isnull=True)
                    )
                )
        else:
            self.searchqueryset = RelatedSearchQuerySet()

        # Apply the search query
        sqs = self.searchqueryset.auto_query(query)

        if self.load_all:
            sqs = sqs.load_all()

        # Filter and order results based on models
        models = self.get_models()
        ordered_models = [m for m in (Person, Biblio, Transcription) if m in models]

        result_list = []
        for model in ordered_models:
            model_results = sqs.models(model)
            result_list.extend(list(model_results))

        return result_list
    

class ContributionDocForm(forms.ModelForm):
    # 1) Use a simple CharField, not ModelChoiceField
    person = forms.CharField(
        widget=PersonWidget(
            fk_field=ContributionDoc._meta.get_field("person"),
            attrs={'class': 'ContributionDoc_person', 'placeholder': 'nom, prénom'}
        ),
        required=False
    )
    contribution_type = forms.ModelChoiceField(
        queryset=ContributionType.objects.filter(type__in=('doc', 'any')),
        empty_label=None,
        required=False
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
                raise forms.ValidationError("Cette personne est introuvable dans la base.")

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
        desired_modern = True if litterature == "s" else False

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
        fields = ['title', 'slug', 'file', 'url', 'access_public', 'access_groups']
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': 255, 'placeholder': _('Title')}),
            'slug': forms.TextInput(attrs={'maxlength': 255, 'placeholder': _('Slug')}),
            'file': forms.ClearableFileInput(),
            'url': forms.URLInput(attrs={'placeholder': _('URL')}),
        }


class ContributionDocSecForm(ContributionDocForm):
    """Form for secondary literature contributions (modern persons only)."""

    def __init__(self, *args, **kwargs):
        """Initialize the form and filter for modern persons if possible."""
        super().__init__(*args, **kwargs)
        # If the Person model has a 'modern' field, filter the queryset for modern persons
        if hasattr(Person, 'modern'):
            self.fields['person'].widget.attrs['data-modern'] = 'true'
        # Optionally, you could add logic here to filter choices if using a ModelChoiceField


# ===============================
# ProjectForm Definition
# ===============================
class ProjectForm(forms.ModelForm):
    url = forms.SlugField(
        label=_("Url"),
        help_text=_('ATTENTION, doit être unique. Uniquement caractères non-accentués, tiret et chiffres. Pas d\'espaces ni de ponctuation.'),
        required=True,
        widget=forms.TextInput(attrs={
            'size': 40,
            'style': 'width: 60%;',
            'data-slug-source': 'name',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Project
        fields = '__all__'

    class Media:
        js = (
            'js/lib/urlify.js',
            'js/admin/project_url_tools.js',
        )

