# AGENTS.md — Lumières Lausanne

Always read these files when relevant:
- `descr/prod-deploy-runbook.md` for staging/prod deployment steps and postmortem notes.
- `descr/deployment.md` for schema and migration notes.
- `descr/roles.md` for role/permission changes that must be applied in prod DB.

Operational guardrails:
- Treat production as read-only unless the user explicitly authorizes changes.
- Prefer showing exact commands before running them on remote VMs.
- Keep staging/prod aligned with the documented Docker image tags and compose files.

Repo conventions:
- Compose files live at repo root. Local dev uses `docker-compose.yml`; staging uses `docker/docker-compose.staging.yml`; prod uses `docker-compose.yml` plus `docker/docker-compose.prod.yml`.
- On prod, `/u01/projects/dockerized/lumieres2-prod/.env` must set `COMPOSE_FILE=docker-compose.yml:docker/docker-compose.prod.yml`, `COMPOSE_PROJECT_NAME=lumieres-prod`, and a release-tagged `LUMIERES_IMAGE`.
- Static changes on staging/prod usually require `collectstatic` after deploying a new image.
- Prod releases follow the “merge dev → master → tag vYYYY.MM.DD → deploy tag” workflow.

Sensitive data:
- Avoid opening files under `descr/private` unless explicitly requested.
