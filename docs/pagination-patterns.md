# Pagination Patterns in Transcriptions

## Overview

This document describes the pagination marker patterns found in the `fiches_transcription.text` field and how they are processed by the facsimile viewer synchronization system.

As of December 2025, pagination synchronization is based on **existing folio/page markers** in the transcription text (e.g. `<1>`, `<1v>`), not on custom `<<n>>` markers.

## Analysis Summary (November 2025)

- **Total transcriptions analyzed**: 1,241
- **Transcriptions with folio markers**: 896 (72%)
- **Total pagination markers found**: 4,761

## Supported Patterns

### Angle-bracket folio markers (used for sync)

**Pattern**: `<1>`, `<2>`, `<123>`, `<1r>`, `<1v>`, `<123v>` (case-insensitive `r`/`v`)

These markers are treated as **page-break markers**. Each occurrence indicates a transition to the “next” facsimile image.

**Important**: the numeric part is not used to compute a canvas index. The system uses the **order of occurrences** in the text.

Example (simplified):
- first marker found in the text → first displayed facsimile canvas
- second marker → next facsimile canvas
- etc.

This makes synchronization robust even when the folio numbering in the transcription is not perfectly aligned with the IIIF source (e.g. additional covers/blanks).

## Facsimile start canvas offset

Some IIIF manifests contain extra canvases at the beginning (e.g. book cover, guard pages, blank pages). To avoid shifting all page-break mappings in the transcription, the `Transcription` model provides:

- `facsimile_start_canvas` (integer, optional, 1-based)
  - empty/null → start at canvas 1 (the first canvas)
  - `2` → treat the second canvas as the first transcription page, etc.

During rendering, the viewer computes:
- `startCanvasIndex0 = facsimile_start_canvas - 1` (defaults to `0`)
- for each marker occurrence `i` (0-based): `canvasIndex = startCanvasIndex0 + i`

## Implementation

### JavaScript (transcription-sync.js)

The pagination synchronization system:

1. Extracts all supported `<…>` markers in document order
2. Treats each marker occurrence as a sequential page break
3. Applies the `facsimile_start_canvas` offset to map marker #1 → canvas index

Each marker is wrapped in a span with tracking attributes (generated at runtime):
```html
<span class="page-tag" 
      data-folio="[marker-content-without-brackets]" 
      data-marker-index="[1-based-occurrence-index]"
      data-canvas-index="[0-based-canvas-index]"
      >
  [original-marker]
</span>
```

## Data Sources

Analysis performed using `tools/analyze_pagination_final.py` on the production database.

Example transcriptions for testing:
- **Implicit only**: 1288, 1287, 1080, 1088, 779
- **Explicit only**: 1097, 1106, 942, 766, 1197
- **Mixed patterns**: 735, 737, 1423, 775, 777

## See Also

- [Facsimile Viewer Integration](./openseadragon-integration.md)
- [IIIF Facsimile Migration](./iiif-facsimile-migration.md)
