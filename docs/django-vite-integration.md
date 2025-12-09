# Django Integration Guide for Vite Build System

This guide explains how to integrate the Vite build system with Django templates.

## Overview

The Vite build system has been successfully integrated with minimal changes to the Django configuration. Assets are built to `app/static/dist/` and served through Django's static file system.

## Django Template Tags

Custom template tags are provided in `fiches/templatetags/vite_tags.py` to simplify asset loading.

### Available Tags

#### `{% vite_hmr %}`
Includes the Vite HMR client in development mode (automatic hot reload).

```django
{% load vite_tags %}
{% vite_hmr %}
```

#### `{% vite_css 'path' %}`
Loads a CSS asset with automatic hashing in production.

```django
{% load vite_tags %}
{% vite_css 'css/main.css' %}
```

Output in production:
```html
<link rel="stylesheet" href="/static/dist/css/main.DHBATib1.css">
```

#### `{% vite_js 'path' %}`
Loads a JavaScript module with automatic hashing in production.

```django
{% load vite_tags %}
{% vite_js 'js/main.js' %}
```

Output in production:
```html
<script type="module" src="/static/dist/js/main.BPILkIgG.js"></script>
```

#### `{% vite_asset 'path' 'type' %}`
Returns just the URL (useful for custom tags or inline usage).

```django
{% load vite_tags %}
<link rel="stylesheet" href="{% vite_asset 'css/main.css' %}">
```

## Template Migration

### Example: Modern Base Template

See `app/fiches/templates/base_vite.html` for a complete example.

```django
{% load static vite_tags %}
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Lumières.Lausanne{% endblock %}</title>
    
    {# Vite HMR in development #}
    {% vite_hmr %}
    
    {# Main stylesheet #}
    {% vite_css 'css/main.css' %}
    
    {# Main JavaScript #}
    {% vite_js 'js/main.js' %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

### Hybrid Approach (Gradual Migration)

You can load both old and new assets during migration:

```django
{% load static vite_tags %}

{# New Vite assets #}
{% vite_css 'css/main.css' %}

{# Legacy assets - remove gradually #}
<link rel="stylesheet" href="{% static 'css/old-styles.css' %}">

{# New JavaScript modules #}
{% vite_js 'js/main.js' %}

{# Legacy jQuery - keep during transition #}
<script src="https://code.jquery.com/jquery-1.8.2.min.js"></script>
```

## Development vs Production

### Development Mode
- `DEBUG = True` in Django settings
- Assets loaded from Vite dev server (`http://localhost:3000`)
- Hot Module Replacement (HMR) enabled
- No build step required

**Start dev server:**
```bash
npm run dev
```

### Production Mode
- `DEBUG = False` in Django settings
- Assets loaded from `app/static/dist/`
- Hashed filenames for cache busting
- Requires build step

**Build for production:**
```bash
npm run build
```

## Configuration

### Django Settings

No changes needed! The existing configuration works:

```python
# app/lumieres_project/settings.py

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR.parent / "static",  # Includes app/static/dist/
    BASE_DIR.parent / "ckeditor/static",
]
```

### Optional: Vite Dev Server URL

You can customize the Vite dev server URL:

```python
# settings.py
VITE_DEV_SERVER = "http://localhost:3000"  # Default
```

## Asset Organization

### Source Files (Development)
```
app/static/src/
├── js/
│   ├── main.js          # Main entry point
│   ├── search.js        # Search page
│   ├── collection.js    # Collection management
│   ├── admin.js         # Admin interface
│   ├── modules/         # Feature modules
│   └── utils/           # Shared utilities
└── css/
    ├── main.css         # Main entry point
    ├── base/            # Reset, typography
    ├── components/      # UI components
    ├── layout/          # Grid, containers
    ├── pages/           # Page-specific
    ├── utils/           # Helpers
    └── theme/           # Colors, spacing
```

### Built Files (Production)
```
app/static/dist/
├── .vite/
│   └── manifest.json    # Maps source to built files
├── js/
│   ├── main.[hash].js
│   ├── search.[hash].js
│   └── ...
└── css/
    ├── main.[hash].css
    └── ...
```

## Available JavaScript Modules

### Main Application (`main.js`)
Automatically initializes:
- Carousel (Swiper.js)
- Lightbox
- Global namespace (window.LL)

### Search Module (`search.js`)
Search filter system for biographical searches:
```javascript
// Available globally
window.search_filter.init();
```

### Collection Module (`collection.js`)
Collection CRUD operations:
```javascript
// Available globally
window.collection.create();
window.collection.edit(collId);
window.collection.remove(collId, collTitle);
```

### Admin Module (`admin.js`)
Admin-specific features (auto-loaded on admin pages).

## Utilities

### DOM Helpers
Vanilla JS utilities providing jQuery-like API:

```javascript
import { $, $1, on, addClass } from './utils/dom.js';

// Query elements
const elements = $('.my-class');
const element = $1('#my-id');

// Add event listener
on('.button', 'click', (e) => {
  console.log('Clicked!');
});

// Add class
addClass(element, 'active');
```

See `app/static/src/js/utils/dom.js` for full API.

## Troubleshooting

### Assets not loading in production

1. Ensure build has been run: `npm run build`
2. Check manifest exists: `app/static/dist/.vite/manifest.json`
3. Verify static files collected: `python manage.py collectstatic`

### HMR not working in development

1. Ensure Vite dev server is running: `npm run dev`
2. Check `DEBUG = True` in Django settings
3. Verify dev server accessible at `http://localhost:3000`

### JavaScript errors

1. Check browser console for errors
2. Verify all dependencies installed: `npm install`
3. Check build output for errors: `npm run build`

## Migration Checklist

When migrating a template to use Vite assets:

- [ ] Load `vite_tags` template tag library
- [ ] Add `{% vite_hmr %}` in head (development HMR)
- [ ] Replace old CSS with `{% vite_css 'css/main.css' %}`
- [ ] Replace old JS with `{% vite_js 'js/main.js' %}`
- [ ] Test in both development and production modes
- [ ] Remove old jQuery/CSS when no longer needed
- [ ] Update any custom JavaScript to use new modules

## Performance Benefits

### Before (jQuery)
- jQuery 1.8.2: ~93KB
- jQuery UI: ~232KB
- jCarousel: ~46KB
- Various plugins: ~50KB
- **Total: ~421KB uncompressed**

### After (Modern Stack)
- Main bundle: ~70KB (includes Swiper)
- Individual modules: Code-split and lazy-loaded
- **Total: ~70KB + on-demand modules**
- **Gzipped: ~22KB**

### Improvements
- ⚡ **80% smaller** initial bundle
- 🚀 **Faster** page load times
- 📦 **Code splitting** for better caching
- 🔄 **Hot reload** during development
- 🎯 **Modern ES2022** features

## Next Steps

1. **Gradual Migration**: Update templates one at a time
2. **Test Thoroughly**: Verify all functionality works
3. **Monitor Performance**: Check page load times
4. **Remove Legacy Code**: Clean up old jQuery files when safe
5. **Optimize Further**: Add page-specific bundles as needed

## Support

For issues or questions:
- Check the [Front-end Build System](frontend-build-system.md) documentation
- Review the example templates in `app/fiches/templates/`
- Consult the Vite documentation: https://vitejs.dev/
