# models/notes.py

from ckeditor.fields import RichTextField
from django.contrib.auth.models import Group
from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from fiches.models.contributions.ac_model import ACModel


class NoteBase(ACModel):
    """
    Abstract base model for notes.
    """
    text = RichTextField(verbose_name=_("Note"), config_name='note_ckeditor', blank=True)
    groups = models.ManyToManyField(Group, blank=True, verbose_name=_("Visible pour"))

    class Meta:
        abstract = True
        permissions = (
            ("can_see_note", "Can see Note"),
            ("can_publish_note", "Can publish note"),
        )

    def __str__(self):
        return strip_tags(self.text[:30])
