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

# 🚀 Lumières Lausanne Facsimile Viewer - Phase 2 Implementation Plan

**Status**: ✅ DOCUMENTATION COMPLETE - READY FOR IMPLEMENTATION  
**Date**: February 2, 2026  
**Project**: Facsimile Viewer UX Refactoring (Phase 2)

---

## 📋 What You Need To Do Now

### 1️⃣ Review the Documentation

All implementation details are documented in 6 markdown files:

**📄 Documentation Files Location**: `.github/agents/`

```
✅ PHASE-1-DEAD-CODE-ANALYSIS.md
   └─ Analysis of unused code (rotate, brightness, contrast, fullscreen)
   └─ Decision: Keep code but don't expose in UI

📋 PHASE-2-REFACTOR-NAV-BAR.md
   └─ Refactor: 3 buttons + sync toggle → 4-button unified bar
   └─ Add options dropdown menu
   └─ Estimated: 4 hours

📋 PHASE-3-MODE-CONDITIONAL-LOGIC.md
   └─ Auto-disable buttons based on content availability
   └─ Dynamic options menu per mode
   └─ Estimated: 3 hours

📋 PHASE-4-UPDATE-DATE-FIELDS.md
   └─ Add publication_date + modification_date fields
   └─ Database migration included
   └─ Estimated: 4 hours

📋 PHASE-5-VISUAL-TESTING.md
   └─ Playwright automated tests (8 test cases)
   └─ Manual testing workflow
   └─ Estimated: 3 hours

📋 MASTER-PLAN.md
   └─ Complete project orchestration
   └─ Timeline, budget, risk assessment
```

### 2️⃣ Key Approvals Needed

Before implementation starts, please confirm:

**PHASE 1 - Code Cleanup**:
- [ ] Keep rotate/brightness/contrast code (undocumented) or remove?
- [ ] Remove fullscreen CSS?

**PHASE 2 - Navigation Bar**:
- [ ] Approve 4-button layout design?
- [ ] Approve CSS styling direction?
- [ ] Any color/styling preferences for dropdown?

**PHASE 3 - Conditional Logic**:
- [ ] Approve: Only facsimilé → force viewer-only mode?
- [ ] Approve: Only text → force text-only mode?
- [ ] Approve: Both available → default to split-view?

**PHASE 4 - Date Fields**:
- [ ] Backfill strategy: Use existing modified_date or manual review?
- [ ] Date format: "dd.mm.yyyy" acceptable?

**PHASE 5 - Testing**:
- [ ] Playwright test suite coverage sufficient?
- [ ] Manual testing workflow comprehensive?

---

## 🎯 Implementation Phases Overview

### Phase 2: Refactor Navigation Bar (4 hours)
**What changes visually**:
```
BEFORE:
┌─────────┬──────────────────┬───────────┐    ┌───────────────────┐
│ Texte   │ Texte+Facsimilé  │ Facsimilé │    │ 🔗 Synchroniser   │
└─────────┴──────────────────┴───────────┘    └───────────────────┘
<3 separate buttons at bottom>

AFTER:
┌─────────┬──────────────────┬───────────┬──────────────┐
│ Texte   │ Texte+Facsimilé  │ Facsimilé │ Options  ▼   │
└─────────┴──────────────────┴───────────┴──────────────┘
```

**Files Modified**:
- `app/fiches/templates/fiches/display/transcription.html`
- `app/fiches/static/fiches/css/transcription-layout.css` (+80 lines)
- `app/fiches/static/fiches/js/transcription-sync.js` (+25 lines)

---

### Phase 3: Mode Conditional Logic (3 hours)
**What changes functionally**:
- Buttons disable/enable based on available content
- Options menu shows different options per mode
- Auto-select appropriate mode if only one available

**Test Scenarios**:
1. ✅ Both text + facsimilé (primary): All buttons enabled, split-view default
2. ✅ Text only: Text button only, options visible
3. ✅ Facsimilé only: Viewer button only, no options

---

### Phase 4: Update Date Fields (4 hours)
**What changes in database/admin**:
- Add `publication_date` (when made public)
- Add `modification_date` (last edited)
- Auto-populate on save
- Display in citation section

**Data Migration**:
- Backfill existing public transcriptions
- No data loss

---

### Phase 5: Visual Testing (3 hours)
**What we test**:
- ✅ 8 automated Playwright test cases
- ✅ Manual testing checklist
- ✅ Browser compatibility (Chrome, Firefox)
- ✅ Mobile responsive (375px viewport)
- ✅ Keyboard navigation

**Primary Test URL**: `http://localhost:8000/fiches/trans/1080/`

---

## 🗂️ Complete File List

### Files to Create (New)
```
.github/agents/
├── PHASE-1-DEAD-CODE-ANALYSIS.md ✅
├── PHASE-2-REFACTOR-NAV-BAR.md ✅
├── PHASE-3-MODE-CONDITIONAL-LOGIC.md ✅
├── PHASE-4-UPDATE-DATE-FIELDS.md ✅
├── PHASE-5-VISUAL-TESTING.md ✅
└── MASTER-PLAN.md ✅

app/fiches/tests/
└── test_facsimile_viewer_e2e.py (to create in Phase 5)

descr/
└── TEST-RESULTS-2026-02-02.md (to create in Phase 5)
```

### Files to Modify

**Frontend (Phases 2-3)**:
- `app/fiches/templates/fiches/display/transcription.html`
- `app/fiches/static/fiches/css/transcription-layout.css`
- `app/fiches/static/fiches/css/viewer-controls.css` (cleanup)
- `app/fiches/static/fiches/js/transcription-sync.js`

**Backend (Phase 4)**:
- `app/fiches/models/__init__.py` (add 2 fields + save() override)
- `app/fiches/admin.py` (add fieldsets)
- `app/fiches/forms.py` (if custom edit form exists)
- `app/fiches/migrations/XXXX_add_publication_modification_dates.py` (new)

**Frontend Display (Phase 4)**:
- `app/fiches/templates/fiches/display/transcription.html` (update citation)

---

## 📅 Recommended Timeline

```
Mon 2026-02-03: Phase 2 - Refactor navigation bar (4h)
Tue 2026-02-04: Phase 3 - Mode conditional logic (3h) + Code Review
Wed 2026-02-05: Phase 4 - Update date fields (4h) + Database testing
Thu 2026-02-06: Phase 5 - Visual testing (3h) + Manual verification
Fri 2026-02-07: Deploy to Staging + Client testing
Mon 2026-02-10: Deploy to Production
```

**Total**: 19 hours developer work  
**Budget**: CHF 2'090 (@ CHF 110/hour)

---

## 🔍 Quality Assurance Plan

### Manual Testing (Phase 5)
Test on **`http://localhost:8000/fiches/trans/1080/`**:

1. ✅ Navigation structure (4 buttons, single row)
2. ✅ Options menu (open/close/outside click)
3. ✅ Mode switching (all 3 modes work)
4. ✅ Options content (different per mode)
5. ✅ Date display (citation section)
6. ✅ Keyboard nav (Tab/Enter work)
7. ✅ Mobile responsive (375px viewport)
8. ✅ Browser compat (Chrome, Firefox)

### Automated Testing (Phase 5)
- 8 Playwright test cases
- Screenshots for documentation
- Browser console error checking

---

## 🚦 Current Status

```
Phase 1: Analysis ✅ COMPLETE
Phase 2: Ready for Implementation 📋
Phase 3: Ready for Implementation 📋
Phase 4: Ready for Implementation 📋
Phase 5: Ready for Implementation 📋
```

---

## ✅ Next Steps

### Immediate (Today)
1. Read `.github/agents/MASTER-PLAN.md` for overview
2. Read each phase documentation (2-5)
3. Provide feedback/approvals

### After Approval
1. Implement Phase 2 (4 hours)
2. Code review + screenshot
3. Implement Phase 3 (3 hours)
4. Code review + testing
5. Implement Phase 4 (4 hours) - can be parallel
6. Database testing
7. Implement Phase 5 (3 hours)
8. All tests pass → Ready for deployment

---

## 📞 Questions to Ask

Before implementation, confirm:

1. **UI Design**: Is the 4-button layout acceptable, or prefer different arrangement?
2. **Options Menu**: Should "Options ▼" be on right side? Any preferred styling?
3. **Date Fields**: Should dates be required or optional in admin form?
4. **Mode Defaults**: Is "Text+Facsimilé" the correct default when both available?
5. **Testing**: Playwright tests sufficient, or need additional manual tests?

---

## 🎓 Key Technical Decisions Made

### Decision 1: Keep Unused Code
- Rotate/brightness/contrast controls exist but not exposed
- No user sees them, minimal code footprint
- Could be useful for future features

### Decision 2: Remove Sync Button
- Sync always active (per client requirement)
- No need for toggle button
- Cleaner UI

### Decision 3: Single-Row Navigation
- Matches HallerNet design (client reference)
- More compact than current 2-row layout
- Better mobile experience

### Decision 4: Contextual Options Menu
- Different options per mode (text vs. split vs. viewer)
- Dynamic content in dropdown
- Cleaner than 3 separate buttons

### Decision 5: Separate Date Fields
- `publication_date`: When made public (stable for citations)
- `modification_date`: Last edited (transparency for changes)
- Both display in citation section

---

## 📊 Project Metrics

| Metric | Value |
|--------|-------|
| Total Phases | 5 |
| Total Hours | 19 |
| Cost | CHF 2'090 |
| Test Cases | 8 |
| Files Modified | 8 |
| New Database Fields | 2 |
| Database Migration | 1 |
| Languages | 3 (Django, JavaScript, CSS) |

---

## 🎯 Success Criteria

**Project Complete When**:
- ✅ All 5 phases implemented
- ✅ All test cases pass (Phase 5)
- ✅ Manual testing checklist 100% complete
- ✅ Browser compatibility verified (Chrome, Firefox)
- ✅ Screenshots documented
- ✅ Database migration runs successfully
- ✅ Ready for production deployment
- ✅ Client approval received

---

## 📝 Implementation Notes

### For Developers

1. **Code Style**: Follow existing patterns in codebase
2. **Comments**: Add comments explaining new logic
3. **Backwards Compatibility**: No breaking changes
4. **Testing**: Run tests after each phase
5. **Documentation**: Update inline code comments

### For QA

1. **Test URL**: Always use `/fiches/trans/1080/` for primary testing
2. **Browser Dev Tools**: Check console for JS errors
3. **SessionStorage**: Verify checkbox state persistence
4. **Mobile**: Test at 375px viewport
5. **Accessibility**: Tab/Enter should work for all interactions

### For Client

1. **Screenshots**: You'll get before/after screenshots each phase
2. **Testing**: Can test on staging before production
3. **Feedback**: We'll implement requested changes
4. **Timeline**: 1 week from start to production ready
5. **Support**: Available for questions during implementation

---

## 🔐 Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Browser issues | Phase 5 testing covers Chrome/Firefox |
| Performance regression | Minimal changes, no new libraries |
| Data loss | Database backup before migration |
| User confusion | Clear visual design, matches reference |
| Code conflicts | Feature branch with regular merges |

---

## 📞 Support & Questions

All implementation details are in the documentation files. If you have questions:

1. **Check the relevant phase documentation** (.github/agents/)
2. **Look at the MASTER-PLAN.md** for overview
3. **Ask specific questions** about business logic or design

---

## ✨ What You're Getting

### Deliverables
1. ✅ Refactored UI matching client requirements
2. ✅ Automated test suite (8 tests)
3. ✅ Database migration for date fields
4. ✅ Updated admin interface
5. ✅ Complete documentation
6. ✅ Screenshots for approval

### Timeline
1 week from implementation start to production ready

### Quality
- Browser tested (Chrome, Firefox)
- Mobile responsive
- Keyboard accessible
- No console errors
- Full test coverage

---

## 🎓 How to Use This Documentation

```
START HERE
    ↓
Read MASTER-PLAN.md (overview)
    ↓
Read PHASE-1-DEAD-CODE-ANALYSIS.md (already done)
    ↓
Review PHASE-2-REFACTOR-NAV-BAR.md
    → [ ] Approve design → Start implementation
    ↓
Review PHASE-3-MODE-CONDITIONAL-LOGIC.md
    → [ ] Approve logic → Start implementation
    ↓
Review PHASE-4-UPDATE-DATE-FIELDS.md
    → [ ] Approve model → Start implementation
    ↓
Review PHASE-5-VISUAL-TESTING.md
    → [ ] Approve tests → Start testing
    ↓
ALL COMPLETE ✅
```

---

## 🚀 Ready to Start?

**All documentation is complete!** 

Next action: **Provide approval/feedback** on the 5 phases, then implementation can begin.

Each phase has:
- ✅ Detailed requirements
- ✅ File list to modify
- ✅ Implementation code snippets
- ✅ Testing instructions
- ✅ Success criteria

**Estimated Implementation Time**: 19 hours  
**Estimated Timeline**: 1 week (with reviews)

---

**Last Updated**: February 2, 2026  
**Documentation Status**: ✅ COMPLETE AND READY FOR REVIEW

See `.github/agents/` for all phase documentation.
