# Pin the same Python base for builders and runtime; uv stays in build/dev stages.
FROM ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 AS uv
FROM python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 AS python-base
RUN python -m pip install --no-cache-dir --upgrade pip==26.2.1

########## Common base with uv + build tools ##########
FROM python-base AS base
COPY --from=uv /uv /uvx /usr/local/bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libmariadb-dev \
    libjpeg-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml uv.lock ./

########## Stage 2: builder — prod venv only ##########
FROM base AS builder
RUN uv sync --locked --no-install-project --no-dev

########## Development target — select explicitly with --target dev ##########
FROM base AS dev
RUN uv sync --locked --no-install-project
COPY app/ /app/
RUN mkdir -p /app/logging
EXPOSE 8000
CMD ["python","manage.py","runserver","0.0.0.0:8000"]

########## Default target: production runtime, with no development tools ##########
FROM python-base AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    libjpeg62-turbo zlib1g \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app/ /app/

RUN mkdir -p /app/logging && chown -R 10001:10001 /app
USER 10001

EXPOSE 8000
CMD ["gunicorn","lumieres_project.wsgi:application","--bind","0.0.0.0:8000","--workers","3","--timeout","120"]
