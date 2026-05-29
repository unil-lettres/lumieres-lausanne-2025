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

# fiches/models/finding.py

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import ImageField  # Ensure sorl-thumbnail is installed

from fiches.models.content.image import Image
from fiches.models.documents.document import Document


class Finding(models.Model):
    title = models.CharField(_("Titre"), max_length=200)

    created_on = models.DateTimeField(verbose_name="créé le", auto_now_add=True)
    modified_on = models.DateTimeField(verbose_name="modifié le", auto_now=True)
    published = models.BooleanField(_("Publié"), default=False, help_text=_("Cocher pour donner un accès public."))
    author = models.ForeignKey(User, verbose_name=_("Auteur"), on_delete=models.SET_NULL, null=True, blank=True)
    author2 = models.ForeignKey(
        User,
        verbose_name=_("2e auteur"),
        related_name="finding_set2",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    description = models.TextField(_("Description"))
    thumbnail = ImageField(_("Vignette"), upload_to="images/%Y/%m")  # Using sorl-thumbnail's ImageField
    content = RichTextField(verbose_name=_("Contenu"), config_name="project_ckeditor")

    images = GenericRelation(Image)
    documents = GenericRelation(Document)

    class Meta:
        verbose_name = _("Trouvaille")
        ordering = ["-created_on"]
        app_label = "fiches"

    def __str__(self):
        return self.title
