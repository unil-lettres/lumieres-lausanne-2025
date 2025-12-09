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
 * Simple lightbox module
 * Replaces jQuery lightbox plugin
 */

import { $, $1, on, addClass, removeClass, html, attr, ready } from '../utils/dom.js';

let lightboxOverlay = null;
let lightboxContent = null;

/**
 * Create lightbox overlay
 */
function createLightbox() {
  if (lightboxOverlay) {
    return;
  }

  lightboxOverlay = document.createElement('div');
  lightboxOverlay.className = 'lightbox-overlay';
  lightboxOverlay.innerHTML = `
    <div class="lightbox-content">
      <button class="lightbox-close" aria-label="Close">&times;</button>
      <div class="lightbox-image-container"></div>
    </div>
  `;

  document.body.appendChild(lightboxOverlay);
  lightboxContent = $1('.lightbox-image-container', lightboxOverlay);

  // Close on overlay click
  on(lightboxOverlay, 'click', (e) => {
    if (e.target === lightboxOverlay || e.target.classList.contains('lightbox-close')) {
      closeLightbox();
    }
  });

  // Close on Escape key
  on(document, 'keydown', (e) => {
    if (e.key === 'Escape') {
      closeLightbox();
    }
  });
}

/**
 * Open lightbox with image
 * @param {string} src - Image source URL
 * @param {string} alt - Image alt text
 */
function openLightbox(src, alt = '') {
  if (!lightboxOverlay) {
    createLightbox();
  }

  const img = document.createElement('img');
  img.src = src;
  img.alt = alt;

  lightboxContent.innerHTML = '';
  lightboxContent.appendChild(img);

  addClass(lightboxOverlay, 'active');
  addClass(document.body, 'lightbox-active');
}

/**
 * Close lightbox
 */
function closeLightbox() {
  if (!lightboxOverlay) {
    return;
  }

  removeClass(lightboxOverlay, 'active');
  removeClass(document.body, 'lightbox-active');

  setTimeout(() => {
    lightboxContent.innerHTML = '';
  }, 300);
}

/**
 * Initialize lightbox
 */
function initLightbox() {
  const lightboxLinks = $('a[rel="lightbox"], a[data-lightbox]');

  lightboxLinks.forEach((link) => {
    on(link, 'click', (e) => {
      e.preventDefault();
      const href = attr(link, 'href');
      const alt = attr(link, 'title') || '';
      openLightbox(href, alt);
    });
  });
}

// Export for global use
window.LL = window.LL || {};
window.LL.initLightbox = initLightbox;
window.LL.openLightbox = openLightbox;
window.LL.closeLightbox = closeLightbox;

export default initLightbox;
export { openLightbox, closeLightbox };
