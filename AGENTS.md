# AGENTS.md — Lumières Lausanne

<!-- BEGIN SHARED AGENT CONTEXT -->
## Shared agent context entry point

When a conversation starts with `context lumieres`, `contexte lumieres`, or
`../agents/kickstart.md lumieres`, treat it as a context-load command before answering
project-specific questions. Do not infer project context from active IDE tabs,
shell history, approved command prefixes, or recent conversation drift.

Load the shared and project-specific rules before acting:

- `../agents/kickstart.md`
- `../agents/agents.yaml`
- `../agents/phases.yaml`
- stack files referenced by `../agents/CONTEXT.lumieres.md`
- `../agents/CONTEXT.lumieres.md`
- `../agents/projects/lumieres/project-policy.yaml`
- `../unil-ops/data/inventory/projects.json` entry for `lumieres`
- relevant `../unil-ops` inventory, runbooks, health cache, and backup metadata through
  the `unil_ops` MCP server when available

The context-load confirmation should be short and include:

```text
context lumieres loaded.
MCP: unil_ops available
Agent context loaded: ../agents/CONTEXT.lumieres.md.
Scope: Lumieres Lausanne project; primary dev worktree or Xavier validation lane must be stated explicitly; docs in descr/; production service lumieres.
Before acting, I will state the concrete target environment, host/service,
worktree/docs root, runtime, and rollback boundary when relevant.
```

If the registered MCP tools are not visible in the current Codex session, use:

```text
MCP: unil_ops registered but not available in this session
```

Context loading is preparation, not authorization. Production writes,
deployments, VM maintenance, restores, and rollback steps still require the
explicit project boundary preflight and the relevant runbook or request file.
<!-- END SHARED AGENT CONTEXT -->

Always read these files when relevant:
- `/Users/jganivet/Développement/Backups/lumieres.unil.ch/README.md` for local backup entry points and cross-references.
- `/Users/jganivet/Développement/Backups/lumieres.unil.ch/LOCAL-BACKUP-PROCEDURE.md` for production backup refresh rules.
- `/Users/jganivet/Développement/unil-ops/docs/runbooks/vms/lumieres.md` for VM operations context.
- `descr/prod-deploy-runbook.md` for staging/prod deployment steps and postmortem notes.
- `descr/deployment.md` for schema and migration notes.
- `descr/roles.md` for role/permission changes that must be applied in prod DB.

Operational guardrails:
- Before any Lumières operation, explicitly choose the target local stack/worktree:
  - `dev`: `/Users/jganivet/Développement/lumieres-lausanne-newfeats`, normal current work.
  - `xavier`: `/Users/jganivet/Développement/lumieres-xavier-clean-repo`, isolated Xavier branch validation.
- State the chosen stack before running Docker, migration, database, test, or browser-test commands.
- Do not mix commands between these worktrees. Xavier migrations/restores must only run in the `xavier` stack; normal dev documentation/work should stay in the `dev` worktree.
- Treat production as read-only unless the user explicitly authorizes changes.
- Prefer showing exact commands before running them on remote VMs.
- Keep staging/prod aligned with the documented Docker image tags and compose files.

Repo conventions:
- Compose files live at repo root. Local dev uses `docker-compose.yml`; staging uses `docker-compose.staging.yml`; prod uses `docker-compose.yml` plus `docker-compose.prod.yml`.
- On prod, `/u01/projects/dockerized/lumieres2-prod/.env` must set `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`, `COMPOSE_PROJECT_NAME=lumieres-prod`, and a release-tagged `LUMIERES_IMAGE`.
- Static changes on staging/prod usually require `collectstatic` after deploying a new image.
- Prod releases follow the “merge dev → master → tag vYYYY.MM.DD → deploy tag” workflow.

Form and template regression guardrails:
- Before changing a link/action to POST in an edit template, check whether the control is rendered inside an existing `<form>`.
- Never add a nested `<form>` inside `form.edit-form` or `#biblio-form-id`; nested forms are invalid HTML and can break real browser submission even when Django test-client POSTs pass.
- If a POST control must appear inside an existing edit form, use `button type="button"` with a JS-created temporary POST form, or move the control outside the parent form.
- For form-related hotfixes, validate with a real browser against the local stack or staging: open the affected edit page, submit via the actual UI save control, confirm redirect and persistence, and check logs for 500s.
- Add or update a regression test for the rendered HTML contract when a partial template is reused across display/edit contexts.

Sensitive data:
- Avoid opening files under `descr/private` unless explicitly requested.
