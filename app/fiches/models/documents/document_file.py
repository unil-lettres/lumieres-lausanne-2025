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

import mimetypes
import re
from urllib.parse import urlparse

from django.db import models
from django.urls import reverse

from fiches.models.contributions.ac_model import ACModel


class DocumentFile(ACModel):
    """Model representing a file/document with access control (owner, public, groups).

    Inherits access_owner, access_public, access_groups from ACModel.
    """

    title: models.CharField = models.CharField(max_length=255, blank=True)
    slug: models.SlugField = models.SlugField(max_length=255, blank=True)
    file: models.FileField = models.FileField(upload_to="documents/", blank=True, null=True)
    url: models.URLField = models.URLField(blank=True, null=True)

    class Meta:
        """Meta options for DocumentFile."""

        db_table = "fiches_documentfile"
        verbose_name = "Fichier"
        verbose_name_plural = "Fichiers"

    def __str__(self) -> str:
        """Return a string representation of the document file."""
        return self.title or self.slug or f"DocumentFile #{self.id}"

    def user_access(self, user, any_login: bool = False) -> bool:
        """Check if the user has access to the document file.

        Uses ACModel logic for access control.
        """
        return super().user_access(user, any_login=any_login)

    def get_filetype(self) -> str:
        """Return a string describing the file type.

        'pdf'    if attribute file exists and the mimetype is 'application/pdf'.
        'image'  if attribute file exists and the mimetype is 'image/*'.
        'url'    otherwise.
        """
        filetype = "url"
        if self.file:
            mt, enc = mimetypes.guess_type(f"{self.file}")
            if mt and re.match(r"^image/.*$", mt):
                filetype = "image"
            elif mt == "application/pdf":
                filetype = "pdf"
        return filetype

    def get_absolute_url(self) -> str:
        """Return the absolute URL for the document file."""
        if self.url and urlparse(self.url)[1]:
            return self.url
        else:
            use_slug_as_id = True
            if use_slug_as_id and self.slug:
                return reverse("serve-file", kwargs={"documentfile_key": str(self.slug)}, current_app="fiches")
            else:
                return reverse("serve-file", kwargs={"documentfile_key": str(self.id)}, current_app="fiches")
