# dev.mk is sub makefile about dev receipes
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: dev/init
dev/init:  ## Initialize the development environment
	$(CP) .env.template .env

.PHONY: dev/install
dev/install:  ## Install dependencies
	pip install -e .[dev,tools,docs]
	
# Install the latest Node.js using nvm
.PHONY: dev/node-install
dev/node-install:
	# Install nvm if not present
	if ! command -v nvm >/dev/null 2>&1; then \
	  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash; \
	  export NVM_DIR="$$HOME/.nvm"; \
	  [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh"; \
	fi; \
	export NVM_DIR="$$HOME/.nvm"; \
	[ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh"; \
	nvm install node; \
	nvm use node; \
	node -v; \
	npm -v

$(APP_PATH):  ## Create a app basics
	$(MKDIR) $(APP_PATH)

$(APP_PATH)/__init__.py: app
	$(TOUCH) $(APP_PATH)/__init__.py

.PHONY: dev/up
dev/up:  ## Prepare and Start the development environment
dev/up: SERVICES=db phpmyadmin
dev/up: docker/compose/up

.PHONY: dev/down
dev/down:  ## Stop and Delete the development environment
dev/down: SERVICES=db phpmyadmin
dev/down: docker/compose/up

.PHONY: dev/start
dev/start:  ## Start the development environment
dev/start: SERVICES=db phpmyadmin
dev/start: docker/compose/start

.PHONY: dev/stop
dev/stop:  ## Stop the development environment
dev/stop: SERVICES=db phpmyadmin
dev/stop: docker/compose/stop

.PHONY: dev/restart
dev/restart:  ## Restart the development environment
dev/restart: SERVICES=db
dev/restart: phpmyadmin docker/compose/restart

.PHONY: dev/logs
dev/logs:  ## Show logs of the development environment
dev/logs: SERVICES=db phpmyadmin
dev/logs: docker/compose/logs

.PHONY: dev/runserver
dev/runserver:  ## Run the django dev server
	cd $(APP_PATH) && python manage.py runserver

.PHONY: dev/shell
dev/shell:  ## Open a shell with Djangop
	cd $(APP_PATH) && python manage.py shell

.PHONY: dev/createsuperuser
dev/createsuperuser:  ## Create a superuser for Django
	cd $(APP_PATH) && python manage.py createsuperuser