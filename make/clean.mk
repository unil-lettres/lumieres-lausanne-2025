# clean.mk is sub makefile about cleaning commands.
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: clean
clean:  ## clean the project
clean: clean/build clean/pyc clean/tests clean/caches docs/clean

clean/pyc:  ## remove Python file artifacts
	@echo "Cleaning up Python artifacts..."
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.mypy_cache' -exec rm -fr {} +
	
.PHONY: clean/tests
clean/tests:  ## remove tests and coverage artifacts
	@echo "Cleaning up test and coverage artifacts..."
	$(RM) .tox/
	$(RM) .coverage
	$(RM) htmlcov/
	find . -name '.pytest_cache' -exec rm -fr {} +
	
.PHONY: clean/build
clean/build:  ## remove build artifacts
	@echo "Cleaning up build artifacts..."
	$(RM) build/
	$(RM) dist/
	$(RM) .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	
.PHONY: clean/caches
clean/caches:  ## remove caches
	@echo "Cleaning up caches..."
	$(RM) .cache/
	$(RM) .mypy_cache/
	$(RM) .pytest_cache/
	$(RM) .tox/
	$(RM) .coverage
	$(RM) htmlcov/
	$(RM) .ruff_cache/