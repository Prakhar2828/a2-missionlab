# Phase P — Full Release-Candidate QA

## Objective

Qualify the Phase O-complete A2 MissionLab candidate as a release candidate without reopening completed product-design phases or introducing new mission reconstruction. Phase P is a verification phase: it strengthens test orchestration, makes portable browser coverage mandatory in CI, runs the complete protected Windows release matrix, and records what remains manual/device-only.

## Immutable starting point

Phase P starts only from the completed Phase O local state:

- branch: `phase-10-quality-recovery`
- HEAD: `8e0ba840391e7b239fca422cb660c7354fa4349b`
- tree: `a3a48442cf0cd3777e17cdb50d93c3be8d918f64`
- expected `origin/main`: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- recovery branch remains unpublished

Phase P does not push, merge, deploy, publish a release, or start Phase Q.

## Release-candidate layers

### 1. Static / syntax / publication / evidence

The Windows release installer must rerun the existing release contracts, including:

- Python compilation and JavaScript syntax
- public text/markup integrity
- final public-experience structure and local-link integrity
- publication pack, publication web, and release manifest validation
- Phase K publication contract
- Phase L typography contract
- Phase M accessibility contract
- Phase N performance/failure-state contract
- Phase O metadata/social/README contract
- processed-data analytical/evidence validators available in the real repository
- pure deterministic model validators

No correct historical gate may be weakened to obtain a pass.

### 2. Portable Chromium CI gate

`.github/workflows/ci.yml` must install Chrome for Testing, pass the action's exact `chrome-path` output into `PHASE_P_CHROME`, and run:

`python scripts/validation/validate_phase_p_regression.py --portable`

The portable gate is required, not best-effort. It covers:

- Mission Explorer interaction/scroll stability
- Through Orion Windows navigation/scroll stability
- deterministic GNC AUTO/MANUAL behavior
- Mission Control decision/layout behavior
- PSI model interaction
- trajectory-correction model interaction
- space-weather model interaction
- entry/descent/recovery interaction
- the global eight-route responsive smoke matrix

This is a Chromium CI gate. It is not represented as Edge, Safari, or real-device coverage.

### 3. Local Windows exhaustive release gate

The Windows release installer runs:

`python scripts/validation/validate_phase_p_regression.py --windows-release`

That command orchestrates the full protected browser stack with the release browsers available on the user's machine, including the portable suites plus Phase K, L, M, N, and O browser contracts. Existing validators retain their own exact case-count and browser requirements; Phase P does not replace them with a weaker umbrella test.

## Required viewport contract

The protected Phase M matrix already covers the master-prompt release viewport set, including:

- 320 × 568
- 360-class phone
- 375-class phone
- 390 × 844
- 430 × 932
- phone landscape
- tablet portrait
- tablet landscape
- approximately 1024 px
- 1280 × 800
- 1440 × 900
- 1920 × 1080 where practical

Phase P treats that matrix as mandatory protected evidence rather than recreating a second competing responsive system.

## Failure behavior

The release gate is fail-closed:

- first failing validator stops qualification
- no failing browser suite is converted into a warning
- no missing required release browser is treated as a pass
- no `undefined`, `NaN`, raw stack trace, broken-image state, or blank critical canvas is accepted when a protected failure-state regression covers it
- the engineering-log completion entry is appended only after every required Windows gate succeeds

## Manual / device QA boundary

The following are **NOT AUTOMATED BY PHASE P** and must not be claimed as executed by CI or the Windows headless browser suite:

- iPhone Safari on physical hardware
- Android Chrome on physical hardware
- physical tablet browser testing
- desktop Safari where accessible
- assistive-technology review with a real screen reader
- subjective visual review for polish, memorability, and executive-level hiring impact

Those limitations are explicit. Phase Q owns the adversarial executive review/final polish; it must not be silently folded into Phase P.

## Protected systems

Phase P does not intentionally alter public route markup, simulation physics, mission evidence, imagery, typography, responsive CSS, accessibility semantics, performance ownership, or failure-state UI. Any product mutation during Phase P must be justified by a demonstrated release-candidate defect and then requalified through the complete gate.

## Dedicated Phase P artifacts

- `scripts/validation/validate_phase_p_release_candidate.py`
  - static QA-control contract
  - CI enforcement contract
  - protected validator inventory
  - manual/device boundary contract
- `scripts/validation/validate_phase_p_regression.py`
  - portable Chromium CI orchestration
  - exhaustive Windows release orchestration
- `docs/PHASE_P_RELEASE_CANDIDATE_QA.md`
  - release scope, coverage, and honest limitations

## Phase boundary

Successful Phase P means the candidate has passed the complete release-candidate qualification available on the real Windows repository plus mandatory portable CI coverage. It does **not** mean Phase Q is complete, and it does not authorize a push or deployment.
