# tests.mk: backend (pytest) test recipes.
#
# The backend suite lives in tests/backend and uses the in-memory SQLite test
# settings (lumieres_project.settings_test, via pyproject addopts), so it needs
# no MySQL/Solr and runs identically on the host or in the app container.
#
# Recipe prefixes:
#   dev/tests/<cmd>        run inside the app container (stack must be up)
#   dev/tests/local/<cmd>  run on the host via `uv run` (no services needed)
#
# PYTEST_ARGS=...  is forwarded to pytest (e.g. PYTEST_ARGS="-k biblio -vv").
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

PYTEST_ARGS ?=

# Reuse COMPOSE from dev.mk; run from /app without a TTY so it works in CI too.
DOCKER_PYTEST = $(COMPOSE) exec -T -w /app app pytest
LOCAL_PYTEST  = uv run pytest

# Coverage HTML is written under tests/reports (bind-mounted), so the container
# run is viewable on the host at tests/reports/htmlcov/index.html.
COV_HTML_DIR = tests/reports/htmlcov

.PHONY: dev/tests/run dev/tests/cov dev/tests/html
.PHONY: dev/tests/local dev/tests/local/cov dev/tests/local/html

# Container recipes ===========================================================

dev/tests/run:  ## Run the backend test suite in the app container (PYTEST_ARGS=...)
	$(DOCKER_PYTEST) $(PYTEST_ARGS)

dev/tests/cov:  ## Backend tests with a terminal coverage report (container)
	$(DOCKER_PYTEST) --cov --cov-report=term-missing $(PYTEST_ARGS)

dev/tests/html:  ## Backend tests with an HTML coverage report (container)
	$(DOCKER_PYTEST) --cov --cov-report=term-missing --cov-report=html:$(COV_HTML_DIR) $(PYTEST_ARGS)
	@echo "HTML coverage report: $(COV_HTML_DIR)/index.html"

# Host recipes (uv) ===========================================================

dev/tests/local:  ## Run the backend test suite on the host via uv (no services)
	$(LOCAL_PYTEST) $(PYTEST_ARGS)

dev/tests/local/cov:  ## Host backend tests with a terminal coverage report
	$(LOCAL_PYTEST) --cov --cov-report=term-missing $(PYTEST_ARGS)

dev/tests/local/html:  ## Host backend tests with an HTML coverage report (-> htmlcov/)
	$(LOCAL_PYTEST) --cov --cov-report=term-missing --cov-report=html $(PYTEST_ARGS)
	@echo "HTML coverage report: htmlcov/index.html"

# Misc ========================================================================

.PHONY: test/dockerignore
test/dockerignore:  ## Testing dockerignore
	rsync -avn . /tmp --exclude-from .dockerignore
