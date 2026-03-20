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

# Implementation Coordination Checklist

**Project**: Lumières Lausanne Facsimile Viewer - Phase 2 Enhancements  
**Start Date**: [To be scheduled]  
**Expected Completion**: +19 working hours

---

## 📋 PRE-IMPLEMENTATION CHECKLIST

### Phase 1: Code Analysis ✅ COMPLETE

- [x] Dead code identified and documented
- [x] Unused features catalogued (rotate, brightness, contrast, fullscreen)
- [x] Cleanup strategy decided (keep code, don't expose)
- [x] Decision documented

**Status**: Ready → Phase 2

---

### Pre-Phase-2 Requirements

- [ ] **User Approval**: Read MASTER-PLAN.md + provide feedback
- [ ] **Code Review Setup**: Assign reviewer for PRs
- [ ] **QA Assigned**: Designate tester for Phase 5
- [ ] **Server Ready**: Django dev server available on localhost:8000
- [ ] **Branch Created**: `feat/facsimile-viewer-phase2` from dev

---

## 🔧 IMPLEMENTATION CHECKLIST

### PHASE 2: Refactor Navigation Bar (4 hours)

**Prerequisites**:
- [ ] Branch created and checked out
- [ ] Phase 2 documentation reviewed
- [ ] Design approved

**Implementation**:
- [ ] Step 1: Modify template HTML
  - [ ] Remove sync button wrapper
  - [ ] Add options dropdown structure
  - [ ] Verify markup valid

- [ ] Step 2: Update CSS styling
  - [ ] Single-row button layout
  - [ ] Dropdown menu styling
  - [ ] Responsive adjustments
  - [ ] No visual regressions

- [ ] Step 3: Add JavaScript logic
  - [ ] Options menu toggle (open/close)
  - [ ] Click outside to close
  - [ ] Checkbox state persistence
  - [ ] Event listener cleanup

**Testing Before Review**:
- [ ] No console errors on localhost
- [ ] Visual matches target design
- [ ] Options menu opens/closes
- [ ] Checkboxes persist state

**Code Review**:
- [ ] Reviewer approves changes
- [ ] Screenshots provided to PM
- [ ] Feedback incorporated

**Status After Complete**: Ready → Phase 3

---

### PHASE 3: Mode Conditional Logic (3 hours)

**Prerequisites**:
- [ ] Phase 2 merged into branch
- [ ] Phase 3 documentation reviewed
- [ ] Logic rules approved

**Implementation**:
- [ ] Step 1: Add data attributes to template
  - [ ] `data-has-facsimile` attribute
  - [ ] `data-has-transcription` attribute
  - [ ] Verify template renders correctly

- [ ] Step 2: Add CSS conditional states
  - [ ] Disabled button styling
  - [ ] Opacity/cursor changes
  - [ ] No active state on disabled

- [ ] Step 3: Add JavaScript initialization
  - [ ] `initializeModeAvailability()` function
  - [ ] Button disable/enable logic
  - [ ] Console logging for debug

- [ ] Step 4: Update options per mode
  - [ ] `updateOptionsMenuForMode()` function
  - [ ] Different options per mode
  - [ ] Dynamic menu content

**Testing Before Review**:
- [ ] Test URL: `/fiches/trans/1080/` (both text + facsimilé)
  - [ ] All buttons enabled
  - [ ] Split-view active by default
  - [ ] Options visible per mode

- [ ] Find test URL for text-only (no facsimilé)
  - [ ] Text button only enabled
  - [ ] Text-specific options shown

- [ ] No console errors
- [ ] Modes switch smoothly
- [ ] Mode defaults correct

**Code Review**:
- [ ] Reviewer approves changes
- [ ] Screenshots provided
- [ ] Feedback incorporated

**Status After Complete**: Ready → Phase 4 & 5

---

### PHASE 4: Update Date Model Fields (4 hours)

**Prerequisites**:
- [ ] Phase 2 & 3 merged (or at least committed)
- [ ] Phase 4 documentation reviewed
- [ ] Data model decisions made

**Implementation**:
- [ ] Step 1: Update Django model
  - [ ] Add `publication_date` field (DateField, optional)
  - [ ] Add `modification_date` field (DateField, optional)
  - [ ] Add save() override for auto-population
  - [ ] No syntax errors

- [ ] Step 2: Create database migration
  - [ ] Run `python manage.py makemigrations`
  - [ ] Review migration file
  - [ ] Add data backfill logic

- [ ] Step 3: Apply migration locally
  - [ ] Run `python manage.py migrate fiches`
  - [ ] Verify no errors
  - [ ] Check database (dates populated)

- [ ] Step 4: Update admin interface
  - [ ] Add "Dates" fieldset
  - [ ] publication_date editable
  - [ ] modification_date editable
  - [ ] created_date, modified_date read-only

- [ ] Step 5: Update template display
  - [ ] Citation section updated
  - [ ] Dates display: "d.m.Y" format
  - [ ] Only show if not NULL
  - [ ] No template errors

**Testing Before Review**:
- [ ] Test URL: `/fiches/trans/1080/`
  - [ ] Dates visible in "Citer comme" section
  - [ ] Format correct

- [ ] Admin interface:
  - [ ] Can create transcription with dates
  - [ ] Can edit dates
  - [ ] Dates auto-save correctly

- [ ] Database:
  - [ ] Migration reversible (if needed)
  - [ ] No data loss

**Code Review**:
- [ ] Reviewer approves schema changes
- [ ] DBA reviews migration
- [ ] Screenshots of admin/display provided

**Status After Complete**: Ready → Phase 5

---

### PHASE 5: Visual Testing & Validation (3 hours)

**Prerequisites**:
- [ ] Phases 2-4 complete
- [ ] All code merged
- [ ] Phase 5 documentation reviewed
- [ ] Playwright installed (`pip install pytest-playwright`)

**Implementation**:
- [ ] Step 1: Write Playwright tests
  - [ ] Create `test_facsimile_viewer_e2e.py`
  - [ ] 8 test cases implemented
  - [ ] Tests well-commented

- [ ] Step 2: Run automated tests
  - [ ] Install browser binaries: `playwright install`
  - [ ] Run: `pytest app/fiches/tests/test_facsimile_viewer_e2e.py -v`
  - [ ] All tests pass
  - [ ] Screenshots captured

- [ ] Step 3: Manual testing workflow
  - [ ] Follow Phase 5 manual test checklist
  - [ ] Test all 9 scenarios
  - [ ] Document results

- [ ] Step 4: Browser compatibility
  - [ ] Chrome (latest) ✅
  - [ ] Firefox (latest) ✅
  - [ ] Safari (optional) ⏸

**Testing Scenarios**:
- [ ] Test 1: Both text + facsimilé
  - [ ] URL: `/fiches/trans/1080/`
  - [ ] Expected: All buttons enabled

- [ ] Test 2: Text only
  - [ ] URL: Find one without facsimilé
  - [ ] Expected: Text button only

- [ ] Test 3: Mobile responsive
  - [ ] Viewport: 375×812px
  - [ ] Expected: Layout adapts

- [ ] Test 4: Keyboard navigation
  - [ ] Tab through buttons
  - [ ] Enter to select
  - [ ] All functional

- [ ] Test 5: Date display
  - [ ] Citation section
  - [ ] Format correct

- [ ] Test 6: No console errors
  - [ ] DevTools Console
  - [ ] All errors fixed

**Deliverables**:
- [ ] Test results document: `TEST-RESULTS-2026-02-02.md`
- [ ] Screenshots (all test scenarios)
- [ ] Playwright test file in repo

**Status After Complete**: Ready → DEPLOYMENT ✅

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment Verification

- [ ] All phases complete
- [ ] Phase 5 tests pass
- [ ] No console errors
- [ ] Database migration tested
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Screenshots ready
- [ ] Client approval obtained

### Staging Deployment

- [ ] Create release branch: `release/v2026.02.02-facsimile-phase2`
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Client testing on staging
- [ ] Client approval

### Production Deployment

- [ ] Merge to master
- [ ] Create git tag: `v2026.02.02`
- [ ] Deploy to production
- [ ] Database migration (if applicable)
- [ ] Monitor logs for errors
- [ ] Verify on production
- [ ] Notify client of deployment

---

## 📊 Status Tracking

### Approval Gates

```
Phase 1 ✅
    ↓
[ ] Phase 2 Code Review
    ↓
[ ] Phase 3 Code Review
    ↓
[ ] Phase 4 Code Review + QA
    ↓
[ ] Phase 5 Test Results
    ↓
[ ] Final Approval
    ↓
DEPLOYMENT APPROVED ✅
```

### Communication Points

- [ ] **Before Phase 2**: Design approval
- [ ] **After Phase 2**: Screenshot + demo
- [ ] **After Phase 3**: Logic approval
- [ ] **After Phase 4**: Data migration verification
- [ ] **After Phase 5**: Test results + release notes
- [ ] **Pre-Deployment**: Go/no-go decision
- [ ] **Post-Deployment**: Confirmation to client

---

## 📝 Documentation Checklist

- [x] PHASE-1-DEAD-CODE-ANALYSIS.md ✅
- [x] PHASE-2-REFACTOR-NAV-BAR.md ✅
- [x] PHASE-3-MODE-CONDITIONAL-LOGIC.md ✅
- [x] PHASE-4-UPDATE-DATE-FIELDS.md ✅
- [x] PHASE-5-VISUAL-TESTING.md ✅
- [x] MASTER-PLAN.md ✅
- [x] README.md ✅

- [ ] Implementation checklist (this file)
- [ ] Release notes (to create during deployment)
- [ ] Client UAT guide (to create before staging)

---

## 🎯 Success Criteria

**Phase 2 ✅**: Navigation bar refactored
- [ ] 4 buttons in single row
- [ ] Options dropdown works
- [ ] No visual regressions

**Phase 3 ✅**: Mode conditional logic
- [ ] Buttons disable correctly
- [ ] Options dynamic per mode
- [ ] All scenarios tested

**Phase 4 ✅**: Date fields added
- [ ] Migration runs
- [ ] Dates display
- [ ] Admin form works

**Phase 5 ✅**: Testing complete
- [ ] All Playwright tests pass
- [ ] Manual tests 100%
- [ ] Browser compatible

**DEPLOYMENT ✅**: Ready for production
- [ ] No outstanding issues
- [ ] Client approved
- [ ] Deployment plan ready

---

## 📞 Escalation Path

| Issue | Action | Owner | Escalate To |
|-------|--------|-------|-------------|
| Blocking bug | Create issue, stop work | Dev | Tech Lead |
| Design question | Create discussion | Dev | PM |
| Migration failure | Rollback, investigate | DBA | Tech Lead |
| Client feedback | Create task | PM | Dev Team |
| Performance issue | Profile, optimize | Dev | Tech Lead |

---

## 📋 Quick Reference

### Test URLs
- Primary: `http://localhost:8000/fiches/trans/1080/` (has facsimilé)
- Backup: Find transcription without facsimilé for text-only test

### Key Files
- Template: `app/fiches/templates/fiches/display/transcription.html`
- CSS Layout: `app/fiches/static/fiches/css/transcription-layout.css`
- JS: `app/fiches/static/fiches/js/transcription-sync.js`
- Model: `app/fiches/models/__init__.py`
- Admin: `app/fiches/admin.py`

### Commands
```bash
# Dev server
python manage.py runserver 0.0.0.0:8000

# Migrations
python manage.py makemigrations
python manage.py migrate

# Tests
pytest app/fiches/tests/test_facsimile_viewer_e2e.py -v

# Admin
python manage.py createsuperuser (if needed)
http://localhost:8000/admin/
```

---

## 📅 Timeline

| Date | Phase | Status | Owner |
|------|-------|--------|-------|
| 2026-02-02 | 1 Analysis | ✅ Complete | [Name] |
| 2026-02-03 | 2 Nav Bar | [ ] | [Name] |
| 2026-02-04 | 3 Logic + Review | [ ] | [Name] |
| 2026-02-05 | 4 Dates + QA | [ ] | [Name] |
| 2026-02-06 | 5 Testing | [ ] | [Name] |
| 2026-02-07 | Staging Deploy | [ ] | [Name] |
| 2026-02-10 | Prod Deploy | [ ] | [Name] |

---

## 🎓 Training/Handoff

### For New Team Members
1. Read README.md
2. Read MASTER-PLAN.md
3. Read relevant phase documentation
4. Review test results
5. Pair program with original developer

### For Support Team
1. Documentation location: `.github/agents/`
2. Test URLs documented
3. Known issues: None (see TEST-RESULTS.md)
4. Escalation: See escalation path above

---

**Last Updated**: February 2, 2026  
**Status**: ✅ READY FOR IMPLEMENTATION  
**Next**: Schedule implementation kickoff

**Sign-off**:
- [ ] Tech Lead: ___________________
- [ ] PM: ___________________
- [ ] QA: ___________________
- [ ] Client: ___________________
