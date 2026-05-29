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

# models/free_content.py

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _

from fiches.models.content.image import Image
from fiches.models.documents.document import Document


class FreeContentManager(models.Manager):
    def get_content(self, name):
        try:
            return self.get(name=name)
        except self.model.DoesNotExist:
            return None


class FreeContent(models.Model):
    name = models.CharField(_("Nom"), unique=True, max_length=200)
    title = models.CharField(_("Titre"), max_length=200)

    created_on = models.DateTimeField(verbose_name="créé le", auto_now_add=True)
    modified_on = models.DateTimeField(verbose_name="modifié le", auto_now=True)
    author = models.ForeignKey(User, verbose_name=_("Auteur"), on_delete=models.SET_NULL, null=True, blank=True)

    content = RichTextField(verbose_name=_("Contenu"), config_name="project_ckeditor", blank=True)

    images = GenericRelation(Image)
    documents = GenericRelation(Document)

    objects = FreeContentManager()

    class Meta:
        verbose_name = _("Contenu libre")
        verbose_name_plural = _("Contenus libres")
        ordering = ["title"]

    def __str__(self):
        return self.title
