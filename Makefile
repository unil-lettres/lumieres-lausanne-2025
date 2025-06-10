# Makefile for the Lumieres Lausanne project
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.DEFAULT_GOAL 	:= all


ifeq ($(OS), Windows_NT)
	WEB_BROWSER = powershell -Command Start-Process
	RM			= rm -Force -Path
	CP			= copy
	TOUCH		= New-Item -type file
	MKDIR		= New-Item -type directory
else
	WEB_BROWSER = open
	RM			= rm -rf
	CP			= cp -r
	TOUCH		= touch
	MKDIR		= mkdir -p
endif

MAKE_SUB		= ./make
APP_PATH		= ./app

# Helper functions
include $(MAKE_SUB)/helpers.mk

# Dev part
include $(MAKE_SUB)/dev.mk

# Docker Compose part
SERVICES ?=
include $(MAKE_SUB)/docker-compose.mk

# Cleaning part
include $(MAKE_SUB)/clean.mk

# Docs part
include $(MAKE_SUB)/docs.mk

# Migration part
include $(MAKE_SUB)/db.mk


# Recipes =====================================================================

# TODO: Improve help messages -issue #10
help:  ## Print the help
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)