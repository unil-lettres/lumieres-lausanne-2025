# -*- coding: utf-8 -*-
#
#    [License and copyright information]
#

from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext_lazy as _
from django import forms

from utils.fields import DictField

# Domain models
from fiches.models.documents.document import (
    DocumentType,
    ManuscriptType,
    Depot,
    LITTERATURE_TYPE_CHOICES,
    DocumentLanguage,
)
from fiches.models.contributions.keyword import PrimaryKeyword, SecondaryKeyword
from fiches.models.misc.society import Society
from fiches.models import Project


# ------------------------------------------------------------
# Saved filters (unchanged)
# ------------------------------------------------------------
class SearchFilters(models.Model):
    title = models.CharField(_("Titre"), max_length=30)
    model_name = models.CharField(max_length=30)
    query_def = models.TextField(blank=True)
    display_columns = models.TextField(blank=True)
    display_settings = DictField(blank=True)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    groups = models.ManyToManyField(Group, blank=True)

    class Meta:
        verbose_name = _("Filtre de recherche")
        verbose_name_plural = _("Filtre de recherche")
        app_label = "fiches"

    def __str__(self):
        return self.title


# ------------------------------------------------------------
# Read-only SQL views (unchanged)
# ------------------------------------------------------------
class PlaceView(models.Model):
    """Mapping to SQL view fiches_placeview (read-only)."""
    biblio_id = models.IntegerField(null=True, blank=True, verbose_name=_("Biblio ID"))
    place_name = models.CharField(max_length=255, verbose_name=_("Place Name"))

    def __str__(self):
        return f"PlaceView for {self.place_name} (Biblio ID: {self.biblio_id})"

    class Meta:
        app_label = "fiches"
        verbose_name = _("Place View")
        verbose_name_plural = _("Place Views")
        ordering = ["place_name"]
        managed = False


class JournaltitleView(models.Model):
    journal_title = models.CharField(
        max_length=512, primary_key=True, verbose_name=_("Journal Title")
    )

    def __str__(self):
        return self.journal_title

    class Meta:
        managed = False
        db_table = "fiches_journaltitleview"
        verbose_name = _("Journal Title View")
        verbose_name_plural = _("Journal Title Views")
        ordering = ["journal_title"]


# ------------------------------------------------------------
# Forms
# ------------------------------------------------------------
class QuickSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_("Rechercher"),
        widget=forms.TextInput(attrs={"placeholder": "Recherche…", "class": "search-input"}),
    )


class BiblioExtendedSearchForm(forms.Form):
    """Advanced search form (Django-5 safe, no DB queries at import time)."""

    # Recherche libre dans les champs
    EXPR_FIELDS_CHOICE = (
        ("title", "Titre du document"),
        ("authors", "Auteur / Contributeur"),
        ("person", "Personne"),
        ("edit", "Editeur"),
        ("place", "Lieu d'édition"),
    )
    OP_FIELD_CHOICES = (("or", "Ou"), ("and", "Et"), ("not", "Sauf"))

    sort = forms.ChoiceField(
        required=False,
        initial="",
        choices=(("d", "Date croissante"), ("-d", "Date décroissante"), ("t", "Titre")),
    )
    nbi = forms.ChoiceField(
        required=False,
        initial="",
        choices=(("10", "10"), ("", "25"), ("50", "50"), ("75", "75")),
    )
    grp = forms.ChoiceField(
        required=False,
        initial="d",
        choices=(("d", "Type et auteur"), ("a", "Auteur et type"), ("", "– sans regroupement –")),
    )

    x0_fld = forms.ChoiceField(required=False, choices=EXPR_FIELDS_CHOICE, initial="title")
    x0_val = forms.CharField(required=False)

    x1_op = forms.ChoiceField(required=False, choices=OP_FIELD_CHOICES, initial="and")
    x1_fld = forms.ChoiceField(required=False, choices=EXPR_FIELDS_CHOICE, initial="authors")
    x1_val = forms.CharField(required=False)

    x2_op = forms.ChoiceField(required=False, choices=OP_FIELD_CHOICES, initial="and")
    x2_fld = forms.ChoiceField(required=False, choices=EXPR_FIELDS_CHOICE, initial="place")
    x2_val = forms.CharField(required=False)

    x3_op = forms.ChoiceField(required=False, choices=OP_FIELD_CHOICES, initial="and")
    x3_fld = forms.ChoiceField(required=False, choices=EXPR_FIELDS_CHOICE, initial="edit")
    x3_val = forms.CharField(required=False)

    # Type de documents
    dt = forms.ModelMultipleChoiceField(
        required=False,
        queryset=DocumentType.objects.all().order_by("id"),
        widget=forms.CheckboxSelectMultiple(),
        label=_("Type de document"),
    )

    # Type de littérature
    ltype = forms.MultipleChoiceField(
        required=False,
        choices=LITTERATURE_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        label=_("Type de littérature"),
    )

    # Dates
    date_from = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.TextInput(attrs={"maxlength": "7", "placeholder": "aaaa.mm"}),
        label=_("Date de parution (de)"),
    )
    date_to = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.TextInput(attrs={"maxlength": "7", "placeholder": "aaaa.mm"}),
        label=_("Date de parution (à)"),
    )

    # Modification date
    mdate_from = forms.DateField(
        required=False,
        input_formats=("%Y.%m.%d",),
        widget=forms.DateInput(attrs={"size": "10", "maxlength": "10", "placeholder": "aaaa.mm.jj"}),
        label=_("Date d'enregistrement (de)"),
    )
    mdate_to = forms.DateField(
        required=False,
        input_formats=("%Y.%m.%d",),
        widget=forms.DateInput(attrs={"size": "10", "maxlength": "10", "placeholder": "aaaa.mm.jj"}),
        label=_("Date d'enregistrement (à)"),
    )

    # Langue (ModelChoiceField to avoid DB access at import time)
    l = forms.ModelChoiceField(
        required=False,
        queryset=DocumentLanguage.objects.none(),
        empty_label="< toutes >",
        label=_("Langue"),
    )

    # Lieu de dépôt
    depot = forms.ModelChoiceField(
        required=False,
        queryset=Depot.objects.none(),
        label=_("Lieu de dépôt"),
    )

    # Projets
    proj = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Project.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label=_("Projets"),
    )
    proj_op = forms.ChoiceField(required=False, initial="and", choices=OP_FIELD_CHOICES, label=_("Projets (op.)"))

    # Société/Académie
    society = forms.ModelChoiceField(
        required=False,
        queryset=Society.objects.none(),
        label=_("Société/Académie"),
    )

    # Revue (use the SQL view; no tuple building at import time)
    journal = forms.ModelChoiceField(
        required=False,
        queryset=JournaltitleView.objects.none(),
        empty_label="---------",
        label=_("Revue"),
    )

    # Type de manuscrit
    mtype = forms.ModelChoiceField(
        required=False,
        queryset=ManuscriptType.objects.none(),
        label=_("Type de manuscrit"),
    )

    # Mots clés
    kw0_op = forms.ChoiceField(required=False, initial="and", choices=OP_FIELD_CHOICES)
    kw0_p = forms.ModelChoiceField(
        required=False,
        queryset=PrimaryKeyword.objects.none(),
        empty_label="< mot-clé primaire >",
        widget=forms.Select(attrs={"class": "pkw"}),
    )
    kw0_s = forms.ModelChoiceField(required=False, queryset=SecondaryKeyword.objects.none())

    kw1_op = forms.ChoiceField(required=False, initial="and", choices=OP_FIELD_CHOICES)
    kw1_p = forms.ModelChoiceField(
        required=False,
        queryset=PrimaryKeyword.objects.none(),
        empty_label="< mot-clé primaire >",
        widget=forms.Select(attrs={"class": "pkw"}),
    )
    kw1_s = forms.ModelChoiceField(required=False, queryset=SecondaryKeyword.objects.none())

    kw2_op = forms.ChoiceField(required=False, initial="and", choices=OP_FIELD_CHOICES)
    kw2_p = forms.ModelChoiceField(
        required=False,
        queryset=PrimaryKeyword.objects.none(),
        empty_label="< mot-clé primaire >",
        widget=forms.Select(attrs={"class": "pkw"}),
    )
    kw2_s = forms.ModelChoiceField(required=False, queryset=SecondaryKeyword.objects.none())

    kw3_op = forms.ChoiceField(required=False, initial="and", choices=OP_FIELD_CHOICES)
    kw3_p = forms.ModelChoiceField(
        required=False,
        queryset=PrimaryKeyword.objects.none(),
        empty_label="< mot-clé primaire >",
        widget=forms.Select(attrs={"class": "pkw"}),
    )
    kw3_s = forms.ModelChoiceField(required=False, queryset=SecondaryKeyword.objects.none())

    # Etat collapsed/expanded des groupes de champs
    cl1 = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput(attrs={"class": "collapse_status"}))
    cl2 = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput(attrs={"class": "collapse_status"}))
    cl3 = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput(attrs={"class": "collapse_status"}))
    cl4 = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput(attrs={"class": "collapse_status"}))

# --------
# Runtime wiring (no DB access at import time)
# --------
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    # Simple alphabetical ordering for nicer UX
    self.fields["l"].queryset = DocumentLanguage.objects.order_by("name")
    self.fields["journal"].queryset = JournaltitleView.objects.order_by("journal_title")

    self.fields["depot"].queryset = Depot.objects.order_by("name")
    self.fields["mtype"].queryset = ManuscriptType.objects.order_by("name")
    self.fields["society"].queryset = Society.objects.order_by("name")

    # Default projects (permission-aware override is done in the view)
    self.fields["proj"].queryset = Project.objects.filter(publish=True).order_by("name")

    # Keywords — use 'word' (not 'name')
    pk_qs = PrimaryKeyword.objects.order_by("word")
    sk_qs = SecondaryKeyword.objects.order_by("word")

    for fld in ("kw0_p", "kw1_p", "kw2_p", "kw3_p"):
        self.fields[fld].queryset = pk_qs
        self.fields[fld].label_from_instance = lambda obj: obj.word

    for fld in ("kw0_s", "kw1_s", "kw2_s", "kw3_s"):
        self.fields[fld].queryset = sk_qs
        self.fields[fld].label_from_instance = lambda obj: obj.word

