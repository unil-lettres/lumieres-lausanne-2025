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
 * Carousel module using Swiper
 * Replaces jQuery jCarousel
 */

import Swiper from 'swiper';
import 'swiper/css';
import { $, $1, on, data } from '../utils/dom.js';

/**
 * Initialize carousels
 * @param {Element} scope - Optional scope element
 */
function initCarousel(scope) {
  const context = scope || document;
  const carousels = $('.jcarousel', context);

  carousels.forEach((carousel) => {
    // Skip if already initialized
    if (data(carousel, 'llCarouselInitialized')) {
      return;
    }

    // Initialize Swiper
    const swiper = new Swiper(carousel, {
      slidesPerView: 'auto',
      spaceBetween: 10,
      loop: true,
      navigation: {
        nextEl: '.next',
        prevEl: '.prev',
      },
      on: {
        init: function () {
          data(carousel, 'llCarouselInitialized', 'true');
          data(carousel, 'swiper', this);
        },
      },
    });

    // Store swiper instance
    carousel.swiperInstance = swiper;
  });
}

// Export for global use
window.LL = window.LL || {};
window.LL.initCarousel = initCarousel;

export default initCarousel;
