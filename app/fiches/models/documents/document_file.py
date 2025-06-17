import mimetypes
import re
from urllib.parse import urlparse

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class DocumentFile(models.Model):
    access_owner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    access_public = models.BooleanField(default=False)
    title = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=255, blank=True)
    file = models.FileField(upload_to="documents/", blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "fiches_documentfile"
        # managed = False  # If your DB table is not managed by Django migrations

    def __str__(self):
        return self.title or self.slug or f"DocumentFile #{self.id}"

    def user_access(self, user, any_login=False):
        """
        Example logic:
        - If `any_login=True`, any authenticated user can access if `access_public` is also True, or ...
        - Otherwise only staff or the owner can see it.
        """
        # If completely public, let anyone see:
        if self.access_public:
            return True

        # If any_login is True, at least require an authenticated user:
        if any_login and user.is_authenticated:
            return True

        # Otherwise owner or staff only:
        if user.is_authenticated:
            if user.is_staff or (self.access_owner and user.id == self.access_owner.id):
                return True

        return False

    def get_filetype(self):
        """
        Return a string:
            'pdf'    if attribute file exists and the mimetype is 'application/pdf'
            'image'  if attribute file exists and the mimetype is 'image/*'
            'url'    otherwise
        """
        filetype = "url"
        if self.file:
            (mt, enc) = mimetypes.guess_type("%s" % self.file)
            if re.match(r"^image/.*$", mt):
                filetype = "image"
            elif mt == "application/pdf":
                filetype = "pdf"

        return filetype

    def get_absolute_url(self):
        if self.url and urlparse(self.url)[1]:
            return self.url
        else:
            use_slug_as_id = True
            if use_slug_as_id and self.slug:
                return reverse("serve-file", kwargs={"documentfile_key": str(self.slug)}, current_app="fiches")
            else:
                return reverse("serve-file", kwargs={"documentfile_key": str(self.id)}, current_app="fiches")
