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

/**
 * Admin Module
 * Admin-specific functionality
 */

import { ready, $, $1, on } from './utils/dom.js';

/**
 * Initialize admin features
 */
function initAdmin() {
  // Admin light theme toggle
  initThemeToggle();

  // Admin activity log change list
  initActivityLog();

  // Project URL tools
  initProjectUrlTools();
}

/**
 * Initialize theme toggle
 */
function initThemeToggle() {
  const themeToggle = $1('#admin-theme-toggle');

  if (themeToggle) {
    on(themeToggle, 'click', () => {
      document.body.classList.toggle('admin-light-theme');

      const isLight = document.body.classList.contains('admin-light-theme');
      localStorage.setItem('admin-theme', isLight ? 'light' : 'dark');
    });

    // Restore saved theme
    const savedTheme = localStorage.getItem('admin-theme');
    if (savedTheme === 'light') {
      document.body.classList.add('admin-light-theme');
    }
  }
}

/**
 * Initialize activity log functionality
 */
function initActivityLog() {
  const activityLog = $1('#activity-log-list');

  if (activityLog) {
    // Add any activity log specific behaviors
    const rows = $('.activity-row', activityLog);

    rows.forEach((row) => {
      on(row, 'click', () => {
        row.classList.toggle('expanded');
      });
    });
  }
}

/**
 * Initialize project URL tools
 */
function initProjectUrlTools() {
  const urlForm = $1('#project-url-form');

  if (urlForm) {
    on(urlForm, 'submit', (e) => {
      const urlInput = $1('#id_url', urlForm);
      if (urlInput && urlInput.value) {
        // Validate URL format
        try {
          new URL(urlInput.value);
        } catch {
          e.preventDefault();
          alert('Please enter a valid URL');
        }
      }
    });
  }
}

// Initialize on DOM ready
ready(initAdmin);

export default initAdmin;
