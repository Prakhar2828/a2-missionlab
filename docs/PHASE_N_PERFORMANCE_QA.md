# Phase N — Performance + Loading + Failure-State QA

## Scope

Phase N hardens the current Phase M product without changing protected mission models, evidence boundaries, interaction semantics, or visual identity.

The phase is intentionally bounded to current-tree debt that remains after Phases K–M:

- stop globally eager Earth/Moon JPEG transfer on routes that never draw those bodies,
- suspend Mission Explorer and GNC animation work when their canvases are offscreen or the document is hidden,
- remove the permanently bypassed pre-Phase-I Entry renderer from `js/mission.js`,
- remove duplicate Windows crew-geometry resize redraw ownership,
- defer below-fold figure/image decoding where the route does not need the image immediately,
- convert broken image resources into explicit, readable fallback states,
- keep celestial canvases usable through procedural Earth/Moon rendering if optional JPEG assets fail.

## Immutable starting state

- Branch: `phase-10-quality-recovery`
- Starting HEAD: `14e161281e733b700159c5a306e970a8de74dea3`
- Starting tree: `72f26106a8eccbb5b500e95e74bb54fc9eb5b81b`
- Phase M implementation parent: `60cdc7a1be2b081b0fcd7e7105cc4de8806f356a`
- Protected `origin/main`: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- Recovery branch publication state: local-only / unpublished

## Quantified starting costs

At the Phase N start:

- Earth JPEG: 518,573 bytes
- Moon JPEG: 252,499 bytes
- Combined celestial JPEG payload: 771,072 bytes (~753 KiB)
- `js/mission.js`: 27,082 bytes
- Mission route JavaScript: 97,830 bytes across eight scripts
- Technical Report figures: 13 eager local images
- Mission Explorer figures: 7 eager local images

`js/core.js` was loaded by several routes that never draw Earth or Moon, so the 771,072-byte optional image payload was globally requested even where it provided no value.

## Phase N design

### 1. Lazy celestial ownership

`js/core.js` now keeps Earth and Moon resources in an `idle` state until `drawEarth()` or `drawMoon()` is actually called. The first draw still immediately renders the existing procedural body, so the visualization never waits on the JPEG. Successful image decode upgrades later draws; a failed JPEG leaves the procedural fallback in place.

A dedicated `a2:celestialchange` event requests only the redraws that need the newly resolved asset instead of synthesizing a global window resize.

### 2. Visibility-aware animation

Mission Explorer and GNC now follow the already-proven Mission Control pattern:

- `IntersectionObserver`
- `document.hidden`
- explicit RAF ownership
- no accumulated hidden/offscreen catch-up on resume

Mission Explorer also retains its Phase M reduced-motion contract. GNC does not use reduced-motion to disable the meaningful control simulation; it only stops work when the experience is not visible.

Both canvases expose `data-a2-animation="running|paused"` as a deterministic QA surface.

### 3. Dead route code removal

The old Entry/descent/recovery block in `js/mission.js` was permanently bypassed by the Phase I `data-entry-phase-i` contract. Phase N removes that dead renderer while leaving the protected Phase I implementation in `js/entry-model.js` + `js/entry.js` unchanged.

### 4. Image loading policy

- The homepage hero remains eager/high-priority.
- Below-fold homepage imagery is lazy-decoded.
- Mission Explorer engineering figures are lazy-decoded.
- GNC, Mission Control, Windows lower-page figures, and all Technical Report figures are lazy-decoded.
- Unused NASA image preconnects are removed from routes that do not request NASA imagery.
- Through Orion's Windows keeps its current primary image eager and preserves adjacent-image preload behavior.

### 5. Explicit failure quality

The shared runtime now owns image failures in capture phase, including images inserted after startup. Images with a declared local fallback still use it. If the fallback also fails, or a local technical figure is missing, the broken image is hidden and a readable status replaces it:

> Figure unavailable in this build. The surrounding mission context remains available.

Celestial JPEG failure remains a visualization fallback, not a route failure: procedural Earth/Moon rendering continues.

## Protected contracts

Phase N must not change:

- trajectory two-body impulse-response model or evidence boundaries,
- PSI model/evidence behavior,
- Space Weather model/evidence behavior,
- Phase I Entry model/evidence behavior,
- GNC deterministic AUTO/MANUAL model, cadence invariants, disturbance recovery, or control semantics,
- Mission Control decision/evidence behavior,
- Windows 25-image navigation/lightbox behavior,
- Phase K publication/library contracts,
- Phase L typography hierarchy,
- Phase M accessibility and responsive contracts, including the >=44 px shared control floor and >=64 px Mission Control floor.

## Validation contract

Phase N adds:

- `scripts/validation/validate_phase_n_performance.py` — static/loading/failure contract,
- `scripts/validation/phase_n_performance_regression.html` — browser harness,
- `scripts/validation/validate_phase_n_regression.py` — required Windows Edge + Chrome driver plus an explicit celestial-failure pass.

The browser regression validates both normal asset loading and an intentional 404 mode for the Earth/Moon JPEGs. In failure mode, the route must report celestial fallback state while still rendering a nonblank procedural canvas.

The browser harness does not assume that a canvas is visible at route load, and it does not use `scrollIntoView()` from the nested test iframe. It disables route smooth scrolling, computes the canvas document-space position, scrolls the route window directly to explicit visible/offscreen positions, and couples each RAF assertion to measured canvas geometry. This avoids outer-frame scroll capture and startup-position races while preserving the actual requirement: work runs when the canvas is visible and stops when it is materially offscreen.

The harness also does **not** wait for `window.load`, because public routes can intentionally contain remote NASA imagery that is irrelevant to the local performance contract and may remain pending. It waits for same-origin route DOM readiness instead. Completion is explicit: the browser POSTs its finished 20-case JSON result to a tokenized loopback endpoint owned by the Python driver. The driver waits for that exact completion signal and then terminates the isolated headless browser process tree. `--dump-dom` and virtual-time expiry are not used as completion signals.

The missing-local-figure assertion respects the same lazy-loading policy it is protecting. The harness first positions the Technical Report figure into the route viewport, then swaps that visible image to an intentionally missing local resource. This guarantees that Chromium actually attempts the resource before the test waits for the shared capture-phase `error` handler. An offscreen `loading="lazy"` image is not treated as a failure merely because the browser has correctly deferred requesting it.

The release installer must also rerun the protected public/static/model/evidence/browser gates and the Phase M 192-case accessibility/responsive matrix before creating a local implementation commit.

## Browser coverage rule

Package construction may use an available Chromium browser to exercise the Phase N harness, but that is not claimed as the Windows release gate. The deterministic installer requires both installed Microsoft Edge and Google Chrome and fails closed if either browser or either Phase N normal/failure pass fails.

## Limitations

- Native iPhone Safari, Android Chrome, tablet hardware, and desktop Safari remain manual release-candidate checks unless they are actually run.
- Phase N does not rewrite all historical CSS/JS or introduce a bundler; the project remains a zero-cost static application.
- Lazy loading depends on browser heuristics, so the contract is semantic (`loading="lazy"`) rather than a claim that a specific browser will defer every image by an identical number of pixels.
