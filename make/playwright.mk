#
#  Copyright (C) 2010-2025 Université de Lausanne, RISET
#  < http://www.unil.ch/riset/ >
#
#  This file is part of Lumières.Lausanne.
#  Lumières.Lausanne is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Lumières.Lausanne is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  This copyright notice MUST APPEAR in all copies of the file.
#

.PHONY: test-pw-install test-pw-chrome test-pw-firefox test-pw-webkit test-pw-all test-pw-headed test-pw-debug test-pw-ui test-pw-mobile

# Playwright test commands

test-pw-install: ## Install Playwright dependencies and browsers
	pip install -e ".[test]"
	playwright install

test-pw-chrome: ## Run tests on Chrome only
	pytest app/fiches/tests/test_playwright_facsimile.py -k "chromium" -v --tb=short

test-pw-firefox: ## Run tests on Firefox only
	pytest app/fiches/tests/test_playwright_facsimile.py -k "firefox" -v --tb=short

test-pw-webkit: ## Run tests on Safari (WebKit) only
	pytest app/fiches/tests/test_playwright_facsimile.py -k "webkit" -v --tb=short

test-pw-all: ## Run all Playwright tests on all browsers (Chrome, Firefox, Safari)
	pytest app/fiches/tests/test_playwright_facsimile.py -v --tb=short

test-pw-headed: ## Run all tests with visible browser windows
	pytest app/fiches/tests/test_playwright_facsimile.py -v --tb=short --headed

test-pw-debug: ## Run tests in debug mode (interactive pauses)
	PWDEBUG=1 pytest app/fiches/tests/test_playwright_facsimile.py -v --tb=short

test-pw-ui: ## Run tests in Playwright UI mode (interactive)
	pytest app/fiches/tests/test_playwright_facsimile.py --ui

test-pw-mobile: ## Run mobile responsive tests
	pytest app/fiches/tests/test_playwright_facsimile.py -k "320px or 768px" -v --tb=short

test-pw-phase2: ## Run Phase 2 Navigation Bar tests only
	pytest app/fiches/tests/test_playwright_facsimile.py::TestPhase2NavigationBar -v --tb=short

test-pw-phase3: ## Run Phase 3 Mode Conditional Logic tests only
	pytest app/fiches/tests/test_playwright_facsimile.py::TestPhase3ModeConditionalLogic -v --tb=short

test-pw-phase4: ## Run Phase 4 Options Persistence tests only
	pytest app/fiches/tests/test_playwright_facsimile.py::TestPhase4OptionsPersistence -v --tb=short

test-pw-a11y: ## Run Accessibility tests only
	pytest app/fiches/tests/test_playwright_facsimile.py::TestAccessibility -v --tb=short

test-pw-responsive: ## Run Responsive Design tests only
	pytest app/fiches/tests/test_playwright_facsimile.py::TestResponsive -v --tb=short

test-pw-compat: ## Run Browser Compatibility tests
	pytest app/fiches/tests/test_playwright_facsimile.py -k "chromium or firefox or webkit" -v --tb=short

test-pw-collect: ## List all available tests (no execution)
	pytest app/fiches/tests/test_playwright_facsimile.py --collect-only -q

test-pw-clean: ## Clean test results and cache
	rm -rf test-results/ .pytest_cache/ .pw/ */__pycache__/

test-pw-failed: ## Run only previously failed tests
	pytest app/fiches/tests/test_playwright_facsimile.py --lf -v --tb=short

test-pw-fast: ## Run tests with minimal output (fast feedback)
	pytest app/fiches/tests/test_playwright_facsimile.py -q
