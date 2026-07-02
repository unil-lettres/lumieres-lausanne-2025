# docs.mk: documentation generation (mkdocs via uv).
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: docs/build docs/serve docs/clean

docs/build:  ## Build the documentation site
	uv run mkdocs build

docs/serve:  ## Serve the documentation locally (auto-reload)
	uv run mkdocs serve

docs/clean:  ## Remove the built documentation
	$(RM) site
