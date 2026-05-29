"""Test settings: inherit the project defaults, swap heavy services.

Used by pytest (``--ds=lumieres_project.settings_test`` /
``DJANGO_SETTINGS_MODULE`` in ``pyproject.toml``). Everything stays
in-process / in-memory so the suite is fast and does **not** require the
MySQL ``lluser`` to hold ``CREATE`` privileges nor a running Solr.
"""

from .settings import *  # noqa: F401,F403

# In-memory SQLite avoids the MySQL test-database setup entirely. CHECK and
# FOREIGN KEY constraints are enforced (Django enables PRAGMA
# foreign_keys=ON on every connection).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable Haystack's realtime signal so saving an indexed model does not
# try to push to Solr during tests.
HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.BaseSignalProcessor"

# Cheap password hasher for faster user creation in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Force DEBUG off so template errors surface clearly in tests.
DEBUG = False
