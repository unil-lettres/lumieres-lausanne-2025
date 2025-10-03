# -*- coding: utf-8 -*-
#
#    Copyright (C) ...
#
from haystack.indexes import *
from haystack import indexes
import datetime
import unicodedata
from django.apps import apps  # ← use the app registry (robust to module path changes)
# from django.db.models import Q  # (unused here)

# No direct model imports; they may have moved.
# from fiches.models import DocumentFile, PrimaryKeyword, SecondaryKeyword, Person, Society, NoteBase, ACModel
# from fiches.models.document import Biblio, Manuscript, Transcription


# Migrating from haystack 1.x to 2.x
# https://django-haystack.readthedocs.io/en/master/migration_from_1_to_2.html

class BiblioIndex(indexes.SearchIndex, indexes.Indexable):
    text            = indexes.CharField(document=True, use_template=True)
    authors         = indexes.CharField(use_template=True)
    biblio_persons  = indexes.MultiValueField()
    title           = indexes.CharField(model_attr="title")
    modelSort       = indexes.CharField(default="B00")
    doctype         = indexes.CharField(model_attr="document_type__id")
    sort1           = indexes.CharField(null=True, stored=True)
    sort2           = indexes.CharField(null=True, stored=True)

    def _doc_type_label(self, obj):
        return (getattr(obj.document_type, "name", "") or "").strip().lower()

    def _doc_type_weight(self, label):
        order_map = {
            "livre": "B10",
            "chapitre de livre": "B20",
            "article de revue": "B30",
            "manuscrit": "B40",
        }
        return order_map.get(label, "B90")

    def _strip_accents(self, value):
        if not value:
            return ""
        normalized = unicodedata.normalize("NFKD", value)
        return ''.join(ch for ch in normalized if not unicodedata.combining(ch))

    def _normalize_author(self, obj):
        name = getattr(obj, "first_author_name", "") or ""
        if not name and hasattr(obj, "get_contributors"):
            try:
                contributors = obj.get_contributors().select_related("person")
            except Exception:
                contributors = obj.get_contributors()
            for contrib in contributors:
                person = getattr(contrib, "person", None)
                if person and getattr(person, "name", None):
                    name = person.name
                    break
        name = self._strip_accents(str(name or ""))
        return name.casefold()

    def _normalize_date(self, value):
        if isinstance(value, datetime.datetime):
            value = value.date()
        if isinstance(value, datetime.date):
            return value.isoformat()
        if isinstance(value, (int, float)):
            try:
                return f"{int(value):04d}-12-31"
            except Exception:
                return "9999-12-31"
        if isinstance(value, str):
            digits = ''.join(ch for ch in value if ch.isdigit())
            if len(digits) >= 4:
                return f"{digits[:4]}-12-31"
            return "9999-12-31"
        return "9999-12-31"

    def prepare_modelSort(self, obj):
        label = self._doc_type_label(obj)
        return self._doc_type_weight(label)

    def prepare_sort1(self, obj):
        author = self._normalize_author(obj)
        if not author:
            author = "zzzzzz"
        return author

    def prepare_sort2(self, obj):
        label = self._doc_type_label(obj)
        if label == "livre":
            date_val = getattr(obj, "date", None)
            return self._normalize_date(date_val)
        return ""

    def prepare_biblio_persons(self, obj):
        return [str(p) for p in obj.subj_person.all()]

    def get_model(self):
        # resolve at runtime: fiches.Biblio
        return apps.get_model("fiches", "Biblio")

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()



# class ManuscriptIndex(SearchIndex):
#     text = CharField(document=True, use_template=True, template_name='search/indexes/fiches/biblio_text.txt')
#     title = CharField(model_attr='title')
#     modelSort = CharField(default="CCC")
#     def get_queryset(self):
#         return ManuscriptB.objects.all()
# site.register(ManuscriptB, ManuscriptIndex)


class PersonIndex(indexes.SearchIndex, indexes.Indexable):
    text        = indexes.CharField(document=True, use_template=True)
    person_name = indexes.CharField(model_attr="name")
    modelSort   = indexes.CharField(default="A00")
    sort1       = indexes.CharField(null=True)
    sort2       = indexes.CharField(null=True)

    def prepare_modelSort(self, obj):
        return "A00"

    def prepare_sort1(self, obj):
        name = (obj.name or "").strip()
        if not name:
            return ""
        parts = [part.strip() for part in name.split(",") if part.strip()]
        primary = parts[0] if parts else name
        return primary.casefold()

    def prepare_sort2(self, obj):
        name = (obj.name or "").strip()
        parts = [part.strip() for part in name.split(",") if part.strip()]
        secondary = parts[1] if len(parts) > 1 else ""
        return secondary.casefold()

    def get_model(self):
        # resolve at runtime: fiches.Person
        return apps.get_model("fiches", "Person")

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return (
            self.get_model()
            .objects.filter(biography__isnull=False, biography__valid=True)
            .distinct()
        )


class TranscriptionIndex(indexes.SearchIndex, indexes.Indexable):
    text      = indexes.CharField(document=True, use_template=True)
    modelSort = indexes.CharField(default="C00")
    sort1     = indexes.CharField(null=True)
    sort2     = indexes.CharField(null=True)

    def prepare_modelSort(self, obj):
        return "C00"

    def prepare_sort1(self, obj):
        source = getattr(obj, "manuscript_b", None)
        name = getattr(source, "first_author_name", "") if source else ""
        return str(name).casefold()

    def prepare_sort2(self, obj):
        source = getattr(obj, "manuscript_b", None)
        date_val = getattr(source, "date", None) if source else None
        if hasattr(date_val, "isoformat"):
            return date_val.isoformat()
        return str(date_val or "")

    def get_model(self):
        # resolve at runtime: fiches.Transcription
        return apps.get_model("fiches", "Transcription")

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
