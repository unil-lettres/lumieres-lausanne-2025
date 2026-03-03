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
  -- Facsimile viewer (IIIF) – 1-based start canvas index (optional):
  ALTER TABLE fiches_transcription ADD COLUMN facsimile_start_canvas int NULL AFTER facsimile_iiif_url;
  -- Transcription citation dates:
  ALTER TABLE fiches_transcription ADD COLUMN published_date datetime NULL AFTER facsimile_start_canvas;
  ALTER TABLE fiches_transcription ADD COLUMN published_by_id int NULL AFTER published_date;
  ALTER TABLE fiches_transcription ADD COLUMN modified_date datetime NULL AFTER published_by_id;
  ALTER TABLE fiches_transcription ADD COLUMN modified_by_id int NULL AFTER modified_date;
  -- Backfill transcription dates and users from activity logs (run once after adding fields):
  UPDATE fiches_transcription t
  LEFT JOIN (
    SELECT object_id, MIN(date) AS first_activity_date, MAX(date) AS last_activity_date
    FROM fiches_activitylog
    WHERE model_name = 'Transcription'
    GROUP BY object_id
  ) a ON a.object_id = t.id
  SET
    t.published_date = COALESCE(
      t.published_date,
      CASE WHEN t.access_public = 1 THEN a.first_activity_date ELSE NULL END
    ),
    t.published_by_id = COALESCE(
      t.published_by_id,
      CASE
        WHEN t.access_public = 1 THEN (
          SELECT l.user_id
          FROM fiches_activitylog l
          WHERE l.model_name = 'Transcription'
            AND l.object_id = t.id
            AND l.user_id IS NOT NULL
          ORDER BY l.date ASC, l.id ASC
          LIMIT 1
        )
        ELSE NULL
      END
    ),
    t.modified_date = COALESCE(t.modified_date, a.last_activity_date),
    t.modified_by_id = COALESCE(
      t.modified_by_id,
      (
        SELECT l.user_id
        FROM fiches_activitylog l
        WHERE l.model_name = 'Transcription'
          AND l.object_id = t.id
          AND l.user_id IS NOT NULL
        ORDER BY l.date DESC, l.id DESC
        LIMIT 1
      )
    );
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
   docker compose -f docker-compose.yml -f docker-compose.staging.yml pull web
   docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --no-deps web
   docker compose -f docker-compose.yml -f docker-compose.staging.yml logs -f web
   ```
   If `COMPOSE_FILE` is set on the host (recommended), you can run `docker compose` without `-f`.
3. **Post-deploy checks**
   ```bash
   curl -I http://127.0.0.1:8000/
   docker compose -f docker-compose.yml -f docker-compose.staging.yml exec web \
     bash -lc 'python /app/app/manage.py collectstatic --noinput'
   ```
   _Static files are stored on the host via `/var/www/lumieres2/static`, so `collectstatic` must run after every deploy to refresh the bind-mounted tree._
4. **Search index refresh**
   ```bash
  docker compose -f docker-compose.yml -f docker-compose.staging.yml exec web \
    bash -lc 'python /app/app/manage.py rebuild_index --noinput'
   ```
   Use `update_index` instead of `rebuild_index` when the schema didn’t change.

## Smoke-test checklist after deploy
- [ ] Rebuild/run the index command above.
- [ ] Sync roles (see `descr/roles.md`):
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.staging.yml exec web \
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

## Staging-Only Realignment: Published Date/User From Last Saved Event
Use this only on staging (`plt-tst-2.unil.ch`) to validate Béatrice’s rule before any prod change.

### Guardrails (staging)
- Work only in `/var/www/lumieres2`.
- Use staging compose files only: `docker-compose.yml` + `docker-compose.staging.yml`.
- Snapshot publication fields before update for quick rollback.
- Do not run this on prod unless explicitly approved.

### 1) Connect and pre-check
```bash
ssh <user>@plt-tst-2.unil.ch
cd /var/www/lumieres2

docker compose -f docker-compose.yml -f docker-compose.staging.yml ps
```

### 2) Preview impact (read-only)
```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    WITH last_event AS (
      SELECT
        object_id,
        date AS last_saved_date,
        user_id AS last_saved_user_id,
        ROW_NUMBER() OVER (
          PARTITION BY object_id
          ORDER BY date DESC, id DESC
        ) AS rn
      FROM fiches_activitylog
      WHERE model_name = \"Transcription\"
    )
    SELECT COUNT(*) AS public_rows_with_change
    FROM fiches_transcription t
    JOIN last_event e ON e.object_id = t.id AND e.rn = 1
    WHERE t.access_public = 1
      AND (
        COALESCE(t.published_date, \"1000-01-01\") <> COALESCE(e.last_saved_date, \"1000-01-01\")
        OR COALESCE(t.published_by_id, -1) <> COALESCE(e.last_saved_user_id, -1)
      );

    WITH last_event AS (
      SELECT
        object_id,
        date AS last_saved_date,
        user_id AS last_saved_user_id,
        ROW_NUMBER() OVER (
          PARTITION BY object_id
          ORDER BY date DESC, id DESC
        ) AS rn
      FROM fiches_activitylog
      WHERE model_name = \"Transcription\"
    )
    SELECT
      t.id,
      t.published_date AS before_published_date,
      e.last_saved_date AS after_published_date,
      t.published_by_id AS before_published_by,
      e.last_saved_user_id AS after_published_by
    FROM fiches_transcription t
    JOIN last_event e ON e.object_id = t.id AND e.rn = 1
    WHERE t.access_public = 1
      AND (
        COALESCE(t.published_date, \"1000-01-01\") <> COALESCE(e.last_saved_date, \"1000-01-01\")
        OR COALESCE(t.published_by_id, -1) <> COALESCE(e.last_saved_user_id, -1)
      )
    ORDER BY t.id
    LIMIT 25;
  "'
```

### 3) Snapshot + realignment update (write)
```bash
TS="$(date +%Y%m%d_%H%M%S)"

docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    CREATE TABLE backup_transcription_pub_realign_${TS} AS
    SELECT id, published_date, published_by_id
    FROM fiches_transcription;

    START TRANSACTION;

    WITH last_event AS (
      SELECT
        object_id,
        date AS last_saved_date,
        user_id AS last_saved_user_id,
        ROW_NUMBER() OVER (
          PARTITION BY object_id
          ORDER BY date DESC, id DESC
        ) AS rn
      FROM fiches_activitylog
      WHERE model_name = \"Transcription\"
    )
    UPDATE fiches_transcription t
    JOIN last_event e ON e.object_id = t.id AND e.rn = 1
    SET
      t.published_date = e.last_saved_date,
      t.published_by_id = e.last_saved_user_id
    WHERE t.access_public = 1;

    COMMIT;
  "'
```

### 4) Post-update verification
```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    SELECT COUNT(*) AS public_total
    FROM fiches_transcription
    WHERE access_public = 1;

    SELECT COUNT(*) AS published_date_filled
    FROM fiches_transcription
    WHERE access_public = 1 AND published_date IS NOT NULL;

    SELECT COUNT(*) AS published_by_filled
    FROM fiches_transcription
    WHERE access_public = 1 AND published_by_id IS NOT NULL;
  "'
```

### 5) Rollback (if needed)
```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    UPDATE fiches_transcription t
    JOIN backup_transcription_pub_realign_${TS} b ON b.id = t.id
    SET
      t.published_date = b.published_date,
      t.published_by_id = b.published_by_id;
  "'
```

### Execution Record (2026-02-24, staging)
- Scope confirmed: `plt-tst-2.unil.ch`, `/var/www/lumieres2`, staging compose files only.
- Read-only preview result:
  - `public_rows_with_change=1126`
  - `public_last_event_user_null=0`
- Realignment script executed on staging:
  - Backup table created: `backup_transcription_pub_realign_20260224_084143`
  - Update rule applied to `access_public=1` rows only:
    - `published_date = last_saved_date` (latest `fiches_activitylog` event)
    - `published_by_id = last_saved_user_id` (same latest event)
- Post-update verification:
  - `public_total=1126`
  - `published_date_filled=1126`
  - `published_by_filled=1126`
- Status: waiting for Béatrice functional validation before promoting same rule to prod.

## Tips
- Compose/env files are root-owned; edit with `sudo`.
- Shared dirs (`logging`, `media`, `static`) have group write bits for UID 10001 (web container user) to share with host users.
- When code changes include new dependencies, rebuild the image before pushing.

## Production Special Case: New Image + "Date de mise en ligne" DB fields (plan-first)

Use this procedure when a prod image introduces transcription publication fields and DB backfill logic.
This is for the mutualized production VM, so operations must stay scoped to Lumieres only.

### Guardrails (prod, mutualized VM)
- Work only in `/u01/projects/dockerized/lumieres2-prod`.
- Do not run host-wide Docker maintenance (`docker system prune`, volume deletion, daemon restart).
- Do not restart unrelated containers or services.
- Always prepare rollback assets before any DB write or container recreate.

### 1) Read-only reconnaissance (no writes)
```bash
ssh <user>@lumieres-srv2.unil.ch
cd /u01/projects/dockerized/lumieres2-prod

docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml images
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml logs --tail=100 web
df -h
```

### 2) Backup/snapshot before changes
```bash
cd /u01/projects/dockerized/lumieres2-prod
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p backups/${TS}
cp -a docker-compose.prod.base.yml docker-compose.prod.yml .env backups/${TS}/
test -f .env.prod && cp -a .env.prod backups/${TS}/

# Full DB backup (required before schema/data writes)
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec -T db \
  bash -lc 'mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" --single-transaction --no-tablespaces "$MYSQL_DATABASE"' \
  > backups/${TS}/lumieres-prod.sql

test -s backups/${TS}/lumieres-prod.sql
sha256sum backups/${TS}/lumieres-prod.sql > backups/${TS}/lumieres-prod.sql.sha256
```

### 3) DB schema + data strategy (additive + reversible)
1. Check whether columns are already present.
2. Add only missing columns as nullable.
3. Create a snapshot table for publication-related fields before backfill.
4. Run backfill.

```bash
# 3.1 Check columns
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    SHOW COLUMNS FROM fiches_transcription LIKE \"published_date\";
    SHOW COLUMNS FROM fiches_transcription LIKE \"published_by_id\";
    SHOW COLUMNS FROM fiches_transcription LIKE \"modified_date\";
    SHOW COLUMNS FROM fiches_transcription LIKE \"modified_by_id\";
  "'

# 3.2 Add missing columns (run only for columns that are absent)
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    ALTER TABLE fiches_transcription ADD COLUMN published_date datetime NULL AFTER facsimile_start_canvas;
    ALTER TABLE fiches_transcription ADD COLUMN published_by_id int NULL AFTER published_date;
    ALTER TABLE fiches_transcription ADD COLUMN modified_date datetime NULL AFTER published_by_id;
    ALTER TABLE fiches_transcription ADD COLUMN modified_by_id int NULL AFTER modified_date;
  "'

# 3.3 Snapshot fields before backfill (fast rollback path)
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    CREATE TABLE IF NOT EXISTS backup_transcription_pub_${TS} AS
    SELECT id, published_date, published_by_id, modified_date, modified_by_id
    FROM fiches_transcription;
  "'

# 3.4 Backfill publication/modified data
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    UPDATE fiches_transcription t
    LEFT JOIN (
      SELECT object_id, MIN(date) AS first_activity_date, MAX(date) AS last_activity_date
      FROM fiches_activitylog
      WHERE model_name = \"Transcription\"
      GROUP BY object_id
    ) a ON a.object_id = t.id
    SET
      t.published_date = COALESCE(
        t.published_date,
        CASE WHEN t.access_public = 1 THEN a.first_activity_date ELSE NULL END
      ),
      t.published_by_id = COALESCE(
        t.published_by_id,
        CASE
          WHEN t.access_public = 1 THEN (
            SELECT l.user_id
            FROM fiches_activitylog l
            WHERE l.model_name = \"Transcription\"
              AND l.object_id = t.id
              AND l.user_id IS NOT NULL
            ORDER BY l.date ASC, l.id ASC
            LIMIT 1
          )
          ELSE NULL
        END
      ),
      t.modified_date = COALESCE(t.modified_date, a.last_activity_date),
      t.modified_by_id = COALESCE(
        t.modified_by_id,
        (
          SELECT l.user_id
          FROM fiches_activitylog l
          WHERE l.model_name = \"Transcription\"
            AND l.object_id = t.id
            AND l.user_id IS NOT NULL
          ORDER BY l.date DESC, l.id DESC
          LIMIT 1
        )
      );
  "'
```

### 4) Deploy web image and post-deploy tasks
```bash
cd /u01/projects/dockerized/lumieres2-prod

docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml pull web
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml up -d --no-deps web
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml logs --tail=200 web

docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec web \
  bash -lc "python /app/app/manage.py collectstatic --noinput"
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec web \
  bash -lc "python /app/app/manage.py sync_status_roles --apply"
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec web \
  bash -lc "python /app/app/manage.py update_index"
```

Use `rebuild_index --noinput` instead of `update_index` if index schema changed.

### 5) Validation gates
```bash
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml ps
curl -I https://lumieres.unil.ch/
```

Manual checks:
- Transcription edit: `Accès public` + `Date de mise en ligne` behavior.
- Transcription read view: publication metadata display.
- Global search still returns expected results.

### 6) Rollback

App rollback:
```bash
# Set previous known-good tag in .env.prod or compose override, then:
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml pull web
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml up -d --no-deps web
```

DB rollback (fast path: undo backfill values only):
```bash
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
    UPDATE fiches_transcription t
    JOIN backup_transcription_pub_${TS} b ON b.id = t.id
    SET
      t.published_date = b.published_date,
      t.published_by_id = b.published_by_id,
      t.modified_date = b.modified_date,
      t.modified_by_id = b.modified_by_id;
  "'
```

DB rollback (full restore):
```bash
docker compose -f docker-compose.prod.base.yml -f docker-compose.prod.yml exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' \
  < backups/<timestamp>/lumieres-prod.sql
```

### Execution Record (2026-02-20)
- Release tag deployed: `v2026.02.20`
- Final pinned prod image: `LUMIERES_IMAGE=unillett/lumieres:v2026.02.20`
- Backup baseline:
  - `backups/20260220_135841/lumieres-prod.sql`
  - SHA256: `430ff474255526ef0964b8ab12c288ee408b06ef3644472da069a30e6deb962d`
  - Fast rollback table: `backup_transcription_pub_20260220_135841`
- Manual DB schema/backfill status:
  - Added `published_date`, `published_by_id`, `modified_date`, `modified_by_id`
  - Backfill counts: `total_transcriptions=1360`, `published_filled=1125`, `modified_filled=1359`
- Post-deploy tasks completed:
  - `collectstatic --noinput` (`1420` files copied)
  - `sync_status_roles --apply`
  - `update_index`
- Live check: `curl -I https://lumieres.unil.ch/` => `HTTP/2 200`

### Incident Note (2026-02-26): 502 Bad Gateway on Production
- Symptom window: started after an early-morning Docker restart (around 05:07 CET on `2026-02-26`).
- Root cause: `front` (nginx) kept a stale resolved IP for `web` and continued proxying to an old upstream address after `web` was recreated.
- Quick recovery used:
  ```bash
  cd /u01/projects/dockerized/lumieres2-prod
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --force-recreate front
  curl -I https://lumieres.unil.ch/
  ```
- Permanent mitigation (prod `nginx.conf`):
  ```nginx
  location / {
    resolver 127.0.0.11 valid=30s ipv6=off;
    set $django_upstream http://web:8000;
    proxy_pass $django_upstream;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    proxy_redirect off;
  }
  ```
- Apply mitigation safely:
  ```bash
  cd /u01/projects/dockerized/lumieres2-prod
  TS="$(date +%Y%m%d_%H%M%S)"
  cp -a nginx.conf backups/${TS}.nginx.conf.bak
  # edit nginx.conf with resolver + variable proxy_pass shown above
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --force-recreate front
  docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T front nginx -t
  curl -I https://lumieres.unil.ch/
  ```
- Prevention rule: after any `web` recreate/redeploy on prod, run a public check (`curl -I https://lumieres.unil.ch/`) and, if needed, recreate `front` immediately.

### Execution Record (2026-02-26)
- Release tag deployed: `v2026.02.26`
- Final pinned prod image: `LUMIERES_IMAGE=unillett/lumieres:v2026.02.26`
- Backup baseline:
  - `backups/20260226_080738/lumieres-prod.sql`
  - SHA256: `903f2864d97aef1d9b02cba1ef4f5caf24662ea4c598802567374da970867b95`
  - Fast rollback table: `backup_transcription_pub_realign_20260226_080738`
- DB realignment completed (published date/user from last saved event):
  - Scope: `access_public = 1` only
  - Verification counts: `public_total=1125`, `published_date_filled=1125`, `published_by_filled=1125`
  - Safety checks: `non_public_with_published_date=0`, `non_public_with_published_by=0`
- Deploy/post-deploy completed:
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml pull web`
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps web`
  - `collectstatic --noinput` (`1420` files copied)
  - `sync_status_roles --apply`
  - `update_index`
- Live check: `curl -I https://lumieres.unil.ch/` => `HTTP/2 200`
- Follow-up noted:
  - `https://www.lumieres.unil.ch/` returns `400` on current prod image (`v2026.02.26`) because prod `ALLOWED_HOSTS` is hardcoded.
  - Fix already pushed to `dev`: commit `d4b2425` (add `www.lumieres.unil.ch` to prod `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`).
  - Cleanup of backup artifacts (`backup_transcription_pub*` tables / old dumps) deferred.

### Execution Record (2026-02-27)
- Release tag deployed: `v2026.02.27`
- Final pinned prod image: `LUMIERES_IMAGE=unillett/lumieres:v2026.02.27`
- Backup baseline:
  - `backups/20260227_153309/` (compose/env snapshot)
  - `.env.bak-20260227_153309-before-v2026.02.27`
- Deploy/post-deploy completed:
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml pull web`
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps web`
  - `collectstatic --noinput` (`1420` files copied)
  - `sync_status_roles --apply`
  - `update_index`
- Live checks:
  - `curl -I https://lumieres.unil.ch/` => `HTTP/2 200`
  - `curl -I https://lumieres.unil.ch/projets/` => `HTTP/2 200`

Process notes from deployment:
- Compose filename drift on prod host:
  - In practice, prod currently runs with `docker-compose.yml` + `docker-compose.prod.yml`.
  - Some older instructions still mention `docker-compose.prod.base.yml`; verify files present on host before running commands.
- CI sequencing nuance:
  - Pushing `master` and then pushing the release tag triggers two `docker-prod` workflow runs for the same commit.
  - For release deploys, wait for the tag-triggered run and confirm `unillett/lumieres:vYYYY.MM.DD` is published before pulling on prod.

### Local Fix Record (2026-03-02)
- Branch: `dev`
- Scope: transcription display, edited mode (`Version éditée`)
- Issue: in `Notes de l'éditeur`, adapted words remained displayed as blue `.sic` forms after notes were rebuilt client-side.
- Root cause:
  - note HTML is reconstructed from `data-note` in JS (`createBottomNotes` / `positionSideNotes`),
  - but correction spans (`.corr`) were only injected once on the initial transcription DOM, not in reconstructed note fragments.
- Fix implemented:
  - added shared JS helper `parseAndNormalizeNoteHtml()` in `fiches/display/transcription_field.html`,
  - used it for both bottom notes and side notes so note fragments now inject `.corr` after each `.sic[data-corr]`,
  - removed temporary CSS override that forced `.sic` visibility in edited mode for notes.
- Files changed:
  - `app/fiches/templates/fiches/display/transcription_field.html`
  - `app/static/css/tinyMCE_transcripts.css`
- Local validation:
  - Docker stack running locally,
  - `python manage.py check` => no issues,
  - manual check on `http://127.0.0.1:8000/fiches/trans/270/`: in `Version éditée`, blue words disappear in `Notes de l'éditeur`; recipient address behavior remains correct.
