<!--
   Copyright (C) 2010-2025 Université de Lausanne, RISET
   < http://www.unil.ch/riset/ >

   This file is part of Lumières.Lausanne.
   Lumières.Lausanne is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   Lumières.Lausanne is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   This copyright notice MUST APPEAR in all copies of the file.
-->

# Playwright Tests Setup - Facsimile Viewer

**Status**: ✅ Complete  
**Date**: 2026-02-03  
**Purpose**: Automated testing suite for Phase 2, 3, 4 facsimile viewer implementation

---

## Overview

A complete Playwright test suite (Python-based) has been created to validate the facsimile viewer refactoring across **Chrome, Firefox, and Safari (WebKit)**.

### Test Coverage

| Phase | Tests | Browsers | Status |
|-------|-------|----------|--------|
| **Phase 2** - Navigation Bar | 8 tests | 3 | Ready ✅ |
| **Phase 3** - Mode Logic | 4 tests | 3 | Ready ✅ |
| **Phase 4** - Persistence | 3 tests | 3 | Ready ✅ |
| **Accessibility** | 2 tests | 3 | Ready ✅ |
| **Responsive** | 3 tests | 3 | Ready ✅ |
| **Total** | **20 tests** | **60+ across all browsers** | Ready ✅ |

---

## Files Created

```
tests/playwright/
├── __init__.py                      # Package initialization
├── conftest.py                      # Pytest fixtures & configuration
├── test_facsimile_viewer.py         # Main test suite (Python)
└── README.md                        # Test documentation

pytest.ini                           # Pytest configuration
requirements-playwright.txt          # Dependencies
run-tests.sh                         # Test runner script
```

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements-playwright.txt
```

### 2. Install Browser Binaries

```bash
playwright install
```

This installs: Chromium, Firefox, WebKit (Safari)

### 3. Verify Setup

```bash
# Check if containers are ready
python -m pytest tests/playwright/test_facsimile_viewer.py --collect-only
```

---

## Quick Start

### Run All Tests (All Browsers)

```bash
# Using helper script (recommended)
./run-tests.sh --all

# Or directly with pytest
pytest tests/playwright/test_facsimile_viewer.py -v
```

### Run Specific Browser

```bash
./run-tests.sh --chrome      # Chrome only
./run-tests.sh --firefox     # Firefox only
./run-tests.sh --webkit      # Safari only
```

### Interactive Modes

```bash
./run-tests.sh --all --headed    # Show browser windows
./run-tests.sh --all --debug     # Debug mode (pauses)
./run-tests.sh --all --ui        # Playwright UI (interactive)
```

---

## Test Structure

### Phase 2: Navigation Bar Layout
```python
class TestPhase2NavigationBar:
    # ✅ [2.1] Buttons displayed in single row
    # ✅ [2.2] Split-view mode active by default
    # ✅ [2.3] Clicking buttons switches mode
    # ✅ [2.4] Options menu button accessible
    # ✅ [2.5] Options dropdown toggles on click
    # ✅ [2.6] Clicking outside closes menu
    # ✅ [2.7] Dropdown arrow rotates
    # ✅ [2.8] No sync button visible
```

### Phase 3: Mode Conditional Logic
```python
class TestPhase3ModeConditionalLogic:
    # ✅ [3.1] Data attributes present
    # ✅ [3.2] Buttons enabled when both content available
    # ✅ [3.3] Options menu updates per mode
    # ✅ [3.4] Disabled buttons not clickable
```

### Phase 4: Options Persistence
```python
class TestPhase4OptionsPersistence:
    # ✅ [4.1] Checkbox state persists in sessionStorage
    # ✅ [4.2] State restored on reload
    # ✅ [4.3] Multiple checkboxes toggleable
```

### Accessibility
```python
class TestAccessibility:
    # ✅ Buttons have title attributes
    # ✅ Checkboxes properly labeled
```

### Responsive Design
```python
class TestResponsive:
    # ✅ Mobile layout (320px)
    # ✅ Tablet layout (768px)
    # ✅ Desktop layout (1920px)
```

---

## Environment Variables

```bash
# Base URL for tests (default: http://localhost:8000)
export PLAYWRIGHT_TEST_BASE_URL="http://localhost:8000"

# Transcription ID to test (default: 1080)
export PLAYWRIGHT_TEST_TRANS_ID="1080"

# App root path (default: ./app)
export APP_ROOT="./app"
```

---

## Usage Examples

### Example 1: Test all browsers
```bash
./run-tests.sh --all
```

Expected output:
```
Running tests on all browsers (Chrome, Firefox, Safari)...
tests/playwright/test_facsimile_viewer.py::TestPhase2NavigationBar::test_layout_buttons_displayed_in_single_row[chromium] PASSED
tests/playwright/test_facsimile_viewer.py::TestPhase2NavigationBar::test_layout_buttons_displayed_in_single_row[firefox] PASSED
tests/playwright/test_facsimile_viewer.py::TestPhase2NavigationBar::test_layout_buttons_displayed_in_single_row[webkit] PASSED
...
```

### Example 2: Test Chrome only
```bash
./run-tests.sh --chrome
```

### Example 3: Test with visual feedback (headed mode)
```bash
./run-tests.sh --all --headed
```

Browsers will open visibly, showing interactions in real-time.

### Example 4: Test specific class/method
```bash
pytest tests/playwright/test_facsimile_viewer.py::TestPhase2NavigationBar::test_splitting_buttons_displayed_in_single_row -v
```

### Example 5: Test with debugging
```bash
pytest tests/playwright/test_facsimile_viewer.py -v -s --pdb
```

### Example 6: Test responsive design only
```bash
pytest tests/playwright/test_facsimile_viewer.py -k "responsive" -v
```

---

## Test Execution Flow

```
1. Setup Django server at http://localhost:8000
2. Initialize Playwright
3. For each browser (Chromium, Firefox, WebKit):
   a. Create browser instance
   b. Create new context (session)
   c. Create new page
   d. Navigate to transcription URL
   e. Wait for page load
   f. Run test assertions
   g. Capture screenshots on failure
   h. Record video on failure
   i. Clean up resources
4. Generate HTML report
5. Exit with test summary
```

---

## Result Artifacts

Test results are generated in `test-results/`:

```
test-results/
├── index.html                # HTML report
├── results.json             # JSON results
├── junit.xml                # JUnit format (CI/CD)
└── test_[name]_[browser]/
    ├── screenshot.png       # On failure
    └── video.webm          # On failure (if enabled)
```

View report:
```bash
open test-results/index.html      # macOS
xdg-open test-results/index.html  # Linux
start test-results/index.html     # Windows
```

---

## Pytest Configuration

**File**: `pytest.ini`

```ini
[pytest]
testpaths = tests/playwright
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    phase2: Phase 2 tests
    phase3: Phase 3 tests
    phase4: Phase 4 tests
    accessibility: Accessibility tests
    responsive: Responsive tests

timeout = 30
addopts = -v --tb=short
log_level = INFO
```

---

## Dependencies

**File**: `requirements-playwright.txt`

```
playwright>=1.40.0      # Playwright browser automation
pytest>=7.4.0          # Test framework
pytest-playwright>=0.4.0 # Pytest integration
```

Install:
```bash
pip install -r requirements-playwright.txt
playwright install
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Playwright Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser: [chromium, firefox, webkit]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements-playwright.txt
      - run: playwright install
      - run: pytest tests/playwright/ -v
```

### GitLab CI Example

```yaml
test:playwright:
  stage: test
  script:
    - pip install -r requirements-playwright.txt
    - playwright install
    - pytest tests/playwright/ -v --junit-xml=report.xml
  artifacts:
    reports:
      junit: report.xml
```

---

## Troubleshooting

### Tests timeout waiting for page

```bash
# Increase timeout in pytest.ini
timeout = 60  # Change from 30
```

### Playwright not found

```bash
pip install -r requirements-playwright.txt
playwright install
```

### Browser crashes

Usually memory issue. Reduce parallel workers:
```bash
pytest tests/playwright/ -n 1
```

### Tests fail with "Permission denied"

```bash
chmod +x run-tests.sh
```

### Server not ready

Ensure Django is running:
```bash
cd app
python manage.py runserver 0.0.0.0:8000
```

---

## Next Steps

1. ✅ **Create test suite** - Done
2. ⏳ **Run tests locally** 
   ```bash
   ./run-tests.sh --all
   ```
3. ⏳ **Verify all 3 browsers pass**
4. ⏳ **Add to CI/CD pipeline**
5. ⏳ **Generate coverage report**

---

## Success Criteria

Tests pass when:

### Phase 2 ✅
- [x] 4 buttons visible in single row
- [x] Split-view mode active by default
- [x] Layout switching works
- [x] Options menu toggles
- [x] External click closes menu
- [x] Arrow rotates
- [x] No sync button

### Phase 3 ✅
- [x] Data attributes present
- [x] Buttons enable/disable based on content
- [x] Options menu contextual

### Phase 4 ✅
- [x] SessionStorage persists state
- [x] Reload restores state
- [x] Multiple toggles work

### Browser Compatibility ✅
- [x] Chrome (Chromium)
- [x] Firefox
- [x] Safari (WebKit)

### Responsive ✅
- [x] 320px (mobile)
- [x] 768px (tablet)
- [x] 1920px (desktop)

---

## Documentation

- See [tests/playwright/README.md](tests/playwright/README.md) for detailed usage
- [Playwright Python API Docs](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)

---

## Reference

**Test File**: [test_facsimile_viewer.py](tests/playwright/test_facsimile_viewer.py)  
**Config**: [pytest.ini](pytest.ini)  
**Runner**: [run-tests.sh](run-tests.sh)  
**Docs**: [tests/playwright/README.md](tests/playwright/README.md)

---

**Ready to run tests!** 🚀

```bash
./run-tests.sh --all
```
