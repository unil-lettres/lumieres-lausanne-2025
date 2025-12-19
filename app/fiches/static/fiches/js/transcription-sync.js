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
    setupLayoutToggles(cfg);
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
        // Skip sync toggle button
        if (btn.id === 'sync-toggle-btn') return;
        
        var newLayout = btn.getAttribute('data-layout');
        
        log('[Layout Toggle] Button clicked:', e.target);
        log('[Layout Toggle] New layout:', newLayout);
        
        updateActiveButton(buttons, newLayout);
        document.body.setAttribute('data-layout-mode', newLayout);
        
        try { sessionStorage.setItem(STORAGE_KEY_LAYOUT, newLayout); } catch (_) {}

        // Disable sync when switching away from split-view
        if (newLayout !== DEFAULT_LAYOUT) {
          disableSyncIfActive();
        }

        resetViewerZoom();
      });
    });

    setupSyncToggleButton();
  }

  function updateActiveButton(buttons, layoutName) {
    buttons.forEach(function (b) { b.classList.remove('active'); });
    var activeBtn = document.querySelector('.layout-btn[data-layout="' + layoutName + '"]');
    if (activeBtn) activeBtn.classList.add('active');
  }

  function disableSyncIfActive() {
    if (window.TranscriptionSyncEnabled) {
      window.TranscriptionSyncEnabled = false;
      var syncToggleBtn = document.getElementById('sync-toggle-btn');
      if (syncToggleBtn) {
        updateSyncButtonState(syncToggleBtn, false);
        try { sessionStorage.setItem(STORAGE_KEY_SYNC, false); } catch (_) {}
        log('[Layout Toggle] Sync automatically disabled - not in split-view mode');
      }
    }
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

  function setupSyncToggleButton() {
    var syncToggleBtn = document.getElementById('sync-toggle-btn');
    if (!syncToggleBtn) return;

    var savedSyncState = true;
    try { 
      var syncStateStr = sessionStorage.getItem(STORAGE_KEY_SYNC);
      savedSyncState = syncStateStr !== 'false';
    } catch (_) { 
      // Default to enabled
    }
    
    window.TranscriptionSyncEnabled = savedSyncState;
    updateSyncButtonState(syncToggleBtn, savedSyncState);
    
    syncToggleBtn.addEventListener('click', function (e) {
      e.preventDefault();
      
      var currentLayout = document.body.getAttribute('data-layout-mode');
      if (currentLayout !== DEFAULT_LAYOUT) {
        log('[Sync Toggle] Cannot toggle sync - not in split-view mode');
        return;
      }
      
      var newState = !window.TranscriptionSyncEnabled;
      window.TranscriptionSyncEnabled = newState;
      updateSyncButtonState(syncToggleBtn, newState);
      try { sessionStorage.setItem(STORAGE_KEY_SYNC, newState); } catch (_) {}
      log('[Sync Toggle] Synchronization', newState ? 'enabled' : 'disabled');

      // If sync is being turned on, immediately align viewer to the current text position
      if (newState && typeof window.lumiereSyncViewerToScroll === 'function') {
        window.lumiereSyncViewerToScroll();
      }
    });
  }

  function updateSyncButtonState(btn, isEnabled) {
    if (isEnabled) {
      btn.classList.add('active');
      btn.title = 'Désactiver la synchronisation texte-facsimilé';
      btn.innerHTML = '🔗 Synchroniser la navigation';
    } else {
      btn.classList.remove('active');
      btn.title = 'Activer la synchronisation texte-facsimilé';
      btn.innerHTML = '🔌 Synchroniser la navigation';
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
      if (key !== lastMarkerIndicatorKey) {
        showMarkerToast((!isBeforeFirstMarker && folio) ? ('Repère <' + folio + '>') : 'Repère —');
        lastMarkerIndicatorKey = key;
      }
    }

    function showMarkerToast(text) {
      var container = document.getElementById('openseadragon-viewer');
      if (!container) return;

      var toast = document.getElementById('viewer-marker-toast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'viewer-marker-toast';
        toast.className = 'marker-toast';
        toast.setAttribute('aria-live', 'polite');
        toast.setAttribute('role', 'status');
        container.appendChild(toast);
      }

      toast.textContent = text || '';
      toast.classList.remove('show');
      // force reflow to restart animation
      void toast.offsetWidth; // eslint-disable-line no-unused-expressions
      toast.classList.add('show');
    }

    // Sync viewer page to transcription
    try {
      viewer.addHandler('page', function (ev) {
        if (typeof ev.page !== 'number') return;

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
    // Require real angle brackets and digits (optionally r/v) with word-boundaries around
    var reFolio = /(^|[^0-9A-Za-z])(?:&lt;|<)\s*(\d{1,3})\s*([rv])?\s*(?:&gt;|>)(?![0-9A-Za-z])/gi;

    var markerIndex = 1; // 1 is already reserved for the virtual first marker
    transcriptionHTML = transcriptionHTML.replace(reFolio, function (full, prefix, num, rv) {
      var folio = String(num || '') + String(rv || '');
      var canvasIndex = startCanvasIndex0 + markerIndex;

      if (seqCount > 0) {
        if (canvasIndex < 0) canvasIndex = 0;
        if (canvasIndex >= seqCount) canvasIndex = seqCount - 1;
      }

      var wrapped =
        prefix +
        '<span class="page-tag"' +
        ' data-folio="' + folio + '"' +
        ' data-marker-index="' + (markerIndex + 1) + '"' +
        ' data-canvas-index="' + canvasIndex + '"' +
        ' id="page-tag-' + markerIndex + '">' +
        full +
        '</span>';

      markerIndex += 1;
      return wrapped;
    });

    transcriptionBox.innerHTML = transcriptionHTML;
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

    if (!inView.length) return tags[0] || null;

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
