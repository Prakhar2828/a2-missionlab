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
