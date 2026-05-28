# docker-compose.mk: low-level wrappers around `docker compose`.
#
# COMPOSE points to the dev stack (main file + dev override with watch).
# COMPOSE_BASE only loads the main file (use it for prod-like local runs).

COMPOSE_BASE = docker compose -f docker-compose.yml
COMPOSE      = $(COMPOSE_BASE) -f docker/docker-compose.dev.yml

SERVICES ?=

.PHONY: docker/compose/up docker/compose/down docker/compose/start docker/compose/stop
.PHONY: docker/compose/restart docker/compose/logs docker/compose/build docker/compose/watch
.PHONY: docker/compose/ps docker/compose/config

docker/compose/up:  ## Bring up the dev stack (SERVICES=... to scope)
	$(COMPOSE) up -d $(SERVICES)

docker/compose/down:  ## Bring down the dev stack
	$(COMPOSE) down $(SERVICES)

docker/compose/start:  ## Start existing containers
	$(COMPOSE) start $(SERVICES)

docker/compose/stop:  ## Stop containers without removing
	$(COMPOSE) stop $(SERVICES)

docker/compose/restart:  ## Restart containers
	$(COMPOSE) restart $(SERVICES)

docker/compose/logs:  ## Follow logs (SERVICES=app to scope)
	$(COMPOSE) logs -f $(SERVICES)

docker/compose/build:  ## Build images
	$(COMPOSE) build $(SERVICES)

docker/compose/watch:  ## Run with develop.watch (hot reload)
	$(COMPOSE) watch

docker/compose/ps:  ## List running services
	$(COMPOSE) ps

docker/compose/config:  ## Show the merged compose configuration
	$(COMPOSE) config
