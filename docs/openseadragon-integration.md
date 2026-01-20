````markdown
<!--
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
-->

# OpenSeadragon IIIF Viewer Integration

> **Navigation**: [Home](index.md) > [Developer Documentation](index.md#developer-documentation) > OpenSeadragon Integration

## Overview

This document describes the integration of OpenSeadragon viewer for displaying IIIF facsimiles alongside transcriptions in the Lumières.Lausanne application.

**Related Documentation:**

- **[IIIF Facsimile Migration](iiif-facsimile-migration.md)** - Database migration and implementation details
- **[Facsimile Usage Guide](facsimile-usage-guide.md)** - User-facing documentation
- **[Administrator Guide](en/facsimile-admin-guide.md)** - Admin interface documentation

---


## Changes Made

### 1. Template Updates (`app/fiches/templates/fiches/display/transcription.html`)

#### CSS Additions
- **Two-column layout**: Added flexbox-based layout with transcription on the left and viewer panel on the right
- **Viewer panel**: Fixed 450px width, sticky positioning to stay visible while scrolling
- **Responsive design**: Stacks vertically on screens smaller than 1200px
- **Viewer container**: 600px height with black background

#### JavaScript Integration
- **OpenSeadragon library**: Added script tag to load `/static/js/lib/openseadragon/openseadragon.min.js`
- **Viewer initialization**: Configured OpenSeadragon with:
  - IIIF image service support
  - Navigation controls (zoom in/out, home)
  - Mini-navigator in bottom-right corner
  - Custom button IDs for control integration

#### HTML Structure
- **Container div**: `.transcription-viewer-container` wraps both columns
- **Transcription column**: `.transcription-content` contains all existing content
- **Viewer panel**: `.viewer-panel` with controls and viewer div
- **Control buttons**: Zoom +/-, Reset buttons in French

### 2. Current Configuration

The viewer currently uses a sample IIIF URL for testing:
```javascript
var iiifUrl = "https://iiif.dcsr.unil.ch/iiif/2/patrinum-IG-9-81-2-007-050-recto.jp2/info.json";
```

## Next Steps

To complete the integration, the following tasks are needed:

### 1. Add IIIF URL Field to Transcription Model
Add a new field to store the IIIF URL in `app/fiches/models/documents/document.py`:

```python
class Transcription(ACModel):
    # ... existing fields ...
    
    iiif_url = models.URLField(
        verbose_name=_("URL IIIF"),
        blank=True,
        null=True,
        help_text=_("URL du service d'images IIIF (doit se terminer par /info.json)")
    )
    
    show_facsimile = models.BooleanField(
        verbose_name=_("Afficher le facsimilé"),
        default=False,
        help_text=_("Afficher le visualiseur de facsimilé sur la page de transcription")
    )
```

### 2. Create and Run Migration
```bash
cd /workspaces/lumieres-lausanne/app
python manage.py makemigrations fiches
python manage.py migrate
```

### 3. Update the Form
Add the new fields to `TranscriptionForm` in `app/fiches/forms.py`:

```python
class TranscriptionForm(forms.ModelForm):
    # ... existing fields ...
    
    class Meta:
        model = Transcription
        fields = '__all__'
```

### 4. Update the Template
Replace the hardcoded IIIF URL in the JavaScript with the model field:

```javascript
// In transcription.html, replace:
var iiifUrl = "https://iiif.dcsr.unil.ch/...";

// With:
{% if trans.show_facsimile and trans.iiif_url %}
var iiifUrl = "{{ trans.iiif_url }}";
{% else %}
var iiifUrl = null;
{% endif %}
```

### 5. Update the Edition Template
Add IIIF URL field to `app/fiches/templates/fiches/edition/transcription.html`:

```html
<fieldset>
    <div class="fieldWrapper">
        <label for="id_iiif_url">{{ transForm.iiif_url.label }}</label>
        {{ transForm.iiif_url }}
        <span class="helptext">{{ transForm.iiif_url.help_text }}</span>
    </div>
    
    <div class="fieldWrapper">
        {{ transForm.show_facsimile }}
        <label for="id_show_facsimile" class="inner-label">{{ transForm.show_facsimile.label }}</label>
    </div>
</fieldset>
```

### 6. Add Validation
Add URL validation to ensure it's a valid IIIF info.json URL:

```python
from django.core.exceptions import ValidationError

class Transcription(ACModel):
    # ... fields ...
    
    def clean(self):
        super().clean()
        if self.iiif_url and not self.iiif_url.endswith('/info.json'):
            raise ValidationError({
                'iiif_url': _("L'URL IIIF doit se terminer par '/info.json'")
            })
```

## Testing

### Sample IIIF URLs for Testing
- Patrinum (UNIL): `https://iiif.dcsr.unil.ch/iiif/2/patrinum-IG-9-81-2-007-050-recto.jp2/info.json`
- Other IIIF servers: Any valid IIIF Image API 2.0 or 3.0 endpoint

### Browser Compatibility
OpenSeadragon supports:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Features

### Current Features
- ✅ Side-by-side view of transcription and facsimile
- ✅ Sticky viewer panel (stays visible while scrolling)
- ✅ Zoom controls
- ✅ Mini-navigator
- ✅ Responsive layout

### Future Enhancements (Optional)
- Toggle to hide/show viewer
- Multiple image support (for multi-page documents)
- Synchronized scrolling between transcription and images
- Image rotation controls
- Fullscreen mode
- Download/print options

## Documentation References

- OpenSeadragon: https://openseadragon.github.io/
- IIIF Image API: https://iiif.io/api/image/
- OpenSeadragon Examples: https://openseadragon.github.io/examples/

## Issue Tracking

Related GitHub Issue: #66 - Setup project: Configure and install OpenSeadragon
