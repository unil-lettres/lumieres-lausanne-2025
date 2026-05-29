"""Sanity checks for the Django test configuration.

These tests do not hit the database; they only verify that the project test
settings are importable and contain the expected baseline.
"""

from __future__ import annotations

from django.conf import settings


def test_settings_module_loaded():
    assert settings.SETTINGS_MODULE == "lumieres_project.settings_test"


def test_test_db_is_sqlite():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"


def test_secret_key_is_defined():
    assert settings.SECRET_KEY, "SECRET_KEY must be defined"


def test_core_apps_installed():
    required = {
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "haystack",
    }
    missing = required - set(settings.INSTALLED_APPS)
    assert not missing, f"Missing INSTALLED_APPS entries: {missing}"


def test_root_urlconf():
    assert settings.ROOT_URLCONF == "lumieres_project.urls"
