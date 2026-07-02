# Staging named-entities deployment - 2026-07-02

Target: `plt-tst-2.unil.ch`, `/var/www/lumieres2`, Compose project `lumieres-staging`.

Integration branch:

- `staging/named_entities`
- merge commit: `554499f`
- base: `origin/master` at `v2026.06.30.1`
- feature branch merged: `origin/feat/named_entities`

Temporary image:

- `unillett/lumieres:named-entities-2026-07-02-554499f`
- local build/push from the integration branch, `linux/amd64`

Staging rollback bundle:

- `/home/jganivet/lumieres-staging-backups/20260702_081752-named-entities-pre-refresh/`
- includes staging compose/env snapshots, image list, validated staging DB dump, and Solr configset archive.

Database refresh:

- Staging DB was replaced from a live production dump streamed from `lumieres-srv2.unil.ch`.
- The import stripped MySQL `DEFINER=` clauses because staging lacks the production definer privileges.
- Staging DB was recreated with `utf8mb4` and `utf8mb4_0900_ai_ci`.
- Post-refresh counts observed before migrations: `11687` bibliographic fiches, `1406` transcriptions.

Migration handling:

- Production/staging restored DB had no recorded `fiches` rows in `django_migrations`.
- Existing production schema already contained the baseline transcription metadata and no `django_content_type.name` column.
- Faked existing baseline through `fiches.0006_drop_legacy_contenttype_name`.
- Applied normally: `fiches.0007_placecategory` through `fiches.0019_document_nature`.

Solr:

- Staging Solr configset was backed up, then replaced from `settings/solr/configsets/lumieres/`.
- Solr was restarted and reached healthy state.
- `rebuild_index --noinput` completed after deployment.

Validation:

- Backend tests before deployment: `453 passed`.
- `manage.py check`: no issues.
- Public staging smoke checks:
  - `/`: `HTTP 200`
  - `/chercher/bibliographie/`: `HTTP 200`
  - `/chercher/person/list/`: `HTTP 200`
  - `/chercher/place/list/`: `HTTP 200`

Rollback outline:

1. Stop the named-entities web container.
2. Restore the staging DB from `staging-before-prod-refresh.sql.gz`.
3. Restore Solr configset from `solr-configsets-before-refresh.tgz` and restart Solr.
4. Start staging without `/home/jganivet/lumieres-staging-named-entities.override.yml` to return to `unillett/lumieres:stage-latest`.
5. Rebuild the search index.
