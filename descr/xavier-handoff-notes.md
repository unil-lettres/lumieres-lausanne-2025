# Xavier Handoff Notes

Recorded: 2026-05-27

Current staging integration status as of 2026-07-09 is summarized in
`descr/project-state-2026-07-09.md`. In short, `origin/staging/named_entities`
is the branch deployed to `https://plt-tst-2.unil.ch/` for validation; it
contains Xavier's `feat/named_entities` plus the latest production hotfix
`v2026.07.03`. Do not deploy `feat/named_entities` directly.

## Branch / GitHub Workflow Push Issue
- Xavier created a feature branch for named entities work (`feat/named-entities` / `feat/named_entities` naming to verify locally).
- His push was rejected by GitHub with:
  - `refusing to allow an OAuth App to create or update workflow .github/workflows/docker-prod.yml without workflow scope`
- Interpretation:
  - GitHub rejects pushes whose new commits create or modify `.github/workflows/docker-prod.yml` unless the OAuth token has the `workflow` scope.
  - Xavier says he did not intentionally modify that file.
  - Likely causes include a branch created from a stale/wrong local base, inherited local commits, or an accidental workflow-file change included by tooling.
- Suggested diagnosis:
  ```bash
  git fetch origin
  git switch feat/named_entities
  git log --oneline --name-status origin/dev..HEAD -- .github/workflows/docker-prod.yml
  git diff --name-status origin/dev...HEAD
  ```
- Preferred resolution:
  - For named-entities work, do not include any change to `.github/workflows/docker-prod.yml`.
  - Recreate/clean the branch from `origin/dev` and keep only application/test/doc changes relevant to the feature.
  - Only reauthorize a token with `workflow` scope if modifying GitHub Actions is actually required.

## Test Layout Discussion
- Xavier objected that tests are currently under `app/fiches/tests/`, inside the `app` tree.
- Clarification:
  - This is a common Django layout and was the existing repository convention.
  - It is not ideal if the project wants a pytest-first architecture with a global `conftest.py`.
- Current inconsistency observed:
  - `pyproject.toml` configures `pytest` with `testpaths = ["tests"]`.
  - Existing tests are mostly under `app/fiches/tests/`.
  - The Makefile path uses the Django runner (`python app/manage.py test`).
- Xavier reports that he has already migrated tests toward a separate root-level tests folder and increased the count from 36 to 51 tests.
- Agreed direction:
  - A root `tests/` layout is acceptable if it makes pytest configuration and shared fixtures cleaner.
  - Existing tests can be moved/renamed as long as the behavior they cover remains covered.

## Specific Test: `test_dead_code_removal.py`
- Xavier questioned `app/fiches/tests/test_dead_code_removal.py`, asking whether it tests dead code or is itself dead test code.
- Finding:
  - It is not related to the recent Beatrice/admin-permission fixes.
  - It came from the facsimile viewer work.
  - It checks that removed viewer controls (`rotate`, `brightness`, `contrast`, related dropdown utilities and CSS classes) do not reappear, while essential viewer controls remain.
- Assessment:
  - The intent is a regression test, not literally a test for dead code.
  - The filename is confusing.
- Better names:
  - `test_facsimile_viewer_controls.py`
  - `test_viewer_controls_regressions.py`
- Do not delete without checking whether another test covers the same regression.

## Clean Code / Headers
- Xavier plans to do clean code because he noticed several odd elements.
- He also wants to clean/harmonize file headers because the repository contains mixed styles.
- This is acceptable, but should be reviewed with clear commit boundaries.
- Recommended commit split:
  1. Test architecture migration.
  2. Test cleanup/deduplication.
  3. Header harmonization.
  4. Mechanical clean code / refactor without behavior changes.
  5. Functional named-entities development.
- Review guardrail:
  - Avoid a single huge commit mixing headers, tests, refactors, bug fixes, and new features.
  - Keep mechanical changes separate from behavior changes so review can focus on risk.

## Repository Privacy Note
- Quote/pricing documents must not be committed to GitHub.
- `descr/devis/` is intentionally ignored in `.gitignore`.

## Local Worktree Separation

As of 2026-06-09, local Lumières work is split across two intentionally
separate worktrees:

1. Current `dev` worktree:
   - path: `/Users/jganivet/Développement/lumieres-lausanne-newfeats`;
   - branch: `dev`;
   - purpose: normal Lumières work, documentation, deployment notes and current
     development context;
   - local Docker use should follow the repository's standard dev workflow.

2. Xavier clean-repo test worktree:
   - path: `/Users/jganivet/Développement/lumieres-xavier-clean-repo`;
   - branch/commit: `origin/chore/clean-repo`, checked out detached at the
     tested commit;
   - purpose: isolated validation of Xavier's reorganization branch;
   - Docker Compose project name: `lumieres-xavier`;
   - app URL: `http://127.0.0.1:8010/`;
   - phpMyAdmin URL: `http://127.0.0.1:8011/`;
   - override file: `/private/tmp/lumieres-xavier-compose.override.yml`;
   - database volume: `lumieres-xavier_db_data`;
   - Solr volume: `lumieres-xavier_solr_data`;
   - media mount: local production backup media mounted read-only from
     `/Users/jganivet/Développement/Backups/lumieres.unil.ch/lumieres-prod-media`.

Keep these two contexts distinct. Do not run Xavier branch migrations or
database restore commands from the main `dev` worktree. Conversely, do not use
the Xavier worktree as the place for normal `dev` documentation edits.

Useful orientation commands:

```bash
git worktree list
pwd
git status --short --branch
```

To inspect the Xavier stack from the Xavier worktree:

```bash
cd /Users/jganivet/Développement/lumieres-xavier-clean-repo
docker compose -p lumieres-xavier \
  -f docker-compose.yml \
  -f docker/docker-compose.dev.yml \
  -f /private/tmp/lumieres-xavier-compose.override.yml \
  ps
```

To run checks in Xavier's isolated app container:

```bash
cd /Users/jganivet/Développement/lumieres-xavier-clean-repo
docker compose -p lumieres-xavier \
  -f docker-compose.yml \
  -f docker/docker-compose.dev.yml \
  -f /private/tmp/lumieres-xavier-compose.override.yml \
  exec -T -w /app app /opt/venv/bin/pytest
```

Xavier's branch currently uses `pytest` as the canonical test runner via
`pyproject.toml`; `python app/manage.py test` should not be assumed equivalent
unless this is explicitly restored and documented.

## `feat/named_entities` Review Notes - Section 3 Fiches Lieux

Recorded: 2026-06-12
Basis document: `descr/2026-05-05 LL_dev_entites-nommees.docx`
Test target: isolated Xavier stack only

Tested branch:

- worktree: `/Users/jganivet/Développement/lumieres-xavier-clean-repo`;
- branch/commit: `origin/feat/named_entities` at `1dd8cff`;
- app URL: `http://127.0.0.1:8010/`;
- admin URL: `http://127.0.0.1:8010/fiches_admin/`.

Automated checks run in the Xavier stack:

- targeted place tests: `67 passed`;
- full backend suite: `382 passed`;
- `python manage.py check`: OK;
- `python manage.py makemigrations --check --dry-run`: no changes detected.

Findings to notify Xavier:

1. `Note de lieu` is not manually usable in the admin UI.
   - Manual test: open `Fiches lieux`, create/edit a place, expand
     `Notes de lieu`, add a note row.
   - Problem: the CKEditor area appears, but the cursor does not appear and the
     user cannot type into the note field.
   - Browser diagnosis: after adding a new note inline, the form contains the
     hidden `textarea[name="notes-0-text"]`, but no editable CKEditor iframe or
     div is initialized for `id_notes-0-text`; the only CKEditor instance found
     is the inline prototype `id_notes-__prefix__-text`.
   - Requirement impact: section 3.2 explicitly requires `Note (texte libre),
     avec accès`.
   - Backend caveat: the formset can be posted programmatically and tests can
     save note data, but manual data entry is blocked.

2. Category seed list does not match the May 5 requirements document.
   - Required by document: `pays`, `canton/département`, `région`,
     `ville/village`, `domaine`, `maison de campagne`, `quartier`.
   - Current seed values: `Pays`, `Canton`, `Département`, `Région`, `Ville`,
     `Village`, `Bailliage`, `Quartier`, `Lieu-dit`.
   - Missing: `Domaine`, `Maison de campagne`.
   - Extra relative to document: `Bailliage`, `Lieu-dit`.
   - Decision needed: either align seed data to the document or confirm that
     Xavier's expanded category vocabulary is intentionally accepted.

3. Public listing headings do not match the May 5 requirements wording.
   - Required: `Lieu d'impression`; actual:
     `Publications imprimées dans ce lieu`.
   - Required: `Lieu de rédaction`; actual:
     `Manuscrits rédigés dans ce lieu`.
   - Required: `Publications - Lieu mentionné`; actual:
     `Publications mentionnant ce lieu`.
   - Required: `Manuscrits - Lieu mentionné`; actual:
     `Transcriptions liées à ce lieu`.
   - Required `Personnes` is functionally present, but actual heading is
     `Personnes liées à ce lieu`.

4. Template comment is rendered on the public place page.
   - Manual test URL: `http://127.0.0.1:8010/fiches/lieu/13/`.
   - The page renders this literal Django-template comment before the
     manuscripts section:
     `{# 3.4.2 §2 — manuscripts written at this place. NB: Manuscript.get_absolute_url ... #}`
   - This should be hidden from public output. Use a real template comment that
     Django consumes, or move the note to a Python/code comment outside the
     rendered HTML.

5. `Note de lieu` access is not enforced on the public place page.
   - Test URL: `http://127.0.0.1:8010/fiches/lieu/14/`.
   - A non-public note (`access_public=False`) attached to the place is rendered
     for an anonymous public request.
   - Code symptom: the template iterates over `place.notes.all` directly,
     without filtering notes through the access rules used by other note types.
   - Requirement impact: section 3.2 requires notes "avec accès"; private or
     group-restricted notes should not leak on a public place fiche.

6. Migration rehearsal revealed a local DB schema inconsistency.
   - In the isolated Xavier DB, `contenttypes.0002_remove_content_type_name`
     was marked applied while `django_content_type.name NOT NULL` still existed.
   - First `migrate fiches` applied `0006-0008` but crashed during
     `post_migrate` when Django tried to create content types for the new
     models.
   - Local-only fix applied to Xavier DB:
     `ALTER TABLE django_content_type DROP COLUMN name;`
   - Before staging/prod migration, verify whether the same inconsistency
     exists; otherwise Xavier's place migrations can fail after DDL has already
     run.

7. Existing admin JavaScript noise remains.
   - Browser console reports `django is not defined` from
     `/static/js/fiches_admin.js:26`, already on the admin login page.
   - This is not specific to `PlaceRecord`, and did not block place CRUD, but it
     should be tracked separately.

Confirmed working in manual/browser checks:

- create a fiche lieu in the admin;
- required `Nom` and `Catégorie` fields;
- variants;
- related places;
- multiple reference sites entered manually in the admin on a single place
  fiche: GeoNames, Wikidata and DHS;
- reference URL generated from identifier, for example GeoNames `2659811`;
- generated reference URLs persist after save and render as public links;
- duplicate use of the same reference site on one place is rejected by the admin
  form;
- manual reference URL entry is preserved and takes precedence over URL
  generation from the identifier;
- public place page at `/fiches/lieu/<id>/`;
- duplicate `name + category` rejected;
- same place name allowed with a different category;
- linked biography/publication/manuscript/transcription lists render;
- public lists paginate at 20 records on all five sections (`bio_page`,
  `trans_page`, `print_page`, `redac_page`, `mention_page`);
- list ordering is coherent with the implemented model methods on the generated
  local fixtures;
- secondary literature is excluded from the "printed here" section.

Local manual-test data added on 2026-06-12 to Xavier DB:

- Place `13`: `Test manuel Lausanne`;
- linked biography: `Manuel, Test (Lausanne, 1743 – Berne, 1805)`;
- linked transcription: `Test manuel transcription liee`
  (`/fiches/trans/1622/`, now associated with bibliography `12851`);
- linked printed publication: `Test manuel publication imprimee`;
- linked written manuscript: `Test manuel manuscrit redige`;
- linked mentioned publication: `Test manuel publication mention`.

Additional section 3 pagination/access fixture added on 2026-06-12:

- Place `14`: `Codex Section 3 Pagination Test`;
- 22 linked biographies;
- 22 linked transcriptions;
- 22 linked primary printed publications;
- 22 linked secondary printed publications, used to verify exclusion;
- 22 linked written manuscripts;
- 22 linked mentioned publications;
- one public note and one non-public note, used to verify note visibility.

Additional reference-site fixtures created through the admin UI:

- Place `19`: `Codex Multi Ref ...`, with GeoNames, Wikidata and DHS entered
  manually through inline rows, saved, reopened and verified on the public page.
- Place `20`: `Codex Manual Ref URL ...`, used to verify that a manually entered
  reference URL remains authoritative even when an identifier is also present.

Fixture caveat:

- The first synthetic transcription fixture was created with a legacy
  `manuscript` relation but without `manuscript_b`, which made
  `/fiches/trans/1622/` fail with `NoReverseMatch` on the toolbar link to
  `display-bibliography`.
- This was corrected locally by attaching the transcription to bibliography
  `12851`; the transcription page now returns HTTP 200.
- Treat that specific `NoReverseMatch` as a local fixture problem unless it can
  be reproduced with a real transcription created through the normal UI.

## `feat/named_entities` Retest - 2026-06-26

Test target: isolated Xavier stack only.

Worktree and stack:

- worktree: `/Users/jganivet/Développement/lumieres-xavier-clean-repo`;
- branch/commit: `origin/feat/named_entities` at `4d5bb88`;
- Compose project: `lumieres-xavier`;
- app URL: `http://127.0.0.1:8010/`;
- phpMyAdmin URL: `http://127.0.0.1:8011/`;
- DB volume preserved: `lumieres-xavier_db_data`;
- Solr volume recreated: `lumieres-xavier_solr_data`, because the previous
  generated Solr index used a newer Lucene format than the local `solr:8` image
  could read.

Temporary local override restored at:

`/private/tmp/lumieres-xavier-compose.override.yml`

Local override notes:

- app port limited to `8010`;
- phpMyAdmin port limited to `8011`;
- production media backup mounted read-only from
  `/Users/jganivet/Développement/Backups/lumieres.unil.ch/lumieres-prod-media`;
- Solr command adjusted locally to set
  `PATH=/opt/solr/bin:/opt/docker-solr/scripts:$PATH` before running
  `precreate-core` and `solr-fg`, because the image scripts were not on PATH
  under the Compose `bash -lc` command.

Setup checks:

- `git fetch origin feat/named_entities` showed Xavier force-updated the branch
  from `1dd8cff` to `4d5bb88`;
- isolated worktree switched to detached `origin/feat/named_entities`;
- local `AGENTS.md` stack-separation note remains as the only modified file in
  Xavier's worktree;
- `docker compose ... up -d --build` rebuilt the Xavier app image;
- `python manage.py check`: OK;
- migrations `fiches.0006` through `0012` applied successfully after cleaning
  stale old section-3 tables left by the previous version of Xavier's branch;
- backend tests: `393 passed, 3 warnings`;
- `python manage.py update_index`: completed for existing data, with `0 Fiches
  lieux` before creating a fresh place fixture;
- home page `http://127.0.0.1:8010/`: HTTP 200;
- admin `http://127.0.0.1:8010/fiches_admin/`: HTTP 302 to login;
- search `http://127.0.0.1:8010/chercher/?q=Lausanne`: HTTP 200.

New finding to notify Xavier:

1. Place Solr indexing fails because the Solr schema does not define
   `place_name`.
   - Created local fixture `PlaceRecord` id `1`: `Codex Search Lausanne`, with
     variant `Codex Losanna` and GeoNames reference `2659811`.
   - Public page works:
     `http://127.0.0.1:8010/fiches/lieu/1/` returns HTTP 200 and displays
     `GeoNames : https://www.geonames.org/2659811`.
   - `PlaceRecordIndex` defines extra fields:
     `place_name = indexes.CharField(model_attr="name")` and
     `category = indexes.CharField(model_attr="category__name")`.
   - The place text template includes the expected three reference forms:
     identifier alone, reference-site name plus identifier, and `ref.url`.
   - But saving/indexing a place fails with Solr HTTP 400:
     `ERROR: [doc=fiches.placerecord.1] unknown field 'place_name'`.
   - Reproduction:
     `python manage.py update_index fiches.PlaceRecord`.
   - User-visible consequence:
     global search `http://127.0.0.1:8010/chercher/?q=2659811` returns no
     result for the created place.
  - Likely fix:
     update the Solr configset/schema for the new `PlaceRecordIndex` fields, or
     remove/store those dedicated fields if only the document `text` field is
     required for global search.

## feat/named_entities Issue Review - 2026-06-26

Target stack/worktree:

- Xavier isolated worktree:
  `/Users/jganivet/Développement/lumieres-xavier-clean-repo`.
- Branch tested:
  detached `origin/feat/named_entities` at `4d5bb88`.
- Isolated stack:
  `lumieres-xavier`, app on `http://127.0.0.1:8010/`.

GitHub status:

- Issue `#108` closed on 2026-06-26 after manual CKEditor note-entry
  validation.
- Issue `#109` closed on 2026-06-26 after anonymous public/private note
  visibility validation.
- Issue `#110` closed on 2026-06-26 after public rendered-output validation.
- Issue `#111` closed on 2026-06-26 for the resolved category-alignment scope.
- Follow-up issue `#117` opened for the remaining missing public linked-record
  sections on Fiche lieu.

Local review against current branch:

- `#108` - requirement `3.2`, note de lieu CKEditor:
  fixed in manual browser testing. Julien could add a note containing `salut`
  from `http://127.0.0.1:8010/fiches/lieu/edit/2/`, and the note was confirmed
  persisted in the isolated Xavier database.
- `#109` - requirement `3.2`, access-controlled note display:
  fixed in current code. The public view passes `visible_notes` filtered through
  `note.user_access(user)`, and an anonymous HTTP test rendered the public test
  note while hiding the private test note.
- `#110` - requirement `3.4.2`, leaked template comment:
  fixed in current public template. The previous raw `{# 3.4.2 ... #}` text is
  no longer present in rendered output.
- `#111` - requirements `3.2`, `3.4.1`, `3.4.2`, categories and public labels:
  closed for the category-alignment scope. The seeded categories now match the
  requested set:
  `Pays`, `Canton/Département`, `Région`, `Ville/Village`, `Domaine`,
- `Maison de campagne`, `Quartier`.
- `#117` - requirements `3.4.1`, `3.4.2`, missing public linked-record
  sections:
  opened as a separate follow-up because the public linked-record sections are
  no longer implemented in `display/place.html`; the template now states that
  automatic listings are added later.
- `#118` - section 3, place administration/listing:
  opened because `PlaceRecord` / Fiche lieu records are not visible in
  `fiches_admin/fiches/`, and there is no obvious way to browse or inspect all
  existing places without knowing their ids.

New blocker found during this retest:

- Place indexing still fails against Solr because the current Solr schema does
  not know the new `place_name` field declared by `PlaceRecordIndex`.
  Reproduction in the isolated stack:
  `python manage.py update_index fiches.PlaceRecord`.

Scope clarification on 2026-06-26:

- External references such as GeoNames/Wikidata/DHS are out of scope for global
  search in this phase. They must be enterable, saved, displayed and clickable
  on the public place fiche, but they do not need to be searchable by identifier,
  label plus identifier, or full permalink.
- The Solr `unknown field 'place_name'` error remains technically relevant only
  if Xavier keeps place indexing active. It should be fixed or the unused place
  index should be disabled, but it is no longer a functional blocker for
  external-reference search.

Scope clarification on 2026-06-30:

- `Nature du document` is back in scope for the named-entities requirements.
  Treat Xavier's implementation of an admin-managed `DocumentNature` lookup and
  manuscript-only `Biblio.document_nature` dropdown, displayed near
  `Type d'écrit`, as an expected requirement rather than obsolete work.
- Validation should check that the field is available only for manuscript
  bibliographic records, persists on save, is manageable from the admin, and is
  displayed on the read view without affecting non-manuscript bibliography
  forms.
- Requirement section 5, `Recherche avancée`, is also in scope. The expected
  behavior is a new `Liste des lieux` tab after `Liste des personnes`, with the
  same alphabetical-list behavior as the person list and links to the public
  fiche lieu pages.

## `feat/named_entities` Section 1 Retest Setup - 2026-06-26

Target stack/worktree:

- Xavier isolated worktree:
  `/Users/jganivet/Développement/lumieres-xavier-clean-repo`.
- Branch tested:
  detached `origin/feat/named_entities` at `cbb360c`.
- Isolated stack:
  `lumieres-xavier`, app on `http://127.0.0.1:8010/`.

Update performed:

- Fetched `origin/feat/named_entities`.
- Moved the isolated worktree from `4d5bb88` to `cbb360c`.
- Preserved the local `AGENTS.md` worktree guidance change.
- Rebuilt and restarted only the isolated Docker stack `lumieres-xavier`.

Automated checks:

- `python manage.py check`: OK.
- `python manage.py showmigrations fiches`: migrations `0001` through `0012`
  applied.
- `pytest tests/backend/test_tagging_views.py -q`: `8 passed`.
- HTTP smoke:
  `http://127.0.0.1:8010/` returned `200`;
  `http://127.0.0.1:8010/fiches/tagging/place/categories/` returned `200`.

Section 1 implementation observed:

- CKEditor transcription toolbar now includes `TagPerson` / `TagPlace`.
- The named-entity plugin lives in
  `app/ckeditor/static/ckeditor/ckeditor/plugins/nametag/plugin.js`.
- The plugin wraps selections in links to `/fiches/bio/<id>/` or
  `/fiches/lieu/<id>/`.
- For existing editorial `sic`/`corr` corrections, the plugin tries to wrap the
  whole correction unit so both diplomatic and edited renderings remain
  clickable, while removing the correction tooltip title to avoid tooltip
  overlap.
- Inline creation endpoints are available for users with the relevant add
  permissions:
  `/fiches/tagging/person/create/`,
  `/fiches/tagging/place/create/`,
  `/fiches/tagging/place/categories/`.

Manual section 1 checks still needed:

- In a transcription edit page, verify that `Pers` and `Lieu` buttons are
  visible in CKEditor: confirmed by Julien on
  `http://127.0.0.1:8010/fiches/trans/edit/1622/`.
- Select plain text and tag an existing person; save and verify display in
  edited/diplomatic modes.
- Select plain text and tag an existing place; save and verify display in
  edited/diplomatic modes.
- Verify person labels in search results display dates as requested, e.g.
  `Nom, Prénom (1698-1756)`.
- Verify place labels display category, e.g. `Fribourg (canton)` or current
  category casing.
- For a director/admin account, verify inline creation of a missing person and
  place from the tagging dialog.
- For a non-admin/non-director account, verify inline creation is unavailable
  and rejected server-side.
- Test an editorial correction case such as `Greg.` / `Grégoire`: tagging must
  preserve diplomatic and edited information, avoid destructive cleanup, and not
  show conflicting stacked tooltips. Confirmed by Julien on a transcription
  containing `saconay` / `Sacconay`: after tagging, the source became an
  outer person link to `/fiches/bio/744/` wrapping
  `<span class="sic" data-corr="Sacconay">saconay</span>`. The correction data
  was preserved and the old correction `title` was removed, matching the agreed
  non-destructive behavior. Removing the person tag afterwards also preserved
  the editorial span and `data-corr`, leaving
  `<span class="sic" data-corr="Sacconay">saconay</span>`.
- Display validation confirmed by Julien on
  `http://127.0.0.1:8010/fiches/trans/270/`: the bio link works in both
  diplomatic and edited views.
- Issue `#119` opened: creating/selecting a missing person from the `Pers`
  popup can create a bare `Person` without `Biography`, then insert a link to a
  non-existent bio page. Examples from isolated DB:
  `/fiches/bio/4384/` (`lettres`) and `/fiches/bio/4385/` (`change`) both return
  404 because no associated `Biography` exists.
- Retest after Xavier commits `612b11f` and `26bc4ed`: isolated worktree moved
  to `26bc4ed`, app rebuilt, `pytest tests/backend/test_tagging_views.py -q`
  now reports `10 passed`, and `manage.py check` is OK. The URLs
  `/fiches/bio/4384/` and `/fiches/bio/4385/` still return HTTP 404, but now
  render a dedicated page `Fiche biographique non rédigée` with the person name
  and a `Créer la fiche biographique` link instead of Django's generic 404.
  Issue `#119` remains open until this expected state returns HTTP 200 when the
  `Person` exists; HTTP 404 should remain reserved for a missing `Person`.
- Retest after Xavier commits `c342143`, `95a9fc1`, and `5cc2fae`: isolated
  worktree moved to `5cc2fae`, app rebuilt, migrations `0013` and `0014`
  applied on the isolated DB, `manage.py check` is OK, and
  `pytest tests/backend/test_tagging_views.py -q` reports `10 passed`. The URLs
  `/fiches/bio/4384/`, `/fiches/bio/4385/`, and `/fiches/bio/4386/` now return
  HTTP 200 and render `Fiche biographique non rédigée`. This satisfies the
  remaining condition for issue `#119`.
- Retest after `612b11f`: adding then removing a tag around the `saconay` /
  `Sacconay` editorial correction restores the original correction tooltip:
  `<span class="sic" data-corr="Sacconay" title="Sacconay">saconay</span>`.
  This confirms the non-destructive remove behavior for the sensitive
  diplomatic/editorial metadata case.
- Manual checks 1-4 from the section 1 retest list were confirmed by Julien:
  existing-person plain-text tagging works, place tagging/display works in both
  views, person tooltip/label behavior is good, and place search labels include
  the category.
- Issue `#121` opened: clicking a tagging tool without selecting text inserts
  the selected fiche label into the transcription at the cursor/first-character
  position. The requirement describes tagging an existing selected word/passage,
  so no-selection should be blocked with a user message rather than modifying
  transcription content.
- Issue `#122` opened: editing an existing person/place tag can leave an
  incoherent link. In the `somme` test, the edited person tag had
  `data-person="744"` and `title="Sacconay, Frédéric de (1714-1788)"`, but kept
  `href="/fiches/bio/4386/"` from the previous person instead of switching to
  `/fiches/bio/744/`. The same issue was confirmed for a place tag: editing
  `Paris` to `Codex Access Note Test` updated `data-place="2"` and the title,
  but kept `href="/fiches/lieu/1/"` instead of `/fiches/lieu/2/`.
- Xavier pushed a candidate fix for issue `#122` on 2026-06-29:
  `8decaa5 fix(ckeditor): keep href in sync when editing a tag
  (data-cke-saved-href)`. The isolated worktree was updated to `8decaa5`, the
  stack rebuilt, no migrations were pending, `manage.py check` passed, and
  `pytest tests/backend/test_tagging_views.py tests/backend/test_admin_place_record.py -q`
  reported `15 passed`. Manual browser retest of the stale-`href` behavior is
  now completed: changing an existing `Pers` tag from Sacconay `744` to Vincent
  Barras `1051` updated `data-person`, `href`, and `title` coherently; changing
  an existing `Lieu` tag from Paris `4` to Codex Search Lausanne `1` updated
  `data-place`, `href`, and `title` coherently. Issue `#122` was closed on
  2026-06-29.
- The same update also includes `428f338 feat(fiches): register PlaceRecord in
  the admin (browse/search fiches lieux)`. Manual admin review on 2026-06-29
  confirmed that `Fiches lieux` now appears in the Django admin, an existing
  place such as `Nice` opens in edit mode, the main fields are present (`Nom`,
  `Catégorie`, `Lieux associés`), and the `Variantes de lieu` and `Sites de
  référence du lieu` inlines are visible. The admin behavior looks functional.
  Remaining note: the access metadata block (`Public`, `Propriétaire`,
  `Groupes d'accès`) appears at the top of the form; ergonomically it may be
  preferable to move it below the business fields and inlines.
- Issue `#123` opened for discussion: when a selection crosses an existing tag,
  the tagging operation can apply only partially. Test case: `saconay` was
  already tagged, then selecting `cher saconay vos deux` and applying `Pers`
  produced tags around `cher ` and `saconay`, but left `vos deux` outside the
  operation. This should be clarified as either fully supported or refused with
  a clear message.
- Xavier pushed a candidate fix for issue `#123` on 2026-06-29:
  `f968fd0 feat(ckeditor): rebind a tag to the selection, absorbing overlaps
  (#123)`. The isolated worktree was updated to `f968fd0`, the stack rebuilt,
  no migrations were pending, `manage.py check` passed, and
  `pytest tests/backend/test_tagging_views.py tests/backend/test_admin_place_record.py -q`
  reported `15 passed`. Manual browser retest confirmed the `Pers` overlap
  absorption case: starting from `saconay` tagged as person, selecting
  `mon cher saconay vos deux lettres` and applying `Pers` produced one coherent
  outer person tag without nested `ll-tag-person`; removing the person link then
  restored plain text while preserving the editorial
  `<span class="sic" data-corr="Sacconay" title="Sacconay">saconay</span>`.
  Manual browser retest also confirmed the `Lieu` overlap absorption case:
  starting from `Nice` tagged as place, selecting `cet argent à Nice` and
  applying `Lieu` produced one coherent outer place tag without nested
  `ll-tag-place`; removing the place link restored plain text. Issue `#123` was
  closed on 2026-06-29.
- Plain-text person tagging and removal were confirmed working by Julien.
- Plain-text place tagging was confirmed working by Julien. Initial concern
  about missing `Retirer le lien` was a false positive: the button appears only
  when an existing tag/link is selected. Issue `#120` was closed on 2026-06-26.
- Inline place creation from the `Lieu` tagging popup was confirmed working by
  Julien.
- Save/reopen/display persistence for section 1 tagging was confirmed by Julien
  on `http://127.0.0.1:8010/fiches/trans/270/`.
- Permission UI/server check completed with local user `codex_editor_no_create`:
  the user can open `trans/edit/270/` with transcription edit permissions but
  lacks `add_person` and `add_placerecord`; rendered `window.LL_NAMETAG` exposes
  `person: false` and `place: false`, and direct POSTs to
  `/fiches/tagging/person/create/` and `/fiches/tagging/place/create/` both
  return `403 {"success": false, "error": "forbidden"}`.
- Additional manual section 1 tests on `http://127.0.0.1:8010/fiches/trans/edit/270/`
  were completed by Julien on 2026-06-26:
  - simple multi-word `Pers` tagging works technically; test case `j'ay reçu`
    produced a coherent link to `/fiches/bio/744/`;
  - selection crossing an existing tag is not broken HTML but applies only
    partially; tracked separately in issue `#123`;
  - multi-line `Pers` tagging across a `<br />` works and removal preserves the
    line break and text;
  - multi-line `Lieu` tagging across a `<br />` works and removal preserves the
    line break and text;
  - after these tests, display/persistence looked good to Julien. Testing was
    paused here and should resume later from the remaining section 1 edge cases
    and open issues.

## Weekly Report Received 2026-06-02

Source: weekly report about Xavier's work during the week ending 2026-05-31,
branch reported as `chore/clean-repo`, 65+ commits.

Reported changes:

- Lint/code quality:
  - migration from black/isort/flake8/mypy toward Ruff + ty;
  - 887+ findings reportedly resolved, including `F821` NameError,
    wildcard imports, bare `except`, bugbear findings, simplify/comprehension
    cleanups;
  - dead code removed across 16 files.
- Infrastructure:
  - Python 3.13 adoption;
  - uv adoption with `pyproject.toml`, `uv.lock`, `.python-version`;
  - multi-stage Dockerfile refactor;
  - Docker Compose dev override with watch support.
- Tests:
  - 12 test modules moved from `app/fiches/tests/` to `tests/backend/`;
  - SQLite test DB settings added in `settings_test.py`;
  - pytest foundation added;
  - Place model tests added in `test_place_record.py`.
- Database:
  - migration `0005` converts MyISAM tables to InnoDB;
  - migration `0006` seeds `PlaceCategory` lookups;
  - migration history reportedly restored with `0001_initial`.
- Copyright:
  - AGPL/SIER headers normalized across 120+ files;
  - obsolete UTF-8 coding declarations removed.
- Cleanup:
  - removed broken `sync_perms` command;
  - removed pagination middleware / `paginator.py`;
  - removed unused COinS cluster;
  - removed unwired context processor;
  - removed `fiches/dev` script.

Review implications:

- Treat this as a broad repository cleanup, not a narrow feature branch.
- Require a clean branch comparison against `origin/dev` before accepting the
  work, with special attention to migrations, Docker files, workflow files,
  test discovery and removed commands.
- Python 3.13 is a significant runtime change. Validate compatibility with
  Django, dependencies, Docker images and staging/prod deployment expectations
  before adopting it.
- The removal of `sync_perms` is risky because role/permission changes are
  documented in `descr/roles.md` and have been relevant in production. Confirm
  the replacement path before accepting that deletion.
- The MyISAM to InnoDB migration must be reviewed as an operational database
  migration, including staging rehearsal, backup/rollback strategy and lock
  impact.
- The restored migration history must be checked carefully against the current
  production database state to avoid fake/duplicate initial migrations.
- Test relocation is acceptable only if CI and local commands still discover all
  existing regression tests.
- Header normalization and mechanical lint cleanup should remain separate from
  behavior changes in commit history.
