# Xavier regression test plan

Status: draft test checklist for reviewing Xavier's work
Date: 2026-05-29

## Scope

This document lists regression checks to apply before merging Xavier's current
work. It is based on:

- local commit history since the Django 5 cutover;
- deployment/runbook incident notes in `descr/`;
- existing automated tests under `app/fiches/tests/`;
- GitHub PR #99 review comments and issue references;
- Gmail/GitHub notification search results for Lumières regression fixes;
- UNIL mailbox excerpts provided by Julien on 2026-05-29;
- historical debugging spreadsheets:
  - `/Users/jganivet/Desktop/debug lumieres historique/Debuggage LL Python Django 5.2 08.2025.xlsx`
  - `/Users/jganivet/Desktop/debug lumieres historique/Debuggage LL Python Django 5.2 v3.xlsx`
- weekly report received on 2026-06-02 for Xavier's `chore/clean-repo` branch.

Not scanned by default:

- `descr/private/`;
- quote/pricing files under `descr/devis/`.

## Baseline Commands

Run these before functional review:

```bash
python app/manage.py check
python app/manage.py test fiches
pytest app/fiches/tests
```

If Xavier moved tests to a root `tests/` directory, verify that:

```bash
pytest
python app/manage.py test
```

both discover the expected regression coverage, or document which runner is now
canonical.

If Xavier's uv/pytest setup is adopted, also verify the branch-specific command
set documented by Xavier, including the equivalent of:

```bash
uv run pytest tests/backend
uv run python app/manage.py check
```

Confirm whether `settings_test.py` is now required for pytest, and whether the
Django test runner remains supported or intentionally deprecated.

## Review Guardrails

1. Compare Xavier's branch against `origin/dev`.
2. Confirm no accidental workflow or deployment file changes unless explicitly intended:
   ```bash
   git diff --name-status origin/dev...HEAD -- .github docker-compose*.yml descr/deployment.md descr/prod-deploy-runbook.md
   ```
3. Keep test moves, header cleanup, mechanical refactors, and feature work in
   separate commits.
4. Do not delete existing regression tests unless an equivalent renamed test is
   present and easier to understand.
5. Pay special attention to `app/fiches/static/fiches/js/transcription-sync.js`,
   `app/fiches/templates/fiches/display/transcription*.html`,
   `app/fiches/forms.py`, `app/fiches/views/transcription.py`,
   `app/fiches/views/search.py`, `app/fiches/views/bibliography.py`,
   `app/fiches/views/collections.py`, and `app/fiches/admin.py`.
6. For Xavier's `chore/clean-repo` branch, also review:
   - Python runtime changes (`.python-version`, Dockerfile base images);
   - uv files (`pyproject.toml`, `uv.lock`);
   - Ruff/ty configuration and whether findings are style-only or behavioral;
   - migration history and new migrations `0005` / `0006`;
   - removal of management commands, middleware and context processors.

## Automated Regression Coverage To Preserve

Existing tests that must still pass or be replaced by equivalent tests:

- `test_dead_code_removal.py`
  - viewer controls removed during facsimile cleanup must not reappear;
  - essential viewer functions/styles must remain present.
- `test_patrinum_facsimile_sources.py`
  - Patrinum image URLs map to IIIF `info.json`;
  - blocked manifest fallback still extracts record page images.
- `test_last_transcriptions_publications.py`
  - latest public transcriptions are ordered by publication date;
  - public list caps at 50 items.
- `test_transcription_form_defaults.py`
  - `published_by` defaults to the configured user when empty.
- `test_biblio_display.py`
  - bracketed bibliography date components are preserved.
- `test_biblio_subject_person.py`
  - new subject persons can be created by allowed users;
  - secondary literature does not mark new subject persons as secondary;
  - unauthorized users cannot create subject persons;
  - double-pipe subject person input is normalized.
- `test_biblio_edit.py`
  - author field renders the expected name span.
- `test_admin_news_image.py`
  - news legend remains optional;
  - news author defaults to the request user;
  - admin save sets author when missing.
- `test_status_roles.py`
  - `sync_status_roles --apply` grants profile permissions to directeurs;
  - dry-run does not mutate permissions;
  - director user profile inline appears after sync.
- `test_search_person_list.py`
  - person list search keeps inherited menu JavaScript.
- `test_error_views.py`
  - Django 5 500 error handler renders the expected template/status.

If tests were moved to `tests/backend/`, verify every test above still exists
under its new name/path or has an explicit equivalent. Do not accept relocation
as proof of preservation; compare assertions.

Newly reported tests to inspect:

- `test_place_record.py`
  - Place model creation, lookup and category behavior are covered;
  - PlaceCategory seed data from migration `0006` is reflected in tests.

## Manual Functional Checks

### Transcription Viewer And Facsimile

Source: PR #99, GitHub issues #96-#106, facsimile commits, deployment notes.

Test at least one transcription with IIIF facsimile, one without facsimile, and
one with no transcription text.

- Hard reload a transcription in text mode:
  - no visible layout flicker;
  - text mode remains selected;
  - viewer panel is hidden until requested.
- Toggle "Notes en marge":
  - no flicker;
  - checkbox state matches rendered note position;
  - note layout remains correct after reload.
- In facsimile-only mode:
  - the old "Repere" indicator is not visible in the IIIF toolbar.
- In text-only mode:
  - default version is edited/normative, not diplomatic;
  - line breaks are hidden by default;
  - option labels match the expected text-mode semantics.
- In text + facsimile mode:
  - diplomatic version and line-break defaults remain coherent;
  - option labels match split-view semantics;
  - page sync is active only where expected.
  - facsimile and text appear side by side, not with the facsimile pushed below
    the transcription area.
- In Firefox:
  - line height is not excessive in text-only and text + facsimile modes.
- For a transcription without facsimile:
  - the mode bar remains visible;
  - facsimile buttons are disabled/greyed;
  - text mode and text options remain usable.
- For a transcription with no transcription text:
  - facsimile-only default is applied.
- Patrinum fallback:
  - a blocked manifest still displays extracted image tile sources.

### Transcription Metadata And Publication Dates

Source: February 2026 transcription metadata fixes and deployment records.

- Editing a public transcription preserves or updates:
  - `published_date`;
  - `published_by`;
  - `modified_date`;
  - `modified_by`.
- Publication/modified date display uses `d.m.Y` format where expected.
- Manual date editing does not disappear after saving.
- The grey date placeholder in edit mode reads `jj/mm/aaaa` where expected.
- Public latest-transcriptions lists use publication date ordering.
- The home page "Transcriptions" block also uses publication date ordering.
- Non-public transcriptions do not accidentally receive public publication
  metadata.
- Citation block shows publication date and version with the correct context
  variables.

### Editorial Notes And Display Normalization

Source: March 2026 local fix and Beatrice fixes.

- On a known transcription such as `/fiches/trans/270/`, switch to "Version
  éditée".
- In "Notes de l'éditeur":
  - adapted `.sic` words should not remain visible in blue;
  - reconstructed bottom notes and side notes both inject the `.corr` form;
  - recipient address/envelope label remains correct.
- Verify transcription display labels:
  - "adresse du destinataire" is shown where expected;
  - notes display and layout buttons remain centered/aligned.

### Bibliography Edit Form

Source: `.github/chats/biblio-edit.chat.md`, historical debugging spreadsheets,
UNIL mailbox excerpts, May 2026 biblio fixes.

Test a representative bibliographic fiche such as `/fiches/biblio/edit/5948/`
if the fixture/data is present. Also test the historical examples from the
spreadsheet when data is available:

- `/fiches/biblio/8567/`
- `/fiches/biblio/10241/`
- `/fiches/biblio/10829/`

- Existing subject persons are prefilled.
- New subject persons can be added only by authorized users.
- Double-pipe subject person inputs are normalized.
- Secondary literature does not incorrectly mark new subject persons as
  secondary.
- New author/person created from a primary bibliography defaults to a primary
  person without biography.
- New author/person created from a secondary bibliography defaults to a
  secondary person without biography.
- Existing and newly created people appear in author/person autocomplete lists.
- The "Personne" field is not mandatory, like "Société/Académie".
- Keyword labels, including secondary keyword labels, are not empty.
- Primary and secondary keywords are ordered alphabetically in dropdowns.
- Society/academy select options do not contain unexpected duplicates.
- Notes formset names and backend handling remain compatible.
- Bibliography notes can be added and saved.
- Date fields accept and preserve the expected historical date format.
- Bracketed bibliography dates are preserved after save.
- Date ranges do not introduce unexpected spacing, for example avoid
  `1794- 1798` when the expected display is `1794-1798` or the established
  project format.
- Empty day/month parts stay empty after save; they must not be auto-filled.
- `Date` / `Date fin` helper fields do not leak visible parasite labels such
  as `Date f` / `Date 2f`.
- For manuscript bibliographic records, the restored `Nature du document`
  requirement is covered:
  - `Nature du document` is available as an admin-managed dropdown for
    manuscripts;
  - the field is shown near `Type d'écrit`;
  - the selected value persists after save/reopen;
  - the value appears on the bibliography read view;
  - non-manuscript bibliography forms are not affected by the manuscript-only
    field.
- Author/contributor widgets still render names correctly.
- Contribution type persists after save.
- Director, collaborator, and scientific editor roles render in the automatic
  reference header according to the display rules.
- The automatic bibliography reference header includes author/date/title/volume
  data correctly:
  - dates display as natural French dates where expected, not broken slash
    formats;
  - `nb de volumes` appears before pages when filled;
  - title spacing and quotation spacing remain correct.
- Saving a bibliographic fiche does not lose dynamic people, keywords, notes, or
  rich text.
- Saving a bibliographic fiche must be checked for the still-unidentified May
  2026 symptom: "something disappeared when saving a fiche".
- Copied collector/rich-text markup is normalized and does not break display.
- Recommended-but-not-required fields trigger the expected confirmation warning
  before save, for example missing `Lieu`, `Date`, `Pages`.
- Adding a document or URL attachment from a bibliography form works and is not
  blocked by iframe/X-Frame browser protection.
- Bibliography project indexing via the yellow label works and no longer returns
  `Internal Server Error`.

### Project Tabs And Collections

Source: historical debugging spreadsheets, February/March 2026 project tab
fixes.

- On `/projets/` and representative project pages:
  - project tabs render with CSS/JS intact;
  - selected items-per-page persists while paginating;
  - removing a bibliography from a project uses the correct model lookup;
  - removing a transcription from project tabs still works;
  - tab content is not mixed between bibliography/transcription sections.
- Project carousel:
  - clicking a project carousel image opens the expected popup/viewer;
  - orange lateral arrows work outside the popup and inside the popup.
- Project thumbnail/vignette:
  - attaching a vignette to a project works without `Internal Server Error`.
- Trouvailles and actualités image viewers:
  - direct URL such as `/publications/trouvailles/5/` opens the expected
    trouvaille drawer;
  - clicking main/carousel images opens the expected popup/viewer;
  - image navigation remains usable.
- For a shared collection:
  - director account can edit collection owner via dropdown;
  - other collection fields remain read-only where expected.
- Collection edit must not erase existing attached bibliography references,
  access rules, or other data after saving.
- Adding a collection works and is not blocked by iframe/X-Frame browser
  protection.
- Removed/unused controls such as "Afficher/masquer les détails de la
  collection" and "Créer une nouvelle collection" must not reappear unless
  intentionally restored.

### Search

Source: historical debugging spreadsheets, deployment smoke checklist, May 2026
search fixes.

- Named-entities requirement section 5:
  - advanced search includes a `Liste des lieux` tab immediately after
    `Liste des personnes`;
  - the tab displays place fiches in alphabetical order;
  - the A-Z first-letter filter behaves like the person list;
  - each place entry links to its public fiche lieu;
  - the place category is visible where available.
- Global search with multiple keywords, for example "La Harpe lettre":
  - applies AND semantics;
  - ordering remains sensible.
- Global search example "Mingard":
  - result ordering matches the documented expectations.
- Global search example "Lovis":
  - searched fields match the historical rule:
    - biography: all fields;
    - bibliography: all fields, including collection and contribution/person
      fields, excluding fiche author and last modification fields;
    - transcription: all fields except reviewers, state, extent, last
      modification, and access.
- Global search result grouping/order:
  - biographies first;
  - bibliographies by type: book, book chapter, journal article, manuscript;
  - transcriptions last;
  - within each group, alphabetical then date ordering where applicable.
- Search result typography:
  - no extra spaces around book/manuscript titles;
  - no extra spaces inside or after quotation marks for chapter/article titles.
- Advanced search:
  - display parameters/toggles persist;
  - filters such as toujours/jamais/journal still work.
- Advanced bibliographic search:
  - "type de document" and "projets" filters remain visually usable and not
    excessively bulky.
- Advanced biography search:
  - "a publié dans la revue" filter does not spin indefinitely;
  - default filter state is empty.
- Person list search:
  - inherited menu JavaScript remains present;
  - no menu regression from Django 5 template changes.
- Indexed text normalization:
  - accented/case/punctuation variations still find expected records after
    `update_index`.

### Admin, Media, News, Permissions

Source: historical debugging spreadsheets, UNIL mailbox excerpts, production
incident 2026-03-03, role docs, May 2026 permissions fix.

- Django admin 500 handler and custom error pages still render correctly.
- News admin:
  - image upload works;
  - document upload works;
  - news edit page with an attached document opens;
  - missing author is set from current admin user;
  - legend remains optional.
- Document string rendering:
  - attached document rows do not raise `NameError`;
  - `basename` behavior remains available when file title is absent.
- Roles:
  - run `sync_status_roles` dry-run and apply in test/staging;
  - directeurs receive user profile permissions;
  - doctorants retain document attachment permissions;
  - doctorants can edit and delete all documents attached to a bibliographic
    fiche, including documents uploaded by other users;
  - former assistants group handling remains as documented.
- User admin/profile:
  - "Informations supplémentaires" / research topic free field is visible for
    staff accounts that manage users;
  - directeurs have the missing permission corrected in May 2026, so the field
    remains visible for that role;
  - permissions required for that inline survive restores and role syncs.
- User/group admin:
  - individual user selection remains usable enough for group management.
- Person admin:
  - new persons created in admin are available in bibliography author/person
    fields and workspace fiche creation lists;
  - "personne littérature secondaire" persists after save;
  - primary persons with biography appear in "Créer une fiche biographique" /
    "Charger la liste des personnes".
- Project/trouvaille admin:
  - image inline fields are present: legend, image, link, position;
  - document inline fields are present: title, file;
  - duplicate "vignette" fields are not shown;
  - URL field remains visible where historically expected.

### Static, Media, Deployment-Sensitive Paths

Source: Django 5 production cutover postmortem.

- Static assets load from `/static/`.
- Media assets load from `/media/` and `/user-media/` where relevant.
- `/actualites/` renders thumbnails and cached media images.
- Thumbnail cache write paths remain compatible with production media mounts.
- `collectstatic` completes without CKEditor regex warnings.
- CKEditor plugins still work after JS cleanup:
  - notes;
  - footnotes;
  - illegible text plugin;
  - no accidental global variables are reintroduced in touched plugin code.

### Infrastructure, Runtime And Migrations

Source: weekly report received on 2026-06-02 for Xavier's `chore/clean-repo`
branch.

- Python runtime:
  - confirm Python 3.13 is intentional and compatible with Django, Pillow,
    mysqlclient, haystack/pysolr, sorl-thumbnail, CKEditor and deployment images;
  - verify local, CI, staging and production do not disagree on Python version.
- uv:
  - `uv.lock` is present and reproducible;
  - dependency groups are clear for runtime, dev/test and optional tooling;
  - old pip/requirements workflows are either still supported or explicitly
    replaced in documentation.
- Docker:
  - multi-stage Dockerfile still installs runtime dependencies needed by
    mysqlclient, Pillow and media thumbnail generation;
  - dev compose/watch changes do not affect staging/prod compose behavior;
  - root compose file convention remains compatible with deployment docs.
- Database migrations:
  - migration `0005` MyISAM to InnoDB is reviewed as an operational migration;
  - staging rehearsal includes backup, duration estimate and rollback strategy;
  - migration `0006` PlaceCategory seed data is idempotent or otherwise safe;
  - restored `0001_initial` history matches existing production DB state and
    does not require recreating existing tables.
- Removed commands/code:
  - `sync_perms` removal has a documented replacement for role permission sync;
  - removed pagination middleware/paginator, COinS cluster, context processor
    and `fiches/dev` script are verified unused by URL routes, templates,
    settings, management tasks and deployment scripts.

### Biography Forms

Source: historical debugging spreadsheets.

- Representative biography page, for example Barbeyrac reached from
  `/fiches/biblio/8174/`, loads without timeouts or intermittent 500 errors.
- Relations and contacts:
  - primary-person autocomplete appears after entering the first letters;
  - existing names can be selected and saved;
  - admin users can add primary names that are not yet in the database.
- Biography notes can be added and saved.
- Public functions / societies and academies date fields display with dots,
  for example `01.06.1780`, not slashes.
- "Fonds d'archives" accepts long content and does not truncate or reject the
  longer notes reported in May 2026.

### Publications And Static Content

Source: UNIL mailbox excerpts from May 2026.

- Publications > Trouvailles:
  - direct trouvaille links open the correct drawer/content.
- Publications > Vidéos:
  - YouTube videos render and play/embed correctly.
- Bibliographic display pages:
  - long notes and summaries remain readable;
  - long text does not overflow into the footer, especially in Firefox.

### Manuscript And Transcription Creation Forms

Source: historical debugging spreadsheets and UNIL mailbox excerpts.

- New manuscript fiche:
  - "Lieu de dépôt" default remains empty (`----`), not "Archives cantonales
    vaudoises".
- New transcription:
  - can be created and saved without the old `#id_text` required-field blocker
    when no transcription text is expected.
  - transcription notes can be added and saved.
- Transcription editor:
  - Bold button remains available;
  - page/folio markers `<...>` display in black in reading mode;
  - folio-to-scan marker syntax `<<...>>`, if still part of the feature, is
    invisible in reading mode and visually distinct in editing mode.

### Facsimile Feature Requests From December 2025

Source: UNIL mailbox excerpts and `backlog_lumieres_feat_facsimile.xlsx`
mentioned in the mail thread.

Confirm Xavier's work does not regress these feature expectations:

- Table of contents appears as a movable popup.
- Text mode:
  - note call numbers are not duplicated when notes are displayed in the margin;
  - "notes en bas de page" option is available;
  - margin notes remain the text-mode default if that remains the chosen rule.
- Mixed text + facsimile mode:
  - bottom notes are the default if that remains the chosen rule.
- Image viewer:
  - direct jump to a requested scan page works.
- Facsimile-only mode:
  - layout does not overflow below the viewport;
  - viewer height is aligned with the Chavannes volume use case.

## Branch Review Checklist For Xavier's Work

Before accepting Xavier's branch:

- [ ] `git diff --name-status origin/dev...HEAD` contains only intentional
      application/test/doc files.
- [ ] No accidental `.github/workflows/docker-prod.yml` change.
- [ ] Existing regression tests above still exist or are clearly renamed.
- [ ] New root-level `tests/` layout, if introduced, is discoverable by CI and
      does not orphan Django test runner coverage.
- [ ] All automated tests pass.
- [ ] Python 3.13 / uv adoption is explicitly accepted or reverted/deferred.
- [ ] MyISAM to InnoDB migration has a staging rehearsal and rollback plan.
- [ ] `sync_perms` deletion has an approved replacement path.
- [ ] Manual transcription/facsimile checklist completed in Chrome and Firefox.
- [ ] Bibliography edit checklist completed on a data-rich fiche.
- [ ] Search/index checklist completed after `update_index` on staging-like data.
- [ ] Admin/news/media checklist completed with an authenticated staff user.
- [ ] Commit history keeps mechanical refactor/header/test moves separate from
      functional named-entities work.

## Suggested New Tests If Time Allows

- Rename `test_dead_code_removal.py` to `test_facsimile_viewer_controls.py` and
  keep the same regression intent.
- Add a browser-level regression test for transcription mode defaults and option
  persistence if Playwright/Selenium is introduced.
- Add a Django test for project bibliography/transcription removal endpoints.
- Add a regression test for bibliography date parsing/preservation.
- Add a regression test for copied rich-text collector markup normalization.
- Add a test ensuring `pytest` and `python app/manage.py test` agree on test
  discovery, if the test layout is migrated.
