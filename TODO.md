# TODO

## Lint & types (ruff + ty migration)

Tooling switched to astral-sh: **ruff** (lint + format + import sort, replacing
black / isort / flake8 + plugins) and **ty** (type checking, replacing mypy).
Config lives in `pyproject.toml` (`[tool.ruff*]`, `[tool.ty*]`). Recipes:
`make lint` · `make lint/fix` · `make format` · `make format/check` ·
`make typecheck` · `make check`.

Baseline was **1131 errors** on `app/` (ruff 0.15.15). Section 0 (mechanical) is
now applied — `ruff check --fix` (205 fixes) + `ruff format` (66 files) —
leaving **887**, the manual long tail. By family now: D docstrings 563 ·
F pyflakes 111 · E pycodestyle 70 · DJ django 63 · N naming 58 · B bugbear 19 ·
C4 comprehensions 3. (W whitespace and I imports fully cleared.)

### 0. Mechanical fixes — DONE ✅

- [x] `ruff check app --fix` — 205 safe autofixes: import sorting (I001),
      unused imports / redefinitions (F401/F811), docstring blank lines
      (D202/D204/D208/D209/D210), final newline (W292), `not in` (E713).
- [x] `ruff format app` — 66 files reformatted (W291/W293 whitespace, E701
      one-liners, quotes, wrapping).
- [x] **Gotcha fixed:** `--fix` first stripped `CKEDITOR_CONFIGS` from
      `settings.py` (an F401 re-export) and broke startup → added an F401/E402
      per-file-ignore for `settings*.py`. Verified: `manage.py check` clean,
      34 tests pass.
- [ ] Optional: triage `--unsafe-fixes` (97 more) by hand:
      `ruff check app --fix --unsafe-fixes` — remaining F401/F841.

### 1. Real bugs / correctness (review individually — not cosmetic)

- [ ] **F821 undefined-name ×9** — latent `NameError`s; trace each.
- [ ] **F507 ×3** — `%`-format placeholder/arg count mismatch (runtime error).
- [ ] **F841 unused-variable ×6** — not auto-fixed (unsafe); remove or use each.
      (F811 redefinitions ×4 were auto-fixed in `a2e26d2`.)
- [ ] **B904 ×11** — use `raise … from err` inside `except` (keep tracebacks).
- [ ] **B006 mutable default arg ×3**, **B026 ×2**, **B007 / B011 / B018 ×1**.
- [ ] **E722 bare-except ×31** — replace `except:` with explicit exceptions.
- [ ] **DJ008 ×1** — model missing `__str__`.

### 2. Wildcard imports (clears F403 + F405 together — 86 findings)

- [ ] Replace `from x import *` (**F403 ×8**) with explicit imports; this also
      clears the **F405 ×78** "may be undefined from star import" noise
      (likely settings / `__init__` aggregator modules).

### 3. Django model/form conventions (DJ — 63)

- [ ] **DJ012 ×35** — reorder model body (fields → manager → Meta → `__str__`
      → save/methods).
- [ ] **DJ001 ×14** — `null=True` on string field; prefer `blank=True` + `""`.
- [ ] **DJ007 ×10** — ModelForm `fields = "__all__"`; list fields explicitly.
- [ ] **DJ006 ×3** — ModelForm `exclude`; switch to explicit `fields`.

### 4. Naming (N — 58)

- [ ] **N806 ×42** — non-lowercase locals (often class aliases `Foo = …`);
      rename, or `# noqa: N806` where the capitalised alias is intentional.
- [ ] **N802 func ×10**, **N815 mixedCase class attr ×4**, **N803 arg ×2**.

### 5. Remaining pycodestyle (E — 70)

- [ ] **E501 line-too-long ×23** — wrap/refactor (formatter won't split strings).
- [ ] **E402 module-import-not-at-top ×15** — often legit; add targeted
      `# noqa: E402` where load order is required (settings already ignored).
- [ ] **E741 ambiguous-name ×1**. (E701 one-liners were fixed by the formatter;
      E722 bare-except ×31 is tracked in §1.)

### 6. Comprehensions (C4 — 3)

- [ ] **C416 ×2** unnecessary comprehension, **C414 ×1** redundant double-cast.

### 7. Docstrings (D — 563, the long tail; lowest ROI, do last)

Mostly "missing docstring" on legacy code.

- [ ] Missing (D1xx, ×410): **D103 func 74 · D101 class 72 · D102 method 70 ·
      D100 module 63 · D106 nested-class 58 · D105 magic 34 · D107 `__init__`
      22 · D104 package 17**.
- [ ] Style (×153): **D205 49 · D200 44 · D400 39 · D401 17 · D301 2 · D419 2**
      (D202/D204/D208/D209/D210 were auto-fixed).
- [ ] **Decision:** if full docstring coverage isn't a goal, drop `D` from
      `select` (−563) or ignore just the D1xx "missing" subset (−410) before
      grinding through these.

> Static types: `make typecheck` (ty) reports **291 diagnostics**, tracked
> separately — not included in the lint counts above.

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
