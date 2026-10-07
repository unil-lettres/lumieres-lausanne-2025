"""Exercise the built runtime image without a database or external services."""

import importlib.metadata
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import django
import MySQLdb
from django.conf import settings
from django.core.management import call_command
from PIL import Image

assert sys.version_info[:2] == (3, 13), sys.version
expected_uid = int(os.environ.get("EXPECTED_RUNTIME_UID", "10001"))
assert os.geteuid() == expected_uid, "Runtime identity differs from the selected profile"
assert shutil.which("uv") is None, "Build-only uv leaked into runtime"
for module in ("pytest", "ruff", "ty"):
    assert importlib.util.find_spec(module) is None, f"Development tool in runtime: {module}"

minimums = {
    "Django": (5, 2, 18),
    "django-haystack": (3, 4, 0),
    "pillow": (12, 3, 0),
    "sqlparse": (0, 6, 0),
    "setuptools": (83, 0, 0),
    "urllib3": (2, 8, 0),
}
for package, floor in minimums.items():
    installed = importlib.metadata.version(package)
    assert tuple(map(int, installed.split("."))) >= floor, (package, installed, floor)
assert django.VERSION[:2] == (5, 2), "Remain on the accepted Django LTS line"
pip_version = subprocess.check_output(
    ["/usr/local/bin/python", "-c", "import importlib.metadata as m; print(m.version('pip'))"],
    text=True,
).strip()
assert tuple(map(int, pip_version.split("."))) >= (26, 2, 1), pip_version

django.setup()
call_command("check")
assert callable(MySQLdb.connect), "mysqlclient native module must load"
for format_name in ("PNG", "JPEG"):
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, format=format_name)
    buffer.seek(0)
    with Image.open(buffer) as decoded:
        decoded.load()
        assert decoded.size == (8, 8)

# These paths are task-local tmpfs mounts, never application data volumes.
media_probe = Path(settings.MEDIA_ROOT) / "runtime-check.txt"
media_probe.write_text("runtime write check")
assert media_probe.read_text() == "runtime write check"
media_probe.unlink()
assert Path(settings.LOGGING["handlers"]["file"]["filename"]).exists()

print(json.dumps({
    "python": sys.version,
    "uid": os.geteuid(),
    "system_pip": pip_version,
    "packages": sorted(
        [{"name": d.metadata["Name"], "version": d.version}
         for d in importlib.metadata.distributions()],
        key=lambda item: item["name"].lower(),
    ),
    "checks": "Django, native MySQL client, image codecs, writable media/logs, runtime separation passed",
}, indent=2))
