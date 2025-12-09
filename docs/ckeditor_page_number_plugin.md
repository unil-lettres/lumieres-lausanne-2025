# CKEditor Page Number Plugin

## Overview

The Page Number plugin for CKEditor allows users to insert custom page tags in the format `<<page_number>>` into their content. This feature is particularly useful for transcription work where page references need to be marked within the text.

## Features

- **Simple Dialog Interface**: Click the "Page numéro" button to open a dialog
- **Input Validation**: Ensures only valid numeric page numbers are entered
- **Internationalization**: Available in English and French
- **Cursor Position Insertion**: Inserts the tag at the current cursor position

## Usage

### Adding a Page Number Tag

1. Position your cursor where you want to insert the page number tag
2. Click the "Page numéro" button in the CKEditor toolbar
3. Enter the page number in the dialog that appears
4. Click "OK" to insert the tag

The tag will be inserted in the format `<<page_number>>`, for example: `<<5>>`

### Validation

- The page number field cannot be empty
- Only numeric values are accepted
- The plugin will alert you if invalid input is provided

## Configuration

To enable the plugin in a CKEditor configuration, update `app/lumieres_project/settings_ckeditor_configs.py`:

1. Add `pagenumber` to the `extraPlugins` setting:
   ```python
   'extraPlugins': 'existing,plugins,pagenumber',
   ```

2. Add `PageNumber` button to the toolbar:
   ```python
   'toolbar_Name': (
       ['OtherButtons', 'PageNumber'],
   ),
   ```

## Technical Details

### Plugin Structure

```
app/ckeditor/static/ckeditor/ckeditor/plugins/pagenumber/
├── plugin.js              # Main plugin file
├── pagenumber.png         # Toolbar button icon
├── dialogs/
│   └── pagenumber.js      # Dialog definition
└── lang/
    ├── en.js              # English translations
    └── fr.js              # French translations
```

### Output Format

The plugin inserts the page tag as plain text in the format:
```
<<page_number>>
```

This format can be easily identified and processed in downstream applications.

## Localization

The plugin supports the following languages:

- **English (en)**: Button label "Page Number"
- **French (fr)**: Button label "Page numéro"

To add support for additional languages, create a new file in `lang/` directory following the existing pattern.
