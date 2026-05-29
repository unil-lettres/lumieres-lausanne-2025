"""Unit tests for the ckeditor app's view helper functions.

These exercise pure path/URL helpers and the filesystem image browser; none
of them touch the database. Migrated from the legacy ``ckeditor/tests.py``
and modernised (assertTrue/assertFalse, hermetic temp upload dir).
"""

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from django.apps import apps
from django.conf import settings

from ckeditor import views

# Static fixtures shipped with the ckeditor app (dummy.jpg + dummy_thumb.jpg).
# Resolved via the Django app path so it works on the host and in the container.
CKEDITOR_STATIC = Path(apps.get_app_config("ckeditor").path) / "static"


class ViewsTestCase(unittest.TestCase):
    def setUp(self):
        # Retain original settings so tearDown can restore them.
        self._orig = {
            "MEDIA_ROOT": settings.MEDIA_ROOT,
            "MEDIA_URL": settings.MEDIA_URL,
            "CKEDITOR_UPLOAD_PATH": getattr(settings, "CKEDITOR_UPLOAD_PATH", ""),
            "CKEDITOR_RESTRICT_BY_USER": getattr(settings, "CKEDITOR_RESTRICT_BY_USER", False),
            "CKEDITOR_UPLOAD_PREFIX": getattr(settings, "CKEDITOR_UPLOAD_PREFIX", None),
        }

        settings.MEDIA_ROOT = "/media/root/"
        settings.CKEDITOR_UPLOAD_PATH = os.path.join(settings.MEDIA_ROOT, "uploads")
        settings.MEDIA_URL = "/media/"

        self.test_path = os.path.join(
            settings.CKEDITOR_UPLOAD_PATH, "arbitrary", "path", "and", "filename.ext"
        )

        # Mock user object (no DB needed).
        self.mock_user = type("User", (object,), dict(username="test_user", is_superuser=False))

    def tearDown(self):
        for key, value in self._orig.items():
            setattr(settings, key, value)

    def test_get_media_url(self):
        # If provided, prefix URL with CKEDITOR_UPLOAD_PREFIX.
        settings.CKEDITOR_UPLOAD_PREFIX = "/media/ckuploads/"
        self.assertEqual(
            views.get_media_url(self.test_path),
            "/media/ckuploads/arbitrary/path/and/filename.ext",
        )

        # Otherwise fall back to MEDIA_URL + (path - MEDIA_ROOT).
        settings.CKEDITOR_UPLOAD_PREFIX = None
        self.assertEqual(
            views.get_media_url(self.test_path),
            "/media/uploads/arbitrary/path/and/filename.ext",
        )

        # Resulting URL should never include '//'.
        self.assertNotIn("//", views.get_media_url(self.test_path))

    def test_get_thumb_filename(self):
        # Thumbnail filename inserts _thumb before the extension.
        self.assertEqual(
            views.get_thumb_filename(self.test_path),
            self.test_path.replace(".ext", "_thumb.ext"),
        )
        # Without an extension it is appended.
        no_ext_path = self.test_path.replace(".ext", "")
        self.assertEqual(views.get_thumb_filename(no_ext_path), no_ext_path + "_thumb")

    def test_get_image_browse_urls(self):
        settings.MEDIA_ROOT = str(CKEDITOR_STATIC)
        settings.CKEDITOR_UPLOAD_PATH = str(CKEDITOR_STATIC / "test_uploads")

        # The fixture tree contains a single non-thumbnail image.
        self.assertTrue(views.get_image_browse_urls())
        self.assertEqual(len(views.get_image_browse_urls()), 1)

        # Don't limit browse to user path when RESTRICT_BY_USER is False.
        settings.CKEDITOR_RESTRICT_BY_USER = False
        self.assertEqual(len(views.get_image_browse_urls(self.mock_user)), 1)

        # Superusers are never limited to their own path.
        settings.CKEDITOR_RESTRICT_BY_USER = True
        self.mock_user.is_superuser = True
        self.assertEqual(len(views.get_image_browse_urls(self.mock_user)), 1)

        # Non-superusers are limited to their own (here empty) path.
        settings.CKEDITOR_RESTRICT_BY_USER = True
        self.mock_user.is_superuser = False
        self.assertFalse(views.get_image_browse_urls(self.mock_user))

    def test_get_upload_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings.CKEDITOR_UPLOAD_PATH = tmp
            date_path = datetime.now().strftime("%Y/%m/%d")

            # No user-specific path when RESTRICT_BY_USER is False.
            settings.CKEDITOR_RESTRICT_BY_USER = False
            filename = views.get_upload_filename("test.jpg", self.mock_user)
            self.assertFalse(
                filename.replace("/%s/test.jpg" % date_path, "").endswith(self.mock_user.username)
            )

            # User-specific path when RESTRICT_BY_USER is True.
            settings.CKEDITOR_RESTRICT_BY_USER = True
            filename = views.get_upload_filename("test.jpg", self.mock_user)
            self.assertTrue(
                filename.replace("/%s/test.jpg" % date_path, "").endswith(self.mock_user.username)
            )

            # Upload path ends in the current date structure.
            filename = views.get_upload_filename("test.jpg", self.mock_user)
            self.assertTrue(filename.replace("/test.jpg", "").endswith(date_path))
