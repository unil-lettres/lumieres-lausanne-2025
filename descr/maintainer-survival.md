# Lumières Maintainer Survival Page

Status: first-response maintainer entry point
Audience: someone who does not know Lumières and must understand, run, or
recover it quickly

## What This App Is

Lumières Lausanne is a Django application for publishing and editing scholarly
data about the Swiss Enlightenment: bibliographic fiches, biographies,
transcriptions, projects, news, media and search. The production site is
`https://lumieres.unil.ch/`; staging is `https://plt-tst-2.unil.ch/`.

## First Orientation

- Main repo: `https://github.com/unil-lettres/lumieres-lausanne-2025`
- Normal local worktree on Julien's Mac:
  `/Users/jganivet/Développement/lumieres-lausanne-newfeats`
- Xavier isolated validation worktree:
  `/Users/jganivet/Développement/lumieres-xavier-clean-repo`
- Current project state / branch map: `descr/project-state-2026-07-09.md`
- Deployment runbook: `descr/prod-deploy-runbook.md`
- Schema/deployment notes: `descr/deployment.md`

Before any operation, state the target: local dev, Xavier isolated stack,
staging, or production. Do not mix commands between these contexts.

## Install From A Fresh Clone

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

If the DB is new or after a restore:

```bash
docker compose exec -T app python manage.py migrate
docker compose exec -T app python manage.py sync_status_roles --apply
docker compose exec -T app python manage.py createsuperuser
docker compose exec -T app python manage.py rebuild_index --noinput
```

Useful local checks:

```bash
docker compose logs --tail=200 app
docker compose exec -T app python manage.py check
curl -I http://localhost:8000/
```

## Start The Local Dev Stack

From the repo root:

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=200 app
```

Stop local dev:

```bash
docker compose down
```

Do not run Xavier-branch migrations/restores in this worktree. Use the Xavier
isolated worktree for Xavier validation.

## Start / Inspect The Xavier Isolated Stack

Use only for Xavier branch validation:

```bash
cd /Users/jganivet/Développement/lumieres-xavier-clean-repo
docker compose -p lumieres-xavier \
  -f docker-compose.yml \
  -f docker/docker-compose.dev.yml \
  -f /private/tmp/lumieres-xavier-compose.override.yml \
  up -d
docker compose -p lumieres-xavier \
  -f docker-compose.yml \
  -f docker/docker-compose.dev.yml \
  -f /private/tmp/lumieres-xavier-compose.override.yml \
  ps
```

Local URLs:

- app: `http://127.0.0.1:8010/`
- phpMyAdmin: `http://127.0.0.1:8011/`

Promotion rule: validate there first, then promote accepted commits from the
main `newfeats` worktree into `staging/named_entities`; never deploy directly
from the isolated worktree.

## Start / Inspect Staging

Staging host: `plt-tst-2.unil.ch`
Project directory: `/var/www/lumieres2`

```bash
ssh <user>@plt-tst-2.unil.ch
cd /var/www/lumieres2
docker compose -f docker-compose.yml -f docker-compose.staging.yml ps
docker compose -f docker-compose.yml -f docker-compose.staging.yml logs --tail=200 web
curl -I http://127.0.0.1:8000/
```

Routine staging deploy after a new image is available:

```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml pull web
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --no-deps web
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T web \
  python manage.py collectstatic --noinput
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T web \
  python manage.py update_index
```

Current named-entities staging uses `staging/named_entities`; see
`descr/project-state-2026-07-09.md` before changing it.

## Production Survival

Production host: `lumieres-srv2.unil.ch`
SSH user documented in ops notes: `lmradm`
Project directory: `/u01/projects/dockerized/lumieres2-prod`
Public URL: `https://lumieres.unil.ch/`

Production is read-only unless a change is explicitly authorized. First checks:

```bash
ssh lmradm@lumieres-srv2.unil.ch
cd /u01/projects/dockerized/lumieres2-prod
docker compose ps
docker compose config --images
docker compose logs --tail=200 web
curl -I https://lumieres.unil.ch/
```

The prod image must be pinned in `.env` as
`LUMIERES_IMAGE=unillett/lumieres:vYYYY.MM.DD`; do not use `latest`.
For production deploys, use `descr/prod-deploy-runbook.md`.

## Common Emergency Symptoms

- Site down or 500: check `docker compose ps`, `docker compose logs --tail=200 web`,
  then public `curl -I`.
- Static/CSS missing after deploy: run `collectstatic` in the target web
  container.
- Search empty or stale: run `update_index`; use `rebuild_index` only when a
  full rebuild is intended.
- Permission/role issues after DB restore: run `sync_status_roles --apply`.
- Missing media on staging: compare staging media with prod media; prod reads
  must stay read-only unless explicitly authorized.

## What Not To Do

- Do not deploy `feat/named_entities` directly to production.
- Do not run Xavier validation commands in the main dev worktree.
- Do not run production writes/deploys without an explicit rollback boundary.
- Do not rely on `docker compose ps` alone after a prod incident; verify the
  resolved image with `docker compose config --images` and inspect the running
  image/tag.
