---
mode: agent
name: Review Models

description: |
  Review and analyze one or more Django models from the legacy codebase. For each model:
  - Identify all fields, relationships, custom managers, and methods.
  - For each relationship, specify if it is required or optional, its type (ForeignKey, ManyToMany, GenericRelation, etc.), and its multiplicity (e.g., 0..1, 0..n).
  - Note any deprecated or legacy patterns, and suggest improvements or migrations for Django 5.2+.
  - For each model, include the full source code of the model class under review in the documentation (in a collapsible code block or appendix section).
  - Generate or update a documentation file in `docs/models/<ModelName>.md` for each model, including:
    - Model overview
    - Fields and relationships as an array/table, with columns: Field, Type, Required, Multiplicity, Description (see Project example)
    - Custom manager(s) and their methods
    - Legacy/deprecated patterns
    - Migration/modernization suggestions
    - SQL table mapping
    - Mermaid UML diagram
    - References to code and SQL
    - The full source code of the model class (in a collapsible code block or appendix)
    - Space for further review notes and migration scripts
  - Optionally, update `LEGACY_MODELS.md` with a summary or checklist for each reviewed model.
  - The prompt should be reusable for any or all models in the project.

input: |
  - The name(s) of the Django model(s) to review (e.g., FreeContent, Project, News, etc.)
  - The relevant model code and SQL table definition(s)
  - Any specific concerns or migration goals

output: |
  - A new or updated documentation file at `docs/models/<ModelName>.md` for each model reviewed, with the above structure
  - The fields/relationships section must use an array/table format as in the Project example (columns: Field, Type, Required, Multiplicity, Description)
  - The full source code of the model class must be included in the documentation (in a collapsible code block or appendix)
  - Optionally, a summary or checklist in LEGACY_MODELS.md for each model
  - The prompt should be reusable for any or all models in the project
---
Expected output and any relevant constraints for this task.