# -*- coding: utf-8 -*-
#
#    Copyright (C) ...
#
from haystack.indexes import *
from haystack import indexes
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
    modelSort       = indexes.CharField(default="BBB")
    doctype         = indexes.CharField(model_attr="document_type__id")
    sort1           = indexes.CharField(model_attr="first_author_name", null=True)
    sort2           = indexes.CharField(model_attr="date", null=True)

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
    modelSort   = indexes.CharField(default="AAA")
    sort1       = indexes.CharField(model_attr="name", null=True)
    sort2       = indexes.CharField(default="")

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
    modelSort = indexes.CharField(default="DDD")
    sort1     = indexes.CharField(model_attr="manuscript_b__first_author_name", null=True)
    sort2     = indexes.CharField(model_attr="manuscript_b__date", null=True)

    def get_model(self):
        # resolve at runtime: fiches.Transcription
        return apps.get_model("fiches", "Transcription")

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
