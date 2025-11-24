# Pagination Patterns in Transcriptions

## Overview

This document describes the pagination marker patterns found in the `fiches_transcription.text` field and how they are processed by the facsimile viewer synchronization system.

## Analysis Summary (November 2025)

- **Total transcriptions analyzed**: 1,241
- **Transcriptions with folio markers**: 896 (72%)
- **Total pagination markers found**: 4,761

## Supported Patterns

### 1. Implicit Recto Format (75.7% of rectos)

**Pattern**: `<1>`, `<2>`, `<123>`

When only a number appears between angle brackets without an 'r' suffix, it represents a **recto page**.

**Mapping to image sequence**:
- `<1>` → Image 1 (page 1 recto)
- `<2>` → Image 3 (page 2 recto)
- `<N>` → Image (N × 2 - 1)

**Examples**:
- Transcription 1287: Uses `<1>`, `<2>`, `<3>`, etc.
- Total occurrences: 2,029
- Unique markers: 262

### 2. Explicit Recto Format (24.3% of rectos)

**Pattern**: `<1r>`, `<2r>`, `<123r>`

The 'r' suffix explicitly indicates a recto page.

**Mapping to image sequence**:
- `<1r>` → Image 1 (page 1 recto)
- `<2r>` → Image 3 (page 2 recto)
- `<Nr>` → Image (N × 2 - 1)

**Examples**:
- Transcription 1097: Uses `<1r>`, `<2r>`, `<3r>`, etc.
- Total occurrences: 650
- Unique markers: 44

### 3. Verso Format (always explicit)

**Pattern**: `<1v>`, `<2v>`, `<123v>`

The 'v' suffix indicates a verso (back) page.

**Mapping to image sequence**:
- `<1v>` → Image 2 (page 1 verso)
- `<2v>` → Image 4 (page 2 verso)
- `<Nv>` → Image (N × 2)

**Examples**:
- Most common: `<1v>` appears 686 times
- Total occurrences: 2,029
- Unique markers: 157

### 4. Page Format (rare)

**Pattern**: `p. [1]`, `p. [1v]`, `p. 1`

Alternative format using "p." prefix with optional brackets.

**Examples**:
- Transcription 735: Uses `p. [1]`, `p. [1v]`, `p. [2]`, etc.
- Total occurrences: 53
- Unique markers: 53

## Mixed Pattern Transcriptions

**10 transcriptions** use both implicit and explicit recto formats in the same document:

- Transcription 735: `<1v>`, `<2r>`, `p. [3]`, etc.
- Transcription 737: `<1v>`, `<2r>`, `<2v>`, `<3r>`, etc.
- Transcription 1287: `<1>`, `<1v>`, `<2>`, `<2v>`, etc.

## Implementation

### JavaScript (transcription-sync.js)

The pagination synchronization system processes these markers in the following order:

1. **Extract page format** (`/p. 1/`)
2. **Extract explicit recto/verso** (`<1r>`, `<1v>`)
3. **Extract implicit recto** (`<1>`, `<2>`)
   - Excludes patterns already matched as explicit recto/verso
   - Excludes HTML tags

Each marker is wrapped in a span with tracking attributes:
```html
<span class="page-tag" 
      data-page="[mapped-page]" 
      data-original-page="[original]" 
      data-type="[rv-implicit|rv-explicit|p-format]">
  [original-marker]
</span>
```

### Calculation Logic

```javascript
// Implicit recto: <N>
pageNumber = N × 2 - 1

// Explicit recto: <Nr>
pageNumber = N × 2 - 1

// Verso: <Nv>
pageNumber = N × 2
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
