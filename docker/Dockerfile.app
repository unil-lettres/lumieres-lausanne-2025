# syntax=docker/dockerfile:1

########## Stage 1: build dependency wheels ##########
FROM python:3.12-slim-bookworm AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libmariadb-dev \
    libjpeg-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY pyproject.toml .

# Create /tmp/requirements.txt from [project.dependencies]
RUN python - <<'PY'
import tomllib, pathlib
with open("pyproject.toml","rb") as f:
    data = tomllib.load(f)
deps = data.get("project",{}).get("dependencies",[])
pathlib.Path("/tmp/requirements.txt").write_text("\n".join(deps) + "\n")
print("Wrote", len(deps), "deps to /tmp/requirements.txt")
PY

# Build wheels for all deps (mysqlclient & Pillow compile here)
RUN pip install --no-cache-dir --upgrade pip wheel \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt

########## Stage 2: slim runtime ##########
FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# Runtime libs: MySQL client + JPEG/zlib for Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    libjpeg62-turbo zlib1g \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app/app
COPY app/ /app/app/
COPY --from=builder /wheels /wheels
COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt

# Install from prebuilt wheels
RUN pip install --no-cache-dir --no-compile --find-links=/wheels -r /tmp/requirements.txt \
 && rm -rf /wheels

# Ensure a writable fallback for logs if no host volume is mounted
RUN mkdir -p /app/logging && chown -R 10001:10001 /app
USER 10001

EXPOSE 8000
CMD ["gunicorn","lumieres_project.wsgi:application","--bind","0.0.0.0:8000","--workers","3","--timeout","120"]
