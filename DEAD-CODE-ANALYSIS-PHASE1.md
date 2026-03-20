# Dead Code Analysis - Facsimile Viewer Frontend (Phase 1)

**Project**: Lumières Lausanne  
**Date**: February 2, 2026  
**Scope**: JavaScript/CSS facsimile viewer controls  
**Files Analyzed**:
- [app/fiches/static/fiches/js/viewer-controls.js](app/fiches/static/fiches/js/viewer-controls.js)
- [app/fiches/static/fiches/css/viewer-controls.css](app/fiches/static/fiches/css/viewer-controls.css)
- [app/fiches/templates/fiches/display/transcription.html](app/fiches/templates/fiches/display/transcription.html)
- [app/fiches/templates/fiches/includes/viewer_controls.html](app/fiches/templates/fiches/includes/viewer_controls.html)

---

## DEAD CODE FINDINGS

### 1. **Rotate Control**

**Status**: DEAD (Implemented but not exposed)

**Files**:

#### JavaScript
- [app/fiches/static/fiches/js/viewer-controls.js](app/fiches/static/fiches/js/viewer-controls.js#L32)
  - `currentRotation` property: Line 32
  - `rotate()` method: Lines 318-324
  - Event binding: Lines 123-125

#### CSS
- [app/fiches/static/fiches/css/viewer-controls.css](app/fiches/static/fiches/css/viewer-controls.css#L364-L375)
  - `.rotate-icon` styles: Lines 364-375 (including hover/active states)

#### HTML
- **NOT PRESENT** in [app/fiches/templates/fiches/includes/viewer_controls.html](app/fiches/templates/fiches/includes/viewer_controls.html)
  - No button with id `viewer-rotate` exists in the template

**Why It's Dead**:
- The JavaScript bindButton() call on line 123-125 tries to bind events to `viewer-rotate` element
- No HTML button with this ID is rendered in the template
- CSS styling for `.rotate-icon` exists but is never applied to any DOM element

**Implementation Details**:
```javascript
// Line 123-125: Event binding code
this.bindButton('viewer-rotate', function () {
    self.rotate();
});

// Line 318-324: Implementation
rotate: function () {
    if (!this.viewer) return;
    this.currentRotation = (this.currentRotation + 90) % 360;
    this.viewer.viewport.setRotation(this.currentRotation);
},
```

**CSS Implementation**:
```css
/* Lines 364-375 */
.rotate-icon {
    background-image: url('/static/js/lib/openseadragon/images/rotateright_rest.png');
}
.control-btn:hover .rotate-icon {
    background-image: url('/static/js/lib/openseadragon/images/rotateright_hover.png');
}
.control-btn:active .rotate-icon {
    background-image: url('/static/js/lib/openseadragon/images/rotateright_pressed.png');
}
```

**Recommendation**: 
- **REMOVE** (Low priority feature; no UI request from stakeholders)
- OR **EXPOSE** by adding button to template if rotation is desired

**Effort to Remove**: 
- Low (5-10 minutes)
  - Remove lines 32, 123-125, 318-324 from viewer-controls.js
  - Remove lines 364-375 from viewer-controls.css
  - No HTML changes needed (feature already hidden)

---

### 2. **Contrast Control**

**Status**: DEAD (Implemented but not exposed)

**Files**:

#### JavaScript
- [app/fiches/static/fiches/js/viewer-controls.js](app/fiches/static/fiches/js/viewer-controls.js#L33-L35)
  - `filters.contrast` property: Line 35
  - `bindButton('viewer-contrast')` event: Lines 127-129
  - `bindSlider('contrast-slider')` event: Lines 139-142
  - `applyFilters()` method: Lines 334-343

#### CSS
- [app/fiches/static/fiches/css/viewer-controls.css](app/fiches/static/fiches/css/viewer-controls.css#L376-L380)
  - `.contrast-icon::before` styles: Lines 376-380
  - `.dropdown-popup` styles: Lines 415-430
  - Dropdown input range styles: Line 424

#### HTML
- **NOT PRESENT** in [app/fiches/templates/fiches/includes/viewer_controls.html](app/fiches/templates/fiches/includes/viewer_controls.html)
  - No button with id `viewer-contrast` exists
  - No elements with id `contrast-popup` or `contrast-slider` exist

**Why It's Dead**:
- JavaScript code binds to non-existent HTML elements (`viewer-contrast`, `contrast-popup`, `contrast-slider`)
- CSS defines styles for a `.contrast-icon` and dropdown popups that are never rendered
- The filter system is fully implemented but disabled at the UI layer

**Implementation Details**:
```javascript
// Line 127-129: Button binding (element doesn't exist)
this.bindButton('viewer-contrast', function () {
    self.toggleDropdown('contrast-popup');
});

// Line 139-142: Slider binding (element doesn't exist)
this.bindSlider('contrast-slider', function (value) {
    self.filters.contrast = parseInt(value);
    self.applyFilters();
});

// Line 334-343: Filter application (works, but never called via UI)
applyFilters: function () {
    if (!this.viewer) return;
    var canvas = this.viewer.canvas;
    if (canvas) {
        var filterValue = 'brightness(' + this.filters.brightness + '%) contrast(' + this.filters.contrast + '%)';
        canvas.style.filter = filterValue;
        canvas.style.webkitFilter = filterValue;
    }
},
```

**CSS Implementation**:
```css
/* Lines 376-380: Icon styles */
.contrast-icon::before {
    content: "◐";
    font-size: 18px;
    line-height: 1;
    color: #495057;
    font-style: normal;
}

/* Lines 415-430: Dropdown popup (never rendered) */
.dropdown-popup {
    position: absolute;
    top: 100%;
    left: 0;
    width: 120px;
    background: #fff;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 8px;
    margin-top: 2px;
    display: none;
    z-index: 1001;
}
```

**Recommendation**: 
- **REMOVE** (Premature implementation; not in current requirements)
- OR **EXPOSE** by adding controls to template if image adjustment is desired

**Effort to Remove**: 
- Low (5-10 minutes)
  - Remove lines 35, 127-129, 139-142 from viewer-controls.js
  - Remove `filters.contrast` from reset() method (line 329)
  - Remove lines 334-343 applyFilters() from viewer-controls.js entirely
  - Remove lines 376-380, 415-430 from viewer-controls.css
  - No HTML changes needed

---

### 3. **Brightness Control**

**Status**: DEAD (Implemented but not exposed)

**Files**:

#### JavaScript
- [app/fiches/static/fiches/js/viewer-controls.js](app/fiches/static/fiches/js/viewer-controls.js#L34)
  - `filters.brightness` property: Line 34
  - `bindButton('viewer-brightness')` event: Lines 131-133
  - `bindSlider('brightness-slider')` event: Lines 145-148
  - Applied in `applyFilters()`: Lines 334-343

#### CSS
- [app/fiches/static/fiches/css/viewer-controls.css](app/fiches/static/fiches/css/viewer-controls.css#L381-L385)
  - `.brightness-icon::before` styles: Lines 381-385
  - Same dropdown popup styles as contrast (shared)

#### HTML
- **NOT PRESENT** in [app/fiches/templates/fiches/includes/viewer_controls.html](app/fiches/templates/fiches/includes/viewer_controls.html)
  - No button with id `viewer-brightness`
  - No elements with id `brightness-popup` or `brightness-slider`

**Why It's Dead**:
- Mirror of contrast control: identical dead code pattern
- JavaScript binds to non-existent HTML elements
- CSS defines styles never applied to DOM
- Full implementation exists but UI layer disabled

**Implementation Details**:
```javascript
// Line 131-133: Button binding (element doesn't exist)
this.bindButton('viewer-brightness', function () {
    self.toggleDropdown('brightness-popup');
});

// Line 145-148: Slider binding (element doesn't exist)
this.bindSlider('brightness-slider', function (value) {
    self.filters.brightness = parseInt(value);
    self.applyFilters();
});
```

**CSS Implementation**:
```css
/* Lines 381-385: Icon styles */
.brightness-icon::before {
    content: "☀";
    font-size: 18px;
    line-height: 1;
    color: #495057;
    font-style: normal;
}
```

**Recommendation**: 
- **REMOVE** (Same as contrast; depends on whether adjustment controls are desired)
- Related CSS is shared with contrast control

**Effort to Remove**: 
- Low (5 minutes)
  - Remove lines 34, 131-133, 145-148 from viewer-controls.js
  - Remove `filters.brightness` from reset() method (line 328)
  - Remove line 381-385 from viewer-controls.css
  - Note: `applyFilters()` method can only be removed if both brightness AND contrast are removed

---

### 4. **Reset Control - Partial Dead Code**

**Status**: PARTIALLY DEAD (Exposed in UI but resets dead features)

**Files**:

#### JavaScript
- [app/fiches/static/fiches/js/viewer-controls.js](app/fiches/static/fiches/js/viewer-controls.js#L118-121)
  - Event binding: Lines 118-121
  - Implementation: Lines 301-320

#### CSS
- [app/fiches/static/fiches/css/viewer-controls.css](app/fiches/static/fiches/css/viewer-controls.css#L351-L362)
  - `.reset-icon` styles: Lines 351-362

#### HTML
- **PRESENT** in [app/fiches/templates/fiches/includes/viewer_controls.html](app/fiches/templates/fiches/includes/viewer_controls.html#L37-L40)
  - Button exists: Line 37-40

**Why It's Partially Dead**:
- Reset button **IS** exposed and functional
- But it resets properties that have no UI (lines 328-330):
  - `this.filters.brightness = 100;`
  - `this.filters.contrast = 100;`
- These lines are dead code within an otherwise live function

**Implementation Details**:
```javascript
// Lines 301-320: Reset implementation
reset: function () {
    if (!this.viewer) return;
    this.currentRotation = 0; // DEAD: rotation feature not exposed
    this.viewer.viewport.setRotation(0);
    this.viewer.viewport.goHome(true); // LIVE
    this.filters.brightness = 100; // DEAD: brightness not exposed
    this.filters.contrast = 100;     // DEAD: contrast not exposed
    this.applyFilters(); // DEAD: applies non-existent filters
    // ... slider reset code for non-existent sliders
},
```

**Lines 328-330 are Unnecessary**:
```javascript
// These are DEAD and can be removed
this.filters.brightness = 100;
this.filters.contrast = 100;
this.applyFilters(); // Line 331
```

**Lines 333-337 are Unnecessary**:
```javascript
// These reset non-existent sliders (DEAD)
var contrastSlider = document.getElementById('contrast-slider');
var brightnessSlider = document.getElementById('brightness-slider');
if (contrastSlider) { contrastSlider.value = 100; }
if (brightnessSlider) { brightnessSlider.value = 100; }
```

**Recommendation**: 
- **REFACTOR**: Keep reset() function, but remove dead code lines
- Remove lines 325, 328-337 from reset() method

**Effort to Remove**: 
- Low (2-3 minutes)
  - Clean up reset() method to only reset live features
  - Remove filter resets if filters are removed entirely

---

### 5. **Toggle Dropdown Methods**

**Status**: DEAD (Implementation without usage)

**Files**:

#### JavaScript
- [app/fiches/static/fiches/js/viewer-controls.js](app/fiches/static/fiches/js/viewer-controls.js#L248-L268)
  - `setupDropdowns()` method: Lines 248-257
  - `toggleDropdown()` method: Lines 260-271
  - `closeAllDropdowns()` method: Lines 274-279
  - Event listener setup: Lines 248-257

#### CSS
- [app/fiches/static/fiches/css/viewer-controls.css](app/fiches/static/fiches/css/viewer-controls.css#L415-L430)
  - `.dropdown-popup` base styles
  - `.dropdown-popup.show` state

**Why It's Dead**:
- These methods exist to support contrast/brightness dropdowns
- No HTML exists to render dropdowns
- The click event listener (lines 248-257) watches for `.dropdown-popup` elements that don't exist
- Related methods are only called from dead button handlers

**Implementation Details**:
```javascript
// Lines 248-257: Sets up document-level click listener for non-existent elements
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

// Lines 260-271: Toggles dropdowns that don't exist
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

// Lines 274-279: Closes all non-existent dropdowns
closeAllDropdowns: function () {
    var dropdowns = document.querySelectorAll('.dropdown-popup');
    dropdowns.forEach(function (dropdown) {
        dropdown.classList.remove('show');
    });
},
```

**Recommendation**: 
- **REMOVE** - These methods only serve the dead contrast/brightness features
- Can be safely deleted with no impact

**Effort to Remove**: 
- Low (3-5 minutes)
  - Remove methods: setupDropdowns(), toggleDropdown(), closeAllDropdowns()
  - Remove call to setupDropdowns() from init() method (line 50)
  - Remove call to closeAllDropdowns() from reset() method (line 338)
  - Remove CSS: lines 415-430

---

### 6. **Update Slider Value Method**

**Status**: DEAD (Orphaned utility method)

**Files**:

#### JavaScript
- [app/fiches/static/fiches/js/viewer-controls.js](app/fiches/static/fiches/js/viewer-controls.js#L282-L291)
  - `updateSliderValue()` method: Lines 282-291

**Why It's Dead**:
- This method is defined but never called anywhere
- It's intended to update slider display text for non-existent contrast/brightness sliders
- No references to this method exist in the codebase

**Implementation Details**:
```javascript
// Lines 282-291: Unused utility method
updateSliderValue: function (sliderId, text) {
    var slider = document.getElementById(sliderId);
    if (slider) {
        var valueSpan = slider.parentNode.querySelector('.slider-value');
        if (valueSpan) {
            valueSpan.textContent = text;
        }
    }
},
```

**Recommendation**: 
- **REMOVE** - Completely unused orphaned method

**Effort to Remove**: 
- Minimal (1 minute)
  - Delete lines 282-291

---

### 7. **Unused CSS Patterns**

**Status**: DEAD (CSS without markup)

**Files**:

#### CSS
- [app/fiches/static/fiches/css/viewer-controls.css](app/fiches/static/fiches/css/viewer-controls.css#L28-L90)

**Selectors with no corresponding HTML**:
- `.unified-text-btn` - Lines 29-47 (no elements use this class)
- `.ui-button` state overrides - Lines 28-70 (jQuery UI fallback, not in use)

**Why It's Dead**:
- These classes were created as fallback styles for jQuery UI buttons
- Current template uses `.control-btn` class exclusively
- jQuery UI buttons exist in the HTML but these specific overrides aren't needed

**CSS Details**:
```css
/* Lines 29-47: Never applied */
.unified-text-btn,
.ui-button,
.ui-button.ui-widget,
.ui-button.ui-state-default { /* styling */ }

/* Lines 48-52: Hover state for non-existent class */
.unified-text-btn:hover,
.ui-button:hover,
.ui-button.ui-state-default:hover { /* styling */ }
```

**Recommendation**: 
- **REVIEW**: jQuery UI buttons exist in transcription.html but these specific overrides may not be needed
- Check if `#transcription-view-controls` buttons need these styles or if they're handled elsewhere
- Lines 28-70 can likely be removed if no transcription view controls exist

**Effort to Review/Remove**: 
- Medium (15-20 minutes)
  - Check if jQuery UI buttons are actually used in transcription view
  - If they are, verify if current styles in lines 450-520 are sufficient
  - Can then safely remove lines 28-70 if redundant

---

## SUMMARY TABLE

| Feature | File | Lines | Type | Status | Effort |
|---------|------|-------|------|--------|--------|
| Rotate Control | JS | 32, 123-125, 318-324 | Dead | REMOVE | Low |
| Rotate Control | CSS | 364-375 | Dead | REMOVE | Low |
| Contrast Control | JS | 35, 127-129, 139-142, 334-343 | Dead | REMOVE | Low |
| Contrast Control | CSS | 376-380, 415-430 | Dead | REMOVE | Low |
| Brightness Control | JS | 34, 131-133, 145-148 | Dead | REMOVE | Low |
| Brightness Control | CSS | 381-385 | Dead | REMOVE | Low |
| Reset Control | JS | 325, 328-337 | Partial | REFACTOR | Low |
| Dropdown Methods | JS | 248-257, 260-279 | Dead | REMOVE | Low |
| Slider Value Method | JS | 282-291 | Dead | REMOVE | Low |
| UI Button Fallbacks | CSS | 28-70 | Questionable | REVIEW | Medium |

---

## REMOVAL STRATEGY

### Phase 1: Immediate Removal (Low Risk)
These can be safely removed without testing:
1. Rotate control (JS + CSS)
2. Contrast control (JS + CSS)
3. Brightness control (JS + CSS)
4. Dropdown methods (JS + CSS)
5. updateSliderValue() method

**Total Time**: 15-20 minutes  
**Risk Level**: Very Low (features not exposed in UI)

### Phase 2: Refactoring (Low Risk)
1. Remove dead code from reset() method
2. Remove unnecessary filter resets

**Total Time**: 5 minutes  
**Risk Level**: Very Low (only removing unused assignments)

### Phase 3: Review (Medium Risk)
1. Check if jQuery UI button styles are redundant
2. Verify transcription view controls styling

**Total Time**: 15-20 minutes  
**Risk Level**: Low (CSS only, visual regression possible)

---

## RECOMMENDATIONS

1. **Prioritize Removal**: Start with Phases 1-2 (20-25 minutes total)
   - Significant code cleanup
   - Zero functional impact
   - Reduces maintenance burden

2. **Document Decision**: Before removing, confirm with stakeholders:
   - Rotation feature not needed?
   - Image adjustment (brightness/contrast) not planned?

3. **Testing After Removal**:
   - Verify page navigation works (prev/next)
   - Verify zoom in/out works
   - Verify reset button works (rotation reset removed, but zoom reset remains)
   - Verify no console errors

4. **Future Phases**:
   - Phase 2 could expose these features if requested by users
   - Keep feature implementation but add HTML buttons/sliders to template
