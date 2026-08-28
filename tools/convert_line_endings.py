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

"""Convert CRLF to LF in all text files recursively."""

import sys
from pathlib import Path


def is_text_file(file_path):
    """Check if a file is likely a text file."""
    # Skip common binary extensions
    binary_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".ico",
        ".svg",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".exe",
        ".dll",
        ".so",
        ".pyc",
        ".o",
        ".a",
        ".bin",
        ".dat",
        ".db",
        ".sqlite",
        ".webp",
        ".mp3",
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".pdf",
    }

    if file_path.suffix.lower() in binary_extensions:
        return False

    # Try to detect text by reading first chunk
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(512)
            # If we find null bytes, it's likely binary
            if b"\x00" in chunk:
                return False
        return True
    except Exception:
        return False


def convert_crlf_to_lf(file_path):
    """Convert CRLF to LF in a file. Returns True if conversion happened."""
    try:
        with open(file_path, "rb") as f:
            content = f.read()

        if b"\r\n" in content:
            with open(file_path, "wb") as f:
                f.write(content.replace(b"\r\n", b"\n"))
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False


def main():
    root = Path(".")
    converted = []

    # Walk through all directories
    for file_path in root.rglob("*"):
        # Skip directories and git folder
        if file_path.is_dir() or ".git" in file_path.parts:
            continue

        # Check if it's a text file
        if is_text_file(file_path):
            if convert_crlf_to_lf(file_path):
                converted.append(str(file_path))
                print(file_path)

    if converted:
        print(f"\nConverted {len(converted)} file(s)", file=sys.stderr)
    else:
        print("No files to convert", file=sys.stderr)


if __name__ == "__main__":
    main()
