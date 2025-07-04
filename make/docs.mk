# docs.mk is sub makefile abouty documentation generation.
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: docs/build
docs/build:  ## Building the documentation
	mkdocs build

.PHONY: docs/serve
docs/serve:  ## Serving the documentation
docs/serve: docs/build
	mkdocs serve

.PHONY: docs/clean
docs/clean:  ## Cleaning the documentation
	$(RM) site