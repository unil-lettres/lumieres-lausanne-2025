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

# Phase 3: Implement Mode Conditional Logic

**Estimated Time**: 3 hours  
**Status**: Design Phase (Ready for Implementation after Phase 2)  
**Objective**: Enable/disable mode buttons and options menu based on available content (facsimilé presence/absence)

---

## Scope

Control which mode buttons are clickable and what options appear in the menu based on:
- Presence of facsimilé (IIIF URL)
- Presence of transcription text
- Current selected mode

---

## Business Rules

### Rule 1: Only Facsimilé (no transcription)
```
Mode Buttons: [Texte (disabled)] [Texte+Facsimilé (disabled)] [Facsimilé (active)] [Options (disabled)]
Options Menu: HIDDEN (disabled)
Default: Facsimilé mode
Behavior: User cannot switch modes
```

### Rule 2: Only Transcription (no facsimilé)
```
Mode Buttons: [Texte (active)] [Texte+Facsimilé (disabled)] [Facsimilé (disabled)] [Options (enabled)]
Options Menu: Mode-specific options for Text
Default: Texte mode
Behavior: User cannot switch modes
```

### Rule 3: Both Transcription + Facsimilé (normal case)
```
Mode Buttons: [Texte] [Texte+Facsimilé (active)] [Facsimilé] [Options (enabled)]
Options Menu: Mode-specific options (changes per mode)
Default: Texte+Facsimilé
Behavior: User can switch between all modes
```

---

## Implementation

### 1. Data Availability Detection

**File**: `app/fiches/templates/fiches/display/transcription.html`

**Add data attributes** to container:
```html
<div id="layout-toggle-buttons" 
     class="layout-toggle-group"
     data-has-facsimile="{{ trans.facsimile_iiif_url|yesno:'true,false' }}"
     data-has-transcription="true">
    <!-- buttons -->
</div>
```

**Logic**:
- `data-has-facsimile`: Passed from model (existing)
- `data-has-transcription`: Always true (if we're on this page, transcription exists)

**Notes**:
- Model already provides `trans.facsimile_iiif_url`
- Could also check `trans.text` field if needed

### 2. CSS Conditional States

**File**: `app/fiches/static/fiches/css/transcription-layout.css`

**Add rules** for disabled buttons:
```css
/* When no facsimilé: disable facsimilé-related buttons */
#layout-toggle-buttons[data-has-facsimile="false"] .split-view-btn,
#layout-toggle-buttons[data-has-facsimile="false"] .viewer-only-btn,
#layout-toggle-buttons[data-has-facsimile="false"] #options-menu-btn {
    opacity: 0.5;
    cursor: not-allowed;
    background-color: #f0f0f0;
    color: #999;
}

/* When no facsimilé: disable viewer-only mode */
body[data-has-facsimile="false"] .layout-btn.viewer-only-btn,
body[data-has-facsimile="false"] .layout-btn.split-view-btn {
    pointer-events: none;
}

/* When no transcription: disable text-only and split-view */
#layout-toggle-buttons[data-has-transcription="false"] .text-only-btn,
#layout-toggle-buttons[data-has-transcription="false"] .split-view-btn {
    opacity: 0.5;
    cursor: not-allowed;
    background-color: #f0f0f0;
    color: #999;
    pointer-events: none;
}

/* Disabled state styling */
.layout-btn:disabled,
.layout-btn[disabled] {
    opacity: 0.5;
    cursor: not-allowed;
    background-color: #f0f0f0;
    color: #999;
}

.layout-btn:disabled:hover {
    background-color: #f0f0f0;
}
```

### 3. JavaScript Conditional Logic

**File**: `app/fiches/static/fiches/js/transcription-sync.js`

**Add initialization** in main script:
```javascript
/**
 * Initialize mode availability based on content
 */
function initializeModeAvailability() {
    const container = document.getElementById('layout-toggle-buttons');
    if (!container) return;
    
    const hasFacsimile = container.dataset.hasFacsimile === 'true';
    const hasTranscription = container.dataset.hasTranscription === 'true';
    
    const textBtn = container.querySelector('.text-only-btn');
    const splitBtn = container.querySelector('.split-view-btn');
    const viewerBtn = container.querySelector('.viewer-only-btn');
    const optionsBtn = document.getElementById('options-menu-btn');
    
    // Case 1: Only facsimilé
    if (!hasTranscription && hasFacsimile) {
        textBtn.disabled = true;
        splitBtn.disabled = true;
        viewerBtn.disabled = false;
        optionsBtn.disabled = true;
        setLayout('viewer-only'); // Force viewer mode
    }
    
    // Case 2: Only transcription
    else if (hasTranscription && !hasFacsimile) {
        textBtn.disabled = false;
        splitBtn.disabled = true;
        viewerBtn.disabled = true;
        optionsBtn.disabled = false;
        setLayout('text-only'); // Force text mode
    }
    
    // Case 3: Both (normal case)
    else if (hasTranscription && hasFacsimile) {
        textBtn.disabled = false;
        splitBtn.disabled = false;
        viewerBtn.disabled = false;
        optionsBtn.disabled = false;
        // Default already set in CSS (split-view active)
    }
    
    console.log('[Facsimile Viewer] Availability:', {
        hasFacsimile,
        hasTranscription,
        textEnabled: !textBtn.disabled,
        splitEnabled: !splitBtn.disabled,
        viewerEnabled: !viewerBtn.disabled,
        optionsEnabled: !optionsBtn.disabled
    });
}

/**
 * Update options menu visibility based on current mode
 */
function updateOptionsMenuForMode(mode) {
    const optionsDropdown = document.getElementById('options-dropdown');
    const hasFacsimile = document.getElementById('layout-toggle-buttons')?.dataset.hasFacsimile === 'true';
    
    if (!optionsDropdown) return;
    
    // Hide options menu if in viewer-only mode
    if (mode === 'viewer-only') {
        optionsDropdown.innerHTML = '<div style="padding: 8px; color: #999;">Aucune option disponible</div>';
        document.getElementById('options-menu-btn').disabled = true;
    }
    // Show text options
    else if (mode === 'text-only') {
        optionsDropdown.innerHTML = `
            <label class="option-item">
                <input type="checkbox" data-option="use-diplomatic-version" ${sessionStorage.getItem('trans-option-use-diplomatic-version') === 'true' ? 'checked' : ''}>
                <span>Version diplomatique</span>
            </label>
            <label class="option-item">
                <input type="checkbox" data-option="hide-linebreaks" ${sessionStorage.getItem('trans-option-hide-linebreaks') === 'true' ? 'checked' : ''}>
                <span>Masquer les retours à la ligne</span>
            </label>
            <label class="option-item">
                <input type="checkbox" data-option="show-toc" ${sessionStorage.getItem('trans-option-show-toc') === 'true' ? 'checked' : ''}>
                <span>Afficher la table des matières</span>
            </label>
            <label class="option-item">
                <input type="checkbox" data-option="show-marginalia" ${sessionStorage.getItem('trans-option-show-marginalia') === 'true' ? 'checked' : ''}>
                <span>Afficher les notes en marge</span>
            </label>
        `;
        document.getElementById('options-menu-btn').disabled = false;
    }
    // Show split-view options
    else if (mode === 'split-view') {
        optionsDropdown.innerHTML = `
            <label class="option-item">
                <input type="checkbox" data-option="use-edited-version" ${sessionStorage.getItem('trans-option-use-edited-version') === 'true' ? 'checked' : ''}>
                <span>Version éditée</span>
            </label>
            <label class="option-item">
                <input type="checkbox" data-option="hide-linebreaks" ${sessionStorage.getItem('trans-option-hide-linebreaks') === 'true' ? 'checked' : ''}>
                <span>Masquer les retours à la ligne</span>
            </label>
            <label class="option-item">
                <input type="checkbox" data-option="show-toc" ${sessionStorage.getItem('trans-option-show-toc') === 'true' ? 'checked' : ''}>
                <span>Afficher la table des matières</span>
            </label>
        `;
        document.getElementById('options-menu-btn').disabled = false;
    }
    
    // Re-bind checkbox event listeners
    bindOptionCheckboxes();
}

/**
 * Bind event listeners to all option checkboxes
 */
function bindOptionCheckboxes() {
    const optionsDropdown = document.getElementById('options-dropdown');
    const checkboxes = optionsDropdown?.querySelectorAll('input[type="checkbox"]') || [];
    
    checkboxes.forEach(checkbox => {
        // Remove old listeners by cloning
        const newCheckbox = checkbox.cloneNode(true);
        checkbox.parentNode.replaceChild(newCheckbox, checkbox);
        
        // Add new listener
        newCheckbox.addEventListener('change', function() {
            const key = 'trans-option-' + this.dataset.option;
            sessionStorage.setItem(key, this.checked);
            console.log('[Options]', this.dataset.option, '=', this.checked);
            
            // TODO: Phase 4 - Apply visual changes
            // Examples:
            // - Use edited version: show/hide edit marks
            // - Hide linebreaks: remove <br> visualization
            // - Show TOC: toggle TOC panel visibility
            // - Show marginalia: apply margin note styling
        });
    });
}
```

**Call locations**:
- `initializeModeAvailability()` in document.ready or after DOM load
- `updateOptionsMenuForMode(mode)` whenever layout changes

### 4. Update Layout Change Handler

**File**: `app/fiches/static/fiches/js/transcription-sync.js`

**Modify existing layout button click handlers**:
```javascript
// In existing setLayout() or equivalent function
function setLayout(layoutMode) {
    // ... existing code ...
    
    // NEW: Update options menu for this mode
    updateOptionsMenuForMode(layoutMode);
    
    // ... rest of existing code ...
}
```

---

## Files to Modify

| File | Type | Changes | Complexity |
|------|------|---------|------------|
| `app/fiches/templates/fiches/display/transcription.html` | Template | Add data attributes | Low |
| `app/fiches/static/fiches/css/transcription-layout.css` | CSS | Add conditional states | Low |
| `app/fiches/static/fiches/js/transcription-sync.js` | JavaScript | Add init + mode logic | Medium |

---

## Testing Scenarios

### Test Case 1: Page with BOTH transcription + facsimilé (e.g., `/fiches/trans/1080/`)
```
✓ All 4 mode buttons visible and enabled
✓ Clicking each button switches mode
✓ Options menu visible and clickable
✓ Options change based on mode selected
✓ Default mode: Texte+Facsimilé (split-view active)
```

### Test Case 2: Page with ONLY transcription (no facsimilé)
```
✓ "Texte" button enabled (active)
✓ "Texte+Facsimilé" button disabled (grayed, not clickable)
✓ "Facsimilé" button disabled (grayed, not clickable)
✓ "Options" button enabled
✓ Options menu shows only text-specific options
✓ Default mode: Texte (text-only active)
```

### Test Case 3: Page with ONLY facsimilé (no transcription) - if exists
```
✓ "Texte" button disabled (grayed, not clickable)
✓ "Texte+Facsimilé" button disabled (grayed, not clickable)
✓ "Facsimilé" button enabled (active)
✓ "Options" button disabled (grayed, not clickable)
✓ Options menu hidden or shows "no options available"
✓ Default mode: Facsimilé (viewer-only active)
```

---

## Browser Testing

```javascript
// In browser console to verify states:
const container = document.getElementById('layout-toggle-buttons');
console.log('Has Facsimilé:', container.dataset.hasFacsimile);
console.log('Has Transcription:', container.dataset.hasTranscription);
console.log('Text button disabled:', document.querySelector('.text-only-btn').disabled);
console.log('Split button disabled:', document.querySelector('.split-view-btn').disabled);
console.log('Viewer button disabled:', document.querySelector('.viewer-only-btn').disabled);
console.log('Options button disabled:', document.getElementById('options-menu-btn').disabled);
```

---

## Validation Checklist

### Data Attributes
- [ ] Template passes `data-has-facsimile` correctly from model
- [ ] `data-has-transcription` hardcoded to true
- [ ] No console errors when attributes render

### CSS Conditional States
- [ ] Disabled buttons have reduced opacity (0.5)
- [ ] Disabled buttons have gray background
- [ ] Disabled buttons have "not-allowed" cursor
- [ ] Disabled buttons DO NOT respond to clicks

### JavaScript Logic
- [ ] `initializeModeAvailability()` runs on page load
- [ ] Console logs show correct availability detection
- [ ] Buttons disabled/enabled correctly per test cases
- [ ] Mode cannot be changed if buttons disabled
- [ ] Options menu updates when switching modes
- [ ] Options persist across mode switches (sessionStorage)

### User Experience
- [ ] Users cannot click disabled buttons
- [ ] Visual feedback clear (grayed out)
- [ ] Option menu dynamically updates content
- [ ] No glitches or flickering during mode switches
- [ ] Mobile responsive (if applicable)

---

## Edge Cases

| Scenario | Current Behavior | Expected |
|----------|------------------|----------|
| Page load with viewer-only mode possible | CSS pre-sets, then JS adjusts | ✅ Correct |
| Switching mode rapidly | Should debounce/queue updates | ⚠️ Test |
| Small screen width | Options button should not wrap | ⚠️ Test |
| No IIIF URL provided | `data-has-facsimile` = false | ✅ Correct |

---

## Time Breakdown

| Task | Hours | Notes |
|------|-------|-------|
| HTML data attributes | 0.5h | Simple addition |
| CSS conditional states | 0.5h | Several new rules |
| JavaScript initialization | 1.0h | Detect & disable logic |
| Update options per mode | 0.8h | Dynamic menu content |
| Testing & refinement | 0.2h | Cross-browser testing |
| **Total** | **3.0h** | As estimated |

---

## Dependencies

**Blocks On**:
- Phase 2 completion (options menu structure)

**Blocks**:
- Phase 4: Apply visual effects based on options

---

## Approved Scenarios

**Before Implementation**, confirm:
- [ ] Rule 1 (only facsimilé) acceptable: viewer-only forced?
- [ ] Rule 2 (only text) acceptable: text-only forced?
- [ ] Rule 3 (both) default (split-view) acceptable?
- [ ] Option visibility logic matches requirements?

---

**Ready for Review**: ✅  
**Next Phase**: Phase 4 - Apply Visual Changes Based on Options
