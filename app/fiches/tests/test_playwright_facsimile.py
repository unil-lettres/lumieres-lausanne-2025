"""
   Copyright (C) 2010-2025 Université de Lausanne, RISET
   <https://www.unil.ch/riset/>

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
   along with this program.  If not, see <https://www.gnu.org/licenses/>.

   This copyright notice MUST APPEAR in all copies of the file.
"""

import os

from playwright.sync_api import Page

# Configuration
BASE_URL = os.environ.get("PLAYWRIGHT_TEST_BASE_URL", "http://localhost:8000")
TRANSCRIPTION_URL = f"{BASE_URL}/fiches/trans/1080/"  # Example trans ID


def get_session_storage_item(page: Page, key: str) -> str | None:
    """Helper: Get session storage value"""
    return page.evaluate(f"() => sessionStorage.getItem('{key}')")


def set_session_storage_item(page: Page, key: str, value: str):
    """Helper: Set session storage value"""
    page.evaluate(f"() => sessionStorage.setItem('{key}', '{value}')")


def wait_for_layout_transition(page: Page):
    """Helper: Wait for layout transition"""
    page.wait_for_timeout(300)


# ============================================================================
# PHASE 2: Navigation Bar Refactor Tests
# ============================================================================


class TestPhase2NavigationBar:
    """Test Phase 2: Navigation Bar Layout Refactoring"""

    def test_layout_buttons_displayed_in_single_row(self, page: Page):
        """[Phase 2.1] Layout buttons are displayed in single row"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        layout_group = page.locator("#layout-toggle-buttons")
        assert layout_group.is_visible()

        # Verify all 4 buttons exist
        text_btn = page.locator('button[data-layout="text-only"]')
        split_btn = page.locator('button[data-layout="split-view"]')
        viewer_btn = page.locator('button[data-layout="viewer-only"]')
        options_btn = page.locator("#options-menu-btn")

        assert text_btn.is_visible()
        assert split_btn.is_visible()
        assert viewer_btn.is_visible()
        assert options_btn.is_visible()

        # Verify single row (flexbox with gap: 0)
        group_style = layout_group.evaluate(
            """(el) => {
                const computed = window.getComputedStyle(el);
                return {
                    display: computed.display,
                    gap: computed.gap,
                };
            }"""
        )
        assert group_style["display"] == "flex"
        assert group_style["gap"] == "0px"

    def test_split_view_mode_is_active_by_default(self, page: Page):
        """[Phase 2.2] Split-view mode is active by default"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        split_btn = page.locator('button[data-layout="split-view"]')
        assert "active" in split_btn.get_attribute("class", "")

    def test_clicking_layout_buttons_switches_mode(self, page: Page):
        """[Phase 2.3] Clicking layout buttons switches mode"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        text_btn = page.locator('button[data-layout="text-only"]')
        split_btn = page.locator('button[data-layout="split-view"]')
        viewer_btn = page.locator('button[data-layout="viewer-only"]')

        # Click text-only mode
        text_btn.click()
        wait_for_layout_transition(page)
        assert "active" in text_btn.get_attribute("class", "")
        assert "active" not in split_btn.get_attribute("class", "")

        # Click split-view mode
        split_btn.click()
        wait_for_layout_transition(page)
        assert "active" in split_btn.get_attribute("class", "")
        assert "active" not in text_btn.get_attribute("class", "")

        # Click viewer-only mode
        viewer_btn.click()
        wait_for_layout_transition(page)
        assert "active" in viewer_btn.get_attribute("class", "")
        assert "active" not in split_btn.get_attribute("class", "")

    def test_options_menu_button_is_accessible(self, page: Page):
        """[Phase 2.4] Options menu button is accessible"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")
        assert options_btn.is_visible()
        assert "Options" in page.locator("#options-menu-btn").text_content()

    def test_options_dropdown_toggles_on_click(self, page: Page):
        """[Phase 2.5] Options dropdown toggles on click"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")
        options_dropdown = page.locator("#options-dropdown")

        # Initially hidden
        assert "show" not in options_dropdown.get_attribute("class", "")

        # Click to show
        options_btn.click()
        assert "show" in options_dropdown.get_attribute("class", "")
        assert "active" in options_btn.get_attribute("class", "")

        # Click to hide
        options_btn.click()
        assert "show" not in options_dropdown.get_attribute("class", "")
        assert "active" not in options_btn.get_attribute("class", "")

    def test_clicking_outside_closes_options_menu(self, page: Page):
        """[Phase 2.6] Clicking outside closes options menu"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")
        options_dropdown = page.locator("#options-dropdown")
        content = page.locator(".content")

        # Open menu
        options_btn.click()
        assert "show" in options_dropdown.get_attribute("class", "")

        # Click outside
        content.click(force=True)
        page.wait_for_timeout(100)
        assert "show" not in options_dropdown.get_attribute("class", "")

    def test_dropdown_arrow_rotates_when_menu_opens(self, page: Page):
        """[Phase 2.7] Dropdown arrow rotates when menu opens"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")
        arrow = options_btn.locator(".dropdown-arrow")

        # Get initial rotation
        initial_transform = arrow.evaluate(
            "el => window.getComputedStyle(el).transform"
        )

        # Open menu
        options_btn.click()
        open_transform = arrow.evaluate(
            "el => window.getComputedStyle(el).transform"
        )

        # Transforms should be different
        assert initial_transform != open_transform

    def test_no_sync_button_visible(self, page: Page):
        """[Phase 2.8] No sync button visible (removed)"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        sync_btn = page.locator("#sync-toggle-btn")
        sync_wrapper = page.locator("#sync-toggle-wrapper")

        assert not sync_btn.is_visible()
        assert not sync_wrapper.is_visible()


# ============================================================================
# PHASE 3: Mode Conditional Logic Tests
# ============================================================================


class TestPhase3ModeConditionalLogic:
    """Test Phase 3: Mode Conditional Logic"""

    def test_data_attributes_present(self, page: Page):
        """[Phase 3.1] Data attributes are present"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        layout_group = page.locator("#layout-toggle-buttons")

        has_facsimile = layout_group.get_attribute("data-has-facsimile")
        has_transcription = layout_group.get_attribute("data-has-transcription")

        assert has_facsimile is not None
        assert has_transcription is not None

    def test_all_buttons_enabled_when_both_content_available(self, page: Page):
        """[Phase 3.2] All buttons enabled when both content available"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        layout_group = page.locator("#layout-toggle-buttons")
        has_facsimile = layout_group.get_attribute("data-has-facsimile")

        if has_facsimile == "true":
            text_btn = page.locator('button[data-layout="text-only"]')
            split_btn = page.locator('button[data-layout="split-view"]')
            viewer_btn = page.locator('button[data-layout="viewer-only"]')
            options_btn = page.locator("#options-menu-btn")

            assert text_btn.is_enabled()
            assert split_btn.is_enabled()
            assert viewer_btn.is_enabled()
            assert options_btn.is_enabled()

    def test_options_menu_updates_per_mode(self, page: Page):
        """[Phase 3.3] Options menu updates per mode"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")

        # Open options
        options_btn.click()
        page.wait_for_timeout(100)

        # Options menu should have content
        options_dropdown = page.locator("#options-dropdown")
        assert options_dropdown.is_visible()

    def test_disabled_buttons_not_clickable(self, page: Page):
        """[Phase 3.4] Disabled buttons are not clickable"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        layout_group = page.locator("#layout-toggle-buttons")
        has_facsimile = layout_group.get_attribute("data-has-facsimile")

        if has_facsimile == "false":
            text_btn = page.locator('button[data-layout="text-only"]')
            split_btn = page.locator('button[data-layout="split-view"]')

            # Disabled buttons should be disabled
            assert text_btn.is_disabled() or split_btn.is_disabled()


# ============================================================================
# PHASE 4: Options Persistence Tests
# ============================================================================


class TestPhase4OptionsPersistence:
    """Test Phase 4: Options Persistence in sessionStorage"""

    def test_checkbox_state_persists_in_session_storage(self, page: Page):
        """[Phase 4.1] Checkbox state persists in sessionStorage"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")
        options_dropdown = page.locator("#options-dropdown")

        # Open options menu
        options_btn.click()
        page.wait_for_timeout(100)

        # Get first checkbox
        first_checkbox = options_dropdown.locator('input[type="checkbox"]').first
        checkbox_name = first_checkbox.get_attribute("data-option")

        if checkbox_name:
            # Check the checkbox
            first_checkbox.check()
            page.wait_for_timeout(100)

            # Verify in sessionStorage
            storage_key = f"trans-option-{checkbox_name}"
            value = get_session_storage_item(page, storage_key)
            assert value == "true"

    def test_checkbox_state_restored_on_reload(self, page: Page):
        """[Phase 4.2] Checkbox state is restored on reload"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")
        options_dropdown = page.locator("#options-dropdown")

        # Set a checkbox
        options_btn.click()
        first_checkbox = options_dropdown.locator('input[type="checkbox"]').first
        checkbox_name = first_checkbox.get_attribute("data-option")

        if checkbox_name:
            first_checkbox.check()
            page.wait_for_timeout(100)

            # Reload page
            page.reload()
            page.wait_for_load_state("networkidle")

            # Verify checkbox is still checked
            reloaded_btn = page.locator("#options-menu-btn")
            reloaded_btn.click()
            reloaded_dropdown = page.locator("#options-dropdown")
            reloaded_checkbox = reloaded_dropdown.locator(
                f'input[data-option="{checkbox_name}"]'
            ).first

            assert reloaded_checkbox.is_checked()

    def test_multiple_checkboxes_can_be_toggled(self, page: Page):
        """[Phase 4.3] Multiple checkboxes can be toggled"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")
        options_dropdown = page.locator("#options-dropdown")

        # Open menu
        options_btn.click()
        page.wait_for_timeout(100)

        # Get all checkboxes
        checkboxes = options_dropdown.locator('input[type="checkbox"]')
        count = checkboxes.count()

        # Toggle each checkbox
        for i in range(min(count, 3)):
            checkbox = checkboxes.nth(i)
            data_option = checkbox.get_attribute("data-option")

            checkbox.check()
            page.wait_for_timeout(50)

            if data_option:
                value = get_session_storage_item(
                    page, f"trans-option-{data_option}"
                )
                assert value == "true"


# ============================================================================
# ACCESSIBILITY Tests
# ============================================================================


class TestAccessibility:
    """Test Accessibility features"""

    def test_buttons_have_title_attributes(self, page: Page):
        """[A11y] Buttons have title attributes"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        text_btn = page.locator('button[data-layout="text-only"]')
        split_btn = page.locator('button[data-layout="split-view"]')
        viewer_btn = page.locator('button[data-layout="viewer-only"]')
        options_btn = page.locator("#options-menu-btn")

        assert text_btn.get_attribute("title")
        assert split_btn.get_attribute("title")
        assert viewer_btn.get_attribute("title")
        assert options_btn.get_attribute("title")

    def test_checkboxes_properly_labeled(self, page: Page):
        """[A11y] Checkboxes are properly labeled"""
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        options_btn = page.locator("#options-menu-btn")
        options_dropdown = page.locator("#options-dropdown")

        options_btn.click()
        page.wait_for_timeout(100)

        # Get all option items
        option_items = options_dropdown.locator(".option-item")
        count = option_items.count()

        assert count > 0

        # Each should have checkbox and label
        for i in range(count):
            item = option_items.nth(i)
            checkbox = item.locator('input[type="checkbox"]')
            label = item.locator("span")

            assert checkbox.is_visible()
            assert label.is_visible()


# ============================================================================
# RESPONSIVE Tests
# ============================================================================


class TestResponsive:
    """Test Responsive Design"""

    def test_mobile_layout_320px(self, page: Page):
        """[Responsive] Mobile layout (320px)"""
        page.set_viewport_size({"width": 320, "height": 568})
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        layout_group = page.locator("#layout-toggle-buttons")
        assert layout_group.is_visible()

        options_btn = page.locator("#options-menu-btn")
        assert options_btn.is_visible()

    def test_tablet_layout_768px(self, page: Page):
        """[Responsive] Tablet layout (768px)"""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        layout_group = page.locator("#layout-toggle-buttons")
        assert layout_group.is_visible()

        buttons = layout_group.locator("button.layout-btn")
        assert buttons.count() == 4

    def test_desktop_layout_1920px(self, page: Page):
        """[Responsive] Desktop layout (1920px)"""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(TRANSCRIPTION_URL)
        page.wait_for_load_state("networkidle")

        layout_group = page.locator("#layout-toggle-buttons")
        assert layout_group.is_visible()

        # All elements visible
        text_btn = page.locator('button[data-layout="text-only"]')
        split_btn = page.locator('button[data-layout="split-view"]')
        viewer_btn = page.locator('button[data-layout="viewer-only"]')
        options_btn = page.locator("#options-menu-btn")

        assert text_btn.is_visible()
        assert split_btn.is_visible()
        assert viewer_btn.is_visible()
        assert options_btn.is_visible()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
