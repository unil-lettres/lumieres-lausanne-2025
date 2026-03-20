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

# Phase 4: Update Date Model Fields

**Estimated Time**: 4 hours  
**Status**: Design Phase (Ready for Implementation after Phase 3)  
**Objective**: Add dual date fields for transcriptions: `publication_date` (when made public) and `modification_date` (last edited)

---

## Business Context

Current Issue:
- Single `modified_date` field doesn't distinguish between:
  - **When transcription was first published/made public** (stability for citations)
  - **When transcription was last edited** (transparency for changes)

Client Requirement:
- During migration from old DB → preserve original publication date
- New transcriptions → auto-set publication date when "public access" enabled
- Both dates displayed in "Citer comme" section

---

## Database Schema Changes

### Current State

**Model**: `app/fiches/models/Transcription`

```python
# Existing (no changes needed):
modified_date = models.DateTimeField(auto_now=True)  # Django auto-updates on save
created_date = models.DateTimeField(auto_now_add=True)  # Set once at creation

# Issue: Only one "modified" timestamp, unclear publication intent
```

### Target State

```python
# New fields to add:
publication_date = models.DateField(
    verbose_name=_("Date de publication"),
    blank=True,
    null=True,
    help_text=_("Date de la première mise en ligne publique (JJ.MM.AAAA)")
)

modification_date = models.DateField(
    verbose_name=_("Date de dernière modification"),
    blank=True,
    null=True,
    help_text=_("Date de la dernière modification du contenu (JJ.MM.AAAA)")
)

# Keep existing:
modified_date = models.DateTimeField(auto_now=True)  # Still updated automatically
created_date = models.DateTimeField(auto_now_add=True)
```

**Differences**:
- `publication_date`: **DateField** (day precision, not time), set once
- `modification_date`: **DateField** (day precision, updated manually or by admin action)
- `modified_date`: **DateTimeField** (hour precision, auto-updated) - kept for backwards compatibility

---

## Implementation

### 1. Create Database Migration

**File**: `app/fiches/migrations/XXXX_add_publication_modification_dates.py`

**Command to generate**:
```bash
python manage.py makemigrations fiches --name add_publication_modification_dates
```

**Generated migration content** (example):
```python
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('fiches', 'XXXX_previous_migration'),  # Latest migration number
    ]

    operations = [
        # Add new fields
        migrations.AddField(
            model_name='transcription',
            name='publication_date',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Date de publication',
                help_text='Date de la première mise en ligne publique (JJ.MM.AAAA)'
            ),
        ),
        
        migrations.AddField(
            model_name='transcription',
            name='modification_date',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Date de dernière modification',
                help_text='Date de la dernière modification du contenu (JJ.MM.AAAA)'
            ),
        ),
        
        # Data migration: Copy existing modified_date.date() to publication_date for all public transcriptions
        migrations.RunPython(
            code=populate_publication_dates,
            reverse_code=migrations.RunPython.noop,  # No reverse needed
        ),
    ]

# Helper function for data migration
def populate_publication_dates(apps, schema_editor):
    """
    For all existing transcriptions:
    - If access_public=True: set publication_date to current modified_date.date()
    - If access_public=False: leave publication_date NULL
    """
    Transcription = apps.get_model('fiches', 'Transcription')
    
    for trans in Transcription.objects.filter(access_public=True):
        trans.publication_date = trans.modified_date.date()
        trans.modification_date = trans.modified_date.date()
        trans.save(update_fields=['publication_date', 'modification_date'])
    
    print(f"✓ Populated publication_date for {Transcription.objects.filter(access_public=True).count()} public transcriptions")
```

### 2. Update Model Definition

**File**: `app/fiches/models/__init__.py` (or transcription.py)

**Add fields** after existing date fields:
```python
class Transcription(models.Model):
    # ... existing fields ...
    
    # Existing (keep):
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Created"))
    modified_date = models.DateTimeField(auto_now=True, verbose_name=_("Modified"))
    
    # NEW:
    publication_date = models.DateField(
        verbose_name=_("Date de publication"),
        blank=True,
        null=True,
        help_text=_("Date de la première mise en ligne publique (au format JJ.MM.AAAA)")
    )
    
    modification_date = models.DateField(
        verbose_name=_("Date de dernière modification"),
        blank=True,
        null=True,
        help_text=_("Date de la dernière modification du contenu (au format JJ.MM.AAAA). "
                    "Laissez vide pour utiliser la date actuelle lors de la sauvegarde.")
    )
    
    class Meta:
        # ... existing ...
        indexes = [
            # ... existing ...
            models.Index(fields=['publication_date']),
            models.Index(fields=['modification_date']),
        ]
    
    def __str__(self):
        # ... existing ...
        pass
    
    # NEW: Override save() to auto-set modification_date if not provided
    def save(self, *args, **kwargs):
        # If modification_date not set, use today's date
        if not self.modification_date:
            self.modification_date = timezone.now().date()
        
        # If being published for first time, set publication_date
        if self.access_public and not self.publication_date:
            self.publication_date = timezone.now().date()
        
        super().save(*args, **kwargs)
```

**Imports needed**:
```python
from django.utils import timezone
```

### 3. Update Admin Form

**File**: `app/fiches/admin.py`

**Add fields** to Transcription admin:
```python
class TranscriptionAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('General'), {
            'fields': ('manuscript_b', 'status', 'scope', 'author', 'author2', 'reviewers')
        }),
        (_('Content'), {
            'fields': ('text', 'envelope')
        }),
        (_('Access'), {
            'fields': ('access_public', 'access_groups', 'access_private')
        }),
        (_('Dates'), {  # NEW FIELDSET
            'fields': ('publication_date', 'modification_date', 'created_date', 'modified_date'),
            'description': _('Publication date is automatically set when access is made public. '
                             'Modification date should be updated when content is edited.')
        }),
        (_('Facsimile'), {
            'fields': ('facsimile_iiif_url', 'facsimile_start_canvas')
        }),
    )
    
    # Make read-only fields that shouldn't be manually edited
    readonly_fields = ('created_date', 'modified_date')
    
    # Allow editing of new date fields
    # fields shown: publication_date, modification_date
```

### 4. Update Template Display

**File**: `app/fiches/templates/fiches/display/transcription.html`

**Current "Citer comme" section** (around line 267):
```django-html
<div class="field_label">Citer comme</div>
<div class="field_value">
    {% spaceless %}
    <!-- ... existing citation logic ... -->
    {% endwith %}
    Selon la transcription établie par {{ trans.cite_authors }}Lumières.Lausanne (Université de Lausanne),
    url:&nbsp;<a href="{% url 'transcription-display' trans.id %}">
    <!-- ... URL display ... -->
    </a>,
    version du {{ last_activity.date|date:"d.m.Y" }}.
    {% endspaceless %}
</div>
```

**Update to show both dates** (NEW):
```django-html
<div class="field_label">Citer comme</div>
<div class="field_value">
    {% spaceless %}
    <!-- ... existing citation logic (no change) ... -->
    {% endwith %}
    Selon la transcription établie par {{ trans.cite_authors }}Lumières.Lausanne (Université de Lausanne),
    
    <!-- NEW: Show publication and modification dates -->
    {% if trans.publication_date %}
    <br/>Date de mise en ligne:&nbsp;<strong>{{ trans.publication_date|date:"d.m.Y" }}</strong>
    {% endif %}
    
    {% if trans.modification_date %}
    <br/>Version:&nbsp;<strong>{{ trans.modification_date|date:"d.m.Y" }}</strong>
    {% endif %}
    
    url:&nbsp;<a href="{% url 'transcription-display' trans.id %}">
    <!-- ... URL display ... -->
    </a>,
    version du {{ last_activity.date|date:"d.m.Y" }}.
    
    {% endspaceless %}
</div>
```

### 5. Update Edit Form (Optional)

**File**: `app/fiches/forms.py`

If there's a custom edit form for transcriptions:
```python
class TranscriptionEditForm(forms.ModelForm):
    class Meta:
        model = Transcription
        fields = [
            # ... existing fields ...
            'publication_date',
            'modification_date',
            # ... rest ...
        ]
    
    publication_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': 'JJ.MM.AAAA'
        }),
        help_text=_('Auto-set when access is made public. Can be manually edited if needed.')
    )
    
    modification_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': 'JJ.MM.AAAA'
        }),
        help_text=_('Update when content is edited. Auto-fills current date if left blank.')
    )
```

---

## Files to Modify

| File | Type | Changes | Complexity |
|------|------|---------|------------|
| `app/fiches/migrations/XXXX_add_publication_modification_dates.py` | Migration | CREATE (new file) | Medium |
| `app/fiches/models/__init__.py` | Python | Add 2 fields + save() override | Low |
| `app/fiches/admin.py` | Python | Add fields to admin fieldsets | Low |
| `app/fiches/templates/fiches/display/transcription.html` | Template | Update cite section | Low |
| `app/fiches/forms.py` | Python | Add form fields (if edit form exists) | Optional |

---

## Database Migration Steps

### Before Running

```bash
# Check current database state
python manage.py showmigrations fiches

# Check model definition
grep -n "modified_date\|created_date" app/fiches/models/__init__.py
```

### Generate Migration

```bash
# Django will detect new fields
python manage.py makemigrations fiches

# Review migration file created
cat app/fiches/migrations/0NNN_add_publication_modification_dates.py
```

### Apply Migration

```bash
# First: test on dev/staging database
python manage.py migrate fiches --database=staging  # If multi-DB setup

# Then: apply to main database
python manage.py migrate fiches

# Verify
python manage.py showmigrations fiches | grep add_publication_modification_dates
```

### Verify Population

```bash
# Check SQL to verify dates populated
python manage.py dbshell

SELECT id, access_public, publication_date, modification_date, modified_date FROM fiches_transcription LIMIT 5;
```

---

## Backfill Data Strategy

### Scenario 1: Preserve Exact Publication Dates (Recommended)

**For existing public transcriptions**:
- Use `modified_date.date()` as proxy for original publication date
- Assumes current `modified_date` reflects when transcription became public

**SQL for manual backfill** (if needed):
```sql
UPDATE fiches_transcription 
SET publication_date = DATE(modified_date)
WHERE access_public = true AND publication_date IS NULL;

UPDATE fiches_transcription 
SET modification_date = DATE(modified_date)
WHERE modification_date IS NULL;
```

### Scenario 2: Require Manual Review (More Conservative)

**For existing transcriptions**:
- Leave `publication_date` NULL for manual review
- Admin staff reviews and fills in actual publication dates from records/logs
- More time-consuming but more accurate

---

## Testing

### Unit Tests

**File**: `app/fiches/tests/test_transcription_dates.py` (new)

```python
from django.test import TestCase
from django.utils import timezone
from datetime import date
from fiches.models import Transcription
from django.contrib.auth.models import User

class TranscriptionDateTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser')
        self.trans = Transcription.objects.create(
            title='Test Trans',
            author=self.user,
            access_public=False
        )
    
    def test_publication_date_set_on_make_public(self):
        """When transcription becomes public, publication_date should be set"""
        self.trans.access_public = True
        self.trans.save()
        
        self.assertIsNotNone(self.trans.publication_date)
        self.assertEqual(self.trans.publication_date, date.today())
    
    def test_modification_date_set_on_save_if_empty(self):
        """If modification_date is empty, should be set to today on save"""
        trans = Transcription.objects.create(
            title='Test Trans 2',
            author=self.user,
            modification_date=None
        )
        
        trans.save()
        
        self.assertIsNotNone(trans.modification_date)
        self.assertEqual(trans.modification_date, date.today())
    
    def test_publication_date_not_overwritten(self):
        """Once publication_date is set, it should not change"""
        old_date = date(2024, 1, 1)
        self.trans.access_public = True
        self.trans.publication_date = old_date
        self.trans.save()
        
        self.assertEqual(self.trans.publication_date, old_date)
```

### Manual Testing

```bash
# Test 1: Create new transcription, make public
1. Go to /admin/fiches/transcription/add/
2. Fill in fields
3. Check "Access public"
4. Save
5. ✓ Verify: publication_date = today, modification_date = today

# Test 2: Edit existing public transcription
1. Go to /admin/fiches/transcription/<id>/change/
2. Edit text field
3. Update modification_date if needed
4. Save
5. ✓ Verify: modification_date updated, publication_date unchanged

# Test 3: View transcription page
1. Go to /fiches/trans/<id>/
2. Scroll to "Citer comme" section
3. ✓ Verify: Both dates displayed
   - "Date de mise en ligne: dd.mm.yyyy"
   - "Version: dd.mm.yyyy"
```

---

## Browser Testing

### Test Public Transcription Display

**URL**: `/fiches/trans/1080/` (should have publication_date set)

```
Expected in "Citer comme" section:
Selon la transcription établie par Lumières.Lausanne...

Date de mise en ligne: 02.02.2026
Version: 02.02.2026

url: https://...
```

---

## Admin Interface

### Changes Visible

1. **Transcription edit/add page**:
   - New "Dates" fieldset above "Facsimile"
   - Shows: publication_date, modification_date (editable)
   - Shows: created_date, modified_date (read-only)

2. **List view** (optional enhancement):
   - Could add columns for publication_date, modification_date
   - Would help admins see at a glance

---

## Validation Checklist

### Migration
- [ ] Migration file created successfully
- [ ] `makemigrations` detects no model changes after migration applied
- [ ] No SQL errors during migration
- [ ] All existing public transcriptions have publication_date set

### Model
- [ ] Model saves correctly with new fields
- [ ] publication_date not overwritten on subsequent saves
- [ ] modification_date auto-fills if not provided
- [ ] Admin can manually edit both dates

### Template
- [ ] Dates display in "Citer comme" section
- [ ] Format correct: "dd.mm.yyyy"
- [ ] Only shows if date is not NULL
- [ ] No template errors in Django logs

### Admin
- [ ] New fieldset visible in admin form
- [ ] Can create transcription with dates
- [ ] Can edit dates manually
- [ ] Read-only fields display correctly

---

## Time Breakdown

| Task | Hours | Notes |
|------|-------|-------|
| Model fields + save() | 0.5h | Add field defs + override |
| Migration + backfill | 1.0h | Create + data population |
| Admin integration | 0.5h | Add fieldsets, display |
| Template updates | 0.5h | "Citer comme" section |
| Form updates (optional) | 0.5h | If custom form exists |
| Testing + validation | 1.0h | Unit + manual tests |
| **Total** | **4.0h** | As estimated |

---

## Dependencies

**Blocks On**:
- Phase 3 completion (optional, not required)
- Database writable (for migration)

**Blocks**:
- Phase 5: Deployment & testing

---

## Post-Deployment

### For Staging/Production Deployment

```bash
# 1. Backup database before migration
pg_dump -U postgres dbname > backup_pre_dates_migration.sql

# 2. Apply migration
python manage.py migrate fiches

# 3. Verify data
python manage.py shell
>>> from fiches.models import Transcription
>>> Transcription.objects.filter(publication_date__isnull=False).count()
# Should show number of public transcriptions

# 4. Test front-end
# Visit /fiches/trans/<public_id>/ and verify dates display
```

---

**Ready for Review**: ✅  
**PM Decisions Needed**:
- [ ] Backfill Strategy: Use existing modified_date or manual review?
- [ ] Date Display Format: "dd.mm.yyyy" acceptable?
- [ ] Should admin form require these dates, or optional?
