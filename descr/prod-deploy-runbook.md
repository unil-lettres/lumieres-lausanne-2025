# Production Deployment Runbook

Status: active runbook
Audience: ops/dev (manual execution)
Scope: routine production releases for the Dockerized Lumieres stack on lumieres-srv2.unil.ch, plus archived notes from the initial migration period

## Current Production State
- Production cutover to the Dockerized Django 5 stack is complete.
- Production DB schema is stabilized; routine releases do not require legacy DB import or schema normalization.
- Standard production updates are image-based redeploys of the existing compose project under `/u01/projects/dockerized/lumieres2-prod`.
- Prod `.env` sets Compose defaults so commands can be run without repeated `-f` flags:
  - `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`
  - `COMPOSE_PROJECT_NAME=lumieres-prod`
  - `LUMIERES_IMAGE=unillett/lumieres:vYYYY.MM.DD`

## ARIA Lease / Project Ownership
- `2026-05-20`: Helpdesk/DCSR corrected the ARIA deployment `lumieres-srv2`
  from project `fac-hec` to `LTR` and updated `jganivet` permissions so the
  deployment is visible in the new project.
- The same intervention extended the ARIA lease by 12 months.
- Ticket reference: UNIL Helpdesk `#10886806` (Arnaud Burkhalter).
- At the next renewal, verify the deployment is still under `LTR` and use the
  Faculté des lettres budget unit, not a HEC unit.

## Standard Release Procedure
1. Merge `dev` into `master` and push `master`.
2. Create and push the release tag `vYYYY.MM.DD`.
3. Verify the tag image exists on DockerHub.
4. On prod, create rollback assets in `/u01/projects/dockerized/lumieres2-prod/backups/<timestamp>/`:
   - DB dump
   - compose/env snapshot
   - pre-change `.env` backup
5. Update `.env` to pin `LUMIERES_IMAGE` to the release tag.
6. Verify plain Compose resolves to the prod override and pinned image:
   ```bash
   docker compose config --images
   ```
7. Redeploy `web` only:
   ```bash
   docker compose pull web
   docker compose up -d --no-deps web
   ```
8. Run post-deploy tasks:
   ```bash
   docker compose exec -T web python manage.py collectstatic --noinput
   docker compose exec -T web python manage.py sync_status_roles --apply
   docker compose exec -T web python manage.py update_index
   ```
9. Validate:
   - `docker compose ps`
   - `docker inspect lumieres-prod-web-1 --format '{{.Config.Image}}|{{index .Config.Labels "org.opencontainers.image.revision"}}|{{index .Config.Labels "org.opencontainers.image.version"}}'`
   - `curl -I https://lumieres.unil.ch/`
   - `curl -I https://lumieres.unil.ch/projets/`
   - targeted UI smoke checks when the release affects user-visible behavior
10. Guardrail:
   - never leave prod pinned to `latest`; keep `LUMIERES_IMAGE` on an explicit release tag so a restart/recreate cannot silently fall back to an ambiguous image target.

## Archived Initial Migration Plan
The sections below are retained as historical reference for the January-February 2026 migration/cutover. They are not the routine procedure for normal production releases anymore.

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
   - Canonical prod compose is `docker-compose.yml` plus `docker-compose.prod.yml` on the VM.
   - The VM `docker-compose.yml` was originally copied from the repo base template (`docker-compose.prod.base.yml`).
   - Keep `docker-compose.prod.yml` alongside it as the prod override.
   - The base mirrors staging (`web` + `db` + `solr`); the override pins the prod image.
   - `/u01/projects/dockerized/lumieres2-prod/.env` should set `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`.
3) Ensure bind mounts exist:
   - /u01/projects/dockerized/media (reuse)
   - /u01/projects/dockerized/lumieres2-prod/logging
   - /u01/projects/dockerized/lumieres2-prod/static
   - /u01/projects/dockerized/lumieres2-prod/solr (config + data)

## Maintenance Window Plan

### Pre-cutover Checklist (Safety)
- Confirm legacy stack is stopped before starting new `web`/`solr` to avoid port and Traefik conflicts.
- From `/u01/projects/dockerized/lumieres2-prod`, verify compose project and volumes:
  - `docker compose ps`
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
- Legacy DB migration was part of the initial cutover and is retained here as historical context only.
- Media files stay at /u01/projects/dockerized/media.
- New stack uses DockerHub image (prod tag or digest).

## Resolved Decisions
- **Solr configset path**: copy repo `settings/solr/configsets/lumieres` to
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
- Image tag: `unillett/lumieres:v2026.05.05`

## Compose Default Simplification (2026-05-05)
- Prod `.env` now carries the Compose file selection and project name:
  - `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`
  - `COMPOSE_PROJECT_NAME=lumieres-prod`
  - `LUMIERES_IMAGE=unillett/lumieres:v2026.05.05`
- This removes the old footgun where plain `docker compose up -d` could read only `docker-compose.yml` and select the legacy `v2026.01.21` image.
- Validation after the change:
  - `docker compose config --images` resolved `web` to `unillett/lumieres:v2026.05.05`
  - a second plain `docker compose up -d` was a no-op for running containers
  - `manage.py check` passed
  - public checks for `/`, `/projets/`, `/chercher/person/list`, and `/fiches/trans/1288/` returned `HTTP 200`
  - transcription `1288` embedded `308` IIIF tile sources

The deployment records below keep the exact commands used at the time. For new production work, use the standard procedure above.

## Deployment Record (2026-03-19)
Actions performed for prod update:
- Confirmed incident: prod `web` was running `unillett/lumieres:v2026.01.21` while `.env` had drifted to `LUMIERES_IMAGE=unillett/lumieres:latest`.
- Created and pushed release tag `v2026.03.19` from `master` commit `aff6006`.
- Verified `docker-prod` completion for tag push and DockerHub publication for `unillett/lumieres:v2026.03.19`.
- On prod (`/u01/projects/dockerized/lumieres2-prod`), created rollback assets before redeploy:
  - Backup folder: `backups/20260319_114450/`
  - Full DB dump: `backups/20260319_114450/lumieres-prod.sql`
  - SHA256: `e78ffe478b3058e5cbec04f131d85ed71ffb31a89f7ce20f297c4cc6055fcc00`
  - Compose/env snapshot copied to backup folder.
- Updated `.env` pin:
  - `LUMIERES_IMAGE=unillett/lumieres:v2026.03.19`
- Redeployed `web` only:
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml pull web`
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps web`
- Ran post-deploy tasks:
  - `collectstatic --noinput` (`1420` static files copied)
  - `sync_status_roles --apply`
  - `update_index`
- Validation:
  - `docker compose ps` shows `web` on `unillett/lumieres:v2026.03.19`
  - `docker inspect lumieres-prod-web-1` shows revision `aff6006` and version `v2026.03.19`
  - `curl -I https://lumieres.unil.ch/` returned `HTTP/2 200`
  - `curl -I https://lumieres.unil.ch/projets/` returned `HTTP/2 200`

Incident note / root cause:
- A prod restart/recreate surfaced deployment drift: the live `web` container came back on old image `v2026.01.21` while `.env` no longer followed the explicit release-tag workflow.
- Forensics on 2026-03-19 identified the specific trigger chain:
  - host reboot at `2026-03-19 05:09 CET`
  - two `lmradm` crontab `@reboot` entries ran plain `docker compose up -d` in `/u01/projects/dockerized/lumieres2-prod`
  - plain compose resolution in that directory used the legacy `docker-compose.yml` hard pin `unillett/lumieres:v2026.01.21` because `docker-compose.prod.yml` was not included
- Root cause was incorrect reboot automation plus prior drift away from the explicit release-tag workflow.
- Preventive rule: after every prod deploy, verify both the compose-reported image and the container label metadata, and keep `.env` pinned to a release tag rather than `latest`.
- Remediation applied on 2026-03-19:
  - removed both redundant `@reboot ... docker compose up -d` cron entries for `lmradm`
  - retained Docker restart policy `unless-stopped` as the canonical reboot behavior for prod services

## Deployment Record (2026-02-27)
Actions performed for prod update:
- Merged `dev` into `master`, pushed `master` (`61de939`).
- Created and pushed release tag `v2026.02.27`.
- Verified `docker-prod` completion for `master` push and tag push.
- Verified DockerHub tag availability for `unillett/lumieres:v2026.02.27`.
- On prod (`/u01/projects/dockerized/lumieres2-prod`), created rollback assets before redeploy:
  - Backup folder: `backups/20260227_153309/`
  - Compose/env snapshot copied to backup folder.
  - `.env` backup: `.env.bak-20260227_153309-before-v2026.02.27`
- Updated `.env` pin:
  - `LUMIERES_IMAGE=unillett/lumieres:v2026.02.27`
- Redeployed `web` only:
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml pull web`
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps web`
- Ran post-deploy tasks:
  - `collectstatic --noinput` (`1420` static files copied)
  - `sync_status_roles --apply`
  - `update_index`
- Validation:
  - `docker compose ps` shows `web` on `unillett/lumieres:v2026.02.27`
  - `curl -I https://lumieres.unil.ch/` returned `HTTP/2 200`
  - `curl -I https://lumieres.unil.ch/projets/` returned `HTTP/2 200`

Process notes (to smooth next deploy):
- Prod host uses `docker-compose.yml` + `docker-compose.prod.yml`; since 2026-05-05, `.env` sets `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`, so plain `docker compose ...` from `/u01/projects/dockerized/lumieres2-prod` is the current procedure.
- Pushing `master` then pushing a release tag can trigger two `docker-prod` runs for the same SHA.
  For release deployments, wait for the tag-triggered run and verify the release tag exists on DockerHub before pulling on prod.

## Deployment Record (2026-02-20)
Actions performed for prod update:
- Merged `dev` into `master`, pushed `master`.
- Created and pushed release tag `v2026.02.20`.
- Verified DockerHub tag availability for `unillett/lumieres:v2026.02.20`.
- On prod (`/u01/projects/dockerized/lumieres2-prod`), created rollback assets before DB writes:
  - Backup folder: `backups/20260220_135841/`
  - Full DB dump: `backups/20260220_135841/lumieres-prod.sql`
  - SHA256: `430ff474255526ef0964b8ab12c288ee408b06ef3644472da069a30e6deb962d`
  - Compose/env snapshot copied to same backup folder
  - `.env` pre-pin backup: `.env.bak-20260220_135841-before-tag-pin`
- Applied manual DB schema changes (no Django migrations):
  - Added nullable columns on `fiches_transcription`:
    - `published_date`
    - `published_by_id`
    - `modified_date`
    - `modified_by_id`
  - Created fast rollback table: `backup_transcription_pub_20260220_135841` (`1360` rows)
  - Ran backfill from `fiches_activitylog`:
    - `total_transcriptions=1360`
    - `published_filled=1125`
    - `modified_filled=1359`
- Corrected image pin to release tag in `.env`:
  - `LUMIERES_IMAGE=unillett/lumieres:v2026.02.20`
  - Redeployed `web` with `docker compose ... up -d --no-deps web`
- Ran post-deploy tasks:
  - `collectstatic --noinput` (`1420` static files copied)
  - `sync_status_roles --apply`
  - `update_index`
- Validation:
  - `docker compose ps` shows `web` on `unillett/lumieres:v2026.02.20`
  - `curl -I https://lumieres.unil.ch/` returned `HTTP/2 200`
  - Manual UI smoke checks to be completed by product team (transcription publication fields + search paths).

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
