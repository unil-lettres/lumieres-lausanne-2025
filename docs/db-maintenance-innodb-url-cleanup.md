# Database Maintenance: InnoDB Conversion & URL Cleanup

Two one-time maintenance procedures to run on **staging** and **production**:

1. **MyISAM → InnoDB** — convert all legacy tables to the InnoDB engine.
2. **Absolute → relative URLs** — strip the hard-coded `https://lumieres.unil.ch`
   host from editorial content stored in the database.

Both are safe to run more than once (idempotent), but each should normally be
applied **once per environment**, during a maintenance window, **after a fresh
backup**.

---

## 0. Before you start: back up the database

Always snapshot the target database first.

```bash
# Dev (project: LumieresLausanne)
make db/backup        # writes backup/sqldump/v2025/backup.sql

# Staging / Prod (run on the host, from the project directory)
docker compose exec -T db \
  mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" > backup-$(date +%Y%m%d-%H%M%S).sql
```

> **Service names differ by environment.** In **dev** the Django container is
> `app`; in **staging/prod** it is `web`, and `manage.py` lives at
> `/app/app/manage.py`. Commands below use the right name per environment.

---

## 1. MyISAM → InnoDB

InnoDB brings transactions, row-level locking and real foreign-key constraints,
which Django and the rest of the stack assume. The legacy database was imported
entirely as MyISAM.

This is shipped as Django migration
**`fiches.0005_convert_tables_to_innodb`**. It looks up every remaining MyISAM
*base table* in the current schema and runs `ALTER TABLE … ENGINE=InnoDB`
(views are skipped; the operation is a no-op on non-MySQL backends).

### Recommended: run via Django migrate

For a standard release this happens as part of the normal post-deploy `migrate`
step. To run it explicitly:

```bash
# Dev
make dev/docker/migrate ARGS=fiches
# or: docker compose exec app python manage.py migrate fiches

# Staging
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec web \
  bash -lc 'python /app/app/manage.py migrate fiches'

# Prod  (cd /u01/projects/dockerized/lumieres2-prod first)
docker compose exec web \
  bash -lc 'python /app/app/manage.py migrate fiches'
```

> ⚠️ **This can be slow and locks each table while it rebuilds.** On large
> tables expect minutes, not seconds. Run it in a maintenance window and keep
> the backup from step 0 at hand.

### Legacy-dump case (no `django_migrations` table)

If you just restored a **legacy dump**, the schema exists but Django has no
migration history (no `django_migrations` table). The data schema already
matches everything **up to `0004`**, but the tables are still MyISAM, so `0005`
must run **for real**. Fake the existing history, then apply only `0005`:

```bash
docker compose exec web bash -lc '
  M=/app/app/manage.py
  # Mark the already-present schema as applied (no DDL executed):
  for app in contenttypes auth admin sessions sites thumbnail; do
    python $M migrate --fake $app
  done
  python $M migrate --fake fiches 0004
  # Now run the engine conversion for real:
  python $M migrate fiches 0005
'
```

> Do **not** use a bare `migrate --fake` here: it would also fake `0005`,
> marking the conversion done while the tables stay MyISAM.

#### Raw-SQL fallback (no Django needed)

Skip Django entirely, convert with SQL, then fake the whole history once the
engines are correct. Generate the `ALTER` statements from the schema:

```sql
SELECT GROUP_CONCAT(CONCAT('ALTER TABLE `', table_name, '` ENGINE=InnoDB; ') SEPARATOR '\n')
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND engine = 'MyISAM'
  AND table_type = 'BASE TABLE';
-- Copy the generated statements out and run them, e.g.:
-- ALTER TABLE `fiches_biblio` ENGINE=InnoDB; ...
```

(MySQL cannot execute a multi-statement string straight from a query result, so
copy the output and run it, or loop in a shell script.)

### Verify

```sql
-- Expect: 0
SELECT COUNT(*) AS myisam_left
FROM information_schema.tables
WHERE table_schema = DATABASE() AND engine = 'MyISAM';

-- Engine breakdown (NULL engine = views)
SELECT IFNULL(engine, 'VIEW') AS engine, COUNT(*)
FROM information_schema.tables
WHERE table_schema = DATABASE()
GROUP BY engine;
```

---

## 2. Absolute → relative URL cleanup

Editorial content stored in the DB contains absolute links to
`https://lumieres.unil.ch`. These break when the site is served from another
host (staging, local) and are unnecessary on prod. The cleanup rewrites them to
relative links.

Affected columns:

| Table                 | Column        | Replacement                                          |
| --------------------- | ------------- | ---------------------------------------------------- |
| `fiches_freecontent`  | `content`     | `href="https://lumieres.unil.ch` → `href="`          |
| `fiches_news`         | `content`     | `href="https://lumieres.unil.ch` → `href="`          |
| `fiches_project`      | `description` | `href="https://lumieres.unil.ch` → `href="`          |
| `fiches_image`        | `link`        | `https://lumieres.unil.ch` → *(empty)*               |

### Dev: make recipe

```bash
make db/clean-urls
```

This pipes `tools/clean_urls.py` into the `app` container's Python (it reads the
DB credentials from the container environment).

### Staging / Prod: raw SQL (recommended)

`tools/clean_urls.py` is not guaranteed to be present inside the deployed image,
so on servers run the equivalent SQL directly against the `db` service. It is
exactly what the script does, and it is idempotent:

```sql
UPDATE fiches_freecontent SET content     = REPLACE(content,     'href="https://lumieres.unil.ch', 'href="');
UPDATE fiches_news        SET content     = REPLACE(content,     'href="https://lumieres.unil.ch', 'href="');
UPDATE fiches_project     SET description = REPLACE(description, 'href="https://lumieres.unil.ch', 'href="');
UPDATE fiches_image       SET link        = REPLACE(link,        'https://lumieres.unil.ch',        '');
```

Run it via the `db` container:

```bash
# Staging / Prod (from the project directory on the host)
docker compose exec -T db \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" <<'SQL'
UPDATE fiches_freecontent SET content     = REPLACE(content,     'href="https://lumieres.unil.ch', 'href="');
UPDATE fiches_news        SET content     = REPLACE(content,     'href="https://lumieres.unil.ch', 'href="');
UPDATE fiches_project     SET description = REPLACE(description, 'href="https://lumieres.unil.ch', 'href="');
UPDATE fiches_image       SET link        = REPLACE(link,        'https://lumieres.unil.ch',        '');
SQL
```

### Verify

```sql
-- All four should return 0
SELECT 'freecontent' AS src, COUNT(*) FROM fiches_freecontent WHERE content     LIKE '%href="https://lumieres.unil.ch%'
UNION ALL SELECT 'news',        COUNT(*) FROM fiches_news        WHERE content     LIKE '%href="https://lumieres.unil.ch%'
UNION ALL SELECT 'project',     COUNT(*) FROM fiches_project     WHERE description LIKE '%href="https://lumieres.unil.ch%'
UNION ALL SELECT 'image',       COUNT(*) FROM fiches_image       WHERE link        LIKE '%https://lumieres.unil.ch%';
```

---

## Rollback

- **InnoDB conversion**: there is no automatic rollback (we never revert to
  MyISAM). To undo, restore the backup from step 0.
- **URL cleanup**: the replacement is destructive (the absolute host is gone).
  To undo, restore the backup from step 0.

## Related docs

- `docs/migration-transcription-dates.md` — legacy dump schema normalization
- `descr/deployment.md` — staging/prod deploy reference
- `descr/prod-deploy-runbook.md` — production runbook
