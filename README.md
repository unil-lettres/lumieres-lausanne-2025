# Lumières Lausanne

Lumières Lausanne is a Django-based website (UNIL) dedicated to the Swiss Enlightenment.  
This repo contains the application code and the Docker setup for local development, CI, staging, and production releases.

## Requirements

- **Docker Desktop 4.x+** (includes Docker Compose V2)
- **Git**
- (optional) **VS Code** + _Dev Containers_ / _Remote – Containers_ extension

---

## Quick start (local dev with Docker)

```bash
# 1) Clone
git clone https://github.com/unil-lettres/lumieres-lausanne-2025.git
cd lumieres-lausanne-2025
```

### Environment
Local development works out-of-the-box, but these are the effective defaults:

```env
# Used by Django and docker-compose services
DJANGO_ENV=development
DJANGO_DEBUG=1

# MySQL (container: "db")
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_DATABASE=lumieres_lausanne
MYSQL_USER=lluser
MYSQL_PASSWORD=lluser-password
MYSQL_ROOT_PASSWORD=toor

# Solr (container: "solr")
HAYSTACK_URL=http://solr:8983/solr/lumieres
```

### Start the stack

```bash
# 2) Start DB + Solr + app (first run pulls the images)
docker compose up -d
docker compose ps
```

- App: http://localhost:8000  
- Solr admin: http://localhost:8983/ (core: `lumieres`)

---

## Database notes

Production is now running on the migrated, current schema. Routine local setup and routine deployments do not require importing a legacy database dump or applying one-off schema normalization SQL.

If you need an exceptional restore or archival import, use the historical recovery notes in [`descr/deployment.md`](descr/deployment.md). Treat that path as migration/recovery work, not normal project setup.

Useful post-restore commands:

```bash
# Create a Django superuser (optional)
docker compose exec -T app python manage.py createsuperuser

# Refresh roles/permissions after a restore or auth-table refresh
docker compose exec -T app python manage.py sync_status_roles --apply
```

---

## Rebuild the search index (Solr / Haystack)

If search returns no results after a restore, import, or deploy:

```bash
# Ensure Solr core exists (no-op if already there)
docker compose exec -T solr bash -lc 'solr create_core -c lumieres -d /var/solr/configsets/lumieres || true'

# Rebuild via Haystack
docker compose exec -T app python manage.py rebuild_index --noinput --batch-size=500 --verbosity=2

# Sanity: how many docs?
curl -s "http://localhost:8983/solr/lumieres/select?q=*:*&rows=0&wt=json"
```

---

## Media files

Thumbnails and certain pages require files under `app/media/` (mounted into the container).  
Copy your media folder into `app/media/` (or wherever your compose maps it) before testing pages that show images.

---

## Useful commands

```bash
# See container status
docker compose ps

# Follow app logs (Ctrl+C to return)
docker compose logs -f app    # (service name is 'app' in local dev)

# One-shot last N lines
docker compose logs app --tail=200

# Run dev server/manage tasks
docker compose exec -T app python manage.py migrate
docker compose exec -T app python manage.py collectstatic --noinput
docker compose exec -T app python manage.py shell
```

---

## Documentation

Comprehensive documentation is available in the `docs/` directory and built with MkDocs.

### View Documentation

```bash
# Serve documentation locally
mkdocs serve
# Open http://127.0.0.1:8000
```

### Documentation Structure

- **[Home Page](docs/index.md)** - Project overview and quick start
- **User Guides** - For end users browsing the platform
  - [Facsimile Viewer Usage Guide](docs/facsimile-usage-guide.md)
  - [User Guide (EN)](docs/en/facsimile-user-guide.md)
  - [Guide utilisateur (FR)](docs/fr/facsimile-guide-utilisateur.md)
- **Administrator Guides** - For content editors
  - [Admin Guide (EN)](docs/en/facsimile-admin-guide.md)
  - [Guide administrateur (FR)](docs/fr/facsimile-guide-admin.md)
- **Developer Documentation** - Technical details
  - [OpenSeadragon Integration](docs/openseadragon-integration.md)
  - [IIIF Facsimile Migration](docs/iiif-facsimile-migration.md)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for complete documentation structure.

---

## VS Code (optional)

- Open the folder, then: **⌘⇧P / CTRL+SHIFT+P → “Dev Containers: Reopen in Container”**  
  This uses your existing Docker services and mounts the workspace inside the app container.

---

## Staging (notes)

A staging deployment uses a compose override and environment file (e.g. `.env.staging`) and runs with Gunicorn. The image is built multi-arch by GitHub Actions and tagged `latest-stage` (plus an immutable `sha-xxxxxxx` tag). On the staging VM we typically run:

```bash
# From the compose directory on the server (example)
docker compose pull web
docker compose up -d web
```

> If you pin the running image to a **digest** (recommended), keep at least one tag in Docker Hub that references that digest.

---

## Production (notes)

Production runs from `/u01/projects/dockerized/lumieres2-prod` on `lumieres-srv2.unil.ch`. The prod `.env` is expected to include:

```env
COMPOSE_FILE=docker-compose.yml:docker/docker-compose.prod.yml
COMPOSE_PROJECT_NAME=lumieres-prod
LUMIERES_IMAGE=unillett/lumieres:vYYYY.MM.DD
```

With those defaults in place, production operations use plain Compose commands from the prod directory:

```bash
docker compose pull web
docker compose up -d --no-deps web
docker compose exec -T web python manage.py collectstatic --noinput
docker compose exec -T web python manage.py sync_status_roles --apply
docker compose exec -T web python manage.py update_index
docker compose ps
```

Keep `LUMIERES_IMAGE` pinned to an explicit release tag; do not use `latest` for prod.

---

## Troubleshooting

- **Can’t connect to MySQL:** make sure the DB container is healthy (`docker compose ps`) and the DB name matches your environment configuration (`MYSQL_DATABASE`).
- **Search empty:** re-run `rebuild_index`.
- **Solr core missing:** (re)create it, as shown above.
- **Thumbnail errors / missing media:** copy needed media files into `app/media/`.
- **Permission error writing logs in container:** ensure the mounted `logging/` and `media/` are writable by the container user; e.g.
  ```bash
  sudo chown -R 10001:0 logging media
  sudo find logging media -type d -exec chmod 2775 {} \; ; sudo find logging media -type f -exec chmod 664 {} \;
  ```

---

### License & Contact

© University of Lausanne.  
License: pending (internal use only).  
For questions, open an issue or contact the maintainers.
