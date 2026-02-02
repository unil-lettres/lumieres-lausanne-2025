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

(function () {
  'use strict';

  // Constants and helpers ---------------------------------------------------
  var STORAGE_KEY_LAYOUT = 'transcription-layout-mode';
  var STORAGE_KEY_SYNC = 'transcription-sync-enabled';
  var DEFAULT_LAYOUT = 'split-view';
  var SCROLL_SYNC_DELAY = 150;
  var SMOOTH_SCROLL_DURATION = 600;
  var PAGE_SYNC_INIT_DELAY = 500;
  var SCROLL_THRESHOLD_OFFSET = 60; // px from container top
  var SCROLL_TARGET_OFFSET = 50;   // px offset for target scroll position

  function log() {
    if (window?.console) console.log.apply(console, arguments);
  }
  function warn() {
    if (window?.console) console.warn.apply(console, arguments);
  }
  function error() {
    if (window?.console) console.error.apply(console, arguments);
  }

  // Entrypoint -------------------------------------------------------------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    var cfg = window.TranscriptionConfig || {};
    
    // Enable synchronization by default (button was removed from UI)
    // The sync functionality works automatically in split-view mode
    window.TranscriptionSyncEnabled = true;
    log('[Sync] Synchronization initialized as always-enabled');
    
    setupLayoutToggles(cfg);
    initializeModeAvailability(); // PHASE 3: Check content availability
    setupOptionsMenu();
    if (cfg.hasViewer && cfg.iiifUrl) {
      setupViewer(cfg);
    }
  }

  // Layout toggle logic ----------------------------------------------------
  function setupLayoutToggles(cfg) {
    var hasViewer = !!cfg.hasViewer;

    if (!hasViewer) {
      document.body.setAttribute('data-layout-mode', 'text-only');
      try { sessionStorage.removeItem(STORAGE_KEY_LAYOUT); } catch (_) {}
      return;
    }

    var savedLayout = null;
    try { savedLayout = sessionStorage.getItem(STORAGE_KEY_LAYOUT); } catch (_) {}
    var initialLayout = savedLayout || DEFAULT_LAYOUT;

    document.body.setAttribute('data-layout-mode', initialLayout);
    
    var buttons = document.querySelectorAll('.layout-btn');
    updateActiveButton(buttons, initialLayout);

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        // Skip options menu button
        if (btn.id === 'options-menu-btn') return;
        
        var newLayout = btn.getAttribute('data-layout');
        
        log('[Layout Toggle] Button clicked:', e.target);
        log('[Layout Toggle] New layout:', newLayout);
        
        updateActiveButton(buttons, newLayout);
        document.body.setAttribute('data-layout-mode', newLayout);
        
        try { sessionStorage.setItem(STORAGE_KEY_LAYOUT, newLayout); } catch (_) {}

        // Close options dropdown when switching modes
        var optionsDropdown = document.getElementById('options-dropdown');
        var optionsBtn = document.getElementById('options-menu-btn');
        if (optionsDropdown && optionsBtn) {
          optionsDropdown.classList.remove('show');
          optionsBtn.classList.remove('active');
        }

        // PHASE 3: Update options menu for this mode
        updateOptionsMenuForMode(newLayout);
        
        resetViewerZoom();
      });
    });
  }

  function updateActiveButton(buttons, layoutName) {
    buttons.forEach(function (b) { b.classList.remove('active'); });
    var activeBtn = document.querySelector('.layout-btn[data-layout="' + layoutName + '"]');
    if (activeBtn) activeBtn.classList.add('active');
  }

  // PHASE 3: Mode availability logic -------------------------------------
  /**
   * Initialize mode availability based on content
   */
  function initializeModeAvailability() {
    var container = document.getElementById('layout-toggle-buttons');
    if (!container) {
      log('[Mode Availability] Container not found');
      return;
    }
    
    var hasFacsimile = container.dataset.hasFacsimile === 'true';
    var hasTranscription = container.dataset.hasTranscription === 'true';
    
    var textBtn = container.querySelector('.text-only-btn');
    var splitBtn = container.querySelector('.split-view-btn');
    var viewerBtn = container.querySelector('.viewer-only-btn');
    var optionsBtn = document.getElementById('options-menu-btn');
    
    if (!textBtn || !splitBtn || !viewerBtn || !optionsBtn) {
      log('[Mode Availability] Some buttons not found');
      return;
    }
    
    // Case 1: Only facsimile
    if (!hasTranscription && hasFacsimile) {
      textBtn.disabled = true;
      splitBtn.disabled = true;
      viewerBtn.disabled = false;
      optionsBtn.disabled = true;
      setLayout('viewer-only'); // Force viewer mode
      log('[Mode Availability] Only facsimile available - forced viewer-only mode');
    }
    
    // Case 2: Only transcription
    else if (hasTranscription && !hasFacsimile) {
      textBtn.disabled = false;
      splitBtn.disabled = true;
      viewerBtn.disabled = true;
      optionsBtn.disabled = false;
      setLayout('text-only'); // Force text mode
      log('[Mode Availability] Only transcription available - forced text-only mode');
    }
    
    // Case 3: Both (normal case)
    else if (hasTranscription && hasFacsimile) {
      textBtn.disabled = false;
      splitBtn.disabled = false;
      viewerBtn.disabled = false;
      optionsBtn.disabled = false;
      // Default already set in setupLayoutToggles (split-view active)
      log('[Mode Availability] Both transcription and facsimile available');
    }
    
    log('[Facsimile Viewer] Availability:', {
      hasFacsimile: hasFacsimile,
      hasTranscription: hasTranscription,
      textEnabled: !textBtn.disabled,
      splitEnabled: !splitBtn.disabled,
      viewerEnabled: !viewerBtn.disabled,
      optionsEnabled: !optionsBtn.disabled
    });
  }

  /**
   * Helper to set layout mode (used by initializeModeAvailability)
   */
  function setLayout(layoutMode) {
    document.body.setAttribute('data-layout-mode', layoutMode);
    var buttons = document.querySelectorAll('.layout-btn');
    updateActiveButton(buttons, layoutMode);
    
    try { sessionStorage.setItem(STORAGE_KEY_LAYOUT, layoutMode); } catch (_) {}
    
    // Update options menu for this mode
    updateOptionsMenuForMode(layoutMode);
  }

  /**
   * Update options menu visibility based on current mode
   */
  function updateOptionsMenuForMode(mode) {
    var optionsDropdown = document.getElementById('options-dropdown');
    var optionsBtn = document.getElementById('options-menu-btn');
    var hasFacsimile = document.getElementById('layout-toggle-buttons')?.dataset.hasFacsimile === 'true';
    
    if (!optionsDropdown || !optionsBtn) return;
    
    // Hide options menu if in viewer-only mode
    if (mode === 'viewer-only') {
      optionsDropdown.innerHTML = '<div style="padding: 8px; color: #999;">Aucune option disponible</div>';
      optionsBtn.disabled = true;
      log('[Options Menu] Viewer-only mode - no options');
    }
    // Show text options
    else if (mode === 'text-only') {
      optionsDropdown.innerHTML = [
        '<label class="option-item">',
        '  <input type="checkbox" data-option="use-diplomatic-version" ' + (sessionStorage.getItem('trans-option-use-diplomatic-version') === 'true' ? 'checked' : '') + '>',
        '  <span>Version diplomatique</span>',
        '</label>',
        '<label class="option-item">',
        '  <input type="checkbox" data-option="hide-linebreaks" ' + (sessionStorage.getItem('trans-option-hide-linebreaks') === 'true' ? 'checked' : '') + '>',
        '  <span>Masquer les retours à la ligne</span>',
        '</label>',
        '<label class="option-item">',
        '  <input type="checkbox" data-option="show-toc" ' + (sessionStorage.getItem('trans-option-show-toc') === 'true' ? 'checked' : '') + '>',
        '  <span>Afficher la table des matières</span>',
        '</label>',
        '<label class="option-item">',
        '  <input type="checkbox" data-option="show-marginalia" ' + (sessionStorage.getItem('trans-option-show-marginalia') === 'true' ? 'checked' : '') + '>',
        '  <span>Afficher les notes en marge</span>',
        '</label>'
      ].join('');
      optionsBtn.disabled = false;
      log('[Options Menu] Text-only mode options set');
    }
    // Show split-view options
    else if (mode === 'split-view') {
      optionsDropdown.innerHTML = [
        '<label class="option-item">',
        '  <input type="checkbox" data-option="use-edited-version" ' + (sessionStorage.getItem('trans-option-use-edited-version') === 'true' ? 'checked' : '') + '>',
        '  <span>Version éditée</span>',
        '</label>',
        '<label class="option-item">',
        '  <input type="checkbox" data-option="hide-linebreaks" ' + (sessionStorage.getItem('trans-option-hide-linebreaks') === 'true' ? 'checked' : '') + '>',
        '  <span>Masquer les retours à la ligne</span>',
        '</label>',
        '<label class="option-item">',
        '  <input type="checkbox" data-option="show-toc" ' + (sessionStorage.getItem('trans-option-show-toc') === 'true' ? 'checked' : '') + '>',
        '  <span>Afficher la table des matières</span>',
        '</label>'
      ].join('');
      optionsBtn.disabled = false;
      log('[Options Menu] Split-view mode options set');
    }
    
    // Re-bind checkbox event listeners
    bindOptionCheckboxes();
  }

  /**
   * Bind event listeners to all option checkboxes
   */
  function bindOptionCheckboxes() {
    var optionsDropdown = document.getElementById('options-dropdown');
    var checkboxes = optionsDropdown?.querySelectorAll('input[type="checkbox"]') || [];
    
    checkboxes.forEach(function(checkbox) {
      // Remove old listeners by cloning
      var newCheckbox = checkbox.cloneNode(true);
      checkbox.parentNode.replaceChild(newCheckbox, checkbox);
      
      // Add new listener
      newCheckbox.addEventListener('change', function() {
        var key = 'trans-option-' + this.dataset.option;
        sessionStorage.setItem(key, this.checked);
        log('[Options]', this.dataset.option, '=', this.checked);
        
        // TODO: Phase 4 - Apply visual changes
        // Examples:
        // - Use edited version: show/hide edit marks
        // - Hide linebreaks: remove <br> visualization
        // - Show TOC: toggle TOC panel visibility
        // - Show marginalia: apply margin note styling
      });
    });
  }

  // Options menu management ------------------------------------------------
  function setupOptionsMenu() {
    var optionsBtn = document.getElementById('options-menu-btn');

    var optionsDropdown = document.getElementById('options-dropdown');
    
    if (!optionsBtn || !optionsDropdown) {
      log('[Options Menu] Elements not found, skipping setup');
      return;
    }
    
    // Toggle menu on button click
    optionsBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      var isShowing = optionsDropdown.classList.contains('show');
      
      if (isShowing) {
        optionsDropdown.classList.remove('show');
        optionsBtn.classList.remove('active');
      } else {
        optionsDropdown.classList.add('show');
        optionsBtn.classList.add('active');
      }
      
      log('[Options Menu] Dropdown', isShowing ? 'closed' : 'opened');
    });
    
    // Close menu on outside click
    document.addEventListener('click', function(e) {
      if (!e.target.closest('#layout-toggle-buttons')) {
        optionsDropdown.classList.remove('show');
        optionsBtn.classList.remove('active');
      }
    });
    
    // Handle option checkbox changes
    var checkboxes = optionsDropdown.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(function(checkbox) {
      // Restore previous state from sessionStorage
      var optionKey = 'trans-option-' + checkbox.dataset.option;
      try {
        var saved = sessionStorage.getItem(optionKey);
        if (saved === 'true') {
          checkbox.checked = true;
        }
      } catch (_) {}
      
      // Save on change
      checkbox.addEventListener('change', function() {
        try {
          sessionStorage.setItem(optionKey, this.checked);
        } catch (_) {}
        log('[Options Menu] Option changed:', this.dataset.option, '=', this.checked);
        // TODO: Phase 3 - Apply visual changes based on option
      });
    });
  }

  function resetViewerZoom() {
    log('[Layout Toggle] Attempting to reset zoom...');
    if (window.lumiereViewer?.viewport) {
      requestAnimationFrame(function() {
        setTimeout(function() {
          log('[Layout Toggle] Resetting viewport zoom to fit image');
          window.lumiereViewer.viewport.goHome(true);
        }, 200);
      });
    } else {
      log('[Layout Toggle] WARNING: lumiereViewer or viewport not available!');
    }
  }

  // Viewer + IIIF ----------------------------------------------------------
  function setupViewer(cfg) {
    if (!window.OpenSeadragon) {
      error('[Viewer] OpenSeadragon not available');
      return;
    }

    var iiifUrl = cfg?.iiifUrl;
    if (!iiifUrl || !iiifUrl.trim()) return;

    if (iiifUrl.indexOf('manifest') !== -1) {
      fetch(iiifUrl)
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function (manifest) {
          var tileSources = extractTileSourcesFromManifest(manifest);
          if (tileSources.length) initViewer(tileSources, cfg);
          else showError('Erreur: Impossible d\'extraire les images du manifeste IIIF');
        })
        .catch(function (e) {
          error('[IIIF] Failed to load manifest:', e);
          showError('Erreur: Impossible de charger le manifeste IIIF<br><small>' + (e && e.message ? e.message : e) + '</small>');
        });
    } else {
      initViewer([iiifUrl], cfg);
    }
  }

  function extractTileSourcesFromManifest(manifest) {
    try { log('[IIIF] Loaded manifest:', manifest); } catch (_) {}
    var tileSources = [];

    // IIIF v3
    if (manifest?.items?.length) {
      manifest.items.forEach(function (canvas) {
        var tileSource = extractTileSourceIIIFv3(canvas);
        if (tileSource) tileSources.push(tileSource);
      });
    }
    // IIIF v2
    else if (manifest?.sequences?.[0]) {
      var canvases = manifest.sequences[0].canvases || [];
      canvases.forEach(function (canvas) {
        var tileSource = extractTileSourceIIIFv2(canvas);
        if (tileSource) tileSources.push(tileSource);
      });
    }

    try { log('[IIIF] Total tile sources extracted:', tileSources.length); } catch (_) {}
    return tileSources;
  }

  function extractTileSourceIIIFv3(canvas) {
    try {
      var annPage = canvas.items?.[0];
      var ann = annPage?.items?.[0];
      var body = ann?.body;
      var svc = body?.service?.[0];
      var id = svc?.['@id'] || svc?.id;
      return id ? id.replace(/\/?$/, '') + '/info.json' : null;
    } catch (_) {
      return null;
    }
  }

  function extractTileSourceIIIFv2(canvas) {
    try {
      var img = canvas.images?.[0];
      var res = img?.resource;
      var svc = res?.service;
      var id = svc?.['@id'] || svc?.id;
      return id ? id.replace(/\/?$/, '') + '/info.json' : null;
    } catch (_) {
      return null;
    }
  }

  function showError(message) {
    var viewerDiv = document.getElementById('openseadragon-viewer');
    if (viewerDiv) {
      viewerDiv.innerHTML = '<div style="color: white; padding: 20px; text-align: center;">' + message + '</div>';
    }
  }

  function initViewer(tileSources, cfg) {
    var initialPageIndex = computeStartCanvasIndex(tileSources.length, cfg?.facsimileStartCanvas);
    var viewer = OpenSeadragon({
      id: 'openseadragon-viewer',
      prefixUrl: (window.STATIC_PREFIX_OPENSEADRAGON || '/static/js/lib/openseadragon/images/') ,
      tileSources: tileSources,
      sequenceMode: true,
      initialPage: initialPageIndex,
      preserveViewport: false,
      preserveImageSizeOnResize: true,
      visibilityRatio: 0.5,
      showNavigationControl: false,
      showZoomControl: false,
      showHomeControl: false,
      showFullPageControl: false,
      showSequenceControl: false,
      showNavigator: tileSources.length > 1,
      navigatorPosition: 'TOP_RIGHT',
      navigatorHeight: '120px',
      navigatorWidth: '150px',
      showReferenceStrip: tileSources.length > 1,
      referenceStripScroll: 'horizontal'
    });

    // Persist sequence size for sync logic
    viewer.lumiereSequenceCount = tileSources.length;

    // Store viewer globally for access from layout toggle
    window.lumiereViewer = viewer;

    viewer.addHandler('open', function () {
      if (window.initViewerControls) window.initViewerControls(viewer);
      initPageSync(viewer, cfg);
    });
  }

  function computeStartCanvasIndex(seqCount, startCanvas1Based) {
    var raw = parseInt(startCanvas1Based, 10);
    var start0 = isFinite(raw) && raw > 0 ? raw - 1 : 0;
    if (seqCount && start0 >= seqCount) start0 = seqCount - 1;
    return Math.max(0, start0);
  }

  function initPageSync(viewer, cfg) {
    var transcriptionBox = document.getElementById('transcription-data');
    if (!transcriptionBox || !viewer) return;

    log('[Page Sync] Initializing page synchronization...');

    var lastSyncedPage = (typeof viewer.currentPage === 'function') ? viewer.currentPage() : null;
    var isProgrammaticScrollSync = false;
    var isProgrammaticViewerSync = false;
    var isProgrammaticBlankSkip = false;
    var scrollTimeout = null;
    var isUserScrolling = false;
    var lastMarkerIndicatorKey = null;
    var isBeforeFirstMarker = true;

    var seqCount = viewer.lumiereSequenceCount || viewer.tileSources?.length || 0;
    var startCanvasIndex0 = computeStartCanvasIndex(seqCount, cfg?.facsimileStartCanvas);
    
    log('[Page Sync] Found sequence with', seqCount, 'page(s).');

    // Extract and wrap page tags
    var markerCount = wrapPageBreakMarkers(transcriptionBox, seqCount, startCanvasIndex0);
    if (!markerCount) {
      log('[Page Sync] No page markers found; scroll synchronization disabled for this transcription.');
      return;
    }

    function updateMarkerIndicator(canvasIndex) {
      var el = document.getElementById('viewer-marker-indicator');
      var tag = (!isBeforeFirstMarker && typeof canvasIndex === 'number') ? findPageTagByCanvasIndex(transcriptionBox, canvasIndex) : null;
      if (window.TranscriptionSyncEnabled && tag && isBlankPageTag(tag)) {
        tag = findNonBlankTagForCanvasIndex(transcriptionBox, canvasIndex);
      }
      var folio = tag ? (tag.getAttribute('data-folio') || '') : '';
      var markerIdx = tag ? (tag.getAttribute('data-marker-index') || '') : '';
      var key = String(isBeforeFirstMarker ? 'before' : canvasIndex) + '|' + String(markerIdx) + '|' + String(folio);

      if (el) {
        el.textContent = (!isBeforeFirstMarker && folio) ? ('Repère: <' + folio + '>') : 'Repère: —';

        if (key !== lastMarkerIndicatorKey) {
          el.classList.remove('blink');
          // force reflow to restart animation
          void el.offsetWidth; // eslint-disable-line no-unused-expressions
          el.classList.add('blink');
        }
      }

      // Also show a short-lived toast over the canvas area when the marker changes.
      lastMarkerIndicatorKey = key;
    }

    function maybeSkipBlankCanvas(canvasIndex) {
      var tag = findPageTagByCanvasIndex(transcriptionBox, canvasIndex);
      if (!tag || !isBlankPageTag(tag)) return false;

      var targetTag = findNonBlankTagForCanvasIndex(transcriptionBox, canvasIndex);
      if (!targetTag) return false;

      var targetIndex = parseInt(targetTag.getAttribute('data-canvas-index'), 10);
      if (!isFinite(targetIndex) || targetIndex === canvasIndex) return false;

      log('[Page Sync] Skipping blank canvas', canvasIndex, '→', targetIndex);
      isProgrammaticBlankSkip = true;
      viewer.goToPage(targetIndex);
      return true;
    }

    // Sync viewer page to transcription
    try {
      viewer.addHandler('page', function (ev) {
        if (typeof ev.page !== 'number') return;

        if (isProgrammaticBlankSkip) {
          isProgrammaticBlankSkip = false;
        } else if (window.TranscriptionSyncEnabled && maybeSkipBlankCanvas(ev.page)) {
          return;
        }

        if (window.TranscriptionSyncEnabled && !isProgrammaticScrollSync && !isUserScrolling && ev.page !== lastSyncedPage) {
          log('[Page Sync] Viewer page changed by user → syncing transcription to page', ev.page);
          syncTranscriptionToViewer(ev.page, transcriptionBox);
        }
        
        lastSyncedPage = ev.page;
        updateMarkerIndicator(ev.page);
      });
    } catch (e) {
      warn('[Page Sync] Could not bind viewer page handler', e);
    }

    // Sync transcription scroll to viewer page
    function syncTranscriptionToViewer(canvasIndex) {
      if (!window.TranscriptionSyncEnabled) {
        log('[Page Sync] Sync disabled - skipping transcription scroll');
        return;
      }

      var targetTag = findPageTagByCanvasIndex(transcriptionBox, canvasIndex);
      if (window.TranscriptionSyncEnabled && targetTag && isBlankPageTag(targetTag)) {
        targetTag = findNonBlankTagForCanvasIndex(transcriptionBox, canvasIndex);
      }
      if (!targetTag) {
        warn('[Page Sync] No page tag found for canvas index', canvasIndex);
        return;
      }

      var folio = targetTag.getAttribute('data-folio') || '?';
      var markerIdx = targetTag.getAttribute('data-marker-index') || '?';
      log('[Page Sync] Found page marker for canvas', canvasIndex, '(marker', markerIdx + ', folio', folio + ') - scrolling...');
      
      isProgrammaticViewerSync = true;
      
      var containerRect = transcriptionBox.getBoundingClientRect();
      var tagRect = targetTag.getBoundingClientRect();
      var scrollOffset = tagRect.top - containerRect.top - SCROLL_TARGET_OFFSET;
      
      transcriptionBox.scrollBy({
        top: scrollOffset,
        behavior: 'smooth'
      });
      
      setTimeout(function () { 
        isProgrammaticViewerSync = false; 
        log('[Page Sync] ✓ Transcription scrolled to canvas', canvasIndex);
      }, SMOOTH_SCROLL_DURATION);
    }

    // Sync viewer page from transcription scroll
    function syncViewerToScroll() {
      if (!window.TranscriptionSyncEnabled) {
        log('[Page Sync] Sync disabled - skipping viewer scroll');
        return;
      }

      if (isProgrammaticViewerSync) {
        log('[Page Sync] Skipping scroll sync (viewer-initiated scroll in progress)');
        return;
      }

      var containerRect = transcriptionBox.getBoundingClientRect();
      var thresholdTop = containerRect.top + SCROLL_THRESHOLD_OFFSET;

      var visible = findVisiblePageTag(transcriptionBox, thresholdTop, transcriptionBox.scrollTop || 0);
      if (window.TranscriptionSyncEnabled && visible && isBlankPageTag(visible)) {
        var nonBlankVisible = findNextNonBlankTag(transcriptionBox, visible);
        visible = nonBlankVisible || visible;
      }
      // If we are above the first marker, stick to the start canvas and clear the repère.
      if (visible === null) {
        isBeforeFirstMarker = true;
        var startIndex = Math.min(Math.max(startCanvasIndex0, 0), seqCount ? seqCount - 1 : 0);
        if (lastSyncedPage !== startIndex) {
          log('[Page Sync] At top of transcription → go to start canvas', startIndex);
          isProgrammaticScrollSync = true;
          lastSyncedPage = startIndex;
          viewer.goToPage(startIndex);
          setTimeout(function () { isProgrammaticScrollSync = false; }, 500);
        }
        updateMarkerIndicator(null);
        return;
      }
      isBeforeFirstMarker = false;

      var canvasIndexStr = visible.getAttribute('data-canvas-index');
      var canvasIndex = canvasIndexStr !== null ? parseInt(canvasIndexStr, 10) : 0;
      var folio = visible.getAttribute('data-folio') || '?';
      var markerIdx = visible.getAttribute('data-marker-index') || '?';
      
      if (!seqCount) { 
        warn('[Page Sync] Viewer has no items yet – skipping sync'); 
        return; 
      }

      var targetIndex = Math.min(Math.max(canvasIndex, 0), seqCount - 1);
      
      if (lastSyncedPage !== targetIndex) {
        log('[Page Sync] ✓ Switching viewer to canvas index', targetIndex, '(marker', markerIdx + ', folio', folio + ')');
        isProgrammaticScrollSync = true;
        lastSyncedPage = targetIndex;
        viewer.goToPage(targetIndex);
        
        setTimeout(function () { 
          isProgrammaticScrollSync = false; 
        }, 500);
      }
    }

    transcriptionBox.addEventListener('scroll', function () {
      isUserScrolling = true;
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(function() {
        isUserScrolling = false;
        syncViewerToScroll();
      }, SCROLL_SYNC_DELAY);
    });

    // Initial alignment: only if current viewer page has a matching tag
    setTimeout(function () {
      var current = (viewer && typeof viewer.currentPage === 'function') ? viewer.currentPage() : null;
      if (current !== null && window.TranscriptionSyncEnabled && maybeSkipBlankCanvas(current)) {
        return;
      }
      if (current !== null && findPageTagByCanvasIndex(transcriptionBox, current)) {
        syncViewerToScroll();
      } else {
        log('[Page Sync] Initial alignment skipped (no matching tag for current viewer page)');
      }
      if (current !== null) updateMarkerIndicator(current);
    }, PAGE_SYNC_INIT_DELAY);

    // Expose a one-shot sync to current scroll position for external triggers (e.g., toggling sync on)
    window.lumiereSyncViewerToScroll = syncViewerToScroll;
  }

  function unwrapExistingPageTags(html) {
    if (!html) return html;
    return html.replace(/<span[^>]*class=["']page-tag["'][^>]*>(.*?)<\/span>/gi, '$1');
  }

  function wrapPageBreakMarkers(transcriptionBox, seqCount, startCanvasIndex0) {
    var transcriptionHTML = unwrapExistingPageTags(transcriptionBox.innerHTML || '');

    // Inject a virtual first marker <1> at the very start so the area before the
    // first explicit marker is mapped to the start canvas without requiring a
    // manual <0>. Keep it minimally visible to be pickable by geometry checks.
    transcriptionHTML =
      '<span class="page-tag page-tag-virtual" ' +
      'data-folio="1" data-marker-index="1" data-canvas-index="' + startCanvasIndex0 + '" ' +
      'id="page-tag-virtual-0" style="display:block;height:1px;overflow:hidden;padding:0;margin:0;"></span>' +
      transcriptionHTML;

    // Marker patterns observed in transcription 1080:
    // - <1>, <2>, <10>, ...
    // - <4v>, <6v>, <10v>, ...
    // - sometimes HTML-escaped: &lt;4v&gt;
    //
    // We treat each marker occurrence as a sequential page-break.
    // Require real angle brackets and digits (optionally r/v) with word-boundaries around.
    // Avoid inline matches by checking surrounding chars at runtime.
    var reFolio = /(?:&lt;|<)\s*(\d{1,3})\s*([rv])?\s*(?:&gt;|>)/gi;

    var markerIndex = 1; // 1 is already reserved for the virtual first marker
    transcriptionHTML = transcriptionHTML.replace(reFolio, function (markerText, num, rv, offset, html) {
      var before = offset > 0 ? html.charAt(offset - 1) : '';
      var after = offset + markerText.length < html.length ? html.charAt(offset + markerText.length) : '';
      if (before && /[0-9A-Za-z]/.test(before)) {
        return markerText;
      }
      if (after && /[0-9A-Za-z]/.test(after)) {
        return markerText;
      }

      // Extra guards: must really be a clean <number[r|v]> token once decoded
      var plain = markerText.replace(/&lt;/gi, '<').replace(/&gt;/gi, '>');
      if (!/^<\s*\d{1,3}\s*[rv]?\s*>$/.test(plain)) {
        return markerText;
      }

      var numValue = parseInt(num, 10);
      var isBlank = isFinite(numValue) && numValue === 0;
      var folio = String(num || '') + String(rv || '');
      var canvasIndex = startCanvasIndex0 + markerIndex;

      if (seqCount > 0) {
        if (canvasIndex < 0) canvasIndex = 0;
        if (canvasIndex >= seqCount) canvasIndex = seqCount - 1;
      }

      var wrapped =
        '<span class="page-tag' + (isBlank ? ' page-tag-blank' : '') + '"' +
        ' data-folio="' + folio + '"' +
        (isBlank ? ' data-blank="true"' : '') +
        ' data-marker-index="' + (markerIndex + 1) + '"' +
        ' data-canvas-index="' + canvasIndex + '"' +
        ' id="page-tag-' + markerIndex + '">' +
        markerText +
        '</span>';

      markerIndex += 1;
      return wrapped;
    });

    transcriptionBox.innerHTML = transcriptionHTML;

    // Remove any page tags that ended up inside a footnote-like context (sup/a/footnote classes)
    try {
      var tags = transcriptionBox.querySelectorAll('.page-tag');
      tags.forEach(function (el) {
        if (el.closest('sup') || el.closest('a') || el.closest('.footnote') || el.closest('.note') || el.closest('.footnote-ref')) {
          el.replaceWith(el.textContent || '');
        }
      });
    } catch (e) {
      warn('[Page Sync] Could not clean footnote page tags', e);
    }

    log('[Page Sync] Wrapped', markerIndex, 'page-break markers; start canvas index', startCanvasIndex0);
    return markerIndex;
  }

  function findPageTagByCanvasIndex(transcriptionBox, canvasIndex) {
    var tags = transcriptionBox.querySelectorAll('.page-tag');
    for (var i = 0; i < tags.length; i++) {
      var tagCanvasIndex = parseInt(tags[i].getAttribute('data-canvas-index'), 10);
      if (tagCanvasIndex === canvasIndex) {
        return tags[i];
      }
    }
    // No exact match: do not force scroll
    return null;
  }

  function isBlankPageTag(tag) {
    return !!tag && tag.getAttribute('data-blank') === 'true';
  }

  function findNextNonBlankTagFromIndex(tags, startIndex) {
    for (var i = startIndex + 1; i < tags.length; i++) {
      if (!isBlankPageTag(tags[i])) return tags[i];
    }
    for (var j = startIndex - 1; j >= 0; j--) {
      if (!isBlankPageTag(tags[j])) return tags[j];
    }
    return null;
  }

  function findNextNonBlankTag(transcriptionBox, startTag) {
    if (!startTag) return null;
    var tags = transcriptionBox.querySelectorAll('.page-tag');
    var startIndex = -1;
    for (var i = 0; i < tags.length; i++) {
      if (tags[i] === startTag) {
        startIndex = i;
        break;
      }
    }
    if (startIndex === -1) return null;
    return findNextNonBlankTagFromIndex(tags, startIndex);
  }

  function findNonBlankTagForCanvasIndex(transcriptionBox, canvasIndex) {
    var tags = transcriptionBox.querySelectorAll('.page-tag');
    var matchIndex = -1;
    for (var i = 0; i < tags.length; i++) {
      var tagCanvasIndex = parseInt(tags[i].getAttribute('data-canvas-index'), 10);
      if (tagCanvasIndex === canvasIndex) {
        matchIndex = i;
        break;
      }
    }
    if (matchIndex === -1) return null;
    if (!isBlankPageTag(tags[matchIndex])) return tags[matchIndex];
    return findNextNonBlankTagFromIndex(tags, matchIndex);
  }

  function findVisiblePageTag(transcriptionBox, thresholdTop, scrollTop) {
    var tags = transcriptionBox.querySelectorAll('.page-tag');
    if (!tags.length) return null;

    var containerRect = transcriptionBox.getBoundingClientRect();
    var viewportBottom = containerRect.bottom;
    var viewportTop = containerRect.top;

    // If we truly are at the very top (no scroll), treat as before-first.
    if (scrollTop <= 0) return null;

    var inView = [];
    for (var i = 0; i < tags.length; i++) {
      var r = tags[i].getBoundingClientRect();
      var intersects = r.bottom >= viewportTop && r.top <= viewportBottom;
      if (!intersects) continue;
      inView.push({ el: tags[i], rect: r });
    }

    if (!inView.length) {
      // Pick the closest tag above the viewport, or if none, the closest below.
      var above = null;
      var below = null;
      for (var j = 0; j < tags.length; j++) {
        var rr = tags[j].getBoundingClientRect();
        if (rr.top <= viewportTop) above = tags[j];
        else if (!below) below = tags[j];
      }
      return above || below || tags[0] || null;
    }

    // Prefer the last tag in view that has crossed the threshold
    var candidate = null;
    for (var j = 0; j < inView.length; j++) {
      if (inView[j].rect.top <= thresholdTop) {
        candidate = inView[j].el;
      }
    }

    if (candidate) return candidate;

    // Otherwise, take the first tag currently in view (nearest upcoming)
    return inView[0].el;
  }

  function findNearestPageTagForCanvasIndex(transcriptionBox, canvasIndex) {
    var tags = transcriptionBox.querySelectorAll('.page-tag');
    if (!tags.length) return null;

    var best = null;
    var bestIdx = -1;
    for (var i = 0; i < tags.length; i++) {
      if (isBlankPageTag(tags[i])) continue;
      var idx = parseInt(tags[i].getAttribute('data-canvas-index'), 10);
      if (!isFinite(idx)) continue;
      if (idx <= canvasIndex && idx >= bestIdx) {
        best = tags[i];
        bestIdx = idx;
      }
    }
    return best || tags[0];
  }
})();
