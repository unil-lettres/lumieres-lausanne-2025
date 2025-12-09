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
      setupViewer(cfg.iiifUrl);
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
    });
  }

  function updateSyncButtonState(btn, isEnabled) {
    if (isEnabled) {
      btn.classList.add('active');
      btn.title = 'Désactiver la synchronisation texte-facsimilé';
      btn.innerHTML = '🔗 Synchro';
    } else {
      btn.classList.remove('active');
      btn.title = 'Activer la synchronisation texte-facsimilé';
      btn.innerHTML = '🔌 Synchro';
    }
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

  function initPageSync(viewer) {
    var transcriptionBox = document.getElementById('transcription-data');
    if (!transcriptionBox || !viewer) return;

    log('[Page Sync] Initializing page synchronization...');

    var lastSyncedPage = (typeof viewer.currentPage === 'function') ? viewer.currentPage() : null;
    var isProgrammaticScrollSync = false;
    var isProgrammaticViewerSync = false;
    var scrollTimeout = null;
    var isUserScrolling = false;

    var seqCount = viewer.lumiereSequenceCount || viewer.tileSources?.length || 0;
    var pageOffset = 1;
    
    log('[Page Sync] Found sequence with', seqCount, 'page(s).');

    // Extract and wrap page tags
    wrapPageTags(transcriptionBox, seqCount);

    // Sync viewer page to transcription
    try {
      viewer.addHandler('page', function (ev) {
        if (typeof ev.page !== 'number') return;
        
        if (window.TranscriptionSyncEnabled && !isProgrammaticScrollSync && !isUserScrolling && ev.page !== lastSyncedPage) {
          log('[Page Sync] Viewer page changed by user → syncing transcription to page', ev.page);
          syncTranscriptionToViewer(ev.page, transcriptionBox);
        }
        
        lastSyncedPage = ev.page;
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

      var originalPage = parseInt(targetTag.getAttribute('data-original-page'), 10);
      log('[Page Sync] Found page tag for canvas', canvasIndex, '(transcription page', originalPage + ') - scrolling...');
      
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

      var visible = findVisiblePageTag(transcriptionBox, thresholdTop);
      if (!visible) return;

      var canvasIndexStr = visible.getAttribute('data-canvas-index');
      var canvasIndex = canvasIndexStr !== null ? parseInt(canvasIndexStr, 10) : 0;
      var originalPage = parseInt(visible.getAttribute('data-original-page'), 10) || 1;
      
      if (!seqCount) { 
        warn('[Page Sync] Viewer has no items yet – skipping sync'); 
        return; 
      }

      var targetIndex = Math.min(Math.max(canvasIndex, 0), seqCount - 1);
      
      if (lastSyncedPage !== targetIndex) {
        log('[Page Sync] ✓ Switching viewer to canvas index', targetIndex, '(transcription page', originalPage + ')');
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

    setTimeout(syncViewerToScroll, PAGE_SYNC_INIT_DELAY);
  }

  function wrapPageTags(transcriptionBox, seqCount) {
    var transcriptionHTML = transcriptionBox.innerHTML;
    var pageTagsRaw = [];
    var m;

    // Extract page tags (new format: <<page_number>>)
    var reNewFormat = /(?:&lt;&lt;|<<)(\d+)(?:&gt;&gt;|>>)/g;
    while ((m = reNewFormat.exec(transcriptionHTML)) !== null) {
      pageTagsRaw.push({ 
        pageNumber: parseInt(m[1], 10), 
        pattern: m[0], 
        type: 'new-format' 
      });
    }

    pageTagsRaw.sort(function (a, b) { 
      return transcriptionHTML.indexOf(a.pattern) - transcriptionHTML.indexOf(b.pattern); 
    });

    log('[Page Sync] Found', pageTagsRaw.length, 'page tags; sequence has', seqCount, 'page(s).');

    // Insert sentinel for first page if needed
    var firstPageNumber = 1;
    if (!pageTagsRaw.some(function (t) { return t.pageNumber === firstPageNumber; })) {
      var sentinel = '<span class="page-tag" data-page="1" data-original-page="1" id="page-tag-start" data-type="sentinel" style="display:inline-block;height:0;line-height:0;overflow:hidden;"></span>';
      transcriptionHTML = sentinel + transcriptionHTML;
      log('[Page Sync] Inserted sentinel page tag for page 1 at the start');
    }

    // Wrap all page markers
    pageTagsRaw.forEach(function (tag, idx) {
      var pageNumber = tag.pageNumber;
      var canvasIndex = pageNumber - 1;
      
      if (seqCount > 0) {
        if (canvasIndex < 0) {
          canvasIndex = 0;
          warn('[Page Sync] Page', pageNumber, 'maps to canvas index < 0, clamped to 0');
        } else if (canvasIndex >= seqCount) {
          canvasIndex = seqCount - 1;
          warn('[Page Sync] Page', pageNumber, 'maps to canvas index', canvasIndex, '>=', seqCount, ', clamped to', (seqCount - 1));
        }
      }
      
      var wrapped = '<span class="page-tag" data-page="' + pageNumber + '" data-original-page="' + pageNumber + '" data-canvas-index="' + canvasIndex + '" id="page-tag-' + idx + '" data-type="' + tag.type + '">' + tag.pattern + '</span>';
      transcriptionHTML = transcriptionHTML.replace(tag.pattern, wrapped);
      
      log('[Page Sync] Page', pageNumber, '→ canvas index', canvasIndex);
    });

    transcriptionBox.innerHTML = transcriptionHTML;
    log('[Page Sync] All page tags wrapped and ready for tracking');
  }

  function findPageTagByCanvasIndex(transcriptionBox, canvasIndex) {
    var tags = transcriptionBox.querySelectorAll('.page-tag');
    var targetTag = null;
    
    for (var i = 0; i < tags.length; i++) {
      var tagCanvasIndex = parseInt(tags[i].getAttribute('data-canvas-index'), 10);
      if (tagCanvasIndex === canvasIndex) {
        targetTag = tags[i];
        break;
      }
    }
    
    return targetTag;
  }

  function findVisiblePageTag(transcriptionBox, thresholdTop) {
    var tags = transcriptionBox.querySelectorAll('.page-tag');
    var visible = null;
    
    for (var i = 0; i < tags.length; i++) {
      var r = tags[i].getBoundingClientRect();
      if (r.top <= thresholdTop) visible = tags[i];
    }
    
    return visible || (tags.length ? tags[0] : null);
  }
})();
