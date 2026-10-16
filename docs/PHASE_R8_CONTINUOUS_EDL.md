# Phase R8 - Continuous EDL cinematic + engineering viewport polish

## Why R8 exists
Visual review of the locally qualified R7 build found two presentation problems that deterministic browser checks did not capture:

1. The additive visual companion still read as a sequence of scene cards rather than one continuous descent. Descent, parachute recovery, and splashdown also reused too much ocean context.
2. The engineering entry graph could be stretched by the state board, while its top evidence panels and loft note overlaid the graph. The only Play button lived below the stage and the original ~4.5 second playback could advance into the loft while a reviewer scrolled back to the graph.

## R8 changes
- Keeps `js/entry-model.js` byte-for-byte unchanged.
- Adds immediate Play/Reset controls inside the engineering stage.
- Slows the engineering reconstruction to a watchable phase-aware ~40 second presentation.
- Moves engineering stage chrome into dedicated grid rows so it cannot cover the plot.
- Caps the desktop graph/state-board height and lets the state board scroll internally rather than stretching the plot.
- Rebuilds the additive companion around a continuous capsule/camera path.
- Keeps descent and drogue phases above a cloud deck with no ocean surface.
- Reveals a distant ocean only late in main-parachute descent.
- Starts the true ocean-recovery scene only at the derived surface crossing.
- Animates drogue deployment, drogue-to-main handoff, main inflation, splash, ripples, and a real-time post-splash settling hold.
- Preserves the R7 evidence boundary: the camera/orientation are illustrative and not private telemetry.

## Boundary
R8 improves presentation and playback only. It does not alter the flight-derived Entry model, public event anchors, modeled heating/dynamic-pressure values, evidence labels, or recovery chronology.
