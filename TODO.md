# TODO

## Staging stack

- [ ] Create staging.mk file with staging recipes
  - [ ] staging/up, staging/down, staging/start, staging/stop
  - [ ] staging/compose/up, staging/compose/down, staging/compose/start, etc.
  - [ ] staging/compose/logs, staging/compose/build
- [ ] Create docker/compose.staging.yml
- [ ] Update COMPOSE_STAGING variable in staging.mk
- [ ] Add staging.mk to main Makefile

## Prod stack

- [ ] Create prod.mk file with prod recipes
  - [ ] prod/up, prod/down, prod/start, prod/stop
  - [ ] prod/compose/up, prod/compose/down, prod/compose/start, etc.
  - [ ] prod/compose/logs, prod/compose/build
- [ ] Create docker/compose.prod.yml
- [ ] Update COMPOSE_PROD variable in prod.mk
- [ ] Add prod.mk to main Makefile

## Docker structure

- [ ] Move docker-compose override files into docker/ folder
  - [ ] Move docker/docker-compose.dev.yml to docker/compose.dev.yml
  - [ ] Update dev.mk COMPOSE variable path
  - [ ] Verify all references are updated

## Solr

- [x] Move solr configuration to settings folder
  - [x] Identify solr data/config location
  - [x] Move to settings/solr
  - [x] Update docker-compose references
  - [ ] Update Django settings if needed

## Tests

Backend suite lives in `tests/backend/` (pytest, SQLite `settings_test`,
`--no-migrations`). Run with `make dev/tests/run` (container) or
`make dev/tests/local` (host). Coverage: `make dev/tests/local/html` → `htmlcov/`.

Baseline: **34 tests, 42% coverage**. Caveat: ~440 of the ~3390 uncovered
statements are dead/broken code (see cleanup below), so real "live" coverage is
higher — clean that first so the number means something.

### Backend

#### 0. Dead / broken code cleanup (do first — it inflates the gap)

Verified by whole-repo reference search + empirical import/instantiation. Remove
one file per commit; run the suite after each. ~446 stmts total.

- [x] Remove `fiches/management/commands/sync_perms.py` (16) — **broken**:
      `ImportError` on `get_models`/`get_app` (removed since Django 1.9);
      superseded by `sync_status_roles`; no references
- [x] Remove `pagination/paginator.py` (77) — **broken**: `AttributeError`
      (`del self._num_pages`) on instantiation; `InfinitePaginator`/
      `FinitePaginator` referenced nowhere
- [x] Remove `pagination/middleware.py` (19) — unused, not in `MIDDLEWARE`
- [x] Remove `utils/aggregates.py` (11) — `Concatenate`/`ConcatenateSQL`
      referenced nowhere
- [x] Remove `fiches/context_processors.py` (5) — not wired in `TEMPLATES`;
      its outputs (`DOCTYPE`, `display_collector`) are set per-view, so removal
      is runtime-safe
- [x] Remove `fiches/dev/__init__.py` (197) — dev-only data script, imports OK
      but zero references (code/templates/docs/CI)
- [x] Remove COinS/Zotero cluster (127): `utils/coins.py` (89),
      `utils/utils_coins.py` (24), `fiches/utils_coin.py` (14) — disabled
      feature, no external callers

> Keep (NOT dead — test gaps, do not remove): `utils/fields.py` `DictField`
> (used by `search.py` + migration 0001), `utils/__init__.py` `dbg_logger`
> (used by views), `fiches/templatetags/paginator.py` (live tag, ≠
> `pagination/paginator.py`).

#### 1. Test infrastructure / fixtures

- [ ] Shared fixtures in `conftest.py` for the common lookup rows
      (`DocumentType` pk=1, `DocumentLanguage` "Français") — remove the
      duplicated `setUp` seeding across tests
- [ ] Model factories (factory_boy or thin helpers) for `Biblio`, `Person`,
      `Transcription`, `ObjectCollection`
- [ ] Add a coverage gate (`--cov-fail-under`) once the baseline is meaningful;
      wire `make dev/tests/cov` into CI
- [ ] Scaffold `tests/frontend/` placeholder for the JS suite

#### 2. Pure functions & template tags (high ROI, little/no DB)

- [ ] `fiches/templatetags/fiches_extras.py` (38%): `startswith`,
      `decodeHtmlEntities`, `substract`, `split`, `attr`, `truncate_chars` /
      `truncatechars`, `urlizename`, `date_f`, `sort_biblio`, `in_group2`,
      `field_verbose_name`, `meta`, `access_strict`/`access_lazy`/
      `access_grouplist`/`df_access`, `docfileinfo`
- [ ] `fiches/utils.py` (21%): `supprime_accent`, `query_fiche`,
      `user_can_change_documentfile`, `user_can_delete_documentfile`,
      `get_default_publisher_user`
- [ ] `pagination/templatetags/pagination_tags.py` (40%): `autopaginate` tag +
      edge cases (orphans, last page, invalid page)
- [ ] `fiches/templatetags/{utils,collector,paginator}.py`
- [ ] `utils/fields.py` `DictField` serialization (if kept)

#### 3. Forms validation (core business rules)

- [ ] `BiblioForm`: required fields, `litterature_type`, language default,
      subject-person permissions (extend existing)
- [ ] `ManuscriptForm`, `TranscriptionForm` (extend defaults),
      `ContributionDocForm` / `ContributionDocSecForm`
- [ ] `ObjectCollectionForm`, `ProjectForm`
- [ ] `FichesSearchForm`: query construction

#### 4. Model methods & managers

- [ ] `models/person/person.py` (29%): name/display helpers, querysets
- [ ] `models/documents/document.py` (82% → fill gaps), `Transcription` managers
- [ ] `models/misc/object_collection.py` (51%), `project.py` (52%),
      `models/documents/document_file.py` (54%), `logging/activity_log.py` (40%)
- [ ] `models/search/search.py` `managed=False` view models behavior
- [ ] `models/person/biography.py` (68% → fill gaps)

#### 5. Views — smoke first, then behavior (largest absolute gap)

- [ ] Permission/auth gating + status codes for: `search` (11%),
      `collections` (14%), `projects` (13%), `biography` (15%),
      `bibliography` (31%), `transcription` (38%), `publications`, `news`
- [ ] Key behaviors: search results, create/edit flows, access control
      (public / private / group-restricted)
- [ ] Error views: extend (`server_error` done) with 403/404

#### 6. Search indexes (Haystack)

- [ ] `fiches/search_indexes.py` (0%, 131 stmts): unit-test `prepare()` /
      `prepare_*` against model instances (no Solr needed); check index text
      templates render

#### 7. Management commands

- [ ] `sync_status_roles` (74%): edge cases, idempotence, `--apply` vs dry-run
