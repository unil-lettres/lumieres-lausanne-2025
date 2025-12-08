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

  // Small helpers -----------------------------------------------------------
  function log() {
    if (window && window.console) console.log.apply(console, arguments);
  }
  function warn() {
    if (window && window.console) console.warn.apply(console, arguments);
  }
  function error() {
    if (window && window.console) console.error.apply(console, arguments);
  }

  // Entrypoint -------------------------------------------------------------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    var cfg = window.TranscriptionConfig || {};
    setupLayoutToggles(cfg);
    if (cfg.hasViewer && cfg.iiifUrl) {
      setupViewer(cfg.iiifUrl);
    }
  }

  // Layout toggle logic ----------------------------------------------------
  function setupLayoutToggles(cfg) {
    var storageKey = 'transcription-layout-mode';
    var hasViewer = !!cfg.hasViewer;

    if (!hasViewer) {
      document.body.setAttribute('data-layout-mode', 'text-only');
      try { sessionStorage.removeItem(storageKey); } catch (_) {}
      return;
    }

    var defaultLayout = 'split-view';
    var savedLayout = null;
    try { savedLayout = sessionStorage.getItem(storageKey); } catch (_) {}
    var initialLayout = savedLayout || defaultLayout;

    document.body.setAttribute('data-layout-mode', initialLayout);
    var buttons = document.querySelectorAll('.layout-btn');
    buttons.forEach(function (b) { b.classList.remove('active'); });
    var activeBtn = document.querySelector('.layout-btn[data-layout="' + initialLayout + '"]');
    if (activeBtn) activeBtn.classList.add('active');

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        log('[Layout Toggle] Button clicked:', e.target);
        var newLayout = btn.getAttribute('data-layout');
        log('[Layout Toggle] New layout:', newLayout);
        buttons.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        document.body.setAttribute('data-layout-mode', newLayout);
        try { sessionStorage.setItem(storageKey, newLayout); } catch (_) {}

        // Reset zoom when switching mode with proper timing
        log('[Layout Toggle] Attempting to reset zoom...');
        if (window.lumiereViewer && window.lumiereViewer.viewport) {
          // Use requestAnimationFrame to wait for layout recalculation, then add extra time
          requestAnimationFrame(function() {
            setTimeout(function() {
              log('[Layout Toggle] Resetting viewport zoom to fit image');
              window.lumiereViewer.viewport.goHome(true);
            }, 200);
          });
        } else {
          log('[Layout Toggle] WARNING: lumiereViewer or viewport not available!');
        }
      });
    });
  }

  // Viewer + IIIF ----------------------------------------------------------
  function setupViewer(iiifUrl) {
    if (!window.OpenSeadragon) {
      error('[Viewer] OpenSeadragon not available');
      return;
    }

    if (!iiifUrl || !iiifUrl.trim()) return;

    if (iiifUrl.indexOf('manifest') !== -1) {
      fetch(iiifUrl)
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function (manifest) {
          var tileSources = extractTileSourcesFromManifest(manifest);
          if (tileSources.length) initViewer(tileSources);
          else showError('Erreur: Impossible d\'extraire les images du manifeste IIIF');
        })
        .catch(function (e) {
          error('[IIIF] Failed to load manifest:', e);
          showError('Erreur: Impossible de charger le manifeste IIIF<br><small>' + (e && e.message ? e.message : e) + '</small>');
        });
    } else {
      initViewer([iiifUrl]);
    }
  }

  function extractTileSourcesFromManifest(manifest) {
    try { log('[IIIF] Loaded manifest:', manifest); } catch (_) {}
    var tileSources = [];

    // IIIF v3
    if (manifest && Array.isArray(manifest.items) && manifest.items.length) {
      manifest.items.forEach(function (canvas) {
        try {
          var annPage = canvas.items && canvas.items[0];
          var ann = annPage && annPage.items && annPage.items[0];
          var body = ann && ann.body;
          var svc = body && body.service && body.service[0];
          var id = svc && (svc['@id'] || svc.id);
          if (id) tileSources.push(id.replace(/\/?$/, '') + '/info.json');
        } catch (_) {}
      });
    }
    // IIIF v2
    else if (manifest && manifest.sequences && manifest.sequences[0]) {
      var canvases = manifest.sequences[0].canvases || [];
      canvases.forEach(function (canvas) {
        try {
          var img = canvas.images && canvas.images[0];
          var res = img && img.resource;
          var svc = res && res.service;
          var id = svc && (svc['@id'] || svc.id);
          if (id) tileSources.push(id.replace(/\/?$/, '') + '/info.json');
        } catch (_) {}
      });
    }

    try { log('[IIIF] Total tile sources extracted:', tileSources.length); } catch (_) {}
    return tileSources;
  }

  function showError(message) {
    var viewerDiv = document.getElementById('openseadragon-viewer');
    if (viewerDiv) {
      viewerDiv.innerHTML = '<div style="color: white; padding: 20px; text-align: center;">' + message + '</div>';
    }
  }

  function initViewer(tileSources) {
    var viewer = OpenSeadragon({
      id: 'openseadragon-viewer',
      prefixUrl: (window.STATIC_PREFIX_OPENSEADRAGON || '/static/js/lib/openseadragon/images/') ,
      tileSources: tileSources,
      sequenceMode: true,
      initialPage: 0,
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
      initPageSync(viewer);
    });
  }

  // Page Synchronization ---------------------------------------------------
  function initPageSync(viewer) {
    var transcriptionBox = document.getElementById('transcription-data');
    if (!transcriptionBox || !viewer) return;

    log('[Page Sync] Initializing page synchronization...');

    var lastSyncedPage = (typeof viewer.currentPage === 'function') ? viewer.currentPage() : null;
    var isProgrammaticScrollSync = false; // Flag for scroll-initiated sync
    var isProgrammaticViewerSync = false; // Flag for viewer-initiated sync
    var isUserScrolling = false;          // Flag for user interaction

    // Extract page tags (five formats)
    var transcriptionHTML = transcriptionBox.innerHTML;
    var pageTagsRaw = [];
    var m;

    // Format 1: /p. 1/ style
    var reP = /\/p\.\s*(\d+)\//g;
    while ((m = reP.exec(transcriptionHTML)) !== null) {
      pageTagsRaw.push({ pageNumber: parseInt(m[1], 10), pattern: m[0], type: 'p-format' });
    }

    // Format 2: Explicit recto/verso in angle brackets <1r>, <1v>, <2r>, <2v>
    var reRV = /(?:<|&lt;)(\d+)([rv])(?:>|&gt;)/gi;
    reRV.lastIndex = 0;
    while ((m = reRV.exec(transcriptionHTML)) !== null) {
      var num = parseInt(m[1], 10);
      var side = m[2].toLowerCase();
      var calc = side === 'r' ? (num * 2 - 1) : (num * 2);
      pageTagsRaw.push({ pageNumber: calc, pattern: m[0], originalPage: num, side: side, type: 'rv-explicit' });
    }

    // Format 3: Explicit recto/verso in square brackets [1r], [1v], [2r], [2v]
    // Exclude years (4+ digits like [1763], [1788])
    var reBracketRV = /\[(\d{1,3})([rv])\]/gi;
    reBracketRV.lastIndex = 0;
    while ((m = reBracketRV.exec(transcriptionHTML)) !== null) {
      var num = parseInt(m[1], 10);
      var side = m[2].toLowerCase();
      var calc = side === 'r' ? (num * 2 - 1) : (num * 2);
      pageTagsRaw.push({ pageNumber: calc, pattern: m[0], originalPage: num, side: side, type: 'bracket-rv-explicit' });
    }

    // Format 4: Implicit recto in angle brackets <1>, <2>, <3> (number only = recto)
    // Must exclude patterns already matched by explicit recto/verso and HTML tags
    var reImplicit = /(?:<|&lt;)(\d+)(?:>|&gt;)/gi;
    reImplicit.lastIndex = 0;
    var explicitPatterns = new Set(pageTagsRaw.map(function(t) { return t.pattern; }));
    while ((m = reImplicit.exec(transcriptionHTML)) !== null) {
      // Skip if this pattern was already matched as explicit r/v
      if (explicitPatterns.has(m[0])) continue;
      
      var num = parseInt(m[1], 10);
      var calc = num * 2 - 1;  // Implicit recto: page N → image (N*2-1)
      pageTagsRaw.push({ pageNumber: calc, pattern: m[0], originalPage: num, side: 'r', type: 'rv-implicit' });
    }

    // Format 5: Implicit recto in square brackets [1], [2], [3] (number only = recto)
    // Exclude years (4+ digits) and already matched patterns
    var reBracketImplicit = /\[(\d{1,3})\]/g;
    reBracketImplicit.lastIndex = 0;
    while ((m = reBracketImplicit.exec(transcriptionHTML)) !== null) {
      // Skip if already matched
      if (explicitPatterns.has(m[0])) continue;
      
      var num = parseInt(m[1], 10);
      var calc = num * 2 - 1;  // Implicit recto: page N → image (N*2-1)
      pageTagsRaw.push({ pageNumber: calc, pattern: m[0], originalPage: num, side: 'r', type: 'bracket-rv-implicit' });
      explicitPatterns.add(m[0]);  // Add to set to avoid duplicates
    }

    // Sort by first occurrence in the HTML
    pageTagsRaw.sort(function (a, b) { return transcriptionHTML.indexOf(a.pattern) - transcriptionHTML.indexOf(b.pattern); });

    var seqCount = viewer.lumiereSequenceCount || (viewer.tileSources ? viewer.tileSources.length : 0);
    log('[Page Sync] Found', pageTagsRaw.length, 'page tags; sequence has', seqCount, 'page(s).');

    // Auto-detect offset: find the first page number in transcription
    var firstTransPageNumber = pageTagsRaw.length > 0 ? pageTagsRaw[0].pageNumber : 1;
    var pageOffset = firstTransPageNumber - 1; // Offset to map to IIIF canvas index 0
    
    log('[Page Sync] First transcription page:', firstTransPageNumber, '→ offset:', pageOffset);

    // Ensure sentinel for first page exists to allow switching back when scrolling to top
    var hasFirstPage = pageTagsRaw.some(function (t) { return t.pageNumber === firstTransPageNumber; });
    if (!hasFirstPage && pageTagsRaw.length > 0) {
      var sentinel = '<span class="page-tag" data-page="' + firstTransPageNumber + '" data-original-page="' + firstTransPageNumber + '" id="page-tag-start" data-type="sentinel" style="display:inline-block;height:0;line-height:0;overflow:hidden;"></span>';
      transcriptionHTML = sentinel + transcriptionHTML;
      log('[Page Sync] Inserted sentinel page tag for page', firstTransPageNumber, 'at the start');
    }

    // Wrap all page markers with spans tracking their mapped canvas index
    pageTagsRaw.forEach(function (tag, idx) {
      var original = tag.pageNumber;
      var canvasIndex = original - pageOffset; // Map to 0-based canvas index
      var mapped = canvasIndex;
      
      // Clamp to valid canvas range
      if (seqCount > 0) {
        if (canvasIndex < 1) {
          mapped = 1;
          warn('[Page Sync] Page', original, 'maps to canvas', canvasIndex, '< 1, clamped to 1');
        } else if (canvasIndex > seqCount) {
          mapped = seqCount;
          warn('[Page Sync] Page', original, 'maps to canvas', canvasIndex, '>', seqCount, ', clamped to', seqCount);
        }
      }
      
      var wrapped = '<span class="page-tag" data-page="' + mapped + '" data-original-page="' + original + '" data-canvas-index="' + (mapped - 1) + '" id="page-tag-' + idx + '" data-type="' + tag.type + '">' + tag.pattern + '</span>';
      transcriptionHTML = transcriptionHTML.replace(tag.pattern, wrapped);
      
      if (canvasIndex !== original) {
        log('[Page Sync] Mapped page', original, '→ canvas index', (mapped - 1), '(offset:', pageOffset + ')');
      }
    });

    transcriptionBox.innerHTML = transcriptionHTML;
    log('[Page Sync] All page tags wrapped and ready for tracking');

    // Keep lastSyncedPage in sync with viewer navigation
    // AND sync transcription scroll position when viewer page changes
    try {
      viewer.addHandler('page', function (ev) {
        if (typeof ev.page === 'number') {
          var newPage = ev.page;
          
          // Only sync transcription if this is a user-initiated page change
          // (not a programmatic change from scroll sync)
          // AND the user is not currently scrolling the transcription manually
          if (!isProgrammaticScrollSync && !isUserScrolling && newPage !== lastSyncedPage) {
            log('[Page Sync] Viewer page changed by user → syncing transcription to page', newPage);
            syncTranscriptionToViewer(newPage);
          }
          
          lastSyncedPage = newPage;
        }
      });
    } catch (e) {
      warn('[Page Sync] Could not bind viewer page handler', e);
    }

    // Handler to scroll transcription to match viewer page
    function syncTranscriptionToViewer(canvasIndex) {
      var tags = transcriptionBox.querySelectorAll('.page-tag');
      var targetTag = null;
      
      // Find the page tag that matches this canvas index
      tags.forEach(function (el) {
        var tagCanvasIndex = parseInt(el.getAttribute('data-canvas-index'), 10);
        if (tagCanvasIndex === canvasIndex) {
          targetTag = el;
        }
      });
      
      if (targetTag) {
        var originalPage = parseInt(targetTag.getAttribute('data-original-page'), 10);
        log('[Page Sync] Found page tag for canvas', canvasIndex, '(transcription page', originalPage + ') - scrolling...');
        
        // Set flag to prevent scroll handler from firing during this sync
        isProgrammaticViewerSync = true;
        
        // Scroll the tag into view with some top offset
        var containerRect = transcriptionBox.getBoundingClientRect();
        var tagRect = targetTag.getBoundingClientRect();
        var scrollOffset = tagRect.top - containerRect.top - 50; // 50px offset from top
        
        transcriptionBox.scrollBy({
          top: scrollOffset,
          behavior: 'smooth'
        });
        
        // Reset flag after animation completes (smooth scroll takes ~500ms)
        setTimeout(function () { 
          isProgrammaticViewerSync = false; 
          log('[Page Sync] ✓ Transcription scrolled to canvas', canvasIndex);
        }, 600);
      } else {
        warn('[Page Sync] No page tag found for canvas index', canvasIndex);
      }
    }

    // Handler to compute the current page from scroll position
    function syncViewerToScroll() {
      // Don't sync if we're in the middle of a viewer-initiated scroll
      if (isProgrammaticViewerSync) {
        log('[Page Sync] Skipping scroll sync (viewer-initiated scroll in progress)');
        return;
      }

      var containerRect = transcriptionBox.getBoundingClientRect();
      // Use a slightly larger threshold (60px) than the scroll target (50px)
      // to ensure the tag we just scrolled to is definitely detected as "visible"
      var thresholdTop = containerRect.top + 60; 

      var visible = null;
      var tags = transcriptionBox.querySelectorAll('.page-tag');
      tags.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.top <= thresholdTop) visible = el;
      });
      if (!visible && tags.length) visible = tags[0];
      if (!visible) return;

      // Use the pre-calculated canvas index from data attribute
      var canvasIndexStr = visible.getAttribute('data-canvas-index');
      var canvasIndex = canvasIndexStr !== null ? parseInt(canvasIndexStr, 10) : 0;
      var originalPage = parseInt(visible.getAttribute('data-original-page'), 10) || 1;
      
      var count = viewer.lumiereSequenceCount || (viewer.tileSources ? viewer.tileSources.length : 0) || 0;
      if (!count) { warn('[Page Sync] Viewer has no items yet – skipping sync'); return; }

      // Clamp canvas index to valid range
      var targetIndex = Math.min(Math.max(canvasIndex, 0), count - 1);
      
      if (lastSyncedPage !== targetIndex) {
        log('[Page Sync] ✓ Switching viewer to canvas index', targetIndex, '(transcription page', originalPage + ')');
        isProgrammaticScrollSync = true;
        lastSyncedPage = targetIndex; // Update before calling viewer to prevent race conditions
        viewer.goToPage(targetIndex);
        
        // Reset flag after page change completes
        setTimeout(function () { 
          isProgrammaticScrollSync = false; 
        }, 500);
      }
    }

    var scrollTimeout;
    transcriptionBox.addEventListener('scroll', function () {
      isUserScrolling = true;
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(function() {
        isUserScrolling = false;
        syncViewerToScroll();
      }, 150);
    });

    // Initial sync after content settles
    setTimeout(syncViewerToScroll, 500);
  }
})();
