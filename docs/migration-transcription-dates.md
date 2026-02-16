# Transcription Date Fields: Schema Update and Backfill

## Summary

This project tracks two transcription dates:

- `published_date`: first public availability date ("Date de mise en ligne")
- `modified_date`: latest technical/editorial date ("Date de modification")
- `published_by_id`: user who set/edited publication date
- `modified_by_id`: user who performed latest modification

For restored legacy dumps, we do not rely on Django migrations.
We apply SQL schema changes and a one-time backfill.

## SQL Schema Update (legacy dump normalization)

Run on the target database:

```sql
ALTER TABLE fiches_transcription
  ADD COLUMN published_date datetime NULL AFTER facsimile_start_canvas;

ALTER TABLE fiches_transcription
  ADD COLUMN published_by_id int NULL AFTER published_date;

ALTER TABLE fiches_transcription
  ADD COLUMN modified_date datetime NULL AFTER published_by_id;

ALTER TABLE fiches_transcription
  ADD COLUMN modified_by_id int NULL AFTER modified_date;
```

## One-time Backfill

Populate dates from `fiches_activitylog`:

```sql
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
  t.modified_date = COALESCE(t.modified_date, a.last_activity_date);
```

Notes:

- This preserves existing values (no overwrite when already set).
- `published_date` is backfilled only for currently public transcriptions.
- You can manually adjust dates afterward if historical corrections are needed.

## Verification

```sql
SHOW COLUMNS FROM fiches_transcription LIKE 'published_date';
SHOW COLUMNS FROM fiches_transcription LIKE 'modified_date';

SELECT
  COUNT(*) AS total,
  SUM(access_public = 1) AS public_total,
  SUM(access_public = 1 AND published_date IS NOT NULL) AS public_with_published_date,
  SUM(modified_date IS NOT NULL) AS with_modified_date
FROM fiches_transcription;
```

## Related Docs

- `descr/deployment.md`
- `README.md`
