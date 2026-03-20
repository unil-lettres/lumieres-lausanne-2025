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

import pytest
import os
from playwright.sync_api import sync_playwright


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", 
        "phase2: Phase 2 - Navigation Bar Layout tests"
    )
    config.addinivalue_line(
        "markers", 
        "phase3: Phase 3 - Mode Conditional Logic tests"
    )
    config.addinivalue_line(
        "markers", 
        "phase4: Phase 4 - Options Persistence tests"
    )
    config.addinivalue_line(
        "markers", 
        "accessibility: Accessibility tests"
    )
    config.addinivalue_line(
        "markers", 
        "responsive: Responsive design tests"
    )


@pytest.fixture(scope="session")
def playwright_instance():
    """Provide Playwright instance for entire test session"""
    with sync_playwright() as p:
        yield p


@pytest.fixture
def base_url():
    """Provide base URL for tests"""
    return os.environ.get("PLAYWRIGHT_TEST_BASE_URL", "http://localhost:8000")


@pytest.fixture
def trans_url(base_url):
    """Provide transcription URL"""
    trans_id = os.environ.get("PLAYWRIGHT_TEST_TRANS_ID", "1080")
    return f"{base_url}/fiches/trans/{trans_id}/"


def pytest_collection_modifyitems(config, items):
    """Modify test collection - add browser markers"""
    for item in items:
        # Add markers for parametrized tests
        if "browser_name" in item.fixturenames:
            if item.callspec:
                browser = item.callspec.params.get("browser_name")
                if browser:
                    item.add_marker(pytest.mark.__dict__.get(browser, pytest.mark.unknown))
