"""
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
"""

"""
Tests for dead code removal (Phase 1b) - facsimile viewer controls
Tests verify that dead code (rotate, brightness, contrast controls) has been removed
from source files and that existing controls remain.
"""

from pathlib import Path

import pytest


@pytest.fixture
def js_file():
    """Read the viewer-controls.js file."""
    js_path = Path(__file__).parent.parent / 'static' / 'fiches' / 'js' / 'viewer-controls.js'
    with open(js_path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def css_file():
    """Read the viewer-controls.css file."""
    css_path = Path(__file__).parent.parent / 'static' / 'fiches' / 'css' / 'viewer-controls.css'
    with open(css_path, 'r', encoding='utf-8') as f:
        return f.read()


def test_no_rotate_function_in_js(js_file):
    """Test 1: Verify that rotate() function was removed from JavaScript."""
    # Check that setupRotate is not defined
    assert 'setupRotate' not in js_file, "setupRotate function should not exist"
    # Check that rotate-specific bindings don't exist
    assert "viewer-rotate" not in js_file, "Rotate button binding should not exist"


def test_no_brightness_function_in_js(js_file):
    """Test 2: Verify that brightness control functions were removed from JavaScript."""
    # Check that setupBrightness is not defined
    assert 'setupBrightness' not in js_file, "setupBrightness function should not exist"
    # Check that brightness-specific bindings don't exist
    assert "viewer-brightness" not in js_file, "Brightness button binding should not exist"
    # Check that brightness slider setup is removed
    assert "brightness-slider" not in js_file, "Brightness slider should not exist"


def test_no_contrast_function_in_js(js_file):
    """Test 3: Verify that contrast control functions were removed from JavaScript."""
    # Check that setupContrast is not defined
    assert 'setupContrast' not in js_file, "setupContrast function should not exist"
    # Check that contrast-specific bindings don't exist
    assert "viewer-contrast" not in js_file, "Contrast button binding should not exist"
    # Check that contrast slider setup is removed
    assert "contrast-slider" not in js_file, "Contrast slider should not exist"


def test_no_dropdown_utilities_in_js(js_file):
    """Test 4: Verify that dropdown utility functions were removed from JavaScript."""
    # Check that dropdown-related functions are removed
    assert 'setupDropdowns' not in js_file, "setupDropdowns function should not exist"
    assert 'toggleDropdown' not in js_file, "toggleDropdown function should not exist"
    assert 'closeAllDropdowns' not in js_file, "closeAllDropdowns function should not exist"
    assert 'updateSliderValue' not in js_file, "updateSliderValue function should not exist"


def test_no_dead_css_classes(css_file):
    """Test 5: Verify that dead CSS classes were removed from CSS file."""
    # Check that dead CSS classes are removed
    assert '.rotate-icon' not in css_file, "rotate-icon CSS class should not exist"
    assert '.brightness-icon' not in css_file, "brightness-icon CSS class should not exist"
    assert '.contrast-icon' not in css_file, "contrast-icon CSS class should not exist"
    assert '.dropdown-popup' not in css_file, "dropdown-popup CSS class should not exist"
    assert '.control-dropdown' not in css_file, "control-dropdown CSS class should not exist"


def test_existing_functions_still_present(js_file):
    """Test 6: Verify that existing critical functions are still present."""
    # Verify that core functionality remains
    assert 'ViewerControls' in js_file, "ViewerControls class should exist"
    assert 'this.bindEvents' in js_file, "bindEvents method should exist"
    assert 'this.updatePageIndicator' in js_file, "updatePageIndicator method should exist"
    # Check for navigation controls
    assert 'viewer-next-page' in js_file or 'nextPage' in js_file, "Navigation controls should exist"
    assert 'viewer-prev-page' in js_file or 'prevPage' in js_file, "Navigation controls should exist"


def test_no_filter_methods_in_js(js_file):
    """Test 7: Verify that filter-related methods were removed."""
    # These methods were only used by brightness/contrast
    assert 'applyFilters' not in js_file, "applyFilters method should not exist"
    assert 'this.brightness' not in js_file, "brightness property should not exist"
    assert 'this.contrast' not in js_file, "contrast property should not exist"


def test_css_file_has_essential_styles(css_file):
    """Test 8: Verify that essential CSS styles are still present."""
    # Check for core control styles
    assert '.viewer-control-bar' in css_file, "viewer-control-bar class should exist"
    assert 'button' in css_file.lower(), "Button styles should exist"
    # Check for layout styles (not removed)
    assert 'flex' in css_file or 'display' in css_file, "Layout styles should exist"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
