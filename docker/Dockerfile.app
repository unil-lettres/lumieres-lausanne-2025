########## Stage 1: common base with uv + build tools ##########
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base
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

########## Stage 3: runtime — slim image with prod venv ##########
FROM python:3.13-slim-bookworm AS runtime
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

########## Stage 4: dev — base image with all deps (uv available) ##########
FROM base AS dev
RUN uv sync --locked --no-install-project
COPY app/ /app/
RUN mkdir -p /app/logging
EXPOSE 8000
CMD ["python","manage.py","runserver","0.0.0.0:8000"]
