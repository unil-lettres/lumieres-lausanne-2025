<!--
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
-->

# Phase 1: Frontend Dead Code Analysis

**Status**: Complete ✅
**Date**: 2026-02-02
**Purpose**: Identify and document unused/dead code in facsimile viewer frontend before refactoring

---

## Summary

Analysis of frontend code for the facsimile viewer reveals **dead code features** (implemented but not exposed in UI) and **legacy dependencies** that should be cleaned up or retained based on PM decision.

### Key Findings

| Category | Item | Status | Recommendation |
|----------|------|--------|---|
| **Dead Features** | Rotate control (rotate by 90°) | Implemented in JS + CSS, no UI button | REMOVE or ADD UI |
| **Dead Features** | Brightness control | Implemented in JS + CSS, dropdown popup defined but unused | REMOVE or ADD UI |
| **Dead Features** | Contrast control | Implemented in JS + CSS, dropdown popup defined but unused | REMOVE or ADD UI |
| **Legacy Deps** | jQuery 1.8.2 (CDN) | Used only for jQuery UI widgets | KEEP (still needed by admin) |
| **Legacy Deps** | jQuery UI 1.9 button widget | Used for toolbar buttons styling | KEEP (will be replaced in Phase 2) |
| **Code Quality** | Global window variables | `TranscriptionConfig`, `ViewerControls`, `enableSync`, `syncTranscription` | REFACTOR in Phase 2 |
| **Code Quality** | Fullscreen icon CSS | Icon defined but no fullscreen implementation | REMOVE |

---

## 1. Dead/Unused Code Spots

### A. Rotate Control
**Files**: 
- `app/fiches/static/fiches/js/viewer-controls.js` (lines 118-120, 355-369)
- `app/fiches/static/fiches/css/viewer-controls.css` (lines 251-259)

**Current State**:
- Function `rotate()` in JS fully implemented (rotates image by 90° increments)
- CSS icons defined with 3 states (rest, hover, active)
- **NOT EXPOSED** in template or UI

**Code Snippet**:
```javascript
// viewer-controls.js, line 118-120
this.bindButton('viewer-rotate', function () {
    self.rotate();
});

// Line 357
rotate: function () {
    if (!this.viewer) return;
    this.currentRotation = (this.currentRotation + 90) % 360;
    this.viewer.setRotation(this.currentRotation);
    console.log('Image rotated to:', this.currentRotation, 'degrees');
},
```

**Decision Needed**: 
- [ ] Remove rotate feature entirely
- [ ] Add rotate button to toolbar in Phase 2

---

### B. Brightness Control
**Files**:
- `app/fiches/static/fiches/js/viewer-controls.js` (lines 131-142, 374-392)
- `app/fiches/static/fiches/css/viewer-controls.css` (lines 290-296, 304-322)

**Current State**:
- Button binding exists (line 131-132)
- Slider logic exists (lines 141-142)
- Dropdown popup CSS defined (`.dropdown-popup`, `.brightness-popup`)
- **NOT EXPOSED** in template or toolbar

**Code Snippet**:
```javascript
// viewer-controls.js, line 131-142
this.bindButton('viewer-brightness', function () {
    self.toggleDropdown('brightness-popup');
});

this.bindSlider('brightness-slider', function (value) {
    self.filters.brightness = parseInt(value);
    self.applyFilters();
});
```

**Decision Needed**:
- [ ] Remove brightness feature entirely
- [ ] Add brightness button + slider popup in Phase 2

---

### C. Contrast Control
**Files**:
- `app/fiches/static/fiches/js/viewer-controls.js` (lines 127-130, 136-140)
- `app/fiches/static/fiches/css/viewer-controls.css` (lines 282-296, 304-322)

**Current State**:
- Button binding exists
- Slider logic exists
- Dropdown popup CSS defined
- **NOT EXPOSED** in template

**Decision Needed**:
- [ ] Remove contrast feature entirely
- [ ] Add contrast button + slider popup in Phase 2

---

### D. Fullscreen Icon
**Files**:
- `app/fiches/static/fiches/css/viewer-controls.css` (lines 261-269)

**Current State**:
```css
.fullscreen-icon {
    background-image: url('/static/js/lib/openseadragon/images/fullscreen_rest.png');
}

.control-btn:hover .fullscreen-icon {
    background-image: url('/static/js/lib/openseadragon/images/fullscreen_hover.png');
}

.control-btn:active .fullscreen-icon {
    background-image: url('/static/js/lib/openseadragon/images/fullscreen_pressed.png');
}
```

- CSS defined but **no JavaScript implementation exists**
- Not exposed in UI
- Not mentioned in client requirements

**Decision Needed**:
- [ ] Remove fullscreen CSS entirely (not needed)

---

## 2. Legacy Dependencies Analysis

### jQuery 1.8.2 + jQuery UI 1.9

**Current Usage**:
- jQuery UI "button" widget for toolbar buttons styling
- jQuery for DOM manipulation in transcription.html (scrollCiteAs function)

**Files**:
- `app/fiches/templates/fiches/display/transcription.html` (lines 45-48)
- `app/static/js/lib/jquery/`
- `app/static/js/lib/jquery-ui-1.9/`

**Status**: 
- Still actively used for admin forms and UI widgets
- Toolbar buttons styled with jQuery UI
- Will be replaced with native HTML/CSS buttons in Phase 2

**Recommendation**: 
- KEEP jQuery/jQuery UI (used elsewhere in app, not just facsimile viewer)
- Remove jQuery dependency from facsimile code in Phase 2 by using vanilla JS

---

## 3. Global Window Variables

**Files**: `app/fiches/static/fiches/js/transcription-sync.js`

**Current Globals**:
```javascript
window.TranscriptionConfig = { ... }  // Configuration object
window.enableSync = true              // Sync state flag
window.syncTranscription = function   // Sync trigger function
window.ViewerControls = function      // Constructor exported
```

**Status**: Created for HTML/JS bridge, works but not ideal

**Recommendation**:
- Refactor in Phase 3 to use data attributes or proper module pattern
- Keep `TranscriptionConfig` as bridge until Phase 3

---

## 4. Unused CSS Classes

**Files**: `app/fiches/static/fiches/css/viewer-controls.css`

**Defined but unused**:
- `.dropdown-popup` - defined but markup never generated
- `.contrast-icon::before` - icon defined but not exposed
- `.brightness-icon::before` - icon defined but not exposed

---

## 5. Code Quality Issues

### A. Memory Leak Prevention
**Status**: ✅ GOOD
- `boundEvents` tracking in ViewerControls (line 38)
- Proper cleanup pattern for event handlers

### B. Event Handler Complexity
**Status**: ⚠️ FIXABLE
- Close popup on outside click (lines 238-247 in viewer-controls.js)
- Could be simplified with event delegation

### C. Regex Fragility
**Files**: `app/fiches/static/fiches/js/transcription-sync.js`
**Pattern**: `/<(\d+[rv]?)>/g` for page markers like `<1>`, `<4v>`, `<10r>`
**Status**: ⚠️ WORKS but fragile for edge cases (e.g., `<01>` vs `<1>`)

---

## Cleanup Plan

### Option A: Minimal (Recommended)
**Phase 1 Decision**: Keep rotate/brightness/contrast code but don't expose in UI
- Reason: May be requested in future, clean removal time investment not justified
- Action: Document as "disabled features" in code comments

### Option B: Aggressive (PM Decision)
**Phase 1 Decision**: Remove all unused code
- Requires: Delete JS functions, CSS classes, CSS icon definitions
- Files affected: viewer-controls.js (~50 lines), viewer-controls.css (~150 lines)
- Time: ~0.5h cleanup

### Option C: Selective
**Phase 1 Decision**: 
- Remove fullscreen CSS (not used, no future plan)
- Keep rotate/brightness/contrast code (may be useful)
- Remove unused `.dropdown-popup` CSS variants

---

## Files Involved

```
app/fiches/static/fiches/
├── css/
│   ├── viewer-controls.css ← 434 lines, contains dead CSS
│   └── transcription-layout.css ← CLEAN
├── js/
│   ├── viewer-controls.js ← 459 lines, contains dead features
│   └── transcription-sync.js ← CLEAN, but uses globals
└── templates/ (no dead code)

app/static/js/lib/
├── jquery/ ← Legacy but still needed
├── jquery-ui-1.9/ ← Legacy but still needed
└── openseadragon/ ← CLEAN
```

---

## Recommendation for Next Steps

✅ **Proceed to Phase 2** with **Option C (Selective Cleanup)**:

1. ✂️ **Remove** fullscreen CSS (not implemented, not needed)
2. 📝 **Document** rotate/brightness/contrast as "disabled features" with TODO comments
3. 🔄 **Replace** jQuery UI button widget with native HTML buttons in Phase 2
4. 🌍 **Refactor** global window variables in Phase 3

**Estimated Impact**:
- 0 hours (document in-code during Phase 2 implementation)
- No breaking changes
- Clean codebase for new features

---

## Review Checklist

- [x] Identified all dead code spots
- [x] Documented legacy dependencies
- [x] Listed global variables
- [x] Assessed memory leaks (none found)
- [x] Created cleanup recommendation
- [ ] **PM Decision**: Which cleanup option? (A/B/C)
- [ ] **PM Decision**: Rotate/brightness/contrast: keep code or remove?

---

**Next Phase**: Phase 2 - Refactor Navigation Bar Layout  
**Blocked Until**: PM review & decision on cleanup option
