---
applyTo: 'docs/**/*.md'
---
# Documentation Standards

- All documentation files must use `markdown` format (`.md`).
- Filenames must be in `snake_case` and lowercase.
- Use [MkDocs](https://www.mkdocs.org/) to build and serve documentation.
- The main configuration file is `mkdocs.yml`.
- Place all documentation in the `docs/` directory.
- Structure documentation with clear headings and a logical hierarchy.
- Use relative links for cross-referencing pages within the documentation.
- Add new pages to the navigation in `mkdocs.yml`.
- Preview documentation locally with `make docs/serve` before publishing.
- Limit lines to a maximum of 80 characters whenever possible.