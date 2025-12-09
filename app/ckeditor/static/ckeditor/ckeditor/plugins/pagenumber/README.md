# Page Number Plugin for CKEditor

## Overview

This plugin adds a "Page Number" button to CKEditor that allows users to insert custom page tags in the format `<<page_number>>`.

## Features

- Dialog-based input for page numbers
- Input validation (numeric values only)
- Internationalization support (English and French)
- Inserts tags at cursor position

## Usage

1. Click the "Page Number" button in the toolbar
2. Enter a page number in the dialog
3. Click OK to insert the tag `<<page_number>>`

## Installation

To use this plugin in a CKEditor configuration:

1. Add `pagenumber` to the `extraPlugins` setting
2. Add `PageNumber` to your toolbar configuration

Example:
```python
'extraPlugins': 'existing,plugins,pagenumber',
'toolbar_Name': (
    ['OtherButtons', 'PageNumber'],
),
```

## Files

- `plugin.js` - Main plugin file
- `dialogs/pagenumber.js` - Dialog definition
- `lang/en.js` - English translations
- `lang/fr.js` - French translations
- `pagenumber.png` - Toolbar button icon
- `test_pagenumber.html` - Manual test page

## Testing

Open `test_pagenumber.html` in a web browser to manually test the plugin functionality.

## License

Copyright (C) 2010-2025 Université de Lausanne, RISET

This file is part of Lumières.Lausanne and is licensed under the GNU General Public License v3.
See the file headers for full license information.
