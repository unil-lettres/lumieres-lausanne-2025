# Makefile for the Lumieres Lausanne project
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.DEFAULT_GOAL := help

ifeq ($(OS), Windows_NT)
	PWSH        = powershell -Command
	WEB_BROWSER = powershell -Command Start-Process
	RM          = $(PWSH) rm -Force -Path
	CP          = $(PWSH) Copy-Item -Recurse -Force
	TOUCH       = $(PWSH) New-Item -type file
	MKDIR       = $(PWSH) New-Item -type directory
else
	WEB_BROWSER = open
	RM          = rm -rf
	CP          = cp -r
	TOUCH       = touch
	MKDIR       = mkdir -p
endif

MAKE_SUB = ./make
APP_PATH = ./app

include $(MAKE_SUB)/clean.mk
include $(MAKE_SUB)/db.mk
include $(MAKE_SUB)/dev.mk
include $(MAKE_SUB)/docs.mk
include $(MAKE_SUB)/helpers.mk
include $(MAKE_SUB)/lint.mk
include $(MAKE_SUB)/tests.mk
include $(MAKE_SUB)/v2024.mk

# Recipes =====================================================================

help:  ## Print the help
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)
