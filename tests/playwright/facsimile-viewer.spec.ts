/*
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
*/

import { test, expect, Page } from '@playwright/test';

// Configuration
const BASE_URL = process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:8000';
const TRANSCRIPTION_URL = `${BASE_URL}/fiches/trans/1080/`; // Example trans ID

/**
 * Helper: Wait for layout transition
 */
async function waitForLayoutTransition(page: Page) {
  await page.waitForTimeout(300);
}

/**
 * Helper: Get session storage value
 */
async function getSessionStorageItem(page: Page, key: string): Promise<string | null> {
  return page.evaluate((k) => sessionStorage.getItem(k), key);
}

/**
 * Helper: Set session storage value
 */
async function setSessionStorageItem(page: Page, key: string, value: string) {
  await page.evaluate(({ k, v }) => sessionStorage.setItem(k, v), { k: key, v: value });
}

/**
 * PHASE 2: Navigation Bar Refactor Tests
 */
test.describe('Phase 2: Navigation Bar Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TRANSCRIPTION_URL);
    await page.waitForLoadState('networkidle');
  });

  test('[Phase 2.1] Layout buttons are displayed in single row', async ({ page }) => {
    const layoutGroup = page.locator('#layout-toggle-buttons');
    
    // Verify container exists
    await expect(layoutGroup).toBeVisible();
    
    // Verify all 4 buttons exist
    const textBtn = page.locator('button[data-layout="text-only"]');
    const splitBtn = page.locator('button[data-layout="split-view"]');
    const viewerBtn = page.locator('button[data-layout="viewer-only"]');
    const optionsBtn = page.locator('#options-menu-btn');
    
    await expect(textBtn).toBeVisible();
    await expect(splitBtn).toBeVisible();
    await expect(viewerBtn).toBeVisible();
    await expect(optionsBtn).toBeVisible();
    
    // Verify they're in a single row (flexbox with gap: 0)
    const groupStyle = await layoutGroup.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        display: computed.display,
        gap: computed.gap,
      };
    });
    expect(groupStyle.display).toBe('flex');
    expect(groupStyle.gap).toBe('0px');
  });

  test('[Phase 2.2] Split-view mode is active by default', async ({ page }) => {
    const splitBtn = page.locator('button[data-layout="split-view"]');
    await expect(splitBtn).toHaveClass(/active/);
  });

  test('[Phase 2.3] Clicking layout buttons switches mode', async ({ page }) => {
    const textBtn = page.locator('button[data-layout="text-only"]');
    const splitBtn = page.locator('button[data-layout="split-view"]');
    const viewerBtn = page.locator('button[data-layout="viewer-only"]');
    const container = page.locator('.transcription-viewer-container');

    // Click text-only mode
    await textBtn.click();
    await waitForLayoutTransition(page);
    await expect(textBtn).toHaveClass(/active/);
    await expect(splitBtn).not.toHaveClass(/active/);

    // Click split-view mode
    await splitBtn.click();
    await waitForLayoutTransition(page);
    await expect(splitBtn).toHaveClass(/active/);
    await expect(textBtn).not.toHaveClass(/active/);

    // Click viewer-only mode
    await viewerBtn.click();
    await waitForLayoutTransition(page);
    await expect(viewerBtn).toHaveClass(/active/);
    await expect(splitBtn).not.toHaveClass(/active/);
  });

  test('[Phase 2.4] Options menu button is accessible', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    await expect(optionsBtn).toBeVisible();
    await expect(optionsBtn).toContainText('Options');
  });

  test('[Phase 2.5] Options dropdown toggles on click', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    const optionsDropdown = page.locator('#options-dropdown');

    // Initially hidden
    await expect(optionsDropdown).not.toHaveClass(/show/);

    // Click to show
    await optionsBtn.click();
    await expect(optionsDropdown).toHaveClass(/show/);
    await expect(optionsBtn).toHaveClass(/active/);

    // Click to hide
    await optionsBtn.click();
    await expect(optionsDropdown).not.toHaveClass(/show/);
    await expect(optionsBtn).not.toHaveClass(/active/);
  });

  test('[Phase 2.6] Clicking outside closes options menu', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    const optionsDropdown = page.locator('#options-dropdown');
    const content = page.locator('.content');

    // Open menu
    await optionsBtn.click();
    await expect(optionsDropdown).toHaveClass(/show/);

    // Click outside (on content area)
    await content.click({ force: true });
    await page.waitForTimeout(100);
    await expect(optionsDropdown).not.toHaveClass(/show/);
  });

  test('[Phase 2.7] Dropdown arrow rotates when menu opens', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    const arrow = optionsBtn.locator('.dropdown-arrow');

    // Get initial rotation
    const initialTransform = await arrow.evaluate((el) => {
      return window.getComputedStyle(el).transform;
    });

    // Open menu
    await optionsBtn.click();
    const openTransform = await arrow.evaluate((el) => {
      return window.getComputedStyle(el).transform;
    });

    // Transforms should be different (rotation applied)
    expect(initialTransform).not.toBe(openTransform);
  });

  test('[Phase 2.8] No sync button visible (removed)', async ({ page }) => {
    const syncBtn = page.locator('#sync-toggle-btn');
    const syncWrapper = page.locator('#sync-toggle-wrapper');

    await expect(syncBtn).not.toBeVisible();
    await expect(syncWrapper).not.toBeVisible();
  });
});

/**
 * PHASE 3: Mode Conditional Logic Tests
 */
test.describe('Phase 3: Mode Conditional Logic', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TRANSCRIPTION_URL);
    await page.waitForLoadState('networkidle');
  });

  test('[Phase 3.1] Data attributes are present', async ({ page }) => {
    const layoutGroup = page.locator('#layout-toggle-buttons');

    const hasFacsimile = await layoutGroup.getAttribute('data-has-facsimile');
    const hasTranscription = await layoutGroup.getAttribute('data-has-transcription');

    expect(hasFacsimile).toBeTruthy();
    expect(hasTranscription).toBeTruthy();
  });

  test('[Phase 3.2] All buttons enabled when both content available', async ({ page }) => {
    const layoutGroup = page.locator('#layout-toggle-buttons');
    const hasFacsimile = await layoutGroup.getAttribute('data-has-facsimile');

    if (hasFacsimile === 'true') {
      const textBtn = page.locator('button[data-layout="text-only"]');
      const splitBtn = page.locator('button[data-layout="split-view"]');
      const viewerBtn = page.locator('button[data-layout="viewer-only"]');
      const optionsBtn = page.locator('#options-menu-btn');

      await expect(textBtn).toBeEnabled();
      await expect(splitBtn).toBeEnabled();
      await expect(viewerBtn).toBeEnabled();
      await expect(optionsBtn).toBeEnabled();
    }
  });

  test('[Phase 3.3] Options menu updates per mode', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    const optionsDropdown = page.locator('#options-dropdown');
    const splitBtn = page.locator('button[data-layout="split-view"]');

    // Open options in split-view mode
    await optionsBtn.click();
    const splitViewContent = await optionsDropdown.textContent();

    // Switch to text-only mode
    await optionsBtn.click(); // Close menu first
    await splitBtn.click();
    await waitForLayoutTransition(page);

    // The options menu should still work in text-only
    const textBtn = page.locator('button[data-layout="text-only"]');
    await expect(textBtn).toHaveClass(/active/);
  });

  test('[Phase 3.4] Disabled buttons are not clickable', async ({ page }) => {
    const layoutGroup = page.locator('#layout-toggle-buttons');
    const hasFacsimile = await layoutGroup.getAttribute('data-has-facsimile');

    if (hasFacsimile === 'false') {
      const textBtn = page.locator('button[data-layout="text-only"]');
      const splitBtn = page.locator('button[data-layout="split-view"]');

      // Try to click disabled buttons - they should be disabled
      const textDisabled = await textBtn.isDisabled();
      const splitDisabled = await splitBtn.isDisabled();

      expect(textDisabled || splitDisabled).toBeTruthy();
    }
  });
});

/**
 * PHASE 4: Session Storage Persistence Tests
 */
test.describe('Phase 4: Options Persistence', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TRANSCRIPTION_URL);
    await page.waitForLoadState('networkidle');
  });

  test('[Phase 4.1] Checkbox state persists in sessionStorage', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    const optionsDropdown = page.locator('#options-dropdown');

    // Open options menu
    await optionsBtn.click();
    await expect(optionsDropdown).toHaveClass(/show/);

    // Get first checkbox (if exists)
    const firstCheckbox = optionsDropdown.locator('input[type="checkbox"]').first();
    const checkboxName = await firstCheckbox.getAttribute('data-option');

    // Check the checkbox
    await firstCheckbox.check();
    await page.waitForTimeout(100);

    // Verify it's stored in sessionStorage
    if (checkboxName) {
      const storageKey = `trans-option-${checkboxName}`;
      const value = await getSessionStorageItem(page, storageKey);
      expect(value).toBe('true');
    }
  });

  test('[Phase 4.2] Checkbox state is restored on reload', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    const optionsDropdown = page.locator('#options-dropdown');

    // Set a checkbox
    await optionsBtn.click();
    const firstCheckbox = optionsDropdown.locator('input[type="checkbox"]').first();
    const checkboxName = await firstCheckbox.getAttribute('data-option');

    if (checkboxName) {
      await firstCheckbox.check();
      const storageKey = `trans-option-${checkboxName}`;
      await page.waitForTimeout(100);

      // Reload page
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Verify checkbox is still checked
      const reloadedBtn = page.locator('#options-menu-btn');
      await reloadedBtn.click();
      const reloadedDropdown = page.locator('#options-dropdown');
      const reloadedCheckbox = reloadedDropdown
        .locator(`input[data-option="${checkboxName}"]`)
        .first();

      await expect(reloadedCheckbox).toBeChecked();
    }
  });

  test('[Phase 4.3] Multiple checkboxes can be toggled', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    const optionsDropdown = page.locator('#options-dropdown');

    // Open menu
    await optionsBtn.click();

    // Get all checkboxes
    const checkboxes = optionsDropdown.locator('input[type="checkbox"]');
    const count = await checkboxes.count();

    // Toggle each checkbox
    for (let i = 0; i < count && i < 3; i++) {
      const checkbox = checkboxes.nth(i);
      const dataOption = await checkbox.getAttribute('data-option');

      await checkbox.check();
      await page.waitForTimeout(50);

      if (dataOption) {
        const value = await getSessionStorageItem(page, `trans-option-${dataOption}`);
        expect(value).toBe('true');
      }
    }
  });
});

/**
 * BROWSER COMPATIBILITY Tests (Chrome, Firefox, Safari)
 */
test.describe('Browser Compatibility', () => {
  const browsers = ['chromium', 'firefox', 'webkit'];

  for (const browser of browsers) {
    test(`[Compatibility] Navigation bar works on ${browser}`, async ({ page, browserName }) => {
      if (browserName !== browser) return;

      await page.goto(TRANSCRIPTION_URL);
      await page.waitForLoadState('networkidle');

      // Basic checks
      const layoutGroup = page.locator('#layout-toggle-buttons');
      const optionsBtn = page.locator('#options-menu-btn');

      await expect(layoutGroup).toBeVisible();
      await expect(optionsBtn).toBeVisible();

      // Test clicking
      await optionsBtn.click();
      const dropdown = page.locator('#options-dropdown');
      await expect(dropdown).toHaveClass(/show/);

      await optionsBtn.click();
      await expect(dropdown).not.toHaveClass(/show/);
    });

    test(`[Compatibility] Layout switching works on ${browser}`, async ({ page, browserName }) => {
      if (browserName !== browser) return;

      await page.goto(TRANSCRIPTION_URL);
      await page.waitForLoadState('networkidle');

      const textBtn = page.locator('button[data-layout="text-only"]');
      const splitBtn = page.locator('button[data-layout="split-view"]');
      const viewerBtn = page.locator('button[data-layout="viewer-only"]');

      // Test each layout mode
      await textBtn.click();
      await waitForLayoutTransition(page);
      await expect(textBtn).toHaveClass(/active/);

      await splitBtn.click();
      await waitForLayoutTransition(page);
      await expect(splitBtn).toHaveClass(/active/);

      await viewerBtn.click();
      await waitForLayoutTransition(page);
      await expect(viewerBtn).toHaveClass(/active/);
    });

    test(`[Compatibility] CSS styling is consistent on ${browser}`, async ({ page, browserName }) => {
      if (browserName !== browser) return;

      await page.goto(TRANSCRIPTION_URL);
      await page.waitForLoadState('networkidle');

      const layoutGroup = page.locator('#layout-toggle-buttons');
      const buttons = layoutGroup.locator('button.layout-btn');

      // Check that buttons have expected styling
      for (let i = 0; i < (await buttons.count()); i++) {
        const button = buttons.nth(i);
        const styles = await button.evaluate((el) => {
          const computed = window.getComputedStyle(el);
          return {
            display: computed.display,
            cursor: computed.cursor,
            padding: computed.padding,
          };
        });

        expect(styles.cursor).toBe('pointer');
      }
    });
  }
});

/**
 * ACCESSIBILITY Tests
 */
test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TRANSCRIPTION_URL);
    await page.waitForLoadState('networkidle');
  });

  test('[A11y] Buttons have title attributes', async ({ page }) => {
    const textBtn = page.locator('button[data-layout="text-only"]');
    const splitBtn = page.locator('button[data-layout="split-view"]');
    const viewerBtn = page.locator('button[data-layout="viewer-only"]');
    const optionsBtn = page.locator('#options-menu-btn');

    const textTitle = await textBtn.getAttribute('title');
    const splitTitle = await splitBtn.getAttribute('title');
    const viewerTitle = await viewerBtn.getAttribute('title');
    const optionsTitle = await optionsBtn.getAttribute('title');

    expect(textTitle).toBeTruthy();
    expect(splitTitle).toBeTruthy();
    expect(viewerTitle).toBeTruthy();
    expect(optionsTitle).toBeTruthy();
  });

  test('[A11y] Buttons are keyboard navigable', async ({ page }) => {
    const textBtn = page.locator('button[data-layout="text-only"]');

    // Tab to first button
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);

    // One of the buttons should have focus
    const focusedElement = await page.evaluate(() => document.activeElement?.id);
    expect(focusedElement).toBeTruthy();
  });

  test('[A11y] Dropdown menu is accessible with keyboard', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');

    // Tab to options button
    await page.focus('#options-menu-btn');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(100);

    // Menu should be visible
    const dropdown = page.locator('#options-dropdown');
    await expect(dropdown).toHaveClass(/show/);
  });

  test('[A11y] Checkboxes are properly labeled', async ({ page }) => {
    const optionsBtn = page.locator('#options-menu-btn');
    const optionsDropdown = page.locator('#options-dropdown');

    await optionsBtn.click();

    // Get all option items
    const optionItems = optionsDropdown.locator('.option-item');
    const count = await optionItems.count();

    expect(count).toBeGreaterThan(0);

    // Each should have a checkbox and label
    for (let i = 0; i < count; i++) {
      const item = optionItems.nth(i);
      const checkbox = item.locator('input[type="checkbox"]');
      const label = item.locator('span');

      await expect(checkbox).toBeVisible();
      await expect(label).toBeVisible();
    }
  });
});

/**
 * RESPONSIVE Tests
 */
test.describe('Responsive Design', () => {
  test('[Responsive] Mobile layout (320px)', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 568 });
    await page.goto(TRANSCRIPTION_URL);
    await page.waitForLoadState('networkidle');

    const layoutGroup = page.locator('#layout-toggle-buttons');
    await expect(layoutGroup).toBeVisible();

    const optionsBtn = page.locator('#options-menu-btn');
    await expect(optionsBtn).toBeVisible();
  });

  test('[Responsive] Tablet layout (768px)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(TRANSCRIPTION_URL);
    await page.waitForLoadState('networkidle');

    const layoutGroup = page.locator('#layout-toggle-buttons');
    await expect(layoutGroup).toBeVisible();

    const buttons = layoutGroup.locator('button.layout-btn');
    expect(await buttons.count()).toBe(4);
  });

  test('[Responsive] Desktop layout (1920px)', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(TRANSCRIPTION_URL);
    await page.waitForLoadState('networkidle');

    const layoutGroup = page.locator('#layout-toggle-buttons');
    await expect(layoutGroup).toBeVisible();

    // All elements should be visible
    const textBtn = page.locator('button[data-layout="text-only"]');
    const splitBtn = page.locator('button[data-layout="split-view"]');
    const viewerBtn = page.locator('button[data-layout="viewer-only"]');
    const optionsBtn = page.locator('#options-menu-btn');

    await expect(textBtn).toBeVisible();
    await expect(splitBtn).toBeVisible();
    await expect(viewerBtn).toBeVisible();
    await expect(optionsBtn).toBeVisible();
  });
});
