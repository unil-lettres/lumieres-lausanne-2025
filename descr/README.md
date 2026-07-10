# Lumieres `descr/` Index

This directory holds project-local operational and planning notes. Keep detailed
Lumieres procedures close to the application code; use `unil-ops` for the
cross-project inventory, VM runbooks, health status, and backup metadata.

## Active Entry Points

- Maintainer survival page: `maintainer-survival.md`
- Current project state / holiday handoff:
  `project-state-2026-07-09.md`
- Deployment: `prod-deploy-runbook.md`
- Schema and migration notes: `deployment.md`
- Production role/permission changes: `roles.md`
- Xavier validation lane: `xavier-handoff-notes.md`,
  `xavier-regression-test-plan.md`
- Current backlog: `backlog.md`
- Production incident history: `postmortem-prod-reboot-wrong-image-2026-03-19.md`

## Attachments And Archives

- `devis/` and top-level PDF/DOCX files are project attachments, not active
  deployment runbooks.
- `private/` may contain sensitive operational notes; do not open or copy from
  it unless explicitly requested.

## Agent Notes

Before deployment, backup refresh, rollback, or VM work, load the Lumieres
context and state the target environment, worktree, runtime, and rollback
boundary. Do not infer the target from open editor tabs.
