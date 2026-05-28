# dev.mk: setup, stack lifecycle, and Django commands.
#
# Recipe prefixes:
#   dev/{init,install}            host-side setup
#   dev/{up,down,start,stop,...}  manage the dev docker stack
#   dev/local/<cmd>               run a command via `uv run` on the host
#   dev/docker/<cmd>              run a command inside the app container
#
# ARGS=...  is forwarded to underlying commands where it makes sense.

ARGS ?=

LOCAL_MANAGE  = uv run python $(APP_PATH)/manage.py
DOCKER_EXEC   = $(COMPOSE) exec app
DOCKER_MANAGE = $(DOCKER_EXEC) python manage.py

# Setup =======================================================================

.PHONY: dev/init dev/install

dev/init:  ## Copy .env.template to .env
	$(CP) .env.template .env

dev/install:  ## Install all deps locally with uv (main + dev + docs)
	uv sync --all-groups

# Stack lifecycle =============================================================

.PHONY: dev/up dev/down dev/start dev/stop dev/restart dev/logs dev/build dev/watch

dev/up:       docker/compose/up        ## Start the dev stack in background
dev/down:     docker/compose/down      ## Stop and remove the dev stack
dev/start:    docker/compose/start     ## Start existing containers
dev/stop:     docker/compose/stop      ## Stop containers without removing
dev/restart:  docker/compose/restart   ## Restart containers
dev/logs:     docker/compose/logs      ## Follow logs (SERVICES=app to scope)
dev/build:    docker/compose/build     ## Build the dev images
dev/watch:    docker/compose/watch     ## Start with hot reload (develop.watch)

# Local commands (uv run) =====================================================

.PHONY: dev/local/runserver dev/local/shell dev/local/createsuperuser
.PHONY: dev/local/makemigrations dev/local/migrate dev/local/showmigrations
.PHONY: dev/local/collectstatic dev/local/test dev/local/cov
.PHONY: dev/local/rebuild-index dev/local/import dev/local/thumbnail-cleanup
.PHONY: dev/local/manage

dev/local/runserver:  ## Run Django dev server on the host
	$(LOCAL_MANAGE) runserver 0.0.0.0:8000

dev/local/shell:  ## Open a Django shell on the host
	$(LOCAL_MANAGE) shell

dev/local/createsuperuser:  ## Create a Django superuser on the host
	$(LOCAL_MANAGE) createsuperuser

dev/local/makemigrations:  ## Make migrations on the host (ARGS=app_name)
	$(LOCAL_MANAGE) makemigrations $(ARGS)

dev/local/migrate:  ## Apply migrations on the host (ARGS=app_name)
	$(LOCAL_MANAGE) migrate $(ARGS)

dev/local/showmigrations:  ## Show migrations on the host (ARGS=app_name)
	$(LOCAL_MANAGE) showmigrations $(ARGS)

dev/local/collectstatic:  ## Collect static files on the host
	$(LOCAL_MANAGE) collectstatic --noinput

dev/local/test:  ## Run pytest on the host (ARGS=...)
	uv run pytest $(ARGS)

dev/local/cov:  ## Run pytest with coverage on the host
	uv run pytest --cov=app --cov-report=term-missing $(ARGS)

dev/local/rebuild-index:  ## Rebuild the Solr index from the host
	$(LOCAL_MANAGE) rebuild_index --noinput --verbosity 2

dev/local/import:  ## Import data into Django from the host (ARGS=...)
	$(LOCAL_MANAGE) import_database $(ARGS)

dev/local/thumbnail-cleanup:  ## Clean the thumbnail cache from the host
	$(LOCAL_MANAGE) thumbnail cleanup

dev/local/manage:  ## Run an arbitrary manage.py command on the host (ARGS=...)
	$(LOCAL_MANAGE) $(ARGS)

# Docker commands (compose exec) ==============================================

.PHONY: dev/docker/shell dev/docker/createsuperuser dev/docker/makemigrations
.PHONY: dev/docker/migrate dev/docker/showmigrations dev/docker/collectstatic
.PHONY: dev/docker/test dev/docker/rebuild-index dev/docker/import
.PHONY: dev/docker/thumbnail-cleanup dev/docker/manage dev/docker/exec dev/docker/bash

dev/docker/shell:  ## Open a Django shell in the container
	$(DOCKER_MANAGE) shell

dev/docker/createsuperuser:  ## Create a Django superuser in the container
	$(DOCKER_MANAGE) createsuperuser

dev/docker/makemigrations:  ## Make migrations in the container (ARGS=app_name)
	$(DOCKER_MANAGE) makemigrations $(ARGS)

dev/docker/migrate:  ## Apply migrations in the container (ARGS=app_name)
	$(DOCKER_MANAGE) migrate $(ARGS)

dev/docker/showmigrations:  ## Show migrations in the container (ARGS=app_name)
	$(DOCKER_MANAGE) showmigrations $(ARGS)

dev/docker/collectstatic:  ## Collect static files in the container
	$(DOCKER_MANAGE) collectstatic --noinput

dev/docker/test:  ## Run Django tests in the container (ARGS=...)
	$(DOCKER_MANAGE) test $(ARGS)

dev/docker/rebuild-index:  ## Rebuild the Solr index in the container
	$(DOCKER_MANAGE) rebuild_index --noinput --verbosity 2

dev/docker/import:  ## Import data into Django in the container (ARGS=...)
	$(DOCKER_MANAGE) import_database $(ARGS)

dev/docker/thumbnail-cleanup:  ## Clean the thumbnail cache in the container
	$(DOCKER_MANAGE) thumbnail cleanup

dev/docker/manage:  ## Run an arbitrary manage.py command in the container (ARGS=...)
	$(DOCKER_MANAGE) $(ARGS)

dev/docker/exec:  ## Run an arbitrary command in the app container (ARGS=...)
	$(DOCKER_EXEC) $(ARGS)

dev/docker/bash:  ## Open a bash shell in the app container
	$(DOCKER_EXEC) bash
