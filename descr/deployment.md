# Lumières Lausanne Deployment Notes

## Staging Environment (`plt-tst-2.unil.ch`)
- **SSH access**: `ssh <user>@plt-tst-2.unil.ch`
- **Compose project root**: `/var/www/lumieres2`
  - `docker-compose.yml`
    Base stack with `db` (MySQL 9.3) and `web` (Django `unillett/lumieres:latest`). No Solr or health checks here.
  - `docker-compose.staging.yml`
    Override used in staging. Adds Solr, health checks, timeouts, and pins the staging image (`unillett/lumieres:stage-latest` or any tag you set).
- `.env`
  Used by the Compose CLI only—sets `COMPOSE_FILE=docker-compose.yml:docker-compose.staging.yml` and `COMPOSE_PROJECT_NAME=lumieres-staging`.
- `.env.staging`
  Injected into containers. Holds Django env, MySQL creds, and Solr URL.
- **Legacy schema fixes** (apply to every imported dump before the app is usable):
  ```sql
  ALTER TABLE fiches_biblio            MODIFY depot varchar(128) NULL;
  ALTER TABLE fiches_manuscript        MODIFY depot varchar(128) NULL;
  ALTER TABLE auth_user                MODIFY last_login datetime NULL;
  ALTER TABLE fiches_contributiondoc   MODIFY document_id int NULL;
  ALTER TABLE fiches_contributionman   MODIFY document_id int NULL;
  ALTER TABLE fiches_notebiblio        MODIFY owner_id int NULL;
  ALTER TABLE fiches_notemanuscript    MODIFY owner_id int NULL;
  -- Facsimile viewer (IIIF) – nullable, safe for rollback:
  ALTER TABLE fiches_transcription ADD COLUMN facsimile_iiif_url varchar(200) NULL AFTER envelope;
  ```
  _We do not run Django migrations on restored legacy dumps; normalize the schema with the ALTERs above, then sync roles and rebuild the index._
- `250715-db-lumieres.sql`: latest imported reference dump (July 15). Keep until replaced.
- Runtime directories bind-mounted into containers: `logging/`, `media/`, `static/`, `staticfiles/`, `solr/`.

## Day-to-day Operations
- Commands inherit both compose files because `.env` sets `COMPOSE_FILE`.
- Check container status:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.staging.yml ps
  ```
- Restart all services (full rebuild):
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build
  ```
- Tail logs for the web app:
  ```bash
  docker compose exec web tail -f /app/logging/app.log
  ```
- Open a shell inside the web container:
  ```bash
  docker compose exec web bash
  ```
- Run typical management commands:
  ```bash
  docker compose exec web python manage.py migrate
  docker compose exec web python manage.py createsuperuser
  ```

## Deployment playbook (staging and prod)
1. **SSH and move to the project directory**
   ```bash
   ssh <user>@<host>
   cd /var/www/lumieres2
   docker compose ps
   ```
2. **Pull and swap only the `web` image**
   (Use when DB/Solr remain unchanged and the same tag is pushed.)
   ```bash
   docker compose -f docker-compose.staging.yml pull web
   docker compose -f docker-compose.staging.yml up -d --no-deps web
   docker compose -f docker-compose.staging.yml logs -f web
   ```
3. **Post-deploy checks**
   ```bash
   curl -I http://127.0.0.1:8000/
   docker compose -f docker-compose.staging.yml exec web \
     bash -lc 'python /app/app/manage.py collectstatic --noinput'
   ```
   _Static files are stored on the host via `/var/www/lumieres2/static`, so `collectstatic` must run after every deploy to refresh the bind-mounted tree._
4. **Search index refresh**
   ```bash
  docker compose -f docker-compose.staging.yml exec web \
    bash -lc 'python /app/app/manage.py rebuild_index --noinput'
   ```
   Use `update_index` instead of `rebuild_index` when the schema didn’t change.

## Smoke-test checklist after deploy
- [ ] Rebuild/run the index command above.
- [ ] Sync roles (see `descr/roles.md`):
  ```bash
  docker compose -f docker-compose.staging.yml exec web \
    bash -lc 'python /app/app/manage.py sync_status_roles --apply'
  ```
- [ ] UI checks
  - [ ] Director account: edit a shared collection and confirm the owner dropdown appears while other fields remain read-only.
  - [ ] Doctorant-only account: edit a bibliographic fiche, add/remove an attachment to ensure permissions work.
  - [ ] Global search: multi-keyword query (e.g. “La Harpe lettre”) returns AND-filtered results with proper ordering.
  - [ ] Advanced search: “Paramètres d’affichage” toggles persist (toujours/jamais/journal filters).
- [ ] Communicate “staging refreshed” to testers/support crew.

## Cleanup Checklist
- Remove temporary backups once verified.
- Preserve `.env` and `.env.staging` (compose relies on both).
- Periodically audit `/var/www/lumieres2`; only the documented files plus data directories should exist.

## Database Maintenance
- Staging MySQL is the `db` service; run SQL via:
  ```bash
  docker compose exec db \
    mysql -ulluser -p${MYSQL_PASSWORD} lumieres_lausanne -e "SHOW TABLES;"
  ```
- Reapply the schema ALTERs after importing production dumps (locally and on staging) to keep Django happy.

## Tips
- Compose/env files are root-owned; edit with `sudo`.
- Shared dirs (`logging`, `media`, `static`) have group write bits for UID 10001 (web container user) to share with host users.
- When code changes include new dependencies, rebuild the image before pushing.
