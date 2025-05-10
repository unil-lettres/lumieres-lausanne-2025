# Makefile for the Lumieres Lausanne project
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.DEFAULT_GOAL := all


ifeq ($(OS), Windows_NT)
	WEB_BROWSER = powershell -Command Start-Process
	RM			= rm -Force -Path
	CP			= copy
else
	WEB_BROWSER = open
	RM			= rm -rf
	CP			= cp -r
endif

MAKE_SUB		= ./make

# Dev part
include $(MAKE_SUB)/dev.mk

# Docker Compose part
SERVICES ?=
include $(MAKE_SUB)/docker-compose.mk

# Cleaning part
include $(MAKE_SUB)/clean.mk