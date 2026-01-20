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

# IIIF Facsimile Viewer Migration

> **Navigation**: [Home](index.md) > [Developer Documentation](index.md#developer-documentation) > IIIF Facsimile Migration

## Overview

This document describes the implementation of IIIF facsimile viewer functionality for transcriptions, including database migration, form validation, and UI enhancements.

**Related Documentation:**

- **[OpenSeadragon Integration](openseadragon-integration.md)** - Technical integration details
- **[Administrator Guide](en/facsimile-admin-guide.md)** - Admin interface usage
- **[Usage Guide](facsimile-usage-guide.md)** - End-user documentation

---

## Changes Made

### Database Migration
- **Migration**: `0009_add_facsimile_iiif_url.py`
- **Field Added**: `facsimile_iiif_url` (URLField, blank=True) to the `Transcription` model
- **Purpose**: Store IIIF manifest URLs for facsimile display

### Model Changes
- **File**: `app/fiches/models/documents/document.py`
- **Model**: `Transcription`
- **Field**: `facsimile_iiif_url = models.URLField(verbose_name=_("Facsimile IIIF URL"), blank=True, help_text=_("URL of the IIIF manifest (e.g., ending with info.json)"))`

### Form Validation
- **File**: `app/fiches/forms.py`
- **Form**: `TranscriptionForm`
- **Validation**: `clean_facsimile_iiif_url()` method validates IIIF manifest URLs by fetching and parsing JSON
- **Widget**: URLInput with custom width (400px)

### Template Updates
- **File**: `app/fiches/templates/fiches/edition/transcription.html`
- **Features**:
  - Facsimile URL input field with validation button
  - OpenSeadragon viewer integration
  - Toggle functionality: "Charger" (load) / "Supprimer" (unload)
  - Input disabled with hidden field when viewer loaded to ensure form submission
  - IIIF manifest parsing for v2/v3 APIs

### JavaScript Functionality
- Client-side URL validation via AJAX
- Viewer loading with tile source extraction from IIIF manifests
- Proper viewer cleanup and state management
- Form submission handling to include disabled input values

## Migration Steps

### 1. Database Migration
```bash
cd /workspaces/lumieres-lausanne
python app/manage.py migrate fiches
```

### 2. Dependencies
Ensure the following are installed:
- OpenSeadragon library (included in static files)
- requests library (for server-side validation)
- jQuery (for client-side interactions)

### 3. Static Files
Ensure static files are collected:
```bash
python app/manage.py collectstatic
```

## Deployment Notes

### Environment Requirements
- Python 3.12+
- Django 5.2
- IIIF-compliant image servers for manifests

### Testing
- Test with valid IIIF manifest URLs
- Verify viewer loads correctly
- Ensure form saves facsimile URLs to database
- Test unload functionality clears URL and destroys viewer

### Rollback
If needed, reverse the migration:
```bash
python app/manage.py migrate fiches 0008
```

### Performance Considerations
- IIIF manifest fetching has 10-second timeout
- Viewer initialization may be resource-intensive for large manifests
- Consider caching manifest responses in production

## Usage

1. Navigate to transcription edit page
2. Enter IIIF manifest URL in "Facsimile IIIF URL" field
3. Click "Charger" to validate and load viewer
4. Viewer appears in right panel with zoom/navigation controls
5. Click "Supprimer" to unload viewer and clear URL
6. Save transcription to persist the URL

## Troubleshooting

### Common Issues
- **Viewer not loading**: Check IIIF manifest URL validity and network connectivity
- **URL not saving**: Ensure form validation passes; check server logs for validation errors
- **Performance issues**: Large manifests may cause slow loading; consider pagination or lazy loading

### Logs
Check Django logs for form validation errors and IIIF parsing issues.