---
applyTo: 'app/**'
---
We are rewriting the Django application, currently resulting from a partial
migration from an older Python/Django version.

> Communication can be in French, but all generated files must be in English.

**Specifications:**
- Python 3.12+
- Django 5.2
- Django project: `app/lumieres_project`
- App to migrate: `app/fiches`

**Convention for migrated code insertion:**
```
# START {type} Migration Part =...
{migration-code-here}
# END {type} Migration Part =...
```

**Django elements locations:**
- Project URLs: `app/lumieres_project/urls.py`
- App URLs: `app/fiches/urls/__init__.py`
- Views: `app/fiches/views/__init__.py`
- Models: `app/fiches/models/__init__.py`
- Tests: `app/fiches/tests/__init__.py`
- Global statics: `app/static/`
- App statics: `app/static/fiches`
- Global templates: `app/template/`
- App templates: `app/template/fiches/`

**Migration steps (to be followed one by one):**
1. Create a simple view  
   - `HttpResponse("{view name}: {url}")`
   - Update the project URLs
2. Migrate models  
   - Model migration
   - Integration of existing data
   - Update the admin
3. Develop the view  
   - Create or update the view and its template
4. Create forms and use generic views
   - Create an HTML form in the template with `{% csrf_token %}`
   - Add a view to handle the form POST
   - Use `ListView` and `DetailView` to display lists and details
   - Adapt URLs for generic views (`<int:pk>`)
   - Update templates for these views
5. Customize Django admin
   - Use `list_display`, `search_fields`, `list_filter`
   - Add custom actions if needed
   - Test add, edit, and delete

> Wait for user request before each step.
> Create or update unit tests at each step.
> Notify if any instruction or configuration files need to be updated.
> Comments the old code.