---
applyTo: '**'
---
**Migration steps (to be followed one by one):**
1. Analyze Model and View
   - Check un current `app/`
   - Check in old code ressource XavierBeheydt/lumieres-lausanne-2024
2. Verify integrity of the model
   - no missing fields
   - no missing relations
   - no missing methods
3. Verifye the view
   - Check if the view is a class-based view or a function-based view
5. Verify the template
   - Check if the template is using the correct context variables
   - Check if the template is rendering the model data correctly
   - Check if the template is using the correct static files (CSS, JS, images)
6. Try to write unit-tests for the model and the view
   - Use Django test framework
   - Test model methods, properties, and relations
   - Test view responses, context, and templates used

> Create or update unit tests at each step.

> To run tests for django, use the following command:
> ```bash
> make django/test
> ```