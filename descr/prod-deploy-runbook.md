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

## Release Pin (Current)
- Image tag: `unillett/lumieres:v2026.01.21`
- amd64 digest: `sha256:aea53e1a06c8e9302a923f6457cf4e11573f3bfac3533fb9dde03d0176027084`
- arm64 digest: `sha256:5b15aa4308316c27277923b024b79f2838d38eca82eb3340d44c32c087664ac9`
