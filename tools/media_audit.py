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

"""Audit Lumières media files against a production SQL dump.

The script is intentionally read-only for the media tree and SQL dump. It writes
CSV/Markdown reports to the requested output directory.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit

KNOWN_TOP_DIRS = ("cache", "documents", "files", "images", "user_uploads")
DIRECT_MEDIA_COLUMNS = {"file", "image", "thumbnail"}
TEXT_TYPES = (
    "char",
    "text",
    "varchar",
    "longtext",
    "mediumtext",
    "tinytext",
    "json",
)

INSERT_RE = re.compile(r"^INSERT INTO `(?P<table>[^`]+)` VALUES (?P<values>.*);$")
CREATE_RE = re.compile(r"^CREATE TABLE `(?P<table>[^`]+)` \(")
COLUMN_RE = re.compile(r"^\s+`(?P<column>[^`]+)`\s+(?P<type>[a-zA-Z0-9()]+)")
MEDIA_URL_RE = re.compile(
    r"""(?ix)
    (?:
        https?://[^"'<>\s]+?
    )?
    (?P<prefix>/user-media/|/media/)
    (?P<path>[^"'<>\s)]+)
    """
)
DIRECT_PATH_RE = re.compile(
    r"""(?ix)
    (?<![A-Za-z0-9_./-])
    (?P<path>(?:cache|documents|files|images|user_uploads)/[^"<>\s]+)
    """
)
UNICODE_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})")


@dataclass
class Column:
    name: str
    sql_type: str


@dataclass
class MediaRef:
    sources: set[str] = field(default_factory=set)
    kinds: set[str] = field(default_factory=set)


class MediaLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paths: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name.lower() in {"href", "src", "data-src", "poster"} and value:
                self.paths.add(value)


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("rt", encoding="utf-8", errors="replace")


def canonical_path(path: str) -> str:
    return unicodedata.normalize("NFC", path)


def decode_unicode_escape_literals(value: str) -> str:
    return UNICODE_ESCAPE_RE.sub(lambda match: chr(int(match.group(1), 16)), value)


def mysql_unescape(value: str) -> str:
    out: list[str] = []
    i = 0
    mapping = {
        "0": "\0",
        "'": "'",
        '"': '"',
        "b": "\b",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "Z": "\x1a",
        "\\": "\\",
    }
    while i < len(value):
        char = value[i]
        if char == "\\" and i + 1 < len(value):
            i += 1
            out.append(mapping.get(value[i], value[i]))
        else:
            out.append(char)
        i += 1
    return "".join(out)


def parse_insert_values(values: str) -> Iterable[list[str | None]]:
    row: list[str | None] = []
    token: list[str] = []
    in_string = False
    escape = False
    row_open = False
    quoted_token = False

    def finish_token() -> None:
        nonlocal token, quoted_token
        raw = "".join(token)
        if quoted_token:
            row.append(mysql_unescape(raw))
        else:
            stripped = raw.strip()
            row.append(None if stripped == "NULL" else stripped)
        token = []
        quoted_token = False

    for char in values:
        if not row_open:
            if char == "(":
                row_open = True
                row = []
                token = []
                quoted_token = False
            continue

        if in_string:
            if escape:
                token.append("\\" + char)
                escape = False
            elif char == "\\":
                escape = True
            elif char == "'":
                in_string = False
            else:
                token.append(char)
            continue

        if char == "'":
            in_string = True
            quoted_token = True
        elif char == ",":
            finish_token()
        elif char == ")":
            finish_token()
            yield row
            row_open = False
        else:
            token.append(char)


def parse_schema(sql_dump: Path) -> dict[str, list[Column]]:
    schemas: dict[str, list[Column]] = {}
    current_table: str | None = None
    current_columns: list[Column] = []

    with open_text(sql_dump) as handle:
        for line in handle:
            line = line.rstrip("\n")
            create_match = CREATE_RE.match(line)
            if create_match:
                current_table = create_match.group("table")
                current_columns = []
                continue

            if current_table:
                if line.startswith(") ENGINE="):
                    schemas[current_table] = current_columns
                    current_table = None
                    current_columns = []
                    continue

                column_match = COLUMN_RE.match(line)
                if column_match:
                    current_columns.append(
                        Column(
                            name=column_match.group("column"),
                            sql_type=column_match.group("type").lower(),
                        )
                    )

    return schemas


def clean_media_path(raw_path: str) -> str | None:
    path = html.unescape(unquote(raw_path)).strip()
    if not path:
        return None

    path = path.replace("\\/", "/").replace("\\", "/")
    if path.startswith("http://") or path.startswith("https://"):
        split = urlsplit(path)
        path = split.path
    if path.startswith("/media/"):
        path = path[len("/media/") :]
    elif path.startswith("/user-media/"):
        path = "user_uploads/" + path[len("/user-media/") :]
    path = path.lstrip("/")
    path = path.split("#", 1)[0].split("?", 1)[0]
    path = path.rstrip(".,;:!?)]}")

    normalized = os.path.normpath(path).replace("\\", "/")
    if normalized in ("", ".") or normalized.startswith("../"):
        return None
    if normalized.split("/", 1)[0] not in KNOWN_TOP_DIRS:
        return None
    return canonical_path(normalized)


def add_ref(
    refs: dict[str, MediaRef], path: str | None, source: str, kind: str
) -> None:
    clean = clean_media_path(path or "")
    if not clean:
        return
    refs[clean].sources.add(source)
    refs[clean].kinds.add(kind)


def extract_paths_from_text(text: str) -> set[str]:
    found: set[str] = set()
    if not text:
        return found
    expanded = html.unescape(unquote(text))
    if "\\u" in expanded:
        expanded = decode_unicode_escape_literals(expanded)

    parser = MediaLinkParser()
    try:
        parser.feed(expanded)
    except Exception:
        pass
    found.update(parser.paths)

    for match in MEDIA_URL_RE.finditer(expanded):
        prefix = match.group("prefix")
        path = match.group("path")
        if prefix == "/user-media/":
            path = "user_uploads/" + path
        found.add(path)
    for match in DIRECT_PATH_RE.finditer(expanded):
        found.add(match.group("path"))
    return found


def walk_json_media(value, refs: dict[str, MediaRef], source: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"name", "url", "path"} and isinstance(nested, str):
                add_ref(refs, nested, source, "json")
            walk_json_media(nested, refs, source)
    elif isinstance(value, list):
        for nested in value:
            walk_json_media(nested, refs, source)
    elif isinstance(value, str):
        if "\\u" in value:
            value = decode_unicode_escape_literals(value)
        for path in extract_paths_from_text(value):
            add_ref(refs, path, source, "json")


def collect_references(
    sql_dump: Path, schemas: dict[str, list[Column]]
) -> dict[str, MediaRef]:
    refs: dict[str, MediaRef] = defaultdict(MediaRef)

    with open_text(sql_dump) as handle:
        for line in handle:
            line = line.rstrip("\n")
            insert_match = INSERT_RE.match(line)
            if not insert_match:
                continue

            table = insert_match.group("table")
            columns = schemas.get(table)
            if not columns:
                continue

            for row in parse_insert_values(insert_match.group("values")):
                if len(row) != len(columns):
                    continue

                row_id = row[0] if row else "?"
                base_source = f"{table}#{row_id}"
                for index, column in enumerate(columns):
                    value = row[index]
                    if not isinstance(value, str) or not value:
                        continue

                    source = f"{base_source}.{column.name}"
                    if column.name in DIRECT_MEDIA_COLUMNS:
                        add_ref(refs, value, source, "direct")

                    if table == "thumbnail_kvstore" and column.name == "value":
                        try:
                            walk_json_media(json.loads(value), refs, source)
                        except json.JSONDecodeError:
                            for path in extract_paths_from_text(value):
                                add_ref(refs, path, source, "json")

                    if (
                        column.name not in DIRECT_MEDIA_COLUMNS
                        and column.sql_type.startswith(TEXT_TYPES)
                    ):
                        for path in extract_paths_from_text(value):
                            add_ref(refs, path, source, "text")

    return refs


def iter_media_files(media_root: Path) -> Iterable[tuple[str, Path, os.stat_result]]:
    for root, dirs, files in os.walk(media_root):
        dirs[:] = [directory for directory in dirs if directory != "__MACOSX"]
        for filename in files:
            if filename in {".DS_Store", "Icon\r"} or filename.startswith("._"):
                continue
            full_path = Path(root) / filename
            try:
                stat = full_path.stat()
            except FileNotFoundError:
                continue
            relpath = full_path.relative_to(media_root).as_posix()
            if relpath.split("/", 1)[0] not in KNOWN_TOP_DIRS:
                continue
            yield relpath, full_path, stat


def classify(relpath: str, ref: MediaRef | None) -> str:
    if ref:
        if "direct" in ref.kinds:
            return "used_direct"
        if relpath.startswith("cache/"):
            return "used_cache"
        if "text" in ref.kinds:
            return "used_text"
        return "used_json"
    if relpath.startswith("cache/"):
        return "generated_cache_candidate"
    return "orphan_candidate"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def format_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
        amount /= 1024
    return f"{value} B"


def audit(
    sql_dump: Path, media_root: Path, output_dir: Path, hash_min_size: int
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    schemas = parse_schema(sql_dump)
    refs = collect_references(sql_dump, schemas)
    media_rows: list[dict] = []
    candidate_rows: list[dict] = []
    large_candidate_rows: list[dict] = []
    used_rows: list[dict] = []
    present_paths: set[str] = set()

    for relpath, full_path, stat in iter_media_files(media_root):
        relpath_key = canonical_path(relpath)
        present_paths.add(relpath_key)
        ref = refs.get(relpath_key)
        status = classify(relpath, ref)
        sources = sorted(ref.sources) if ref else []
        row = {
            "relpath": relpath,
            "top_dir": relpath.split("/", 1)[0],
            "size_bytes": stat.st_size,
            "size_human": format_bytes(stat.st_size),
            "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "status": status,
            "source_count": len(sources),
            "sources": "; ".join(sources[:25]),
        }
        media_rows.append(row)
        if status.startswith("used_"):
            used_rows.append(row)
        else:
            candidate_rows.append(row)
            if stat.st_size >= hash_min_size:
                large_candidate_rows.append(row)

    missing_rows = []
    for relpath, ref in sorted(refs.items()):
        if relpath in present_paths:
            continue
        missing_rows.append(
            {
                "relpath": relpath,
                "kinds": ";".join(sorted(ref.kinds)),
                "source_count": len(ref.sources),
                "sources": "; ".join(sorted(ref.sources)[:25]),
            }
        )

    media_rows.sort(key=lambda row: row["relpath"])
    used_rows.sort(key=lambda row: row["relpath"])
    candidate_rows.sort(key=lambda row: (-int(row["size_bytes"]), row["relpath"]))
    large_candidate_rows.sort(key=lambda row: (-int(row["size_bytes"]), row["relpath"]))

    fields = [
        "relpath",
        "top_dir",
        "size_bytes",
        "size_human",
        "mtime",
        "status",
        "source_count",
        "sources",
    ]
    write_csv(output_dir / "all-media-files.csv", media_rows, fields)
    write_csv(output_dir / "used-files.csv", used_rows, fields)
    write_csv(output_dir / "orphan-candidates.csv", candidate_rows, fields)
    write_csv(output_dir / "large-orphan-candidates.csv", large_candidate_rows, fields)
    write_csv(
        output_dir / "missing-referenced-files.csv",
        missing_rows,
        ["relpath", "kinds", "source_count", "sources"],
    )

    duplicate_rows = []
    if hash_min_size > 0:
        by_size: dict[int, list[dict]] = defaultdict(list)
        for row in large_candidate_rows:
            by_size[int(row["size_bytes"])].append(row)

        hash_groups: dict[str, list[dict]] = defaultdict(list)
        for same_size_rows in by_size.values():
            if len(same_size_rows) < 2:
                continue
            for row in same_size_rows:
                digest = sha256_file(media_root / row["relpath"])
                copy = dict(row)
                copy["sha256"] = digest
                hash_groups[digest].append(copy)

        for digest, rows in hash_groups.items():
            if len(rows) < 2:
                continue
            for row in rows:
                duplicate_rows.append(row)

    write_csv(
        output_dir / "duplicate-large-candidates.csv",
        sorted(duplicate_rows, key=lambda row: (row["sha256"], row["relpath"])),
        ["sha256", *fields],
    )

    status_counts = Counter(row["status"] for row in media_rows)
    status_sizes = Counter()
    top_sizes = Counter()
    top_counts = Counter()
    for row in media_rows:
        size = int(row["size_bytes"])
        status_sizes[row["status"]] += size
        top_sizes[row["top_dir"]] += size
        top_counts[row["top_dir"]] += 1

    with (output_dir / "summary.md").open("w", encoding="utf-8") as handle:
        handle.write("# Lumières Media Audit\n\n")
        handle.write(f"- SQL dump: `{sql_dump}`\n")
        handle.write(f"- Media root: `{media_root}`\n")
        handle.write(f"- Generated: `{datetime.now(timezone.utc).isoformat()}`\n\n")

        handle.write("## Totals by status\n\n")
        handle.write("| Status | Files | Size |\n")
        handle.write("| --- | ---: | ---: |\n")
        for status, count in sorted(status_counts.items()):
            handle.write(
                f"| {status} | {count} | {format_bytes(status_sizes[status])} |\n"
            )

        handle.write("\n## Totals by top directory\n\n")
        handle.write("| Top directory | Files | Size |\n")
        handle.write("| --- | ---: | ---: |\n")
        for top_dir, count in sorted(top_counts.items()):
            handle.write(
                f"| {top_dir} | {count} | {format_bytes(top_sizes[top_dir])} |\n"
            )

        handle.write("\n## Largest orphan candidates\n\n")
        handle.write("| Size | Path |\n")
        handle.write("| ---: | --- |\n")
        for row in candidate_rows[:30]:
            handle.write(f"| {row['size_human']} | `{row['relpath']}` |\n")

        handle.write("\n## Referenced files missing on disk\n\n")
        handle.write(f"- Count: {len(missing_rows)}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-dump", required=True, type=Path)
    parser.add_argument("--media-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--hash-min-size-mb",
        default=100,
        type=int,
        help="Hash orphan candidates at or above this size for duplicate detection. Use 0 to disable.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hash_min_size = args.hash_min_size_mb * 1024 * 1024
    audit(
        sql_dump=args.sql_dump.expanduser().resolve(),
        media_root=args.media_root.expanduser().resolve(),
        output_dir=args.output_dir.expanduser().resolve(),
        hash_min_size=hash_min_size,
    )


if __name__ == "__main__":
    main()
