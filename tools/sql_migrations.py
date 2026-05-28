#!/usr/bin/env python3

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

import os
import re
import subprocess

# Define the path to your showmigrations.txt file
SHOWMIGRATIONS_FILE = "docs/tmp/showmigrations.txt"

# Create a directory to store the migration SQL files if it doesn't exist
OUTPUT_DIR = "docs/tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read through the file line by line
with open(SHOWMIGRATIONS_FILE, 'r') as file:
    current_app = None
    for line in file:
        # Check if the line contains an app name
        match_app = re.match(r'^(\w+)$', line.strip())
        if match_app:
            current_app = match_app.group(1)
            continue

        # Check if the line contains a migration that is not applied (denoted by [ ])
        match_migration = re.match(r'\[ \]\ ([0-9]{4}_[a-zA-Z_]+)', line.strip())
        if match_migration and current_app:
            migration_name = match_migration.group(1)

            # Run sqlmigrate for this specific app and migration
            result = subprocess.run(
                ['python', 'app/manage.py', 'sqlmigrate', current_app, migration_name],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                output_content = result.stdout
            else:
                output_content = f"Error: {result.stderr}"

            # Write the output to a file named after the migration
            output_file_path = os.path.join(OUTPUT_DIR, f"{current_app}_{migration_name}.sql")
            with open(output_file_path, 'w') as output_file:
                output_file.write(output_content)

print("SQL migrations have been printed and saved to files.")