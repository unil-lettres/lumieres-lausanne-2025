# Lumières Lausanne

Lumières Lausanne is a Django-based website (UNIL) dedicated to the Swiss Enlightenment.  
This repo contains the application code and the Docker setup for development, CI, and staging.

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

## Importing the database from a dump

> Works for large .sql files. Replace the dump filename with yours.

1) Put your dump at the repo root, e.g. `lumieres-prod-20250812.sql`.

2) Create (or recreate) the DB, then import:

```bash
# Create DB (if not already present)
docker compose exec -T db sh -lc \
  'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`$MYSQL_DATABASE\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"'

# Import (reads from the host file via STDIN)
docker compose exec -T db sh -lc \
  'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' \
  < lumieres-prod-20250812.sql
```

3) (Only if your dump comes from the historical Django v1 schema) apply these small fixes:

```bash
docker compose exec -T db mysql -uroot -ptoor -e "
ALTER TABLE lumieres_lausanne.fiches_biblio
  MODIFY depot varchar(128) NULL DEFAULT NULL;
ALTER TABLE lumieres_lausanne.fiches_manuscript
  MODIFY depot varchar(128) NULL DEFAULT NULL;
ALTER TABLE lumieres_lausanne.auth_user
  MODIFY COLUMN last_login DATETIME NULL;
"
```

4) Migrate and create a Django superuser (optional):

```bash
docker compose exec -T app python manage.py migrate --noinput
docker compose exec -T app python manage.py createsuperuser
```

---

## Rebuild the search index (Solr / Haystack)

If search returns no results after an import:

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

## Troubleshooting

- **Can’t connect to MySQL:** make sure the DB container is healthy (`docker compose ps`) and the DB name matches the one you imported (`MYSQL_DATABASE`).
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
Released under the [GNU Affero General Public License v3.0](LICENSE).  
For questions, open an issue or contact the maintainers.
