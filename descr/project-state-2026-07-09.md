# Lumières Project State - 2026-07-09

Status: holiday handoff note
Recorded by: Julien / Codex
Scope: local Git/worktree state, production hotfix state, named-entities staging validation

## Short Version

- Production is stable on `v2026.07.03`.
- Thomas' two production bugs are fixed on prod and synced back to `dev`.
- Xavier's named-entities work is deployed only on staging through
  `staging/named_entities`.
- Named entities still need functional validation by Beatrice/Xavier before any
  production rollout decision.
- The main local `dev` worktree has been resynchronised with `origin/dev` after
  preserving the previous local dirty state.

## Live Environments

### Production

- Public URL: `https://lumieres.unil.ch/`
- VM: `lumieres-srv2.unil.ch`
- Compose path: `/u01/projects/dockerized/lumieres2-prod`
- Live web image verified on 2026-07-09:
  `unillett/lumieres:v2026.07.03`
- Live image revision: `c06c2c2a9d7a8a5e567a9900c931787e2626fe90`
- Git tag: `v2026.07.03`
- Branch/release line: `origin/master`

This release contains Thomas' hotfix:

- creating a bibliographic fiche no longer creates an automatic blank duplicate;
- advanced search by registration date includes secondary literature results.

Post-release cleanup already done:

- confirmed bad blank biblio `12909` was empty and deleted from prod;
- deleted 43 strict blank pre-hotfix `tneyroud` biblio fiches from prod after
  creating a backup table/dump under the prod backups directory;
- user-facing message sent to Thomas.

### Staging

- Public URL: `https://plt-tst-2.unil.ch/`
- VM: `plt-tst-2.unil.ch`
- Compose path: `/var/www/lumieres2`
- Named-entities override:
  `/home/jganivet/lumieres-staging-named-entities.override.yml`
- Live web image verified on 2026-07-09:
  `unillett/lumieres:named-entities-2026-07-03-1d1dc5e`
- Integration branch: `origin/staging/named_entities`
- Integration commit: `1d1dc5edfc00a06320e1be95bfa72d0d8519d9fc`

Staging contains:

- Xavier's `feat/named_entities` work;
- the production hotfix from `v2026.07.03`;
- refreshed staging DB/media state from the recent validation cycle.

Staging browser checks after the hotfix merge passed:

- new biblio creation page did not create a blank record on GET;
- biblio edit page showed named-entity fields;
- place list/display/edit pages loaded;
- advanced biblio search by `Date d'enregistrement` worked;
- static assets loaded successfully;
- no browser JS errors or web 500 tracebacks observed;
- temporary browser-test user/place were cleaned afterward.

## Git Branch Map

### `origin/master`

- Current prod release line.
- Current commit: `c06c2c2 Fix biblio creation and date search`.
- Tag: `v2026.07.03`.
- Deployed to production.

### `origin/dev`

- Current main development line.
- Current commit: `027c85a Fix biblio creation and date search`.
- Contains the same Thomas hotfix behavior as prod, but with a different SHA
  because the fix was applied onto the dev history after the prod hotfix.
- Local main worktree was reset to this commit on 2026-07-09.

### `origin/feat/named_entities`

- Xavier's original named-entities feature branch.
- Based originally on the dev line.
- Current commit observed: `1b5cbac Add trailing slash to the search list routes`.
- Do not deploy this branch directly to prod.

### `origin/staging/named_entities`

- Integration branch currently deployed to staging.
- Current commit: `1d1dc5e Merge remote-tracking branch 'origin/master' into staging/named_entities`.
- Combines Xavier's named-entities branch with current production hotfixes.
- Use this as the reference branch for the current staging validation cycle.

## Local Worktrees On This Mac

### Main dev worktree

- Path: `/Users/jganivet/Développement/lumieres-lausanne-newfeats`
- Intended use: normal Lumières work and documentation.
- Branch after cleanup: `dev`
- Synced state after cleanup: `dev...origin/dev` with no ahead/behind.

Before the cleanup, this worktree had one local documentation commit and many
dirty documentation/code-looking changes. The local state was preserved before
syncing:

- safety branch: `safety-local-state-2026-07-09`
- stash: `stash@{0}` with message
  `safety local state before holiday handoff sync 2026-07-09`

Do not drop that stash until the handoff documentation has been reviewed and
confirmed sufficient.

### Xavier validation worktree

- Path: `/Users/jganivet/Développement/lumieres-xavier-clean-repo`
- Intended use: isolated validation of Xavier branches only.
- Current observed state: detached at Xavier's named-entities branch commit.
- Docker Compose project: `lumieres-xavier`
- App URL: `http://127.0.0.1:8010/`
- phpMyAdmin URL: `http://127.0.0.1:8011/`
- Override file: `/private/tmp/lumieres-xavier-compose.override.yml`

Do not run normal dev migrations/restores from this worktree, and do not use it
for routine docs edits.

### Temporary worktrees

Temporary worktrees may still exist under `/private/tmp`, including:

- `/private/tmp/lumieres-staging-named_entities`
- `/private/tmp/lumieres-hotfix-biblio-create-search-date`
- `/private/tmp/lumieres-dev-hotfix-biblio-sync`

They are useful as local history, but should not be treated as authoritative.
The authoritative remote refs are listed in the branch map above.

## Current Open Items

### Named Entities

Pending:

- Beatrice/Xavier functional validation on staging.
- Decision on whether the staged named-entities implementation is accepted as
  is, needs fixes, or should remain isolated longer.
- If Xavier makes follow-up fixes, he should branch from
  `staging/named_entities`, not directly from stale local work.

Production rollout guidance:

- do not merge/deploy `feat/named_entities` directly;
- keep `staging/named_entities` as the current integration reference;
- after validation, plan a normal merge back into `dev`, then `master`, then
  tag/release using the production runbook.

## Workflow For Xavier Fixes

Use this sequence when Xavier pushes follow-up work for named entities.

### 1. Validate Xavier's work locally

Open/use the isolated Xavier worktree:

```bash
cd /Users/jganivet/Développement/lumieres-xavier-clean-repo
```

Target stack:

- worktree: `/Users/jganivet/Développement/lumieres-xavier-clean-repo`
- Docker Compose project: `lumieres-xavier`
- local app: `http://127.0.0.1:8010/`
- local DB volume: `lumieres-xavier_db_data`
- local Solr volume: `lumieres-xavier_solr_data`

Fetch Xavier's branch and validate there. This stack is allowed to have Xavier's
branch-specific runtime/test layout and its own local database state.

When asking Codex to help in this phase, start the request with the target
explicitly, for example:

```text
Target Xavier isolated stack. In /Users/jganivet/Développement/lumieres-xavier-clean-repo,
fetch Xavier's latest feat/named_entities work and validate it locally.
Do not touch staging or production.
```

### 2. Promote only accepted work to the staging integration branch

After local validation passes, switch back to the main Lumières worktree:

```bash
cd /Users/jganivet/Développement/lumieres-lausanne-newfeats
```

Promotion target:

- worktree: `/Users/jganivet/Développement/lumieres-lausanne-newfeats`
- branch to update: `staging/named_entities`
- deployment target: `plt-tst-2.unil.ch`

The staging deployable artifact must come from `staging/named_entities`, not
directly from the isolated Xavier worktree. Merge or cherry-pick Xavier's
accepted commits into `staging/named_entities`, resolve integration/deployment
differences there, then build and deploy staging from that integration commit.

When asking Codex to help in this phase, open the main `newfeats` folder and use
an explicit request such as:

```text
Target main dev worktree. Promote Xavier's validated named-entities fix to
staging/named_entities and deploy it to plt-tst-2. Do not touch production.
```

### 3. Validate staging

After deployment to `plt-tst-2`:

- run `collectstatic` if static files may have changed;
- run migrations/indexing only if the promoted changes require it;
- do browser smoke checks on the touched named-entities paths;
- keep temporary staging test data/users cleaned up after validation.

### 4. Production remains a later decision

Do not treat a successful local Xavier validation or staging deploy as approval
for production. Production rollout still requires Beatrice/Xavier validation and
a normal release plan:

```text
accepted named_entities integration -> dev -> master -> vYYYY.MM.DD tag -> prod deploy
```

### Backlog

- General search result grouping/order requested by Beatrice is recorded in
  `descr/backlog.md`.
- It should be considered with the named-entities/search work, not as an
  isolated emergency hotfix.

### Local Backup Metadata

`unil_ops` reported on 2026-07-09 that the local prod backup refresh metadata was
21 days old against a 14-day threshold. Refreshing the local prod backup before
holiday would improve recovery confidence, but it is separate from the code
handoff.

## Guardrails

- Treat production as read-only unless a production change is explicitly
  authorized.
- Before any Lumières operation, state target environment, host/service,
  worktree/docs root, runtime, and rollback boundary.
- Keep the `dev` and Xavier validation worktrees separate.
- For prod releases, use the standard flow:
  `dev` -> `master` -> tag `vYYYY.MM.DD` -> deploy tagged image.
- For staging named-entities validation, use `staging/named_entities`.
- For form/template hotfixes, validate with a real browser and check logs,
  especially where edit pages contain existing forms.
