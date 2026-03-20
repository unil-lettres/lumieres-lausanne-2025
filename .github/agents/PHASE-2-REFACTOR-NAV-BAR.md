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

# Phase 2: Refactor Navigation Bar Layout

**Estimated Time**: 4 hours
**Status**: Ready for Implementation
**Objective**: Restructure the transcription mode buttons from 3 separate buttons + sync toggle to a single-row unified bar: `Texte | Texte+Facsimilé | Facsimilé | Options ▼`

---

## Current State (Before)

```html
<div id="layout-toggle-buttons" class="layout-toggle-group">
    <button type="button" class="layout-btn" data-layout="text-only">
        Texte
    </button>
    <button type="button" class="layout-btn active" data-layout="split-view">
        Texte + Facsimilé
    </button>
    <button type="button" class="layout-btn" data-layout="viewer-only">
        Facsimilé
    </button>
    <span id="sync-toggle-wrapper" style="margin-left: 20px; display: inline-block; border-left: 1px solid #ccc; padding-left: 20px;">
        <button type="button" id="sync-toggle-btn" class="layout-btn active">
            🔗 Synchro
        </button>
    </span>
</div>

<!-- Separate option buttons (below, to be hidden) -->
<div style="margin-top: 10px;">
    <button class="layout-btn">Version éditée</button>
    <button class="layout-btn">Cacher retours ligne</button>
    <button class="layout-btn">Table des matières</button>
</div>
```

**Issues**:
- 2 separate UI rows
- Sync button separated by visual divider
- 3 option buttons not contextual (always visible)
- Inconsistent button styling

---

## Target State (After)

```html
<div id="layout-toggle-buttons" class="layout-toggle-group">
    <button type="button" class="layout-btn text-only-btn" data-layout="text-only" title="Mode texte uniquement">
        Texte
    </button>
    <button type="button" class="layout-btn split-view-btn active" data-layout="split-view" title="Mode texte et facsimilé synchronisés">
        Texte + Facsimilé
    </button>
    <button type="button" class="layout-btn viewer-only-btn" data-layout="viewer-only" title="Mode facsimilé uniquement">
        Facsimilé
    </button>
    <button type="button" id="options-menu-btn" class="layout-btn options-btn" title="Options d'affichage">
        Options <span class="dropdown-arrow">▼</span>
    </button>
    
    <!-- Options dropdown menu (hidden, shown on click) -->
    <div id="options-dropdown" class="options-dropdown">
        <label class="option-item">
            <input type="checkbox" name="option-version" value="edited" data-option="use-edited-version">
            <span>Version éditée</span>
        </label>
        <label class="option-item">
            <input type="checkbox" name="option-linebreaks" value="hide" data-option="hide-linebreaks">
            <span>Cacher les retours à la ligne</span>
        </label>
        <label class="option-item">
            <input type="checkbox" name="option-toc" value="show" data-option="show-toc">
            <span>Afficher la table des matières</span>
        </label>
    </div>
</div>
```

**Improvements**:
- Single-row unified control bar
- Sync button removed (sync always active, configurable in Phase 4)
- Options menu hidden by default, shown on "Options ▼" click
- Proper aria labels for accessibility

---

## Implementation Details

### 1. HTML Changes

**File**: `app/fiches/templates/fiches/display/transcription.html`

**Changes**:
- Remove `#sync-toggle-wrapper` and sync button markup
- Add `#options-menu-btn` button after facsimilé button
- Add `#options-dropdown` div with checkbox options
- Add `data-layout` attributes to buttons for consistency

**Lines Affected**: 125-159 (current layout-toggle-buttons section)

### 2. CSS Changes

**File**: `app/fiches/static/fiches/css/transcription-layout.css`

**New Classes**:
```css
/* Updated button row styling */
.layout-toggle-group {
    display: flex;
    gap: 0;
    align-items: center;
    background-color: #f5f5f5;
    padding: 8px 12px;
    border-radius: 4px;
    border: 1px solid #ddd;
    margin-bottom: 15px;
}

/* Mode buttons (no gaps, separated by light border) */
.layout-btn {
    flex: 0 0 auto;
    padding: 6px 12px;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 0;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s ease;
}

.layout-btn:first-child {
    border-radius: 3px 0 0 3px;
}

.layout-btn:nth-child(3) {
    border-radius: 0 0 0 0;
}

/* Options button styling */
.options-btn {
    margin-left: auto;
    border-radius: 0 3px 3px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}

.dropdown-arrow {
    font-size: 10px;
    transition: transform 0.2s ease;
}

.options-btn.active .dropdown-arrow {
    transform: rotate(180deg);
}

/* Options dropdown menu */
.options-dropdown {
    position: absolute;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    min-width: 220px;
    display: none;
    margin-top: 4px;
}

.options-dropdown.show {
    display: block;
}

.option-item {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    cursor: pointer;
    user-select: none;
    border-bottom: 1px solid #f0f0f0;
}

.option-item:last-child {
    border-bottom: none;
}

.option-item:hover {
    background-color: #f9f9f9;
}

.option-item input[type="checkbox"] {
    margin-right: 8px;
    cursor: pointer;
}

.option-item span {
    flex: 1;
}

/* Active button state */
.layout-btn.active {
    background-color: #e8e8e8;
    font-weight: 600;
    border-color: #999;
}

.layout-btn:hover:not(.active) {
    background-color: #fafafa;
}
```

**Lines to Add**: After existing `.layout-toggle-group` styles (around line 30)

### 3. JavaScript Changes

**File**: `app/fiches/static/fiches/js/transcription-sync.js`

**Changes**:
1. **Remove sync toggle logic** (currently lines managing sync button)
2. **Add options menu toggle**:
   - Click "Options ▼" → show/hide dropdown
   - Click outside → close dropdown
   - Checkboxes save state to sessionStorage

3. **Update layout toggle binding**:
   - Remove sync button event listener
   - Keep existing layout button handlers

**New Functions to Add**:
```javascript
// Options menu management
function initOptionsMenu() {
    const optionsBtn = document.getElementById('options-menu-btn');
    const optionsDropdown = document.getElementById('options-dropdown');
    
    // Toggle menu on button click
    optionsBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        optionsDropdown.classList.toggle('show');
        optionsBtn.classList.toggle('active');
    });
    
    // Close menu on outside click
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#layout-toggle-buttons')) {
            optionsDropdown.classList.remove('show');
            optionsBtn.classList.remove('active');
        }
    });
    
    // Handle option checkbox changes
    const checkboxes = optionsDropdown.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        // Restore previous state
        const saved = sessionStorage.getItem('trans-option-' + checkbox.dataset.option);
        if (saved === 'true') checkbox.checked = true;
        
        // Save on change
        checkbox.addEventListener('change', function() {
            sessionStorage.setItem('trans-option-' + this.dataset.option, this.checked);
            // TODO: Phase 3 - Apply visual changes based on option
            console.log('Option changed:', this.dataset.option, '=', this.checked);
        });
    });
}
```

**Lines to Modify**:
- Remove sync button binding (around line 450 in current transcription-sync.js)
- Add `initOptionsMenu()` call in initialization section

### 4. CSS Cleanup (Optional)

**File**: `app/fiches/static/fiches/css/viewer-controls.css`

**Deprecate** (mark as unused):
- Old sync button styles
- Old 3-button group styles
- Lines: 80-120 (approximately)

---

## Files to Modify

| File | Type | Changes | Lines |
|------|------|---------|-------|
| `app/fiches/templates/fiches/display/transcription.html` | Template | HTML structure, remove sync wrapper | 125-159 |
| `app/fiches/static/fiches/css/transcription-layout.css` | CSS | New button bar styling, dropdown menu | +80 |
| `app/fiches/static/fiches/js/transcription-sync.js` | JavaScript | Add options menu logic, remove sync button | +25 |
| `app/fiches/static/fiches/css/viewer-controls.css` | CSS | Optional cleanup of old styles | ~20 |

---

## Validation Checklist

### HTML Structure
- [ ] 4 buttons in single row: Texte | Texte+Facsimilé | Facsimilé | Options ▼
- [ ] Sync button removed completely
- [ ] Options dropdown hidden by default
- [ ] 3 checkboxes in dropdown menu
- [ ] No visual horizontal line divider

### CSS & Styling
- [ ] Buttons have no gap between them (border-only separated)
- [ ] Options button positioned on right with `margin-left: auto`
- [ ] Dropdown arrow rotates on menu open
- [ ] Dropdown positioned below button bar, not overlapping content
- [ ] Options dropdown has shadow for depth
- [ ] Checkboxes aligned properly with labels

### JavaScript Functionality
- [ ] Click "Options ▼" toggles dropdown visibility
- [ ] Click outside closes dropdown
- [ ] Checkbox state persists in sessionStorage
- [ ] Console log shows option changes (for Phase 3)
- [ ] No JavaScript errors in console
- [ ] All event listeners properly bound

### Visual Testing
- [ ] Test at `/fiches/trans/1080/`
- [ ] Screenshot: Before state (current) + After state (refactored)
- [ ] Responsive: Check mobile view (if applicable)
- [ ] Accessibility: Tab navigation through buttons
- [ ] Browser compatibility: Chrome, Firefox, Safari

---

## Success Criteria

✅ **Phase 2 Complete When**:
1. Navigation bar is single-row with 4 buttons
2. Options menu opens/closes on button click
3. Checkboxes state persists across page navigation
4. No console errors
5. Visual matches target design (from client requirements doc)
6. All existing functionality preserved (layout switching works)

---

## Testing Commands

```bash
# Visual inspection on localhost
curl http://localhost:8000/fiches/trans/1080/

# Check for JavaScript errors (use browser DevTools)
# - Open DevTools > Console
# - Verify no red errors after page load
# - Test click "Options ▼" → verify dropdown appears

# Check sessionStorage
# - Browser DevTools > Application > SessionStorage
# - Verify keys like "trans-option-use-edited-version" exist
```

---

## Dependencies

**Blocks On**:
- None (can start immediately after Phase 1 review)

**Blocks**:
- Phase 3: Options menu behavior implementation
- Phase 4: Mode conditional logic (disabled states)

---

## Time Breakdown

| Task | Hours | Notes |
|------|-------|-------|
| HTML refactoring | 0.5h | Remove sync, add options menu |
| CSS rewrite | 1.5h | Button bar + dropdown styling |
| JavaScript | 1.0h | Menu toggle + checkbox persistence |
| Testing & refinement | 1.0h | Browser testing, alignment fixes |
| **Total** | **4.0h** | As estimated |

---

## Next Phase

**Phase 3**: Add Contextual Options Menu Logic
- Different options per mode (Text vs. Text+Facsimilé vs. Facsimilé)
- Apply visual changes based on checkbox states
- Disable/enable checkboxes based on available content

---

**Ready for Review**: ✅  
**PM Decision Needed**: 
- [ ] Approve HTML structure changes?
- [ ] Approve CSS styling direction?
- [ ] Any color/styling preferences for dropdown?
