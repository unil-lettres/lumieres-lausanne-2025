# Production Deployment Runbook (Plan Only)

Status: draft plan
Audience: ops/dev (manual execution)
Scope: migrate from legacy Django 1 stack to new Dockerized stack on lumieres-srv2.unil.ch

## Recommended New Compose Location
Use a new, isolated compose project under:

/u01/projects/dockerized/lumieres2-prod

Reasons:
- Same disk as current Docker data (/u01), no cross-device copies.
- Keeps legacy stack intact for quick rollback.
- Mirrors staging layout, avoids touching /u01/projects/dockerized/django-lumieres.lausanne.

## Current Prod Snapshot (for reference)
See: descr/prod-vm-survey-2026-01-20.md
- Legacy compose: /u01/projects/dockerized/django-lumieres.lausanne
- Traefik v1.7 proxy with Host:lumieres.unil.ch labels
- Media: /u01/projects/dockerized/media
- MySQL 5.5 + local Solr

## High-Level Strategy
Keep host/Traefik/media path. Replace app/DB/Solr with new stack.
Create a new compose project and switch Traefik host rule to the new app during cutover.

## Version Parity (Match Staging)
Use the same service versions as the staging VM:
- MySQL: 9.3
- Solr: 8
- App: deploy the production image built from the same commit/tag as staging

## Staging Deployment Notes (GH Actions + DockerHub)
Goal: make staging refresh repeatable and easy.

### Build Trigger
- Docker image for staging is built by a GitHub Actions workflow on push to `dev`.
- Resulting image is published as `unillett/lumieres:stage-latest` on DockerHub.

### How to Check Build/Tag
Option A: GitHub Actions UI (preferred if available)
1) Open the repo Actions page and locate the latest workflow run for `dev`.
2) Wait for it to finish successfully before pulling on the VM.

Option B: DockerHub tag timestamp (quick check)
- The tag `stage-latest` has `last_pushed` and `last_updated` times in the DockerHub API.
- Example check from local shell:
  ```
  curl -fsSL "https://hub.docker.com/v2/repositories/unillett/lumieres/tags/?page_size=1&name=stage-latest"
  ```
  Look at `results[0].tag_last_pushed` and compare to your latest commit time.

### Deploy to Staging VM
Target: https://plt-tst-2.unil.ch (host alias: `plett-stage`)
```
ssh plett-stage
cd /var/www/lumieres2
docker compose -f docker-compose.staging.yml pull web
docker compose -f docker-compose.staging.yml up -d --force-recreate web
```

### Static Files (Required After Web Update)
If logos or CSS don’t change after a deploy, run collectstatic:
```
ssh plett-stage
cd /var/www/lumieres2
docker compose -f docker-compose.staging.yml exec -T web python manage.py collectstatic --noinput
```
Then hard refresh the browser (Ctrl/Cmd+Shift+R).

### Quick Sanity Checks
- Footer logos updated and correct links.
- “Designed by” text colors correct (white + orange).
- Home page renders CSS and images.

## Preflight (No Downtime)
1) Confirm production image tags/digests on DockerHub.
2) Prepare new compose files and env on the VM (no service start yet):
   - Canonical prod compose is the base + override pair:
     - Base template in repo: `docker-compose.prod.base.yml`
     - Override in repo: `docker-compose.prod.yml`
   - On the VM, either:
     - Copy `docker-compose.prod.base.yml` to `/u01/projects/dockerized/lumieres2-prod/docker-compose.yml` and keep `docker-compose.prod.yml` alongside it, or
     - Keep both filenames and set `COMPOSE_FILE=docker-compose.prod.base.yml:docker-compose.prod.yml`.
   - The base mirrors staging (`web` + `db` + `solr`); the override pins the prod image.
   - `/u01/projects/dockerized/lumieres2-prod/.env` (or `COMPOSE_FILE`) should reference both files.
3) Ensure bind mounts exist:
   - /u01/projects/dockerized/media (reuse)
   - /u01/projects/dockerized/lumieres2-prod/logging
   - /u01/projects/dockerized/lumieres2-prod/static
   - /u01/projects/dockerized/lumieres2-prod/solr (config + data)

## Maintenance Window Plan

### Pre-cutover Checklist (Safety)
- Confirm legacy stack is stopped before starting new `web`/`solr` to avoid port and Traefik conflicts.
- From `/u01/projects/dockerized/lumieres2-prod`, verify compose project and volumes:
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml ps`
  - `docker volume ls | grep lumieres-prod`
- Confirm new data paths exist and are writable:
  - `/u01/projects/dockerized/media`
  - `/u01/projects/dockerized/lumieres2-prod/{static,logging}`

### 1) Disable Monitoring
- Pause Uptime Kuma check for https://lumieres.unil.ch

### 2) Enable Maintenance Page
Use a temporary nginx container with the same Traefik Host rule:
1) Stop legacy app container (keep db/solr running for now).
2) Start maintenance container with label Host:lumieres.unil.ch
   Example:
   ```bash
   docker run -d --name lumieres-maintenance \
     --label traefik.enable=true \
     --label traefik.frontend.rule=Host:lumieres.unil.ch \
     --label traefik.port=80 \
     -v /u01/projects/dockerized/lumieres2-prod/maintenance:/usr/share/nginx/html:ro \
     nginx:alpine
   ```

### 3) Backup Legacy DB
1) Dump from legacy mysql:5.5 container.
2) Copy dump off-VM (and keep one local copy on VM).

### 4) Restore into New DB
1) Start new MySQL container in lumieres2-prod.
2) Import dump.
3) Apply schema fixes from descr/deployment.md (legacy dump normalization).
4) Verify schema (facsimile_iiif_url, facsimile_start_canvas, etc).

### 5) Start New Stack
1) Start Solr 8 container (new configset).
2) Start new app container.
3) Run collectstatic (host bind mount).
4) Run sync_status_roles --apply.
5) Rebuild search index (rebuild_index).

### 6) Cutover
1) Stop maintenance container.
2) Ensure new app container has Traefik Host:lumieres.unil.ch labels.
3) Verify TLS and routing.

### 7) Post-Deploy Checks
- Home page, transcription display, search, facsimile viewer.
- Check logs for errors.
- Re-enable Uptime Kuma.

## Rollback Plan
1) Stop new app container (leave DB/Solr for investigation).
2) Start legacy app container with Host:lumieres.unil.ch labels.
3) Remove/stop maintenance container if still running.
4) Validate site is back.

## Notes / Assumptions
- Traefik v1.7 stays as-is; routing is controlled by container labels.
- Legacy DB is MySQL 5.5 and must be migrated to MySQL 9.3 for Django 5.
- Media files stay at /u01/projects/dockerized/media.
- New stack uses DockerHub image (prod tag or digest).

## Resolved Decisions
- **Solr configset path**: copy repo `solr/configsets/lumieres` to
  `/u01/projects/dockerized/lumieres2-prod/solr/configsets/lumieres`.
  Core name stays `lumieres`, created via
  `solr-precreate lumieres /var/solr/configsets/lumieres`.
- **Maintenance page**: use a temporary `nginx:alpine` container with Traefik v1.7
  labels (`Host:lumieres.unil.ch`) and a bind-mount to a simple static
  maintenance page directory.
- **HTTP->HTTPS**: Traefik v1.7 uses a file provider config at
  `/u01/projects/dockerized/proxy_v1file/traefik.toml`. Add a frontend redirect
  to enforce HTTPS without `:443` in the Location header:
  ```
  [frontends.lumieres.redirect]
    regex = "^http://(.*)"
    replacement = "https://$1"
    permanent = true
  ```

## Release Pin (Current)
- Image tag: `unillett/lumieres:v2026.01.27`

## Deployment Record (2026-01-27)
Actions performed for prod update:
- Merged `dev` into `master`, pushed `master`.
- Created and pushed release tag `v2026.01.27`.
- Pulled `unillett/lumieres:v2026.01.27` on prod and recreated `web`.
- Ran `collectstatic` on prod.
- Pinned `LUMIERES_IMAGE` in `/u01/projects/dockerized/lumieres2-prod/.env` to `unillett/lumieres:v2026.01.27`.
Verification checklist:
- Footer UNIL logo updated + link to https://www.unil.ch/lettres.
- “Designed by” white + “Innovagency.ch” orange.

## Postmortem (2026-01-21)
Observed issues and fixes during first prod cutover to Django 5:
- Static/media initially missing: Django does not serve static in prod; added a small `nginx:alpine` front container (Traefik v1.7 on bridge) to serve `/static/`, `/media/`, `/user-media/`, and proxy `/` to `web:8000`.
- Thumbnails missing on `/actualites/`: `MEDIA_ROOT` is `/app/app/media`; mount must be `/u01/projects/dockerized/media:/app/app/media` in the web service (previous `/app/media` mount caused FileNotFoundError).
- Thumbnail cache writes blocked until media cache permissions fixed; ensure `/u01/projects/dockerized/media/cache` is writable (g+rwX with setgid or 2775).
- `prod-latest` tag did not exist on DockerHub; pin to the release tag (`v2026.01.21`) to avoid pull failures.
- Solr 8 required Log4j overrides; mount the 2.17.2 jars into `/opt/solr/server/lib/ext/` (core, api, slf4j-impl, 1.2-api, web).
- Traefik HTTP redirects were applied via file provider config (see above), not
  the global entrypoint redirect.

Action items for next deploy:
- Bake the front nginx service into the prod compose files (or document the runtime `docker run` + `docker network connect bridge` step).
- Keep the web media mount aligned with `MEDIA_ROOT` and validate `/actualites/` renders `<img>` and `/media/cache/...` returns 200.
- Confirm the prod tag exists before recreating containers (avoid `prod-latest`).
