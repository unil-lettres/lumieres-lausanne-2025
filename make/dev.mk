# dev.mk is sub makefile about dev receipes
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: dev/init
dev/init:  ## Initialize the development environment
	$(CP) .env.template .env

.PHONY: dev/install
dev/install:  ## Install dependencies
dev/install: app
	pip install -e .[dev,tools,docs]

$(APP_PATH):  ## Create a app basics
	$(MKDIR) $(APP_PATH)

$(APP_PATH)/__init__.py: app
	$(TOUCH) $(APP_PATH)/__init__.py