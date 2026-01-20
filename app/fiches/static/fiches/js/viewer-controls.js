/*
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
*/

/**
 * Common Viewer Controls JavaScript
 * Provides unified functionality for facsimile viewer controls
 */
(function (window) {
    'use strict';

    /**
     * ViewerControls class to manage OpenSeadragon viewer controls
     */
    function ViewerControls(viewerInstance) {
        this.viewer = viewerInstance;
        this.currentRotation = 0;
        this.filters = {
            brightness: 100,
            contrast: 100
        };
        this.boundEvents = {}; // Track bound event handlers

        this.init();
    }

    ViewerControls.prototype = {

        /**
         * Initialize all controls and event listeners
         */
        init: function () {
            this.bindEvents();
            this.setupDropdowns();
            this.updatePageIndicator();
            this.applyFilters();

            // Listen for viewer events
            if (this.viewer) {
                this.viewer.addHandler('page', this.updatePageIndicator.bind(this));
                this.viewer.addHandler('open', this.updatePageIndicator.bind(this));
                this.viewer.addHandler('sequence', this.updatePageIndicator.bind(this));
            }
        },

        /**
         * Bind click events to control buttons
         */
        bindEvents: function () {
            var self = this;

            // Navigation controls
            this.bindButton('viewer-prev-page', function () {
                console.log('=======================================================================');
                if (!self.viewer) return;

                var currentPage = self.viewer.currentPage();
                var totalPages = self.getTotalPages();

                console.log('Previous clicked - Current:', currentPage, 'Total:', totalPages);

                if (totalPages > 1 && currentPage > 0) {
                    var targetPage = currentPage - 1;
                    console.log('Going to page:', targetPage);
                    self.viewer.goToPage(targetPage);
                }
                console.log('=======================================================================');
            });

            this.bindButton('viewer-next-page', function () {
                console.log('=======================================================================');
                if (!self.viewer) return;

                var currentPage = self.viewer.currentPage();
                var totalPages = self.getTotalPages();

                console.log('Next clicked - Current:', currentPage, 'Total:', totalPages);

                if (totalPages > 1 && currentPage < totalPages - 1) {
                    var targetPage = currentPage + 1;
                    console.log('Going to page:', targetPage);
                    self.viewer.goToPage(targetPage);
                }
                console.log('=======================================================================');
            });

            // Zoom controls
            this.bindButton('viewer-zoom-in', function () {
                if (self.viewer) {
                    self.viewer.viewport.zoomBy(1.2);
                }
            });

            this.bindButton('viewer-zoom-out', function () {
                if (self.viewer) {
                    self.viewer.viewport.zoomBy(0.8);
                }
            });

            // Transform controls
            this.bindButton('viewer-rotate', function () {
                self.rotate();
            });

            this.bindButton('viewer-reset', function () {
                self.reset();
            });

            // Adjustment control popups
            this.bindButton('viewer-contrast', function () {
                self.toggleDropdown('contrast-popup');
            });

            this.bindButton('viewer-brightness', function () {
                self.toggleDropdown('brightness-popup');
            });

            // Slider controls
            this.bindSlider('contrast-slider', function (value) {
                self.filters.contrast = parseInt(value);
                self.applyFilters();
            });

            this.bindSlider('brightness-slider', function (value) {
                self.filters.brightness = parseInt(value);
                self.applyFilters();
            });

            // Page input field handler
            this.bindPageInput('page-input', function (pageNumber) {
                if (!self.viewer) return;
                
                var totalPages = self.getTotalPages();
                var targetPage = parseInt(pageNumber, 10);
                
                // Validate page number
                if (isNaN(targetPage) || targetPage < 1 || targetPage > totalPages) {
                    // Reset to current page if invalid
                    self.updatePageIndicator();
                    return;
                }
                
                // Convert from 1-based display to 0-based index
                var targetIndex = targetPage - 1;
                
                console.log('Page input: navigating to page', targetPage, '(index', targetIndex + ')');
                self.viewer.goToPage(targetIndex);
            });
        },

        /**
         * Bind button click event with error handling
         */
        bindButton: function (id, handler) {
            var element = document.getElementById(id);
            if (element) {
                // Remove any existing event listener first
                if (this.boundEvents[id]) {
                    element.removeEventListener('click', this.boundEvents[id]);
                }
                // Add new event listener and track it
                this.boundEvents[id] = handler;
                element.addEventListener('click', handler);
            }
        },

        /**
         * Bind slider input event with error handling
         */
        bindSlider: function (id, handler) {
            var element = document.getElementById(id);
            if (element) {
                // Remove any existing event listener first
                if (this.boundEvents[id + '_slider']) {
                    element.removeEventListener('input', this.boundEvents[id + '_slider']);
                }
                // Create wrapper function and track it
                var wrapperHandler = function () {
                    handler(this.value);
                };
                this.boundEvents[id + '_slider'] = wrapperHandler;
                element.addEventListener('input', wrapperHandler);
            }
        },

        /**
         * Bind page input events (change and enter key)
         */
        bindPageInput: function (id, handler) {
            var element = document.getElementById(id);
            if (element) {
                // Remove any existing event listeners first
                if (this.boundEvents[id + '_change']) {
                    element.removeEventListener('change', this.boundEvents[id + '_change']);
                }
                if (this.boundEvents[id + '_keypress']) {
                    element.removeEventListener('keypress', this.boundEvents[id + '_keypress']);
                }
                
                // Handle when user leaves the field (blur/change)
                var changeHandler = function () {
                    handler(this.value);
                };
                this.boundEvents[id + '_change'] = changeHandler;
                element.addEventListener('change', changeHandler);
                
                // Handle when user presses Enter
                var keypressHandler = function (e) {
                    if (e.key === 'Enter' || e.keyCode === 13) {
                        e.preventDefault();
                        handler(this.value);
                        this.blur(); // Remove focus after navigating
                    }
                };
                this.boundEvents[id + '_keypress'] = keypressHandler;
                element.addEventListener('keypress', keypressHandler);
            }
        },

        /**
         * Setup dropdown behavior (close on outside click)
         */
        setupDropdowns: function () {
            var self = this;
            document.addEventListener('click', function (event) {
                var isControlButton = event.target.closest('#viewer-contrast, #viewer-brightness');
                var isDropdown = event.target.closest('.dropdown-popup');

                if (!isControlButton && !isDropdown) {
                    self.closeAllDropdowns();
                }
            });
        },

        /**
         * Toggle dropdown popup visibility
         */
        toggleDropdown: function (popupId) {
            var popup = document.getElementById(popupId);
            if (popup) {
                var isVisible = popup.classList.contains('show');
                this.closeAllDropdowns();

                if (!isVisible) {
                    popup.classList.add('show');
                }
            }
        },

        /**
         * Close all dropdown popups
         */
        closeAllDropdowns: function () {
            var dropdowns = document.querySelectorAll('.dropdown-popup');
            dropdowns.forEach(function (dropdown) {
                dropdown.classList.remove('show');
            });
        },

        /**
         * Update slider value display
         */
        updateSliderValue: function (sliderId, text) {
            var slider = document.getElementById(sliderId);
            if (slider) {
                var valueSpan = slider.parentNode.querySelector('.slider-value');
                if (valueSpan) {
                    valueSpan.textContent = text;
                }
            }
        },

        /**
         * Get total number of pages
         */
        getTotalPages: function () {
            if (!this.viewer) return 1;

            // Try multiple methods to get total pages
            if (this.viewer.tileSources && Array.isArray(this.viewer.tileSources)) {
                console.log('Total pages from tileSources:', this.viewer.tileSources.length);
                return this.viewer.tileSources.length;
            }

            if (this.viewer.sequenceMode && this.viewer._sequenceIndex !== undefined) {
                // If we're in sequence mode, the tileSources should be available
                return this.viewer.tileSources ? this.viewer.tileSources.length : 1;
            }

            if (this.viewer.world && typeof this.viewer.world.getItemCount === 'function') {
                var itemCount = this.viewer.world.getItemCount();
                console.log('Total pages from world.getItemCount:', itemCount);
                return Math.max(1, itemCount);
            }

            console.log('Defaulting to 1 page');
            return 1;
        },

        /**
         * Update page indicator display
         */
        updatePageIndicator: function () {
            if (!this.viewer) return;

            var pageInputEl = document.getElementById('page-input');
            var totalPagesEl = document.getElementById('total-pages');

            if (pageInputEl && totalPagesEl) {
                var currentPageIndex = this.viewer.currentPage(); // 0-based
                var currentPage = currentPageIndex + 1; // Convert to 1-based for display
                var totalPages = this.getTotalPages();

                console.log('Page indicator update - Index:', currentPageIndex, 'Display:', currentPage, 'Total:', totalPages);

                pageInputEl.value = currentPage;
                pageInputEl.max = totalPages;
                totalPagesEl.textContent = totalPages;

                // Update navigation button states
                var prevBtn = document.getElementById('viewer-prev-page');
                var nextBtn = document.getElementById('viewer-next-page');

                if (prevBtn) {
                    var canGoPrev = totalPages > 1 && currentPageIndex > 0;
                    prevBtn.disabled = !canGoPrev;
                    console.log('Previous button enabled:', canGoPrev);
                }
                if (nextBtn) {
                    var canGoNext = totalPages > 1 && currentPageIndex < totalPages - 1;
                    nextBtn.disabled = !canGoNext;
                    console.log('Next button enabled:', canGoNext);
                }
            }
        },

        /**
         * Rotate the image by 90 degrees
         */
        rotate: function () {
            if (!this.viewer) return;

            this.currentRotation = (this.currentRotation + 90) % 360;
            this.viewer.viewport.setRotation(this.currentRotation);
        },

        /**
         * Reset all viewer settings to default
         */
        reset: function () {
            if (!this.viewer) return;

            // Reset rotation
            this.currentRotation = 0;
            this.viewer.viewport.setRotation(0);

            // Reset zoom and pan
            this.viewer.viewport.goHome(true);

            // Reset filters
            this.filters.brightness = 100;
            this.filters.contrast = 100;
            this.applyFilters();

            // Reset slider values
            var contrastSlider = document.getElementById('contrast-slider');
            var brightnessSlider = document.getElementById('brightness-slider');

            if (contrastSlider) {
                contrastSlider.value = 100;
            }
            if (brightnessSlider) {
                brightnessSlider.value = 100;
            }

            this.closeAllDropdowns();
        },

        /**
         * Apply CSS filters for brightness and contrast
         */
        applyFilters: function () {
            if (!this.viewer) return;

            var canvas = this.viewer.canvas;
            if (canvas) {
                var filterValue = 'brightness(' + this.filters.brightness + '%) contrast(' + this.filters.contrast + '%)';
                canvas.style.filter = filterValue;
                canvas.style.webkitFilter = filterValue; // Safari compatibility
            }
        },

        /**
         * Destroy controls and clean up event listeners
         */
        destroy: function () {
            this.closeAllDropdowns();
            
            // Remove all tracked event listeners
            for (var id in this.boundEvents) {
                var element = document.getElementById(id.replace('_slider', '').replace('_change', '').replace('_keypress', ''));
                if (element && this.boundEvents[id]) {
                    if (id.includes('_slider')) {
                        element.removeEventListener('input', this.boundEvents[id]);
                    } else if (id.includes('_change')) {
                        element.removeEventListener('change', this.boundEvents[id]);
                    } else if (id.includes('_keypress')) {
                        element.removeEventListener('keypress', this.boundEvents[id]);
                    } else {
                        element.removeEventListener('click', this.boundEvents[id]);
                    }
                }
            }
            this.boundEvents = {};
        }
    };

    /**
     * Global function to initialize viewer controls
     * Usage: window.initViewerControls(viewerInstance)
     */
    window.initViewerControls = function (viewerInstance) {
        if (!viewerInstance) {
            console.warn('ViewerControls: No viewer instance provided');
            return null;
        }

        // Destroy any existing controls first to prevent duplicate event bindings
        if (window.viewerControlsInstance && typeof window.viewerControlsInstance.destroy === 'function') {
            console.log('Destroying existing viewer controls instance');
            window.viewerControlsInstance.destroy();
        }

        console.log('Creating new viewer controls instance');
        window.viewerControlsInstance = new ViewerControls(viewerInstance);
        return window.viewerControlsInstance;
    };

    // Also expose the class for direct usage
    window.ViewerControls = ViewerControls;

})(window);