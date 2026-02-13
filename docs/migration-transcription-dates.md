# Migration of Published and Modified Date Fields on Transcriptions

**File:** docs/migration-transcription-dates.md

---

## Summary
This document outlines the schema migration performed to add two new date fields to the `Transcription` model:

- `published_date`: The datetime when a transcription is first made public.
- `modified_date`: The datetime of last editorial or technical modification (auto-updated).

These fields support auditability and display of publication/modification dates for transcription records.


## Details of the Change
- **Model:** `app/fiches/models/documents/document.py` (`Transcription` class)
- **Fields introduced:**
  - `published_date = models.DateTimeField(null=True, blank=True, editable=False)`
  - `modified_date = models.DateTimeField(auto_now=True)`

  > Only users with the appropriate permission (admin, team, or `publish_transcription` right) can trigger the setting of `published_date` via the platform UI. The field is only set on *first publication*—subsequent unpublishing does not clear it.

- **Historical Data:**
  - For legacy records, publication dates were backfilled using the `fiches_activitylog.date` field in the database dump (`./backup/20260119_sql-dump-db-staging.sql`).

## Migration Steps

### 1. Prepare the Initial Migration
If your database already had the tables but was not tracked in Django migrations, **fake** the initial migration:

```sh
docker compose -f docker-compose.dev.yml -f docker-compose.yml exec --user vscode -w /workspaces/lumieres-lausanne-2025/app devcontainer python manage.py migrate fiches 0001_add_transcription_dates --fake
```

### 2. Apply Field and Data Migrations
Run the new migrations to add fields and backfill data:

```sh
docker compose -f docker-compose.dev.yml -f docker-compose.yml exec --user vscode -w /workspaces/lumieres-lausanne-2025/app devcontainer python manage.py migrate fiches
```

Where:
- `0002_add_transcription_date_fields.py` adds the database fields.
- `0003_populate_transcription_dates.py` backfills dates using legacy log data.

### 3. Migration Archive
For reproducibility, the migrations directory is archived here:

```
backup/fiches_migrations.tar.gz
```
(This contains all migration scripts relevant to this release and should be preserved.)

## Validating the Migration

To check that the new fields are present and populated as expected, run:

```sh
docker compose -f docker-compose.dev.yml -f docker-compose.yml exec --user vscode -w /workspaces/lumieres-lausanne-2025/app devcontainer python manage.py shell -c "from fiches.models.documents.document import Transcription; trans = Transcription.objects.filter(access_public=True).first(); print(f'ID: {trans.id}'); print(f'Published: {trans.published_date}'); print(f'Modified: {trans.modified_date}'); print(f'Public: {trans.access_public}')"
```

This should show meaningful values for `published_date` and `modified_date` for published transcriptions.

## Troubleshooting
- Ensure all migrations are listed as applied:
  ```sh
  docker compose -f docker-compose.dev.yml -f docker-compose.yml exec --user vscode -w /workspaces/lumieres-lausanne-2025/app devcontainer python manage.py showmigrations --list
  ```
- If you migrate again or in another environment, consider starting with the initial fake migration if needed.

## Related Files
- **Model:** `app/fiches/models/documents/document.py`
- **Migrations:** `app/fiches/migrations/`
- **Archive:** `backup/fiches_migrations.tar.gz`

## See Also
- [IIIF Facsimile Migration](iiif-facsimile-migration.md)
- [OpenSeadragon Integration](openseadragon-integration.md)

---

**Last updated:** February 13, 2026
