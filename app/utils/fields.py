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

import pickle

from django.db import models
from django.utils.encoding import smart_str


class DictField(models.Field):
    """DictField is a TextField that contains pickled dictionaries."""

    # Use the Python 3 style for defining metaclasses.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        """Convert the database value to a Python dictionary."""
        if value is None:
            return value
        try:
            return pickle.loads(value.encode("latin1"))  # Using bytes directly
        except (pickle.PickleError, ValueError):
            return value

    def to_python(self, value):
        """Unpickle our string value to Dict after we load it from the DB."""
        if value == "":
            return None

        elif isinstance(value, dict):
            return value

        try:
            if isinstance(value, str):  # Use `str` in Python 3 instead of `basestring`.
                return pickle.loads(smart_str(value))
        except (ValueError, pickle.UnpicklingError):
            return value

        return value

    def get_db_prep_save(self, value, connection):
        """Pickle our Dict object to a string before we save."""
        if isinstance(value, dict):
            value = pickle.dumps(value)
        else:
            return None

        return super().get_db_prep_save(value, connection)
