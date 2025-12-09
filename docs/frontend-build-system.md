# Front-end Build System

This project uses a modern front-end build system with Vite for fast development and optimized production builds.

## Requirements

- **Node.js** 18+ and **npm** 9+

## Quick Start

### Install Dependencies

```bash
npm install
# or using Make
make npm-install
```

### Development

Run the Vite development server with hot module replacement:

```bash
npm run dev
# or using Make
make npm-dev
```

The dev server runs on `http://localhost:3000` and provides:
- Fast hot module replacement (HMR)
- Source maps for debugging
- Live CSS updates without page reload

### Production Build

Build optimized assets for production:

```bash
npm run build
# or using Make
make npm-build
```

This generates minified and optimized files in `app/static/dist/` with:
- Code splitting for better caching
- Minified JavaScript and CSS
- Asset hashing for cache busting
- Source maps for debugging

### Preview Production Build

Preview the production build locally:

```bash
npm run preview
# or using Make
make npm-preview
```

## Project Structure

```
app/static/
├── src/                    # Source files (development)
│   ├── js/
│   │   ├── main.js        # Main entry point
│   │   ├── search.js      # Search functionality
│   │   ├── collection.js  # Collection management
│   │   ├── admin.js       # Admin features
│   │   ├── modules/       # Feature modules
│   │   │   ├── carousel.js
│   │   │   └── lightbox.js
│   │   └── utils/         # Utility functions
│   │       └── dom.js     # DOM helpers
│   ├── css/
│   │   ├── main.css       # Main stylesheet
│   │   ├── base/          # Reset and typography
│   │   ├── components/    # Reusable components
│   │   ├── layout/        # Grid and containers
│   │   ├── pages/         # Page-specific styles
│   │   ├── utils/         # Utility classes
│   │   └── theme/         # Colors and spacing
│   └── assets/
│       ├── images/
│       └── fonts/
└── dist/                   # Built files (production)
    ├── js/
    ├── css/
    └── assets/
```

## Technologies

### Vite
- **Fast development server** with native ES modules
- **Hot Module Replacement (HMR)** for instant updates
- **Optimized builds** with Rollup
- **CSS preprocessing** and PostCSS support

### Vanilla JavaScript
- **No jQuery dependency** - Pure ES6+ JavaScript
- **Modern DOM utilities** for familiar jQuery-like API
- **Modular architecture** with ES6 modules
- **Swiper.js** for carousels (replaces jCarousel)

### Code Quality Tools
- **ESLint** - JavaScript linting with modern ES2022 rules
- **Prettier** - Code formatting for consistency
- **Stylelint** - CSS linting

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint:js` | Lint JavaScript files |
| `npm run lint:css` | Lint CSS files |
| `npm run format` | Format code with Prettier |

## Code Quality

### Linting

Lint JavaScript:
```bash
npm run lint:js
make npm-lint-js
```

Lint CSS:
```bash
npm run lint:css
make npm-lint-css
```

### Formatting

Format all source files:
```bash
npm run format
make npm-format
```

## Django Integration

### Static Files Configuration

The built files are output to `app/static/dist/` which is included in Django's `STATICFILES_DIRS`.

### Using in Templates

In development with Vite dev server running:
```django
{% load static %}
<script type="module" src="http://localhost:3000/@vite/client"></script>
<script type="module" src="http://localhost:3000/js/main.js"></script>
```

In production:
```django
{% load static %}
<link rel="stylesheet" href="{% static 'dist/css/main.[hash].css' %}">
<script type="module" src="{% static 'dist/js/main.[hash].js' %}"></script>
```

## Migration from jQuery

This project has been migrated from jQuery to vanilla JavaScript:

### Key Changes
- **jQuery** → **Vanilla JS with custom DOM utilities**
- **jQuery UI** → **Native CSS and JavaScript**
- **jCarousel** → **Swiper.js**
- **jQuery lightbox** → **Custom vanilla JS lightbox**

### DOM Utilities

The `utils/dom.js` module provides jQuery-like helpers:

```javascript
import { $, $1, on, addClass, removeClass } from './utils/dom.js';

// Query selector (returns NodeList)
const elements = $('.my-class');

// Query single element
const element = $1('#my-id');

// Add event listener
on('.button', 'click', (e) => {
  console.log('Clicked!');
});

// Add/remove classes
addClass(element, 'active');
removeClass(element, 'active');
```

## Clean Build

Remove build artifacts and dependencies:

```bash
npm run clean
# or
make npm-clean
```

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2022+ features
- No IE11 support

## Contributing

When adding new features:

1. Place source files in `app/static/src/`
2. Follow existing file structure
3. Run linters before committing
4. Update this documentation if needed

## License

Copyright (C) 2010-2025 Université de Lausanne, RISET

This is part of Lumières.Lausanne and follows the same GPL-3.0-or-later license.
