# clean.mk: cleanup recipes.
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: clean clean/pyc clean/tests clean/build clean/caches clean/venv clean/uv-cache

clean:  ## Clean the project (everything except venv and uv cache)
clean: clean/build clean/pyc clean/tests clean/caches docs/clean

clean/pyc:  ## Remove Python file artifacts
	@echo "Cleaning up Python artifacts..."
	find . -name '*.pyc' -not -path './.venv/*' -exec rm -f {} +
	find . -name '*.pyo' -not -path './.venv/*' -exec rm -f {} +
	find . -name '*~' -not -path './.venv/*' -exec rm -f {} +
	find . -name '__pycache__' -not -path './.venv/*' -exec rm -fr {} +

clean/tests:  ## Remove tests and coverage artifacts
	@echo "Cleaning up test and coverage artifacts..."
	$(RM) .tox/
	$(RM) .coverage
	$(RM) htmlcov/
	find . -name '.pytest_cache' -not -path './.venv/*' -exec rm -fr {} +

clean/build:  ## Remove build artifacts
	@echo "Cleaning up build artifacts..."
	$(RM) build/
	$(RM) dist/
	$(RM) .eggs/
	find . -name '*.egg-info' -not -path './.venv/*' -exec rm -fr {} +
	find . -name '*.egg' -not -path './.venv/*' -exec rm -f {} +

clean/caches:  ## Remove tool caches
	@echo "Cleaning up caches..."
	$(RM) .cache/
	$(RM) .mypy_cache/
	$(RM) .pytest_cache/
	$(RM) .ruff_cache/

clean/venv:  ## Remove the local virtualenv (re-run `make dev/install`)
	@echo "Removing .venv..."
	$(RM) .venv

clean/uv-cache:  ## Remove the uv global cache
	@echo "Pruning uv cache..."
	uv cache prune
