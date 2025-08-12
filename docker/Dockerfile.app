# syntax=docker/dockerfile:1

############################
# 1) Builder – deps + collectstatic (no app packaging)
############################
FROM python:3.12-slim-bookworm AS builder

# OS-level deps to compile wheels for mysqlclient, Pillow, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc libc-dev pkg-config \
      libmariadb-dev libjpeg-dev zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --- Bring in dependency metadata only (cache-friendly)
COPY pyproject.toml ./

# --- Generate requirements.txt from pyproject [project.dependencies]
RUN python - <<'PY'
import tomllib, sys
from pathlib import Path
cfg = tomllib.loads(Path("pyproject.toml").read_text())
deps = cfg.get("project",{}).get("dependencies", [])
Path("/tmp/requirements.txt").write_text("\n".join(deps) + "\n")
print("Written /tmp/requirements.txt with", len(deps), "deps", file=sys.stderr)
PY

# --- Build & install deps wheels (but NOT the app itself)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
&& pip wheel --wheel-dir /wheels -r /tmp/requirements.txt

# --- Now copy the project code and collect static
COPY app/ ./app

############################
# 2) Runtime – lean image
############################
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
      default-mysql-client libmariadb3 \
      libjpeg62-turbo zlib1g \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd -ms /bin/bash appuser
WORKDIR /app

# Install deps wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy project code
COPY --from=builder /app /app

USER appuser
EXPOSE 8000

# Toggle collectstatic & server mode via env vars
# COLLECTSTATIC=1 (prod), 0 (dev). DJANGO_DEBUG=1 switches to runserver.
CMD ["bash","-lc", "\
  if [ \"${COLLECTSTATIC:-0}\" = \"1\" ]; then \
    DJANGO_SETTINGS_MODULE=lumieres_project.settings \
    python app/manage.py collectstatic --noinput; \
  fi; \
  if [ \"${DJANGO_DEBUG:-0}\" = \"1\" ]; then \
    DJANGO_SETTINGS_MODULE=lumieres_project.settings \
    python app/manage.py runserver 0.0.0.0:8000; \
  else \
    DJANGO_SETTINGS_MODULE=lumieres_project.settings \
    gunicorn app.lumieres_project.wsgi:application --bind 0.0.0.0:8000 --workers 3; \
  fi \
"]
