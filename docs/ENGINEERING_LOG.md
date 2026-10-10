# A2 MissionLab — Engineering & Learning Log

> Living technical record of what we built, why we built it, what the math means, what failed, what we learned, how we validated it, and what remains uncertain.
>
> **Rule:** update this document before every phase commit or merge.

---

## 0. Documentation Standard

A2 MissionLab should leave an auditable trail showing:

- public source data used;

- what NASA/JPL provided directly;

- what we derived ourselves;

- mathematical assumptions;

- code transformations;

- validation methods;

- failures and corrections;

- supported conclusions vs. hypotheses;

- technical and mission-operations learnings.

### Provenance labels

| Label | Meaning |
|---|---|
| **FLIGHT DATA** | Direct value from public Artemis II flight data. |
| **NASA REPORTED** | Publicly reported NASA fact/event/value not necessarily present in the raw data we possess. |
| **DERIVED** | Deterministic calculation performed by A2 MissionLab from public data. |
| **MODEL** | Output of a physical, statistical, or ML model. |
| **SYNTHETIC** | Explicitly invented data used only for testing, demonstration, or education. |

### Interpretation rule

Do not upgrade a hypothesis into a fact.

Example:

- Supported: two public OEM products differ by 40 km at an epoch.

- Not yet supported: the difference was caused by a navigation update or trajectory correction.

- Correct wording until proven: **solution-to-solution difference**.

---

# Phase 0 — Project Foundation

## Goal

Create a zero-cost, public, open-source foundation for reconstructing Artemis II mission operations and engineering using public NASA data.

Long-term coverage:

- mission timeline

- flight dynamics

- GNC

- propulsion

- communications

- ECLSS

- space weather and radiation

- materials/TPS

- entry and recovery

- lunar science

- crew observations

- anomalies and decisions

- postflight engineering

- AI-assisted mission analysis

## Initial architecture

The first prototype established:

- static web application

- mission-event schema

- source catalog

- provenance taxonomy

- decision-thread representation

- validation tooling

- project disclaimer/documentation

Initial structure:

```text

a2-missionlab/

├── README.md

├── LICENSE

├── DISCLAIMER.md

├── index.html

├── styles.css

├── app.js

├── docs/

├── data/

└── scripts/

```

## Validation

```powershell

python scripts/validate_data.py

```

Observed:

```text

OK: 8 mission events and 8 sources validated.

```

Local server:

```powershell

python -m http.server 8000

```

Successful loads:

- `/`

- `/styles.css`

- `/app.js`

- `/data/seed/mission_events.json`

`favicon.ico` returned 404.

### Learning

The favicon 404 was harmless. It was an optional browser request and did not affect application behavior.

## Git/GitHub challenge

First push failed because Windows Git credentials authenticated as another GitHub account.

Observed:

```text

remote: Permission to Prakhar2828/a2-missionlab.git denied to Prakhar6565.

```

Fix:

```powershell

@"

protocol=https

host=github.com

"@ | git credential-manager erase

```

After re-authenticating as the correct account, push succeeded.

### Learning

`git config user.name` changes commit identity, not GitHub authentication. HTTPS authentication was supplied by Git Credential Manager.

Observed Phase 0 commit:

```text

0f16378 Initialize A2 MissionLab Phase 0 foundation

```

---

# Phase 1 — Mission Backbone

Goal: create a trustworthy temporal and geometric spine to which later subsystems can attach.

```text

NASA flight data

      ↓

Mission clock

      ↓

Orion state vectors

      ↓

Earth/Moon geometry

      ↓

mission phases

      ↓

events / systems / science / anomalies

```

---

# Phase 1A — NASA OEM Ingestion

## Source

NASA Artemis II public AROW ephemeris archive:

`all-artemis-ii-oem-files.zip`

Source:

https://www.nasa.gov/missions/artemis/artemis-2/track-nasas-artemis-ii-mission-in-real-time/

## Archive contents

Found:

- 9 standard CCSDS OEM products

- 1 separate high-rate post-RTC3-to-Entry-Interface trajectory product using a different format

OEM metadata included:

```text

ORIGINATOR = NASA/JSC/FOD/FDO

OBJECT_NAME = EM2

CENTER_NAME = EARTH

REF_FRAME = EME2000

TIME_SYSTEM = UTC

```

### Interpretation correction

We initially called the files successive “planning trajectory solutions.” That was too specific.

What the files directly support:

> They are successive NASA/JSC/FOD/FDO-generated public OEM trajectory products, with labels such as `Pre-OTC3`, `Pre-Lunar-Flyby`, and `Post-ICPS-Sep`.

We will not claim exactly how each product was generated until NASA documentation supports it.

## CCSDS OEM state

Each row contains:

```text

timestamp

x y z

vx vy vz

```

For these products:

- position: km

- velocity: km/s

- center: Earth

- frame: EME2000

- time system: UTC

## Parser

Created:

```text

scripts/ingestion/parse_oem.py

```

It:

1. opens the outer ZIP;

2. opens nested ZIPs;

3. skips the non-OEM entry file;

4. parses `.asc` OEMs;

5. preserves metadata;

6. writes clean CSVs;

7. creates a manifest.

## Parsed counts

| OEM product | States |
|---|---:|
| `Artemis_II_OEM_2026_04_02_to_EI_v3.asc` | 3,212 |
| `Artemis_II_OEM_2026_04_03_to_EI.asc` | 3,239 |
| `Artemis_II_OEM_2026_04_04_to_EI.asc` | 3,235 |
| `Artemis_II_OEM_2026_04_06_Pre-OTC3_to_EI.asc` | 2,106 |
| `Artemis_II_OEM_2026_04_07_Pre-Lunar-Flyby_to_EI.asc` | 1,544 |
| `Artemis_II_OEM_2026_04_08_Post-ICPS-Sep_to_EI.asc` | 3,259 |
| `Artemis_II_OEM_2026_04_09_Post-ICPS-Sep_to_EI.asc` | 3,259 |
| `Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.asc` | 3,262 |
| `OEM - 2026.04.02 - post-USS-2 to EI.asc` | 3,193 |

The separate `2026.04.10 - Post-RTC3 to EI` file is intentionally deferred for entry analysis because it uses a different format/units.

## Why raw/processed data is ignored by Git

`.gitignore` includes:

```text

/data/raw/

/data/processed/

```

Reason:

- public raw archives can be downloaded reproducibly;

- generated products can be recreated from code;

- Git should track transformation logic, metadata, and documentation rather than large/redundant generated files.

---

# Phase 1A.2 — Trajectory Validation

Created:

```text

scripts/validation/validate_trajectory.py

```

## Checks

### Structural integrity

- expected CSV exists

- metadata exists

- row count matches manifest

### Metadata integrity

Expected:

```text

CENTER_NAME = EARTH

REF_FRAME = EME2000

TIME_SYSTEM = UTC

```

### Temporal integrity

- timestamps strictly increase

- first state equals `START_TIME`

- final state equals `STOP_TIME`

### Numerical integrity

All six state-vector components must be finite.

Earth-centered radius:

$$

r = \sqrt{x^2+y^2+z^2}

$$

Inertial speed:

$$

v = \sqrt{v_x^2+v_y^2+v_z^2}

$$

## Result

```text

OK: 9 Artemis II OEM trajectory products validated.

```

Observed Earth-centered radii reached about 413,144–413,148 km.

Observed inertial speeds ranged from roughly 0.414 km/s to ~11 km/s.

### Learning

`Earth-centered radius` is not Earth altitude, and it cannot be used directly as Moon distance.

Moon-relative geometry requires the Moon's time-dependent position in the same frame.

---

# Phase 1B — Mission Clock and Primary Trajectory

## Mission clock

Launch epoch configured:

```text

2026-04-01T22:35:12Z

```

Stored in:

```text

data/config/mission.json

```

Used to derive Mission Elapsed Time (MET).

## Primary OEM working reference

```text

Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.csv

```

Rationale:

- latest full pre-entry OEM in the public archive

- spans the mission arc through Entry Interface

- useful comparison reference

Qualification:

- “primary” is an A2 MissionLab design choice

- it is not proven to be an absolute postflight truth solution

- all nine public OEMs are preserved for comparison

## Derived metrics

Created:

```text

scripts/processing/build_primary_trajectory.py

```

Earth-center distance:

$$

r = \sqrt{x^2+y^2+z^2}

$$

Inertial speed:

$$

v = \sqrt{v_x^2+v_y^2+v_z^2}

$$

Earth radial velocity:

$$

v_r = \frac{\mathbf r \cdot \mathbf v}{\|\mathbf r\|}

$$

Interpretation:

- positive → moving away from Earth

- negative → moving toward Earth

- near zero → Earth-distance turning region

## Observed result

```text

States: 3262

Closest Earth-center distance:

6,515.0 km at 2026-04-10T23:53:16.723

Maximum Earth-center distance:

413,144.4 km at 2026-04-06T23:02:51.667

```

### Validation

The maximum Earth distance closely reproduced NASA's public maximum-distance report, giving our first strong independent validation from raw flight data.

---

# Phase 1C — Moon Geometry with JPL SPICE

## Why a second ephemeris is required

NASA OEM gives:

```text

Orion relative to Earth

```

To calculate Moon-relative geometry:

```text

Moon relative to Earth

```

must be known at the same epoch in the same inertial frame.

## Python dependencies

Pinned direct dependencies at Phase 1 closure:

```text
numpy==2.5.3
spiceypy==8.2.0
matplotlib==3.11.2
```

Recorded in:

```text

requirements.txt

```

## JPL kernels

Downloaded via:

```text

scripts/ingestion/download_spice_kernels.py

```

- `de440s.bsp` — planetary/lunar ephemeris

- `naif0012.tls` — leap-second kernel

- `pck00011.tpc` — body constants/radii

Source:

https://naif.jpl.nasa.gov/naif/data_generic.html

SPICE load test:

```text

SPICE kernels loaded successfully

```

## Reference-frame compatibility

NASA OEM uses `EME2000`.

SPICE query uses `J2000`.

For this analysis they are treated as the compatible inertial frame needed for vector subtraction.

## Moon-relative math

$$

\mathbf r_{O/M}=\mathbf r_O-\mathbf r_M

$$

$$

\mathbf v_{O/M}=\mathbf v_O-\mathbf v_M

$$

Moon-center distance:

$$

d_{O/M}=\|\mathbf r_{O/M}\|

$$

Mean-radius lunar altitude:

$$

h=d_{O/M}-R_{Moon,mean}

$$

SPICE mean lunar radius observed:

```text

1737.400 km

```

Moon-relative speed:

$$

v_{rel}=\|\mathbf v_{O/M}\|

$$

Moon radial velocity:

$$

v_{r,M}=

\frac{\mathbf r_{O/M}\cdot\mathbf v_{O/M}}

{\|\mathbf r_{O/M}\|}

$$

Interpretation:

- negative → approaching Moon

- zero → stationary Moon distance

- positive → receding

## Geometric SPICE state

Used:

```python

spice.spkezr("MOON", et, "J2000", "NONE", "EARTH")

```

`NONE` means geometric state without apparent light-time/stellar-aberration correction.

This is appropriate for physical state comparison at a common epoch.

---

# Phase 1C Challenge — SPICE Time Parsing

Initial:

```python

spice.str2et(f"{timestamp} UTC")

```

produced:

```text

SPICE(UNPARSEDTIME)

```

for timestamp strings containing the ISO `T`.

Fix:

```python

spice_time = timestamp.replace("T", " ") + " UTC"

et = spice.str2et(spice_time)

```

### Learning

Mission timing must be explicit about:

- format

- time system

- UTC

- leap seconds

- ephemeris time conversions

---

# Phase 1C.2 — Sampled Lunar Closest Approach

Created:

```text

scripts/processing/add_lunar_geometry.py

```

Observed nearest OEM sample:

```text

UTC: 2026-04-06T22:58:51.667

MET: 05:00:23:40

Moon-center distance: 8,282.980 km

Mean-radius lunar altitude: 6,545.580 km

Moon-relative speed: 1.381019 km/s

Moon radial velocity: -0.018195 km/s

```

### Interpretation

Radial velocity was still negative, so this was not exact pericynthion.

It was only the closest discrete OEM sample.

---

# Phase 1C.3 — Continuous Pericynthion Reconstruction

Created:

```text

scripts/analysis/refine_lunar_closest_approach.py

```

## Cubic Hermite interpolation

The OEM gives endpoint positions and velocities, allowing a smoother continuous interpolation than straight-line position interpolation.

For normalized interval coordinate \\(u\\):

$$

h_{00}=2u^3-3u^2+1

$$

$$

h_{10}=u^3-2u^2+u

$$

$$

h_{01}=-2u^3+3u^2

$$

$$

h_{11}=u^3-u^2

$$

Position:

$$

\mathbf p(u)=

h_{00}\mathbf p_0

+h_{10}\Delta t\mathbf v_0

+h_{01}\mathbf p_1

+h_{11}\Delta t\mathbf v_1

$$

The derivative gives interpolated velocity.

## Golden-section minimization

We minimize:

$$

d(t)=\|\mathbf r_O(t)-\mathbf r_M(t)\|

$$

over the short interval surrounding closest approach.

Why golden-section search:

- one-dimensional minimization

- deterministic

- simple to audit

- no SciPy dependency

## Refined result

```text

UTC: 2026-04-06T23:00:46.177998+00:00

Moon-center distance: 8,281.938 km

Mean-radius lunar altitude: 6,544.538 km

Moon-relative speed: 1.381073 km/s

Moon radial velocity: -0.000000005 km/s

```

Near-zero radial velocity is exactly what we expect at a local minimum in Moon distance.

## External validation

NASA publicly reported about:

- 7:00 p.m. EDT

- 4,067 miles

- 6,545 km above lunar surface

Our result:

```text

6,544.538 km

```

Difference from NASA's rounded value is roughly 1 km (~0.02%).

## Open discrepancy

NASA also publicly reported Moon-relative speed around 3,139 mph.

Our derived:

```text

1.381073 km/s

≈ 3,089 mph

```

Difference: roughly 1.6%.

Status: **OPEN QUESTION**

Potential causes are not yet proven.

We will not force our value to match.

---

# Phase 1D — Lunar Sphere of Influence and Mission-Phase Classification

Created:

```text

scripts/analysis/classify_mission_phases.py

```

## NASA-reported boundary

```text

41,072 miles

```

Using:

$$

1\ mile=1.609344\ km

$$

gives approximately:

```text

66,099.0 km

```

Provenance:

- SOI boundary distance = **NASA REPORTED**

- crossing times = **DERIVED**

## Crossing method

For adjacent samples:

1. determine inside/outside threshold

2. detect crossing

3. linearly interpolate crossing time

## Results

```text

Derived SOI entry:

2026-04-06T04:38:07.532302+00:00

Derived SOI exit:

2026-04-07T17:23:41.922211+00:00

Time inside SOI:

36.76 hours

Pericynthion:

2026-04-06T23:00:46.177998+00:00

Maximum Earth-center distance:

413,144.445 km

2026-04-06T23:02:51.667

```

## External validation

Derived entry ≈ 12:38 a.m. EDT.

NASA publicly reported actual SOI entry around 12:37 a.m. EDT.

Derived exit ≈ 1:23:42 p.m. EDT.

NASA reporting placed exit around 1:23 p.m. EDT.

## A2 MissionLab geometric phases

```text

OUTBOUND_TRANSIT

LUNAR_APPROACH

LUNAR_DEPARTURE

TRANS_EARTH_RETURN

```

These are A2 MissionLab analytical labels, not official NASA phase names.

---

# Phase 1E — Public OEM Solution Comparison

Created:

```text

scripts/analysis/compare_oem_products.py

```

## Question

How do successive public NASA/JSC/FDO OEM products differ from the April 10 public OEM reference?

## Method

At common epochs:

1. April 10 OEM is used as comparison reference

2. other OEM is Hermite-interpolated to same epoch

3. calculate 3-D position difference

4. calculate 3-D velocity difference

5. separate epochs at/before creation from epochs after creation

Position difference:

$$

\Delta r=\|\mathbf r_A-\mathbf r_B\|

$$

Velocity difference:

$$

\Delta v=\|\mathbf v_A-\mathbf v_B\|

$$

## Interpretation rule

These are **solution-to-solution differences**.

They are not automatically:

- navigation errors

- prediction errors

- targeting errors

- maneuver errors

- filter corrections

## Results

| Product | Median position difference | 95th percentile | Maximum | Post-creation median |
|---|---:|---:|---:|---:|
| Apr 2 OEM v3 | 41.721 km | 177.025 km | 209.372 km | 44.418 km |
| Apr 3 OEM | 31.403 km | 164.647 km | 192.122 km | 37.940 km |
| Apr 4 OEM | 29.513 km | 156.245 km | 178.682 km | 49.605 km |
| Apr 6 Pre-OTC3 | 23.908 km | 69.932 km | 78.421 km | 28.319 km |
| Apr 7 Pre-Lunar-Flyby | 10.505 km | 65.724 km | 71.734 km | 18.902 km |
| Apr 8 Post-ICPS-Sep | 0.000 km | 38.371 km | 48.957 km | 8.731 km |
| Apr 9 Post-ICPS-Sep | 0.000 km | 26.258 km | 34.547 km | 14.435 km |
| Apr 2 post-USS-2 | 53.197 km | 175.336 km | 207.873 km | 53.297 km |

## Learnings

### Later products often look more similar to April 10

Broadly true, but not perfectly monotonic.

Example:

```text

Apr 3 post-creation median: 37.940 km

Apr 4 post-creation median: 49.605 km

```

Therefore we should not call this simple convergence.

### Zero median does not mean identical

April 8 and April 9 have median 0 km, but:

```text

Apr 8 p95 = 38.371 km

Apr 9 p95 = 26.258 km

```

So large portions match exactly/effectively exactly while other portions differ materially.

### Hypothesis, not fact

It may be that parts of trajectory history were preserved while other segments were updated.

This remains unproven.

---

# Phase 1F — Analysis Plan (Completed)

This section records the analysis plan that led to Phase 1F.1–F.4. The planned work is now complete and documented in the sections below.


Convert OEM comparison statistics into an auditable time-history analysis.

For each OEM:

- percent common epochs exactly matching April 10

- median difference before product creation

- median difference after product creation

- maximum position difference

- timestamp of maximum

- maximum velocity difference

- timestamp of maximum

- first meaningful divergence

- last meaningful divergence

- time-history plot

Then overlay NASA-reported trajectory events **after** measuring the differences.

Scientific order:

```text

measure

   ↓

visualize

   ↓

overlay documented events

   ↓

test relationships

   ↓

interpret

```

---

# Reproducibility Commands

Run from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\run_phase1.py
git diff --check
git status
```

`scripts/run_phase1.py` executes the full 13-stage Phase 1 pipeline in dependency order. It downloads the required SPICE kernels only when they are missing.

The raw NASA AROW OEM archive is intentionally not version controlled and must exist at:

```text
data/raw/arow/all-artemis-ii-oem-files.zip
```

A successful committed-state reproduction ends with:

```text
PHASE 1 PIPELINE COMPLETE
```

followed by a blank `git diff --check` and:

```text
nothing to commit, working tree clean
```

---

# Current Source Register

### NASA Artemis II flight-derived ephemeris / AROW

https://www.nasa.gov/missions/artemis/artemis-2/track-nasas-artemis-ii-mission-in-real-time/

### NASA Artemis II mission reporting

https://www.nasa.gov/blogs/missions/

### NASA Scientific Visualization Studio

https://svs.gsfc.nasa.gov/

### JPL DE440/DE441 documentation

https://ssd.jpl.nasa.gov/doc/de440_de441.html

### JPL NAIF Generic Kernels

https://naif.jpl.nasa.gov/naif/data_generic.html

### CCSDS Orbit Data Messages

https://ccsds.org/Pubs/502x0b3e1.pdf

---

# Current Open Questions

1. Why does derived Moon-relative speed at pericynthion differ by ~1.6% from NASA's public reported value?
2. What exactly distinguishes each public JSC/FDO OEM product operationally?
3. Why are large portions of the April 8/9 OEMs identical to the April 10 reference while other portions differ?
4. What physical or operational process explains the strong temporal alignment between several later OEM maxima and RTC-2? The alignment is measured, but causality is not established.
5. How should the separate high-rate `Post-RTC3 to EI` trajectory be parsed, validated, and integrated?
6. Which values should be treated as authoritative flight data versus derived analytical products?
7. Which interpolation and coordinate-frame assumptions require further validation?
8. Would a Moon-centered or B-plane analysis materially improve interpretation of the lunar-flyby solution differences?

---

# Documentation Workflow Going Forward

Before every commit or merge:

1. Record the goal.

2. Record the source data.

3. Record the mission concept.

4. Write down the math.

5. Document files/code added or changed.

6. Record exact observed output.

7. Document errors/challenges and fixes.

8. Validate against an independent source when possible.

9. Record what we learned.

10. Record unresolved questions.

11. Record interpretation limits.

12. Only then commit.

The README should stay concise. This log preserves the technical depth, learning trail, and proof behind the project.

# Phase 1F.1 — Time-Resolved OEM Evolution

Created:

scripts/analysis/analyze_oem_evolution.py

## Goal

Move beyond summary statistics and examine how the public NASA/JSC/FDO OEM products differ from the April 10 public OEM as a function of mission time.

## Analysis definitions

### Effectively identical state

A common epoch is considered effectively identical when:

position difference <= 0.000001 km

and

velocity difference <= 0.000001 m/s

The position tolerance corresponds to approximately 1 millimeter.

This is an A2 MissionLab numerical comparison tolerance, not a NASA operational tolerance.

### Meaningful difference threshold

For exploratory analysis:

position difference >= 1 km

is labeled a meaningful solution difference.

This is NOT a NASA navigation limit, flight rule, acceptable error, or mission threshold.

## Results

### April 2 OEM v3

Effectively identical epochs: 7.37%

Median difference: 41.721 km

Maximum: 209.372 km

Maximum epoch: 2026-04-06T22:58:51.667Z

### April 3 OEM

Effectively identical epochs: 17.93%

Median difference: 31.403 km

Maximum: 192.122 km

Maximum epoch: 2026-04-06T23:02:51.667Z

### April 4 OEM

Effectively identical epochs: 26.27%

Median difference: 29.513 km

Maximum: 178.682 km

Maximum epoch: 2026-04-06T23:02:51.667Z

### April 6 Pre-OTC3 OEM

Effectively identical epochs: 19.31%

Median difference: 23.908 km

Maximum: 78.421 km

Maximum epoch: 2026-04-10T02:53:28.122Z

### April 7 Pre-Lunar-Flyby OEM

Effectively identical epochs: 9.24%

Median difference: 10.505 km

Maximum: 71.734 km

Maximum epoch: 2026-04-10T02:53:28.122Z

### April 8 OEM

Effectively identical epochs: 73.24%

Median difference: 0 km

Maximum: 48.957 km

Maximum epoch: 2026-04-10T02:53:28.122Z

### April 9 OEM

Effectively identical epochs: 81.94%

Median difference: 0 km

Maximum: 34.547 km

Maximum epoch: 2026-04-10T02:53:28.122Z

## Major observations

1. Large portions of the later public OEMs are exactly or effectively identical to the April 10 reference.

2. Every product has a median difference of zero for epochs at or before its creation time.

This suggests, but does not prove, that large portions of the already-established trajectory history may have been preserved between releases while later trajectory states changed.

3. Early April 2–4 products show their largest differences around lunar pericynthion.

4. The April 6–9 products all show their largest difference at approximately 2026-04-10 02:53 UTC.

NASA publicly reports that RTC-2 began at 10:53 p.m. EDT April 9, equivalent to 02:53 UTC April 10.

This is a strong temporal alignment but NOT yet evidence that the maneuver caused the observed OEM solution differences.

## Scientific-order rule

We intentionally measured the solution differences before adding mission events.

Next:

measure -> overlay documented events -> inspect alignment -> interpret cautiously

rather than assuming maneuver causality first.

# Phase 1F.2 — Overlay of Documented Trajectory Events

Created:

data/reference/trajectory_events.json

scripts/analysis/overlay_trajectory_events.py

Generated:

docs/assets/phase1f_oem_with_events.svg

## Goal

Overlay independently measured public OEM solution differences with documented Artemis II trajectory events only after the solution-difference analysis had already been performed.

This avoids selecting events in advance and then searching for apparent confirmation.

## Events

### Outbound Correction Burn

UTC:

2026-04-06T03:03:00Z

NASA reported the burn began at 11:03 p.m. EDT on April 5 and lasted 17.5 seconds.

Provenance:

NASA_REPORTED

### Pericynthion

UTC:

2026-04-06T23:00:46.177998Z

This timestamp was independently derived by A2 MissionLab using cubic Hermite interpolation of the NASA OEM trajectory and JPL DE440 lunar geometry.

Provenance:

DERIVED

### Return Correction Burn 1

UTC:

2026-04-08T00:03:00Z

Duration:

15 seconds

Reported delta-v:

1.6 ft/s

Provenance:

NASA_REPORTED

### Return Correction Burn 2

UTC:

2026-04-10T02:53:00Z

Duration:

9 seconds

Reported delta-v:

5.3 ft/s

Provenance:

NASA_REPORTED

### Return Correction Burn 3

UTC:

2026-04-10T18:53:00Z

Duration:

8 seconds

Reported delta-v:

4.2 ft/s

Provenance:

NASA_REPORTED

## Major Observations

1. The April 2, April 3, and April 4 public OEM products reach their largest position differences from the April 10 reference around lunar pericynthion.

2. The April 6, April 7, April 8, and April 9 products reach their maximum position difference at approximately:

2026-04-10T02:53:28Z

This occurs approximately 28 seconds after the publicly reported start of RTC-2 at:

2026-04-10T02:53:00Z

This is a strong temporal alignment.

It is NOT yet proof that RTC-2 caused the solution difference.

3. RTC-1 occurs during a period where several newer OEM products begin or continue diverging from the April 10 reference.

4. By RTC-3, most public OEM differences are decreasing toward Entry Interface, although individual products retain different behavior.

## Interpretation Limits

The plotted curves represent differences between publicly released trajectory solutions.

They do not directly represent:

- navigation error;

- targeting error;

- spacecraft position uncertainty;

- Flight Dynamics Officer allowable error;

- maneuver execution error;

- trajectory-control tolerance.

No causal relationship between a maneuver and a solution change is claimed without further evidence.

## Scientific Workflow

The analysis followed:

measure solution differences

→ visualize them

→ add documented events

→ inspect temporal alignment

→ investigate possible relationships

rather than:

assume maneuver causation

→ construct analysis around that assumption.

# Phase 1F.3 — Event-Window Analysis

Created:

scripts/analysis/analyze_event_windows.py

Generated:

data/processed/trajectory/event_window_analysis.json

## Goal

Quantify public OEM solution behavior within ±30 minutes of documented trajectory events rather than relying only on visual inspection of the time-history plot.

For each event and each public OEM product, the analysis records:

- nearest state approximately 30 minutes before;

- nearest state at the event;

- nearest state approximately 30 minutes after;

- net change in 3-D position difference across the window.

The analysis measures temporal behavior only.

It does not establish causal relationships between maneuvers and trajectory-solution differences.

## OTC

Early OEM products showed large absolute differences from the April 10 reference around OTC:

approximately 166–186 km.

However, their net changes across the ±30 minute window were only approximately +1.6 to +1.9 km.

Later public OEM products were effectively identical to the April 10 reference during this interval.

### Interpretation

No obvious discontinuous solution change is visible in the 3-D position-difference magnitude at OTC.

## Pericynthion

The April 2–4 products reached approximately:

- 209 km;

- 192 km;

- 179 km;

respectively around lunar closest approach.

The curves remained relatively smooth across the ±30 minute window.

### Interpretation

The early trajectory products have their greatest separation from the April 10 reference near lunar flyby geometry.

This does not imply that pericynthion itself caused a trajectory-solution change.

## RTC-1

Differences changed only modestly during the ±30 minute interval.

No strong step-like behavior is visible in the position-difference magnitude.

## RTC-2

Several later OEM products reach their absolute maximum position difference almost exactly at RTC-2.

Examples:

April 6 product:

~78.42 km

April 7 product:

~71.73 km

April 8 product:

~48.96 km

April 9 product:

~34.55 km

However, the local windows show smooth behavior.

Example:

April 8:

48.13 km

→ 48.96 km at RTC-2

→ 47.66 km

April 9:

33.83 km

→ 34.55 km at RTC-2

→ 33.68 km

### Interpretation

The maxima are strongly temporally aligned with RTC-2.

The current analysis does NOT demonstrate a discontinuity caused by the burn.

Therefore:

SUPPORTED:

The maximum public OEM solution difference is temporally aligned with RTC-2.

NOT YET SUPPORTED:

RTC-2 caused the observed solution difference.

## RTC-3

Several later OEM differences decrease across the event window.

Examples:

April 7:

3.96 km

→ 2.11 km

→ 1.89 km

April 8:

3.32 km

→ 1.99 km

→ 1.77 km

April 9:

2.80 km

→ 1.99 km

→ 1.77 km

The behavior is interesting but does not establish that RTC-3 caused solution convergence.

## Key Learning

A scalar 3-D position-difference magnitude is insufficient for diagnosing maneuver effects.

A maneuver primarily changes spacecraft velocity, while resulting position differences evolve afterward.

Additionally, the magnitude removes directional information.

The next analysis should therefore decompose position and velocity differences into a physically meaningful spacecraft-centered frame such as RTN:

R — radial

T — transverse / along-track

N — normal / cross-track

This will help determine whether public trajectory-solution differences primarily reflect:

- radial separation;

- along-track timing/trajectory separation;

- cross-track separation;

- velocity-state differences.

# Phase 1F.4 — RTN State-Residual Decomposition

Created:

scripts/analysis/analyze_rtn_residuals.py

Generated:

data/processed/trajectory/oem_rtn_residuals.csv

data/processed/trajectory/oem_rtn_summary.json

docs/assets/rtn/

## Goal

Decompose public OEM state differences into physically meaningful

Earth-centered radial, transverse/along-track, and normal/cross-track

components rather than relying only on scalar 3-D differences.

## Reference Frame

The RTN basis is constructed from the April 10 public OEM reference state.

R:

Earth-centered radial direction.

T:

Transverse / local along-track direction.

N:

Normal / cross-track direction defined by the reference trajectory's

specific angular momentum vector.

For reference state r and v:

R_hat = r / |r|

N_hat = (r x v) / |r x v|

T_hat = N_hat x R_hat

For another OEM:

delta_r = r_comparison - r_reference

delta_R = delta_r dot R_hat

delta_T = delta_r dot T_hat

delta_N = delta_r dot N_hat

The same basis is used to project inertial velocity-state differences.

The velocity quantities are called delta-v_R, delta-v_T, and delta-v_N.

They are NOT derivatives of rotating-frame RTN coordinates.

## Major Results

### Early OEM products

April 2:

R position RMS: 26.777 km

T position RMS: 74.239 km

N position RMS: 39.647 km

Dominant RMS position axis: T

April 3:

R: 24.811 km

T: 67.294 km

N: 36.438 km

Dominant axis: T

April 4:

R: 22.281 km

T: 62.741 km

N: 35.809 km

Dominant axis: T

### Interpretation

The large early public OEM differences around lunar flyby are primarily

along-track rather than simply radial Earth-distance differences.

### Later OEM products

April 8:

R RMS: 3.319 km

T RMS: 12.112 km

N RMS: 3.644 km

April 9:

R RMS: 2.435 km

T RMS: 7.593 km

N RMS: 3.631 km

The largest RMS component remains along-track.

Near RTC-2, the later OEMs show predominantly negative along-track

separation from the April 10 reference, with smaller radial and

cross-track components.

This establishes the geometry of the public solution difference but

does not establish its internal navigation or targeting cause.

## Frequency vs Magnitude

April 8 and April 9 provide an important statistical example.

April 9:

R is the largest position component at 83.3% of common epochs.

T is the largest at only 15.6%.

However:

T RMS = 7.593 km

R RMS = 2.435 km

Therefore R dominates more frequently, but generally at smaller

amplitudes, while less-frequent T excursions are much larger.

Dominant-component frequency and RMS magnitude answer different

questions.

## Position vs Velocity

The earliest OEMs have along-track-dominated position residuals but

radial-dominated velocity RMS.

This demonstrates that the dominant instantaneous velocity-state

difference does not need to match the accumulated position-difference

direction.

Small velocity differences integrated over long mission intervals can

produce much larger position separation.

## Entry Interface Warning

Several products show large velocity-residual spikes near the terminal

end of the OEM trajectory.

These values will not be interpreted yet.

NASA also released a separate high-rate Post-RTC3-to-Entry-Interface

trajectory product, and entry dynamics will be analyzed separately.

## Lunar Flyby Frame Limitation

This RTN frame is Earth-centered.

Near lunar closest approach, the Earth-centered RTN basis changes

rapidly and does not provide the most natural frame for detailed lunar

targeting analysis.

Future advanced lunar-flyby analysis may use Moon-centered geometry

and B-plane targeting quantities.

## Interpretation Limits

RTN residuals are public solution-to-solution differences.

They are NOT:

- navigation errors;

- spacecraft-state uncertainty;

- FDO tolerances;

- flight-rule limits;

- maneuver execution error.

The April 10 public OEM remains a comparison reference, not a proven

absolute truth trajectory.

## RTN Validation

Created:

scripts/validation/validate_rtn_residuals.py

The RTN decomposition was validated against both its reconstructed vector

magnitudes and the independent scalar residuals produced during Phase 1E.

Results:

Rows checked:

23,188

Missing Phase 1E comparison rows:

0

Maximum position norm reconstruction error:

8.526512829121e-14 km

Maximum velocity norm reconstruction error:

2.220446049250e-16 m/s

Maximum RTN position norm versus Phase 1E scalar difference:

2.842170943040e-14 km

Maximum RTN velocity norm versus Phase 1E scalar difference:

7.105427357601e-15 m/s

Result:

OK: RTN decomposition preserves position and velocity residual magnitudes.

The remaining numerical differences are at floating-point roundoff scale

and are many orders of magnitude below the validation tolerances.

This validates the internal consistency of the RTN transformation and its

agreement with the earlier Phase 1E state-difference calculation.

It does not establish that the April 10 public OEM is an absolute truth

trajectory, nor does it turn solution-to-solution differences into

navigation error.

# Phase 1 Closure — Full Reproducibility Run

A complete Phase 1 reconstruction was executed through:

scripts/run_phase1.py

## Purpose

Verify that the complete Artemis II mission-backbone analysis can be

regenerated in dependency order from the retained source inputs rather

than relying on manually created intermediate files.

## Pipeline

The reproducibility runner executed 13 stages:

1. Validate Phase 0 foundation data.

2. Parse NASA Artemis II OEM products.

3. Validate parsed trajectory products.

4. Build the April 10 primary trajectory.

5. Add JPL SPICE lunar geometry.

6. Refine lunar closest approach.

7. Classify geometric mission phases.

8. Compare public NASA OEM products.

9. Analyze time-resolved OEM evolution.

10. Overlay documented trajectory events.

11. Analyze trajectory-event windows.

12. Decompose OEM residuals into the Earth-centered RTN frame.

13. Validate the RTN residual decomposition.

## Result

PHASE 1 PIPELINE COMPLETE

13 stages completed successfully.

Total runtime during the closure run:

15.94 seconds

The complete mission backbone was regenerated and validated successfully.

## Validation Highlights

Nine public CCSDS OEM trajectory products were parsed and validated.

Primary April 10 OEM:

3,262 states.

Maximum Earth-center distance:

413,144.4 km

2026-04-06T23:02:51.667 UTC

Refined pericynthion:

2026-04-06T23:00:46.177998 UTC

Moon-center distance:

8,281.938 km

Mean-radius lunar altitude:

6,544.538 km

Derived lunar SOI entry:

2026-04-06T04:38:07.532302 UTC

Derived lunar SOI exit:

2026-04-07T17:23:41.922211 UTC

RTN validation:

23,188 residual records checked.

Missing Phase 1E comparison rows:

0

Maximum position magnitude consistency errors were approximately

1e-14 km, consistent with floating-point roundoff.

## Reproducibility Decisions

Raw NASA trajectory data and generated processed datasets remain outside

Git.

Source code, reference event data, configuration, documentation, and

selected deterministic SVG figures remain version controlled.

Matplotlib SVG generation was made deterministic by:

- fixing the SVG hash salt;

- removing generation-date metadata;

- normalizing trailing whitespace after SVG generation.

This allows repeated analysis runs to reproduce the committed figures

without timestamp- or random-ID-driven Git changes.

## Final Committed-State Reproducibility Proof

After the Phase 1 closure changes were committed and pushed, the entire pipeline was rerun from the committed state:

```powershell
.\.venv\Scripts\python.exe scripts\run_phase1.py
```

Observed:

```text
PHASE 1 PIPELINE COMPLETE
Completed 13 steps in 15.89 seconds.
Mission backbone regenerated and validated successfully.
```

The final RTN validator again checked 23,188 residual records with zero missing scalar-comparison rows.

After the complete rerun:

```powershell
git diff --check
git status
```

produced no diff-check errors and:

```text
nothing to commit, working tree clean
```

This is the strongest Phase 1 reproducibility proof: the committed pipeline regenerates the committed analytical figures and leaves no repository changes.

## Merge and Archive Record

Phase 1 was merged into `main` with a non-fast-forward merge:

```text
Merge Phase 1 mission backbone
```

The merge was pushed to GitHub as commit:

```text
afc1a15
```

The completed feature branch `phase-1-mission-backbone` is intentionally retained as a historical development branch.

An annotated milestone tag was created and pushed:

```text
phase-1-complete
```

The tag marks the completed Phase 1 state on `main`.

## Explicit Phase Boundary

The separate high-rate Post-RTC3-to-Entry-Interface trajectory product

remains outside Phase 1.

It is intentionally reserved for the dedicated entry/reentry analysis.

## Phase 1 Status

COMPLETE

The project now has a validated temporal and geometric mission backbone

capable of supporting later Artemis II engineering subsystems.

# Phase 2 — Entry, Reentry, and Recovery Reconstruction

Phase 2 begins with the separate high-rate trajectory product that was intentionally excluded from the Phase 1 mission-backbone analysis.

The purpose of this phase is to reconstruct the Artemis II atmospheric-entry and recovery portion of the mission using public NASA data while preserving strict distinctions between source data, derived quantities, models, and interpretation.

---

# Phase 2A — High-Rate Entry Trajectory Ingestion

## Goal

Understand, parse, and validate the separate NASA Artemis II high-rate trajectory product:

```text
2026.04.10 - Post-RTC3 to EI.zip
```

before performing entry-dynamics analysis.

Unlike the Phase 1 CCSDS OEM trajectory products, this file uses a different trajectory format, coordinate-frame label, unit system, and sampling cadence.

No parser was written until the raw format had first been inspected.

## Source archive

The product is contained inside:

```text
data/raw/arow/all-artemis-ii-oem-files.zip
```

Nested archive:

```text
2026.04.10 - Post-RTC3 to EI.zip
```

Nested trajectory file:

```text
2026.04.10 - Post-RTC3 to EI
```

Observed source-file size:

```text
98,357 bytes
```

Observed line count:

```text
821
```

The file contains:

```text
2 header lines
819 trajectory records
```

Raw source data remain outside Git under:

```text
/data/raw/
```

Generated processed data remain outside Git under:

```text
/data/processed/
```

---

## Raw format inspection

The first two source lines are:

```text
PROP_MAN 11.0
2026   7857312.084    782298.782       817.975  M50 FT FPS SEC
```

The source therefore directly declares:

```text
format identifier: PROP_MAN
format version:    11.0
year:              2026
reference value:   7857312.084
start offset:      782298.782
duration:          817.975
frame label:       M50
position units:    FT
velocity units:    FPS
time units:        SEC
```

The exact operational meaning of `PROP_MAN 11.0` has not yet been established from authoritative documentation.

The frame label `M50` is preserved exactly as supplied by the source.

No M50-to-EME2000/J2000 transformation is performed in Phase 2A.

---

## Record structure

Inspection showed that each trajectory row contains eight numeric fields:

```text
time
x
y
z
vx
vy
vz
auxiliary scalar
```

The first source state is:

```text
8639610.866
12738551.496674
15710657.850539
6736409.861772
-29308.691241
10998.064485
17957.749576
22855.0
```

The first seven fields are interpreted structurally using the source header as:

```text
time     seconds
x y z    feet
vx vy vz feet per second
```

The eighth numeric field is currently stored as:

```text
auxiliary_scalar_raw
```

Its physical meaning and units remain unresolved.

No mass, weight, propellant, or other physical interpretation is assigned without supporting documentation.

---

## Time reconstruction

The source header contains:

```text
year = 2026

reference epoch seconds of year =
7857312.084

start offset =
782298.782 seconds
```

The reference value converts to:

```text
2026-04-01T22:35:12.084000Z
```

The first trajectory time satisfies:

```text
7857312.084
+
782298.782
=
8639610.866
```

exactly.

Therefore the first state occurs at:

```text
2026-04-10T23:53:30.866000Z
```

The final state occurs at:

```text
2026-04-11T00:07:08.841000Z
```

Observed trajectory duration:

```text
817.975 seconds
```

Header duration:

```text
817.975 seconds
```

Difference:

```text
approximately 0 seconds
```

This exact agreement strongly supports the reconstructed timing relationship.

### Phase 1 epoch distinction

The Phase 1 project mission epoch is:

```text
2026-04-01T22:35:12Z
```

The high-rate trajectory header reconstructs a reference epoch of:

```text
2026-04-01T22:35:12.084Z
```

The values differ by:

```text
0.084 seconds
```

The Phase 2 source value is preserved as supplied.

The two epochs will not be silently forced to match.

---

## Sampling cadence

There are:

```text
819 states
818 time intervals
```

Observed cadence:

```text
minimum: 0.975 s
maximum: 1.000 s
median:  1.000 s
```

All non-terminal intervals are:

```text
1.000 seconds
```

The final interval is:

```text
0.975 seconds
```

This final fractional interval allows the record span to terminate exactly at the header duration of:

```text
817.975 seconds
```

---

## Parser

Created:

```text
scripts/ingestion/parse_entry_trajectory.py
```

The parser:

1. opens the existing NASA AROW archive;
2. locates the nested high-rate trajectory ZIP;
3. verifies that it contains one trajectory file;
4. parses the two-line header;
5. extracts eight numeric fields from every state record;
6. preserves the original raw state values;
7. converts feet to kilometers;
8. converts feet per second to kilometers per second;
9. reconstructs UTC timestamps;
10. derives Earth-center distance;
11. derives inertial speed;
12. preserves the unidentified eighth field without assigning physical meaning;
13. writes processed CSV and metadata products.

Generated files:

```text
data/processed/entry/entry_trajectory_m50.csv
data/processed/entry/entry_trajectory_metadata.json
```

These generated products remain ignored by Git.

---

## Numeric parsing challenge

Near the end of the source file, some adjacent numeric fields appear without whitespace between them.

Example:

```text
11112442.914583-1294.795611
```

A parser based only on whitespace splitting could therefore interpret this incorrectly as one token.

The parser instead extracts signed numeric values using a numeric regular expression.

This preserves eight numeric fields per trajectory record even when adjacent signed values are not separated by whitespace.

---

## Derived unit conversions

Exact conversion used:

\[
1\ \mathrm{ft}
=
0.0003048\ \mathrm{km}
\]

Therefore:

\[
x_{km}
=
x_{ft}(0.0003048)
\]

and similarly for the remaining position components.

Velocity conversion:

\[
v_{km/s}
=
v_{ft/s}(0.0003048)
\]

Earth-center distance:

\[
r
=
\sqrt{x^2+y^2+z^2}
\]

Inertial speed:

\[
v
=
\sqrt{v_x^2+v_y^2+v_z^2}
\]

These magnitudes are invariant to axis rotation, so they can be examined before the M50 frame is transformed into the Phase 1 EME2000/J2000 frame.

---

## Parsed result

Observed parser output:

```text
Artemis II High-Rate Entry Trajectory Parser
--------------------------------
Source: 2026.04.10 - Post-RTC3 to EI
Format: PROP_MAN 11.0
Frame: M50
Units: FT FPS SEC

Records: 819
Start:   2026-04-10T23:53:30.866000Z
Stop:    2026-04-11T00:07:08.841000Z
Duration: 817.975 s

First Earth-center distance: 6497.852 km
First inertial speed:        11.000019 km/s

Last Earth-center distance:  6372.054 km
Last inertial speed:         0.398304 km/s

Auxiliary scalar: UNRESOLVED
```

The trajectory therefore spans a region where inertial speed falls from approximately:

```text
11.000 km/s
```

to:

```text
0.398 km/s
```

during approximately:

```text
13 minutes 38 seconds
```

This strongly indicates that the source contains substantial atmospheric-entry dynamics.

However, the exact mission-event meaning of the archive name `Post-RTC3 to EI` is not inferred from the filename alone.

---

## Validator

Created:

```text
scripts/validation/validate_entry_trajectory.py
```

The validator independently rereads the raw NASA source rather than trusting only the parser output.

It checks:

### Source structure

- `PROP_MAN 11.0` header;
- `M50 FT FPS SEC` declaration;
- eight numeric fields per state;
- finite raw numeric values;
- exactly 819 records.

### Raw-state preservation

Every source value is compared against the preserved processed representation.

This includes:

```text
time
x
y
z
vx
vy
vz
auxiliary scalar
```

### Timing

The validator checks:

```text
first time =
reference epoch + start offset
```

and:

```text
last time - first time =
header duration
```

It also verifies strict temporal monotonicity.

### Cadence

Expected:

```text
817 intervals of 1.000 s
1 final interval of 0.975 s
```

### Unit conversion

Every raw position and velocity component is independently converted and compared with the processed values.

### Derived magnitudes

Earth-center distance is independently reconstructed from:

```text
x, y, z
```

and inertial speed is independently reconstructed from:

```text
vx, vy, vz
```

---

## Initial validator failure

The first validator implementation attempted to convert every CSV field to a floating-point value.

The processed CSV also contains a UTC timestamp such as:

```text
2026-04-10T23:53:30.866000Z
```

This caused:

```text
ValueError:
could not convert string to float:
'2026-04-10T23:53:30.866000Z'
```

The validator was corrected to define the numeric columns explicitly and validate `timestamp_utc` separately as an ISO timestamp.

### Learning

Schemas containing mixed numeric and textual fields should validate each field according to its intended data type rather than attempting blanket numeric conversion.

---

## Final validation result

Observed:

```text
Artemis II Entry Trajectory Validation
--------------------------------
Records checked: 819

Start: 2026-04-10T23:53:30.866000Z
Stop:  2026-04-11T00:07:08.841000Z
Duration: 817.975 s

Cadence:
  Regular intervals: 1.000 s
  Terminal interval: 0.975 s

Earth-center distance:
  First: 6497.852 km
  Last:  6372.054 km

Inertial speed:
  First: 11.000019 km/s
  Last:  0.398304 km/s

Auxiliary scalar (meaning unresolved):
  First: 22855.000
  Last:  20476.300

Maximum raw-to-km position conversion error:
  0.000000000000e+00 km

Maximum raw-to-km/s velocity conversion error:
  0.000000000000e+00 km/s

Maximum radius reconstruction error:
  9.094947017729e-13 km

Maximum speed reconstruction error:
  1.776356839400e-15 km/s

OK: high-rate entry trajectory structure, timing, units, raw-state preservation, and numeric conversion validated.
```

The position and velocity conversion comparisons reproduced exactly to stored floating-point precision.

The remaining radius and speed reconstruction differences are approximately:

```text
1e-13 km
1e-15 km/s
```

respectively.

These are consistent with floating-point roundoff.

---

## Auxiliary scalar behavior

Observed:

```text
first:   22855.0
last:    20476.3
minimum: 20476.3
maximum: 22855.0
net change: -2378.7
```

The field changes substantially throughout the entry trajectory.

Its physical interpretation remains:

```text
UNRESOLVED
```

No units or physical meaning are assigned in Phase 2A.

---

## Interpretation limits

Phase 2A establishes the file structure and internal consistency of the high-rate trajectory.

It does NOT yet establish:

- geodetic altitude;
- latitude or longitude;
- ground track;
- flight-path angle;
- atmospheric density;
- aerodynamic acceleration;
- lift or drag;
- bank angle;
- heating rate;
- heat-shield temperature;
- dynamic pressure;
- g-load;
- landing location;
- exact Entry Interface event time;
- physical meaning of the eighth field;
- exact operational meaning of `PROP_MAN 11.0`;
- equivalence between the M50 source coordinates and Phase 1 EME2000 coordinates.

Earth-center distance is not Earth altitude.

The high-rate trajectory will not be directly subtracted from the Phase 1 EME2000 trajectory until the coordinate-frame relationship is explicitly handled.

---

## Phase 2A status

The high-rate entry trajectory has now been:

```text
inspected
→ structurally understood
→ parsed
→ unit converted
→ time reconstructed
→ independently validated
```

Phase 2A ingestion status:

```text
COMPLETE
```

The next engineering problem is to connect this high-rate M50 trajectory to the Phase 1 mission backbone and determine a defensible Earth/entry geometry before calculating atmospheric-entry quantities.

---

# Phase 2B — Entry Frame Handoff and Geometry

# Phase 2B.1 — M50 to J2000 Frame Reconstruction

## Goal

Connect the separate high-rate Phase 2 trajectory to the Phase 1 Artemis II mission backbone in a common inertial coordinate system.

The Phase 1 NASA CCSDS OEM products use:

```text
EME2000
```

The high-rate entry product declares:

```text
M50
```

Direct subtraction of state-vector components from these differently labeled frames would therefore be invalid without first establishing an appropriate coordinate transformation.

---

## Frame question

The high-rate source provides the frame label:

```text
M50
```

Legacy NASA documentation describes M50 / Mean-of-1950 as an Earth-centered inertial reference associated with the mean equator/equinox of the 1950 epoch.

SPICE provides the built-in inertial frame:

```text
B1950
```

and an inertial transformation:

```text
B1950 -> J2000
```

A2 MissionLab therefore tested the following analysis mapping:

```text
NASA source label M50
        ↓
SPICE B1950 analysis proxy
        ↓
SPICE J2000
        ↓
Phase 1 EME2000-compatible analysis frame
```

Important qualification:

The source file itself does not explicitly state:

```text
M50 = SPICE B1950
```

Therefore A2 MissionLab treats B1950 as an analysis representation of the M50 source frame rather than claiming explicit file-level equivalence.

The mapping was tested empirically against the actual Artemis II Phase 1 / Phase 2 trajectory handoff before being adopted.

---

## Initial empirical experiment

The final Phase 1 April 10 OEM state occurs at:

```text
2026-04-10T23:53:16.723Z
```

The first high-rate Phase 2 state occurs at:

```text
2026-04-10T23:53:30.866Z
```

Gap:

```text
14.143000 seconds
```

Because the two datasets do not contain a state at the exact same epoch, the final Phase 1 state was propagated across the short gap using a simple Earth two-body model.

This propagation was used only as a comparison tool.

It is not considered atmospheric-entry flight truth.

Two hypotheses were tested.

### Hypothesis A

Treat the M50 coordinates numerically as though they were already J2000 coordinates.

Result:

```text
Position difference:
78.386809 km

Velocity difference:
125.656974 m/s
```

### Hypothesis B

Represent M50 using SPICE B1950 and transform:

```text
B1950 -> J2000
```

Result:

```text
Position difference:
0.836950 km

Velocity difference:
0.734918 m/s
```

Improvement:

```text
Position:
93.658x

Velocity:
170.981x
```

This very large improvement provides independent mission-data evidence supporting the B1950 analysis representation.

---

## SPICE transformation

Created:

```text
scripts/processing/transform_entry_to_j2000.py
```

The transformation is generated using:

```python
spice.sxform(
    "B1950",
    "J2000",
    et,
)
```

The complete six-dimensional state is transformed:

\[
\mathbf{x}_{J2000}
=
\mathbf{X}_{B1950\rightarrow J2000}
\mathbf{x}_{M50}
\]

where the state contains:

\[
\mathbf{x}
=
\begin{bmatrix}
\mathbf{r} \\
\mathbf{v}
\end{bmatrix}
\]

For these two inertial frames, the SPICE state transformation is effectively constant over the trajectory interval.

Observed maximum transform-time variation:

```text
0.000000000000e+00
```

---

## Rotation diagnostics

Observed B1950-to-J2000 rotation matrix at the first trajectory epoch:

```text
+0.999925707952 -0.011178938138 -0.004859003815
+0.011178938126 +0.999937513350 -0.000027162595
+0.004859003841 -0.000027157926 +0.999988194602
```

Rotation determinant:

```text
1.000000000000000
```

Orthogonality error:

```text
1.570178345518e-16
```

These values are consistent with a proper rigid coordinate rotation.

---

## Magnitude preservation

A pure inertial-axis rotation should preserve vector magnitudes.

Across all 819 states:

Maximum Earth-center radius preservation error:

```text
1.818989403546e-12 km
```

Maximum inertial-speed preservation error:

```text
1.776356839400e-15 km/s
```

These differences are consistent with floating-point roundoff.

The transformation therefore changes coordinate representation without changing physical vector magnitudes.

---

## First transformed state

First Phase 2 J2000 state:

```text
UTC:
2026-04-10T23:53:30.866000Z
```

Position:

```text
x = 3818.913696 km
y = 4831.658097 km
z = 2071.969543 km
```

Velocity:

```text
vx = -8.996695431 km/s
vy =  3.251987226 km/s
vz =  5.429959529 km/s
```

The corresponding invariant quantities remain:

```text
Earth-center distance:
6497.851920 km

Inertial speed:
11.000019 km/s
```

---

## Generated products

The processing step writes:

```text
data/processed/entry/entry_trajectory_j2000.csv
data/processed/entry/entry_frame_transform_metadata.json
```

These are generated analysis products and remain outside Git under:

```text
/data/processed/
```

---

## Independent validator

Created:

```text
scripts/validation/validate_entry_frame_transform.py
```

The validator independently:

- reloads all 819 M50 states;
- recalculates the SPICE B1950-to-J2000 transformation;
- compares every reconstructed transformed state with the stored processed state;
- checks rotation-matrix orthogonality;
- checks rotation determinant;
- checks radius preservation;
- checks speed preservation;
- independently reconstructs the Phase 1-to-Phase 2 handoff comparison;
- requires the transformed trajectory to improve both position and velocity continuity substantially.

Observed stored transform errors:

```text
Maximum position transform error:
0.000000000000e+00 km

Maximum velocity transform error:
0.000000000000e+00 km/s
```

---

## Final handoff validation

Observed:

```text
Phase 1 -> Phase 2 gap:
14.143000 s
```

Without frame transformation:

```text
Position difference:
78.386809 km

Velocity difference:
125.656974 m/s
```

With SPICE B1950 -> J2000:

```text
Position difference:
0.836950 km

Velocity difference:
0.734918 m/s
```

Improvement:

```text
Position:
93.658x

Velocity:
170.981x
```

Result:

```text
OK: entry frame transformation and empirical handoff continuity validated.
```

---

## Interpretation

The approximately two-orders-of-magnitude improvement is strong evidence that representing the M50 source coordinates using SPICE B1950 is appropriate for this analysis.

The result is supported by two independent lines of evidence:

```text
legacy reference-frame definitions
+
actual Artemis II trajectory continuity
```

This is significantly stronger than adopting a frame mapping based only on naming similarity.

---

## Important interpretation limits

The remaining transformed handoff difference:

```text
0.836950 km
0.734918 m/s
```

is NOT interpreted as:

```text
navigation error
trajectory error
state-estimation error
targeting error
maneuver error
spacecraft uncertainty
```

The Phase 1 state and Phase 2 state are separated by:

```text
14.143 seconds
```

and the handoff comparison propagates the final Phase 1 state using a simple two-body Earth model.

During this portion of the mission, atmospheric and other forces may already be relevant.

Therefore the residual represents disagreement between:

```text
short two-body propagated Phase 1 state
```

and:

```text
first transformed high-rate Phase 2 state
```

under the analysis assumptions.

It should not be promoted into an operational error quantity.

---

## EME2000 / J2000 qualification

Phase 1 NASA OEM states are labeled:

```text
EME2000
```

The Phase 2 transformed trajectory is represented as:

```text
J2000
```

For the current mission-scale inertial analysis, A2 MissionLab treats these as compatible realizations for state comparison.

Any future analysis requiring higher-precision reference-frame distinctions must explicitly revisit this assumption.

---

## Phase 2B.1 status

The high-rate trajectory has now been:

```text
M50 source state
→ represented using SPICE B1950
→ transformed to J2000
→ checked for magnitude preservation
→ independently reconstructed
→ empirically compared with Phase 1
```

Status:

```text
COMPLETE
```

The next step is Earth-fixed and geodetic reconstruction so that physically meaningful entry quantities such as altitude, latitude, longitude, radial motion, flight-path geometry, and ground track can be derived.

---

# Phase 2B.2 — Earth-Fixed and Geodetic Entry Reconstruction

## Goal

Transform the high-rate Artemis II entry trajectory from its inertial J2000 representation into an Earth-fixed frame and derive physically meaningful entry geometry.

Phase 2B.1 established the analysis chain:

```text
M50 source state
→ SPICE B1950 analysis proxy
→ J2000
```

Phase 2B.2 extends the chain:

```text
J2000
→ ITRF93
→ WGS 84 geodetic coordinates
→ local Earth-relative flight geometry
```

This makes it possible to derive:

```text
latitude
longitude
geodetic altitude
Earth-relative velocity
east / north / vertical velocity
horizontal speed
flight-path angle
heading
ground-track geometry
```

from the public trajectory.

---

## Earth-orientation source

High-precision Earth orientation is supplied by the NAIF binary Earth PCK:

```text
earth_1962_260806_2126_combined.bpc
```

Local source path:

```text
data/raw/spice/earth_1962_260806_2126_combined.bpc
```

Observed file size:

```text
31,318,016 bytes
```

Pinned SHA-256:

```text
CC87AD1A495CF598800BA403763D350F087AC0B97DA9FEC603278A3864C6A53E
```

The kernel is downloaded from the official JPL/NAIF generic-kernel archive.

It remains outside Git under:

```text
/data/raw/
```

A dedicated downloader verifies the exact pinned artifact before use.

Created:

```text
scripts/ingestion/download_entry_earth_kernel.py
```

The downloader:

1. creates the local SPICE raw-data directory if required;
2. detects whether the exact kernel is already present;
3. calculates SHA-256;
4. accepts the existing file only if the hash matches the pinned value;
5. otherwise downloads the kernel from NAIF;
6. validates the downloaded file against the pinned SHA-256;
7. deletes a newly downloaded file if hash verification fails.

This avoids silently using a moving or altered Earth-orientation product.

---

## Earth-fixed frame

The inertial Phase 2B.1 state is represented in:

```text
J2000
```

Earth-fixed coordinates are reconstructed using:

```python
spice.sxform(
    "J2000",
    "ITRF93",
    et,
)
```

The full six-dimensional state is transformed:

\[
\mathbf{x}_{ITRF93}
=
\mathbf{X}_{J2000\rightarrow ITRF93}(t)
\mathbf{x}_{J2000}
\]

Unlike the B1950-to-J2000 transformation from Phase 2B.1, the J2000-to-ITRF93 transformation is time dependent because the Earth-fixed frame rotates relative to inertial space.

The SPICE state transformation therefore handles both:

```text
position rotation
+
velocity transformation associated with Earth rotation
```

This is important because Earth-relative velocity cannot be obtained merely by rotating the inertial velocity vector with a static 3x3 matrix.

---

## Geodetic model

A2 MissionLab uses the WGS 84 reference ellipsoid:

```text
semi-major axis:
6378.137000 km

inverse flattening:
298.257223563
```

Geodetic coordinates are derived using:

```python
spice.recgeo(...)
```

The resulting quantities are:

```text
geodetic longitude
geodetic latitude
ellipsoidal altitude
```

Important distinction:

```text
Earth-center distance != altitude
```

and:

```text
WGS84 ellipsoidal altitude
!= necessarily local mean sea-level height
```

The project therefore explicitly labels the derived altitude:

```text
WGS84 geodetic altitude
```

rather than generic “height above Earth.”

---

## Local Earth-relative frame

The Earth-fixed ITRF93 velocity is decomposed into a local geodetic East-North-Up basis.

For geodetic longitude \(\lambda\) and latitude \(\phi\):

\[
\hat{\mathbf e}
=
\begin{bmatrix}
-\sin\lambda \\
\cos\lambda \\
0
\end{bmatrix}
\]

\[
\hat{\mathbf n}
=
\begin{bmatrix}
-\sin\phi\cos\lambda \\
-\sin\phi\sin\lambda \\
\cos\phi
\end{bmatrix}
\]

\[
\hat{\mathbf u}
=
\begin{bmatrix}
\cos\phi\cos\lambda \\
\cos\phi\sin\lambda \\
\sin\phi
\end{bmatrix}
\]

Velocity components are:

\[
v_E
=
\mathbf v_{ITRF93}
\cdot
\hat{\mathbf e}
\]

\[
v_N
=
\mathbf v_{ITRF93}
\cdot
\hat{\mathbf n}
\]

\[
v_U
=
\mathbf v_{ITRF93}
\cdot
\hat{\mathbf u}
\]

where:

```text
v_E = east velocity
v_N = north velocity
v_U = vertical / up velocity
```

Negative vertical velocity indicates descent relative to the local geodetic surface normal.

---

## Earth-relative speed

Earth-relative speed is:

\[
v_{ER}
=
\left\|
\mathbf v_{ITRF93}
\right\|
\]

This differs from the inertial speed derived earlier because ITRF93 rotates with Earth.

At Entry Interface:

```text
inertial speed:
approximately 11.000019 km/s

Earth-relative speed:
10.632214 km/s
```

The distinction is physically meaningful and must be maintained throughout entry analysis.

---

## Horizontal speed

Local horizontal speed is:

\[
v_H
=
\sqrt{
v_E^2+v_N^2
}
\]

Vertical velocity is:

\[
v_V=v_U
\]

---

## Earth-relative flight-path angle

Flight-path angle is derived as:

\[
\gamma
=
\tan^{-1}
\left(
\frac{v_U}{v_H}
\right)
\]

implemented using `atan2` so that the sign and quadrant remain well defined.

Interpretation:

```text
gamma < 0
descending

gamma = 0
locally horizontal

gamma > 0
ascending
```

---

## Heading

Heading is calculated clockwise from local geodetic north:

\[
\chi
=
\tan^{-1}
\left(
\frac{v_E}{v_N}
\right)
\]

and normalized to:

```text
0 <= heading < 360 degrees
```

Interpretation:

```text
0 deg   north
90 deg  east
180 deg south
270 deg west
```

Heading becomes increasingly poorly conditioned as horizontal velocity approaches zero.

Terminal-state heading should therefore not be over-interpreted.

---

## Processing implementation

Created:

```text
scripts/processing/build_entry_geometry.py
```

The processing step:

1. loads the Phase 2B.1 J2000 trajectory;
2. loads the leap-second kernel;
3. loads the pinned high-precision Earth-orientation PCK;
4. transforms each J2000 state to ITRF93;
5. derives WGS 84 geodetic coordinates;
6. derives Earth-relative speed;
7. constructs the local ENU basis;
8. decomposes Earth-relative velocity;
9. calculates horizontal speed;
10. calculates vertical velocity;
11. calculates Earth-relative flight-path angle;
12. calculates heading;
13. compares altitude with the Entry Interface reference;
14. preserves all earlier trajectory quantities.

Generated:

```text
data/processed/entry/entry_geometry.csv
data/processed/entry/entry_geometry_metadata.json
```

These generated products remain ignored by Git.

---

## Entry Interface reference

The Orion Entry Interface reference altitude used for this analysis is:

```text
400,000 ft
```

Exact conversion:

\[
400000\ \mathrm{ft}
\times
0.3048\ \frac{\mathrm m}{\mathrm{ft}}
=
121920\ \mathrm m
\]

Therefore:

```text
121.920000 km
```

The comparison is performed after reconstructing WGS 84 altitude from the public trajectory.

The analysis does not alter the trajectory to force the Entry Interface condition.

---

## Reconstructed Entry Interface state

The first high-rate trajectory record occurs at:

```text
2026-04-10T23:53:30.866000Z
```

Derived WGS 84 geodetic position:

```text
Latitude:
18.802121 deg

Longitude:
-145.547425 deg

Altitude:
121.919907 km
```

Entry Interface reference:

```text
121.920000 km
```

Difference:

```text
-0.000092549 km
```

or approximately:

```text
-0.093 m
```

Therefore the first state reproduces the 400,000-ft Entry Interface reference to approximately nine centimeters.

This result was derived from:

```text
public trajectory
→ M50/B1950 frame reconstruction
→ J2000
→ time-dependent ITRF93 transformation
→ WGS84 geodetic conversion
```

rather than being inserted as an assumed trajectory altitude.

This is a strong independent validation of the Phase 2 transformation chain.

---

## Entry Interface velocity geometry

Derived at:

```text
2026-04-10T23:53:30.866000Z
```

Earth-relative speed:

```text
10.632214 km/s
```

From the exploratory geometry reconstruction, the associated local flight geometry was:

```text
vertical velocity:
-1.125755 km/s

horizontal speed:
10.572448 km/s

flight-path angle:
-6.077956 deg

heading:
54.795052 deg
```

The negative flight-path angle and vertical velocity indicate descending motion at atmospheric Entry Interface.

These are A2 MissionLab DERIVED values.

They are not presented as directly reported NASA flight parameters.

---

## Entry trajectory extent

The first state is also the maximum WGS 84 altitude in the dataset:

```text
121.919907 km
```

The trajectory then proceeds through atmospheric descent.

The final state occurs at:

```text
2026-04-11T00:07:08.841000Z
```

Derived terminal coordinates:

```text
Latitude:
32.340599 deg

Longitude:
-117.763094 deg

WGS84 altitude:
-0.000133 km

Earth-relative speed:
0.009130 km/s
```

The terminal altitude corresponds to approximately:

```text
-0.133 m
```

relative to the WGS 84 reference ellipsoid.

The terminal Earth-relative speed corresponds to approximately:

```text
9.13 m/s
```

This indicates that the high-rate file spans substantially more than the initial hypersonic entry segment and continues to a terminal near-surface state.

However, Phase 2B.2 does NOT yet label this final state:

```text
SPLASHDOWN
```

because that event classification will be validated separately against mission reporting.

Likewise, proximity to zero WGS 84 ellipsoidal altitude should not be interpreted as a precise physical ocean-surface measurement.

---

## Frame transformation validation

Maximum position-norm difference between J2000 and ITRF93 representations:

```text
1.818989403546e-12 km
```

A coordinate rotation should preserve physical position magnitude.

The observed residual is consistent with floating-point roundoff.

---

## Independent validator

Created:

```text
scripts/validation/validate_entry_geometry.py
```

The validator independently reconstructs all 819 states.

It verifies:

### Earth-fixed state

For every epoch:

```text
J2000
→ SPICE J2000-to-ITRF93 transform
```

is recomputed independently.

Observed maximum errors:

```text
Position:
0.000000000000e+00 km

Velocity:
0.000000000000e+00 km/s
```

### Geodetic reconstruction

WGS 84 geodetic latitude, longitude, and altitude are independently recalculated.

Observed maximum errors:

```text
Altitude:
0.000000000000e+00 km

Latitude:
0.000000000000e+00 deg

Longitude:
0.000000000000e+00 deg
```

### Velocity decomposition

Earth-relative speed is independently reconstructed from the ITRF93 velocity.

The ENU components are independently checked against the total velocity magnitude.

Observed maximum ENU magnitude error:

```text
1.776356839400e-15 km/s
```

This is consistent with floating-point roundoff.

---

## Entry Interface validation

The validator requires the first high-rate state to reproduce the 400,000-ft Entry Interface altitude within:

```text
1 meter
```

Observed:

```text
Reference:
121.920000 km

Derived:
121.919907 km

Difference:
-0.000092549 km

Difference:
-0.093 m
```

Result:

```text
PASS
```

---

## Terminal-state sanity check

The validator requires the final trajectory state to lie within:

```text
1 meter
```

of the WGS 84 reference ellipsoid.

Observed:

```text
Altitude:
-0.000133 km
```

or:

```text
-0.133 m
```

Result:

```text
PASS
```

This is a geometric terminal-state check.

It is not yet an independent splashdown-event validation.

---

## Permanent pipeline result

Observed:

```text
Earth orientation kernel already present.

SHA256:
CC87AD1A495CF598800BA403763D350F087AC0B97DA9FEC603278A3864C6A53E
```

Geometry builder:

```text
Records:
819

First state:
2026-04-10T23:53:30.866000Z

Latitude:
18.802121 deg

Longitude:
-145.547425 deg

Altitude:
121.919907 km

Earth-relative speed:
10.632214 km/s

Flight-path angle:
-6.077956 deg

Heading:
54.795052 deg
```

Entry Interface check:

```text
Reference altitude:
121.920000 km

Derived altitude:
121.919907 km

Difference:
-0.000093 km
```

Terminal state:

```text
2026-04-11T00:07:08.841000Z

Latitude:
32.340599 deg

Longitude:
-117.763094 deg

Altitude:
-0.000133 km

Earth-relative speed:
0.009130 km/s
```

Final validation:

```text
OK: Earth-fixed frame, WGS84 geodetic geometry,
Earth-relative velocity, and Entry Interface
reconstruction validated.
```

---

## Provenance classification

Direct public source state:

```text
FLIGHT DATA
```

includes the raw high-rate trajectory values and source frame/unit declarations.

Earth-orientation kernel:

```text
authoritative external reference data
JPL/NAIF
```

Entry Interface altitude reference:

```text
NASA REPORTED
```

The following are:

```text
DERIVED
```

- J2000 state representation;
- ITRF93 state;
- WGS 84 latitude;
- WGS 84 longitude;
- WGS 84 altitude;
- Earth-relative velocity;
- east velocity;
- north velocity;
- vertical velocity;
- horizontal speed;
- flight-path angle;
- heading;
- Entry Interface altitude difference.

No atmospheric, aerodynamic, thermal, or guidance model has yet been applied.

---

## Interpretation limits

Phase 2B.2 does NOT yet derive:

- atmospheric density;
- aerodynamic drag;
- aerodynamic lift;
- lift-to-drag ratio;
- angle of attack;
- bank angle;
- dynamic pressure;
- Mach number;
- stagnation heating;
- heat flux;
- heat-shield temperature;
- sensed acceleration;
- crew g-load;
- parachute events;
- exact splashdown event;
- recovery sequence.

The terminal near-zero ellipsoidal altitude does not by itself prove the exact physical ocean-surface altitude.

The trajectory source may contain modeled, reconstructed, or operationally generated states whose exact internal production method has not yet been established.

Derived values must therefore remain labeled according to provenance rather than being upgraded to direct NASA measurements.

---

## Phase 2B.2 status

The high-rate trajectory has now been reconstructed through:

```text
NASA high-rate source
→ M50
→ B1950 analysis proxy
→ J2000
→ ITRF93
→ WGS84
→ Earth-relative local geometry
```

The Entry Interface state independently reproduces the 400,000-ft reference altitude to approximately:

```text
0.093 m
```

Status:

```text
COMPLETE
```

The project now has a defensible physical coordinate system for atmospheric-entry analysis.

The next phase can use this geometry to reconstruct the evolution of the entry itself rather than only its coordinate representation.

---

# Phase 2C — Entry Dynamics Reconstruction

## Goal

Use the validated Earth-fixed Artemis II entry trajectory to reconstruct the time evolution of entry dynamics directly from public trajectory states before introducing any atmospheric, aerodynamic, thermal, or guidance model.

Phase 2B established:

```text
NASA high-rate trajectory
→ M50
→ B1950 analysis proxy
→ J2000
→ ITRF93
→ WGS 84
→ Earth-relative velocity geometry
```

Phase 2C uses that foundation to derive:

```text
altitude evolution
Earth-relative speed evolution
vertical motion
flight-path-angle evolution
kinematic speed deceleration
skip/rebound geometry
entry milestones
```

The analysis deliberately separates kinematic quantities from sensed or aerodynamic acceleration.

---

## Source

Input:

```text
data/processed/entry/entry_geometry.csv
```

The input contains:

```text
819 states
```

covering:

```text
2026-04-10T23:53:30.866000Z
through
2026-04-11T00:07:08.841000Z
```

Elapsed duration:

```text
817.975 seconds
```

Entry Interface is treated as:

```text
EI + 0 s
=
2026-04-10T23:53:30.866000Z
```

because Phase 2B independently reconstructed the first state at approximately the 400,000-ft Orion Entry Interface altitude.

---

## Overall trajectory evolution

Beginning of high-rate entry trajectory:

```text
WGS 84 altitude:
121.919907 km

Earth-relative speed:
10.632214 km/s

flight-path angle:
-6.077956 deg
```

Terminal trajectory state:

```text
WGS 84 altitude:
-0.000133 km

Earth-relative speed:
0.009130 km/s

flight-path angle:
-57.400158 deg
```

The trajectory therefore spans the atmospheric-entry arc from Entry Interface to a terminal near-surface state.

---

## Kinematic deceleration definition

The Earth-relative speed magnitude is:

\[
V
=
\left\|
\mathbf v_{ITRF93}
\right\|
\]

The scalar kinematic speed deceleration is defined as:

\[
a_k
=
-\frac{dV}{dt}
\]

Positive values therefore indicate decreasing Earth-relative speed.

This quantity is labeled:

```text
kinematic deceleration
```

It is NOT automatically:

```text
crew g-load
proper acceleration
accelerometer output
aerodynamic drag acceleration
normal acceleration
seat acceleration
```

Standard gravity is used only as a unit scale:

\[
g_0
=
9.80665\ \mathrm{m/s^2}
\]

and:

\[
a_{g0}
=
\frac{a_k}{g_0}
\]

The resulting value is therefore called:

```text
g0-equivalent scale
```

rather than crew g-load.

---

## Initial finite-difference inspection

A direct numerical derivative using:

```python
numpy.gradient
```

produced a peak kinematic deceleration at:

```text
2026-04-10T23:55:06.866000Z
```

or:

```text
EI + 96.000 s
```

Observed:

```text
Altitude:
60.748759 km

Earth-relative speed:
9.583217 km/s

-dV/dt:
37.158887 m/s^2

g0-equivalent:
3.789152

flight-path angle:
-0.337479 deg
```

The surrounding samples formed a smooth peak rather than an isolated numerical spike.

Examples:

```text
EI+93 s   37.027 m/s^2
EI+94 s   37.116 m/s^2
EI+95 s   37.147 m/s^2
EI+96 s   37.159 m/s^2
EI+97 s   37.114 m/s^2
EI+98 s   37.091 m/s^2
EI+99 s   37.013 m/s^2
```

This motivated a derivative-robustness analysis rather than accepting a single finite-difference estimate without testing.

---

## Derivative robustness methodology

A local quadratic polynomial was fitted to Earth-relative speed around each trajectory state.

For local time coordinate \(\tau\):

\[
V(\tau)
=
a\tau^2+b\tau+c
\]

The derivative at the center of the fitting window is:

\[
\left.
\frac{dV}{dt}
\right|_{\tau=0}
=
b
\]

Therefore:

\[
a_k=-b
\]

The analysis tested odd symmetric windows containing:

```text
5
7
9
11
15
```

trajectory samples.

Because nominal cadence is approximately one second, these represent increasingly broad local smoothing windows.

No SciPy dependency is required.

---

## Derivative robustness result

Observed peaks:

```text
5 samples:
EI + 95.000 s
37.139616 m/s^2

7 samples:
EI + 96.000 s
37.127215 m/s^2

9 samples:
EI + 96.000 s
37.099682 m/s^2

11 samples:
EI + 96.000 s
37.074627 m/s^2

15 samples:
EI + 96.000 s
36.999241 m/s^2
```

Peak-time spread:

```text
1.000 s
```

Peak-magnitude spread:

```text
0.140374 m/s^2
```

Relative spread compared with the approximately 37.1 m/s² peak is small.

This indicates that the inferred peak is stable across reasonable local derivative windows rather than being driven by one differencing choice.

---

## Primary derivative choice

A2 MissionLab uses the:

```text
7-sample local quadratic derivative
```

as the primary reported kinematic derivative.

Reason:

```text
small local window
+
central estimate
+
suppresses single-sample numerical variation
+
peak remains consistent with both smaller and larger windows
```

The raw `numpy.gradient` result is also preserved for transparency.

The primary result is therefore:

```text
UTC:
2026-04-10T23:55:06.866000Z

EI elapsed:
96.000 s

WGS 84 altitude:
60.748759 km

Earth-relative speed:
9.583217 km/s

kinematic deceleration:
37.127215 m/s^2

g0-equivalent scale:
3.785922
```

This is a DERIVED kinematic quantity.

It is not labeled as actual crew g-load.

---

## Altitude-rate consistency check

The numerical time derivative of WGS 84 altitude was compared with the independently derived local ENU vertical velocity.

Numerical altitude derivative:

\[
\dot h_{num}
=
\frac{dh}{dt}
\]

Comparison quantity:

\[
\Delta v_U
=
\dot h_{num}
-
v_U
\]

Initial inspection showed a maximum discrepancy of approximately:

```text
4.499963 m/s
```

at the first trajectory sample.

This first-sample discrepancy is explained by the endpoint derivative, where `numpy.gradient` cannot use a symmetric central difference.

The interior trajectory was therefore evaluated separately.

Observed interior differences:

```text
median absolute:
0.026379 m/s

95th percentile absolute:
0.177064 m/s

maximum absolute:
1.892779 m/s
```

The worst interior sample occurred at:

```text
2026-04-11T00:03:24.866000Z
```

or:

```text
EI + 594.000 s
```

The strong agreement between independently derived ENU vertical velocity and numerical altitude rate provides another internal consistency check on the Earth-fixed geometry.

---

# Phase 2C.1 — Derived Skip/Rebound Geometry

## Initial observation

The entry altitude is not monotonic.

Observed intervals with increasing altitude:

```text
128
```

The trajectory contains one significant local altitude minimum followed by one significant local altitude maximum.

Discrete trajectory extrema:

```text
local minimum:

2026-04-10T23:55:22.866000Z
EI + 112 s
60.350003 km
```

followed by:

```text
local maximum:

2026-04-10T23:57:30.866000Z
EI + 240 s
64.211911 km
```

This indicated a possible skip/rebound trajectory segment.

---

## Turning-event refinement

Altitude extrema were refined using local vertical velocity rather than discrete altitude samples.

A local altitude turning event occurs when:

\[
v_U=0
\]

where:

```text
v_U < 0
descending

v_U > 0
climbing
```

Linear interpolation between adjacent vertical-velocity samples was used to estimate the zero-crossing epoch.

---

## First turning event

Vertical velocity changes:

```text
negative
→
positive
```

therefore:

```text
DESCENT -> CLIMB
```

Derived event:

```text
EI + 112.294128 s
```

UTC:

```text
2026-04-10T23:55:23.160128Z
```

Interpolated altitude:

```text
60.350128 km
```

Interpolated Earth-relative speed:

```text
8.993741 km/s
```

Interpolated flight-path angle:

```text
approximately 0 deg
```

---

## Second turning event

Vertical velocity changes:

```text
positive
→
negative
```

therefore:

```text
CLIMB -> DESCENT
```

Derived event:

```text
EI + 239.647374 s
```

UTC:

```text
2026-04-10T23:57:30.513374Z
```

Interpolated altitude:

```text
64.211808 km
```

Interpolated Earth-relative speed:

```text
6.479165 km/s
```

Interpolated flight-path angle:

```text
approximately 0 deg
```

---

## Skip/rebound segment

Derived duration:

\[
239.647374
-
112.294128
=
127.353246\ \mathrm{s}
\]

Altitude recovery:

\[
64.211808
-
60.350128
=
3.861680\ \mathrm{km}
\]

Earth-relative speed loss during the rebound interval:

\[
8.993741
-
6.479165
=
2.514577\ \mathrm{km/s}
\]

Therefore the public trajectory directly supports a geometric sequence:

```text
descent
→ local minimum
→ climb
→ local maximum
→ renewed descent
```

A2 MissionLab labels this:

```text
DERIVED SKIP/REBOUND GEOMETRY
```

This terminology describes the observed trajectory shape.

It does NOT by itself establish:

```text
guidance mode
bank-reversal command
lift command
specific onboard guidance logic
targeting decision
control-system cause
```

Those require additional evidence.

---

## Positive flight-path angle

The Earth-relative flight-path angle becomes positive during the rebound.

Observed maximum:

```text
+0.402796 deg
```

at:

```text
2026-04-10T23:56:43.866000Z
```

approximately:

```text
EI + 193 s
```

at altitude:

```text
62.767375 km
```

The positive flight-path angle independently confirms that the spacecraft is locally climbing during the rebound segment.

---

## Maximum descent rate

The largest downward ENU velocity in the available trajectory occurs at Entry Interface:

```text
2026-04-10T23:53:30.866000Z
```

Observed:

```text
vertical velocity:
-1125.755 m/s

Earth-relative speed:
10.632214 km/s
```

This describes local Earth-relative vertical motion and is not equivalent to total spacecraft speed.

---

## Altitude milestones

The trajectory crosses major descending-altitude thresholds approximately as follows:

```text
100 km
EI + 22 s
V ≈ 10.652 km/s

80 km
EI + 46 s
V ≈ 10.647 km/s

60 km
EI + 311 s
V ≈ 5.675 km/s

50 km
EI + 374 s
V ≈ 4.400 km/s

40 km
EI + 432 s
V ≈ 2.554 km/s

30 km
EI + 481 s
V ≈ 1.079 km/s

20 km
EI + 526 s
V ≈ 0.345 km/s

10 km
EI + 576 s
V ≈ 0.175 km/s

5 km
EI + 619 s
V ≈ 0.067 km/s

2 km
EI + 669 s
V ≈ 0.056 km/s

1 km
EI + 693 s
V ≈ 0.017 km/s
```

Because the trajectory contains a skip/rebound, altitude thresholds can in principle be crossed more than once.

The milestone analysis records the first descending crossing unless otherwise specified.

---

## Speed milestones

Approximate first descending speed crossings include:

```text
10 km/s
EI + 85 s

9 km/s
EI + 113 s

8 km/s
EI + 147 s

7 km/s
EI + 198 s

6 km/s
EI + 285 s

5 km/s
EI + 350 s

4 km/s
EI + 388 s

3 km/s
EI + 419 s

2 km/s
EI + 450 s

1 km/s
EI + 485 s

0.5 km/s
EI + 512 s

0.2 km/s
EI + 566 s

0.1 km/s
EI + 601 s

0.05 km/s
EI + 679 s
```

Permanent processing uses interpolation between neighboring samples rather than assigning the threshold to the next discrete sample.

---

## Implementation

Created:

```text
scripts/analysis/analyze_entry_dynamics.py
```

The analysis:

1. loads the validated Earth-fixed entry geometry;
2. defines Entry Interface as elapsed time zero;
3. computes raw Earth-relative speed derivatives;
4. computes local quadratic derivatives;
5. evaluates derivative robustness across multiple window lengths;
6. identifies the primary kinematic-deceleration peak;
7. compares numerical altitude rate with ENU vertical velocity;
8. locates vertical-velocity zero crossings;
9. reconstructs skip/rebound geometry;
10. interpolates altitude and speed milestones;
11. writes state-by-state derived dynamics;
12. writes a structured summary;
13. produces deterministic documentation figures.

Generated processed products:

```text
data/processed/entry/entry_dynamics.csv
data/processed/entry/entry_dynamics_summary.json
```

These remain ignored by Git.

---

## Documentation figures

Created:

```text
docs/assets/entry/phase2c_entry_altitude.svg
docs/assets/entry/phase2c_entry_speed.svg
docs/assets/entry/phase2c_entry_kinematic_deceleration.svg
docs/assets/entry/phase2c_entry_flight_path_angle.svg
```

The SVG output uses the project's deterministic figure configuration:

```text
fixed SVG hash salt
generation-date metadata removed
trailing whitespace normalized
```

so repeated analysis runs should not generate unnecessary Git differences.

---

## Independent validator

Created:

```text
scripts/validation/validate_entry_dynamics.py
```

The validator independently reconstructs:

```text
raw speed derivative
7-sample quadratic derivative
primary deceleration peak
derivative robustness
vertical-velocity zero crossings
skip/rebound duration
altitude-rate consistency
```

It also confirms the expected documentation figures exist.

---

## Validation result

Observed:

```text
Artemis II Entry Dynamics Validation
--------------------------------
Records checked: 819
```

Primary derivative:

```text
7-sample local quadratic fit

Peak:
EI + 96.000 s

37.127215 m/s^2

g0-equivalent:
3.785922
```

Derivative reconstruction error:

```text
Raw:
0.000000000000e+00 m/s^2

Smoothed:
0.000000000000e+00 m/s^2
```

Derivative robustness:

```text
Peak-time spread:
1.000 s

Peak-magnitude spread:
0.140374 m/s^2
```

Skip/rebound:

```text
Start:
EI + 112.294128 s

End:
EI + 239.647374 s

Duration:
127.353246 s

Altitude recovery:
3.861680 km

Speed loss:
2.514577 km/s
```

Altitude-rate consistency:

```text
Interior median absolute:
0.026379 m/s

Interior p95 absolute:
0.177064 m/s

Interior maximum absolute:
1.892779 m/s
```

Final result:

```text
OK: entry dynamics, derivative robustness,
and skip/rebound geometry validated.
```

---

## Provenance

The underlying trajectory remains:

```text
FLIGHT DATA
```

The following Phase 2C products are:

```text
DERIVED
```

- EI elapsed time;
- Earth-relative speed derivative;
- kinematic deceleration;
- g0-equivalent scale;
- skip/rebound turning times;
- skip/rebound altitude recovery;
- skip/rebound speed loss;
- altitude milestones;
- speed milestones;
- altitude-rate consistency statistics.

No aerodynamic or atmospheric quantities are introduced in Phase 2C.

---

## Interpretation limits

The derived kinematic deceleration:

\[
-\frac{dV}{dt}
\]

is a scalar rate of change of Earth-relative speed.

It is not automatically:

```text
proper acceleration
crew g-load
aerodynamic acceleration
drag acceleration
lift acceleration
normal load factor
accelerometer measurement
```

The g0-equivalent value:

```text
3.785922
```

means only:

```text
37.127215 m/s^2 divided by standard gravity
```

It should not be presented as:

```text
the crew experienced 3.79 g
```

without additional force/acceleration evidence.

Likewise, the derived skip/rebound geometry demonstrates the trajectory shape but does not identify the specific guidance commands or control logic responsible for it.

---

## Phase 2C status

The project has now reconstructed:

```text
Entry Interface
→ initial atmospheric descent
→ peak kinematic speed deceleration region
→ descent-to-climb turning event
→ skip/rebound climb
→ climb-to-descent turning event
→ continued atmospheric descent
→ low-altitude terminal trajectory
```

from public trajectory states.

Phase 2C status:

```text
COMPLETE
```

The next analysis should correlate the derived trajectory with independently reported NASA entry events before assigning operational labels to later trajectory transitions such as parachute deployment or splashdown.

---

# Phase 2D — Entry Events and Recovery Timeline Validation

## Goal

Correlate the reconstructed Artemis II entry trajectory with independently reported NASA mission events.

Previous Phase 2 work reconstructed the entry trajectory through:

```text
NASA flight-derived ephemeris
→ M50
→ B1950 analysis proxy
→ J2000
→ ITRF93
→ WGS 84
→ Earth-relative geometry
→ entry dynamics
```

Phase 2D adds independent operational-event evidence.

The objective is not to infer parachute or splashdown events from trajectory shape alone.

Instead:

```text
NASA public event report
+
derived trajectory state
→
event correlation
```

---

## NASA event-reference source

A curated reference file was created:

```text
data/reference/artemis_ii_entry_events.json
```

The reference contains actual NASA public reports for:

```text
Entry Interface
Drogue Parachute Deployment
Main Parachute Deployment
Splashdown
```

Reference provenance:

```text
NASA_REPORTED
```

The source timestamps are public blog timestamps with:

```text
minute-level resolution
```

They are therefore interpreted as time intervals:

```text
HH:MM:00 <= event < HH:MM:60
```

rather than exact second-level telemetry epochs.

A derived trajectory state is considered time-consistent if it occurs inside NASA's reported minute.

---

## Trajectory provenance refinement

The Artemis II AROW trajectory products are treated as:

```text
NASA FLIGHT-DERIVED EPHEMERIS
```

This is more precise than describing them as raw onboard telemetry.

The public trajectory represents mission trajectory information derived from the actual flight.

A2 MissionLab therefore distinguishes:

```text
NASA_REPORTED
```

for independently published event facts,

from:

```text
FLIGHT-DERIVED EPHEMERIS
```

for the trajectory,

and:

```text
DERIVED
```

for quantities calculated by this project.

---

# Entry Interface Correlation

NASA reported Entry Interface during the:

```text
23:53 UTC minute
```

with altitude:

```text
400,000 ft
=
121.920000 km
```

The first high-rate trajectory state occurs at:

```text
2026-04-10T23:53:30.866000Z
```

Therefore it occurs:

```text
30.866 s
```

into the NASA-reported minute.

Time correlation:

```text
PASS
```

Derived WGS 84 altitude:

```text
121.919907 km
```

Difference from the NASA Entry Interface reference:

```text
-0.000092549 km
=
-0.093 m
```

Altitude correlation:

```text
PASS
```

---

## Entry Interface distance-to-splashdown check

NASA also reported Orion was approximately:

```text
1,956 statute miles
```

from splashdown at Entry Interface.

A2 MissionLab calculated the spherical great-circle distance from the derived Entry Interface location to the derived terminal surface-crossing location.

Derived distance:

```text
3153.188993 km
```

or:

```text
1959.300804 mi
```

Difference:

```text
+3.300804 mi
```

Percent difference:

```text
+0.1688%
```

Because NASA's published value is explicitly approximate and the project uses a spherical great-circle distance rather than an operational range definition, the approximately 0.17% agreement is treated as strong independent geographic validation.

---

# Drogue Parachute Correlation

NASA reported drogue deployment during the:

```text
00:03 UTC minute
```

with an associated altitude:

```text
23,400 ft
```

Converted exactly:

```text
7.132320 km
```

The trajectory descending through this WGS 84 altitude occurs at:

```text
2026-04-11T00:03:24.817733Z
```

or:

```text
EI + 593.951733 s
```

This occurs:

```text
24.818 s
```

into NASA's reported minute.

Time correlation:

```text
PASS
```

Derived Earth-relative speed at the 23,400-ft altitude anchor:

```text
468.548 ft/s
```

NASA also reported:

```text
479 ft/s
```

during the drogue sequence.

The trajectory reaches exactly:

```text
479 ft/s
```

at:

```text
2026-04-11T00:03:23.960907Z
```

or:

```text
EI + 593.094907 s
```

Offset relative to the 23,400-ft anchor:

```text
-0.856825 s
```

Therefore the altitude and reported velocity conditions align to within approximately one second in the reconstructed trajectory.

This is treated as strong event-sequence agreement.

---

## Drogue 0.8-mile statement

NASA's public update also reported approximately:

```text
0.8 mi
```

from splashdown in association with the drogue sequence.

The reconstructed trajectory reaches a spherical surface distance of exactly:

```text
0.8 mi
```

from the derived terminal location at:

```text
2026-04-11T00:04:01.167311Z
```

or:

```text
EI + 630.301311 s
```

This occurs:

```text
+36.349579 s
```

after the 23,400-ft altitude anchor.

Therefore A2 MissionLab does NOT treat:

```text
23,400 ft
479 ft/s
0.8 mi from splashdown
```

as a synchronous sub-second telemetry tuple.

Instead, these are preserved as associated values from a minute-resolution NASA operational update.

The 23,400-ft altitude and 479-ft/s conditions show close trajectory alignment.

The 0.8-mile statement is retained as an approximate sequence-level observation.

---

# Main Parachute Correlation

NASA reported main parachute deployment during the:

```text
00:04 UTC minute
```

with deployment altitude:

```text
5,400 ft
```

Converted:

```text
1.645920 km
```

The reconstructed trajectory crosses this WGS 84 altitude at:

```text
2026-04-11T00:04:45.680532Z
```

or:

```text
EI + 674.814532 s
```

This occurs:

```text
45.681 s
```

into NASA's reported minute.

Time correlation:

```text
PASS
```

Earth-relative speed at this altitude:

```text
202.653 ft/s
```

NASA reported that main deployment was:

```text
reducing velocity to less than 200 ft/s
```

The trajectory reaches:

```text
200.000 ft/s
```

at:

```text
2026-04-11T00:04:48.316247Z
```

or:

```text
EI + 677.450247 s
```

Time after the 5,400-ft altitude anchor:

```text
+2.635715 s
```

Altitude when 200 ft/s is reached:

```text
4839.669 ft
```

This is consistent with NASA's wording describing velocity reduction following deployment rather than requiring speed to already be below 200 ft/s at the exact deployment altitude.

---

# Splashdown Correlation

NASA reported successful splashdown during the:

```text
00:07 UTC minute
```

in the:

```text
Pacific Ocean off San Diego
```

A2 MissionLab independently reconstructs the descending WGS 84 zero-altitude crossing.

Derived crossing:

```text
2026-04-11T00:07:08.823676Z
```

or:

```text
EI + 817.957676 s
```

This occurs:

```text
8.824 s
```

into NASA's reported splashdown minute.

Time correlation:

```text
PASS
```

Derived location:

```text
Latitude:
32.340599 deg

Longitude:
-117.763095 deg
```

Derived Earth-relative speed:

```text
9.128 m/s
```

or:

```text
20.419 mph
```

The final file state occurs only approximately:

```text
0.017 s
```

later at:

```text
2026-04-11T00:07:08.841000Z
```

with WGS 84 altitude:

```text
-0.000133 km
```

and Earth-relative speed:

```text
9.130 m/s
```

---

## Splashdown terminology

Phase 2B previously labeled the final trajectory state:

```text
terminal near-surface state
```

Phase 2D provides independent NASA event evidence sufficient to refine this classification to:

```text
DERIVED SPLASHDOWN-CORRELATED SURFACE CROSSING
```

This means:

```text
derived trajectory geometry
+
NASA-reported splashdown minute
+
terminal flight-derived ephemeris
```

are mutually consistent.

However, the project does NOT claim:

```text
2026-04-11T00:07:08.823676Z
```

is NASA's official splashdown timestamp.

NASA's public source provides only minute-level timing.

The sub-second value is an A2 MissionLab trajectory correlation.

---

# Phase 2D implementation

Created:

```text
scripts/analysis/correlate_entry_events.py
```

The analysis:

1. loads the NASA event reference catalog;
2. loads the validated Earth-fixed entry trajectory;
3. reconstructs the zero-altitude terminal crossing;
4. calculates the terminal geodetic location;
5. calculates spherical great-circle distance to that terminal point;
6. correlates the Entry Interface state;
7. reconstructs the 23,400-ft drogue altitude crossing;
8. independently reconstructs the 479-ft/s crossing;
9. reconstructs the 0.8-mi-to-terminal condition;
10. reconstructs the 5,400-ft main-parachute altitude crossing;
11. reconstructs the subsequent 200-ft/s threshold;
12. correlates the derived surface crossing with NASA's splashdown minute;
13. preserves operational interpretation limits;
14. produces deterministic event figures.

Generated processed output:

```text
data/processed/entry/entry_event_correlations.json
```

This remains ignored under:

```text
data/processed/
```

---

## Documentation figures

Created:

```text
docs/assets/entry/phase2d_entry_events_altitude.svg
docs/assets/entry/phase2d_terminal_ground_track.svg
```

The first figure overlays the NASA-correlated entry events onto the reconstructed altitude history.

The second shows the terminal geographic ground track with:

```text
Drogues
Mains
Splashdown correlation
```

marked.

The figures use the project's deterministic SVG configuration.

---

# Independent validation

Created:

```text
scripts/validation/validate_entry_events.py
```

The validator independently requires all four major NASA events to correlate within the reported minute.

Observed:

```text
Entry Interface: PASS
Drogues:         PASS
Mains:           PASS
Splashdown:      PASS
```

---

## Entry Interface validation

Observed altitude difference:

```text
-0.093 m
```

Observed distance-to-terminal difference from NASA's approximate 1,956-mile value:

```text
+0.1688%
```

Both satisfy the Phase 2D validation criteria.

---

## Drogue validation

Observed offset between:

```text
23,400-ft altitude crossing
```

and:

```text
479-ft/s speed crossing
```

is:

```text
-0.856825 s
```

The validator requires this alignment to be within:

```text
2 seconds
```

Result:

```text
PASS
```

The 0.8-mile condition occurs:

```text
+36.349579 s
```

after the altitude anchor.

This value is intentionally NOT used as a synchronous deployment-state validation requirement.

---

## Main parachute validation

Observed:

```text
5,400-ft altitude anchor:
2026-04-11T00:04:45.680532Z
```

The trajectory reaches:

```text
200 ft/s
```

after:

```text
+2.635715 s
```

The validator requires the 200-ft/s threshold to follow the altitude anchor within a short physically plausible interval.

Result:

```text
PASS
```

---

## Splashdown validation

The derived WGS 84 surface crossing occurs during NASA's reported splashdown minute.

Observed:

```text
UTC:
2026-04-11T00:07:08.823676Z

Latitude:
32.340599 deg

Longitude:
-117.763095 deg

Earth-relative speed:
9.128 m/s
```

Classification:

```text
DERIVED_SPLASHDOWN_CORRELATED_SURFACE_CROSSING
```

Result:

```text
PASS
```

---

# Permanent validation result

Observed:

```text
Artemis II Entry Event Correlation Validation
--------------------------------

Minute-level NASA event matches:
  Entry Interface: PASS
  Drogues:         PASS
  Mains:           PASS
  Splashdown:      PASS
```

Additional validation:

```text
Entry Interface altitude difference:
-0.093 m

Entry Interface range difference:
+0.1688%

Drogue 479-ft/s offset:
-0.856825 s

Main 200-ft/s response offset:
+2.635715 s
```

Final result:

```text
OK: NASA entry-event timing,
reported-condition alignment,
and splashdown correlation validated.
```

---

# Provenance classification

NASA public event facts:

```text
NASA_REPORTED
```

NASA trajectory:

```text
NASA FLIGHT-DERIVED EPHEMERIS
```

Project event correlations:

```text
DERIVED
```

This includes:

```text
sub-second event-correlated epochs
WGS84 event coordinates
event-state speeds
terminal surface crossing
distance-to-terminal values
event-condition offsets
```

The project does not promote these derived values into official NASA telemetry timestamps.

---

# Interpretation limits

NASA blog timestamps have minute-level public resolution.

The project therefore does not claim sub-second event timing from those reports.

NASA-reported altitude references are not assumed to use exactly the same geodetic datum as A2 MissionLab's WGS 84 ellipsoidal altitude.

The NASA 1,956-mile Entry Interface range is approximate.

A2 MissionLab uses a spherical great-circle distance for its independent comparison.

The NASA 0.8-mile drogue statement is retained as an associated public-report condition but is not interpreted as synchronous with the 23,400-ft deployment state.

The derived terminal crossing is strongly correlated with splashdown but is not claimed as an official NASA splashdown timestamp.

---

# Phase 2D status

The project now independently correlates:

```text
Entry Interface
Drogue deployment
Main parachute deployment
Splashdown
```

against actual NASA public mission reporting.

All four events occur inside NASA's reported UTC minute.

Phase 2D status:

```text
COMPLETE
```

The high-rate entry product can now be interpreted as an end-to-end entry and descent trajectory with independently validated operational event anchors.

