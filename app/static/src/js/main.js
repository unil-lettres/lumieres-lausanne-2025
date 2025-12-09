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
 * Main entry point for Lumières.Lausanne front-end application
 */

import { ready } from './utils/dom.js';
import './modules/carousel.js';
import './modules/lightbox.js';

// Global namespace for backward compatibility
window.LL = window.LL || {};

/**
 * Initialize application
 */
ready(() => {
  // Initialize modules
  if (window.LL.initCarousel) {
    window.LL.initCarousel();
  }

  if (window.LL.initLightbox) {
    window.LL.initLightbox();
  }
});
