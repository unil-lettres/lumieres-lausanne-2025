# Lumières Lausanne

Lumières Lausanne is a Django application for publishing and editing scholarly
data about the Swiss Enlightenment: bibliographic records, biographies,
transcriptions, projects, news, media, and search.

This public repository contains the application source, development containers,
tests, and user/developer documentation. Internal operational documentation,
environment inventories, incident reports, deployment runbooks, and project
handoff notes are maintained outside the public repository.

## Local development

Requirements:

- Docker Desktop 4.x+ or Docker Engine with Compose V2;
- Git.

```bash
git clone https://github.com/unil-lettres/lumieres-lausanne-2025.git
cd lumieres-lausanne-2025
cp .env.template .env
docker compose up -d
docker compose ps
```

The local application is available at `http://localhost:8000/` by default.

## Tests and documentation

```bash
docker compose exec -T app pytest
mkdocs serve
```

Public documentation lives under [`docs/`](docs/).

## License and contact

Copyright University of Lausanne.

Lumières Lausanne is free software distributed under the GNU Affero General
Public License, version 3 or later. For project questions, open a GitHub issue.
