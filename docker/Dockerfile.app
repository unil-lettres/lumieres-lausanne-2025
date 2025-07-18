# syntax=docker/dockerfile:1

############################
# 1) Builder – wheels + static
############################
FROM python:3.12-slim-bookworm AS builder

# OS-level deps needed to compile wheels **and** run collectstatic
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc libc-dev pkg-config \
      libmariadb-dev libjpeg-dev zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Copy code & dependency metadata ----------------------------------------
COPY pyproject.toml poetry.lock* ./
COPY app/ ./app

# --- Build wheels and install them (needed for collectstatic) ---------------
RUN pip install --upgrade pip setuptools wheel \
 && pip wheel --wheel-dir /wheels . \
 && pip install --no-cache-dir /wheels/*

# --- Collect static assets ---------------------------------------------------
WORKDIR /app/app
ENV DJANGO_SETTINGS_MODULE=lumieres_project.settings_build
RUN python manage.py collectstatic --noinput

############################
# 2) Runtime – lean image
############################
FROM python:3.12-slim-bookworm AS runtime

# Only runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
      default-mysql-client libmariadb3 \
      libjpeg62-turbo zlib1g \
  && rm -rf /var/lib/apt/lists/*

# Non-root user for best practice
RUN useradd -ms /bin/bash appuser
WORKDIR /app

# Install the wheels we built earlier
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy *all* project code **including** pre-collected staticfiles
COPY --from=builder /app /app

USER appuser

EXPOSE 8000
CMD ["gunicorn", "app.lumieres_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
