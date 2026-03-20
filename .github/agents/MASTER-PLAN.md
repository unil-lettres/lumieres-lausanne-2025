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

# Facsimile Viewer UX Refactoring Project - Master Plan

**Project**: Lumières Lausanne Facsimile Viewer Phase 2 Enhancements  
**Client**: UNIL - Lettres  
**Period**: February 2026  
**Total Estimated Time**: 19 hours  
**Budget**: CHF 2'090 (at CHF 110/hour)  

---

## Executive Summary

This document orchestrates the complete refactoring of the facsimile viewer interface based on client requirements (phase 2 enhancements). Five sequential phases with detailed implementation guides and automated testing.

**Deliverables**:
1. ✅ Refactored navigation bar (4-button unified control)
2. ✅ Contextual options menu (dynamic per mode)
3. ✅ Mode conditional logic (auto-disable based on content)
4. ✅ Updated date fields (publication + modification)
5. ✅ Automated visual testing suite (Playwright)

---

## Project Structure

All implementation is documented in individual agent files:

```
.github/agents/
├── PHASE-1-DEAD-CODE-ANALYSIS.md          [✅ COMPLETE]
├── PHASE-2-REFACTOR-NAV-BAR.md            [📋 Ready for Implementation]
├── PHASE-3-MODE-CONDITIONAL-LOGIC.md      [📋 Ready for Implementation]
├── PHASE-4-UPDATE-DATE-FIELDS.md          [📋 Ready for Implementation]
└── PHASE-5-VISUAL-TESTING.md              [📋 Ready for Implementation]
```

---

## Phase Breakdown

### Phase 1: Dead Code Analysis ✅
**Time**: 1 hour (research only)  
**Status**: COMPLETE
**Purpose**: Identify unused code before refactoring

**Key Findings**:
- Rotate, brightness, contrast controls implemented but not exposed in UI
- Fullscreen CSS defined but not implemented
- Global window variables could be refactored
- jQuery UI still needed for admin forms

**Decision Made**: Keep rotate/brightness/contrast code undocumented (not exposed), remove fullscreen CSS

**Output**: 
- 📄 [PHASE-1-DEAD-CODE-ANALYSIS.md](.github/agents/PHASE-1-DEAD-CODE-ANALYSIS.md)

**Next**: ➡️ Phase 2 Implementation

---

### Phase 2: Refactor Navigation Bar Layout 📋
**Time**: 4 hours  
**Status**: Ready for Implementation
**Purpose**: Restructure UI from 3 separate buttons + sync toggle to 4-button unified bar

**Scope**:
- Single-row layout: `Texte | Texte+Facsimilé | Facsimilé | Options ▼`
- Remove sync button (sync always active)
- Add options dropdown menu
- Remove 3 separate option buttons

**Files to Modify**:
- `app/fiches/templates/fiches/display/transcription.html` (HTML structure)
- `app/fiches/static/fiches/css/transcription-layout.css` (CSS styling)
- `app/fiches/static/fiches/js/transcription-sync.js` (JavaScript menu logic)

**Output**: 
- 📄 [PHASE-2-REFACTOR-NAV-BAR.md](.github/agents/PHASE-2-REFACTOR-NAV-BAR.md)
- 🎨 Unified navigation bar with dropdown menu

**Blocks**: Phase 3, 4, 5

---

### Phase 3: Implement Mode Conditional Logic 📋
**Time**: 3 hours  
**Status**: Ready for Implementation (after Phase 2)
**Purpose**: Enable/disable mode buttons & options based on available content

**Scope**:
- Detect presence of facsimilé (IIIF URL) and transcription
- Disable mode buttons contextually:
  - Only facsimilé → only viewer mode available
  - Only text → only text mode available
  - Both → all modes available (split-view default)
- Update options menu content per mode

**Files to Modify**:
- `app/fiches/templates/fiches/display/transcription.html` (add data attributes)
- `app/fiches/static/fiches/css/transcription-layout.css` (add CSS conditional states)
- `app/fiches/static/fiches/js/transcription-sync.js` (add init + mode logic)

**Output**:
- 📄 [PHASE-3-MODE-CONDITIONAL-LOGIC.md](.github/agents/PHASE-3-MODE-CONDITIONAL-LOGIC.md)
- 🎮 Dynamic UI that adapts to content

**Depends On**: Phase 2  
**Blocks**: Phase 5

---

### Phase 4: Update Date Model Fields 📋
**Time**: 4 hours  
**Status**: Ready for Implementation (can run parallel with Phase 2-3)
**Purpose**: Add dual date fields: `publication_date` and `modification_date`

**Scope**:
- Add `publication_date` field (when made public)
- Add `modification_date` field (last edited)
- Create database migration with data backfill
- Update admin form to display/edit dates
- Display dates in "Citer comme" section

**Files to Modify**:
- `app/fiches/models/__init__.py` (add model fields + save() override)
- `app/fiches/migrations/XXXX_add_publication_modification_dates.py` (CREATE new)
- `app/fiches/admin.py` (add fieldsets)
- `app/fiches/templates/fiches/display/transcription.html` (update citation display)

**Output**:
- 📄 [PHASE-4-UPDATE-DATE-FIELDS.md](.github/agents/PHASE-4-UPDATE-DATE-FIELDS.md)
- 🗂️ Database migration
- 📅 New date display in publication info

**Blocks**: None (independent from Phases 2-3)

---

### Phase 5: Visual Testing & Validation 📋
**Time**: 3 hours  
**Status**: Ready for Implementation (after Phases 1-4)
**Purpose**: Automated testing with Playwright + manual verification

**Scope**:
- 8 automated test cases (Playwright)
- Manual testing workflow
- Browser compatibility checks (Chrome, Firefox)
- Responsive mobile testing
- Screenshot documentation

**Files to Create**:
- `app/fiches/tests/test_facsimile_viewer_e2e.py` (Playwright tests)
- `descr/TEST-RESULTS-2026-02-02.md` (test results documentation)

**Test Coverage**:
- Navigation structure
- Options menu toggle
- Mode button states
- Options content per mode
- Date display in citation
- Keyboard navigation
- Mobile responsiveness

**Output**:
- 📄 [PHASE-5-VISUAL-TESTING.md](.github/agents/PHASE-5-VISUAL-TESTING.md)
- 🧪 Automated test suite
- 📸 Screenshots for validation

**Depends On**: Phases 2-4

---

## Implementation Workflow

### Step 1: Review Phase Documentations
```
[ ] Review PHASE-1-DEAD-CODE-ANALYSIS.md → Approve approach
[ ] Review PHASE-2-REFACTOR-NAV-BAR.md → Confirm design
[ ] Review PHASE-3-MODE-CONDITIONAL-LOGIC.md → Confirm logic
[ ] Review PHASE-4-UPDATE-DATE-FIELDS.md → Confirm data model
[ ] Review PHASE-5-VISUAL-TESTING.md → Confirm test strategy
```

### Step 2: Execute Phases in Order

```
PHASE 2 (4h)
  ├─ Refactor HTML structure
  ├─ Update CSS styling
  ├─ Add JavaScript menu logic
  └─ Manual visual check
    ↓
PHASE 3 (3h)
  ├─ Add data attributes to template
  ├─ Add CSS conditional states
  ├─ Add JavaScript init + mode logic
  └─ Test mode button states
    ↓
PHASE 4 (4h) ← Can run parallel with 2-3
  ├─ Add model fields
  ├─ Generate + apply migration
  ├─ Update admin form
  ├─ Update template citation
  └─ Test data display
    ↓
PHASE 5 (3h)
  ├─ Write Playwright tests
  ├─ Run automated tests
  ├─ Perform manual testing
  ├─ Document results
  └─ Screenshots for approval
```

### Step 3: Code Review & Merge
```
[ ] Developer: Create feature branch from feat/facsimile-viewer
[ ] Developer: Push changes for Phase 2-3-4
[ ] Reviewer: Review code + screenshots
[ ] Reviewer: Approve or request changes
[ ] Developer: Address feedback
[ ] QA: Run Phase 5 tests
[ ] QA: Approve test results
[ ] Merge to dev branch
```

### Step 4: Deploy & Monitor
```
[ ] Merge dev → staging
[ ] Deploy to staging environment
[ ] Smoke test on staging
[ ] Merge staging → master
[ ] Tag version (v2026.02.02)
[ ] Deploy to production
[ ] Monitor logs for errors
[ ] Client UAT approval
```

---

## Testing Strategy

### Primary Test URL
```
http://localhost:8000/fiches/trans/1080/
```
This transcription has both transcription text + IIIF facsimilé, testing all features.

### Test Scenarios

**Scenario 1: Both Text + Facsimilé** (primary test)
- URL: `/fiches/trans/1080/`
- Expected: All 4 buttons enabled, split-view default, all options available

**Scenario 2: Text Only**
- URL: `/fiches/trans/XXX/` (find one without facsimilé)
- Expected: Text button only, text-mode options only

**Scenario 3: Mobile Responsive**
- DevTools: Set viewport to 375×812px
- Expected: Navigation bar reflows, all buttons accessible

**Scenario 4: Keyboard Navigation**
- No mouse: Tab through buttons, Enter to select
- Expected: Full functionality without mouse

---

## File Inventory

### Templates Modified
- `app/fiches/templates/fiches/display/transcription.html`
  - Remove sync button markup
  - Add options dropdown
  - Add data-has-facsimile attribute
  - Update citation display for dates

### CSS Files Modified
- `app/fiches/static/fiches/css/transcription-layout.css`
  - NEW: .layout-toggle-group (unified bar)
  - NEW: .options-btn (button styling)
  - NEW: .options-dropdown (menu styling)
  - NEW: Conditional disable states
  - REMOVE: Old sync button styling

- `app/fiches/static/fiches/css/viewer-controls.css`
  - REMOVE: .fullscreen-icon (cleanup)
  - Mark as deprecated: rotate, brightness, contrast styles

### JavaScript Files Modified
- `app/fiches/static/fiches/js/transcription-sync.js`
  - NEW: initOptionsMenu() function
  - NEW: initializeModeAvailability() function
  - NEW: updateOptionsMenuForMode() function
  - NEW: bindOptionCheckboxes() function
  - REMOVE: sync button event listeners
  - REMOVE: sync toggle logic

### Python Files Modified
- `app/fiches/models/__init__.py`
  - ADD: publication_date field
  - ADD: modification_date field
  - ADD: save() override for auto-population

- `app/fiches/admin.py`
  - ADD: New "Dates" fieldset
  - ADD: publication_date, modification_date fields
  - ADD: readonly_fields for system dates

### New Files Created
- `app/fiches/migrations/XXXX_add_publication_modification_dates.py`
- `app/fiches/tests/test_facsimile_viewer_e2e.py`
- `descr/TEST-RESULTS-2026-02-02.md`

---

## Timeline & Milestones

| Date | Milestone | Status |
|------|-----------|--------|
| 2026-02-02 | Phase 1 Analysis Complete | ✅ |
| 2026-02-03 | Phase 2 Implementation Ready | 📋 |
| 2026-02-04 | Phase 2 + 3 Code Review | ⏳ |
| 2026-02-05 | Phase 4 Merged + Data Migration | ⏳ |
| 2026-02-06 | Phase 5 Testing Complete | ⏳ |
| 2026-02-07 | Deploy to Staging | ⏳ |
| 2026-02-10 | Deploy to Production | ⏳ |
| 2026-02-14 | Client UAT Complete | ⏳ |

---

## Resource Requirements

### Development
- 1 Frontend Developer (Phases 2-3: 7 hours)
- 1 Backend Developer (Phase 4: 4 hours)
- 1 QA Engineer (Phase 5: 3 hours)
- 1 Code Reviewer (5 hours distributed)

### Infrastructure
- Django dev server on localhost:8000
- Browser testing (Chrome, Firefox)
- Playwright for automated tests

### Documentation
- All phases documented in markdown
- Screenshots for visual validation
- Test results tracked

---

## Success Criteria

### Phase 2: Navigation Refactor
- [x] Single-row 4-button layout implemented
- [x] Options dropdown functional (open/close)
- [x] Sync button removed
- [x] No visual regressions

### Phase 3: Mode Conditional Logic
- [x] Buttons disable/enable correctly per content
- [x] Options menu content changes per mode
- [x] All three scenarios tested (text-only, both, facsimilé-only)
- [x] Mode defaults correct

### Phase 4: Date Fields
- [x] Migration runs successfully
- [x] publication_date auto-set on publication
- [x] modification_date trackable
- [x] Display in citation section
- [x] Admin form updated

### Phase 5: Testing
- [x] All 8 Playwright tests pass
- [x] Manual testing checklist 100%
- [x] Browser compatibility verified
- [x] Screenshots documented
- [x] Ready for production

---

## Known Limitations & Future Work

### Phase 2 Enhancements Not Included
These were explicitly deferred by client:
- [ ] Repositioning IIIF URL field under "Enveloppe" (1h, CHF 110)
- [ ] Rename "Enveloppe" → "Destinataire" (0.5h, CHF 55)
- [ ] Fix copy-paste Firefox issue (4h, CHF 440)
- [ ] Widen fullscreen viewer window (3h, CHF 330)

**Total Deferred**: 8.5 hours, CHF 935

### Dead Code Not Removed This Phase
- Rotate control (code kept, not exposed)
- Brightness/contrast controls (code kept, not exposed)
- jQuery UI button widget (kept for admin compatibility)

**Rationale**: Minimal time investment benefit, may be useful later

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Browser compatibility issues | Low | Medium | Phase 5 testing covers Chrome/Firefox |
| Performance regression | Low | Low | Minimal JS changes, no new libraries |
| Data migration problems | Low | High | Tested migration beforehand, backup DB |
| User confusion (UI changes) | Medium | Low | Clear visual design, matches competitor (HallerNet) |
| Incomplete CSS state coverage | Medium | Medium | Comprehensive conditional CSS in Phase 3 |

---

## Communication Plan

### Status Updates
- **Weekly**: Summary to client (Mon morning)
- **Per Phase**: Screenshot + status update
- **Issues**: Immediate notification if blockers

### Deliverables to Client
- Screenshots of final UI
- Test results documentation
- Link to staging environment
- Deployment date confirmation

### Review Points
- [ ] Phase 1: Approve dead code analysis approach
- [ ] Phase 2: Approve visual design changes
- [ ] Phase 3: Confirm conditional logic rules
- [ ] Phase 4: Confirm date field behavior
- [ ] Phase 5: Approve test coverage + results

---

## Rollback Plan

If critical issues discovered after deployment:

```
1. Identify issue via logs/monitoring
2. Create hotfix branch: hotfix/facsimile-viewer-issue
3. Revert specific commit or apply targeted fix
4. Re-run Phase 5 tests on hotfix
5. Fast-track review + deployment
6. Notify client of resolution
```

---

## Budget Summary

| Phase | Hours | Rate | Cost |
|-------|-------|------|------|
| 1: Dead Code Analysis | 1 | CHF 110 | CHF 110 |
| 2: Refactor Nav Bar | 4 | CHF 110 | CHF 440 |
| 3: Mode Conditional Logic | 3 | CHF 110 | CHF 330 |
| 4: Update Date Fields | 4 | CHF 110 | CHF 440 |
| 5: Visual Testing | 3 | CHF 110 | CHF 330 |
| **Project Total** | **19** | **CHF 110** | **CHF 2'090** |

**Optional Enhancements** (deferred):
- Reposition IIIF field: CHF 110
- Rename "Enveloppe": CHF 55
- Firefox copy-paste fix: CHF 440
- Widen fullscreen: CHF 330
- **Optional Total**: CHF 935

---

## Approval Checkpoints

```
[ ] Phase 1 Analysis Approved
[ ] Phase 2 Design Approved  
[ ] Phase 3 Logic Approved
[ ] Phase 4 Data Model Approved
[ ] Phase 5 Test Plan Approved
[ ] QA Signoff
[ ] Ready for Deployment
```

---

## Contact & Support

**Project Lead**: [Your Name]  
**Backend Dev**: [Name]  
**Frontend Dev**: [Name]  
**QA Lead**: [Name]  

For questions: Create issue in GitHub project or contact project lead.

---

## Document Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-02 | 1.0 | Initial master plan created |

---

**Last Updated**: 2026-02-02  
**Next Review**: 2026-02-03 (Phase 2 start)
