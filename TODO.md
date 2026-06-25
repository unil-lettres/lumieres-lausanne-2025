# TODO

## Named entities — place fiches (Lieux, section 3)

Built brick by brick on this branch; full status + commit table in the local draft
`PR-named-entities-section-3.md`.

**Done ✅**

- [x] Data model (migrations 0006–0012): `PlaceCategory`, `ReferenceSite` (+seeds),
      `PlaceRecord`, `PlaceVariant`, `PlaceReferenceSite`, `NotePlace`; drop of the phantom
      `django_content_type.name` column (0006).
- [x] Search (Solr) foundation: `PlaceRecordIndex` + variant/reference reindex signals
      (variants and reference sites searchable in 3 forms).
- [x] Uniqueness (3.3): name + category, enforced at the model **and** the form.
- [x] Editing interface (3.2): create/edit views + `lieu/` URLs + templates; chip/autocomplete
      widgets (variants, reference permalink, related-places search) replacing the inline
      formsets; dedicated `place-autocomplete` endpoint (`ajax_search` refuses ACModels).
- [x] Creation entry points: workspace « Création de fiches » + read-view button.
- [x] Read-view page (3.4 *page*): proper fiche display (extends `display_base2`).

**Blocked 🔒 — needs cross-section place tagging (§1 / §2 / §4)**

- [ ] 3.4.1 linked biographies listing (← §2: bio lieu de naissance/décès/fonction → `PlaceRecord`)
- [ ] 3.4.2 publications listings, 3 sections (← §4: biblio « Lieu » / « Lieu 2 » → `PlaceRecord`)
- [ ] 3.4.3 transcriptions listing (← §1: « Sujets › Lieu(x) » in transcriptions)

**Other pending (independent of tagging)**

- [ ] Place **tagging** in transcriptions / bio / biblio (§1 / §2 / §4) — prerequisite for 3.4.
- [ ] « Liste des lieux » advanced-search tab (§5) — also gives the place list page + `add_url`.
- [ ] Wire places into the global search results UI (the Solr index foundation is in place).
- [ ] Read-view note gating (#109), template comment (#110), public labels (#111).

## Lint & types (ruff + ty migration)

Tooling switched to astral-sh: **ruff** (lint + format + import sort, replacing
black / isort / flake8 + plugins) and **ty** (type checking, replacing mypy).
Config lives in `pyproject.toml` (`[tool.ruff*]`, `[tool.ty*]`). Recipes:
`make lint` · `make lint/fix` · `make format` · `make format/check` ·
`make typecheck` · `make check`.

Baseline was **1131 errors** on `app/` (ruff 0.15.15). After the mechanical
fixes, the correctness/robustness pass, and adopting the client's expanded
ruleset (Q/SIM/C90/PLR/UP), **868** remain.

**Done** (regression tests in `tests/backend/test_lint_regressions.py` where
behaviour changed): F821/F507 latent bugs · bugbear B-series
(B006/B026/B904/B011/B018/B007) · wildcard imports (F403/F405) · SIM115 file
handling · E722 bare-excepts narrowed to precise types · the mechanical
SIM/C4/F401/F841 lot.

**Deferred to backlog** (client decision):
- **Complexity — C901 + PLR0915/0912/0911/0913 (~73)**: refactoring legacy
  functions is high-risk/subjective; revisit as a dedicated effort.
- **Docstrings — D (~557)**: bulk back-filling, low ROI on legacy code.

**Remaining actionable**: UP031 printf→f-string (65) · N naming (58) · DJ
conventions DJ012/007/006/008 (~49) · PLR2004 magic-value (20) ·
E501/E402/E741 (31). **DJ001** (null on a string field, 14) needs a **migration**
on the legacy DB — handle carefully/separately.

> The numbered breakdown below is the original migration plan; items in §1–§2
> and the mechanical parts are now done per the summary above.

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

Current state: **391 tests** (the place-fiches work added ~99 to the previous 292).
Coverage was last measured at 57% before that work — re-run `make dev/tests/local/html` to
refresh. Original baseline was 34 tests / 42%.

### Backend

#### 0. Dead / broken code cleanup — DONE ✅

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

- [ ] Shared fixtures in `conftest.py` for common lookup rows
      (`DocumentType`, `DocumentLanguage "Français"`) — `test_document_models.py`
      already duplicates these; extract to conftest when a third consumer appears
- [ ] Model factories (factory_boy or thin helpers) for `Biblio`, `Person`,
      `Transcription`, `ObjectCollection`
- [ ] Add a coverage gate (`--cov-fail-under`) once the baseline stabilises;
      wire into CI
- [ ] Scaffold `tests/frontend/` placeholder for the JS suite

#### 2. Pure functions & template tags — DONE ✅

- [x] `fiches/templatetags/fiches_extras.py` (38% → **85%**): all pure filters +
      template tag parsers; `docfileinfo` / `BiblioRefNode` deferred (URL
      resolver + template file needed)
- [x] `fiches/utils.py` (21% → **92%**): `supprime_accent`, `query_fiche` (all
      prefix variants), `user_can_change/delete_documentfile`, `log_model_activity`,
      `get_last_model_activity`, `get_default_publisher_user`
- [x] `pagination/templatetags/pagination_tags.py` (40% → **55%**): page-window
      logic, F507 regression; inline-autopaginate branch still open
- [x] `fiches/templatetags/{collector,paginator}.py` (38% → **92%**, 22% → **100%**)
- [x] `utils/fields.py` `DictField` (31% → **83%**): pickle round-trip, edge cases

#### 3. Forms validation (core business rules)

- [ ] `BiblioForm`: required fields, `litterature_type`, language default,
      subject-person permissions (extend existing)
- [ ] `ManuscriptForm`, `TranscriptionForm` (extend defaults),
      `ContributionDocForm` / `ContributionDocSecForm`
- [ ] `ObjectCollectionForm`, `ProjectForm`
- [ ] `FichesSearchForm`: query construction

#### 4. Model methods & managers — mostly done

- [x] `models/person/person.py` (29% → **89%**): managers, name helpers,
      `get_biography`, `get_valid_biography`, `renum_bio`, `format_for_ajax_search`,
      `get_relations`/`get_reverse_relations` empty paths
- [x] `models/documents/document.py` (82% → **92%**): `__str__` helpers,
      `getDocumentTypes`, `updateFirstAuthor`, `Transcription` managers/methods.
      **Bugs found:** `Manuscript.getFirstAuthorName()` uses wrong related name
      (`contributionman_set` vs `contribution_mans_documents`);
      `Manuscript.get_absolute_url()` passes `pk=` kwarg but URL pattern expects
      `man_id` — both documented as regression tests.
- [x] `models/misc/object_collection.py` (51% → **86%**): slug, M2M helpers,
      `ACModel.user_access` (38% → **92%**)
- [x] `models/misc/project.py` (52% → **100%**): `is_editable`, M2M helpers,
      `get_transcriptions`
- [x] `logging/activity_log.py` (40% → **83%**): `ObjectActivities.activities()`,
      `object_info`, `get_object`, `__str__`; `sanitize()` skipped (raw MySQL SQL)
- [x] `models/person/biography.py` (68% → **89%**): `Nationality`/`Religion`
      `__str__`, `person_name` variants, `relations`/`reverse_relations`,
      `Profession`/`SocietyMembership` date formatting
- [x] `fiches/widgets.py` (69% → **98%**): `PersonWidget`, `StaticList`,
      `DynamicList` — all render paths
- [ ] `models/documents/document_file.py` (**54%**, 16 stmts) — open
- [ ] `models/search/search.py` (**83%**) — managed=False view models, minor gaps
- [ ] `models/person/relation.py` (**78%**) — minor gaps

#### 5. Views — smoke first, then behavior (largest absolute gap)

- [ ] Permission/auth gating + status codes for: `search` (11%),
      `collections` (14%), `projects` (12%), `biography` (12%),
      `bibliography` (30%), `transcription` (38%), `publications` (44%),
      `news` (38%)
- [ ] Key behaviors: search results, create/edit flows, access control
      (public / private / group-restricted)
- [ ] Error views: extend (`server_error` done) with 403/404

#### 6. Search indexes (Haystack)

- [ ] `fiches/search_indexes.py` (**37%**, 82 stmts missing): unit-test
      `prepare()` / `prepare_*` against model instances (no Solr needed);
      check index text templates render

#### 7. Management commands

- [ ] `sync_status_roles` (**74%**): edge cases, idempotence, `--apply` vs dry-run
