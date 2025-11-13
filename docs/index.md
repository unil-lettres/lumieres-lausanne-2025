<!--
Copyright (C) 2010-2025 Université de Lausanne, RISET
<https://www.unil.ch/riset/>

This file is part of Lumières.Lausanne.
Lumières.Lausanne is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Lumières.Lausanne is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This copyright notice MUST APPEAR in all copies of the file.
-->

# Lumières.Lausanne Documentation

Welcome to the Lumières.Lausanne documentation. This platform is a digital humanities project for managing and displaying historical transcriptions, documents, and facsimiles.

## About the Project

**Lumières.Lausanne** is a Django-based web application developed by RISET at the Université de Lausanne (UNIL) for scholarly research and publication of historical documents from the Enlightenment period.

### Key Features

- **Transcription Management**: Create, edit, and publish historical transcriptions
- **IIIF Facsimile Viewer**: Display high-resolution facsimiles alongside transcriptions using IIIF and OpenSeadragon
- **Advanced Search**: Full-text search and filtering capabilities
- **Multilingual Support**: Content and interface available in French and English
- **Rich Text Editing**: CKEditor integration for formatted content

### Technology Stack

- **Backend**: Python 3.12+, Django 5.2
- **Frontend**: JavaScript, jQuery, OpenSeadragon
- **Standards**: IIIF (International Image Interoperability Framework)
- **Database**: PostgreSQL
- **Search**: Apache Solr

---

## Documentation Structure

This documentation is organized into three main sections:

### 👥 User Guides

Documentation for end users who browse and interact with the platform.

- **[Facsimile Viewer Usage Guide](facsimile-usage-guide.md)** - Complete guide to using the IIIF facsimile viewer
- **[Facsimile User Guide (EN)](en/facsimile-user-guide.md)** - English version of the user guide
- **[Guide utilisateur (FR)](fr/facsimile-guide-utilisateur.md)** - French version of the user guide

### 🛠️ Administrator Guides

Documentation for administrators and content editors managing the platform.

- **[Facsimile Admin Guide (EN)](en/facsimile-admin-guide.md)** - Complete administrator guide for managing IIIF facsimiles
- **[Guide administrateur (FR)](fr/facsimile-guide-admin.md)** - French version of the administrator guide

### 💻 Developer Documentation

Technical documentation for developers working on the platform.

- **[OpenSeadragon Integration](openseadragon-integration.md)** - Technical details of the OpenSeadragon viewer integration
- **[IIIF Facsimile Migration](iiif-facsimile-migration.md)** - Migration documentation for the IIIF facsimile feature

---

## Quick Start

### For Users

If you're a researcher or reader using the platform:

1. Browse to a transcription page
2. Use the layout mode buttons to switch between:
   - **Text only** (📄) - Read the transcription
   - **Text + Facsimile** (📄🖼️) - View transcription and original document side-by-side
   - **Facsimile only** (🖼️) - Examine the original document

See the **[Facsimile Viewer Usage Guide](facsimile-usage-guide.md)** for detailed instructions.

### For Administrators

If you're managing transcriptions and facsimiles:

1. Navigate to the transcription edit page in the admin interface
2. Add an IIIF manifest URL in the "Facsimile IIIF URL" field
3. Click "Charger" (Load) to validate and preview
4. Save the transcription

See the **[Facsimile Admin Guide](en/facsimile-admin-guide.md)** for complete instructions.

### For Developers

If you're developing or maintaining the platform:

1. Clone the repository
2. Set up the development environment using Docker Compose
3. Review the technical documentation for architecture details

See the **[IIIF Facsimile Migration](iiif-facsimile-migration.md)** and **[OpenSeadragon Integration](openseadragon-integration.md)** guides.

---

## Recent Updates

### Version 2025.1 (Branch: `feat/facsimile-viewer`)

**IIIF Facsimile Viewer Implementation**

- ✅ Added `facsimile_iiif_url` field to Transcription model
- ✅ Implemented OpenSeadragon viewer integration
- ✅ Added layout mode toggles (text/split/viewer)
- ✅ Implemented page synchronization between text and images
- ✅ Added form validation for IIIF manifest URLs
- ✅ Responsive layout for mobile and desktop
- ✅ Comprehensive documentation in English and French

See **[IIIF Facsimile Migration](iiif-facsimile-migration.md)** for detailed changelog.

---

## Getting Help

### Common Issues

- **Facsimile not loading?** Check the [Troubleshooting section](facsimile-usage-guide.md#troubleshooting) in the usage guide
- **Admin validation errors?** See the [Error Messages section](en/facsimile-admin-guide.md#error-messages-and-debugging)
- **Developer setup issues?** Review the [Migration Steps](iiif-facsimile-migration.md#migration-steps)

### Support Resources

- **GitHub Repository**: [unil-lettres/lumieres-lausanne-2025](https://github.com/unil-lettres/lumieres-lausanne-2025)
- **Issue Tracker**: Report bugs and feature requests on GitHub
- **RISET Contact**: Technical support from RISET, UNIL

---

## External Resources

### IIIF Standards

- [IIIF Presentation API](https://iiif.io/api/presentation/) - Official specification
- [IIIF Image API](https://iiif.io/api/image/) - Image service specification
- [Awesome IIIF](https://github.com/IIIF/awesome-iiif) - Community resources

### Tools & Libraries

- [OpenSeadragon](https://openseadragon.github.io/) - Deep zoom viewer library
- [Mirador](https://projectmirador.org/) - Reference IIIF viewer
- [IIIF Validator](https://presentation-validator.iiif.io/) - Manifest validation tool

### Django Documentation

- [Django 5.2 Documentation](https://docs.djangoproject.com/en/5.2/)
- [Django Forms](https://docs.djangoproject.com/en/5.2/topics/forms/)
- [Django Models](https://docs.djangoproject.com/en/5.2/topics/db/models/)

---

## Contributing

Contributions to the documentation are welcome! Please follow these guidelines:

1. All source files must be in English
2. Include the copyright header (see [copyright.md](copyright.md))
3. Use Markdown for formatting
4. Test locally with `mkdocs serve` before submitting

---

## License

This project is licensed under the GNU General Public License v3.0 or later.

See **[Copyright & License](copyright.md)** for complete information.

---

**Last Updated**: November 13, 2025  
**Current Branch**: `feat/facsimile-viewer`  
**Version**: 2025.1
