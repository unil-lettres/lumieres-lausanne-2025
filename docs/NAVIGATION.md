# Documentation Navigation Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                        📚 Lumières.Lausanne                         │
│                      Documentation Home Page                        │
│                          docs/index.md                              │
└────────────┬──────────────────┬──────────────────┬──────────────────┘
             │                  │                  │
    ┌────────▼────────┐ ┌──────▼────────┐ ┌──────▼────────┐
    │   👥 Users      │ │ 🛠️ Admins     │ │ 💻 Developers │
    └────────┬────────┘ └───────┬───────┘ └───────┬───────┘
             │                  │                  │
             │                  │                  │
    ┌────────▼────────────────────────────┐       │
    │  User Guides                        │       │
    ├─────────────────────────────────────┤       │
    │ • facsimile-usage-guide.md         │       │
    │   (Complete guide)                  │       │
    │                                     │       │
    │ • en/facsimile-user-guide.md       │       │
    │   (Simplified EN)                   │       │
    │                                     │       │
    │ • fr/facsimile-guide-utilisateur.md│       │
    │   (Simplified FR)                   │       │
    └─────────────────────────────────────┘       │
                                                  │
             ┌────────────────────────────────────┘
             │
    ┌────────▼────────────────────────────┐
    │  Administrator Guides               │
    ├─────────────────────────────────────┤
    │ • en/facsimile-admin-guide.md      │
    │   (Complete EN admin guide)         │
    │   - Field management                │
    │   - Validation & preview            │
    │   - Error debugging                 │
    │                                     │
    │ • fr/facsimile-guide-admin.md      │
    │   (Complete FR admin guide)         │
    │   - Gestion des champs             │
    │   - Validation & prévisualisation  │
    │   - Débogage des erreurs           │
    └─────────────────────────────────────┘
                     │
                     │
            ┌────────▼────────────────────────────┐
            │  Developer Documentation            │
            ├─────────────────────────────────────┤
            │ • openseadragon-integration.md     │
            │   - Technical integration           │
            │   - Next steps                      │
            │                                     │
            │ • iiif-facsimile-migration.md      │
            │   - Database migration              │
            │   - Form validation                 │
            │   - Template updates                │
            └─────────────────────────────────────┘
```

## Cross-Reference Network

```
facsimile-usage-guide.md ──────┐
        │                      │
        │                      ▼
        │           en/facsimile-admin-guide.md ──┐
        │                      │                  │
        │                      │                  ▼
        │                      │      openseadragon-integration.md
        │                      │                  │
        │                      ▼                  │
        └──────────> fr/facsimile-guide-admin.md │
                               │                  │
                               │                  │
                               ▼                  ▼
                    iiif-facsimile-migration.md ─┘
```

## Language Links

```
┌─────────────────────┐          ┌─────────────────────┐
│   English (EN)      │ ◄──────► │    Français (FR)    │
├─────────────────────┤          ├─────────────────────┤
│ User Guide          │ ◄──────► │ Guide utilisateur   │
│ Admin Guide         │ ◄──────► │ Guide administrateur│
└─────────────────────┘          └─────────────────────┘
```

## Documentation Types by Audience

```
┌──────────────────────────────────────────────────────────────────┐
│                        AUDIENCE MATRIX                           │
├──────────────────┬─────────────┬──────────────┬──────────────────┤
│  Document        │ 👥 Users    │ 🛠️ Admins    │ 💻 Developers    │
├──────────────────┼─────────────┼──────────────┼──────────────────┤
│ index.md         │ ✅ Primary  │ ✅ Primary   │ ✅ Primary       │
│ usage-guide.md   │ ✅ Primary  │ ⚪ Reference │ ⚪ Reference     │
│ user-guide.md    │ ✅ Primary  │ ⚪ Reference │ ⚪ Reference     │
│ admin-guide.md   │ ⚪ Reference│ ✅ Primary   │ ⚪ Reference     │
│ integration.md   │ ❌ Skip     │ ⚪ Reference │ ✅ Primary       │
│ migration.md     │ ❌ Skip     │ ⚪ Reference │ ✅ Primary       │
│ copyright.md     │ ⚪ Reference│ ⚪ Reference │ ⚪ Reference     │
└──────────────────┴─────────────┴──────────────┴──────────────────┘

Legend:
✅ Primary   = Main documentation for this audience
⚪ Reference = Secondary/reference material
❌ Skip      = Not relevant for this audience
```

## File Organization

```
docs/
│
├── 🏠 Landing & Meta
│   ├── index.md              (Home page - all audiences)
│   ├── README.md             (Documentation guide)
│   ├── ARCHITECTURE.md       (Structure overview)
│   ├── IMPLEMENTATION.md     (Implementation notes)
│   └── copyright.md          (Legal)
│
├── 👥 User Documentation
│   ├── facsimile-usage-guide.md
│   ├── en/
│   │   └── facsimile-user-guide.md
│   └── fr/
│       └── facsimile-guide-utilisateur.md
│
├── 🛠️ Admin Documentation
│   ├── en/
│   │   └── facsimile-admin-guide.md
│   └── fr/
│       └── facsimile-guide-admin.md
│
├── 💻 Developer Documentation
│   ├── openseadragon-integration.md
│   └── iiif-facsimile-migration.md
│
└── 🖼️ Assets
    ├── img/
    └── theme/
```

## Navigation Paths

### Path 1: New User
```
index.md
  → User Guides section
    → facsimile-usage-guide.md
      → Display modes
      → Viewer controls
      → Troubleshooting
```

### Path 2: Content Editor
```
index.md
  → Administrator Guides section
    → en/facsimile-admin-guide.md
      → Adding IIIF URL
      → Validation
      → Error debugging
```

### Path 3: Developer
```
index.md
  → Developer Documentation section
    → iiif-facsimile-migration.md
      → Database changes
      → Form validation
      → Template updates
    → openseadragon-integration.md
      → Integration details
      → Next steps
```

### Path 4: Cross-Language
```
en/facsimile-user-guide.md
  → Related Documentation
    → fr/facsimile-guide-utilisateur.md
      (Same content in French)
```

## Quick Reference Links

### From Any Page

Every page includes:

1. **Breadcrumb** navigation:
   ```
   Home > Section > Current Page
   ```

2. **Related Documentation** section:
   ```markdown
   **Related Documentation:**
   - [Page 1](link1.md)
   - [Page 2](link2.md)
   ```

3. **Bottom metadata**:
   ```markdown
   Last Updated: YYYY-MM-DD
   Version: X.Y
   ```

## MkDocs Menu Structure

```yaml
nav:
  - Home: index.md
  - User Guides:
    - Facsimile Viewer Usage
    - User Guide (EN)
    - Guide utilisateur (FR)
  - Administrator Guides:
    - Admin Guide (EN)
    - Guide administrateur (FR)
  - Developer Documentation:
    - OpenSeadragon Integration
    - IIIF Facsimile Migration
  - About:
    - Documentation Structure
    - Implementation Notes
    - Copyright & License
```

---

**Generated**: November 13, 2025  
**Purpose**: Visual reference for documentation structure
