# Lumières Lausanne Backlog

## Future Analytics / Public Visit Audit Trail

Status: backlog item, no implementation yet  
Recorded: 2026-04-24  
Environment observed: production (`lumieres-srv2.unil.ch`)

### Current Findings
- The app has an authenticated editorial activity table (`fiches_activitylog`), but it is not a public visit analytics trail.
- Public request data currently exists in the `lumieres-prod-front-1` nginx container logs.
- The nginx access log is currently emitted through Docker's `json-file` log driver, not to a durable mounted `access.log`.
- The current `front` container was created on 2026-02-26, so existing raw visit data likely starts there and is tied to that container lifecycle.
- Traefik v1.7 access logging does not appear to be enabled; Traefik logs mostly contain proxy/error events.
- Static/media paths have `access_log off`, so asset hits are intentionally excluded.
- No Matomo, Plausible, GoAccess, AWStats, Umami, or similar analytics stack was found under `/u01/projects/dockerized`.

### Traffic Snapshot
Read-only aggregation of `lumieres-prod-front-1` logs on 2026-04-24 showed:

- Total nginx log lines since current front container creation: about `691,876`.
- Bot-like traffic by user-agent heuristic: about `514,168` requests, roughly 74%.
- Likely human or unknown traffic: about `177,708` requests, roughly 26%.
- Top automated/monitoring user agents included:
  - `SemrushBot`
  - `ClaudeBot`
  - `PetalBot`
  - `GPTBot`
  - `Uptime-Kuma`
  - `UptimeRobot`
  - `meta-externalagent`
  - `GoogleOther`
  - `Baiduspider`
  - `OAI-SearchBot`
  - `bingbot`

### Recommended Feature Direction
- Create a durable nginx access log bind mount, for example:
  - `/u01/projects/dockerized/lumieres2-prod/logging/access.log`
- Add log rotation and retention policy for raw access logs.
- Treat raw access logs as sensitive operational/audit data because they contain IP addresses and user agents.
- Generate scheduled reports from access logs rather than relying on ad hoc `docker logs` extraction.
- Produce two report levels:
  - raw audit CSV for authorized operators only
  - privacy-conscious analytics summary for stakeholders
- Include request classification in reports:
  - `monitoring`
  - `search_indexing`
  - `seo_or_scraper`
  - `ai_crawler`
  - `likely_human`
  - `unknown_suspicious`
- For "interesting human traffic", count only dynamic/content page `GET` requests with useful statuses, exclude known monitors/bots, and group visits by date plus an anonymized visitor key.

### Bot Mitigation Guidance
- Do not start with broad blocking; Lumières is a public academic site and legitimate search indexing has value.
- Consider mitigation only if bots cause load, scraping concerns, noisy analytics, excessive 404s, or log retention issues.
- Prefer staged controls:
  - publish or tune `robots.txt`
  - rate-limit abusive paths or IPs with nginx
  - block only clearly abusive user agents or request patterns after evidence
  - keep major search crawlers allowed unless there is a specific reason to restrict them

### Open Decisions
- Required retention period for raw logs.
- Whether IP addresses should be stored raw, truncated, hashed, or only retained in restricted audit exports.
- Who may receive raw audit data versus aggregated analytics.
- Whether the first implementation should be a simple CSV/GoAccess report or a dedicated analytics service.
