---
applyTo: '**'
---
We are rewriting the Django application, currently resulting from a partial
migration from an older Python/Django version.

> Communication can be in French, but all generated files must be in English.

**Specifications:**
- Python 3.12+
- Django 5.2
- Django project: `app/lumieres_project`
- App to migrate: `app/fiches`

**Django elements locations:**
- Project URLs: `app/lumieres_project/urls.py`
- App URLs: `app/fiches/urls.py`
- Views: `app/fiches/views/__init__.py`
- Models: `app/fiches/models/__init__.py`
- Tests: `app/fiches/tests/__init__.py`
- Global statics: `app/static/`
- App statics: `app/fiches/static/fiches/`
- App templates: `app/fiches/templates/fiches/`

**Instructions**
- Wait for user request before each step.
- Notify if any instruction or configuration files need to be updated.
- Create or update unit tests at each step (if working to `app/**`).
- Add copyright with `docs/copyright.md` template in every top of source files commented.