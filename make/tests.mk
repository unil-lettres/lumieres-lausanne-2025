# tests.mk is sub makefile for tests project recipes
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: test/dockerignore
test/dockerignore:  ## Testing dockerignore
	rsync -avn . /tmp --exclude-from .dockerignore
