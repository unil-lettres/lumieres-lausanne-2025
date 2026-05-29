"""Pytest configuration for the backend (Python/Django) test suite.

``DJANGO_SETTINGS_MODULE`` is normally provided by ``pyproject.toml``
(``[tool.pytest.ini_options]``); we set it here as a defensive default so the
suite can also be invoked without that file on the working directory (e.g.
from an IDE runner).

The ``tests/`` parent directory is intentionally **not** a Python package: it
is a logical container for sibling suites written in other stacks (e.g.
``tests/frontend/`` for JS).
"""

from __future__ import annotations

import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lumieres_project.settings_test")

django.setup()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Create tables for unmanaged models too.

    Some fiches models are declared ``Meta.managed = False`` because in
    production they map to SQL views or manually-maintained tables (e.g.
    ``SecondaryKeyword`` and the search views). pytest-django's
    ``--no-migrations`` mode skips them, which breaks any test exercising code
    that queries those tables. We force-create them here against the in-memory
    SQLite test DB.
    """
    from django.apps import apps
    from django.db import connection

    with django_db_blocker.unblock():
        with connection.schema_editor() as schema_editor:
            existing = set(connection.introspection.table_names())
            for model in apps.get_app_config("fiches").get_models(include_auto_created=True):
                if model._meta.managed:
                    continue
                if model._meta.db_table in existing:
                    continue
                schema_editor.create_model(model)
