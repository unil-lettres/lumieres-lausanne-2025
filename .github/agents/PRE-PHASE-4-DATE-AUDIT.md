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

# 📊 PRE-IMPLEMENTATION AUDIT: Date Fields Analysis

**Date**: February 2, 2026  
**Purpose**: Analyze current date field usage before implementing new date model fields  
**Status**: ⏳ AWAITING YOUR REVIEW

---

## 🔍 EXECUTIVE SUMMARY

**Finding**: The Transcription model **currently has NO dedicated date fields**. 

- ❌ No `created_date` field
- ❌ No `modified_date` field  
- ❌ No `publication_date` field
- ✅ But: The parent class `ACModel` has `access_public` boolean (not a date)

**Source of "Last Modified" info**: 
- Stored in separate `ActivityLog` table
- Displayed as "Dernière modification" in template from `last_activity.date`

**Implication**: 
- We're NOT changing existing date behavior, we're **ADDING new tracking**
- Safe migration: No existing date fields to migrate
- Frontend currently relies on ActivityLog for modification times

---

## 📋 CURRENT STATE: Model Analysis

### Model Hierarchy

```
ACModel (abstract base class)
  ├─ access_owner (ForeignKey to User)
  ├─ access_public (BooleanField) ← Only date-related: publication toggle
  └─ access_groups (ManyToManyField)

Transcription (inherits from ACModel)
  ├─ manuscript (ForeignKey)
  ├─ manuscript_b (ForeignKey to Biblio)
  ├─ author (ForeignKey to User)
  ├─ author2 (ForeignKey to User)
  ├─ status (IntegerField: 0=En cours, 1=Fini)
  ├─ scope (IntegerField: 0=Intégrale, 1=Extrait)
  ├─ text (RichTextField)
  ├─ envelope (RichTextField)
  ├─ facsimile_iiif_url (URLField) ← NEW in Phase 4
  ├─ facsimile_start_canvas (PositiveIntegerField) ← NEW in Phase 4
  ├─ access_private (BooleanField)
  
  ❌ NO date fields currently
```

### Files Involved

```
app/fiches/models/documents/document.py (839 lines)
  └─ class Transcription (line 734) - NO DATE FIELDS

app/fiches/models/contributions/ac_model.py (70 lines)
  └─ class ACModel - NO DATE FIELDS

app/fiches/admin.py (587 lines)
  └─ class TranscriptionAdmin (line 519)
     ├─ list_display: ("id", "sorting")
     ├─ list_filter: ("status",)
     └─ NO DATE FIELDS CONFIGURED

app/fiches/forms.py
  └─ NO TranscriptionForm with date fields found
     (Forms for Biblio exist with date handling, but not Transcription)

app/fiches/templates/fiches/display/transcription.html
  └─ Uses: last_activity.date from view context (NOT from model)
```

---

## 🗄️ DATABASE: How Dates Are Currently Tracked

### Current Date Tracking Mechanism

**Where modification info comes from**:

1. **ActivityLog table** (separate table for audit trail)
   - Tracks all changes to any model
   - Stored in: `app/fiches/models/logging/activity_log.py` (if exists)
   - Contains: object_id, model_name, date, user, action

2. **Template Usage** (transcription.html):
   ```django-html
   {{ last_activity.date|date:"d M. Y - H:i" }} ({{ last_activity.user.username }})
   ```
   This is passed from view context, not from Transcription model directly.

3. **No Publication Date Tracking**:
   - When `access_public` changes from False → True, NO timestamp is recorded
   - Only the ActivityLog entry shows something changed
   - No audit trail specific to publication action

### Data Flow Diagram

```
USER CREATES TRANSCRIPTION
        ↓
Transcription model saved
(no dates recorded in model)
        ↓
ActivityLog entry created
        ↓
TEMPLATE DISPLAYS:
  "Dernière modification: {{ last_activity.date }}"
  "Transcrit par: {{ trans.author }}"
  (No publication date shown)

USER MAKES PUBLIC (access_public = True)
        ↓
Transcription.access_public = True
        ↓
ActivityLog entry created (generic)
        ↓
NO PUBLICATION DATE RECORDED ← This is the gap we're fixing!
```

---

## 🎯 PHASE 4 CHANGES: What We're Adding

### New Fields to Add

```python
# app/fiches/models/documents/document.py
class Transcription(ACModel):
    # ... existing fields ...
    
    # NEW FIELDS:
    publication_date = models.DateField(
        verbose_name=_("Date de publication"),
        blank=True,
        null=True,
        help_text=_("Date de la première mise en ligne publique")
    )
    
    modification_date = models.DateField(
        verbose_name=_("Date de dernière modification"),
        blank=True,
        null=True,
        help_text=_("Date de la dernière modification du contenu")
    )
    
    # Add custom save() to auto-populate
    def save(self, *args, **kwargs):
        # If being published for first time
        if self.access_public and not self.publication_date:
            self.publication_date = timezone.now().date()
        
        # If modification_date not set, use today
        if not self.modification_date:
            self.modification_date = timezone.now().date()
        
        super().save(*args, **kwargs)
```

---

## 📊 DATA MIGRATION STRATEGY (NO RISK)

### Current Data State

**All existing Transcription records**:
- ✅ Have `access_public` boolean (True or False)
- ✅ Have entries in ActivityLog table (creation + modifications)
- ❌ Have NO publication_date field (will be NULL after column creation)
- ❌ Have NO modification_date field (will be NULL after column creation)

### Migration Plan

**Step 1**: Create columns (Django migration)
```python
migrations.AddField(
    model_name='transcription',
    name='publication_date',
    field=models.DateField(blank=True, null=True)
),
migrations.AddField(
    model_name='transcription',
    name='modification_date',
    field=models.DateField(blank=True, null=True)
),
```

**Step 2**: Backfill data (Python data migration)
```python
def backfill_dates(apps, schema_editor):
    Transcription = apps.get_model('fiches', 'Transcription')
    ActivityLog = apps.get_model('fiches', 'ActivityLog')
    
    for trans in Transcription.objects.all():
        # Get first ActivityLog entry (creation)
        first_log = ActivityLog.objects.filter(
            object_id=trans.id,
            model_name='Transcription'
        ).order_by('date').first()
        
        # Get latest ActivityLog entry
        latest_log = ActivityLog.objects.filter(
            object_id=trans.id,
            model_name='Transcription'
        ).order_by('-date').first()
        
        if first_log and trans.access_public:
            # Set publication_date to first modification date if public
            trans.publication_date = first_log.date.date()
        
        if latest_log:
            # Set modification_date to latest change
            trans.modification_date = latest_log.date.date()
        
        trans.save(update_fields=['publication_date', 'modification_date'])
```

**Result After Migration**:
- All public transcriptions: publication_date = first creation/modification date
- All transcriptions: modification_date = latest activity date
- Private transcriptions: both dates NULL (as intended)

### Risk Assessment

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Data loss | None | Pure additive, no columns removed |
| Rollback needed | Low | Simple migration, reversible |
| Performance impact | None | Adding 2 date columns only |
| Data accuracy | Medium | Backfill uses ActivityLog (best available) |

---

## 🎨 FRONTEND: How Dates Will Be Displayed

### Current Display (transcription.html)

```django-html
<div class="field_label">Dernière modification</div>
<div class="field_value last">
    {{ last_activity.date|date:"d M. Y - H:i" }} 
    ({{ last_activity.user.username }})
</div>
```

### After Phase 4 (NEW Display)

```django-html
<div class="field_label">Citer comme</div>
<div class="field_value">
    ...existing citation...
    
    <!-- NEW: Publication dates -->
    {% if trans.publication_date %}
    <br/>Date de mise en ligne: <strong>{{ trans.publication_date|date:"d.m.Y" }}</strong>
    {% endif %}
    
    {% if trans.modification_date %}
    <br/>Version: <strong>{{ trans.modification_date|date:"d.m.Y" }}</strong>
    {% endif %}
    
    url: <a href="...">...</a>
    version du {{ last_activity.date|date:"d.m.Y" }}.
</div>
```

### Date Formats

| Field | Current Format | New Format | Type |
|-------|---|---|---|
| `last_activity.date` | `d M. Y - H:i` (e.g., "02 Feb. 2026 - 14:25") | ✓ Unchanged | DateTime |
| `publication_date` | New | `d.m.Y` (e.g., "02.02.2026") | Date |
| `modification_date` | New | `d.m.Y` (e.g., "02.02.2026") | Date |

---

## 👨‍💼 ADMIN INTERFACE: How Dates Will Be Edited

### Current Admin (transcription admin.py, line 519)

```python
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "sorting")
    list_filter = ("status",)
    # NO DATE FIELDS CONFIGURED
```

### After Phase 4 (IMPROVED Admin)

```python
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "sorting", "status", "publication_date", "modification_date")
    list_filter = ("status", "publication_date", "modification_date")
    
    fieldsets = (
        (_('General'), {
            'fields': ('manuscript_b', 'status', 'scope', 'author', 'author2')
        }),
        (_('Content'), {
            'fields': ('text', 'envelope')
        }),
        (_('Access'), {
            'fields': ('access_public', 'access_groups', 'access_private')
        }),
        (_('Dates'), {  # NEW FIELDSET
            'fields': ('publication_date', 'modification_date', 'created_date', 'modified_date'),
            'description': _('Publication date auto-set when access is made public.')
        }),
        (_('Facsimile'), {
            'fields': ('facsimile_iiif_url', 'facsimile_start_canvas')
        }),
    )
    
    readonly_fields = ('created_date', 'modified_date')
```

### Admin Behavior

| Action | Before | After |
|--------|--------|-------|
| Create transcription | No dates recorded | publication_date & modification_date auto-filled |
| Make public | No date recorded | publication_date auto-set to today |
| Edit content | ActivityLog only | modification_date auto-updated |
| Admin edit | Manual only | Can manually adjust dates if needed |

---

## 🔧 IMPLEMENTATION CHECKLIST

### Before Starting

- [ ] Backup production database
- [ ] Note current ActivityLog table structure
- [ ] Identify count of public vs private transcriptions
- [ ] Confirm no existing date field conflicts

### Phase 4 Implementation

- [ ] Add `publication_date` field to model
- [ ] Add `modification_date` field to model
- [ ] Add `save()` override for auto-population
- [ ] Generate Django migration
- [ ] Create data migration (backfill from ActivityLog)
- [ ] Update admin form + fieldsets
- [ ] Update template display
- [ ] Test locally
- [ ] QA review (dates sensible)
- [ ] Deploy migration

### Post-Implementation

- [ ] Verify dates populated correctly
- [ ] Spot-check 10 public transcriptions
- [ ] Confirm display format matches spec
- [ ] Admin can edit dates manually if needed
- [ ] ActivityLog still works (not replaced)

---

## ⚠️ CONSIDERATIONS & DECISIONS NEEDED

### Decision 1: Backfill Strategy
- **Option A** (Recommended): Use ActivityLog date as publication_date
  - Pro: Maintains historical accuracy
  - Con: Relies on ActivityLog existing + not being purged
  
- **Option B**: Use today's date for all existing records
  - Pro: Fresh slate for new system
  - Con: Loses publication history

**Recommendation**: **Option A** - use ActivityLog

### Decision 2: Privacy of Dates
- **Option A**: Show both dates to public
- **Option B**: Show dates only to owners
- **Option C**: Show publication date public, modification date to owners only

**Current Spec**: Show both in citation (public)
**Recommendation**: Keep public (client requirement for transparency)

### Decision 3: Allow Manual Override?
- **Option A**: Dates auto-set, not editable
- **Option B**: Dates auto-set, editable by admin
- **Option C**: Dates optional, must be manually set

**Recommendation**: **Option B** - auto-set but allow manual correction

---

## 📈 ESTIMATED IMPACT

### On Performance
- Adding 2 date columns: **Negligible** impact
- Index on publication_date: Could improve queries on "recent publications"

### On Storage
- Each date = 3 bytes (MySQL DATE type)
- For 10,000 transcriptions = ~60 KB additional storage

### On Code
- New lines: ~50 (model + save override)
- Migration complexity: Low (simple AddField + backfill)
- Template changes: ~10 lines

---

## 🎯 SUCCESS CRITERIA FOR PHASE 4

- [ ] Both new fields present in model
- [ ] Migration runs successfully (forward + backward)
- [ ] All public transcriptions have publication_date set
- [ ] All transcriptions have modification_date set or NULL
- [ ] Admin interface shows dates in new fieldset
- [ ] Template displays dates in citation section
- [ ] No console errors
- [ ] Dates display in correct format (dd.mm.yyyy)
- [ ] Manual date editing works in admin

---

## 🚀 NEXT STEPS (AWAITING YOUR REVIEW)

1. **Review this audit document**
2. **Approve or suggest changes** to:
   - Backfill strategy (ActivityLog-based)
   - Date format (dd.mm.yyyy)
   - Admin editability (manual override allowed)
   - Privacy level (public display)

3. **Confirm Phase 4 can proceed** with this approach

4. **Signal ready** when approved

---

## 📞 QUESTIONS FOR YOU

1. **Backfill**: Use ActivityLog creation date as publication_date? (Recommended)
2. **Format**: Display dates as "dd.mm.yyyy"? (French format)
3. **Editability**: Allow admin to manually override dates?
4. **Privacy**: Show modification_date to public in citations?
5. **Null handling**: Leave dates NULL for non-public transcriptions?

---

**Document Status**: ⏳ **AWAITING YOUR APPROVAL**  
**Blockers**: None identified  
**Risk Level**: LOW (additive changes, no existing data modified)

---

**Next Action**: Provide feedback/approval on this audit, then Phase 4 can proceed immediately.
