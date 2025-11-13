# Documentation Structure

This directory contains the documentation for the Lumières.Lausanne project, built with MkDocs.

## Quick Start

### View the Documentation

To build and serve the documentation locally:

```bash
# From the project root
mkdocs serve
```

Then open http://127.0.0.1:8000 in your browser.

### Build Static Site

To build the static documentation site:

```bash
mkdocs build
```

The built site will be in the `site/` directory.

## Documentation Structure

```
docs/
├── index.md                          # Home page
├── copyright.md                      # License and copyright information
├── facsimile-usage-guide.md         # Complete usage guide (EN)
├── iiif-facsimile-migration.md      # Developer: migration details
├── openseadragon-integration.md     # Developer: integration architecture
├── en/                              # English documentation
│   ├── facsimile-admin-guide.md    # Administrator guide (EN)
│   └── facsimile-user-guide.md     # User guide (EN)
├── fr/                              # French documentation
│   ├── facsimile-guide-admin.md    # Administrator guide (FR)
│   └── facsimile-guide-utilisateur.md # User guide (FR)
├── img/                             # Screenshots and images
└── theme/                           # Custom theme files (if any)
```

## Target Audiences

### 👥 Users

End users who browse and interact with the platform should read:
- [Facsimile Viewer Usage Guide](facsimile-usage-guide.md)
- [User Guide (EN)](en/facsimile-user-guide.md)
- [Guide utilisateur (FR)](fr/facsimile-guide-utilisateur.md)

### 🛠️ Administrators

Content editors and administrators should read:
- [Administrator Guide (EN)](en/facsimile-admin-guide.md)
- [Guide administrateur (FR)](fr/facsimile-guide-admin.md)

### 💻 Developers

Developers working on the platform should read:
- [IIIF Facsimile Migration](iiif-facsimile-migration.md)
- [OpenSeadragon Integration](openseadragon-integration.md)

## Adding Documentation

### Create a New Page

1. Create a new `.md` file in the appropriate directory
2. Add the copyright header (see [copyright.md](copyright.md))
3. Add navigation breadcrumbs at the top
4. Add cross-references to related documentation
5. Update `mkdocs.yml` navigation

### Copyright Header

All documentation files must include the copyright header. See [copyright.md](copyright.md) for the template.

### Cross-References

Use relative links for internal documentation:

```markdown
See the [Administrator Guide](en/facsimile-admin-guide.md) for details.
```

### Images

Place screenshots and images in the `img/` directory:

```markdown
![Description](img/screenshot.png)
```

## MkDocs Configuration

The site is configured in `mkdocs.yml` at the project root.

### Navigation Structure

The navigation is organized into:
- **Home**: Landing page
- **User Guides**: For end users
- **Administrator Guides**: For content editors
- **Developer Documentation**: For developers
- **Legal**: Copyright and license

### Theme

Currently using the `readthedocs` theme. To customize, edit `mkdocs.yml`.

### Extensions

Enabled Markdown extensions:
- `toc`: Table of contents with permalinks
- `admonition`: Call-out boxes
- `codehilite`: Syntax highlighting
- `meta`: Page metadata

## Writing Guidelines

### Language

- All source files must be in English
- French translations go in `fr/` directory
- Code examples and technical terms remain in English

### Formatting

- Use ATX-style headers (`# Header`)
- Use fenced code blocks with language specified
- Use semantic line breaks (one sentence per line)
- Keep lines under 100 characters when possible

### Structure

1. Copyright header
2. Title (H1)
3. Navigation breadcrumb
4. Overview section
5. Related documentation links
6. Main content
7. References and resources
8. Footer with last updated date

### Example Structure

```markdown
<!--
Copyright header
-->

# Page Title

> **Navigation**: [Home](../index.md) > Section > Page Title

## Overview

Brief description of the page.

**Related Documentation:**
- [Link to related page](other-page.md)

---

## Main Content

...

---

**Last Updated**: YYYY-MM-DD
```

## Maintenance

### Updating Documentation

When updating documentation:

1. Ensure all cross-references are still valid
2. Update screenshots if UI has changed
3. Update "Last Updated" date
4. Check that `mkdocs serve` builds without errors
5. Review broken links

### Version Control

- Documentation follows the same branching strategy as code
- Update docs in the same PR as code changes
- Tag documentation versions with code releases

## Deployment

The documentation can be deployed to:
- GitHub Pages (via `mkdocs gh-deploy`)
- Static hosting (build with `mkdocs build`)
- Read the Docs (automatic builds from GitHub)

### GitHub Pages

To deploy to GitHub Pages:

```bash
mkdocs gh-deploy
```

This builds and pushes to the `gh-pages` branch.

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [MkDocs Themes](https://github.com/mkdocs/mkdocs/wiki/MkDocs-Themes)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) (alternative theme)

---

**Last Updated**: November 13, 2025
