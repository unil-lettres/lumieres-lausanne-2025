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

# Phase 5: Visual Testing & Validation with Playwright

**Estimated Time**: 3 hours  
**Status**: Ready for Implementation (after Phases 1-4 complete)  
**Objective**: Automated visual testing using Playwright to validate all UI changes and ensure consistency across browsers

---

## Test Strategy

### Scope

Test the following on **primary test URL**: `/fiches/trans/1080/` (has both transcription + facsimilé)

1. ✅ Navigation bar structure (single row, 4 buttons)
2. ✅ Options menu toggle (open/close behavior)
3. ✅ Mode button states (enabled/disabled per rules)
4. ✅ Options menu content (different per mode)
5. ✅ Transcription display (text, split, viewer-only modes)
6. ✅ Date display in "Citer comme" section
7. ✅ Browser compatibility (Chrome, Firefox)

### Test URL

```
Primary: http://localhost:8000/fiches/trans/1080/
Backup (text-only): http://localhost:8000/fiches/trans/XXX/  # transcription without facsimilé
```

---

## Playwright Test File

### Create Test File

**File**: `app/fiches/tests/test_facsimile_viewer_e2e.py`

```python
"""
End-to-end tests for facsimile viewer UI using Playwright
Tests the navigation bar refactoring and options menu
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from fiches.models import Transcription, Bibliography, Person

# Note: Requires pytest-playwright installation
# pip install pytest-playwright

@pytest.mark.playwright
class TestFacsimileViewerUI:
    
    browser_name = "chromium"  # chromium, firefox, webkit
    
    @pytest.fixture(autouse=True)
    def setup(self, page, django_live_server):
        """Setup before each test"""
        self.page = page
        self.live_server = django_live_server
        self.base_url = django_live_server.url
    
    # ===== Test 1: Navigation Bar Structure =====
    
    def test_navbar_single_row_four_buttons(self, live_server):
        """Verify navigation bar is single row with 4 buttons"""
        url = f"{self.base_url}/fiches/trans/1080/"
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        # Get navigation container
        navbar = self.page.locator('#layout-toggle-buttons')
        assert navbar.is_visible(), "Navigation bar should be visible"
        
        # Get all buttons
        buttons = navbar.locator('.layout-btn')
        count = buttons.count()
        assert count == 4, f"Expected 4 buttons, found {count}"
        
        # Verify button labels
        labels = [buttons.nth(i).text_content().strip() for i in range(4)]
        expected = ['Texte', 'Texte + Facsimilé', 'Facsimilé', 'Options']
        assert labels == expected, f"Labels mismatch: {labels} vs {expected}"
        
        # Verify single row layout (no wrapping)
        bbox_first = buttons.nth(0).bounding_box()
        bbox_last = buttons.nth(3).bounding_box()
        # Y-coordinate should be approximately same (same row)
        assert abs(bbox_first['y'] - bbox_last['y']) < 5, "Buttons should be in same row"
        
        # Take screenshot
        self.page.screenshot(path="/tmp/test_navbar_structure.png")
    
    # ===== Test 2: Options Menu Toggle =====
    
    def test_options_menu_toggle(self):
        """Verify Options menu opens/closes correctly"""
        url = f"{self.base_url}/fiches/trans/1080/"
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        # Get options button and menu
        options_btn = self.page.locator('#options-menu-btn')
        options_menu = self.page.locator('#options-dropdown')
        
        # Initially hidden
        assert options_menu.is_hidden(), "Menu should be hidden initially"
        
        # Click button to open
        options_btn.click()
        self.page.wait_for_timeout(300)  # Wait for animation
        assert options_menu.is_visible(), "Menu should be visible after click"
        
        # Take screenshot of open menu
        self.page.screenshot(path="/tmp/test_options_menu_open.png")
        
        # Click button to close
        options_btn.click()
        self.page.wait_for_timeout(300)
        assert options_menu.is_hidden(), "Menu should be hidden after second click"
        
        # Click outside to close
        options_btn.click()  # Open first
        self.page.wait_for_timeout(300)
        self.page.locator('h1').click()  # Click somewhere else
        self.page.wait_for_timeout(300)
        assert options_menu.is_hidden(), "Menu should close when clicking outside"
    
    # ===== Test 3: Mode Button States (With Facsimilé) =====
    
    def test_mode_button_states_with_facsimile(self):
        """Verify all mode buttons enabled when facsimilé present"""
        url = f"{self.base_url}/fiches/trans/1080/"  # Has facsimilé
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        navbar = self.page.locator('#layout-toggle-buttons')
        text_btn = navbar.locator('.text-only-btn')
        split_btn = navbar.locator('.split-view-btn')
        viewer_btn = navbar.locator('.viewer-only-btn')
        options_btn = self.page.locator('#options-menu-btn')
        
        # All buttons should be enabled (not disabled)
        assert text_btn.is_enabled(), "Text button should be enabled"
        assert split_btn.is_enabled(), "Split button should be enabled"
        assert viewer_btn.is_enabled(), "Viewer button should be enabled"
        assert options_btn.is_enabled(), "Options button should be enabled"
        
        # All buttons should be clickable (not grayed)
        # Check opacity (should not be 0.5)
        text_opacity = text_btn.evaluate("el => window.getComputedStyle(el).opacity")
        assert float(text_opacity) > 0.8, "Text button should not be grayed"
        
        # Split-view should be active by default
        split_classes = split_btn.get_attribute("class")
        assert "active" in split_classes, "Split-view should be active by default"
    
    # ===== Test 4: Options Menu Content Per Mode =====
    
    def test_options_content_text_mode(self):
        """Verify options menu shows text-mode options"""
        url = f"{self.base_url}/fiches/trans/1080/"
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        # Switch to text-only mode
        self.page.locator('#layout-toggle-buttons .text-only-btn').click()
        self.page.wait_for_timeout(300)
        
        # Open options menu
        self.page.locator('#options-menu-btn').click()
        self.page.wait_for_timeout(300)
        
        # Check for text-mode options
        menu = self.page.locator('#options-dropdown')
        options_text = menu.text_content()
        
        # Should contain text-specific options
        assert 'Version diplomatique' in options_text or 'Édition' in options_text, \
            "Should show version option in text mode"
        assert 'Retours' in options_text or 'ligne' in options_text, \
            "Should show linebreaks option in text mode"
        
        # Take screenshot
        self.page.screenshot(path="/tmp/test_options_text_mode.png")
    
    def test_options_content_split_mode(self):
        """Verify options menu shows split-view mode options"""
        url = f"{self.base_url}/fiches/trans/1080/"
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        # Ensure split-view mode (should be default)
        self.page.locator('#layout-toggle-buttons .split-view-btn').click()
        self.page.wait_for_timeout(300)
        
        # Open options menu
        self.page.locator('#options-menu-btn').click()
        self.page.wait_for_timeout(300)
        
        # Check for split-mode options
        menu = self.page.locator('#options-dropdown')
        options_text = menu.text_content()
        
        # Should contain split-mode specific options
        # Note: These may differ from text mode
        assert 'Édité' in options_text or 'Version' in options_text, \
            "Should show version option in split mode"
        
        # Take screenshot
        self.page.screenshot(path="/tmp/test_options_split_mode.png")
    
    # ===== Test 5: Mode Switching =====
    
    def test_mode_switching_text_to_viewer(self):
        """Test switching between text and viewer modes"""
        url = f"{self.base_url}/fiches/trans/1080/"
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        navbar = self.page.locator('#layout-toggle-buttons')
        text_btn = navbar.locator('.text-only-btn')
        viewer_btn = navbar.locator('.viewer-only-btn')
        transcription_area = self.page.locator('.transcription-content')
        viewer_area = self.page.locator('.viewer-panel')
        
        # Start in split-view (default)
        assert transcription_area.is_visible(), "Transcription visible in default mode"
        assert viewer_area.is_visible(), "Viewer visible in default mode"
        
        # Switch to text-only
        text_btn.click()
        self.page.wait_for_timeout(500)
        assert transcription_area.is_visible(), "Transcription visible in text mode"
        # Viewer may be hidden or off-screen
        
        # Verify active class
        active_classes = text_btn.get_attribute("class")
        assert "active" in active_classes, "Text button should be marked active"
        
        # Take screenshots for each mode
        self.page.screenshot(path="/tmp/test_mode_text_only.png")
        
        # Switch to viewer-only
        viewer_btn.click()
        self.page.wait_for_timeout(500)
        active_classes = viewer_btn.get_attribute("class")
        assert "active" in active_classes, "Viewer button should be marked active"
        
        self.page.screenshot(path="/tmp/test_mode_viewer_only.png")
    
    # ===== Test 6: Date Display in Citation =====
    
    def test_cite_section_dates(self):
        """Verify publication and modification dates display in citation"""
        url = f"{self.base_url}/fiches/trans/1080/"
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        # Scroll to "Citer comme" section
        cite_section = self.page.locator('.cite_as')
        cite_section.scroll_into_view()
        self.page.wait_for_timeout(300)
        
        # Get citation text
        cite_text = cite_section.text_content()
        
        # Should contain dates
        # Format: "Date de mise en ligne: dd.mm.yyyy"
        # Format: "Version: dd.mm.yyyy"
        assert 'mise en ligne' in cite_text or 'publication' in cite_text.lower(), \
            "Should show publication date label"
        
        # Take screenshot of cite section
        self.page.screenshot(path="/tmp/test_cite_section.png")
        
        # Verify date format (dd.mm.yyyy)
        import re
        date_pattern = r'\d{2}\.\d{2}\.\d{4}'
        dates_found = re.findall(date_pattern, cite_text)
        assert len(dates_found) >= 1, f"Should find at least 1 date in format dd.mm.yyyy, found: {dates_found}"
    
    # ===== Test 7: Responsive Behavior =====
    
    def test_responsive_mobile_view(self):
        """Test layout on mobile viewport"""
        # Set mobile viewport
        self.page.set_viewport_size({"width": 375, "height": 812})
        
        url = f"{self.base_url}/fiches/trans/1080/"
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        # Navigation bar should still be visible and functional
        navbar = self.page.locator('#layout-toggle-buttons')
        assert navbar.is_visible(), "Navigation bar should be visible on mobile"
        
        # Buttons should be accessible
        buttons = navbar.locator('.layout-btn')
        assert buttons.count() == 4, "All 4 buttons should be present on mobile"
        
        # Take screenshot
        self.page.screenshot(path="/tmp/test_responsive_mobile.png")
    
    # ===== Test 8: Accessibility =====
    
    def test_keyboard_navigation(self):
        """Test keyboard navigation through buttons"""
        url = f"{self.base_url}/fiches/trans/1080/"
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        
        # Focus first button using Tab
        self.page.locator('#layout-toggle-buttons .text-only-btn').focus()
        
        # Tab through buttons
        for i in range(4):
            focused_element = self.page.evaluate("document.activeElement.className")
            assert 'layout-btn' in focused_element or 'options' in focused_element, \
                f"Button {i} should be focused"
            self.page.keyboard.press('Tab')
        
        # Click should work
        self.page.locator('#layout-toggle-buttons .text-only-btn').focus()
        self.page.keyboard.press('Enter')
        self.page.wait_for_timeout(300)
        
        active = self.page.locator('#layout-toggle-buttons .text-only-btn').get_attribute("class")
        assert "active" in active, "Button should activate on Enter key"


# ===== Manual Test Script (alternative if Playwright not available) =====

class ManualTestScript:
    """Manual testing steps documented"""
    
    @staticmethod
    def test_all():
        """Complete manual test flow"""
        tests = [
            "1. Navigation Bar Structure",
            "   - Verify 4 buttons in single row: Texte | Texte+Facsimilé | Facsimilé | Options",
            "   - No horizontal line separators between buttons",
            "   - Options button on right side",
            "",
            "2. Options Menu Toggle",
            "   - Click 'Options ▼' → menu appears below",
            "   - Click 'Options ▼' again → menu disappears",
            "   - Click outside menu → menu disappears",
            "   - Arrow indicator rotates on toggle",
            "",
            "3. Mode Button States (With Facsimilé at /fiches/trans/1080/)",
            "   - All 4 buttons should be enabled (not grayed)",
            "   - 'Texte+Facsimilé' button is active (highlighted) by default",
            "   - All buttons clickable",
            "",
            "4. Options Menu Content - Text Mode",
            "   - Click 'Texte' button",
            "   - Click 'Options ▼' button",
            "   - Menu shows text-specific options",
            "   - Expected: Version diplomatique, Retours à la ligne, Table des matières, Notes",
            "",
            "5. Options Menu Content - Split-View Mode",
            "   - Click 'Texte+Facsimilé' button",
            "   - Click 'Options ▼' button",
            "   - Menu shows split-view options",
            "   - Expected: Version éditée, Retours à la ligne, Table des matières",
            "",
            "6. Options Menu Content - Viewer Only Mode",
            "   - Click 'Facsimilé' button",
            "   - Options button should be disabled (grayed)",
            "   - Click 'Options ▼' → no menu or empty",
            "",
            "7. Date Display in Citation",
            "   - Scroll to bottom 'Citer comme' section",
            "   - Should show:",
            "     * Date de mise en ligne: dd.mm.yyyy",
            "     * Version: dd.mm.yyyy",
            "",
            "8. Responsive Mobile",
            "   - Open DevTools → mobile view (375px width)",
            "   - Navigation bar still visible and functional",
            "   - All buttons accessible",
            "",
            "9. Browser Compatibility",
            "   - Test in Chrome (latest)",
            "   - Test in Firefox (latest)",
            "   - Test in Safari (if available)",
            "   - No console errors",
        ]
        return "\n".join(tests)


if __name__ == "__main__":
    print("Automated tests: Use pytest-playwright")
    print("\nManual test steps:")
    print(ManualTestScript.test_all())
```

---

## Running Playwright Tests

### Installation

```bash
# Install Playwright
pip install pytest-playwright

# Install browser binaries
playwright install
```

### Run Tests

```bash
# Run all E2E tests
pytest app/fiches/tests/test_facsimile_viewer_e2e.py -v

# Run specific test
pytest app/fiches/tests/test_facsimile_viewer_e2e.py::TestFacsimileViewerUI::test_navbar_single_row_four_buttons -v

# Run with screenshots
pytest app/fiches/tests/test_facsimile_viewer_e2e.py -v --screenshot=on

# Run headless (default) or headed
pytest app/fiches/tests/test_facsimile_viewer_e2e.py --headed

# Run in specific browser
pytest app/fiches/tests/test_facsimile_viewer_e2e.py -k "chromium"
```

### Screenshot Output

Screenshots saved to `/tmp/test_*.png`:
- `/tmp/test_navbar_structure.png`
- `/tmp/test_options_menu_open.png`
- `/tmp/test_options_text_mode.png`
- `/tmp/test_options_split_mode.png`
- `/tmp/test_mode_text_only.png`
- `/tmp/test_mode_viewer_only.png`
- `/tmp/test_cite_section.png`
- `/tmp/test_responsive_mobile.png`

---

## Manual Testing Workflow

### Before Starting

```bash
# 1. Start Django dev server (DEBUG=True)
python manage.py runserver 0.0.0.0:8000

# 2. Access primary test URL
curl http://localhost:8000/fiches/trans/1080/

# 3. Open browser DevTools
# - Chrome/Firefox: F12
# - Check Console tab for errors
```

### Test Flow

1. **Navigation Structure**
   - [ ] 4 buttons visible in single row
   - [ ] Button labels correct: Texte, Texte+Facsimilé, Facsimilé, Options
   - [ ] No visual gap/line between first 3 buttons
   - [ ] Options button pushed to right

2. **Options Menu**
   - [ ] Click "Options ▼" → dropdown appears
   - [ ] Click outside → dropdown closes
   - [ ] Arrow rotates on toggle
   - [ ] Menu shadow visible (depth effect)

3. **Mode Switching**
   - [ ] Click "Texte" → text-only view (left column only)
   - [ ] Click "Texte+Facsimilé" → split view (both columns)
   - [ ] Click "Facsimilé" → viewer-only (right column full width)
   - [ ] Each mode button highlights when active

4. **Options Per Mode**
   - [ ] Text mode: Shows version, linebreaks, TOC, marginalia options
   - [ ] Split mode: Shows version, linebreaks, TOC options (no marginalia)
   - [ ] Viewer mode: Options button disabled or no options

5. **Data Persistence**
   - [ ] Check/uncheck option → refresh page → option state preserved
   - [ ] Via browser console: `sessionStorage.getItem('trans-option-*')`

6. **Dates in Citation**
   - [ ] Scroll to "Citer comme" section
   - [ ] Verify format: "Date de mise en ligne: dd.mm.yyyy"
   - [ ] Verify format: "Version: dd.mm.yyyy"

7. **Browser Testing**
   - [ ] Chrome: No console errors
   - [ ] Firefox: No console errors
   - [ ] Mobile (375px): All buttons accessible

---

## Test Results Documentation

### Template

Create file: `descr/TEST-RESULTS-2026-02-02.md`

```markdown
# Facsimile Viewer Refactoring - Test Results

**Date**: 2026-02-02
**Tester**: [Name]
**Browsers Tested**: Chrome, Firefox

## Test Summary

| Test | Status | Notes |
|------|--------|-------|
| Navigation bar structure | ✅ PASS | 4 buttons in single row |
| Options menu toggle | ✅ PASS | Opens/closes correctly |
| Mode button states | ✅ PASS | All enabled with facsimilé |
| Options content - text | ✅ PASS | Shows correct options |
| Options content - split | ✅ PASS | Shows correct options |
| Mode switching | ✅ PASS | All transitions smooth |
| Date display | ✅ PASS | Dates visible in citation |
| Responsive mobile | ✅ PASS | Layout adapts |
| Keyboard navigation | ✅ PASS | Tab/Enter work |
| **Overall** | **✅ PASS** | Ready for deployment |

## Issues Found

None

## Browser Compatibility

- Chrome 126: ✅ PASS
- Firefox 125: ✅ PASS
- Safari 17: ⏸ Not tested

## Screenshots

- [Navigation bar](screenshots/navbar.png)
- [Options menu open](screenshots/options_open.png)
- [Text mode](screenshots/text_mode.png)
- [Citation section](screenshots/cite_section.png)

## Recommendations

None - ready for production
```

---

## Validation Checklist

### Automated Tests (Playwright)
- [ ] All 8 test cases pass
- [ ] No timeout errors
- [ ] Screenshots captured for documentation
- [ ] No browser console errors

### Manual Tests
- [ ] Navigation structure verified visually
- [ ] Options menu toggle works smoothly
- [ ] All mode buttons functional
- [ ] Options content correct per mode
- [ ] Dates display correctly in citation
- [ ] Mobile responsive
- [ ] Keyboard navigation works

### Browser Compatibility
- [ ] Chrome (latest): No issues
- [ ] Firefox (latest): No issues
- [ ] Safari (optional): No issues

### Performance
- [ ] Page loads in <3s on localhost
- [ ] No lag when switching modes
- [ ] Options menu appears instantly
- [ ] No memory leaks (check DevTools)

---

## Files Involved

| File | Purpose |
|------|---------|
| `app/fiches/tests/test_facsimile_viewer_e2e.py` | Playwright test suite (new) |
| `descr/TEST-RESULTS-2026-02-02.md` | Test results documentation |

---

## Time Breakdown

| Task | Hours | Notes |
|------|-------|-------|
| Write Playwright test suite | 1.0h | 8 test cases |
| Run automated tests | 0.5h | Debug failures if any |
| Manual testing workflow | 1.0h | Complete test checklist |
| Document results | 0.5h | Screenshots + summary |
| **Total** | **3.0h** | As estimated |

---

## Dependencies

**Blocks On**:
- Phases 1-4 completed and merged
- Django dev server running on localhost:8000

**Blocks**:
- Phase 6: Deployment (after tests pass)

---

## Success Criteria

✅ **Phase 5 Complete When**:
1. All 8 Playwright tests pass
2. Manual testing checklist 100% complete
3. No console errors in browsers
4. Screenshots document final UI
5. Test results documented
6. Ready for production deployment

---

## Post-Testing

### If Issues Found

1. Document issue in GitHub Issues
2. Create fix branch: `fix/facsimile-viewer-issue-XXX`
3. Re-run affected test
4. Document in test results

### If All Pass

1. Create summary document
2. Commit test file
3. Ready for deployment to staging/prod

---

**Ready for Review**: ✅  
**Next**: Deploy to Staging/Production
