# dev.mk is sub makefile about dev receipes
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: dev/init
dev/init:  ## Initialize the development environment
	$(CP) .env.template .env

.PHONY: dev/install
dev/install:  ## Install dependencies
	pip install -e .[dev,tools]