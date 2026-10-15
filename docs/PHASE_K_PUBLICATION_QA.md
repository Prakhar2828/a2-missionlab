# Phase K — Technical Report + Mission Library QA Contract

## Scope

Phase K upgrades two publication surfaces without changing the underlying Artemis II reconstruction:

- `technical-report.html`
- `library.html` / `library.js`

The immutable starting state is Phase J documentation commit:

`c7758aa415928467da0ebb6e48c276c1082be566`

No Phase F/G/H/I/J simulation or mission-behavior contract may be weakened to support publication polish.

## Technical Report contract

The Technical Report must behave as an engineering publication rather than a marketing page.

Required publication apparatus:

- abstract
- executive summary
- exact study-baseline revision identifier
- explicit evidence policy
- stable section anchors
- figure index
- table index
- numbered figure captions
- numbered tables with captions
- numbered Sutton–Graves equation
- consolidated quantitative results
- reproducibility / validation section
- limitations
- references and repository-artifact ledger
- dedicated screen and print/PDF CSS

The report must not load the obsolete top-level `app.js` runtime.

Repository evidence links are pinned to the immutable Phase J study baseline instead of an obsolete historical branch name.

Current campaign-context links are dated and use current NASA mission/science landing pages. Campaign schedule text remains explicitly time-bounded because future architecture can change.

## Mission Library contract

The Mission Library preserves all 28 deep dives but changes the information architecture from a flat full-document render into a question-led knowledge system.

Required knowledge path:

`QUESTION → EXPLANATION → EVIDENCE → SOURCE`

Required category system:

1. Flight Dynamics
2. Vehicle & GNC
3. Mission Operations
4. Entry & Recovery
5. Environment & Radiation
6. Lunar Science
7. Data & Software
8. Evidence & Methods
9. Future Artemis

Every deep dive must have:

- one canonical category
- one curated engineering question
- searchable technical content
- evidence legend
- mission context
- analytical / physical method
- inputs and outputs
- interpretation boundary
- assumptions / uncertainty / limitations
- repository evidence links
- technical capability summary
- related-question discovery

Only one full deep dive is rendered at a time. Search/filter result cards remain lightweight. Deep-dive figures use lazy loading.

## Evidence boundaries

Phase K publication changes do not alter the canonical evidence taxonomy:

- NASA REPORTED
- MISSIONLAB DERIVED
- MODELED
- INFERRED
- UNKNOWN / NOT PUBLIC

Permanent non-equivalences remain intact, including:

- public OEM state != Orion onboard navigation state
- DSN tracking != onboard navigation sensor
- temporal sequence != causation
- statistical anomaly != spacecraft fault
- modeled heating != measured TPS telemetry
- public mission reconstruction != private Mission Control data
- educational maneuver modeling != NASA targeting solution
- environmental context != crew dosimetry
- PSI model != flight-qualified plume analysis
- Artemis II loft/rebound != Artemis I skip entry

## Dedicated static validation

Run:

```text
python scripts/validation/validate_phase_k_publication.py
```

The validator requires:

- dedicated report/library stylesheets
- exact Phase J study baseline identity
- 13 stable Technical Report figure anchors
- 3 numbered Technical Report tables
- print/PDF CSS
- no obsolete report `app.js`
- no obsolete `public-experience-v3` repository links in Phase K publication surfaces
- all report figure assets present
- all 28 library topics retained
- all 28 topics mapped to questions and categories
- focused single-article Library rendering
- related-topic discovery
- lazy-loaded deep-dive imagery

## Dedicated browser regression

Run on the real Windows release machine:

```text
python scripts/validation/validate_phase_k_regression.py --required
```

Chrome and Edge are both required for release.

Representative widths:

- 390 × 844 phone portrait
- 844 × 390 phone landscape
- 768 × 1024 tablet portrait
- 1440 × 900 desktop

The browser regression verifies:

- 28 initial Library result cards
- 10 Library filter controls (`All` + 9 categories)
- correct result count
- Entry & Recovery category filtering
- Sutton search coverage: exactly the `convective-heating` and `thermal-protection` deep dives, because the latter explicitly discusses the Sutton–Graves external-flow estimate versus Avcoat material response
- one focused deep dive at a time
- explicit four-stage knowledge path
- curated engineering question
- related-question links
- Library horizontal containment
- 4-block report revision metadata
- executive summary presence
- all 13 indexed report figures
- all 3 numbered report tables
- obsolete report `app.js` absent
- report horizontal containment

## Protected regressions

Phase K release must also preserve the existing browser contracts for:

- Mission Explorer
- Through Orion's Windows
- GNC
- Mission Control
- PSI
- Trajectory Correction
- Space Weather
- Entry / Descent / Recovery
- global responsive QA

A Phase K publication improvement is not allowed to weaken an existing protected test.

## Zero-cost / architecture boundary

Phase K adds no backend, paid service, paid font, inference API, database, analytics product, or recurring dependency.

The deployment remains static HTML/CSS/JavaScript on the existing zero-cost architecture.
