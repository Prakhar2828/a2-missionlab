# Phase D — Mission Control QA

## Scope

Phase D rebuilds the Mission Control presentation while preserving the
four public-data scenario classes and the evidence boundaries around
NASA-reported, MissionLab-derived, modeled, and unknown/not-public
information.

The visualization canvas is structurally independent from event and
discipline narrative content. Narrative paragraphs cannot occupy the
canvas region at any responsive breakpoint.

## Product contract

The experience separates five concerns:

1. scenario selection
2. mission visualization
3. event and evidence context
4. discipline lens
5. seven-stage operational decision reconstruction

FLIGHT remains the starting integrator.

Selectable perspectives:

- FLIGHT
- FDO
- FAO
- EECOM
- COMM
- SCIENCE
- ENG SUPPORT

COMM remains explicitly identified as MissionLab shorthand.

ENG SUPPORT remains explicitly identified as a MissionLab synthesis
lens rather than a claimed Artemis II front-room console position.

No private NASA telemetry, private flight-control displays, fabricated
voice loops, proprietary control laws, private option trees, or
unpublished console ownership are claimed.

## Decision model

The public UI follows the seven-stage Phase 7B evidence model:

1. DETECT
2. EVIDENCE
3. CONSTRAINTS
4. OPTIONS
5. DECISION
6. ACTION
7. OUTCOME

The UI does not claim that the displayed synthesis is a private
mission-control transcript or complete internal decision history.

## Geometry stability

Event and discipline panels use breakpoint-specific fixed layout
tracks sized for the longest supported content.

Changing a scenario or discipline therefore changes the information,
not the control-room geometry.

The dedicated regression separately verifies that the fixed panel
sizes are large enough to contain every tested content state without
vertical clipping.

## Dedicated browser regression

Run:

`scripts/validation/validate_mission_control_regression.py --required`

The regression requires both Microsoft Edge and Google Chrome.

Each browser exercises:

- 390 x 844 phone portrait
- 430 x 932 larger phone
- 768 x 1024 tablet
- 844 x 390 phone landscape
- 1280 x 800 laptop
- 1440 x 900 desktop

For every viewport, the regression exercises all four scenarios across
all seven discipline lenses for 28 state combinations.

The browser regression verifies:

- event narrative is not a descendant of the visualization surface
- role narrative is not a descendant of the visualization surface
- event and role context never intersect the canvas
- all four scenario states update
- all seven role states update
- exactly one scenario exposes aria-pressed=true
- exactly one discipline exposes aria-pressed=true
- event title updates
- event classification updates
- event summary updates
- evidence label updates
- evidence-boundary copy updates
- discipline title updates
- discipline explanation updates
- discipline questions update
- all seven decision stages update
- decision model retains DECISION between OPTIONS and ACTION
- waste-system visualization retains TEMP, WASTE, CABIN, POWER
- scenario and role controls meet a 44 px minimum touch target
- canvas dimensions remain nonzero
- no horizontal page overflow
- no scenario/role-triggered outer-page scroll jump above 1 px
- no scenario/role-triggered control-room geometry jump above 1 px
- fixed context panels do not clip their content
- lower-page content remains reachable

## Validation boundary

Automated browser testing proves the tested Edge and Chrome behavior
only.

It does not constitute Safari, Firefox, iOS Safari, Android hardware,
or subjective visual-design validation. Those remain part of later
deep browser, responsive, accessibility, and visual QA.
