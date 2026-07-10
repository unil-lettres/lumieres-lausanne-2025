# Lumières Lausanne

Lumières Lausanne is a Django application for publishing and editing scholarly
data about the Swiss Enlightenment: bibliographic fiches, biographies,
transcriptions, projects, news, media and search.

This repository contains the application code, Docker Compose setup, CI
configuration, and maintainer documentation for local development, staging, and
production releases.

## Maintainer First

If you are fixing an outage, restoring data, deploying, or taking over without
knowing the project, start here:

- [Maintainer survival page](descr/maintainer-survival.md): stack paths,
  restart/check commands, DB dump import, superuser creation, health checks.
- [Current project state](descr/project-state-2026-07-09.md): branch map,
  staging/named-entities status, local worktree guardrails.
- [Production deployment runbook](descr/prod-deploy-runbook.md): release and
  rollback procedure.
- [Wiki Lettres production page](descr/wiki-lumieres-informations-techniques.md):
  copy-pastable technical VM page for the institutional wiki.
- [Documentation index](descr/README.md): all local operational notes.

Production is `https://lumieres.unil.ch/`. Staging is
`https://plt-tst-2.unil.ch/`.

## Branches

- `master`: current production release line.
- `dev`: main development line.
- `staging/named_entities`: named-entities integration branch currently used
  for staging validation.
- `feat/named_entities`: Xavier's original feature branch; do not deploy it
  directly.

Use `descr/project-state-2026-07-09.md` before changing the named-entities
workflow.

## Requirements

- Docker Desktop 4.x+ or Docker Engine with Compose V2.
- Git.
- Optional: VS Code with Dev Containers.

## Quick Start: Local Development

```bash
git clone https://github.com/unil-lettres/lumieres-lausanne-2025.git
cd lumieres-lausanne-2025
cp .env.template .env
docker compose up -d
docker compose ps
```

Local URLs:

- app: `http://localhost:8000/`
- Solr admin: `http://localhost:8983/solr/#/lumieres`

Useful first-run commands:

```bash
docker compose exec -T app python manage.py migrate
docker compose exec -T app python manage.py sync_status_roles --apply
docker compose exec -T app python manage.py createsuperuser
docker compose exec -T app python manage.py update_index
```

Useful local checks:

```bash
docker compose logs --tail=200 app
docker compose exec -T app python manage.py check
curl -I http://localhost:8000/
```

Stop local dev:

```bash
docker compose down
```

## Local Data Notes

Production and staging use the current migrated schema. Routine local setup and
routine deploys do not require legacy DB normalization SQL.

After a DB restore or auth-table refresh, run:

```bash
docker compose exec -T app python manage.py sync_status_roles --apply
docker compose exec -T app python manage.py update_index
```

If search is still empty or inconsistent, use a full rebuild:

```bash
docker compose exec -T app python manage.py rebuild_index --noinput
```

Some pages need media files under `app/media/`, mounted into the container. Use
the production backup/media notes before copying real media.

## Xavier Isolated Validation Stack

Xavier branch validation uses a separate local worktree and Docker project. Do
not mix it with normal `dev` work:

- worktree: `/Users/jganivet/Développement/lumieres-xavier-clean-repo`
- app: `http://127.0.0.1:8010/`
- phpMyAdmin: `http://127.0.0.1:8011/`

Validate Xavier's work there first, then promote accepted commits from the main
`newfeats` worktree into `staging/named_entities`. See
[Maintainer survival page](descr/maintainer-survival.md) and
[Xavier handoff notes](descr/xavier-handoff-notes.md).

## Documentation

Operational documentation lives in `descr/`. User/developer background docs live
in `docs/` and can be served with MkDocs:

```bash
mkdocs serve
```

Important starting points:

- [descr/maintainer-survival.md](descr/maintainer-survival.md)
- [descr/project-state-2026-07-09.md](descr/project-state-2026-07-09.md)
- [descr/prod-deploy-runbook.md](descr/prod-deploy-runbook.md)
- [descr/deployment.md](descr/deployment.md)
- [docs/index.md](docs/index.md)

## Production Guardrails

- Treat production as read-only unless a change is explicitly authorized.
- On prod, always verify the resolved image before `up -d`:
  `docker compose config --images`.
- Keep prod pinned to an explicit release tag through `LUMIERES_IMAGE`; do not
  deploy `latest`.
- Run `collectstatic` after deploying image changes that affect static assets.
- Run `sync_status_roles --apply` after DB restores or auth-table refreshes.

## License And Contact

Copyright University of Lausanne.

License: pending / internal use.

For project questions, open an issue or contact the maintainers.
