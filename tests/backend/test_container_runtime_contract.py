"""Regression checks for the container filesystem and Compose mount contract."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_image_and_django_share_the_app_root():
    """Keep Django's writable paths below the runtime image work directory."""
    dockerfile = (REPOSITORY_ROOT / "docker" / "Dockerfile.app").read_text()
    settings = (REPOSITORY_ROOT / "app" / "lumieres_project" / "settings.py").read_text()

    assert "WORKDIR /app" in dockerfile
    assert "COPY app/ /app/" in dockerfile
    assert 'logfile = BASE_DIR.parent / "logging"' in settings
    assert "BASE_DIR).parent.parent" not in settings


def test_deployment_compose_files_match_the_runtime_image_layout():
    """Prevent deployment files from restoring the obsolete /app/app layout."""
    expected_mounts = {
        "docker-compose.staging.yml": (
            "/var/www/lumieres2/static:/app/lumieres_project/staticfiles",
            "/var/www/lumieres2/media:/app/media",
            "/var/www/lumieres2/logging:/app/logging",
        ),
        "docker-compose.prod.base.yml": (
            "/u01/projects/dockerized/lumieres2-prod/static:/app/lumieres_project/staticfiles",
            "/u01/projects/dockerized/media:/app/media",
            "/u01/projects/dockerized/lumieres2-prod/logging:/app/logging",
        ),
    }

    for filename, mounts in expected_mounts.items():
        compose = (REPOSITORY_ROOT / "docker" / filename).read_text()
        assert "working_dir: /app\n" in compose
        assert "/app/app" not in compose
        for mount in mounts:
            assert mount in compose
