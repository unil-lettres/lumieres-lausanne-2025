# lint.mk: linting, formatting, and type-checking (ruff + ty, via uv).
#
# Ruff replaces black + isort + flake8 (and its plugins); ty replaces mypy.
# Config lives in pyproject.toml ([tool.ruff*] and [tool.ty*]).
#
# Recipes operate on the application source ($(LINT_PATHS)); extend the list
# to cover tests/ and tools/ once they are clean.
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

LINT_PATHS ?= app

RUFF = uv run ruff
TY   = uv run ty

.PHONY: lint lint/fix format format/check typecheck check

lint:  ## Report lint errors (ruff check, no changes)
	$(RUFF) check $(LINT_PATHS)

lint/fix:  ## Apply safe lint fixes (ruff check --fix)
	$(RUFF) check --fix $(LINT_PATHS)

format:  ## Format the code in place (ruff format)
	$(RUFF) format $(LINT_PATHS)

format/check:  ## Check formatting without writing (ruff format --check)
	$(RUFF) format --check $(LINT_PATHS)

typecheck:  ## Run the static type checker (ty check, reads [tool.ty])
	$(TY) check

check:  ## CI-style gate: lint + format check + type check (no mutation)
check: lint format/check typecheck
