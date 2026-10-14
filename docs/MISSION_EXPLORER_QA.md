# Mission Explorer Interaction QA

Phase B establishes deterministic geometry and strict horizontal containment for
the Mission Explorer.

## Defect class 1: page jump

The earlier mobile implementation used a viewport-width-derived stage height.

On browsers with a classic vertical scrollbar, scrollbar appearance can alter
the layout viewport width. A height derived from `vw` therefore changes too.

The original failure was approximately 21.7 CSS pixels.

Mission Explorer now uses fixed outer heights at its responsive breakpoints.

## Defect class 2: navigation intrinsic-width leakage

A horizontal milestone flex rail created a large min-content width.

That intrinsic width could propagate through nested CSS Grid containers and make
the Mission Explorer navigation wider than the visible story panel. The document
still reported zero horizontal overflow because the outer page clipped overflow,
but interactive elements such as the range input and milestone buttons extended
outside the usable viewport.

Mission Explorer now uses:

- `min-width: 0` at every relevant grid boundary
- explicit `width` and `max-width` containment
- a bounded range input
- a wrapping milestone grid instead of a horizontal flex rail
- two milestone columns in the narrow story panel
- three milestone columns when the whole Explorer has collapsed to a wider
  single-column tablet layout
- two columns again on phone layouts

## Automated browser matrix

The dedicated Mission Explorer regression tests:

- 360 x 800
- 390 x 844
- 430 x 932
- 768 x 1024
- 844 x 390
- 1180 x 820
- 1366 x 768
- 1440 x 900

Local release validation requires Chrome and Edge.

## Interaction coverage

The regression exercises:

- every Mission Explorer moment
- Previous
- Next
- every milestone button
- representative free timeline positions
- start/end disabled states
- timeline accessible value text

## Geometry invariants

No tested interaction may create more than one CSS pixel of:

- page scroll drift
- shell top drift
- shell height drift
- stage top drift
- stage height drift
- story height drift
- navigation top or height drift
- control-row top or height drift
- Previous/Next vertical drift
- control document-position drift
- document client-width drift
- document scroll-height drift
- horizontal control overflow beyond the story panel

Page-level horizontal overflow must also remain zero.

## Manual final-release gate

Before final release, verify Mission Explorer on real:

- iPhone Safari
- Android Chrome
- tablet Safari or Chrome
- macOS Safari

Test portrait and landscape where applicable.
