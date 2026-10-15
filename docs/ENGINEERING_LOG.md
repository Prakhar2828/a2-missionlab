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

---

# Phase 2E — Atmospheric and Aerothermal Reconstruction

# Phase 2E.1 — Modeled Atmosphere and Dynamic Pressure

## Goal

Add an atmospheric environment to the validated Artemis II entry trajectory without introducing a vehicle aerodynamic or heating model.

Previous Phase 2 work established:

```text
NASA flight-derived ephemeris
→ inertial-frame reconstruction
→ Earth-fixed trajectory
→ WGS 84 geometry
→ Earth-relative velocity
→ entry dynamics
→ NASA event correlations
```

Phase 2E.1 extends this chain with:

```text
flight-derived trajectory
+
empirical atmosphere model
→ density
→ neutral temperature
→ modeled dynamic pressure
```

The atmosphere is explicitly separated from flight-derived trajectory quantities.

---

## Provenance separation

The underlying trajectory is treated as:

```text
NASA FLIGHT-DERIVED EPHEMERIS
```

Earth-fixed geometry and Earth-relative velocity are:

```text
DERIVED
```

NRLMSIS atmospheric quantities are:

```text
MODEL
```

This includes:

```text
total mass density
neutral temperature
```

Dynamic pressure combines modeled atmospheric density with derived Earth-relative speed and is therefore classified:

```text
MODEL-DERIVED
```

Phase 2E.1 does not promote modeled atmospheric quantities into flight measurements.

---

## Atmospheric model

A2 MissionLab uses:

```text
NRLMSIS 2.0
```

through:

```text
pymsis 0.12.0
```

The package version is pinned in:

```text
requirements.txt
```

The trajectory is evaluated in aligned fly-through mode, where each atmospheric-model evaluation corresponds to one trajectory epoch and location.

Total states:

```text
819
```

---

## Model trajectory inputs

Each NRLMSIS evaluation uses the corresponding derived trajectory values:

```text
UTC epoch
geodetic longitude
geodetic latitude
WGS 84 altitude
```

The model trajectory therefore follows Orion through the complete Phase 2 entry arc.

One final trajectory state has WGS 84 altitude:

```text
-0.000133 km
```

Because the atmospheric-model evaluation is not extended below zero altitude, that single state is evaluated at:

```text
0.000000 km
```

The original trajectory altitude remains preserved independently.

Number of clipped model states:

```text
1
```

---

# Historical Solar and Geomagnetic Drivers

## Driver source

The initial inspection used the historical space-weather driver source consumed by `pymsis`:

```text
SW-All.csv
```

Provider:

```text
CelesTrak
```

Observed local file size:

```text
2,890,313 bytes
```

Observed SHA-256:

```text
50130BC78F48B02FEC4424DA59098A065D5DE06562DB73BBCC3631BCCBFFBAEE
```

Because this external source can change over time, normal atmospheric reconstruction should not silently depend on a future revision.

---

## Pinned driver snapshot

Created:

```text
scripts/ingestion/capture_msis_drivers.py
```

The ingestion step reconstructs the exact historical model inputs used for every trajectory state and writes:

```text
data/reference/artemis_ii_msis_drivers.csv
```

The committed snapshot contains:

```text
819 records
```

and preserves:

```text
F10.7
81-day F10.7 average
daily Ap
current 3-hour Ap
3-hour prior Ap
6-hour prior Ap
9-hour prior Ap
12–33-hour average Ap
36–57-hour average Ap
```

Observed driver-snapshot SHA-256:

```text
6A688BE48A211CD2426B81EE30148EDD04FDAA28C438DE04066121AC940D21DA
```

Metadata is stored in:

```text
data/reference/artemis_ii_msis_environment.json
```

The source `SW-All.csv` itself is not committed.

Instead, its hash is recorded so the exact source revision used to produce the committed model-input snapshot can be identified.

---

## Driver values during entry

The entry crosses the UTC date boundary from April 10 to April 11.

Observed F10.7 values:

```text
96.700
93.700
```

Observed F10.7a values:

```text
124.100
123.800
```

Observed current 3-hour Ap values:

```text
5.000
7.000
```

First trajectory Ap history vector:

```text
17.000
5.000
22.000
27.000
32.000
9.625
5.500
```

Last trajectory Ap history vector:

```text
12.000
7.000
5.000
22.000
27.000
12.500
5.750
```

Storm-time geomagnetic mode is used so the full seven-element Ap history vector is supplied to NRLMSIS.

---

# UTC Driver-Boundary Control

## Motivation

The entry crosses:

```text
00:00 UTC
```

and the historical F10.7/F10.7a/Ap inputs change at the UTC-date boundary.

The initial trajectory calculation showed a one-step modeled density increase of approximately:

```text
+2.142846275%
```

between:

```text
2026-04-10T23:59:59.866000Z
```

and:

```text
2026-04-11T00:00:00.866000Z
```

This could not initially be interpreted as a model-driver discontinuity because Orion also changes altitude substantially during the same second.

A controlled experiment was therefore performed.

---

## Boundary trajectory states

Before UTC midnight:

```text
UTC:
2026-04-10T23:59:59.866000Z

altitude:
47.319239 km
```

After UTC midnight:

```text
UTC:
2026-04-11T00:00:00.866000Z

altitude:
47.154503 km
```

Altitude change:

```text
-164.736 m
```

Observed modeled densities:

```text
Before:
1.423128647730e-03 kg/m^3

After:
1.453624106944e-03 kg/m^3
```

Observed one-second density change:

```text
+2.142846275%
```

---

## Fixed-geometry driver experiment

The spacecraft geometry was held fixed while the pre-midnight and post-midnight space-weather drivers were exchanged.

At the pre-midnight state:

```text
density with pre-midnight drivers:
1.423128647730e-03 kg/m^3

density with post-midnight drivers:
1.423128647730e-03 kg/m^3
```

Relative driver effect:

```text
+0.000000000000%
```

At the post-midnight state:

```text
density with pre-midnight drivers:
1.453624106944e-03 kg/m^3

density with post-midnight drivers:
1.453624106944e-03 kg/m^3
```

Relative driver effect:

```text
+0.000000000000%
```

---

## Fixed-driver trajectory experiment

The actual geometry/time evolution was evaluated while retaining the pre-midnight model-driver set.

Resulting density change:

```text
+2.142846275%
```

This is identical at reported precision to the original trajectory density change.

Residual attributable to the UTC driver swap:

```text
0.000000000000 percentage points
```

Therefore:

```text
the apparent midnight density step is caused by
Orion descending through the atmospheric density gradient
```

rather than a measurable discontinuity from the F10.7/F10.7a/Ap change at approximately 47 km.

This control is preserved in:

```text
data/reference/artemis_ii_msis_environment.json
```

---

# Atmosphere Reconstruction

Created:

```text
scripts/analysis/build_entry_atmosphere.py
```

The analysis reads:

```text
validated entry geometry
+
pinned model-driver snapshot
```

and evaluates NRLMSIS 2.0 for all:

```text
819 states
```

Generated products:

```text
data/processed/entry/entry_atmosphere.csv
data/processed/entry/entry_atmosphere_summary.json
```

These remain ignored under:

```text
data/processed/
```

---

## Entry Interface atmosphere

At:

```text
2026-04-10T23:53:30.866000Z
```

with WGS 84 altitude:

```text
121.919907 km
```

NRLMSIS 2.0 gives:

```text
total mass density:
1.453686149233e-08 kg/m^3

neutral temperature:
415.921 K
```

These are MODEL quantities.

---

# Dynamic Pressure Reconstruction

## Definition

Phase 2E.1 defines modeled dynamic pressure as:

\[
q
=
\frac{1}{2}\rho V^2
\]

where:

```text
rho = NRLMSIS modeled total mass density

V = Earth-relative trajectory speed
```

The Earth-relative velocity comes from the ITRF93 trajectory reconstruction.

No independent atmospheric-wind model is currently applied.

Therefore the calculation assumes:

```text
zero local atmospheric wind
relative to the rotating Earth-fixed frame
```

Dynamic pressure is classified:

```text
MODEL-DERIVED
```

and not as a directly measured flight quantity.

---

## Entry Interface dynamic pressure

At Entry Interface:

```text
density:
1.453686149233e-08 kg/m^3

Earth-relative speed:
10.632214 km/s
```

Modeled dynamic pressure:

```text
0.821652 Pa
```

or approximately:

```text
0.017161 psf
```

The low modeled dynamic pressure is consistent with Entry Interface occurring in the extremely tenuous upper atmosphere.

---

# Double-Peaked Modeled Dynamic-Pressure History

The reconstructed entry contains two dominant local dynamic-pressure peaks.

## Early peak

Derived at:

```text
2026-04-10T23:55:05.866000Z
```

or:

```text
EI + 95.000 s
```

Altitude:

```text
60.807901 km
```

Earth-relative speed:

```text
9.6205 km/s
```

Modeled dynamic pressure:

```text
12.798779 kPa
```

This occurs approximately one second before the Phase 2C primary peak kinematic-deceleration estimate.

---

## Global peak

Derived at:

```text
2026-04-11T00:00:41.866000Z
```

or:

```text
EI + 431.000 s
```

Altitude:

```text
40.042026 km
```

Earth-relative speed:

```text
2.587485 km/s
```

NRLMSIS density:

```text
3.826211439446e-03 kg/m^3
```

Neutral temperature:

```text
253.416 K
```

Modeled dynamic pressure:

```text
12.808389 kPa
```

or:

```text
267.509 psf
```

This is the global maximum of the modeled dynamic-pressure history.

---

## Similarity of dominant peaks

The two dominant modeled peaks are:

```text
12.808389 kPa
12.798779 kPa
```

Relative magnitude difference:

```text
0.075024%
```

The modeled entry therefore exhibits a pronounced double-peaked dynamic-pressure history over the reconstructed skip-entry trajectory.

This is a derived property of:

```text
modeled density
+
flight-derived trajectory speed
```

No claim is made that NASA directly reported these dynamic-pressure values.

Likewise, the project does not yet assign a guidance or aerodynamic cause solely from the shape of the dynamic-pressure curve.

---

# Atmosphere at Peak Kinematic Deceleration

Phase 2C located the primary 7-sample quadratic kinematic-deceleration peak at:

```text
2026-04-10T23:55:06.866000Z
```

or:

```text
EI + 96.000 s
```

Altitude:

```text
60.748759 km
```

Earth-relative speed:

```text
9.583217 km/s
```

Kinematic deceleration:

```text
37.127215 m/s^2
```

NRLMSIS modeled density at that state:

```text
2.786277036648e-04 kg/m^3
```

Modeled dynamic pressure:

```text
12.794311 kPa
```

The peak kinematic-deceleration epoch therefore lies within approximately one second of the early modeled dynamic-pressure peak.

This temporal association is documented.

It is not interpreted as proof of a particular aerodynamic-force decomposition.

---

# Additional Dynamic-Pressure Structure

The five largest local modeled dynamic-pressure maxima are:

```text
2026-04-11T00:00:41.866000Z
EI + 431 s
40.042 km
12.80839 kPa

2026-04-10T23:55:05.866000Z
EI + 95 s
60.808 km
12.79878 kPa

2026-04-11T00:01:05.866000Z
EI + 455 s
35.748 km
12.11569 kPa

2026-04-11T00:01:07.866000Z
EI + 457 s
35.310 km
12.11339 kPa

2026-04-11T00:02:54.866000Z
EI + 564 s
11.975 km
6.66357 kPa
```

Later local structure may reflect changing descent regimes, including the recovery sequence already correlated in Phase 2D.

Phase 2E.1 does not assign physical causes to each secondary maximum without further modeling or independent evidence.

---

# NRLMSIS 2.0 / 2.1 Sensitivity Check

The complete 819-state trajectory was also evaluated using NRLMSIS 2.1 as a sensitivity check.

Observed maximum relative total-mass-density difference:

```text
0.000000000000%
```

Observed maximum neutral-temperature difference:

```text
0.000000000000 K
```

Therefore, for these requested output quantities and these trajectory states under `pymsis 0.12.0`, selecting NRLMSIS 2.0 rather than 2.1 produces no observed difference at reported numerical precision.

The project nevertheless retains NRLMSIS 2.0 as the explicitly selected Phase 2E.1 model.

---

# Reproducibility

The complete model chain is pinned by:

```text
pymsis:
0.12.0

NRLMSIS:
2.0

SW-All.csv SHA-256:
50130BC78F48B02FEC4424DA59098A065D5DE06562DB73BBCC3631BCCBFFBAEE

driver snapshot SHA-256:
6A688BE48A211CD2426B81EE30148EDD04FDAA28C438DE04066121AC940D21DA
```

The committed driver snapshot removes normal analysis dependence on future changes to the external CelesTrak source.

---

# Independent Validation

Created:

```text
scripts/validation/validate_entry_atmosphere.py
```

The validator independently:

```text
loads all 819 geometry states
loads all 819 pinned driver states
reruns NRLMSIS 2.0
reconstructs total mass density
reconstructs neutral temperature
recalculates dynamic pressure
checks the global dynamic-pressure peak
checks the dominant local peaks
rechecks NRLMSIS 2.0 versus 2.1
checks the UTC-boundary control
checks required deterministic figures
```

Observed reconstruction errors:

```text
Maximum density error:
0.000000000000e+00 kg/m^3

Maximum temperature error:
0.000000000000e+00 K

Maximum dynamic-pressure error:
0.000000000000e+00 Pa
```

Result:

```text
PASS
```

---

## Dynamic-pressure validation

Global modeled dynamic-pressure peak:

```text
UTC:
2026-04-11T00:00:41.866000Z

altitude:
40.042026 km

speed:
2.587485 km/s

dynamic pressure:
12.808389 kPa
```

Two dominant local peaks:

```text
40.042026 km
12.808389 kPa

60.807901 km
12.798779 kPa
```

Relative difference:

```text
0.075024%
```

The validator requires the two dominant modeled peaks to remain within:

```text
1%
```

of one another.

Result:

```text
PASS
```

---

# Documentation Figures

Created:

```text
docs/assets/entry/phase2e_density.svg
docs/assets/entry/phase2e_dynamic_pressure.svg
```

The density figure uses logarithmic vertical scaling because modeled atmospheric density spans many orders of magnitude across the entry trajectory.

The dynamic-pressure figure identifies:

```text
early modeled q peak
global modeled q peak
peak kinematic-deceleration epoch
```

SVG generation follows the project's deterministic plotting configuration.

---

# Interpretation Limits

Phase 2E.1 does not yet reconstruct:

```text
atmospheric winds
true air-relative velocity
speed of sound
Mach number
aerodynamic coefficients
drag force
lift force
angle of attack
bank angle
vehicle load factor
proper acceleration
crew g-load
convective heat flux
radiative heat flux
stagnation heating
heat-shield temperature
TPS material response
```

NRLMSIS is an empirical atmospheric model.

Its density and temperature outputs are not direct Artemis II atmospheric measurements.

The dynamic-pressure reconstruction assumes zero local atmospheric wind and therefore uses Earth-relative trajectory speed as the atmospheric-relative speed approximation.

At the highest altitudes, rarefied-flow effects also limit how literally continuum aerodynamic quantities should be interpreted.

---

# Phase 2E.1 Status

The project now has a reproducible atmosphere reconstruction covering the complete high-rate entry trajectory:

```text
flight-derived trajectory
+
pinned historical model forcing
+
NRLMSIS 2.0
→ modeled density
→ modeled neutral temperature
→ modeled dynamic pressure
```

The atmospheric model reproduces a double-peaked modeled dynamic-pressure history:

```text
early peak:
12.798779 kPa at EI + 95 s

global peak:
12.808389 kPa at EI + 431 s
```

with only:

```text
0.075024%
```

difference in peak magnitude.

The apparent modeled-density change at the UTC date boundary was independently shown to arise from trajectory descent rather than the model-driver transition.

Phase 2E.1 status:

```text
COMPLETE
```

The next atmospheric/aerothermal step should introduce additional physics only with explicitly documented assumptions.

---

# Phase 2E.2 — Free-Stream Mach and Flow-Regime Reconstruction

## Goal

Extend the Phase 2E atmospheric reconstruction into a free-stream compressibility timeline.

Phase 2E.1 established:

```text
NASA flight-derived trajectory
+
NRLMSIS 2.0 atmosphere
→ modeled density
→ modeled neutral temperature
→ modeled dynamic pressure
```

Phase 2E.2 adds:

```text
modeled neutral composition
+
modeled neutral temperature
+
Earth-relative trajectory speed
→ mixture thermodynamic properties
→ modeled speed of sound
→ modeled free-stream Mach
→ formal flow-regime transitions
```

The objective is to reconstruct the free-stream Mach history before introducing shock-layer, heating, or TPS models.

---

# Provenance

The underlying velocity is:

```text
DERIVED_FROM_NASA_FLIGHT_DERIVED_EPHEMERIS
```

NRLMSIS composition and neutral temperature are:

```text
MODEL
```

The following quantities are:

```text
MODEL_DERIVED
```

- thermal-mixture composition fractions;
- mixture specific-heat ratio;
- effective mixture molar mass;
- effective specific gas constant;
- free-stream speed of sound;
- free-stream Mach number;
- formal compressibility regime;
- Mach-threshold crossing epochs.

No Mach value in Phase 2E.2 is treated as direct NASA telemetry.

---

# Input Data

Phase 2E.2 consumes:

```text
data/processed/entry/entry_geometry.csv
data/processed/entry/entry_atmosphere.csv
data/reference/artemis_ii_msis_drivers.csv
data/reference/artemis_ii_entry_events.json
```

Total aligned trajectory states:

```text
819
```

The NRLMSIS atmospheric state is reconstructed using the same pinned historical forcing established in Phase 2E.1.

---

# Free-Stream Velocity Assumption

The velocity used in the Mach calculation is the reconstructed Earth-relative trajectory speed.

Therefore:

```text
V_free-stream ≈ V_Earth-relative
```

This assumes:

```text
zero local atmospheric wind
```

No atmospheric wind model is currently applied.

The approximation is adequate for constructing the first modeled compressibility timeline, but the resulting Mach number remains:

```text
MODEL-DERIVED
```

rather than flight-measured.

---

# Thermal Species Model

NRLMSIS 2.0 provides the neutral species used in the acoustic mixture.

Phase 2E.2 includes the thermal species:

```text
N2
O2
O
He
H
Ar
N
```

The species are divided into:

```text
diatomic:
N2
O2
```

and:

```text
monatomic:
O
He
H
Ar
N
```

---

## Anomalous oxygen

NRLMSIS also exposes:

```text
anomalous O
```

This component is excluded from the acoustic mixture because it is not treated as a thermal species in equilibrium at the neutral temperature.

It is retained only for a sensitivity check.

Observed maximum anomalous-oxygen particle fraction across the complete entry trajectory:

```text
0.000000000000e+00 %
```

Therefore its exclusion produces no meaningful numerical effect for this trajectory.

---

# Calorically Perfect Mixture Approximation

For the exploratory free-stream acoustic model:

```text
diatomic species:
cv / R = 5/2

monatomic species:
cv / R = 3/2
```

Vibrational excitation is neglected.

For mole fractions:

\[
x_i
\]

the dimensionless constant-volume heat capacity is approximated as:

\[
\frac{c_v}{R}
=
\frac{5}{2}x_{diatomic}
+
\frac{3}{2}x_{monatomic}
\]

and the mixture specific-heat ratio is:

\[
\gamma
=
1
+
\frac{1}{c_v/R}
\]

---

# Mixture Molar Mass

The effective mixture molar mass is reconstructed using:

\[
M_{mix}
=
\sum_i x_i M_i
\]

where:

```text
x_i = mole fraction
M_i = species molar mass
```

The effective specific gas constant is then:

\[
R_{mix}
=
\frac{R_u}{M_{mix}}
\]

using:

```text
R_u = 8.31446261815324 J/(mol K)
```

---

# Modeled Speed of Sound

The Phase 2E.2 free-stream sound speed is:

\[
a
=
\sqrt{
\gamma
R_{mix}
T
}
\]

where:

```text
gamma = modeled thermal-mixture specific-heat ratio
R_mix = modeled mixture gas constant
T = NRLMSIS neutral temperature
```

The Mach number is:

\[
M
=
\frac{V}{a}
\]

where:

```text
V = Earth-relative trajectory speed
```

---

# Thermal-Mass Consistency Check

The mass density reconstructed from the modeled thermal species was independently compared against NRLMSIS total mass density.

Maximum observed relative difference:

```text
1.632719908634e-05 %
```

The worst case occurred during the high-altitude portion of the entry.

This very small difference supports internal consistency between the species composition and the total modeled atmospheric density.

---

# Exploratory Formulation Refinement

An earlier exploratory formulation included anomalous O in the acoustic mixture and reconstructed the gas constant from modeled pressure divided by total mass density.

The refined permanent formulation:

```text
excludes anomalous O
+
uses thermal species directly
+
derives mixture molar mass explicitly
```

Observed maximum change relative to the exploratory formulation:

```text
sound speed:
-8.163598558838e-06 %

Mach:
+8.163599227091e-06 %
```

The numerical change is negligible, but the refined formulation is physically cleaner and is retained permanently.

---

# Entry Interface

At:

```text
2026-04-10T23:53:30.866000Z
```

the reconstructed state is:

```text
Altitude:
121.919907 km

Earth-relative speed:
10.632214 km/s

NRLMSIS neutral temperature:
415.921 K
```

Modeled thermal-mixture properties:

```text
gamma:
1.434384762

modeled speed of sound:
436.020413 m/s
```

Formal free-stream Mach:

```text
24.384670
```

Therefore the trajectory begins inside the nominal hypersonic Mach regime.

However, the high-altitude continuum validity of this number is not yet established.

---

# Non-Monotonic Early Mach History

Mach does not decrease monotonically beginning at Entry Interface.

Although the Earth-relative spacecraft speed changes only modestly during the first tens of seconds, the modeled atmospheric temperature and composition cause the modeled sound speed to decrease substantially.

The formal free-stream Mach therefore initially rises.

Observed ascending threshold crossings include:

```text
Mach 25
2026-04-10T23:53:31.906993Z
EI + 1.041 s
120.753 km
```

```text
Mach 30
2026-04-10T23:53:38.059687Z
EI + 7.194 s
114.056 km
```

```text
Mach 35
2026-04-10T23:53:43.069316Z
EI + 12.203 s
108.856 km
```

This behavior is a property of the modeled free-stream atmosphere and should not be interpreted solely from vehicle velocity.

---

# Maximum Formal Free-Stream Mach

The permanent reconstruction identifies its maximum formal free-stream Mach at:

```text
UTC:
2026-04-10T23:53:50.866000Z

EI elapsed:
20.000 s

Altitude:
101.215372 km

Earth-relative speed:
10.650226 km/s

Neutral temperature:
182.980 K

gamma:
1.410199166

mixture molar mass:
28.166444 g/mol

effective specific gas constant:
295.190359 J/(kg K)

modeled speed of sound:
275.990073 m/s
```

Formal Mach:

```text
38.589162
```

This is classified as:

```text
MAXIMUM FORMAL FREE-STREAM MACH
```

rather than an unrestricted physical claim about continuum hypersonic flow.

A continuum-validity analysis has not yet been applied at approximately 101 km altitude.

---

# Descending Mach Threshold History

After the early maximum, Mach enters its final sustained decline.

Observed descending threshold crossings are:

```text
Mach 35
2026-04-10T23:54:39.204295Z
EI + 68.338 s
66.982 km
```

```text
Mach 30
2026-04-10T23:55:13.083443Z
EI + 102.217 s
60.488 km
```

```text
Mach 25
2026-04-10T23:56:07.544064Z
EI + 156.678 s
61.349 km
```

```text
Mach 20
2026-04-10T23:58:04.195676Z
EI + 273.330 s
63.196 km
```

```text
Mach 15
2026-04-10T23:59:27.420606Z
EI + 356.555 s
53.096 km
```

```text
Mach 10
2026-04-11T00:00:21.803535Z
EI + 410.938 s
43.684 km
```

```text
Mach 5
2026-04-11T00:01:15.681771Z
EI + 464.816 s
33.506 km
```

```text
Mach 3
2026-04-11T00:01:39.445165Z
EI + 488.579 s
28.252 km
```

```text
Mach 1.2
2026-04-11T00:02:16.569754Z
EI + 525.704 s
20.030 km
```

```text
Mach 1
2026-04-11T00:02:26.449533Z
EI + 535.584 s
17.859 km
```

```text
Mach 0.8
2026-04-11T00:02:43.862307Z
EI + 552.996 s
14.116 km
```

---

# Formal Flow-Regime Definitions

For Phase 2E.2, the following conventional categories are used:

```text
Mach >= 5.0
HYPERSONIC

1.2 <= Mach < 5.0
SUPERSONIC

0.8 <= Mach < 1.2
TRANSONIC

Mach < 0.8
SUBSONIC
```

These categories are descriptive labels for the modeled free-stream Mach timeline.

They do not replace a rarefied-flow or continuum-validity classification.

---

# Final Hypersonic Exit

The final descending Mach 5 crossing occurs at:

```text
UTC:
2026-04-11T00:01:15.681771Z

EI elapsed:
464.815771 s

Altitude:
33.505721 km

Earth-relative speed:
1535.716 m/s

Modeled speed of sound:
307.142 m/s

Mach:
5.000000
```

Phase 2E.2 labels this:

```text
formal hypersonic → supersonic transition
```

---

# Final Transonic Entry

The final descending Mach 1.2 crossing occurs at:

```text
UTC:
2026-04-11T00:02:16.569754Z

EI elapsed:
525.703754 s

Altitude:
20.029568 km

Earth-relative speed:
347.615 m/s

Modeled speed of sound:
289.678 m/s

Mach:
1.200000
```

This marks the Phase 2E.2 transition:

```text
formal supersonic → transonic
```

---

# Mach 1

The reconstructed Mach 1 crossing occurs at:

```text
UTC:
2026-04-11T00:02:26.449533Z

EI elapsed:
535.583533 s

Altitude:
17.859327 km

Earth-relative speed:
288.457 m/s

Modeled speed of sound:
288.457 m/s

Mach:
1.000000
```

---

# Final Subsonic Entry

The final descending Mach 0.8 crossing occurs at:

```text
UTC:
2026-04-11T00:02:43.862307Z

EI elapsed:
552.996307 s

Altitude:
14.116279 km

Earth-relative speed:
232.936 m/s

Modeled speed of sound:
291.170 m/s

Mach:
0.800000
```

Phase 2E.2 labels this:

```text
formal transonic → subsonic transition
```

---

# Dynamic-Pressure Context

The Phase 2E.1 early modeled dynamic-pressure peak occurs at:

```text
2026-04-10T23:55:05.866000Z
EI + 95 s
60.807901 km
```

Modeled Mach at this state:

```text
30.911622
```

The global modeled dynamic-pressure peak occurs at:

```text
2026-04-11T00:00:41.866000Z
EI + 431 s
40.042026 km
```

Modeled Mach:

```text
8.102942
```

Therefore the two nearly equal dynamic-pressure peaks occur in substantially different modeled compressibility regimes.

The first occurs at approximately:

```text
Mach 30.9
```

while the second occurs at approximately:

```text
Mach 8.1
```

This illustrates why dynamic pressure alone does not characterize the full aerothermodynamic state.

---

# Recovery Event Mach Conditions

Phase 2D independently correlated the parachute and splashdown sequence using NASA public reporting.

Phase 2E.2 evaluates the modeled free-stream Mach at those event anchors.

## Drogue altitude anchor

At the NASA-reported:

```text
23,400 ft
```

altitude anchor:

```text
EI + 593.951733 s
```

Modeled free-stream Mach:

```text
0.450737
```

Therefore the drogue altitude anchor is well inside the formal subsonic regime.

---

## Main parachute altitude anchor

At:

```text
5,400 ft
```

or:

```text
EI + 674.814532 s
```

Modeled free-stream Mach:

```text
0.183603
```

---

## Splashdown-correlated surface crossing

At the Phase 2D derived surface crossing:

```text
EI + 817.957676 s
```

Modeled free-stream Mach:

```text
0.026717
```

This value is derived from the modeled sound speed and Earth-relative terminal trajectory speed.

It is not a NASA-reported splashdown Mach number.

---

# Composition-Aware Versus Constant Dry-Air Model

A sensitivity calculation also evaluates the simpler approximation:

```text
gamma = 1.4
R = 287.05287 J/(kg K)
```

while retaining the same NRLMSIS neutral temperature.

At Entry Interface, the composition-aware atmosphere differs noticeably because the upper-atmosphere mixture has a substantial monatomic fraction.

The exploratory Entry Interface comparison gave:

```text
composition-aware Mach:
24.384670

constant-dry-air Mach:
26.005995
```

Difference:

```text
-6.234428%
```

However, lower in the atmosphere the difference rapidly becomes small.

Maximum absolute Mach difference at or below:

```text
80 km:
0.064422236%
```

At or below:

```text
60 km:
0.062820488%
```

Therefore the composition-aware treatment is most important in the high-altitude portion of the trajectory.

The final lower-atmosphere flow-regime transitions are comparatively insensitive to the dry-air approximation.

---

# Permanent Implementation

Created:

```text
scripts/analysis/build_entry_mach.py
```

The analysis:

1. loads the validated Earth-fixed trajectory;
2. loads the Phase 2E.1 modeled atmosphere;
3. loads the pinned MSIS drivers;
4. reruns NRLMSIS 2.0 to obtain thermal neutral species;
5. excludes anomalous oxygen from the acoustic mixture;
6. computes thermal species mole fractions;
7. computes modeled mixture gamma;
8. computes modeled mixture molar mass;
9. computes modeled specific gas constant;
10. computes modeled free-stream sound speed;
11. computes modeled free-stream Mach;
12. classifies formal flow regime;
13. reconstructs all ascending and descending Mach-threshold crossings;
14. identifies the maximum formal Mach state;
15. correlates Mach with Phase 2D recovery events;
16. performs dry-air sensitivity analysis;
17. writes deterministic documentation figures.

Generated processed products:

```text
data/processed/entry/entry_mach.csv
data/processed/entry/entry_mach_summary.json
```

These remain ignored under:

```text
data/processed/
```

---

# Documentation Figures

Created:

```text
docs/assets/entry/phase2e_mach_history.svg
docs/assets/entry/phase2e_flow_regime_timeline.svg
```

The Mach-history figure shows:

```text
Entry Interface
initial formal Mach rise
formal maximum Mach
final Mach decline
Mach-regime thresholds
```

The flow-regime timeline maps the reconstructed trajectory into:

```text
hypersonic
supersonic
transonic
subsonic
```

using the Phase 2E.2 threshold definitions.

SVG output follows the project's deterministic plotting configuration.

---

# Independent Validator

Created:

```text
scripts/validation/validate_entry_mach.py
```

The validator independently reconstructs the thermal mixture and verifies:

```text
gamma
specific gas constant
speed of sound
Mach number
maximum Mach state
thermal-species mass consistency
anomalous-O contribution
Mach threshold crossing structure
final flow-regime transitions
recovery-event Mach conditions
dry-air sensitivity
documentation figures
```

---

# Validation Results

Records checked:

```text
819
```

Independent reconstruction errors:

```text
Maximum gamma error:
0.000000000000e+00

Maximum specific-gas-constant error:
0.000000000000e+00 J/(kg K)

Maximum sound-speed error:
0.000000000000e+00 m/s

Maximum Mach error:
0.000000000000e+00
```

Result:

```text
PASS
```

---

## Maximum-Mach validation

Observed:

```text
UTC:
2026-04-10T23:53:50.866000Z

Altitude:
101.215372 km

Mach:
38.589162
```

The validator requires the maximum to occur:

```text
EI + 15 to 25 s
```

at altitude:

```text
95 to 105 km
```

and formal Mach:

```text
38 to 39
```

Result:

```text
PASS
```

---

## Threshold crossing-count validation

Expected crossing structure:

```text
Mach 35:
2 crossings

Mach 30:
2 crossings

Mach 25:
2 crossings

Mach 20:
1 crossing

Mach 15:
1 crossing

Mach 10:
1 crossing

Mach 5:
1 crossing

Mach 3:
1 crossing

Mach 1.2:
1 crossing

Mach 1:
1 crossing

Mach 0.8:
1 crossing
```

The duplicate crossings of Mach:

```text
25
30
35
```

result from the initial modeled Mach rise followed by the final decline.

The permanent output matches this expected topology.

Result:

```text
PASS
```

---

## Thermal-mixture validation

Observed maximum anomalous-O particle fraction:

```text
0.000000000000e+00%
```

Observed maximum difference between thermal-species reconstructed mass density and stored NRLMSIS total mass density:

```text
1.632719908634e-05%
```

Result:

```text
PASS
```

---

## Flow-transition validation

Validated final transitions:

```text
Hypersonic → Supersonic
EI + 464.815771 s
33.505721 km

Supersonic → Transonic
EI + 525.703754 s
20.029568 km

Mach 1
EI + 535.583533 s
17.859327 km

Transonic → Subsonic
EI + 552.996307 s
14.116279 km
```

Result:

```text
PASS
```

---

## Recovery validation

Modeled free-stream Mach:

```text
Drogue altitude anchor:
0.450737

Main altitude anchor:
0.183603

Splashdown-correlated surface crossing:
0.026717
```

All recovery anchors satisfy the expected low-Mach sanity checks.

Result:

```text
PASS
```

---

# Permanent Validation Result

Observed:

```text
OK: thermal-mixture sound speed,
formal free-stream Mach,
and flow-regime transitions validated.
```

---

# Interpretation Limits

The Phase 2E.2 Mach number is a:

```text
MODEL-DERIVED FREE-STREAM ESTIMATE
```

It assumes:

```text
Earth-relative velocity ≈ air-relative velocity
```

and therefore neglects atmospheric winds.

The modeled gas is treated as:

```text
ideal
calorically perfect
neutral
```

with:

```text
vibrational excitation neglected
```

The result does not model:

```text
shock-layer conditions
normal-shock temperature
real-gas thermodynamics
vibrational excitation
dissociation
ionization
plasma chemistry
chemical nonequilibrium
radiative heating
convective heating
TPS response
```

The maximum formal Mach occurs at approximately:

```text
101 km altitude
```

where rarefied-flow effects may be important.

Therefore:

```text
Mach 38.589162
```

is retained as a formal ideal-mixture free-stream estimate until continuum validity is evaluated.

---

# Phase 2E.2 Status

The reconstructed entry now includes a complete modeled compressibility timeline:

```text
Entry Interface
M ≈ 24.38

→ formal Mach rise

→ M25 ascending
→ M30 ascending
→ M35 ascending

→ formal maximum
M ≈ 38.59
EI + 20 s
101.2 km

→ final Mach decline

→ M35
→ M30
→ M25
→ M20
→ M15
→ M10

→ M5
formal hypersonic exit
33.5 km

→ M3

→ M1.2
formal transonic entry
20.0 km

→ M1
17.9 km

→ M0.8
formal subsonic entry
14.1 km

→ drogue deployment anchor
M ≈ 0.451

→ main parachute anchor
M ≈ 0.184

→ splashdown-correlated surface crossing
M ≈ 0.027
```

Phase 2E.2 status:

```text
COMPLETE
```

Before using the highest-altitude Mach estimates for aerothermal interpretation, the next step should evaluate rarefaction and continuum validity.

---

# Phase 2E.3 — Body-Scale Rarefaction and Continuum Validity

## Goal

Determine where the Artemis II reconstructed entry transitions from rarefied flow toward body-scale continuum behavior before applying any continuum aerothermal heating correlation.

Previous Phase 2E work established:

```text
flight-derived trajectory
+
NRLMSIS atmosphere
→ modeled density
→ modeled dynamic pressure
→ modeled free-stream Mach
```

Phase 2E.3 adds:

```text
modeled thermal particle number density
+
reference collision model
+
Orion characteristic length
→ mean free path
→ body-scale Knudsen number
→ rarefaction classification
```

This phase does not calculate heating.

Its purpose is to determine where continuum-based aerodynamic or aerothermal interpretations become increasingly defensible at the whole-vehicle scale.

---

# Provenance

Thermal particle number density originates from the NRLMSIS-based thermal mixture reconstructed in Phase 2E.2.

It is:

```text
MODEL-DERIVED
```

The reference hard-sphere mean free path is:

```text
MODEL
```

The body-scale Knudsen number and flow-regime classification are:

```text
MODEL-DERIVED
```

No Knudsen number in Phase 2E.3 is a NASA-reported flight quantity.

---

# Characteristic Length

Phase 2E.3 uses:

```text
L = 5.0 m
```

as the characteristic body scale.

This corresponds to the approximately:

```text
16.5 ft / 5 m
```

diameter of the Orion crew module and heat shield reported by NASA.

The resulting Knudsen number is therefore explicitly called:

```text
BODY-SCALE KNUDSEN NUMBER
```

rather than a universal or local Knudsen number.

---

# Mean-Free-Path Approximation

The Phase 2E.3 reference mean free path uses the hard-sphere kinetic-theory relation:

\[
\lambda
=
\frac{
1
}{
\sqrt{2}
\pi
d^2
n
}
\]

where:

```text
lambda = reference mean free path
d      = effective hard-sphere collision diameter
n      = modeled thermal particle number density
```

Reference effective collision diameter:

```text
d = 3.7e-10 m
```

or:

```text
3.7 Å
```

This is an approximate effective collision diameter for air.

The model does not calculate multicomponent collision integrals or species-dependent collision cross sections.

---

# Body-Scale Knudsen Number

The body-scale Knudsen number is:

\[
Kn
=
\frac{\lambda}{L}
\]

with:

```text
L = 5.0 m
```

The Phase 2E.3 descriptive classifications are:

```text
Kn < 0.01
CONTINUUM

0.01 <= Kn < 0.1
SLIP

0.1 <= Kn < 10
TRANSITION

Kn >= 10
FREE MOLECULAR
```

A supplementary:

```text
Kn = 0.001
```

threshold is retained as a deeper-continuum reference.

---

# Entry Interface

At:

```text
2026-04-10T23:53:30.866000Z
```

with altitude:

```text
121.919907 km
```

and modeled free-stream Mach:

```text
24.384670
```

the modeled thermal particle number density is:

```text
3.355249486709e+17 m^-3
```

The reference mean free path is:

```text
4.900121659 m
```

Using the 5 m Orion characteristic length:

```text
Kn = 0.980024332
```

Classification:

```text
TRANSITION
```

Therefore Entry Interface is not treated as body-scale continuum flow under the Phase 2E.3 model.

---

# Maximum Formal Mach State

Phase 2E.2 identified its maximum formal free-stream Mach at:

```text
UTC:
2026-04-10T23:53:50.866000Z

EI elapsed:
20.000 s

Altitude:
101.215372 km

Mach:
38.589162
```

At this state:

```text
thermal particle number density:
1.032751434043e+19 m^-3

reference mean free path:
0.159197365 m

body-scale Kn:
0.031839473
```

Classification:

```text
SLIP
```

This substantially improves the interpretation of the Phase 2E.2 result.

The value:

```text
Mach 38.589162
```

occurs before the reconstructed entry reaches the nominal body-scale continuum threshold.

It should therefore remain described as:

```text
MAXIMUM FORMAL FREE-STREAM MACH
```

rather than as an unrestricted continuum-flow aerodynamic Mach condition.

---

# Rarefaction Threshold Timeline

## Transition to Slip

The descending:

```text
Kn = 0.1
```

crossing occurs at:

```text
UTC:
2026-04-10T23:53:44.603030Z

EI elapsed:
13.737030 s

Altitude:
107.309481 km

Mach:
36.256967

Mean free path:
0.500000000 m
```

This marks the Phase 2E.3 body-scale:

```text
TRANSITION → SLIP
```

boundary.

---

## Slip to Continuum

The descending:

```text
Kn = 0.01
```

crossing occurs at:

```text
UTC:
2026-04-10T23:53:58.784054Z

EI elapsed:
27.918054 s

Altitude:
94.025448 km

Mach:
37.793429

Mean free path:
0.050000000 m
```

This marks the nominal Phase 2E.3 body-scale:

```text
SLIP → CONTINUUM
```

boundary.

The label is intentionally body-scale only.

It does not establish continuum validity for every local shock-layer or boundary-layer gradient.

---

## Deep-Continuum Reference

The descending:

```text
Kn = 0.001
```

crossing occurs at:

```text
UTC:
2026-04-10T23:54:16.115112Z

EI elapsed:
45.249112 s

Altitude:
80.330899 km

Mach:
38.262468

Mean free path:
0.005000000 m
```

Phase 2E.3 retains this as a:

```text
DEEP CONTINUUM REFERENCE
```

rather than a separate fundamental flow-regime boundary.

---

# Selected Rarefaction Evolution

The read-only inspection produced the following representative body-scale behavior:

```text
120 km
Kn = 7.906652e-01
TRANSITION

110 km
Kn = 1.667895e-01
TRANSITION

100 km
Kn = 2.589168e-02
SLIP

90 km
Kn = 5.286801e-03
CONTINUUM

80 km
Kn = 9.445916e-04
CONTINUUM

70 km
Kn = 1.942004e-04
CONTINUUM

60 km
Kn = 5.242558e-05
CONTINUUM

50 km
Kn = 1.546611e-05
CONTINUUM

40 km
Kn = 4.107885e-06
CONTINUUM
```

The model therefore shows a rapid reduction in body-scale rarefaction through the upper entry corridor.

---

# Collision-Diameter Sensitivity

The hard-sphere collision diameter is an approximation.

Phase 2E.3 therefore evaluates the nominal continuum boundary using:

```text
3.5 Å
3.7 Å
4.0 Å
```

collision diameters.

Observed:

```text
d = 3.5e-10 m
Kn = 0.01 altitude:
93.303912 km
```

```text
d = 3.7e-10 m
Kn = 0.01 altitude:
94.025448 km
```

```text
d = 4.0e-10 m
Kn = 0.01 altitude:
95.029468 km
```

Total altitude spread:

```text
1.725556 km
```

The nominal body-scale continuum threshold is therefore relatively insensitive to this reasonable collision-diameter range for the intended Phase 2E.3 interpretation.

---

# Dynamic-Pressure Peak Context

Phase 2E.1 reconstructed two nearly equal dominant modeled dynamic-pressure peaks.

Phase 2E.3 evaluates body-scale Knudsen number at both.

## Global modeled dynamic-pressure peak

At:

```text
2026-04-11T00:00:41.866000Z
```

with:

```text
Altitude:
40.042026 km

Mach:
8.102942

Dynamic pressure:
12.808389 kPa
```

the body-scale Knudsen number is:

```text
4.132698035660e-06
```

Classification:

```text
CONTINUUM
```

---

## Early modeled dynamic-pressure peak

At:

```text
2026-04-10T23:55:05.866000Z
```

with:

```text
Altitude:
60.807901 km

Mach:
30.911621

Dynamic pressure:
12.798779 kPa
```

the body-scale Knudsen number is:

```text
5.717446655451e-05
```

Classification:

```text
CONTINUUM
```

Both dominant modeled dynamic-pressure peaks therefore occur far below:

```text
Kn = 0.01
```

and also below:

```text
Kn = 0.001
```

under the Phase 2E.3 whole-body model.

This substantially strengthens the continuum interpretation of those dynamic-pressure states compared with the highest-altitude portion of the trajectory.

---

# Permanent Implementation

Created:

```text
data/reference/artemis_ii_rarefaction_model.json
```

This file defines:

```text
characteristic length
reference collision diameter
collision-diameter sensitivity range
body-scale regime thresholds
model interpretation limits
source provenance
```

Created:

```text
scripts/analysis/build_entry_rarefaction.py
```

The analysis:

1. loads the Phase 2E.2 Mach reconstruction;
2. loads the permanent rarefaction-model definition;
3. calculates reference hard-sphere mean free path;
4. calculates body-scale Knudsen number;
5. classifies body-scale rarefaction regime;
6. reconstructs Kn threshold crossings;
7. performs collision-diameter sensitivity analysis;
8. evaluates rarefaction at the maximum formal Mach state;
9. evaluates rarefaction at the two dominant dynamic-pressure peaks;
10. creates deterministic documentation figures.

Generated processed products:

```text
data/processed/entry/entry_rarefaction.csv
data/processed/entry/entry_rarefaction_summary.json
```

These remain ignored.

---

# Documentation Figures

Created:

```text
docs/assets/entry/phase2e_knudsen_history.svg
docs/assets/entry/phase2e_knudsen_altitude.svg
```

The first figure shows body-scale Knudsen number through time.

The second shows body-scale Knudsen number as a function of trajectory altitude.

Both use logarithmic Knudsen scaling because the modeled quantity changes across many orders of magnitude.

---

# Independent Validation

Created:

```text
scripts/validation/validate_entry_rarefaction.py
```

The validator independently recalculates:

```text
mean free path
body-scale Knudsen number
rarefaction classification
Kn threshold crossings
collision-diameter sensitivity
dynamic-pressure-peak rarefaction
```

Observed reconstruction errors:

```text
Maximum mean-free-path error:
0.000000000000e+00 m

Maximum Knudsen-number error:
0.000000000000e+00
```

Result:

```text
PASS
```

---

# Threshold Validation

Independently reconstructed:

```text
Kn = 0.1
EI + 13.737030 s
107.309481 km
```

```text
Kn = 0.01
EI + 27.918054 s
94.025448 km
```

```text
Kn = 0.001
EI + 45.249112 s
80.330899 km
```

All lie within the permanent validation windows.

Result:

```text
PASS
```

---

# Sensitivity Validation

Observed `Kn=0.01` altitude spread over the permanent collision-diameter sensitivity range:

```text
1.725556 km
```

Validation requirement:

```text
< 2 km
```

Result:

```text
PASS
```

---

# Dynamic-Pressure Peak Validation

The validator requires both dominant dynamic-pressure peaks to satisfy:

```text
Kn < 0.001
```

Observed:

```text
Global q peak:
4.132698035660e-06

Early q peak:
5.717446655451e-05
```

Both pass by a large margin.

Result:

```text
PASS
```

---

# Permanent Validation Result

Observed:

```text
OK: body-scale mean free path,
Knudsen number,
rarefaction classification,
and sensitivity validated.
```

---

# Interpretation Limits

The Phase 2E.3 result is explicitly a:

```text
BODY-SCALE RAREFACTION INDICATOR
```

It is not:

```text
a local gradient-length Knudsen number
a shock-layer breakdown parameter
a boundary-layer Knudsen number
a DSMC solution
a Navier-Stokes validity proof
a chemical-nonequilibrium model
```

The reference mean free path uses a single effective hard-sphere collision diameter rather than a full multicomponent collision-integral treatment.

The 5 m characteristic length represents the full Orion crew-module / heat-shield body scale.

Local flow structures can have much smaller characteristic gradient lengths and therefore larger local Knudsen numbers.

Consequently:

```text
Kn < 0.01
```

in Phase 2E.3 should be interpreted as:

```text
nominal whole-body continuum behavior
```

rather than universal local continuum validity.

---

# Phase 2E.3 Status

The reconstructed entry now contains a body-scale rarefaction timeline:

```text
Entry Interface
121.9 km
Kn ≈ 0.98
TRANSITION

→

Kn = 0.1
107.3 km
transition → slip

→

Maximum formal Mach
101.2 km
Mach ≈ 38.59
Kn ≈ 0.0318
SLIP

→

Kn = 0.01
94.0 km
nominal body-scale continuum threshold

→

Kn = 0.001
80.3 km
deep-continuum reference

→

Early dynamic-pressure peak
60.8 km
Mach ≈ 30.91
Kn ≈ 5.72e-05
CONTINUUM

→

Global dynamic-pressure peak
40.0 km
Mach ≈ 8.10
Kn ≈ 4.13e-06
CONTINUUM
```

Phase 2E.3 status:

```text
COMPLETE
```

The next aerothermal phase may now apply continuum-based correlations only inside an explicitly bounded region rather than blindly extending them to Entry Interface.

---

# Phase 2E.4 — Sutton–Graves Stagnation-Point Convective Heating

## Goal

Add a bounded low-fidelity aerothermal reconstruction to the Artemis II entry analysis after establishing:

```text
trajectory
→ Earth-fixed geometry
→ atmospheric state
→ dynamic pressure
→ free-stream Mach
→ body-scale rarefaction
```

Phase 2E.4 introduces a stagnation-point convective-heating engineering correlation while explicitly restricting primary interpretation to the portion of the trajectory where:

```text
body-scale Kn < 0.01
AND
Mach >= 5
```

The stronger continuum sensitivity region is:

```text
body-scale Kn < 0.001
AND
Mach >= 5
```

The full-trajectory mathematical integral is retained only as a diagnostic quantity.

---

# Provenance

Input trajectory velocity:

```text
DERIVED_FROM_NASA_FLIGHT_DERIVED_EPHEMERIS
```

Atmospheric density:

```text
MODEL
NRLMSIS 2.0
```

Sutton–Graves heat flux:

```text
MODEL_DERIVED
```

Integrated convective heat load:

```text
MODEL_DERIVED
```

The resulting heating history is not NASA flight telemetry and is not an Artemis II measured TPS heat-flux history.

---

# Permanent Model Definition

Created:

```text
data/reference/artemis_ii_convective_heating_model.json
```

The model definition permanently records:

```text
Sutton–Graves Earth constant
Orion reference nose radius
density provenance
velocity assumption
continuum/hypersonic domain gates
nose-radius sensitivity definition
source provenance
interpretation limits
```

No Artemis II-specific calibration multiplier is applied.

---

# Sutton–Graves Correlation

The permanent low-fidelity convective-heating model uses:

\[
\dot q
=
k
\sqrt{
\frac{\rho_\infty}{R_n}
}
V_\infty^3
\]

where:

```text
q_dot = stagnation-point convective heat flux
k     = Earth Sutton–Graves constant
rho   = modeled free-stream atmospheric density
Rn    = reference nose radius
V     = free-stream velocity approximation
```

Permanent Earth constant:

```text
k = 1.74153e-4
```

with the SI implementation used in the model producing:

```text
W/m²
```

from:

```text
rho in kg/m³
Rn in m
V in m/s
```

The correlation is treated as a:

```text
cold-wall engineering stagnation-point correlation
```

rather than a high-fidelity Orion aerothermal solution.

---

# Orion Reference Geometry

Phase 2E.4 uses:

```text
Rn = 6.035 m
```

as the reference nose radius.

The value comes from NASA Orion EFT-1 heritage/reference geometry.

The project therefore labels it:

```text
ORION_EFT1_HERITAGE_REFERENCE
```

and explicitly does not claim:

```text
6.035 m = Artemis II as-flown effective stagnation radius
```

until an Artemis II-specific authoritative geometry source is identified.

---

# Velocity Assumption

The Sutton–Graves relation uses the same free-stream velocity approximation established earlier in Phase 2E:

```text
V_free-stream ≈ V_Earth-relative
```

No local atmospheric wind model is applied.

Therefore:

```text
Earth-relative trajectory velocity
```

is used as the velocity input to the heating correlation.

---

# Density Input

Atmospheric density is:

```text
NRLMSIS 2.0 modeled total mass density
```

from Phase 2E.1.

It is not measured atmospheric density along the Artemis II trajectory.

---

# Entry Interface

At Entry Interface:

```text
UTC:
2026-04-10T23:53:30.866000Z

Altitude:
121.919907 km

Mach:
24.384670

Body-scale Kn:
0.980024332

Density:
1.453686149233e-08 kg/m³

Velocity:
10.632214 km/s
```

The formal Sutton–Graves result is:

```text
1.027304 W/cm²
```

However:

```text
Kn ≈ 0.98
```

places Entry Interface in the Phase 2E.3 body-scale transition regime.

Therefore this value is retained only as a:

```text
FORMAL DIAGNOSTIC RESULT
```

and is not continuum-qualified.

---

# Maximum Formal Mach State

Phase 2E.2 identified maximum formal free-stream Mach at:

```text
UTC:
2026-04-10T23:53:50.866000Z

EI elapsed:
20.000 s

Altitude:
101.215372 km

Mach:
38.589162

Body-scale Kn:
0.031839473
```

Formal Sutton–Graves heat flux:

```text
5.951922 W/cm²
```

The state remains in the Phase 2E.3:

```text
SLIP
```

regime.

It is therefore not used as a primary continuum-qualified heating state.

---

# Continuum Gates

## Nominal body-scale continuum boundary

The descending:

```text
Kn = 0.01
```

boundary occurs at:

```text
UTC:
2026-04-10T23:53:58.784054Z

EI elapsed:
27.918054 s

Altitude:
94.025448 km

Mach:
37.793429
```

Interpolated Sutton–Graves heat flux:

```text
10.740910 W/cm²
```

This boundary defines the start of the permanent:

```text
PRIMARY HEATING DOMAIN
```

subject also to:

```text
Mach >= 5
```

---

## Stronger continuum boundary

The descending:

```text
Kn = 0.001
```

boundary occurs at:

```text
UTC:
2026-04-10T23:54:16.115112Z

EI elapsed:
45.249112 s

Altitude:
80.330899 km

Mach:
38.262468
```

Interpolated Sutton–Graves heat flux:

```text
34.071681 W/cm²
```

This defines the start of the:

```text
STRONGER CONTINUUM SENSITIVITY DOMAIN
```

subject again to:

```text
Mach >= 5
```

---

# Qualified Sutton–Graves Peak

The maximum formal Sutton–Graves heat flux occurs at:

```text
UTC:
2026-04-10T23:54:55.866000Z

EI elapsed:
85.000 s

Altitude:
61.878469 km

Earth-relative speed:
9.984103 km/s

Mach:
32.285653

Body-scale Kn:
6.547686230258e-05

NRLMSIS density:
2.414985356154e-04 kg/m³
```

Sutton–Graves heat flux:

```text
109.641953 W/cm²
```

The same state is simultaneously:

```text
global formal SG peak
primary-domain SG peak
stronger-continuum-domain SG peak
```

because:

```text
Kn << 0.001
```

and:

```text
Mach >> 5
```

at the peak.

Therefore the reconstructed peak itself does not depend on extrapolating the continuum correlation into the high-altitude rarefied-flow portion of the trajectory.

---

# Heating Peak Versus Dynamic-Pressure Peaks

Phase 2E.1 identified two nearly equal dominant dynamic-pressure peaks.

Phase 2E.4 shows that their aerothermal conditions are dramatically different.

## Early dynamic-pressure peak

At:

```text
UTC:
2026-04-10T23:55:05.866000Z

EI elapsed:
95.000 s

Altitude:
60.807901 km

Mach:
30.911621

Dynamic pressure:
12.798779 kPa
```

the Sutton–Graves heat flux is:

```text
104.975953 W/cm²
```

This occurs:

```text
+10.000 s
```

after the Sutton–Graves heating peak.

The early dynamic-pressure maximum therefore occurs near the main convective-heating pulse.

---

## Global dynamic-pressure peak

At:

```text
UTC:
2026-04-11T00:00:41.866000Z

EI elapsed:
431.000 s

Altitude:
40.042026 km

Mach:
8.102942

Dynamic pressure:
12.808389 kPa
```

the Sutton–Graves heat flux is only:

```text
7.596440 W/cm²
```

This occurs:

```text
+346.000 s
```

after the Sutton–Graves peak.

Although the two dynamic-pressure maxima differ by only approximately:

```text
0.075%
```

their Sutton–Graves heating levels differ by more than an order of magnitude.

This follows naturally from the different functional dependencies.

Dynamic pressure behaves as:

\[
q
\propto
\rho V^2
\]

while the Sutton–Graves correlation behaves as:

\[
\dot q
\propto
\sqrt{\rho}V^3
\]

The much stronger velocity dependence causes convective heating to peak earlier in entry while the vehicle retains substantially greater speed.

---

# Final Hypersonic Boundary

Phase 2E.2 identified the final descending:

```text
Mach = 5
```

crossing at:

```text
UTC:
2026-04-11T00:01:15.681771Z

EI elapsed:
464.815771 s
```

Sutton–Graves heat flux at this boundary:

```text
2.595809202 W/cm²
```

The permanent primary and stronger heating domains terminate here.

This prevents the hypersonic stagnation-heating correlation from being presented as physically meaningful throughout parachute descent and recovery.

---

# Integrated Convective Heat Load

Heat load is calculated by numerical integration:

\[
Q
=
\int
\dot q\,dt
\]

using trapezoidal integration across the reconstructed high-rate entry history.

---

## Formal full-trajectory diagnostic integral

Mathematically integrating Sutton–Graves over the entire trajectory gives:

```text
164.401704626 MJ/m²
```

This value is retained for accounting and sensitivity only.

It is not the project's primary reported convective heat load because the integration includes regions outside the intended continuum/hypersonic interpretation domain.

---

## Contribution before nominal continuum

Formal contribution prior to:

```text
Kn = 0.01
```

is:

```text
1.192062485 MJ/m²
```

or:

```text
0.725091317%
```

of the formal full-trajectory integral.

Therefore the rarefied upper-entry section contributes less than one percent of the formal Sutton–Graves integral.

---

# Primary Convective Heat Load

Permanent primary domain:

```text
Kn < 0.01
AND
Mach >= 5
```

Integrated convective heat load:

```text
162.686370921 MJ/m²
```

Fraction of formal full-trajectory integral:

```text
98.956620487%
```

This is the project's principal Phase 2E.4 low-fidelity convective heat-load result.

It should always be reported with its model and domain qualifiers.

---

# Stronger Continuum Sensitivity

Stronger interpretation domain:

```text
Kn < 0.001
AND
Mach >= 5
```

Integrated convective heat load:

```text
159.150073328 MJ/m²
```

Fraction of formal full-trajectory integral:

```text
96.805610191%
```

Difference from the primary-domain result:

```text
3.536297593 MJ/m²
```

or approximately:

```text
2.17%
```

of the primary-domain value.

This demonstrates that the bulk of the reconstructed Sutton–Graves convective heat load is accumulated after the trajectory is already well inside the Phase 2E.3 body-scale continuum regime.

---

# Post-Hypersonic Diagnostic Contribution

Formal contribution after the final Mach 5 crossing:

```text
0.523271220 MJ/m²
```

or:

```text
0.318288196%
```

of the formal full-trajectory integral.

Therefore nearly all of the formal Sutton–Graves integral is accumulated during the selected continuum/hypersonic interval.

This justifies terminating the permanent physical interpretation at the final Mach 5 crossing.

---

# Permanent Domain-Gating Decision

Phase 2E.4 permanently adopts:

```text
PRIMARY REPORTED DOMAIN

Kn < 0.01
AND
Mach >= 5
```

with:

```text
162.686370921 MJ/m²
```

as the primary modeled convective heat load.

The stronger sensitivity is:

```text
Kn < 0.001
AND
Mach >= 5
```

with:

```text
159.150073328 MJ/m²
```

The:

```text
164.401704626 MJ/m²
```

full-trajectory integral remains:

```text
DIAGNOSTIC ONLY
```

---

# Nose-Radius Sensitivity

The Sutton–Graves relation contains:

\[
\dot q
\propto
R_n^{-1/2}
\]

A numerical:

```text
±10%
```

radius sensitivity was evaluated.

This is explicitly:

```text
NOT
an asserted Orion geometry uncertainty
```

and exists only to characterize model sensitivity.

Cases:

```text
Rn = 5.431500 m
-10%

Peak:
115.572766 W/cm²
```

```text
Rn = 6.035000 m
reference

Peak:
109.641953 W/cm²
```

```text
Rn = 6.638500 m
+10%

Peak:
104.539500 W/cm²
```

The behavior follows the expected inverse-square-root radius dependence.

---

# Why No Artemis II Calibration Factor Was Applied

Phase 2E.4 intentionally does not tune the reconstructed heating history to:

```text
Orion EFT-1
Artemis I
or another Orion mission
```

reported heat-flux values.

Those missions differ in:

```text
entry trajectory
entry speed
flight-path geometry
atmospheric history
guidance history
wall conditions
TPS state
aerothermal modeling assumptions
```

A numerical correction factor derived from another mission would imply an unsupported level of Artemis II-specific accuracy.

Therefore the permanent model remains:

```text
Sutton–Graves
+
NRLMSIS density
+
Earth-relative velocity
+
6.035 m Orion heritage radius
```

with no artificial mission calibration.

---

# Heritage Context

Historical Orion aerothermal results may be used only as broad engineering-scale context.

They are not treated as validation targets for the Artemis II reconstruction.

Phase 2E.4 therefore distinguishes:

```text
heritage sanity scale
```

from:

```text
mission-specific validation
```

The latter would require authoritative Artemis II aerothermal data.

---

# Permanent Implementation

Created:

```text
scripts/analysis/build_entry_heating.py
```

The analysis:

```text
loads Phase 2E.3 rarefaction states
loads the permanent heating model
computes Sutton–Graves heat flux at all 819 states
identifies the formal/global heating peak
verifies that the peak lies in both qualified domains
reconstructs the Kn=0.01 boundary
reconstructs the Kn=0.001 boundary
reconstructs the final Mach 5 boundary
integrates primary heat load
integrates stronger-continuum heat load
integrates diagnostic excluded regions
evaluates nose-radius sensitivity
compares heating timing with dynamic-pressure peaks
writes deterministic documentation figures
```

Generated processed products:

```text
data/processed/entry/entry_heating.csv
data/processed/entry/entry_heating_summary.json
```

These remain ignored under:

```text
data/processed/
```

---

# Output Fields

The generated heating trajectory adds:

```text
sg_convective_heat_flux_w_m2
sg_convective_heat_flux_w_cm2
sg_formal_cumulative_heat_load_j_m2
sg_primary_domain
sg_stronger_continuum_domain
```

to the upstream reconstructed entry state.

---

# Documentation Figures

Created:

```text
docs/assets/entry/phase2e_sutton_graves_heat_flux.svg
docs/assets/entry/phase2e_sutton_graves_heat_load.svg
```

The heat-flux figure identifies the permanent domain boundaries and the Sutton–Graves heating peak.

The heat-load figure shows accumulation of the formal diagnostic integral while marking the continuum and hypersonic boundaries used for physical interpretation.

SVG generation follows the deterministic plotting configuration established in earlier phases.

---

# Independent Validation

Created:

```text
scripts/validation/validate_entry_heating.py
```

The validator independently reconstructs:

```text
Sutton–Graves heat flux
peak heating state
Kn=0.01 gate
Kn=0.001 gate
final Mach 5 gate
full formal heat load
primary-domain heat load
stronger-continuum heat load
excluded-domain contributions
nose-radius sensitivity ordering
```

---

# Numerical Reconstruction Validation

Records checked:

```text
819
```

Maximum independently reconstructed heat-flux error:

```text
0.000000000000e+00 W/m²
```

Result:

```text
PASS
```

---

# Qualified Peak Validation

Independently reconstructed:

```text
UTC:
2026-04-10T23:54:55.866000Z

EI elapsed:
85.000 s

Altitude:
61.878469 km

Heat flux:
109.641953 W/cm²

Body-scale Kn:
6.547686230258e-05
```

Permanent regression requirements include:

```text
peak time:
EI + 80 to 90 s

peak altitude:
58 to 65 km

peak heat flux:
100 to 120 W/cm²

peak Kn:
< 0.001
```

Result:

```text
PASS
```

---

# Heat-Load Validation

Independently reconstructed:

```text
Primary:
162.686370921 MJ/m²

Stronger continuum:
159.150073328 MJ/m²

Formal full trajectory:
164.401704626 MJ/m²
```

The primary-domain result contains:

```text
98.956620487%
```

of the formal total.

The validator requires:

```text
> 98%
```

Result:

```text
PASS
```

---

# Excluded-Domain Validation

Before:

```text
Kn = 0.01
```

the formal integral contributes:

```text
0.725091317%
```

Validator requirement:

```text
< 1%
```

Result:

```text
PASS
```

After final:

```text
Mach 5
```

the formal integral contributes:

```text
0.318288196%
```

Validator requirement:

```text
< 1%
```

Result:

```text
PASS
```

---

# Radius-Sensitivity Validation

The validator requires:

```text
smaller nose radius
→ higher heat flux

reference radius
→ intermediate heat flux

larger nose radius
→ lower heat flux
```

Observed:

```text
115.572766
>
109.641953
>
104.539500 W/cm²
```

Result:

```text
PASS
```

---

# Permanent Validation Result

Observed:

```text
OK: Sutton-Graves heat flux,
continuum/hypersonic domain gating,
integrated heat load,
and radius sensitivity validated.
```

---

# Interpretation Limits

The Phase 2E.4 reconstruction is:

```text
LOW-FIDELITY
MODEL-DERIVED
COLD-WALL
STAGNATION-POINT
CONVECTIVE HEATING
```

It does not include:

```text
radiative heating
finite wall temperature
Avcoat ablation
Avcoat pyrolysis
blowing
surface recession
catalytic effects
shock-layer chemical nonequilibrium
dissociation
ionization
detailed CFD
DSMC
TPS conduction
internal material temperature
bondline temperature
structural thermal response
```

The 6.035 m radius is:

```text
ORION EFT-1 HERITAGE GEOMETRY
```

and is not currently claimed to be:

```text
ARTEMIS II AS-FLOWN EFFECTIVE STAGNATION RADIUS
```

The model therefore should not be presented as a prediction of actual Artemis II TPS temperatures or heat-shield material response.

---

# Phase 2E.4 Status

The reconstructed Artemis II entry now contains a bounded low-fidelity aerothermal timeline:

```text
Entry Interface
Kn ≈ 0.98
formal SG only

→

Kn = 0.01
EI + 27.918 s
94.025 km
primary model domain begins

→

Kn = 0.001
EI + 45.249 s
80.331 km
stronger continuum domain begins

→

Qualified SG peak
EI + 85 s
61.878 km
Mach ≈ 32.29
Kn ≈ 6.55e-05
109.642 W/cm²

→

Early q peak
EI + 95 s
60.808 km
SG ≈ 104.976 W/cm²

→

Global q peak
EI + 431 s
40.042 km
SG ≈ 7.596 W/cm²

→

Mach 5
EI + 464.816 s
SG ≈ 2.596 W/cm²
primary model domain ends
```

Permanent primary heat load:

```text
162.686370921 MJ/m²
```

Stronger continuum sensitivity:

```text
159.150073328 MJ/m²
```

Formal full-trajectory diagnostic:

```text
164.401704626 MJ/m²
```

Phase 2E.4 status:

```text
COMPLETE
```

---

# Phase 2F.1 — Orion TPS Heritage Evidence and Engineering Decision Thread

## Goal

Phase 2F.1 establishes the evidence foundation connecting:

```text
Artemis I heat-shield anomaly
→ investigation
→ root cause
→ operational constraint
→ Artemis II entry mitigation
→ Artemis II flight outcome
→ long-term manufacturing corrective action
```

The purpose is not to create a new thermal-protection-system damage model.

Instead, the phase creates a provenance-controlled engineering decision thread that can later appear in the MissionLab mission-control and engineering interfaces.

Phase 2F.1 deliberately separates:

```text
Phase 2E.4:
modeled Artemis II external aerothermal environment
```

from:

```text
Phase 2F.1:
NASA-reported Orion TPS evidence,
engineering findings,
decisions,
and postflight outcomes
```

---

# Why This Phase Is Separate From Phase 2E.4

Phase 2E.4 produced a low-fidelity external stagnation-point convective-heating reconstruction using:

```text
Sutton–Graves
+
NRLMSIS 2.0 density
+
Earth-relative velocity
+
Orion heritage nose radius
```

That model reconstructs an external heating environment.

It does not calculate:

```text
Avcoat internal temperature
pyrolysis
gas generation
gas transport
permeability
internal pressure
crack formation
char liberation
surface recession
bondline temperature
TPS structural response
```

NASA's Artemis I investigation showed that the unexpected heat-shield phenomenon depended on material permeability, internal gas-pressure accumulation, and thermal time history.

Therefore:

```text
external heat flux
```

cannot be converted directly into:

```text
char-loss quantity
damage probability
recession depth
or TPS failure probability
```

Phase 2F.1 preserves that separation explicitly.

---

# Source Philosophy

Phase 2F.1 uses authoritative NASA material only.

Permitted source hosts in the permanent validator are:

```text
www.nasa.gov
nasa.gov
ntrs.nasa.gov
```

The evidence catalog contains:

```text
17 evidence records
10 evidence categories
5 unique source URLs
```

Source hosts represented:

```text
www.nasa.gov
ntrs.nasa.gov
```

All evidence records use:

```text
NASA_REPORTED
```

provenance.

The derived thread uses:

```text
DERIVED_FROM_NASA_REPORTED_EVIDENCE
```

provenance.

---

# Permanent Evidence Catalog

Created:

```text
data/reference/artemis_tps_evidence.json
```

Dataset identifier:

```text
phase2f1_orion_tps_heritage_evidence
```

Mission:

```text
Artemis II
```

Scope:

```text
Orion thermal protection system heritage,
Artemis I heat-shield anomaly/root cause,
Artemis II mitigation,
and Artemis II postflight outcome
```

---

# Evidence Inventory

The permanent evidence catalog contains 17 records.

## Orion TPS architecture

```text
orion_heat_shield_architecture
```

NASA reports that Orion's ablative heat shield is:

```text
16.5 ft diameter
```

and its outer heat-shield surface uses:

```text
186 Avcoat blocks
```

Avcoat is bonded to the underlying structural heat-shield system.

This record provides physical TPS context.

It is not itself part of the anomaly decision sequence.

---

## Avcoat functional behavior

```text
avcoat_function
```

Avcoat is an ablative material designed to lose material in a controlled fashion during entry.

This transfers thermal energy away from the vehicle.

This distinction is important because:

```text
controlled ablation
```

is expected TPS behavior, whereas:

```text
unexpected cracking and char liberation
```

was the Artemis I anomaly.

This record is contextual rather than a decision-thread event.

---

# Artemis I Anomaly

Evidence record:

```text
artemis_i_unexpected_char_loss
```

Postflight inspection identified unexpected loss of charred Avcoat material from portions of the Artemis I Orion heat shield.

The spacecraft completed the mission safely.

The anomaly therefore represented:

```text
unexpected TPS material behavior
```

rather than:

```text
loss of crew protection
```

NASA nevertheless initiated an extensive root-cause investigation before committing crew to the next mission.

---

# Investigation Evidence

NASA's investigation did not rely on a single model or visual inspection.

The evidence program included:

```text
flight instrumentation
physical sample extraction
nondestructive evaluation
material analysis
thermal testing
aerothermal testing
hypersonic testing
modeling and simulation
root-cause analysis
independent review
```

---

# Artemis I Flight Instrumentation

Evidence record:

```text
artemis_i_instrumentation
```

NASA reports that the Artemis I heat shield was heavily instrumented with:

```text
pressure sensors
strain gauges
thermocouples
```

at varying depths in the ablative material.

These measurements supported:

```text
computer-model validation
entry-environment reconstruction
internal-temperature profiles
timing analysis of char loss
```

MissionLab does not possess these complete raw internal TPS sensor histories.

Therefore Phase 2E.4 quantities must not be represented as equivalent to this instrumentation.

---

# Postflight Sample Campaign

Evidence record:

```text
artemis_i_sample_campaign
```

NASA removed approximately:

```text
200 Avcoat samples
```

from the Artemis I heat shield for analysis and inspection.

Nondestructive evaluation was also used to examine internal material condition.

The root-cause determination therefore included extensive physical examination of the flown heat shield.

---

# Thermal Test Campaign

Evidence record:

```text
artemis_i_thermal_test_campaign
```

NASA reports:

```text
8 postflight thermal test campaigns
```

comprising:

```text
121 individual tests
```

These included facilities capable of investigating:

```text
convective heating
radiative heating
combined convective/radiative heating
full-block behavior
hypersonic flow
material permeability
microstructure
```

MissionLab does not reproduce this test campaign.

The test counts are retained only as NASA-reported evidence of investigation depth.

---

# Ground Replication

Evidence record:

```text
artemis_i_ground_replication
```

NASA was able to reproduce the relevant cracking/char-loss phenomenon under reconstructed conditions during the investigation.

This provides stronger causal evidence than postflight visual correlation alone.

The MissionLab decision thread therefore treats ground replication as part of:

```text
EVIDENCE_COLLECTION
```

rather than as an independent MissionLab model result.

---

# Artemis I Root Cause

Evidence record:

```text
artemis_i_root_cause_low_permeability
```

The investigation determined that gases generated within the ablative Avcoat could not escape adequately from portions of material with insufficient permeability.

The resulting sequence was:

```text
entry heating
→ Avcoat thermal response / pyrolysis
→ gas generation
→ restricted venting
→ internal pressure accumulation
→ cracking
→ liberation of charred material
```

The essential engineering parameter was therefore not simply:

```text
peak external heat flux
```

but also:

```text
material permeability
+
internal gas transport
+
thermal time history
```

---

# Role of the Artemis I Skip Entry

Evidence record:

```text
artemis_i_skip_entry_role
```

Artemis I used skip-guidance entry.

During the period between atmospheric encounters:

```text
external heating rate decreased
```

while:

```text
thermal energy remained within the Avcoat
```

NASA's investigation found that this thermal history contributed to continued gas generation and accumulation inside insufficiently permeable material.

This is an important MissionLab interpretation boundary.

A single peak-heating value cannot reproduce this mechanism.

---

# Permeable Versus Less-Permeable Regions

Evidence record:

```text
permeable_regions_did_not_show_same_behavior
```

NASA reported that local Avcoat regions identified as permeable before flight did not show the same cracking or char-loss behavior.

Those regions allowed gases produced during ablation to vent.

This observation strongly supported:

```text
permeability
```

as a key root-cause parameter.

MissionLab does not infer a numerical permeability threshold because no such project-qualified threshold is present in the public evidence catalog.

---

# Engineering Constraint for Artemis II

The Artemis II heat shield had already been produced and integrated while the Artemis I investigation was underway.

NASA's engineering problem therefore became:

```text
Can the existing Artemis II heat shield
be flown safely with operational changes?
```

The investigation and ground-test program established acceptable flight rationale for doing so.

The permanent decision thread represents this as:

```text
CONSTRAINT
```

between:

```text
ROOT_CAUSE
```

and:

```text
DECISION_AND_ACTION
```

---

# Artemis II Trajectory Mitigation

Evidence records:

```text
artemis_ii_trajectory_mitigation
artemis_ii_no_skip_entry
```

NASA modified the Artemis II entry profile to reduce exposure to the conditions associated with the Artemis I phenomenon.

Public NASA reporting describes the change as:

```text
shortening the distance Orion travels
between atmospheric entry and splashdown
```

and NASA technical reporting states that Artemis II flew:

```text
without the Artemis I-style skip entry
```

in order to minimize the crack-inducing conditions identified by the investigation.

This is a direct example of:

```text
hardware evidence
→ environment understanding
→ operational mitigation
```

---

# Artemis II Postflight Outcome

Phase 2F.1 includes four postflight evidence records:

```text
artemis_ii_postflight_tps_expected
artemis_ii_char_loss_reduced
artemis_ii_arcjet_consistency
artemis_ii_entry_velocity_prediction
```

---

# TPS Performance

NASA's initial Artemis II assessment reported:

```text
thermal protection system performed as expected
```

with:

```text
no unusual conditions identified
```

This is treated as an initial postflight assessment.

It is not assumed to be the final detailed heat-shield material-analysis result.

---

# Artemis II Char-Loss Outcome

NASA reported that the Artemis I-type char-loss behavior was:

```text
significantly reduced
```

on Artemis II in both:

```text
quantity
and
size
```

No public quantitative percentage is assigned in the evidence catalog.

MissionLab therefore preserves NASA's qualitative wording and does not invent a numerical reduction.

---

# Arc-Jet Consistency

NASA reported that Artemis II heat-shield performance was consistent with the post-Artemis-I arc-jet ground-testing program.

This provides an important closure path:

```text
Artemis I observation
→ investigation
→ replicated mechanism
→ mitigation
→ Artemis II flight
→ behavior consistent with test expectations
```

However, the public source does not provide enough numerical detail to perform a MissionLab flight-versus-arc-jet residual analysis.

---

# Entry-Interface Prediction Accuracy

NASA reported that Artemis II entry-interface velocity was:

```text
within 1 mph of prediction
```

The evidence record deliberately preserves the semantic:

```text
within
```

rather than interpreting the statement as an exact:

```text
1.000 mph error
```

This mission-level prediction agreement is useful context.

It is not direct validation of MissionLab's:

```text
trajectory reconstruction
NRLMSIS model
or Sutton–Graves heating estimate
```

unless NASA publishes the corresponding prediction dataset required for an apples-to-apples comparison.

---

# Long-Term Corrective Action

Evidence record:

```text
artemis_iii_permeability_manufacturing_change
```

For future Orion heat shields, NASA applied the Artemis I lesson directly to material production.

Public NASA reporting describes production changes intended to achieve:

```text
greater uniformity
and
consistent permeability
```

with more permeable Avcoat blocks.

This is represented as:

```text
LONG_TERM_CORRECTIVE_ACTION
```

because it addresses the material parameter implicated in the root cause, rather than relying only on operational trajectory mitigation.

---

# Permanent Decision Thread

The Phase 2F.1 engineering sequence is:

```text
DETECTION
→
EVIDENCE_COLLECTION
→
ROOT_CAUSE
→
CONSTRAINT
→
DECISION_AND_ACTION
→
FLIGHT_OUTCOME
→
LONG_TERM_CORRECTIVE_ACTION
```

Seven stages are preserved in this exact order.

---

# Stage 1 — Detection

Evidence records:

```text
1
```

Stage:

```text
DETECTION
```

Meaning:

```text
Unexpected Artemis I heat-shield char loss
was identified after flight.
```

---

# Stage 2 — Evidence Collection

Evidence records:

```text
4
```

Stage:

```text
EVIDENCE_COLLECTION
```

Includes:

```text
flight instrumentation
postflight Avcoat sampling
eight thermal-test campaigns / 121 tests
ground replication of the phenomenon
```

---

# Stage 3 — Root Cause

Evidence records:

```text
3
```

Stage:

```text
ROOT_CAUSE
```

Includes:

```text
low permeability
internal gas-pressure buildup
skip-entry thermal-history role
permeable-region comparison
```

---

# Stage 4 — Constraint

Evidence records:

```text
1
```

Stage:

```text
CONSTRAINT
```

Represents the engineering requirement to establish safe flight rationale for the existing Artemis II heat shield.

---

# Stage 5 — Decision and Action

Evidence records:

```text
2
```

Stage:

```text
DECISION_AND_ACTION
```

Represents:

```text
Artemis II trajectory modification
+
removal of the Artemis I-style skip entry
```

---

# Stage 6 — Flight Outcome

Evidence records:

```text
4
```

Stage:

```text
FLIGHT_OUTCOME
```

Includes:

```text
TPS performance as expected
reduced char loss
consistency with arc-jet tests
entry-interface velocity within 1 mph of prediction
```

---

# Stage 7 — Long-Term Corrective Action

Evidence records:

```text
1
```

Stage:

```text
LONG_TERM_CORRECTIVE_ACTION
```

Represents future Avcoat manufacturing changes aimed at greater uniformity and consistent permeability.

---

# Context-Only Evidence

Two evidence records intentionally do not appear as decision-thread events:

```text
orion_heat_shield_architecture
avcoat_function
```

They provide engineering background needed to interpret the thread.

They are not themselves:

```text
detection
investigation
root cause
decision
or outcome
```

events.

The derived-product validator requires exactly these two records to remain context-only.

---

# Derived Decision-Thread Product

Created:

```text
scripts/analysis/build_tps_decision_thread.py
```

Generated processed product:

```text
data/processed/entry/tps_decision_thread.json
```

The processed JSON remains ignored from Git.

The derived product contains:

```text
7 stages
15 directly referenced evidence records
2 context-only records
4 unique source URLs used by the thread
```

Every evidence claim embedded in the derived product is copied from the validated reference dataset.

---

# Decision-Thread Visualization

Created:

```text
docs/assets/entry/phase2f_tps_decision_thread.svg
```

The deterministic visualization shows the sequence:

```text
Detection
→ Evidence collection
→ Root cause
→ Constraint
→ Decision & action
→ Flight outcome
→ Long-term corrective action
```

The visualization is an engineering evidence map.

It is not a quantitative TPS-response plot.

---

# Evidence Catalog Validator

Created:

```text
scripts/validation/validate_tps_evidence.py
```

The validator checks:

```text
JSON validity
dataset identifier
mission
top-level provenance
17-record evidence inventory
unique evidence IDs
required evidence categories
NASA source hosts
source-date syntax
nonempty claims
nonempty interpretation fields
limitations
decision-thread references
decision-stage ordering
numerical evidence invariants
MissionLab interpretation guardrails
```

Source dates may be represented as:

```text
null
YYYY
YYYY-MM-DD
```

This preserves source precision without inventing dates.

---

# Evidence Validation Result

Observed:

```text
Evidence items checked: 17
Decision-thread stages: 7
Evidence categories: 10
Unique source URLs: 5
```

Source hosts:

```text
ntrs.nasa.gov
www.nasa.gov
```

Decision-thread order:

```text
DETECTION
EVIDENCE_COLLECTION
ROOT_CAUSE
CONSTRAINT
DECISION_AND_ACTION
FLIGHT_OUTCOME
LONG_TERM_CORRECTIVE_ACTION
```

Key numerical invariants:

```text
Orion heat-shield diameter:
16.5 ft

Artemis II Avcoat blocks:
186

Artemis I thermal campaigns:
8

Artemis I individual tests:
121

Artemis II EI prediction:
within 1 mph
```

Result:

```text
PASS
```

---

# Derived-Product Validator

Created:

```text
scripts/validation/validate_tps_decision_thread.py
```

This validator independently compares:

```text
reference evidence dataset
versus
generated decision-thread product
```

It checks:

```text
product identifier
mission
derived provenance
source dataset ID
seven-stage ordering
stage indices
stage summaries
evidence-reference ordering
evidence counts
exact claim reproduction
exact source reproduction
exact limitations reproduction
NASA source hosts
context-only evidence inventory
referenced-evidence inventory
Phase 2E.4 relationship guardrails
allowed-use guardrails
prohibited-inference guardrails
documentation SVG presence
```

---

# Derived-Product Validation Result

Observed:

```text
Stages checked:
7

Evidence records checked:
17

Thread-referenced evidence:
15

Context-only evidence:
2

Unique thread source URLs:
4
```

Context-only records:

```text
avcoat_function
orion_heat_shield_architecture
```

Guardrail preservation:

```text
Source claims copied exactly:
PASS

NASA source hosts only:
PASS

Phase 2E.4 relationship preserved:
PASS

Prohibited inferences preserved:
PASS
```

Final result:

```text
PASS
```

---

# Relationship to Phase 2E.4

Phase 2E.4 produced:

```text
Qualified Sutton–Graves peak:
109.641953 W/cm²

Primary modeled convective heat load:
162.686370921 MJ/m²
```

Phase 2F.1 does not calibrate either number using Artemis I or Artemis II char-loss observations.

The permanent interpretation is:

```text
Phase 2E.4
describes a low-fidelity external
aerothermal environment.

Phase 2F.1
describes authoritative TPS heritage,
material behavior evidence,
engineering decisions,
and observed outcomes.
```

They are related contextually but remain different classes of evidence.

---

# Explicit Prohibited Inferences

The evidence dataset permanently prohibits:

```text
predict Artemis II char-loss quantity
from Sutton–Graves heat flux alone
```

```text
predict Avcoat recession depth
without a material-response model
```

```text
predict internal heat-shield temperature
without TPS thermal-response data
```

```text
treat Artemis II reduced char loss
as numerical validation of the
MissionLab heating model
```

```text
invent quantitative permeability limits
not published by NASA
```

```text
calibrate the Sutton–Graves model
to Artemis I or Artemis II
char-loss observations
```

These are scientific interpretation guardrails rather than software limitations alone.

---

# What Phase 2F.1 Teaches

The key engineering lesson is that spacecraft anomalies cannot always be reduced to a single maximum environment value.

The Artemis I heat-shield issue involved interaction among:

```text
trajectory
+
heating history
+
material thermal response
+
pyrolysis-gas generation
+
permeability
+
internal pressure
```

This explains why:

```text
peak heat flux alone
```

is insufficient to predict the anomaly.

It also demonstrates how mission engineering can mitigate a hardware/material risk by changing:

```text
the environment experienced by the hardware
```

rather than immediately replacing the hardware itself.

The Artemis I to Artemis II sequence is therefore a particularly strong example of operational engineering decision-making.

---

# Phase 2F.1 Status

Permanent evidence foundation:

```text
COMPLETE
```

Evidence catalog:

```text
17 records
PASS
```

Decision thread:

```text
7 stages
PASS
```

Thread-referenced evidence:

```text
15 records
```

Context-only evidence:

```text
2 records
```

Interpretation guardrails:

```text
PASS
```

Phase 2F.1 status:

```text
COMPLETE
```

---

# Phase 2F.2 — Artemis I vs Artemis II Entry-Profile Heritage Comparison

## Goal

Phase 2F.2 quantitatively compares selected Artemis I entry-profile heritage landmarks with the reconstructed Artemis II entry trajectory.

The phase asks:

```text
How did the flown Artemis II entry profile differ
from the Artemis I skip-entry profile associated
with the heat-shield investigation?
```

The comparison is intentionally limited to quantities that can be supported by authoritative NASA material and the existing MissionLab Artemis II reconstruction.

This is not:

```text
a complete Artemis I trajectory reconstruction
a guidance-law reconstruction
a TPS material-response model
a crew-load comparison
or a damage-prediction model
```

---

# Relationship to Phase 2F.1

Phase 2F.1 established the qualitative engineering decision chain:

```text
Artemis I anomaly
→ investigation
→ root cause
→ constraint
→ Artemis II trajectory mitigation
→ flight outcome
→ future manufacturing corrective action
```

Phase 2F.2 adds quantitative trajectory context to that chain.

It does not attempt to infer:

```text
how much char loss was prevented
how much TPS risk was reduced
or what fraction of the trajectory change
was attributable to any single design constraint
```

Instead, it reconstructs measurable differences between the two entry-profile architectures.

---

# Source Foundation

Created:

```text
data/reference/artemis_entry_profile_heritage.json
```

Dataset identifier:

```text
phase2f2_artemis_entry_profile_heritage
```

The reference dataset contains:

```text
7 NASA-reported evidence records
4 unique source URLs
```

Permitted source hosts:

```text
ntrs.nasa.gov
www.nasa.gov
```

All source evidence uses:

```text
NASA_REPORTED
```

provenance.

---

# Permanent Source Evidence

The evidence catalog preserves the following reference quantities.

## Artemis I Entry Interface

NASA-reported Entry Interface altitude:

```text
400,000 ft
```

NASA-reconstructed Artemis I Entry Interface inertial velocity magnitude:

```text
36,062.65680 ft/s
```

Converted:

```text
10.991897793 km/s
```

This quantity is used as the primary Artemis I entry-speed reference.

---

# Artemis I Skip Entry

NASA classifies Artemis I as:

```text
SKIP ENTRY
```

NASA-reported actual skip apogee:

```text
287.40 kft
```

Converted:

```text
87.599520 km
```

NASA-reported predicted skip apogee:

```text
293.5 kft
```

MissionLab uses the actual flight value.

---

# Artemis I Sensed Acceleration Heritage

NASA reports first and second peak sensed-acceleration magnitudes of:

```text
4.05 g
3.89 g
```

These values are retained as heritage context only.

They are explicitly not compared directly with the Phase 2C MissionLab quantity:

```text
-d|V_Earth-relative|/dt / g0
```

because the latter is a kinematic speed derivative expressed on a g0 scale.

It is not:

```text
crew g-load
proper acceleration
accelerometer output
or isolated aerodynamic acceleration
```

---

# Artemis I Entry Duration

NASA's Artemis I mission timeline reports:

```text
Entry Interface MET:
025/11:15:52

Splashdown MET:
025/11:36:27
```

Difference:

```text
1,235.0 s
```

This provides the Artemis I Entry Interface to splashdown duration.

---

# Artemis II Official Profile Terminology

NASA technical reporting classifies Artemis II as:

```text
MODIFIED TRAJECTORY WITHOUT SKIP ENTRY
```

NASA public mission coverage also uses the label:

```text
LOFTED ENTRY SEQUENCE
```

MissionLab therefore uses the derived terminology:

```text
VERTICAL REBOUND / LOFT
```

and explicitly prohibits:

```text
ARTEMIS II SKIP ENTRY
```

as a MissionLab classification.

---

# Why the Terminology Matters

Phase 2C identified two vertical-velocity sign changes in the Artemis II reconstructed trajectory:

```text
descent → climb
climb → descent
```

Those sign changes create a real geometric altitude rebound.

However:

```text
geometric altitude rebound
```

does not automatically imply:

```text
skip-entry guidance classification
```

NASA explicitly says Artemis II did not use the Artemis I skip entry.

Therefore MissionLab preserves both facts:

```text
The Artemis II trajectory contains
a measurable altitude rebound.

AND

Artemis II is not classified
as a skip entry.
```

---

# Source Validator

Created:

```text
scripts/validation/validate_entry_profile_heritage.py
```

The validator checks:

```text
dataset identity
NASA provenance
source URL host restrictions
source-date syntax
evidence ID inventory
Artemis I Entry Interface altitude
Artemis I Entry Interface inertial speed
Artemis I skip-apogee altitude
Artemis I sensed-acceleration peaks
Artemis I EI-to-splashdown duration
Artemis II no-skip classification
Artemis II lofted-entry public label
Artemis II public pre-EI speed context
planned comparison metrics
planned figure inventory
interpretation guardrails
```

Observed validation:

```text
Evidence items checked:
7

Unique source URLs:
4
```

Source hosts:

```text
ntrs.nasa.gov
www.nasa.gov
```

Result:

```text
PASS
```

---

# Permanent Comparison Analyzer

Created:

```text
scripts/analysis/compare_artemis_entry_profiles.py
```

The analyzer combines:

```text
NASA Artemis I published entry landmarks
+
NASA Artemis II high-rate entry ephemeris
+
MissionLab Artemis II entry dynamics
+
MissionLab terminal event correlation
```

into:

```text
data/processed/entry/artemis_entry_profile_comparison.json
```

The processed JSON remains ignored from Git.

---

# Comparison Provenance

The derived comparison product is labeled:

```text
MIXED_NASA_REPORTED_NASA_FLIGHT_DERIVED_MISSIONLAB_DERIVED
```

This is intentional.

The individual quantities have different provenance.

Artemis I heritage landmarks:

```text
NASA_REPORTED
```

Artemis II high-rate source trajectory:

```text
NASA flight-derived ephemeris
```

Artemis II rebound detection and surface-crossing correlation:

```text
MISSIONLAB_DERIVED
```

No cross-mission result is allowed to obscure these distinctions.

---

# Artemis II Reconstructed Entry Interface

MissionLab Entry Interface epoch:

```text
2026-04-10T23:53:30.866000Z
```

WGS84 altitude:

```text
121.919907 km
```

Earth-relative speed:

```text
10.632214 km/s
```

The first high-rate M50 source state occurs at the same reconstructed Entry Interface epoch.

Its inertial speed magnitude is:

```text
11.000018640 km/s
```

---

# Matched Entry-Interface Inertial-Speed Comparison

The original exploratory comparison used public mission speeds.

That approach was rejected as the permanent primary comparison because the public values do not provide sufficiently matched epoch/frame semantics.

The permanent comparison instead uses:

```text
Artemis I:
NASA-reconstructed EI inertial velocity magnitude

Artemis II:
NASA flight-derived first M50 high-rate
source-state inertial velocity magnitude
```

Artemis I:

```text
10.991897793 km/s
```

Artemis II:

```text
11.000018640 km/s
```

Signed difference:

```text
Artemis II - Artemis I

+0.008120847 km/s
```

Equivalent:

```text
+8.121 m/s
```

Absolute difference:

```text
8.121 m/s
```

Relative difference using Artemis I as the denominator:

```text
+0.073880%
```

Relationship:

```text
ARTEMIS_II_HIGHER
```

---

# Why Speed Magnitude Is Used

The Artemis I source reports an inertial velocity magnitude.

The Artemis II high-rate entry product is expressed in:

```text
M50
```

MissionLab preserves M50 as the source frame.

The cross-mission comparison therefore does not compare individual vector components.

Instead it compares:

```text
|V|
```

because a pure coordinate-frame rotation preserves vector magnitude.

The comparison is therefore intentionally limited to inertial velocity magnitude.

This does not resolve every M50 convention question documented elsewhere in the project.

---

# Key Speed Result

The two missions reached Entry Interface with extremely similar inertial speed magnitudes.

Difference:

```text
8.121 m/s
```

Relative difference:

```text
0.073880%
```

This means the large differences in later entry-profile structure cannot be summarized as:

```text
Artemis II simply entered much slower.
```

The technical Entry Interface speeds were effectively very close at mission scale.

---

# Public Artemis II Speed Context

NASA public mission coverage reported approximately:

```text
23,864 mph
```

maximum velocity just before Entry Interface.

Converted:

```text
10.668162560 km/s
```

Difference between the first M50 inertial state and this public value:

```text
+331.856 m/s
```

This value remains:

```text
CONTEXT ONLY
```

because the public statement and high-rate source state do not provide identical technical semantics.

MissionLab does not force them into agreement.

---

# Entry-Duration Comparison

Artemis I NASA-reported Entry Interface to splashdown:

```text
1,235.000000 s
```

Artemis II MissionLab Entry Interface to derived WGS84 surface crossing:

```text
817.957676 s
```

Difference:

```text
417.042324 s
```

Artemis II is therefore shorter by:

```text
33.768609%
```

relative to the Artemis I duration.

---

# Duration-Provenance Limitation

The comparison endpoints are not identically sourced.

Artemis I uses:

```text
NASA-reported EI MET
and
NASA-reported splashdown MET
```

Artemis II uses:

```text
MissionLab reconstructed Entry Interface
and
MissionLab derived WGS84 surface crossing
correlated with NASA's splashdown minute
```

Therefore the result is a mission-profile duration comparison, not a sub-second official event-time residual.

---

# Upper-Profile Landmark Comparison

Artemis I actual skip apogee:

```text
87.599520 km
```

Artemis II derived rebound top:

```text
64.211808 km
```

Difference:

```text
23.387712 km
```

Relative to the Artemis I skip-apogee altitude, the Artemis II landmark is:

```text
26.698448%
```

lower.

---

# Upper-Landmark Interpretation Limit

These two altitudes are not asserted to represent identical guidance events.

Artemis I value:

```text
skip apogee
```

Artemis II value:

```text
derived climb-to-descent rebound top
```

They are compared only as:

```text
upper-profile trajectory landmarks
```

This allows the geometric scale of the profiles to be compared without misclassifying Artemis II as a skip entry.

---

# Artemis II Derived Rebound

The Phase 2C vertical-velocity analysis identified:

```text
DESCENT_TO_CLIMB
```

at:

```text
EI+112.294128 s
```

Altitude:

```text
60.350128 km
```

Speed:

```text
8.993741 km/s
```

The second crossing:

```text
CLIMB_TO_DESCENT
```

occurs at:

```text
EI+239.647374 s
```

Altitude:

```text
64.211808 km
```

Speed:

```text
6.479165 km/s
```

---

# Artemis II Rebound Metrics

Rebound duration:

```text
127.353246 s
```

Altitude recovery:

```text
3.861680 km
```

Speed loss during rebound:

```text
2.514577 km/s
```

These quantities describe the reconstructed Artemis II vertical trajectory structure.

They do not redefine the official entry classification.

---

# Core Cross-Mission Result

The most important Phase 2F.2 observation is the combination of three results.

Entry Interface inertial speed:

```text
Artemis I:
10.991897793 km/s

Artemis II:
11.000018640 km/s

difference:
+0.073880%
```

Entry duration:

```text
Artemis II:
33.768609% shorter
```

Upper trajectory landmark:

```text
Artemis II:
26.698448% lower
```

The two missions therefore entered the atmosphere with nearly identical inertial speed magnitudes while following substantially different subsequent trajectory structures.

This is stronger than attributing the profile difference to a major Entry Interface speed difference.

---

# Figures

Created:

```text
docs/assets/entry/phase2f_entry_duration_comparison.svg
```

This figure compares:

```text
Artemis I NASA-reported EI-to-splashdown duration
versus
Artemis II MissionLab EI-to-surface-crossing duration
```

Created:

```text
docs/assets/entry/phase2f_skip_loft_altitude_comparison.svg
```

This figure compares:

```text
Artemis I skip apogee
versus
Artemis II rebound top
```

with their different trajectory classifications preserved.

Created:

```text
docs/assets/entry/phase2f_artemis_ii_rebound_profile.svg
```

This figure shows the actual reconstructed Artemis II altitude history surrounding:

```text
descent → climb
```

and:

```text
climb → descent
```

events.

All figures use deterministic SVG configuration.

---

# Independent Comparison Validator

Created:

```text
scripts/validation/validate_artemis_entry_profile_comparison.py
```

The validator independently reconstructs the expected cross-mission metrics from the underlying reference and processed products.

It checks:

```text
product identifier
reference-dataset identifier
mixed provenance label
819 high-rate Artemis II entry records
Entry Interface epoch alignment
Artemis I entry classification
Artemis II no-skip classification
Artemis II loft public label
MissionLab rebound terminology
rebound duration
rebound altitude recovery
rebound speed loss
cross-mission duration comparison
upper-profile landmark comparison
matched inertial EI speed comparison
signed speed-difference direction
absolute speed difference
relative speed difference
Artemis I sensed-acceleration guardrail
interpretation guardrail preservation
three SVG outputs
```

---

# Comparison Validation Result

Observed classification:

```text
Artemis I:
SKIP_ENTRY

Artemis II:
MODIFIED_TRAJECTORY_WITHOUT_SKIP_ENTRY

Artemis II derived feature:
VERTICAL REBOUND / LOFT
```

Observed duration comparison:

```text
Artemis I:
1235.000000 s

Artemis II:
817.957676 s

shorter by:
417.042324 s

reduction:
33.768609%
```

Observed upper-profile comparison:

```text
Artemis I skip apogee:
87.599520 km

Artemis II rebound top:
64.211808 km

lower by:
23.387712 km

relative difference:
26.698448%
```

Observed matched EI inertial-speed comparison:

```text
Artemis I:
10.991897793 km/s

Artemis II:
11.000018640 km/s

Artemis II - Artemis I:
+0.008120847 km/s
+8.121 m/s

absolute difference:
8.121 m/s

relative difference:
+0.073880%

relationship:
ARTEMIS_II_HIGHER
```

Figures checked:

```text
3
```

Final result:

```text
PASS
```

---

# Permanent Guardrails

Artemis II must not be labeled:

```text
SKIP ENTRY
```

MissionLab may describe its reconstructed feature as:

```text
vertical rebound
```

or:

```text
loft
```

Artemis I sensed acceleration:

```text
4.05 g
3.89 g
```

must not be directly compared with Phase 2C:

```text
kinematic deceleration / g0
```

Public mission speed numbers with unmatched semantics remain:

```text
CONTEXT ONLY
```

The Artemis I skip-apogee altitude and Artemis II rebound-top altitude must not be described as identical guidance phases.

No Phase 2F.2 trajectory quantity may be converted directly into:

```text
Avcoat char-loss quantity
TPS recession
TPS damage probability
crew load
or heat-shield failure probability
```

MissionLab also does not claim that every Artemis I versus Artemis II trajectory difference was caused exclusively by the heat-shield investigation.

---

# What Phase 2F.2 Teaches

A mission trajectory can change substantially even when the atmospheric Entry Interface energy state appears very similar at first glance.

For Artemis I and Artemis II:

```text
EI inertial speed magnitudes:
nearly equal
```

while:

```text
entry duration:
substantially different
```

and:

```text
upper-profile geometry:
substantially different
```

This demonstrates why mission analysis cannot rely only on a single scalar such as:

```text
entry velocity
```

Trajectory shape and time history matter.

For TPS analysis in particular, the vehicle's thermal response depends on the history of the environment, not merely the initial speed or a single peak quantity.

This directly reinforces the central Phase 2F lesson:

```text
trajectory history
+
material response
+
time-dependent thermal behavior
```

matter together.

---

# Phase 2F.2 Status

Source heritage dataset:

```text
7 records
PASS
```

Permanent cross-mission comparison:

```text
PASS
```

Matched EI inertial-speed comparison:

```text
PASS
```

Trajectory classification guardrails:

```text
PASS
```

Figures:

```text
3
PASS
```

Phase 2F.2 status:

```text
COMPLETE
```

---

# Phase 2F.3 — Artemis II Loft / Rebound Heating-History Segmentation

## Goal

Phase 2F.3 connects the existing Phase 2E.4 modeled external convective-heating history to the derived Artemis II vertical rebound / loft identified in Phase 2C and formalized in Phase 2F.2.

The phase asks:

```text
What happened to the modeled external
convective heating before, during,
and after the Artemis II loft / rebound?
```

This phase does not introduce a new aerothermal model.

Instead it segments the existing Phase 2E.4 Sutton-Graves heating product relative to the derived trajectory landmarks.

---

# Relationship to Phase 2E.4

Phase 2E.4 produced:

```text
entry_heating.csv
entry_heating_summary.json
```

with:

```text
819 trajectory states
Sutton-Graves convective heat flux
formal cumulative heat load
Knudsen-domain flags
Mach-domain flags
```

The stronger-continuum interpretation domain is:

```text
Kn < 0.001
and
Mach >= 5
```

Its integrated modeled convective heat load is:

```text
159.150073328 MJ/m^2
```

Phase 2F.3 does not alter this model or recompute its physical assumptions.

It only partitions that existing heating history around the Artemis II derived vertical rebound.

---

# Relationship to Phase 2F.2

Phase 2F.2 established the Artemis II trajectory terminology:

```text
NASA classification:
MODIFIED TRAJECTORY WITHOUT SKIP ENTRY

NASA public label:
LOFTED ENTRY SEQUENCE

MissionLab derived feature:
VERTICAL REBOUND / LOFT
```

Phase 2F.3 therefore preserves:

```text
loft
rebound
```

as the allowed terminology.

It does not relabel Artemis II as a skip entry.

---

# Permanent Analyzer

Created:

```text
scripts/analysis/analyze_loft_heating_history.py
```

The analyzer combines:

```text
Phase 2E.4 entry_heating.csv
+
Phase 2E.4 entry_heating_summary.json
+
Phase 2C entry_dynamics_summary.json
```

and writes:

```text
data/processed/entry/loft_heating_history.json
```

The processed JSON remains ignored from Git.

---

# Product Provenance

The derived product uses:

```text
MISSIONLAB_DERIVED_FROM_PHASE2E4_MODEL_OUTPUT
```

provenance.

This is important because the result is not:

```text
measured heat-shield heat flux
onboard thermal telemetry
Avcoat internal temperature
material-response reconstruction
or postflight damage measurement
```

It is a segmentation of the existing MissionLab external aerothermal model.

---

# Thermal-History Ordering

The reconstructed ordering is:

```text
strong-continuum start
EI+45.249112 s

Sutton-Graves peak
EI+85.000000 s

loft / rebound start
EI+112.294128 s

loft / rebound end
EI+239.647374 s

final Mach 5 crossing
EI+464.815771 s
```

The ordering is therefore:

```text
strong-domain start
→ SG peak
→ loft start
→ loft end
→ Mach 5
```

This ordering is independently validated.

---

# Sutton-Graves Peak Relative to Loft

Peak modeled Sutton-Graves heat flux:

```text
109.641953 W/cm^2
```

Peak time:

```text
EI+85.000000 s
```

Loft start:

```text
EI+112.294128 s
```

Difference:

```text
27.294128 s
```

Therefore the modeled external convective-heating peak occurs:

```text
27.294128 s before loft start
```

---

# Strong-Domain Segmentation

The stronger-continuum / hypersonic domain is partitioned into three permanent segments.

## Pre-Loft Segment

Segment identifier:

```text
PRE_REBOUND_STRONG_DOMAIN
```

Bounds:

```text
Kn < 0.001 start
to
derived descent-to-climb crossing
```

Integrated modeled heat load:

```text
58.914089364 MJ/m^2
```

Fraction of stronger-domain total:

```text
37.017947%
```

---

## Loft / Rebound Segment

Segment identifier:

```text
REBOUND_LOFT
```

Bounds:

```text
descent-to-climb
to
climb-to-descent
```

Duration:

```text
127.353246 s
```

Integrated modeled heat load:

```text
60.443349677 MJ/m^2
```

Fraction of stronger-domain total:

```text
37.978839%
```

---

## Post-Loft Segment

Segment identifier:

```text
POST_REBOUND_TO_MACH5
```

Bounds:

```text
climb-to-descent
to
final Mach 5 crossing
```

Integrated modeled heat load:

```text
39.792634286 MJ/m^2
```

Fraction of stronger-domain total:

```text
25.003215%
```

---

# Heat-Load Partition Closure

The reconstructed partition sums to:

```text
159.150073328 MJ/m^2
```

Existing Phase 2E.4 stronger-domain heat load:

```text
159.150073328 MJ/m^2
```

Closure error:

```text
-0.000000030 J/m^2
```

Percent sum:

```text
100.000000000%
```

The segmentation therefore reproduces the Phase 2E.4 stronger-domain integral to essentially numerical precision.

---

# Key Heat-Load Result

The loft / rebound interval alone accounts for:

```text
37.978839%
```

of the entire stronger-continuum, Mach>=5 modeled convective heat load.

This is slightly more than the pre-loft segment:

```text
37.978839%
versus
37.017947%
```

The post-loft portion contributes:

```text
25.003215%
```

This demonstrates that a substantial portion of modeled external heating continues to accumulate after the formal Sutton-Graves peak.

---

# External Heat Flux at Loft Start

Derived loft start:

```text
EI+112.294128 s
```

Altitude:

```text
60.350128 km
```

Earth-relative speed:

```text
8.993741 km/s
```

Mach:

```text
28.826346
```

Body-scale Knudsen number:

```text
5.403559655275e-05
```

Modeled external Sutton-Graves heat flux:

```text
88.222385 W/cm^2
```

---

# External Heat Flux at Loft End

Derived loft end:

```text
EI+239.647374 s
```

Altitude:

```text
64.211808 km
```

Earth-relative speed:

```text
6.479165 km/s
```

Mach:

```text
21.291566
```

Body-scale Knudsen number:

```text
8.988479177380e-05
```

Modeled external Sutton-Graves heat flux:

```text
25.574568 W/cm^2
```

---

# External Heat-Flux Change Across the Loft

Loft-start modeled external heat flux:

```text
88.222385 W/cm^2
```

Loft-end modeled external heat flux:

```text
25.574568 W/cm^2
```

Signed change:

```text
-71.011249%
```

Classification:

```text
DECREASED
```

This refers only to the modeled external convective heat-flux boundary condition.

---

# Important Thermal Interpretation Limit

A decrease in modeled external heat flux does not imply:

```text
decreasing Avcoat internal temperature
```

or:

```text
cooling throughout the TPS
```

because MissionLab does not currently model:

```text
solid conduction
material thermal inertia
Avcoat pyrolysis
gas generation
internal gas pressure
char evolution
permeability
recession
or coupled material response
```

External heating can decline while internal material temperatures continue evolving because of thermal lag.

Therefore MissionLab uses:

```text
external heat-flux decline
```

and does not use:

```text
TPS cooling
```

as an inferred conclusion.

---

# Rebound Interval Extrema

The permanent analyzer includes interpolated interval boundaries when determining extrema.

This corrects the exploratory inspection, which initially searched only integer-second trajectory samples.

Permanent rebound maximum:

```text
88.222385 W/cm^2
```

at:

```text
EI+112.294128 s
```

Location classification:

```text
START_BOUNDARY
```

Permanent rebound minimum:

```text
25.574568 W/cm^2
```

at:

```text
EI+239.647374 s
```

Location classification:

```text
END_BOUNDARY
```

Average modeled external heat flux during the loft:

```text
47.461177 W/cm^2
```

---

# Why Boundary Interpolation Matters

The loft boundaries occur at:

```text
EI+112.294128 s
EI+239.647374 s
```

rather than at integer-second samples.

Searching only sampled states would produce approximately:

```text
87.502812 W/cm^2
```

and:

```text
25.657622 W/cm^2
```

for the nearest interior samples.

Those are not the actual interval-boundary values.

The permanent implementation explicitly inserts interpolated endpoints before:

```text
integration
minimum calculation
maximum calculation
average calculation
```

so all interval statistics use identical mathematical boundaries.

---

# Post-Peak Heating Context

Heat load accumulated from the SG peak to loft start:

```text
27.555928369 MJ/m^2
```

Heat load accumulated from the SG peak through loft end:

```text
87.999278046 MJ/m^2
```

This represents:

```text
55.293269%
```

of the entire stronger-domain heat load.

Heat load accumulated from the SG peak through final Mach 5:

```text
127.791912333 MJ/m^2
```

This represents:

```text
80.296483%
```

of the stronger-domain heat load.

---

# Key Post-Peak Result

The modeled Sutton-Graves peak is not the point at which most integrated heating is complete.

From the SG peak through final Mach 5, the model still accumulates:

```text
127.791912333 MJ/m^2
```

or:

```text
80.296483%
```

of the full stronger-domain integrated heat load.

This reinforces the distinction between:

```text
peak heat flux
```

and:

```text
integrated heat load
```

They describe different aspects of the thermal environment.

---

# Figures

Created:

```text
docs/assets/entry/phase2f_loft_heating_flux.svg
```

This figure shows modeled external Sutton-Graves heat flux through:

```text
SG peak
loft start
loft end
```

within the permanent stronger-continuum / hypersonic interpretation domain.

Created:

```text
docs/assets/entry/phase2f_loft_heat_load_partition.svg
```

This figure compares the modeled stronger-domain integrated heat load for:

```text
pre-loft
loft / rebound
post-loft
```

Created:

```text
docs/assets/entry/phase2f_loft_cumulative_heat_load.svg
```

This figure shows cumulative modeled external convective heat load from the stronger-continuum boundary through final Mach 5 with the loft boundaries marked.

All figures use deterministic SVG configuration.

---

# Independent Validator

Created:

```text
scripts/validation/validate_loft_heating_history.py
```

The validator independently reconstructs:

```text
thermal-history ordering
three segment boundaries
segment heat-load integrals
segment percentages
segment durations
boundary-interpolated extrema
average loft heat flux
external flux change
partition closure
post-peak heat-load accumulation
figure inventory
interpretation guardrails
```

from the existing Phase 2E.4 and Phase 2C products.

---

# Validation Results

Thermal-history ordering:

```text
strong start:
EI+45.249112 s

SG peak:
EI+85.000000 s

loft start:
EI+112.294128 s

loft end:
EI+239.647374 s

Mach 5:
EI+464.815771 s
```

Strong-domain partition:

```text
PRE_REBOUND_STRONG_DOMAIN
58.914089364 MJ/m^2
37.017947%

REBOUND_LOFT
60.443349677 MJ/m^2
37.978839%

POST_REBOUND_TO_MACH5
39.792634286 MJ/m^2
25.003215%
```

External loft heat-flux change:

```text
start:
88.222385 W/cm^2

end:
25.574568 W/cm^2

change:
-71.011249%
```

Boundary extrema:

```text
maximum:
START_BOUNDARY

minimum:
END_BOUNDARY
```

Partition reconstruction:

```text
159.150073328 MJ/m^2
```

Phase 2E.4 reference:

```text
159.150073328 MJ/m^2
```

Closure error:

```text
-0.000000030 J/m^2
```

Percent sum:

```text
100.000000000%
```

Figures checked:

```text
3
```

Final validation result:

```text
PASS
```

---

# Permanent Guardrails

The following inference is prohibited:

```text
external heat-flux decline
→ internal TPS cooling
```

The following inference is prohibited:

```text
external Sutton-Graves heat load
→ Avcoat char-loss quantity
```

The following inference is prohibited:

```text
loft geometry
→ TPS damage quantity
```

The following inference is prohibited:

```text
loft
→ Artemis II skip-entry classification
```

No Phase 2F.3 output represents:

```text
internal Avcoat temperature
pyrolysis-gas generation
internal gas pressure
material permeability
char thickness
recession depth
crack initiation
or damage probability
```

---

# What Phase 2F.3 Teaches

The Artemis II loft occurs after the modeled external heat-flux peak, but not after the external thermal environment becomes insignificant.

The loft interval alone contains approximately:

```text
38%
```

of the entire stronger-domain integrated modeled heat load.

At the same time, modeled external heat flux falls by approximately:

```text
71%
```

across the loft.

These observations demonstrate why:

```text
peak heat flux
```

and:

```text
integrated heat load
```

must not be treated as interchangeable quantities.

They also demonstrate why TPS interpretation requires time history.

Ablative material behavior depends on the coupled evolution of:

```text
external heating
+
material temperature
+
thermal transport
+
pyrolysis
+
gas flow
+
material structure
```

MissionLab currently reconstructs only the first element with a low-fidelity engineering heating correlation.

---

# Phase 2F.3 Status

External heating segmentation:

```text
PASS
```

Boundary interpolation:

```text
PASS
```

Strong-domain partition closure:

```text
PASS
```

Post-peak heat-load analysis:

```text
PASS
```

Interpretation guardrails:

```text
PASS
```

Figures:

```text
3
PASS
```

Phase 2F.3 status:

```text
COMPLETE
```

---

# Phase 2F.4 — Orion TPS Evidence-to-Physics Boundary

## Goal

Phase 2F.4 defines the explicit boundary between:

```text
what MissionLab quantitatively reconstructs
```

and:

```text
what NASA's Artemis I investigation establishes
qualitatively about internal Avcoat material response
```

The purpose of this phase is not to extend the Sutton-Graves model into an unsupported damage model.

Instead it answers:

```text
Where does the current MissionLab physics model stop?
```

and:

```text
What additional material-response physics would be
required before char loss could be predicted quantitatively?
```

---

# Why This Phase Is Necessary

By the end of Phase 2F.3, MissionLab had reconstructed:

```text
trajectory
atmosphere
Mach
rarefaction
external convective heating
integrated external heat load
loft / rebound geometry
heating-history segmentation
```

NASA's Artemis I heat-shield investigation, however, describes a mechanism involving:

```text
internal material temperature
pyrolysis
gas generation
gas transport
permeability
internal pressure
cracking
char liberation
```

Those are different physical domains.

Without an explicit boundary, it would be easy to incorrectly imply that:

```text
external Sutton-Graves heat flux
```

directly predicts:

```text
Avcoat damage
```

Phase 2F.4 permanently prevents that interpretation.

---

# Permanent Boundary Reference

Created:

```text
data/reference/artemis_tps_physics_boundary.json
```

Dataset identifier:

```text
phase2f4_artemis_tps_physics_boundary
```

Provenance:

```text
PROJECT_SCOPE_GUARDRAIL_WITH_NASA_REPORTED_MECHANISM
```

The reference links back to:

```text
phase2f1_orion_tps_heritage_evidence
```

and uses:

```text
14
```

selected Phase 2F.1 evidence records.

---

# NASA-Reported Mechanism

The Phase 2F.4 reference preserves the NASA-reported Artemis I root-cause sequence exactly as represented in the Phase 2F.1 evidence dataset.

Sequence:

```text
1. Avcoat heats during atmospheric entry

2. pyrolysis and ablation generate gases
   inside the material

3. low-permeability Avcoat restricts
   gas escape

4. internal gas pressure increases

5. cracks form

6. charred material is liberated
```

The Phase 2F.4 analyzer verifies that this sequence exactly matches the Phase 2F.1 evidence source before generating the processed product.

---

# Evidence vs Prediction

The sequence above represents:

```text
NASA-reported mechanism evidence
```

It does not mean MissionLab calculates each stage.

MissionLab currently calculates only the external entry environment.

The distinction is:

```text
NASA reports the mechanism.

MissionLab does not numerically reproduce
the complete mechanism.
```

---

# Eight-Stage Physics Chain

Phase 2F.4 defines eight permanent stages.

## Stage 1 — Trajectory / External Flow

Identifier:

```text
trajectory_external_flow
```

Status:

```text
MISSIONLAB_RECONSTRUCTS
```

Inside current MissionLab quantitative model:

```text
TRUE
```

This stage includes quantities such as:

```text
trajectory state
Earth-fixed position
WGS84 altitude
Earth-relative speed
atmospheric density
Mach
body-scale Knudsen number
```

---

# Stage 2 — External Convective Heating

Identifier:

```text
external_convective_heating
```

Status:

```text
MISSIONLAB_MODELS
```

Inside current MissionLab quantitative model:

```text
TRUE
```

This stage includes:

```text
Sutton-Graves external convective heat flux
```

and:

```text
integrated modeled external convective heat load
```

This is the final stage currently inside MissionLab's quantitative TPS-related physics model.

---

# Current Quantitative Physics Boundary

The permanent MissionLab quantitative frontier is:

```text
after:

EXTERNAL CONVECTIVE HEATING

and before:

SURFACE / INTERNAL THERMAL RESPONSE
```

Therefore:

```text
last stage inside model:
external_convective_heating

order:
2
```

and:

```text
first stage outside model:
surface_internal_thermal_response

order:
3
```

---

# Stage 3 — Surface / Internal Thermal Response

Identifier:

```text
surface_internal_thermal_response
```

Status:

```text
BOUNDARY_NOT_MODELED
```

Inside current MissionLab quantitative model:

```text
FALSE
```

A material-response solution would be required to convert the external aerothermal boundary condition into quantities such as:

```text
surface temperature
through-thickness temperature
thermal gradients
stored thermal energy
```

MissionLab does not currently perform this calculation.

---

# Stage 4 — Pyrolysis / Gas Generation

Identifier:

```text
pyrolysis_gas_generation
```

Status:

```text
NASA_MECHANISM_KNOWN_NOT_MODELED
```

NASA reports that gases are generated inside Avcoat during entry material response.

MissionLab does not currently calculate:

```text
pyrolysis rate
gas-generation rate
chemical decomposition
```

---

# Stage 5 — Gas Transport / Permeability

Identifier:

```text
gas_transport_permeability
```

Status:

```text
NASA_MECHANISM_KNOWN_NOT_MODELED
```

NASA identified:

```text
low permeability
```

and:

```text
restricted gas escape
```

as central to the Artemis I mechanism.

MissionLab does not currently possess or solve:

```text
local Avcoat permeability
gas transport
porous flow
spatial permeability variation
```

---

# Stage 6 — Internal Gas Pressure

Identifier:

```text
internal_pressure
```

Status:

```text
NASA_MECHANISM_KNOWN_NOT_MODELED
```

NASA reports that restricted gas escape produced:

```text
internal gas-pressure buildup
```

MissionLab does not calculate:

```text
pore pressure
internal gas pressure
pressure gradients
```

---

# Stage 7 — Cracking / Fracture

Identifier:

```text
cracking_fracture
```

Status:

```text
NASA_MECHANISM_KNOWN_NOT_MODELED
```

NASA reports cracking as part of the Artemis I mechanism.

MissionLab does not currently solve:

```text
stress
strain
fracture mechanics
crack initiation
crack propagation
```

---

# Stage 8 — Char Liberation / Damage

Identifier:

```text
char_liberation_damage
```

Status:

```text
NASA_OBSERVED_OUTCOME_NOT_PREDICTED
```

NASA observed unexpected Artemis I char liberation.

NASA later reported that Artemis I-type char loss was significantly reduced on Artemis II.

MissionLab does not predict:

```text
char-loss mass
char-loss area
char-loss probability
damage location
damage severity
recession depth
```

---

# Permanent Physics Boundary

The resulting model structure is:

```text
TRAJECTORY / EXTERNAL FLOW
          |
          v
EXTERNAL CONVECTIVE HEATING
          |
          v
================================================
CURRENT MISSIONLAB QUANTITATIVE PHYSICS BOUNDARY
================================================
          |
          v
SURFACE / INTERNAL THERMAL RESPONSE
          |
          v
PYROLYSIS / GAS GENERATION
          |
          v
GAS TRANSPORT / PERMEABILITY
          |
          v
INTERNAL GAS PRESSURE
          |
          v
CRACKING / FRACTURE
          |
          v
CHAR LIBERATION / DAMAGE
```

---

# MissionLab Quantitative Products

The boundary reference identifies:

```text
9
```

current quantitative or derived MissionLab product categories relevant to the TPS chain.

These include:

```text
trajectory time history
WGS84 altitude and Earth-relative speed
atmospheric density
free-stream Mach
body-scale Knudsen number
external Sutton-Graves heat flux
integrated external Sutton-Graves heat load
loft / rebound boundaries
loft / rebound heating-history segmentation
```

---

# Material-Response Quantities Not Reconstructed

Phase 2F.4 explicitly inventories:

```text
17
```

material-response quantities that are absent from the current model.

These include:

```text
surface temperature
through-thickness Avcoat temperature
thermal conductivity field
specific heat / enthalpy response
Avcoat density evolution
pyrolysis rate
pyrolysis-gas generation
gas transport
local permeability
internal gas pressure
thermal stress
mechanical stress / strain
crack initiation
crack propagation
char-layer structural response
recession depth
char-liberation quantity
```

This inventory is a deliberate modeling limitation rather than an implementation omission hidden from the user.

---

# NASA Investigation Data Not Present as MissionLab Inputs

Phase 2F.4 also identifies:

```text
7
```

classes of investigation data unavailable as current MissionLab quantitative inputs.

These include:

```text
pressure-sensor time series
strain-gauge time series
thermocouple time series at multiple Avcoat depths
internal temperature profiles
sample-level Avcoat measurements
detailed arc-jet response data
full coupled Orion material-response model
```

The distinction is important because NASA's root-cause analysis had access to evidence that MissionLab does not.

---

# External Environment Context Retained

Phase 2F.4 preserves the Phase 2F.3 external environment only as context.

Stronger-continuum / Mach>=5 modeled SG heat load:

```text
159.150073328 MJ/m^2
```

External SG flux at loft start:

```text
88.222385 W/cm^2
```

External SG flux at loft end:

```text
25.574568 W/cm^2
```

Signed modeled external flux change:

```text
-71.011249%
```

These remain:

```text
external aerothermal model outputs
```

They do not become internal TPS response quantities.

---

# Prohibited Model Bridge 1

The following direct inference is prohibited:

```text
external Sutton-Graves heat flux
→
Avcoat internal temperature
```

Reason:

```text
MissionLab does not solve the
material thermal-response problem.
```

---

# Prohibited Model Bridge 2

The following direct inference is prohibited:

```text
external Sutton-Graves heat load
→
pyrolysis rate
```

Reason:

```text
No Avcoat pyrolysis kinetics or coupled
thermal-response model is implemented.
```

---

# Prohibited Model Bridge 3

The following direct inference is prohibited:

```text
external Sutton-Graves heat load
→
internal gas pressure
```

Reason:

```text
gas generation
+
gas transport
+
permeability
+
pressure evolution
```

are not modeled.

---

# Prohibited Model Bridge 4

The following direct inference is prohibited:

```text
loft / rebound geometry
→
crack probability
```

MissionLab does not solve the mechanical or fracture-response problem.

---

# Prohibited Model Bridge 5

The following direct inference is prohibited:

```text
external heating history
→
char-loss mass or area
```

No validated public damage-transfer law has been incorporated into MissionLab.

---

# Prohibited Model Bridge 6

The following direct inference is prohibited:

```text
external heat-flux decline
→
TPS cooling
```

Internal temperature can lag the external boundary condition due to thermal inertia and through-thickness energy transport.

---

# Prohibited Model Bridge 7

The following direct inference is prohibited:

```text
Artemis I / Artemis II
trajectory difference
→
numerical char-loss reduction percentage
```

NASA publicly described Artemis II char loss as significantly reduced.

MissionLab does not convert that qualitative description into an invented percentage.

---

# Model Assertions

Phase 2F.4 permanently records eight Boolean assertions.

All must remain:

```text
FALSE
```

Observed:

```text
avcoat_damage_model_created:
FALSE

material_properties_invented:
FALSE

sutton_graves_calibrated_to_char_loss:
FALSE

internal_tps_temperature_inferred:
FALSE

pyrolysis_rate_inferred:
FALSE

internal_pressure_inferred:
FALSE

crack_probability_inferred:
FALSE

char_loss_quantity_inferred:
FALSE
```

If any of these becomes true in a future phase, that change would require an explicit new physical model, evidence base, validation strategy, and documentation.

---

# Permanent Analyzer

Created:

```text
scripts/analysis/build_tps_physics_boundary.py
```

The analyzer verifies:

```text
Phase 2F.1 source evidence linkage
NASA mechanism sequence
eight-stage ordering
quantitative-model membership
stage 2 quantitative frontier
stage 3 boundary start
all material-response assertions remain false
```

It then combines the scope reference with the existing Phase 2F.3 external-environment context.

---

# Processed Summary

Generated:

```text
data/processed/entry/tps_physics_boundary_summary.json
```

Product identifier:

```text
phase2f4_tps_physics_boundary_summary
```

Provenance:

```text
MIXED_PROJECT_SCOPE_GUARDRAIL_NASA_REPORTED_MECHANISM_MISSIONLAB_DERIVED_CONTEXT
```

The generated product remains ignored from Git.

---

# Causal-Boundary Figure

Created:

```text
docs/assets/entry/phase2f_tps_physics_boundary.svg
```

The figure explicitly places the MissionLab quantitative boundary between:

```text
EXTERNAL CONVECTIVE HEATING
```

and:

```text
SURFACE / INTERNAL THERMAL RESPONSE
```

The diagram then preserves the remaining NASA-reported mechanism stages below the boundary.

The figure does not imply that MissionLab numerically computes those lower stages.

---

# Independent Validator

Created:

```text
scripts/validation/validate_tps_physics_boundary.py
```

The validator independently checks:

```text
boundary dataset identity
boundary provenance
Phase 2F.1 source dataset identity
14 evidence references
NASA mechanism sequence
eight-stage physics chain
stage ordering
stage statuses
quantitative-model membership
stage 2 quantitative frontier
stage 3 boundary start
17 absent material-response quantities
7 absent NASA investigation-data categories
7 prohibited model bridges
8 false model assertions
processed summary provenance
Phase 2F.3 external-environment context
figure identity and validity
```

---

# Validation Result

Evidence foundation:

```text
Phase 2F.1 dataset:
phase2f1_orion_tps_heritage_evidence

source evidence items verified:
14

NASA root-cause sequence:
VERIFIED
```

Quantitative frontier:

```text
stage 1:
TRAJECTORY / EXTERNAL FLOW
MISSIONLAB_RECONSTRUCTS

stage 2:
EXTERNAL CONVECTIVE HEATING
MISSIONLAB_MODELS
```

Boundary:

```text
stage 3:
SURFACE / INTERNAL THERMAL RESPONSE
NOT MODELED
```

Remaining mechanism:

```text
pyrolysis / gas generation
gas transport / permeability
internal gas pressure
cracking / fracture
char liberation / damage
```

Boundary inventory:

```text
physics stages:
8

material-response quantities absent:
17

investigation-data categories absent:
7

prohibited model bridges:
7

prohibited model assertions false:
8 / 8
```

Figure:

```text
1
PASS
```

Final result:

```text
PASS
```

---

# What Phase 2F.4 Establishes

MissionLab now has a precise answer to the question:

```text
How far can the public-data reconstruction
go before it becomes speculative?
```

The answer is:

```text
MissionLab can reconstruct the flight
trajectory and model the external
aerothermal environment.

MissionLab currently stops before
internal TPS material response.
```

NASA's investigation provides authoritative evidence for the mechanism beyond that point, but evidence for a mechanism is not equivalent to possessing a validated quantitative model for that mechanism.

---

# Why This Boundary Improves the Project

Stopping at a justified physics boundary makes the project stronger.

It prevents apparently sophisticated but unsupported calculations such as:

```text
inventing Avcoat permeability
estimating internal pressure from SG heat load
predicting crack probability
predicting char-loss mass
assigning numerical Artemis II damage reduction
```

Those calculations would create false precision.

Instead MissionLab preserves:

```text
what is measured or NASA-reported
what is derived
what is modeled
what is not available
what cannot yet be inferred
```

This is consistent with the project's provenance-first architecture.

---

# Phase 2F.4 Status

NASA mechanism linkage:

```text
PASS
```

Quantitative frontier:

```text
PASS
```

Physics-stage ordering:

```text
PASS
```

Missing-physics inventory:

```text
PASS
```

Prohibited model bridges:

```text
PASS
```

Model assertions:

```text
8 / 8 FALSE
PASS
```

Causal-boundary figure:

```text
PASS
```

Phase 2F.4 status:

```text
COMPLETE
```

---

# Phase 2F — Orion TPS & Heat-Shield Heritage Closure

Phase 2F is now composed of four completed subphases.

## Phase 2F.1

```text
Orion TPS heritage evidence
+
Artemis I anomaly
+
root-cause investigation
+
Artemis II mitigation
+
postflight outcome
```

Status:

```text
COMPLETE
```

## Phase 2F.2

```text
Artemis I skip-entry heritage
versus
Artemis II modified lofted / no-skip profile
```

Key result:

```text
EI inertial speeds differ by only:

8.121 m/s
0.073880%
```

while the trajectory structures differ substantially.

Status:

```text
COMPLETE
```

## Phase 2F.3

```text
time-resolved external heating
through the Artemis II loft / rebound
```

Key result:

```text
37.978839%
```

of the stronger-domain modeled convective heat load accumulates during the loft / rebound interval.

Status:

```text
COMPLETE
```

## Phase 2F.4

```text
explicit evidence-to-physics boundary
```

Permanent frontier:

```text
external convective heating
→
STOP
→
internal material response not modeled
```

Status:

```text
COMPLETE
```

---

# Phase 2F Final Interpretation

Phase 2F establishes the following engineering chain:

```text
Artemis I identified an abnormal
Avcoat char-loss mechanism.

NASA's investigation linked that
mechanism to internal material
response, permeability, gas pressure,
and cracking.

Artemis II flew a modified trajectory
without the Artemis I skip entry.

MissionLab reconstructs that trajectory
and its modeled external heating history.

The Artemis II loft occurs after peak
modeled SG heat flux while substantial
integrated external heating continues.

MissionLab stops before internal Avcoat
material response and therefore does not
predict char loss.
```

This distinction is permanent unless a future phase introduces a separately justified and validated material-response model.

---

# Phase 2F Final Status

```text
2F.1 TPS evidence and decision thread:
COMPLETE

2F.2 Artemis I / II entry-profile comparison:
COMPLETE

2F.3 loft heating-history segmentation:
COMPLETE

2F.4 TPS evidence-to-physics boundary:
COMPLETE
```

Overall Phase 2F status:

```text
COMPLETE
```

---

# Phase 2G.1 — Geocentric Lunar Occultation Reconstruction

## Goal

Phase 2G.1 begins the communications-geometry portion of A2 MissionLab.

The objective is to determine whether the existing Artemis II trajectory reconstruction can independently reproduce the lunar-flyby communications blackout reported by NASA using first-principles Earth-Moon-Orion geometry.

The specific question is:

```text
From the center of Earth, when does the solid Moon
intersect the direct Earth-to-Orion line of sight?
```

This phase intentionally solves only the geometric occultation problem.

It does not yet model:

```text
individual Deep Space Network stations
ground-station elevation constraints
antenna masks
RF link margin
received signal strength
network scheduling
tracking handovers
communications-system state
or O2O optical-link availability
```

---

# NASA Public Communications Reference

NASA publicly reported a planned lunar-flyby communications blackout during Artemis II Flight Day 6.

Reference public timing:

```text
Loss of signal:
2026-04-06T22:44:00Z

Acquisition of signal:
2026-04-06T23:25:00Z
```

Duration from the public minute-level timestamps:

```text
2460 s
41.000 min
```

NASA described the loss of communications as occurring while Orion passed behind the Moon and the lunar body blocked the radio path to the Deep Space Network.

These NASA timestamps are treated as:

```text
NASA_REPORTED
PUBLIC_TIMELINE_MINUTE_LEVEL
```

They are not treated as exact geometric lunar-limb contact measurements.

---

# Communications Architecture Context

The Phase 2G.1 reference preserves the broader Artemis II communications architecture.

Primary public radio-frequency architecture includes:

```text
Near Space Network
Deep Space Network
```

NASA reports that communications support transitioned toward the Deep Space Network for deep-space portions of the mission.

Artemis II also carried:

```text
O2O
Orion Artemis II Optical Communications System
```

O2O is retained as mission context only in Phase 2G.1.

Optical communications availability requires additional geometry and operational constraints and is therefore not inferred from the RF lunar-occultation calculation.

---

# Permanent Reference

Created:

```text
data/reference/artemis_ii_communications_events.json
```

Dataset identifier:

```text
phase2g1_artemis_ii_communications_reference
```

Provenance:

```text
NASA_REPORTED
```

The reference contains:

```text
public lunar LOS
public lunar AOS
communications architecture
source provenance
geometric-model assumptions
validation thresholds
interpretation guardrails
```

---

# Geometry Definition

Let:

```text
O = Earth-center to Orion position vector
M = Earth-center to Moon position vector
```

Both are represented in:

```text
J2000
```

The closest point on the Earth-Orion infinite line to the Moon center is found using the projection parameter:

```text
u = (M dot O) / (O dot O)
```

The projected point is:

```text
P = u O
```

The perpendicular Moon-center distance to the Earth-Orion line is:

```text
d = |M - P|
```

The Moon is geometrically between Earth and Orion when:

```text
0 < u < 1
```

The adopted lunar-limb clearance is:

```text
C = d - R_moon
```

where:

```text
R_moon = SPICE mean lunar radius
```

Therefore:

```text
C > 0
Earth-Orion LOS clears the spherical Moon

C = 0
geometric lunar-limb contact

C < 0
the spherical Moon intersects the Earth-Orion LOS
```

The occultation state is therefore:

```text
0 < u < 1
AND
C < 0
```

---

# Lunar Radius

The analyzer obtains the Moon radii directly from SPICE.

Mean adopted radius:

```text
1737.400000 km
```

No locally varying lunar topography is modeled.

This means the derived contacts represent crossings of a:

```text
spherical mean-radius lunar limb
```

rather than the true local terrain limb.

---

# Orion Trajectory Source

Phase 2G.1 uses:

```text
data/processed/trajectory/primary_trajectory.csv
```

Trajectory states:

```text
3262
```

Mission interval:

```text
2026-04-02T01:57:37.084Z
through
2026-04-10T23:53:16.723Z
```

Trajectory cadence:

```text
minimum:
60.000 s

median:
240.000 s

maximum:
296.550 s
```

The primary trajectory originates from NASA flight-derived Artemis II public OEM products processed through the Phase 1 mission-backbone pipeline.

---

# Orion Interpolation

The public OEM states are not sampled finely enough to define occultation contact times directly.

The permanent implementation therefore uses:

```text
piecewise cubic Hermite interpolation
```

using both:

```text
position
and
velocity
```

from adjacent public OEM states.

For interpolation parameter:

```text
s = (t - t0) / (t1 - t0)
```

the position is reconstructed using the standard cubic Hermite basis:

```text
r(t) =
h00 r0
+
h10 Delta_t v0
+
h01 r1
+
h11 Delta_t v1
```

with:

```text
h00 = 2s^3 - 3s^2 + 1

h10 = s^3 - 2s^2 + s

h01 = -2s^3 + 3s^2

h11 = s^3 - s^2
```

This is more physically appropriate than linearly interpolating the already-derived lunar-limb-clearance scalar.

---

# Moon Ephemeris

The Moon state is evaluated directly at each requested calculation time using:

```text
SPICE DE440S
```

with:

```text
target:
MOON

observer:
EARTH

frame:
J2000

aberration correction:
NONE
```

This preserves the Phase 1 Earth/Moon geometry convention.

---

# Aberration and Light-Time Boundary

The occultation calculation uses:

```text
aberration correction = NONE
```

The geometry is therefore a simultaneous geometric state comparison.

It does not attempt to reproduce a complete radio-signal light-time solution.

One-way Earth-Orion light time is calculated only as useful mission context:

```text
Earth-Orion range / speed of light
```

and is not applied as an aberration correction to the occultation geometry.

---

# Exploratory Inspection

Before permanent implementation, Phase 2G.1 ran a read-only inspection using sampled trajectory geometry and linear interpolation of the derived lunar-limb-clearance scalar.

Exploratory contacts:

```text
Ingress:
2026-04-06T22:41:44.101648Z

Egress:
2026-04-06T23:21:34.918123Z

Duration:
2390.816 s
39.847 min
```

This was already broadly consistent with NASA's approximately 41-minute public communications window.

---

# Permanent Refined Contacts

The permanent implementation replaces scalar interpolation with:

```text
cubic-Hermite Orion interpolation
+
direct SPICE Moon evaluation
+
iterative root refinement
```

Refined Earth-center geometric ingress:

```text
2026-04-06T22:41:43.652252Z
```

Refined Earth-center geometric egress:

```text
2026-04-06T23:21:35.489288Z
```

Derived duration:

```text
2391.837 s
39.864 min
```

The permanent result differs only slightly from the exploratory calculation.

Approximate exploratory-to-permanent shifts:

```text
Ingress:
about -0.45 s

Egress:
about +0.57 s

Duration:
about +1.02 s
```

This demonstrates that the initial sampled reconstruction was already stable while the permanent implementation provides a more defensible interpolation method.

---

# NASA Comparison

NASA public LOS:

```text
2026-04-06T22:44:00Z
```

MissionLab Earth-center geometric ingress:

```text
2026-04-06T22:41:43.652252Z
```

Difference:

```text
-136.348 s
```

The MissionLab Earth-center limb crossing occurs approximately:

```text
2.272 min earlier
```

than the NASA public LOS time.

NASA public AOS:

```text
2026-04-06T23:25:00Z
```

MissionLab Earth-center geometric egress:

```text
2026-04-06T23:21:35.489288Z
```

Difference:

```text
-204.511 s
```

The MissionLab Earth-center limb crossing occurs approximately:

```text
3.409 min earlier
```

than the NASA public AOS time.

---

# Duration Comparison

MissionLab geocentric duration:

```text
2391.837 s
39.864 min
```

NASA public duration:

```text
2460.000 s
41.000 min
```

Difference:

```text
-68.163 s
```

or approximately:

```text
-1.136 min
```

The derived geocentric occultation therefore reproduces the reported approximate communications-blackout duration to within a little over one minute.

---

# Window Overlap

The derived geometric interval and NASA public communications interval overlap by:

```text
0.868716
```

or:

```text
86.8716%
```

under the interval-over-union comparison used by Phase 2G.1.

This provides a quantitative consistency measure while preserving the distinction between:

```text
Earth-center geometry
```

and:

```text
operational network contact timing
```

---

# Why the Contacts Should Not Match Exactly

An exact match is neither required nor expected.

MissionLab Phase 2G.1 uses:

```text
observer:
Earth center
```

Actual Deep Space Network support is topocentric.

The DSN consists of geographically separated ground complexes, so a real antenna's line of sight originates from:

```text
Earth surface
```

rather than:

```text
Earth center
```

The contact geometry can therefore shift by minutes near lunar occultation.

Additional operational effects can include:

```text
station selection
ground-station horizon
antenna tracking constraints
link margin
network scheduling
handover criteria
communications-system configuration
```

None of these are part of the Phase 2G.1 calculation.

---

# Deepest Geometric Occultation

The analyzer minimizes lunar-limb clearance within the refined occultation interval using a continuous scalar search.

Derived deepest geometric occultation:

```text
UTC:
2026-04-06T23:01:39.567083Z
```

Lunar-limb clearance:

```text
-1156.057 km
```

A negative value means the Earth-Orion LOS penetrates the adopted spherical lunar disk by that amount in projected radial clearance.

Earth-Orion range:

```text
413143.655 km
```

One-way light time:

```text
1.378099 s
```

This time is not identical to pericynthion because:

```text
minimum Orion-Moon distance
```

and:

```text
minimum projected Moon-to-Earth-Orion-LOS distance
```

are different geometric optimization problems.

---

# Pericynthion Context

Refined MissionLab pericynthion:

```text
2026-04-06T23:00:46.177998Z
```

Phase 2G.1 independently verifies:

```text
inside geocentric occultation:
TRUE

geometrically occulted:
TRUE
```

This is an important mission-level consistency result.

The project's independently reconstructed closest lunar approach occurs inside the independently reconstructed lunar communications blackout geometry.

---

# Mission-Operations Interpretation

The geometry produces a direct mission-operations relationship:

```text
lunar flyby
+
Earth-Moon-Orion alignment
→
lunar occultation
→
loss of direct Earth-Orion RF line of sight
```

This is fundamentally different from an arbitrary communications outage.

The communication interruption is geometrically driven by the mission trajectory.

That relationship is especially relevant to mission-control interpretation because the blackout can be placed directly on the common mission clock alongside:

```text
lunar SOI
pericynthion
trajectory state
maneuvers
science observations
and later communications events
```

---

# Sampled Communications Geometry Product

Generated:

```text
data/processed/communications/lunar_occultation_geometry.csv
```

Rows:

```text
3262
```

Each trajectory sample includes:

```text
UTC
MET
Earth-Orion range
Earth-Moon range
one-way light time
projection fraction
Moon-between-Earth-and-Orion flag
Moon-center distance to LOS
lunar-limb clearance
Earth-center Moon-Orion angular separation
geometric occultation flag
```

This product remains ignored from Git because it is reproducibly generated.

---

# Processed Summary

Generated:

```text
data/processed/communications/lunar_occultation_summary.json
```

Product identifier:

```text
phase2g1_geocentric_lunar_occultation
```

Provenance:

```text
MISSIONLAB_DERIVED_GEOMETRY_WITH_NASA_REPORTED_VALIDATION_REFERENCE
```

The processed summary remains ignored from Git.

---

# Permanent Figure

Created:

```text
docs/assets/communications/phase2g_lunar_occultation_geometry.svg
```

The figure shows:

```text
Earth-center lunar-limb clearance
geometric zero-clearance boundary
MissionLab ingress
MissionLab egress
NASA public LOS
NASA public AOS
```

The figure therefore makes the distinction between the geometric reconstruction and NASA's operational communications timing visually explicit.

---

# Permanent Analyzer

Created:

```text
scripts/analysis/build_lunar_occultation_geometry.py
```

The analyzer performs:

```text
trajectory ingestion
SPICE Moon-state evaluation
Hermite Orion interpolation
Earth-Orion LOS construction
Moon projection onto LOS
lunar-limb-clearance calculation
sampled occultation classification
contact bracketing
sub-sample root refinement
deepest-occultation search
pericynthion correlation
NASA-window comparison
light-time context
deterministic figure generation
processed-product generation
```

---

# Independent Validator

Created:

```text
scripts/validation/validate_lunar_occultation_geometry.py
```

The validator independently reconstructs the geometry rather than trusting the analyzer output.

It verifies:

```text
3262 trajectory states
NASA LOS reference
NASA AOS reference
Earth-center model definition
SPICE lunar radius
two occultation contact brackets
independently refined ingress
independently refined egress
occultation duration
NASA timing consistency
window-overlap threshold
pericynthion containment
pericynthion occultation state
processed summary
3262-row communications geometry CSV
SVG existence and validity
interpretation guardrails
```

---

# Validation Thresholds

Phase 2G.1 intentionally uses broad operational-consistency thresholds because the validation target is minute-level NASA communications reporting, while the model is Earth-centered geometry.

Maximum absolute contact offset:

```text
300 s
```

Maximum duration difference:

```text
180 s
```

Minimum interval overlap:

```text
0.8
```

Expected geometric duration range:

```text
35 to 45 min
```

Pericynthion must lie inside the occultation interval:

```text
TRUE
```

Observed values satisfy all thresholds.

---

# Independent Validation Result

Independent ingress:

```text
2026-04-06T22:41:43.652252Z
```

Independent egress:

```text
2026-04-06T23:21:35.489288Z
```

Duration:

```text
2391.837 s
39.864 min
```

NASA comparison:

```text
Ingress offset:
-136.348 s

Egress offset:
-204.511 s

Duration difference:
-68.163 s

Window overlap:
0.868716
```

Pericynthion:

```text
inside derived occultation:
TRUE

geometrically occulted:
TRUE
```

Generated products:

```text
sampled geometry:
PASS

summary:
PASS

figure:
PASS
```

Final independent validator result:

```text
PASS
```

---

# Interpretation Guardrails

Phase 2G.1 permanently preserves the following distinctions.

## Guardrail 1

```text
Geometric lunar occultation
!=
actual Deep Space Network link availability
```

## Guardrail 2

```text
Earth-center line-of-sight geometry
!=
topocentric geometry from an individual DSN antenna
```

## Guardrail 3

```text
NASA public LOS/AOS minute-level timestamps
!=
exact lunar-limb contact measurements
```

## Guardrail 4

```text
RF lunar occultation geometry
!=
O2O optical-link availability
```

## Guardrail 5

Geometric occultation alone does not provide:

```text
received signal strength
antenna gain
link margin
network schedule
tracking state
communications performance
```

---

# Engineering Significance

Phase 2G.1 provides the first MissionLab communications reconstruction tied directly to independently reconstructed flight geometry.

The chain is now:

```text
NASA flight-derived trajectory
        ↓
MissionLab Earth-Moon-Orion geometry
        ↓
Earth-Orion line of sight
        ↓
lunar-limb intersection
        ↓
derived lunar occultation window
        ↓
comparison with NASA-reported communications blackout
```

The agreement is strong enough to demonstrate that the public trajectory products contain sufficient information to reproduce the dominant geometric cause of the reported lunar-flyby communications blackout.

At the same time, the remaining several-minute timing difference demonstrates why:

```text
geometric visibility
```

must not be automatically relabeled as:

```text
operational communications availability
```

That distinction becomes the foundation for the next communications phases.

---

# Phase 2G.1 Status

Reference evidence:

```text
PASS
```

Geometric model:

```text
PASS
```

Hermite trajectory interpolation:

```text
PASS
```

SPICE Moon geometry:

```text
PASS
```

Ingress refinement:

```text
PASS
```

Egress refinement:

```text
PASS
```

NASA public-window consistency:

```text
PASS
```

Pericynthion containment:

```text
PASS
```

Independent validation:

```text
PASS
```

Interpretation guardrails:

```text
PASS
```

Phase 2G.1 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2G.2 — Topocentric Deep Space Network Geometry

## Goal

Phase 2G.2 extends the Phase 2G.1 Earth-center lunar-occultation reconstruction to physically located Deep Space Network reference stations on Earth's surface.

Phase 2G.1 established that the dominant lunar-flyby communications interruption could be independently reconstructed using:

```text
Earth center
→ Orion
→ Moon occultation
```

The remaining question was whether part of the several-minute difference between MissionLab's Earth-center geometric contacts and NASA's public communications LOS/AOS timing could be explained by:

```text
topocentric parallax
```

from actual Deep Space Network locations.

The specific Phase 2G.2 questions are:

```text
How does lunar occultation timing change
when the observer moves from Earth's center
to a DSN ground location?

Which representative DSN complexes are
geometrically capable of viewing Orion
during the NASA public contact window?

How much of the Phase 2G.1 timing residual
can topocentric geometry explain?
```

Phase 2G.2 does not attempt to identify the operationally assigned Artemis II antenna.

---

# Parent Phase 2G.1 Result

Phase 2G.1 derived the geocentric occultation interval:

```text
Ingress:
2026-04-06T22:41:43.652252Z

Egress:
2026-04-06T23:21:35.489288Z

Duration:
2391.837 s
39.864 min
```

NASA public operational reference:

```text
LOS:
2026-04-06T22:44:00Z

AOS:
2026-04-06T23:25:00Z
```

Earth-center offsets:

```text
Ingress - NASA LOS:
-136.348 s

Egress - NASA AOS:
-204.511 s
```

Total absolute timing offset:

```text
340.858 s
```

Phase 2G.2 therefore investigates whether replacing the Earth-center observer with an Earth-surface DSN reference station explains part of this residual.

---

# Reference Dataset

Created:

```text
data/reference/dsn_topocentric_geometry_reference.json
```

Dataset identifier:

```text
phase2g2_dsn_topocentric_geometry_reference
```

Provenance:

```text
MIXED_NAIF_REFERENCE_AND_NASA_REPORTED
```

The dataset preserves:

```text
NASA public communications timing
NASA public Earthset/Earthrise context
NAIF DSN station coordinates
NAIF DSN station velocities
station coordinate epoch
Earth reference spheroid
Earth-orientation kernel identity
model assumptions
validation thresholds
interpretation guardrails
```

---

# DSN Reference-Station Strategy

Phase 2G.2 uses one representative 70-meter antenna from each of the three Deep Space Network complexes:

```text
DSS-14
Goldstone, California

DSS-43
Canberra, Australia

DSS-63
Madrid, Spain
```

These stations provide geographically separated topocentric reference locations.

Their purpose is:

```text
geometric comparison
```

not:

```text
operational tracking assignment
```

The analysis explicitly records:

```text
operational_assignment_claimed = FALSE
```

for all three stations.

---

# Why Representative Stations Are Used

Public sources examined for Phase 2G.2 did not establish the exact DSS antenna assigned to the April 6 lunar-flyby LOS/AOS interval with sufficient confidence for MissionLab to make an operational attribution.

Therefore MissionLab does not select or tune a station in order to reproduce NASA's public timestamps.

Instead, the three DSN complexes are sampled using authoritative fixed reference stations.

The logic is:

```text
Goldstone reference geometry
Canberra reference geometry
Madrid reference geometry

        ↓

compare physical visibility
and lunar-occultation timing
```

Any similarity to NASA timing is treated as:

```text
geometric consistency
```

and not proof of operational assignment.

---

# NAIF Station Reference

Station coordinates and plate-motion velocities come from the NAIF Deep Space Network ITRF93 station reference.

Coordinate frame:

```text
ITRF93
```

Reference epoch:

```text
2003 JAN 01 00:00:00 TDB
```

Station motion model:

```text
constant Cartesian plate velocity
```

Units:

```text
position:
meters

velocity:
meters per year
```

MissionLab propagates each station from the 2003.0 reference epoch to the requested 2026 calculation time.

---

# DSS-14 Reference

Complex:

```text
Goldstone
```

Diameter:

```text
70 m
```

ITRF93 position at reference epoch:

```text
X = -2353621.420 m
Y = -4641341.472 m
Z = +3677052.318 m
```

Velocity:

```text
VX = -0.0180 m/year
VY = +0.0065 m/year
VZ = -0.0038 m/year
```

---

# DSS-43 Reference

Complex:

```text
Canberra
```

Diameter:

```text
70 m
```

ITRF93 position at reference epoch:

```text
X = -4460894.917 m
Y = +2682361.507 m
Z = -3674748.152 m
```

Velocity:

```text
VX = -0.0335 m/year
VY = -0.0041 m/year
VZ = +0.0392 m/year
```

---

# DSS-63 Reference

Complex:

```text
Madrid
```

Diameter:

```text
70 m
```

ITRF93 position at reference epoch:

```text
X = +4849092.518 m
Y = -360180.348 m
Z = +4115109.251 m
```

Velocity:

```text
VX = -0.0100 m/year
VY = +0.0242 m/year
VZ = +0.0156 m/year
```

---

# Earth Orientation

A topocentric calculation requires the rotating Earth-fixed station position to be transformed into the inertial trajectory frame.

Phase 2G.2 uses the high-precision NAIF Earth binary PCK already introduced during the entry-geometry work:

```text
earth_1962_260806_2126_combined.bpc
```

Validated SHA256:

```text
CC87AD1A495CF598800BA403763D350F087AC0B97DA9FEC603278A3864C6A53E
```

Station transformation:

```text
ITRF93
→
J2000
```

is evaluated at every requested epoch.

The kernel hash is checked before analysis to prevent silent Earth-orientation input changes.

---

# Orion State Reconstruction

Orion continues to use the primary public flight-derived trajectory.

Frame:

```text
J2000
```

Between public OEM states, Orion position is reconstructed using:

```text
piecewise cubic Hermite interpolation
```

from adjacent:

```text
position
+
velocity
```

states.

This preserves consistency with Phase 2G.1.

---

# Moon State Reconstruction

Moon state:

```text
SPICE DE440S
```

Target:

```text
MOON
```

Observer:

```text
EARTH
```

Frame:

```text
J2000
```

Aberration correction:

```text
NONE
```

The same spherical SPICE mean-radius Moon used in Phase 2G.1 is retained.

---

# Station Propagation

For each station:

```text
r_station(t)
=
r_station(epoch)
+
v_station × elapsed_years
```

The propagated position remains in:

```text
ITRF93
```

until transformed to J2000 using the Earth binary PCK.

This incorporates the published plate-motion velocity rather than treating the 2003 reference position as fixed through 2026.

---

# Topocentric Occultation Geometry

For a station position:

```text
S
```

Orion:

```text
O
```

Moon:

```text
M
```

define:

```text
V = O - S
```

and:

```text
W = M - S
```

The projection parameter is:

```text
u = (W dot V) / (V dot V)
```

The projected point along the station-Orion LOS is:

```text
P = u V
```

The Moon-center distance from the LOS is:

```text
d = |W - P|
```

The lunar-limb clearance becomes:

```text
C = d - R_moon
```

A lunar occultation requires:

```text
0 < u < 1
```

and:

```text
C < 0
```

This is the same physical test as Phase 2G.1, but the observer is now a moving Earth-surface station rather than Earth's center.

---

# Local Horizon Geometry

Topocentric lunar-occultation timing alone is not sufficient.

A station must also have Orion above its local horizon to be a plausible direct RF observer.

MissionLab therefore transforms Orion into:

```text
ITRF93
```

and computes a local geodetic vertical using the Earth reference spheroid.

The station-Orion elevation is then derived from:

```text
elevation
=
asin(
unit(station_to_Orion)
dot
local_up
)
```

Horizon threshold:

```text
0 deg
```

Therefore:

```text
elevation > 0
```

is required for basic geometric plausibility as a direct observer.

This is a simple geometric horizon test.

It is not an operational antenna mask.

---

# Analysis Window

Permanent Phase 2G.2 analysis interval:

```text
2026-04-06T22:00:00Z
through
2026-04-07T00:00:00Z
```

Sampling interval:

```text
30 s
```

Inclusive timestamps per station:

```text
241
```

Reference stations:

```text
3
```

Total sampled rows:

```text
723
```

The permanent CSV row count was independently verified.

---

# DSS-14 Goldstone Result

Topocentric ingress:

```text
2026-04-06T22:42:01.283698Z
```

Topocentric egress:

```text
2026-04-06T23:21:30.325466Z
```

Duration:

```text
2369.042 s
39.484 min
```

Shift from Earth-center geometry:

```text
Ingress:
+17.631 s

Egress:
-5.164 s
```

Difference from NASA public timing:

```text
Ingress - NASA LOS:
-118.716 s

Egress - NASA AOS:
-209.675 s
```

Total absolute NASA timing offset:

```text
328.391 s
```

Orion elevation at NASA LOS:

```text
-78.274 deg
```

Orion elevation at NASA AOS:

```text
-81.897 deg
```

Therefore:

```text
above horizon at both NASA contacts:
FALSE
```

Goldstone is not a plausible direct Earth-to-Orion observer during this interval under the modeled geometry.

---

# DSS-43 Canberra Result

Topocentric ingress:

```text
2026-04-06T22:42:50.341173Z
```

Topocentric egress:

```text
2026-04-06T23:23:08.532040Z
```

Duration:

```text
2418.191 s
40.303 min
```

Shift from Earth-center geometry:

```text
Ingress:
+66.689 s

Egress:
+93.043 s
```

Difference from NASA public timing:

```text
Ingress - NASA LOS:
-69.659 s

Egress - NASA AOS:
-111.468 s
```

Total absolute NASA timing offset:

```text
181.127 s
```

Orion elevation at NASA LOS:

```text
+25.504 deg
```

Orion elevation at NASA AOS:

```text
+17.388 deg
```

Therefore:

```text
above horizon at both NASA contacts:
TRUE
```

At NASA LOS:

```text
geometrically occulted:
TRUE
```

At NASA AOS:

```text
geometrically occulted:
FALSE
```

Among the three representative 70-meter reference antennas, DSS-43 is the only one with direct geometric visibility to Orion at both NASA public contact times.

---

# DSS-63 Madrid Result

Topocentric ingress:

```text
2026-04-06T22:40:48.695648Z
```

Topocentric egress:

```text
2026-04-06T23:20:01.160190Z
```

Duration:

```text
2352.465 s
39.208 min
```

Shift from Earth-center geometry:

```text
Ingress:
-54.957 s

Egress:
-94.329 s
```

Difference from NASA public timing:

```text
Ingress - NASA LOS:
-191.304 s

Egress - NASA AOS:
-298.840 s
```

Total absolute NASA timing offset:

```text
490.144 s
```

Orion elevation at NASA LOS:

```text
-9.473 deg
```

Orion elevation at NASA AOS:

```text
-2.732 deg
```

Therefore:

```text
above horizon at both NASA contacts:
FALSE
```

Madrid is also not a plausible direct Earth-to-Orion observer at these times under the modeled geometry.

---

# Geometric Plausibility Result

Reference stations above the local geometric horizon at both NASA public contact times:

```text
DSS-43
```

Only:

```text
Canberra
```

passes this basic topocentric visibility test among the three representative 70-meter antennas.

This result is derived from geometry.

It does not establish an operational tracking assignment.

---

# Timing Similarity Result

Earth-center model:

```text
total absolute NASA contact offset:
340.858 s
```

Best representative topocentric model:

```text
DSS-43
181.127 s
```

Absolute reduction:

```text
159.731 s
```

Fractional improvement:

```text
46.862%
```

Therefore almost half of the Phase 2G.1 Earth-center timing residual can be explained simply by replacing:

```text
Earth center
```

with:

```text
a physically plausible Earth-surface observer
```

at the Canberra DSN complex reference location.

---

# Important Non-Conclusion

The following statement is NOT made:

```text
DSS-43 was the operational Artemis II
flyby tracking antenna.
```

MissionLab does not have sufficient public evidence in this phase to establish that claim.

The actual conclusion is:

```text
Among the representative 70-meter reference
antennas at the three DSN complexes,
DSS-43 is the only station geometrically above
the horizon at both NASA public contact times
and also gives the closest pure occultation
timing agreement.
```

That is a geometry result.

It is not a network-assignment result.

---

# Why Residual Timing Still Remains

Even with Canberra topocentric geometry:

```text
Ingress residual:
-69.659 s

Egress residual:
-111.468 s
```

MissionLab intentionally does not tune these remaining differences away.

Possible contributors outside the Phase 2G.2 model include:

```text
actual assigned DSS antenna location
public minute-level timestamp precision
local lunar limb topography
signal acquisition criteria
receiver or transmitter state
antenna pointing constraints
link-margin thresholds
network scheduling
handover timing
operational reporting latency
light-time conventions
other communications-system constraints
```

No unsupported correction is introduced merely to force agreement.

---

# Communications-Layer Separation

Phase 2G now establishes three distinct layers:

```text
SPACECRAFT / CELESTIAL GEOMETRY
        ↓
Earthset / Earthrise
and geocentric lunar occultation

GROUND-STATION GEOMETRY
        ↓
topocentric station-specific
lunar occultation
and local horizon

OPERATIONAL COMMUNICATIONS
        ↓
NASA LOS / AOS
network configuration
tracking assignment
link availability
```

These layers are physically related but are not interchangeable.

This distinction is foundational for the later communications-event reconstruction.

---

# Permanent Sampled Product

Generated:

```text
data/processed/communications/dsn_topocentric_geometry.csv
```

Rows:

```text
723
```

Each sampled row contains:

```text
station
UTC
projection fraction
Moon-between-station-and-Orion flag
lunar-limb clearance
Moon-center LOS distance
geometric occultation flag
Orion elevation
station-Orion range
one-way light time
```

The product is reproducibly generated and remains ignored from Git.

---

# Permanent Summary

Generated:

```text
data/processed/communications/dsn_topocentric_summary.json
```

Product identifier:

```text
phase2g2_dsn_topocentric_geometry
```

Provenance:

```text
MISSIONLAB_DERIVED_TOPOCENTRIC_GEOMETRY_WITH_NAIF_STATION_REFERENCE_AND_NASA_REPORTED_TIMING
```

The summary preserves:

```text
model configuration
NASA reference timing
geocentric parent result
station-specific contacts
station elevations
horizon plausibility
timing ranking
timing improvement
non-assignment statement
interpretation guardrails
```

This processed summary remains ignored from Git.

---

# Permanent Figures

Created:

```text
docs/assets/communications/phase2g2_dsn_topocentric_occultation.svg
```

This figure compares:

```text
DSS-14 lunar-limb clearance
DSS-43 lunar-limb clearance
DSS-63 lunar-limb clearance
NASA LOS
NASA AOS
geometric lunar limb
```

Also created:

```text
docs/assets/communications/phase2g2_dsn_station_elevation.svg
```

This figure compares:

```text
DSS-14 Orion elevation
DSS-43 Orion elevation
DSS-63 Orion elevation
geometric horizon
NASA LOS
NASA AOS
```

Together the figures separate:

```text
occultation
```

from:

```text
basic ground-station visibility
```

---

# Permanent Analyzer

Created:

```text
scripts/analysis/build_dsn_topocentric_geometry.py
```

The analyzer performs:

```text
authoritative reference loading
Earth binary-PCK hash verification
station plate-motion propagation
ITRF93-to-J2000 transformation
Orion Hermite interpolation
SPICE Moon evaluation
station-Orion LOS construction
lunar occultation calculation
local geodetic elevation calculation
30-second sampled timeline generation
sub-second contact refinement
geocentric comparison
NASA timing comparison
horizon-plausibility classification
timing-similarity ranking
deterministic SVG generation
processed CSV generation
processed summary generation
```

---

# Independent Validator

Created:

```text
scripts/validation/validate_dsn_topocentric_geometry.py
```

The validator independently reconstructs:

```text
station propagation
Earth orientation
topocentric occultation
contact roots
local elevations
NASA timing offsets
horizon plausibility
timing ranking
topocentric improvement
```

It independently verifies the authoritative reference values for:

```text
DSS-14
DSS-43
DSS-63
```

and checks:

```text
station positions
station velocities
Earth kernel SHA256
3262 trajectory states
two contacts per station
summary agreement
only DSS-43 above horizon at both NASA contacts
DSS-43 best pure timing agreement
DSS-43 occulted at NASA LOS
DSS-43 clear at NASA AOS
minimum timing-improvement threshold
723 sampled output rows
occultation SVG
elevation SVG
non-assignment guardrails
```

---

# Independent Validation Result

Independent results:

```text
DSS-43

Ingress:
2026-04-06T22:42:50.341173Z

Egress:
2026-04-06T23:23:08.532040Z

NASA LOS elevation:
+25.504 deg

NASA AOS elevation:
+17.388 deg

Total absolute NASA timing offset:
181.127 s

Horizon plausible:
TRUE
```

```text
DSS-14

Ingress:
2026-04-06T22:42:01.283698Z

Egress:
2026-04-06T23:21:30.325466Z

NASA LOS elevation:
-78.274 deg

NASA AOS elevation:
-81.897 deg

Total absolute NASA timing offset:
328.391 s

Horizon plausible:
FALSE
```

```text
DSS-63

Ingress:
2026-04-06T22:40:48.695648Z

Egress:
2026-04-06T23:20:01.160190Z

NASA LOS elevation:
-9.473 deg

NASA AOS elevation:
-2.732 deg

Total absolute NASA timing offset:
490.144 s

Horizon plausible:
FALSE
```

Derived validation conclusions:

```text
only reference station above horizon
at both NASA contacts:
DSS-43
```

```text
best pure timing agreement:
DSS-43
```

```text
timing improvement vs Earth-center:
46.862%
```

Generated products:

```text
sampled rows:
723

summary:
PASS

occultation figure:
PASS

elevation figure:
PASS
```

Final independent validator result:

```text
PASS
```

---

# Interpretation Guardrails

## Guardrail 1

```text
Representative 70-meter station geometry
!=
actual Artemis II tracking assignment
```

## Guardrail 2

```text
Best NASA timing agreement
!=
proof of operational antenna identity
```

## Guardrail 3

```text
Topocentric lunar visibility
!=
actual RF link availability
```

## Guardrail 4

```text
Above geometric horizon
!=
antenna scheduled and tracking
```

## Guardrail 5

Phase 2G.2 does not infer:

```text
antenna gain
link budget
signal strength
modulation state
network schedule
handover logic
receiver lock
transmitter state
```

## Guardrail 6

NASA public LOS/AOS timestamps remain:

```text
minute-level operational references
```

not exact physical lunar-limb observations.

## Guardrail 7

```text
DSN RF geometry
!=
O2O optical availability
```

---

# Engineering Significance

Phase 2G.2 demonstrates quantitatively why an Earth-center communications model is incomplete.

Moving the observer from:

```text
Earth center
```

to:

```text
a physical DSN location
```

changes lunar-occultation contacts by approximately tens to more than ninety seconds.

For Canberra:

```text
Ingress shift from Earth center:
+66.689 s

Egress shift from Earth center:
+93.043 s
```

That change reduces the NASA timing residual by:

```text
46.862%
```

without introducing any fitted parameter.

The result therefore provides a physically motivated explanation for a substantial portion of the Phase 2G.1 residual.

Just as importantly, the local horizon calculation eliminates Goldstone and Madrid as plausible direct observers at the public contact times for these representative reference antennas.

This demonstrates how:

```text
trajectory
+
Earth rotation
+
station location
+
Moon geometry
```

combine into mission-operational communications geometry.

---

# Phase 2G.2 Status

NAIF station reference:

```text
PASS
```

Station plate motion:

```text
PASS
```

Earth orientation:

```text
PASS
```

Orion interpolation:

```text
PASS
```

Moon geometry:

```text
PASS
```

Topocentric occultation:

```text
PASS
```

Local horizon reconstruction:

```text
PASS
```

NASA timing comparison:

```text
PASS
```

DSS-43 geometric plausibility:

```text
PASS
```

Operational assignment guardrail:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2G.2 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2H.1 — Operational Communications Event Catalog

## Goal

Phase 2H.1 begins the operational communications reconstruction portion of A2 MissionLab.

Phase 2G reconstructed the physical communications geometry:

```text
2G.1
geocentric lunar occultation

2G.2
topocentric DSN reference-station geometry
```

Phase 2H moves from:

```text
what geometry permits
```

to:

```text
what NASA publicly reported happened operationally
```

The first requirement is therefore a communications event catalog that preserves the actual precision and semantics of the public evidence.

The central rule is:

```text
Do not turn imprecise public reporting
into artificially precise mission telemetry.
```

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_communications_event_catalog.json
```

Dataset identifier:

```text
phase2h1_artemis_ii_communications_event_catalog
```

Provenance:

```text
NASA_AND_NASA_JPL_REPORTED_WITH_MISSIONLAB_APPROXIMATE_ANCHORS
```

The catalog contains:

```text
16 events
```

spanning:

```text
RF communications
optical communications
geometric communications context
network transition context
planned events
reported events
anomaly events
recovery events
```

---

# Why a Precision Taxonomy Is Required

NASA public mission reporting does not use one uniform timing convention.

Different communications events are described using phrases such as:

```text
6:44 p.m.
just after noon
about two hours before
after translunar injection
shortly afterward
moments after Earthrise
```

These statements do not all support the same timestamp precision.

MissionLab therefore preserves source precision as part of the data model.

---

# Precision Classes

## EXACT

Definition:

```text
The source provides sufficient explicit
precision to treat the event timestamp
as an exact event value.
```

Phase 2H.1 count:

```text
0
```

No public communications event in this first catalog is promoted to this class.

---

## MINUTE_LEVEL

Definition:

```text
The source identifies a specific minute.

Seconds are stored as zero only as a
representation convention.

The source does not support second-level
measurement precision.
```

Phase 2H.1 count:

```text
7
```

Examples include:

```text
planned Earthset
reported Earthset
planned blackout start
reported blackout start
planned Earthrise
reported Earthrise
planned DSN reacquisition
```

---

## APPROXIMATE

Definition:

```text
The source provides approximate timing.

A computational reference anchor may be
constructed, but the anchor is explicitly
marked non-exact.
```

Phase 2H.1 count:

```text
2
```

Events:

```text
O2O 100 GB downlink milestone
unexpected Flight Day 9 return-link loss
```

---

## DATE_LEVEL

Definition:

```text
The source establishes the calendar date
but does not justify assigning a useful
time of day.
```

Phase 2H.1 count:

```text
3
```

Events include:

```text
early Madrid DSN communications evidence
deep-space emergency communications test
O2O links to two U.S. ground stations
```

---

## SEQUENCE_ONLY

Definition:

```text
The source establishes ordering relative
to another mission event or phase but does
not support assigning a timestamp.
```

Phase 2H.1 count:

```text
4
```

Examples:

```text
NSN leads communications soon after launch
NSN-to-DSN support transition after TLI
DSN reacquisition moments after Earthrise
two-way communications restored shortly
after the Flight Day 9 return-link loss
```

These events intentionally receive no invented UTC or MET timestamp.

---

# Event-State Taxonomy

The catalog also separates event timing precision from event semantics.

## PLANNED

NASA-published expected or scheduled event.

## OBSERVED_REPORTED

NASA or NASA/JPL reporting states that the event occurred.

## REPORTED

NASA reports an event or anomaly, but the available public evidence does not justify a more precise observed event timestamp.

## SEQUENCE_REPORTED

NASA establishes event ordering but not a defensible absolute timestamp.

This separation allows MissionLab to preserve distinctions such as:

```text
planned Earthset
versus
reported Earthset
```

rather than collapsing them into one event.

---

# Catalog Composition

Total events:

```text
16
```

Precision counts:

```text
EXACT:
0

MINUTE_LEVEL:
7

APPROXIMATE:
2

DATE_LEVEL:
3

SEQUENCE_ONLY:
4
```

Domain counts:

```text
GEOMETRIC_CONTEXT:
4

OPTICAL:
2

RF:
10
```

---

# Near Space Network Initial Support

Catalog event:

```text
nsn_leads_initial_orion_communications
```

Precision:

```text
SEQUENCE_ONLY
```

Ordering:

```text
SOON_AFTER_LAUNCH_BEFORE_DSN_HANDOFF
```

MissionLab does not assign a fabricated handoff timestamp.

The evidence establishes that the Near Space Network initially led Orion communications and that support later transitioned toward the Deep Space Network.

---

# Early Deep Space Network Evidence

Catalog event:

```text
dsn_madrid_early_mission_signal_acquisition
```

Precision:

```text
DATE_LEVEL
```

Date:

```text
2026-04-01
```

Associated DSN assets:

```text
DSS-54
DSS-56
```

The source demonstrates early Artemis II communications activity from Madrid.

It does not provide a source-supported event time suitable for MissionLab.

---

# NSN-to-DSN Primary Support Transition

Catalog event:

```text
primary_support_transition_nsn_to_dsn
```

Precision:

```text
SEQUENCE_ONLY
```

Ordering:

```text
AFTER_TRANSLUNAR_INJECTION
```

This is intentionally not represented using an exact or approximate handoff timestamp.

The public evidence supports mission sequence but not a defensible transition epoch.

---

# Emergency Communications Test

Catalog event:

```text
dsn_emergency_communications_test
```

Final precision classification:

```text
DATE_LEVEL
```

Event state:

```text
OBSERVED_REPORTED
```

Date:

```text
2026-04-03
```

The initial NASA reporting described the test as planned for later in Flight Day 3.

A later NASA update reported that the crew had been testing Orion's emergency communications system in deep space.

Therefore the permanent catalog records:

```text
the test occurred
```

but does not invent:

```text
an execution timestamp
```

---

# O2O Ground-Station Activity

Catalog event:

```text
o2o_two_us_ground_station_links
```

Domain:

```text
OPTICAL
```

Precision:

```text
DATE_LEVEL
```

Date:

```text
2026-04-03
```

NASA reported O2O connecting to two U.S.-based optical ground stations and transmitting:

```text
high-definition video
mission data
```

The event is preserved separately from RF network availability.

---

# O2O 100 GB Milestone

Catalog event:

```text
o2o_100_gb_downlink_milestone
```

Precision:

```text
APPROXIMATE
```

NASA timing language:

```text
just after 12 p.m. EDT
```

MissionLab computational anchor:

```text
2026-04-04T16:00:00Z
```

Mission elapsed time at anchor:

```text
02:17:24:48
```

The anchor semantics are explicitly:

```text
REFERENCE_CLOCK_ANCHOR_FOR_JUST_AFTER_12_PM_EDT
```

and:

```text
anchor_is_not_exact = TRUE
```

Therefore:

```text
16:00 UTC
```

must never be presented as the observed exact milestone time.

---

# Flight Day 6 Planned Earthset

Catalog event:

```text
lunar_earthset_planned
```

UTC:

```text
2026-04-06T22:45:00Z
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
PLANNED
```

---

# Flight Day 6 Reported Earthset

Catalog event:

```text
lunar_earthset_reported
```

UTC:

```text
2026-04-06T22:41:00Z
```

MET:

```text
05:00:05:48
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
OBSERVED_REPORTED
```

Difference from planned Earthset:

```text
-240 s
```

or:

```text
4 minutes earlier
```

This distinction is retained permanently rather than replacing the plan with the later report.

---

# Planned Lunar Blackout Start

Catalog event:

```text
lunar_blackout_start_planned
```

UTC:

```text
2026-04-06T22:44:00Z
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
PLANNED
```

---

# Reported Lunar Blackout Start

Catalog event:

```text
lunar_blackout_start_reported
```

UTC:

```text
2026-04-06T22:44:00Z
```

MET:

```text
05:00:08:48
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
OBSERVED_REPORTED
```

Difference from planned blackout:

```text
0 s
```

at the available minute-level precision.

---

# Earthset-to-Blackout Separation

Reported Earthset:

```text
22:41 UTC
```

Reported blackout start:

```text
22:44 UTC
```

Separation:

```text
180 s
3 min
```

This reinforces the Phase 2G principle that:

```text
geometric Earth disappearance
```

and:

```text
operational RF communications loss
```

are related but not interchangeable mission events.

---

# Planned Lunar Earthrise

Catalog event:

```text
lunar_earthrise_planned
```

UTC:

```text
2026-04-06T23:25:00Z
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
PLANNED
```

---

# Reported Lunar Earthrise

Catalog event:

```text
lunar_earthrise_reported
```

UTC:

```text
2026-04-06T23:24:00Z
```

MET:

```text
05:00:48:48
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
OBSERVED_REPORTED
```

Difference from planned Earthrise:

```text
-60 s
```

or:

```text
1 minute earlier
```

---

# Planned DSN Reacquisition

Catalog event:

```text
dsn_reacquisition_planned
```

UTC:

```text
2026-04-06T23:25:00Z
```

MET:

```text
05:00:49:48
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
PLANNED
```

---

# Live DSN Reacquisition Report

Catalog event:

```text
dsn_reacquisition_live_report
```

Precision:

```text
SEQUENCE_ONLY
```

Ordering:

```text
MOMENTS_AFTER_REPORTED_EARTHRISE
```

NASA's public live reporting establishes that the DSN reacquired Orion after Earthrise.

It does not establish a source-supported exact reacquisition timestamp suitable for MissionLab.

Therefore the live event receives no invented UTC or MET.

---

# Earthrise-to-Public-AOS Separation

Reported Earthrise:

```text
23:24 UTC
```

Planned public AOS:

```text
23:25 UTC
```

Separation:

```text
60 s
1 min
```

The live reacquisition itself remains:

```text
SEQUENCE_ONLY
```

rather than being silently converted to exactly 23:25 UTC.

---

# Phase 2G Cross-Check

The Phase 2H.1 blackout reference was cross-checked against the Phase 2G communications reference.

Phase 2G LOS:

```text
2026-04-06T22:44:00Z
```

Phase 2H planned blackout:

```text
2026-04-06T22:44:00Z
```

Phase 2H reported blackout:

```text
2026-04-06T22:44:00Z
```

Result:

```text
PASS
```

Phase 2G AOS reference:

```text
2026-04-06T23:25:00Z
```

Phase 2H planned AOS:

```text
2026-04-06T23:25:00Z
```

Result:

```text
PASS
```

This keeps the communications geometry and operational-event datasets internally consistent without conflating their meanings.

---

# Flight Day 9 Unexpected Return-Link Loss

Catalog event:

```text
unexpected_return_link_loss
```

Domain:

```text
RF
```

Precision:

```text
APPROXIMATE
```

NASA reported the event occurred:

```text
about two hours before RTC2
```

Existing MissionLab RTC2 reference:

```text
2026-04-10T02:53:00Z
```

MissionLab approximate computational anchor:

```text
~2026-04-10T00:53:00Z
```

Approximate MET:

```text
~08:02:17:48
```

Anchor-to-RTC2 separation:

```text
~7200 s
~2.000 h
```

The catalog explicitly records:

```text
anchor_is_not_exact = TRUE
```

Therefore:

```text
00:53 UTC
```

must never be described as NASA's exact observed outage time.

It exists only to place the phrase:

```text
about two hours before RTC2
```

approximately on the common MissionLab clock.

---

# Flight Day 9 Communications Recovery

Catalog event:

```text
two_way_communications_reestablished
```

Precision:

```text
SEQUENCE_ONLY
```

Ordering:

```text
SHORTLY_AFTER_UNEXPECTED_RETURN_LINK_LOSS_BEFORE_RTC2
```

NASA's report establishes:

```text
unexpected return-link LOS
        ↓
communications recovery
        ↓
RTC2 preparations continue
```

but does not support assigning an exact recovery timestamp.

MissionLab therefore preserves the sequence without inventing one.

---

# Timeline Builder

Created:

```text
scripts/analysis/build_communications_event_timeline.py
```

The builder performs:

```text
catalog validation
mission-clock loading
UTC parsing
MET conversion
precision enforcement
planned-versus-reported comparison
Phase 2G cross-checking
RTC2 anchor correlation
approximate-anchor handling
domain counting
precision counting
state counting
timeline CSV generation
summary JSON generation
deterministic SVG generation
```

---

# Permanent Timeline Product

Generated:

```text
data/processed/communications/communications_event_timeline.csv
```

Rows:

```text
16
```

The CSV includes:

```text
event ID
event name
domain
network
event state
precision
time representation
source timestamp
approximate anchor
date
MET
approximate-MET flag
ordering
source ID
provenance
```

The generated file remains ignored from Git.

---

# Permanent Summary Product

Generated:

```text
data/processed/communications/communications_event_summary.json
```

Product identifier:

```text
phase2h1_communications_event_timeline
```

The summary includes:

```text
event counts
precision counts
domain counts
event-state counts
time-representation counts
planned-versus-reported differences
Flight Day 6 separations
Flight Day 9 approximate anchor
RTC2 reference
precision guardrails
output paths
```

The generated file remains ignored from Git.

---

# Permanent Figure

Created:

```text
docs/assets/communications/phase2h1_communications_event_timeline.svg
```

The figure places only events with defensible timeline positions on the UTC axis.

Marker semantics:

```text
circle
reported event

square
planned event

x
approximate anchor
```

Events classified as:

```text
DATE_LEVEL
SEQUENCE_ONLY
```

are intentionally not assigned an artificial position on the time axis.

---

# Independent Validator

Created:

```text
scripts/validation/validate_communications_event_timeline.py
```

The validator independently checks:

```text
dataset identity
product identity
16-event catalog
exact event ID set
source references
precision semantics
minute-level timestamp integrity
approximate-anchor guardrails
precision counts
domain counts
planned-versus-reported Earthset difference
planned-versus-reported blackout difference
planned-versus-reported Earthrise difference
Earthset-to-blackout separation
Earthrise-to-planned-AOS separation
Phase 2G timing consistency
RTC2 identity
Flight Day 9 approximate anchor
emergency communications test precision
NSN-to-DSN handoff precision
live DSN reacquisition precision
mission launch epoch
summary contents
16-row CSV
absence of invented MET values
timeline SVG
guardrails
```

---

# Independent Validation Result

Catalog:

```text
events:
16
```

Precision:

```text
EXACT:
0

MINUTE_LEVEL:
7

APPROXIMATE:
2

DATE_LEVEL:
3

SEQUENCE_ONLY:
4
```

Flight Day 6:

```text
reported Earthset - planned:
-240 s

reported blackout - planned:
0 s

reported Earthrise - planned:
-60 s

reported Earthset -> blackout:
180 s

reported Earthrise -> planned AOS:
60 s
```

Flight Day 9:

```text
RTC2:
2026-04-10T02:53:00Z

approximate return-link-loss anchor:
~2026-04-10T00:53:00Z

separation:
~2.000 h
```

Precision guardrails:

```text
NSN-to-DSN handoff:
SEQUENCE_ONLY

emergency communications test:
DATE_LEVEL

live DSN reacquisition:
SEQUENCE_ONLY

return-link-loss anchor:
APPROXIMATE
```

Products:

```text
timeline CSV rows:
16

summary:
PASS

timeline figure:
PASS
```

Final independent validation:

```text
PASS
```

---

# Interpretation Guardrails

## Guardrail 1

```text
Minute-level timestamp
!=
second-level measurement
```

A stored `:00` second does not imply the event occurred exactly at zero seconds past the minute.

---

## Guardrail 2

```text
Approximate anchor
!=
observed timestamp
```

This applies especially to:

```text
O2O 100 GB milestone
Flight Day 9 return-link loss
```

---

## Guardrail 3

```text
DATE_LEVEL
!=
known time of day
```

No artificial time is assigned to date-only evidence.

---

## Guardrail 4

```text
SEQUENCE_ONLY
!=
timestamped event
```

No artificial timestamp or MET is assigned.

---

## Guardrail 5

```text
PLANNED
!=
OBSERVED_REPORTED
```

Planned and live-reported mission events remain separate catalog objects.

---

## Guardrail 6

```text
Earthset / Earthrise
!=
RF LOS / AOS
```

Geometric context remains distinct from communications-system state.

---

## Guardrail 7

```text
O2O optical activity
!=
primary RF network availability
```

Optical and RF systems remain distinct communications domains.

---

## Guardrail 8

Phase 2H.1 does not infer:

```text
antenna assignment
link margin
signal strength
network schedule
receiver lock threshold
transmitter configuration
unreported outage duration
unreported recovery timestamp
```

---

# Engineering Significance

Phase 2H.1 establishes a provenance-safe operational communications timeline.

The communications model now contains distinct representations for:

```text
physical geometry
planned operations
reported events
approximate reports
date-only evidence
sequence-only evidence
RF systems
optical systems
communications anomalies
communications recovery
```

The Flight Day 6 sequence now demonstrates explicitly:

```text
reported Earthset
22:41
        ↓
reported communications blackout
22:44
        ↓
reported Earthrise
23:24
        ↓
DSN reacquisition
moments afterward
```

This provides an operational complement to the Phase 2G geometric reconstruction.

The Flight Day 9 event adds a different communications failure mode:

```text
not lunar occultation
not planned

data-rate change
        ↓
unexpected return-link LOS
        ↓
communications recovery
        ↓
RTC2
```

That gives MissionLab both:

```text
planned geometry-driven communications loss
```

and:

```text
unplanned communications-system anomaly
```

on the same mission evidence framework.

---

# Phase 2H.1 Status

Source catalog:

```text
PASS
```

Precision taxonomy:

```text
PASS
```

Event-state taxonomy:

```text
PASS
```

Planned-versus-reported separation:

```text
PASS
```

Mission-clock integration:

```text
PASS
```

Phase 2G cross-check:

```text
PASS
```

Flight Day 9 approximate anchoring:

```text
PASS
```

Non-invention guardrails:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2H.1 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2H.2 — Mission-Clock Communications Correlation

## Goal

Phase 2H.2 integrates previously independent Artemis II mission products onto one common mission clock.

The purpose is not to create new mission facts.

The purpose is to correlate existing products while preserving:

```text
source provenance
timing precision
derived-versus-reported distinctions
planned-versus-reported distinctions
approximate-event guardrails
```

The integrated sources are:

```text
Phase 1
trajectory
lunar SOI
pericynthion
maximum Earth distance
trajectory correction burns

Phase 2G.1
geocentric lunar occultation

Phase 2G.2
topocentric DSN reference-station geometry

Phase 2H.1
operational communications event catalog
```

The result is a synchronized mission-operations timeline.

---

# Permanent Analyzer

Created:

```text
scripts/analysis/build_mission_clock_communications_correlation.py
```

The analyzer combines:

```text
mission configuration
communications event catalog
trajectory event catalog
mission-phase summary
geocentric occultation summary
topocentric DSN summary
communications-event summary
```

It does not alter the underlying products.

Instead, it constructs a new correlation layer.

---

# Permanent Validator

Created:

```text
scripts/validation/validate_mission_clock_communications_correlation.py
```

The validator independently reconstructs and checks:

```text
event identity
event ordering
event timestamps
mission phases
SOI containment
cross-phase timing relationships
approximate-event preservation
minute-level precision preservation
sequence-only event preservation
generated CSV
generated figures
summary metrics
```

---

# Synchronized Event Count

The permanent correlation contains:

```text
17 synchronized events
```

These events span:

```text
optical communications
trajectory correction burns
lunar mission geometry
RF communications
communications anomaly context
```

---

# Mission Phase Counts

The synchronized events are distributed across MissionLab geometric mission phases as follows:

```text
OUTBOUND_TRANSIT:
2

LUNAR_APPROACH:
6

LUNAR_DEPARTURE:
6

TRANS_EARTH_RETURN:
3
```

Total:

```text
17
```

---

# Mission Anchors

Launch epoch:

```text
2026-04-01T22:35:12Z
```

Derived lunar SOI entry:

```text
2026-04-06T04:38:07.532302Z
```

Refined pericynthion:

```text
2026-04-06T23:00:46.177998Z
```

Derived lunar SOI exit:

```text
2026-04-07T17:23:41.922211Z
```

All synchronized events use this common mission clock.

---

# Outbound Optical Context

The first synchronized communications event is the O2O 100 GB milestone anchor.

Approximate anchor:

```text
~2026-04-04T16:00:00Z
```

Approximate MET:

```text
~02:17:24:48
```

Mission phase:

```text
OUTBOUND_TRANSIT
```

Precision remains:

```text
APPROXIMATE
```

This value remains a computational anchor for NASA's public:

```text
just after 12 p.m. EDT
```

language.

It is not promoted to an exact milestone timestamp.

---

# Outbound Correction Burn

OTC:

```text
2026-04-06T03:03:00Z
```

MET:

```text
04:04:27:48
```

Mission phase:

```text
OUTBOUND_TRANSIT
```

The burn occurs before lunar SOI entry.

---

# OTC to Lunar SOI Entry

OTC:

```text
2026-04-06T03:03:00Z
```

Lunar SOI entry:

```text
2026-04-06T04:38:07.532302Z
```

Separation:

```text
5707.532 s
95.126 min
1.585 h
```

This places the outbound trajectory correction approximately 1.6 hours before MissionLab's derived lunar SOI entry.

---

# Lunar SOI Entry

Derived entry:

```text
2026-04-06T04:38:07.532302Z
```

MET:

```text
04:06:02:56
```

Mission phase begins:

```text
LUNAR_APPROACH
```

---

# SOI Entry to Reported Earthset

Reported Earthset:

```text
2026-04-06T22:41:00Z
```

SOI-entry-to-Earthset separation:

```text
64972.468 s
1082.874 min
18.048 h
```

The lunar communications sequence therefore occurs deep inside the derived lunar SOI interval rather than at SOI entry.

---

# Flight Day 6 Integrated Sequence

Phase 2H.2 produces the following synchronized Flight Day 6 sequence:

```text
01. 22:41:00.000
    Reported Earthset

02. 22:41:43.652
    Geocentric occultation ingress

03. 22:42:50.341
    DSS-43 topocentric ingress

04. 22:44:00.000
    Reported RF blackout start

05. 23:00:46.178
    Pericynthion

06. 23:02:51.667
    Maximum Earth-center distance

07. 23:21:35.489
    Geocentric occultation egress

08. 23:23:08.532
    DSS-43 topocentric egress

09. 23:24:00.000
    Reported Earthrise

10. 23:25:00.000
    Planned public DSN AOS
```

This sequence combines:

```text
NASA-reported geometric context
MissionLab-derived geometry
NASA-reported RF operations
NASA-planned RF operations
trajectory-derived mission anchors
```

without collapsing them into one provenance class.

---

# Reported Earthset

Reported Earthset:

```text
2026-04-06T22:41:00Z
```

MET:

```text
05:00:05:48
```

Mission phase:

```text
LUNAR_APPROACH
```

Provenance:

```text
NASA_REPORTED
```

Precision:

```text
MINUTE_LEVEL
```

---

# Geocentric Occultation Ingress

Derived geocentric ingress:

```text
2026-04-06T22:41:43.652252Z
```

MET:

```text
05:00:06:32
```

Mission phase:

```text
LUNAR_APPROACH
```

Provenance:

```text
MISSIONLAB_DERIVED
```

Source layer:

```text
PHASE_2G1
```

---

# Earthset to Geocentric Occultation

Reported Earthset precedes MissionLab's geocentric occultation ingress by approximately:

```text
43.652 s
```

This is not treated as a contradiction.

The NASA Earthset report and the MissionLab spherical mean-lunar-limb geometry are different event definitions with different precision and modeling assumptions.

---

# DSS-43 Topocentric Ingress

Derived DSS-43 reference ingress:

```text
2026-04-06T22:42:50.341173Z
```

MET:

```text
05:00:07:38
```

Mission phase:

```text
LUNAR_APPROACH
```

Source layer:

```text
PHASE_2G2
```

The DSS-43 reference remains:

```text
representative topocentric geometry
```

and not:

```text
an inferred Artemis II operational antenna assignment
```

---

# Geometry to Reported RF Blackout

Reported RF blackout:

```text
2026-04-06T22:44:00Z
```

Geocentric ingress-to-blackout separation:

```text
136.348 s
2.272 min
```

DSS-43 ingress-to-blackout separation:

```text
69.659 s
1.161 min
```

The topocentric reference geometry therefore moves substantially closer to the operational blackout timing than the Earth-center geometry.

Phase 2H.2 does not reinterpret this as proof of station assignment.

---

# Reported RF Blackout Start

Reported blackout start:

```text
2026-04-06T22:44:00Z
```

MET:

```text
05:00:08:48
```

Mission phase:

```text
LUNAR_APPROACH
```

Provenance:

```text
NASA_REPORTED
```

Precision:

```text
MINUTE_LEVEL
```

---

# Blackout to Pericynthion

Reported blackout:

```text
22:44:00 UTC
```

Pericynthion:

```text
23:00:46.177998 UTC
```

Separation:

```text
1006.178 s
16.770 min
```

Therefore Orion reaches closest lunar approach approximately 16.8 minutes after the reported communications blackout begins.

---

# Pericynthion

Refined pericynthion:

```text
2026-04-06T23:00:46.177998Z
```

MET:

```text
05:00:25:34
```

Mission phase:

```text
LUNAR_APPROACH
```

At this instant, Orion remains inside:

```text
geocentric lunar occultation
```

and:

```text
DSS-43 topocentric lunar occultation
```

under the Phase 2G models.

---

# Maximum Earth-Center Distance

Maximum sampled Earth-center distance occurs at:

```text
2026-04-06T23:02:51.667Z
```

MET:

```text
05:00:27:40
```

Mission phase:

```text
LUNAR_DEPARTURE
```

This event occurs:

```text
125.489 s
2.091 min
```

after pericynthion.

This illustrates an important geometric distinction:

```text
minimum Moon-centered range
!=
maximum Earth-centered range
```

The two extrema occur at different mission times.

---

# Geocentric Occultation Egress

Derived geocentric egress:

```text
2026-04-06T23:21:35.489288Z
```

MET:

```text
05:00:46:23
```

Mission phase:

```text
LUNAR_DEPARTURE
```

---

# Geocentric Egress to Reported Earthrise

Reported Earthrise:

```text
2026-04-06T23:24:00Z
```

Separation from geocentric egress:

```text
144.511 s
2.409 min
```

The mean-radius geocentric geometry therefore clears the Moon approximately 2.4 minutes before the minute-level reported Earthrise.

---

# DSS-43 Topocentric Egress

Derived DSS-43 reference egress:

```text
2026-04-06T23:23:08.532040Z
```

MET:

```text
05:00:47:57
```

Mission phase:

```text
LUNAR_DEPARTURE
```

---

# DSS-43 Egress to Reported Earthrise

Reported Earthrise:

```text
23:24:00 UTC
```

DSS-43 egress:

```text
23:23:08.532040 UTC
```

Separation:

```text
51.468 s
0.858 min
```

The DSS-43 reference geometry is therefore less than one minute earlier than the reported Earthrise at the precision available from the public NASA report.

This remains a geometry consistency result rather than an operational station-identification result.

---

# Pericynthion to Reported Earthrise

Pericynthion:

```text
23:00:46.177998 UTC
```

Reported Earthrise:

```text
23:24:00 UTC
```

Separation:

```text
1393.822 s
23.230 min
```

---

# Reported Earthrise

Reported Earthrise:

```text
2026-04-06T23:24:00Z
```

MET:

```text
05:00:48:48
```

Mission phase:

```text
LUNAR_DEPARTURE
```

Provenance:

```text
NASA_REPORTED
```

Precision:

```text
MINUTE_LEVEL
```

---

# Planned Public DSN AOS

Planned public DSN reacquisition:

```text
2026-04-06T23:25:00Z
```

MET:

```text
05:00:49:48
```

Mission phase:

```text
LUNAR_DEPARTURE
```

State:

```text
PLANNED
```

Precision:

```text
MINUTE_LEVEL
```

This remains separate from the live NASA reacquisition report.

---

# Live DSN Reacquisition

The live operational relation remains:

```text
dsn_reacquisition_live_report
```

Precision:

```text
SEQUENCE_ONLY
```

Ordering:

```text
MOMENTS_AFTER_REPORTED_EARTHRISE
```

Permanent Phase 2H.2 representation:

```text
UTC:
NONE

MET:
NONE
```

No timestamp is synthesized from:

```text
planned public AOS
```

or:

```text
reported Earthrise
```

This is an explicit non-invention guardrail.

---

# Planned AOS to Lunar SOI Exit

Planned public AOS:

```text
2026-04-06T23:25:00Z
```

Derived lunar SOI exit:

```text
2026-04-07T17:23:41.922211Z
```

Separation:

```text
64721.922 s
1078.699 min
17.978 h
```

Therefore the communications blackout and reacquisition occur near the lunar flyby itself, while Orion remains inside the adopted lunar SOI for almost another 18 hours.

---

# Lunar SOI Exit

Derived SOI exit:

```text
2026-04-07T17:23:41.922211Z
```

MET:

```text
05:18:48:30
```

Mission phase through this event:

```text
LUNAR_DEPARTURE
```

Afterward:

```text
TRANS_EARTH_RETURN
```

---

# SOI Exit to RTC1

RTC1:

```text
2026-04-08T00:03:00Z
```

Separation after lunar SOI exit:

```text
23958.078 s
399.301 min
6.655 h
```

RTC1 therefore occurs during:

```text
TRANS_EARTH_RETURN
```

several hours after leaving the adopted lunar SOI.

---

# Flight Day 9 Return-Link Event

Approximate return-link LOS anchor:

```text
~2026-04-10T00:53:00Z
```

Approximate MET:

```text
~08:02:17:48
```

Mission phase:

```text
TRANS_EARTH_RETURN
```

Precision:

```text
APPROXIMATE
```

RTC2:

```text
2026-04-10T02:53:00Z
```

Separation:

```text
7200 s
120 min
2.000 h
```

The approximate anchor remains explicitly derived from NASA's:

```text
about two hours before RTC2
```

language.

It is not an exact outage time.

---

# Flight Day 6 Lunar SOI Containment

All ten synchronized Flight Day 6 flyby events fall inside MissionLab's derived lunar SOI interval.

Validated:

```text
Reported Earthset:
TRUE

Geocentric occultation ingress:
TRUE

DSS-43 topocentric ingress:
TRUE

Reported RF blackout:
TRUE

Pericynthion:
TRUE

Maximum Earth-center distance:
TRUE

Geocentric occultation egress:
TRUE

DSS-43 topocentric egress:
TRUE

Reported Earthrise:
TRUE

Planned public DSN AOS:
TRUE
```

This creates a coherent lunar-flyby operational window.

---

# Permanent Correlation Product

Generated:

```text
data/processed/communications/mission_clock_communications_correlation.csv
```

Rows:

```text
17
```

Each synchronized event includes:

```text
event ID
name
UTC
MET
mission phase
event kind
domain
source layer
provenance
precision
approximate flag
source ID
interpretation notes
```

The file remains reproducibly generated and ignored from Git.

---

# Permanent Summary

Generated:

```text
data/processed/communications/mission_clock_communications_correlation_summary.json
```

Product identifier:

```text
phase2h2_mission_clock_communications_correlation
```

The summary preserves:

```text
input product identities
mission anchors
mission-phase counts
domain counts
approximate-event identities
Flight Day 6 ordered sequence
correlation metrics
SOI containment
untimed operational relations
interpretation guardrails
output paths
```

The file remains ignored from Git.

---

# Mission-Clock Figure

Created:

```text
docs/assets/communications/phase2h2_mission_clock_correlation.svg
```

The figure displays synchronized events across:

```text
Optical
Burns
Geometry
RF communications
```

Marker semantics:

```text
circle:
reported or derived event

square:
planned event

x:
approximate computational anchor
```

Sequence-only events are not assigned an artificial horizontal-axis location.

---

# Flight Day 6 Correlation Figure

Created:

```text
docs/assets/communications/phase2h2_flyby_correlation.svg
```

The figure focuses specifically on the lunar-flyby communications interval.

It includes:

```text
geocentric occultation interval
DSS-43 topocentric occultation interval
reported Earthset
reported RF blackout
pericynthion
maximum Earth distance
reported Earthrise
planned DSN AOS
```

The purpose is to show visually that:

```text
celestial geometry
ground-station geometry
mission trajectory
and
operational communications reporting
```

are closely related but distinct layers.

---

# Correlation Metrics

Phase 2H.2 permanently records:

```text
OTC -> lunar SOI entry:
5707.532 s
95.126 min

SOI entry -> reported Earthset:
64972.468 s
1082.874 min

Geocentric ingress -> reported blackout:
136.348 s
2.272 min

DSS-43 ingress -> reported blackout:
69.659 s
1.161 min

Reported blackout -> pericynthion:
1006.178 s
16.770 min

Pericynthion -> maximum Earth distance:
125.489 s
2.091 min

Geocentric egress -> reported Earthrise:
144.511 s
2.409 min

DSS-43 egress -> reported Earthrise:
51.468 s
0.858 min

Pericynthion -> reported Earthrise:
1393.822 s
23.230 min

Planned AOS -> lunar SOI exit:
64721.922 s
1078.699 min

Lunar SOI exit -> RTC1:
23958.078 s
399.301 min

Approximate return-link LOS -> RTC2:
7200.000 s
120.000 min
```

---

# Cross-Phase Architecture

Phase 2H.2 creates the following analysis chain:

```text
PHASE 1
trajectory
SOI
burns
pericynthion
maximum Earth distance

        ↓

PHASE 2G.1
Earth-center occultation

        ↓

PHASE 2G.2
ground-station topocentric occultation

        ↓

PHASE 2H.1
operational communications evidence

        ↓

PHASE 2H.2
synchronized mission-operations correlation
```

No earlier product is overwritten.

The correlation product references and preserves each source layer.

---

# Precision Preservation

Phase 2H.2 does not change source precision merely because an event is placed on the common mission clock.

For example:

```text
NASA minute-level Earthset
```

remains:

```text
MINUTE_LEVEL
```

even though MissionLab can calculate a MET representation.

Likewise:

```text
approximate O2O anchor
```

remains:

```text
APPROXIMATE
```

and:

```text
live DSN reacquisition
```

remains:

```text
SEQUENCE_ONLY
```

---

# Interpretation Guardrails

## Guardrail 1

```text
Correlation
!=
new source evidence
```

Phase 2H.2 relates existing products but does not manufacture additional NASA facts.

---

## Guardrail 2

```text
MissionLab-derived geometry
!=
NASA operational timestamp
```

Derived occultation contacts retain their MissionLab provenance.

---

## Guardrail 3

```text
MET conversion
!=
increased source precision
```

Converting a minute-level UTC event into MET does not make it second-level telemetry.

---

## Guardrail 4

```text
Approximate anchor
!=
exact timestamp
```

This applies to:

```text
O2O 100 GB milestone
unexpected Flight Day 9 return-link LOS
```

---

## Guardrail 5

```text
SEQUENCE_ONLY
!=
timed event
```

The live DSN reacquisition remains untimed.

---

## Guardrail 6

```text
DSS-43 timing agreement
!=
operational station assignment
```

DSS-43 remains a representative topocentric reference.

---

## Guardrail 7

```text
RF communications
!=
O2O optical communications
```

Both can share the mission clock without being treated as the same communications channel.

---

# Independent Validation

The validator independently confirmed:

```text
17 synchronized events
```

Mission phase distribution:

```text
OUTBOUND_TRANSIT:
2

LUNAR_APPROACH:
6

LUNAR_DEPARTURE:
6

TRANS_EARTH_RETURN:
3
```

Flight Day 6 sequence:

```text
PASS
```

Independent correlation values:

```text
PASS
```

All ten Flight Day 6 events inside lunar SOI:

```text
TRUE
```

Approximate O2O anchor:

```text
PASS
```

Approximate Flight Day 9 return-link anchor:

```text
PASS
```

Live DSN reacquisition precision:

```text
SEQUENCE_ONLY
```

Live DSN reacquisition UTC:

```text
NONE
```

Live DSN reacquisition MET:

```text
NONE
```

Generated correlation CSV:

```text
17 rows
PASS
```

Summary:

```text
PASS
```

Mission-clock figure:

```text
PASS
```

Flyby correlation figure:

```text
PASS
```

Final independent validation:

```text
PASS
```

---

# Engineering Significance

Phase 2H.2 turns several individual analyses into a coherent mission-operations reconstruction.

Before this phase, MissionLab had independently reconstructed:

```text
where Orion was
when Orion entered the lunar SOI
when closest lunar approach occurred
when the Moon geometrically blocked Earth
how DSN ground location changed that geometry
and what NASA publicly reported about communications
```

Phase 2H.2 now places all of those facts on one clock.

The resulting Flight Day 6 sequence shows:

```text
Earth disappears from Orion's view
        ↓
geocentric LOS crosses lunar limb
        ↓
Canberra reference LOS crosses lunar limb
        ↓
NASA reports RF blackout
        ↓
Orion reaches pericynthion
        ↓
Orion reaches maximum Earth distance
        ↓
geometric LOS begins clearing
        ↓
Canberra reference LOS clears
        ↓
NASA reports Earthrise
        ↓
planned DSN AOS
```

This is much closer to a flight-control style representation than a collection of isolated plots.

It explicitly connects:

```text
trajectory
geometry
network visibility
operations
mission phase
and event provenance
```

while retaining the uncertainty and source boundaries of each layer.

---

# Phase 2H.2 Status

Mission-clock synchronization:

```text
PASS
```

Phase 1 integration:

```text
PASS
```

Phase 2G.1 integration:

```text
PASS
```

Phase 2G.2 integration:

```text
PASS
```

Phase 2H.1 integration:

```text
PASS
```

Flight Day 6 ordering:

```text
PASS
```

Lunar SOI containment:

```text
PASS
```

Correlation metrics:

```text
PASS
```

Approximate-event preservation:

```text
PASS
```

Sequence-only event preservation:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2H.2 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2H.3 — O2O Optical Communications Reconstruction

## Goal

Phase 2H.3 reconstructs the Artemis II Orion Artemis II Optical Communications System, or O2O, as a communications system distinct from the mission's primary RF communications architecture.

The analysis separates four evidence layers:

```text
PREMISSION ARCHITECTURE
        ↓
GROUND / OPERATIONS SEGMENT
        ↓
LIVE MISSION REPORTING
        ↓
POSTFLIGHT PERFORMANCE
```

The primary engineering rule is:

```text
O2O optical communications
!=
primary Artemis II RF communications
```

NASA's Near Space Network and Deep Space Network remained the mission's primary communications support.

O2O operated as a parallel optical communications demonstration.

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_o2o_reference.json
```

Dataset identifier:

```text
phase2h3_artemis_ii_o2o_reference
```

Provenance:

```text
NASA_AND_NASA_NTRS_REPORTED_WITH_MISSIONLAB_DERIVED_METRICS
```

The reference dataset preserves:

```text
mission role
optical architecture
terminal architecture
ground segment
mission-control operations segment
live mission events
postflight results
source evidence layers
interpretation guardrails
```

---

# O2O Mission Role

System:

```text
Orion Artemis II Optical Communications System
```

Short name:

```text
O2O
```

Classification:

```text
OPTICAL_COMMUNICATIONS_DEMONSTRATION
```

Primary mission communications:

```text
Near Space Network
Deep Space Network
```

Primary RF replacement:

```text
FALSE
```

This distinction is permanent.

O2O must not be described as replacing NASA's primary RF communications architecture.

---

# Optical Architecture

Nominal wavelength:

```text
1550 nm
```

Optical band:

```text
OPTICAL_C_BAND
```

Maximum architecture return/downlink rate:

```text
260 Mbps
```

Maximum architecture forward/uplink rate:

```text
20 Mbps
```

Derived maximum-return to maximum-forward ratio:

```text
260 / 20
= 13.000x
```

This ratio compares architecture maxima only.

It does not imply:

```text
13x average mission throughput
```

or:

```text
13x operational efficiency
```

---

# O2O Flight Terminal

The permanent terminal component set is:

```text
Optical Module
Modem
Controller
```

## Optical Module

Telescope aperture:

```text
4 inches
```

Gimbal count:

```text
2
```

Functions include:

```text
optical transmission
optical reception
pointing toward optical ground terminals
```

## Modem

MissionLab records the modem as the component responsible for converting mission information to and from optical communications signals.

## Controller

MissionLab records the controller as the interface between:

```text
Orion flight avionics
and
the O2O optical terminal
```

including control and pointing functions.

---

# Optical Line of Sight

The reference architecture records:

```text
line_of_sight_required = TRUE
```

Optical communications therefore have different environmental and geometric constraints from RF communications.

Phase 2H.3 does not model:

```text
cloud attenuation
atmospheric turbulence
optical scintillation
received optical power
pointing error
optical link margin
weather scheduling
pass scheduling
```

Those remain outside the current reconstruction.

---

# Main Optical Ground Segment

Two primary U.S. optical ground sites are preserved.

## White Sands Complex

Location:

```text
Las Cruces, New Mexico, USA
```

Role:

```text
PRIMARY_OPTICAL_GROUND_STATION
```

Premission status:

```text
PLANNED
```

Mission status:

```text
MISSION_USED
```

---

## Table Mountain Facility

Organization:

```text
NASA Jet Propulsion Laboratory
```

Location:

```text
Southern California, USA
```

Role:

```text
PRIMARY_OPTICAL_GROUND_STATION
```

The permanent reference includes a cross-source mapping note.

Premission NASA material explicitly identifies:

```text
Table Mountain Facility
```

while the postflight NASA reporting refers more generally to:

```text
NASA JPL in Southern California
```

MissionLab preserves that relationship without pretending the postflight article independently re-identifies the exact facility name.

---

# Additional Demonstration Ground Site

Additional site:

```text
Australian National University
Quantum Optical Ground Station
```

Short name:

```text
QOGS
```

Location:

```text
Mount Stromlo
Canberra, Australia
```

Role:

```text
ADDITIONAL_OPTICAL_DEMONSTRATION_SITE
```

Mission status:

```text
MISSION_DEMONSTRATED
```

The site demonstrated that additional optical infrastructure beyond the two main U.S. ground sites could participate successfully in Artemis II O2O operations.

---

# Environmental Ground-Site Context

Optical communications are sensitive to atmospheric obscuration.

The permanent reference records:

```text
clear_sky_dependency = TRUE
```

and notes NASA's use of favorable ground locations for optical operations.

Phase 2H.3 does not convert this contextual fact into:

```text
a weather model
cloud probability model
atmospheric attenuation model
```

---

# Mission-Control Operations Segment

The reconstructed O2O operations segment is centered at:

```text
Johnson Space Center
Houston, Texas, USA
```

Permanent operations elements:

```text
MCC
Artemis II Mission Control Center

LSTC
Lasercomm Space Terminal Console

LPAC
Lasercomm Link Planning and Analysis Center
```

This is an especially important mission-operations connection.

O2O was not merely a spacecraft hardware experiment.

Its link planning and execution were integrated with the human-spaceflight mission-control environment.

---

# Existing Phase 2H.1 Cross-Checks

Phase 2H.3 reuses two operational events already established during Phase 2H.1.

No duplicate timestamps are invented.

---

# Flight Day 3 Optical Ground Links

Catalog event:

```text
o2o_two_us_ground_station_links
```

Precision:

```text
DATE_LEVEL
```

State:

```text
OBSERVED_REPORTED
```

NASA reported successful O2O connections with two U.S.-based ground stations.

Reported content included:

```text
high-definition video
mission data
```

No unsupported time of day is assigned.

---

# Flight Day 4 100 GB Milestone

Catalog event:

```text
o2o_100_gb_downlink_milestone
```

Precision:

```text
APPROXIMATE
```

NASA timing language:

```text
just after 12 p.m. EDT
```

MissionLab computational anchor:

```text
~2026-04-04T16:00:00Z
```

Anchor exact:

```text
FALSE
```

The event is modeled as:

```text
greater than 100 GB
```

rather than:

```text
exactly 100 GB
```

because the public report states that O2O had surpassed the threshold.

---

# Postflight Mission Total

NASA-reported mission data exchange:

```text
484 GB
```

Permanent semantics:

```text
DATA_EXCHANGED_BETWEEN_ORION_AND_EARTH
```

Downlink-only:

```text
FALSE
```

Single session:

```text
FALSE
```

Therefore MissionLab must not describe the result as:

```text
484 GB downlinked
```

unless a future source explicitly supports that statement.

The supported interpretation is:

```text
484 GB exchanged between Orion and Earth
```

across the mission.

---

# Demonstrated Downlink Performance

NASA reported:

```text
multiple 260 Mbps downlinks
```

Maximum demonstrated downlink:

```text
260 Mbps
```

This matches the architecture maximum return/downlink rate.

That establishes:

```text
architecture maximum:
260 Mbps

mission demonstrated:
260 Mbps
```

It does not establish:

```text
mission-average throughput:
260 Mbps
```

---

# 26 GB Main-Ground-Station Transfer

NASA reported a transfer involving the two main U.S. optical ground stations:

```text
26 GB
```

in:

```text
under one hour
```

Exact duration:

```text
UNKNOWN
```

Individual ground-station assignment:

```text
NONE
```

MissionLab therefore does not attribute the complete 26 GB result exclusively to:

```text
White Sands
```

or:

```text
Table Mountain
```

---

# Derived 26 GB Average-Rate Lower Bound

MissionLab derives a lower bound using:

```text
26 GB
```

and the duration upper bound:

```text
1 hour
```

Using decimal gigabytes:

```text
26 GB
= 26 × 8 × 1000 megabits
= 208,000 megabits
```

One hour:

```text
3600 seconds
```

Therefore:

```text
208000 / 3600
= 57.777777... Mbps
```

Because NASA reported a duration of:

```text
less than one hour
```

the average transfer rate must have been:

```text
>57.778 Mbps
```

This is a:

```text
MISSIONLAB_DERIVED LOWER BOUND
```

It is not:

```text
NASA-reported throughput
```

and not:

```text
the actual average transfer rate
```

because the exact transfer duration is unknown.

---

# Architecture Maximum vs Derived Transfer Lower Bound

Architecture maximum return/downlink:

```text
260 Mbps
```

Derived 26 GB transfer average-rate lower bound:

```text
>57.778 Mbps
```

These values answer different questions.

The first is:

```text
maximum architecture capability
```

The second is:

```text
minimum possible average rate
consistent with the reported
26 GB in under one hour
```

They must not be directly interpreted as observed instantaneous-rate measurements from the same transfer.

---

# Mount Stromlo Result

NASA reported more than:

```text
15.5 hours
```

of dual-stream video through Mount Stromlo.

Permanent relation:

```text
GREATER_THAN
```

Derived duration lower bound:

```text
15.5 × 3600
= 55,800 seconds
```

Therefore:

```text
>55,800 seconds
```

of reported mission aggregate dual-stream video support.

---

# Mount Stromlo Continuity Guardrail

Continuous single pass:

```text
FALSE
```

The public result does not establish one uninterrupted:

```text
15.5-hour optical pass
```

Therefore MissionLab represents the result as an aggregate duration rather than a continuous contact window.

---

# Mount Stromlo Rate Demonstration

Maximum demonstrated downlink:

```text
260 Mbps
```

This establishes that Mount Stromlo successfully demonstrated the highest O2O downlink rate reported for the system.

It does not establish:

```text
260 Mbps continuously
```

for the full reported video duration.

---

# Lunar-Flyby Optical Content

Postflight NASA reporting supports optical downlink of imagery associated with:

```text
Earthset
Earthrise
other mission imagery
```

The permanent dataset therefore records:

```text
earthset_images_downlinked = TRUE
earthrise_images_downlinked = TRUE
other_mission_images_downlinked = TRUE
```

This is especially relevant to the Phase 2G and 2H mission reconstruction because Earthset and Earthrise are already represented on the common mission clock.

Phase 2H.3 does not infer an exact optical-transmission timestamp for those images.

---

# Forward Optical Link

Postflight evidence also establishes:

```text
forward_data_to_orion_demonstrated = TRUE
```

This is operationally distinct from the optical return/downlink.

The architecture maximum forward rate remains:

```text
20 Mbps
```

while the return maximum remains:

```text
260 Mbps
```

---

# Evidence Layers

Phase 2H.3 explicitly separates three source layers.

## PREMISSION_ARCHITECTURE

Examples:

```text
terminal components
1550 nm optical architecture
maximum link rates
White Sands
Table Mountain
MCC / LSTC / LPAC
```

These describe system design and planned architecture.

---

## LIVE_MISSION_REPORTED

Examples:

```text
Flight Day 3 links to two U.S. stations
Flight Day 4 >100 GB milestone
```

These are reports published while Artemis II was operating.

---

## POSTFLIGHT_REPORTED

Examples:

```text
484 GB mission exchange
multiple 260 Mbps downlinks
26 GB in under one hour
Mount Stromlo >15.5 h video
Mount Stromlo 260 Mbps
Earthset imagery
Earthrise imagery
forward-link demonstration
```

These describe mission results after execution.

---

# Permanent Analyzer

Created:

```text
scripts/analysis/analyze_o2o_optical_communications.py
```

The analyzer validates and reconstructs:

```text
mission role
optical architecture
terminal component identity
terminal hardware values
ground-site identity
operations-segment identity
Phase 2H.1 event consistency
mission aggregate performance
rate architecture
Mount Stromlo performance
optical-versus-RF boundary
derived quantitative metrics
```

---

# Permanent Metrics Product

Generated:

```text
data/processed/communications/o2o_performance_metrics.csv
```

Rows:

```text
9
```

Metrics:

```text
architecture maximum forward rate
architecture maximum return rate
Flight Day 4 downlink threshold
mission total data exchange
mission maximum demonstrated downlink
main-ground-station transfer volume
derived average-rate lower bound
Mount Stromlo video-duration lower bound
Mount Stromlo maximum demonstrated rate
```

This processed product remains ignored from Git.

---

# Permanent Summary Product

Generated:

```text
data/processed/communications/o2o_optical_communications_summary.json
```

Product identifier:

```text
phase2h3_o2o_optical_communications_analysis
```

The summary preserves:

```text
mission role
architecture
ground segment
operations segment
live-event cross-checks
postflight results
derived metrics
source evidence-layer counts
guardrails
output paths
```

This processed product remains ignored from Git.

---

# Architecture Figure

Created:

```text
docs/assets/communications/phase2h3_o2o_architecture.svg
```

The figure represents:

```text
Orion O2O terminal
        ↓
White Sands
Table Mountain / JPL
Mount Stromlo QOGS
        ↓
Johnson Space Center
MCC / LSTC / LPAC
```

It also includes the permanent architecture boundary:

```text
O2O = parallel optical demonstration

NSN + DSN = primary RF communications
```

---

# Link-Rate Figure

Created:

```text
docs/assets/communications/phase2h3_o2o_link_rates.svg
```

The figure compares:

```text
20 Mbps
architecture maximum forward

260 Mbps
architecture maximum return

260 Mbps
mission maximum demonstrated downlink

>57.778 Mbps
derived 26 GB transfer average-rate lower bound
```

The figure explicitly identifies the lower-bound metric as derived rather than NASA-reported instantaneous throughput.

---

# Independent Validator

Created:

```text
scripts/validation/validate_o2o_optical_communications.py
```

The independent validator confirms:

```text
reference dataset identity
analysis product identity
mission role
primary RF boundary
1550 nm wavelength
260 Mbps return maximum
20 Mbps forward maximum
terminal component set
4-inch telescope
two gimbals
two main U.S. optical sites
Mount Stromlo identity
MCC / LSTC / LPAC identity
Flight Day 3 precision
Flight Day 4 precision
100 GB approximate anchor
484 GB semantics
260 Mbps mission demonstration
26 GB transfer semantics
derived >57.778 Mbps bound
Mount Stromlo duration semantics
Mount Stromlo continuity guardrail
Mount Stromlo 260 Mbps result
Earthset imagery result
Earthrise imagery result
forward-link result
9-row metrics CSV
summary integrity
architecture SVG
link-rate SVG
guardrail preservation
```

---

# Independent Validation Result

Mission role:

```text
optical demonstration:
TRUE

primary RF replacement:
FALSE
```

Architecture:

```text
wavelength:
1550 nm

max return/downlink:
260 Mbps

max forward/uplink:
20 Mbps

max return / max forward:
13.000x

terminal components:
3

telescope:
4 in

gimbals:
2
```

Ground segment:

```text
main optical sites:
2

additional demonstrated sites:
1

White Sands:
PASS

Table Mountain / JPL:
PASS

Mount Stromlo QOGS:
PASS
```

Mission-control operations:

```text
MCC:
PASS

LSTC:
PASS

LPAC:
PASS
```

Live mission precision:

```text
Flight Day 3:
DATE_LEVEL

Flight Day 4 100 GB:
APPROXIMATE

100 GB anchor exact:
FALSE
```

Postflight:

```text
mission exchange:
484 GB

marked downlink-only:
FALSE

multiple 260 Mbps downlinks:
TRUE

26 GB transfer:
<1 h

derived average-rate lower bound:
>57.778 Mbps

Mount Stromlo video:
>15.5 h

Mount Stromlo continuous-pass claim:
FALSE

Mount Stromlo 260 Mbps:
TRUE

Earthset imagery:
TRUE

Earthrise imagery:
TRUE

forward data to Orion:
TRUE
```

Products:

```text
performance metrics rows:
9

summary:
PASS

architecture figure:
PASS

link-rate figure:
PASS
```

Final validation:

```text
PASS
```

---

# Interpretation Guardrails

## Guardrail 1

```text
O2O
!=
primary Artemis II communications architecture
```

NSN and DSN remain the primary RF communications networks.

---

## Guardrail 2

```text
484 GB exchanged
!=
484 GB downlinked
```

The public source uses bidirectional exchange language.

---

## Guardrail 3

```text
484 GB mission aggregate
!=
one continuous optical session
```

---

## Guardrail 4

```text
260 Mbps demonstrated
!=
260 Mbps mission average
```

---

## Guardrail 5

```text
>100 GB milestone
!=
exactly 100 GB
```

---

## Guardrail 6

```text
~16:00 UTC anchor
!=
exact milestone timestamp
```

---

## Guardrail 7

```text
26 GB in <1 hour
!=
known transfer duration
```

---

## Guardrail 8

```text
>57.778 Mbps
=
derived lower bound
```

not an observed NASA throughput measurement.

---

## Guardrail 9

```text
>15.5 h Mount Stromlo video
!=
one continuous 15.5 h pass
```

---

## Guardrail 10

```text
premission capability
!=
mission demonstration
```

unless postflight evidence explicitly confirms the capability was demonstrated.

---

## Guardrail 11

```text
optical ground-site participation
!=
RF DSN antenna assignment
```

---

## Guardrail 12

Phase 2H.3 does not infer:

```text
optical link budget
received optical power
weather losses
cloud attenuation
pointing losses
signal-to-noise ratio
pass schedule
exact pass duration
exact imagery transmission times
mission-average optical throughput
```

---

# Engineering Significance

Phase 2H.3 extends the communications reconstruction beyond conventional RF communications.

MissionLab now represents three distinct communications perspectives:

```text
RF network architecture
        +
RF lunar occultation geometry
        +
high-rate optical communications demonstration
```

The O2O reconstruction shows that Artemis II was simultaneously a crewed lunar mission and a deep-space communications technology demonstration.

The architecture links:

```text
Orion spacecraft hardware
        ↓
laser communications
        ↓
distributed optical ground stations
        ↓
Johnson Space Center mission operations
```

The postflight results demonstrate that the architecture operated at substantial scale:

```text
484 GB exchanged
260 Mbps demonstrated
international optical ground support
bidirectional communication
lunar-flyby imagery
```

while the provenance framework prevents those results from being overstated.

---

# Phase 2H.3 Status

Reference dataset:

```text
PASS
```

Optical architecture:

```text
PASS
```

Ground segment:

```text
PASS
```

Mission-control operations segment:

```text
PASS
```

Phase 2H.1 cross-check:

```text
PASS
```

Postflight performance reconstruction:

```text
PASS
```

Derived transfer-rate lower bound:

```text
PASS
```

Optical-versus-RF boundary:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2H.3 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2H.4 — Communications Operational Threads

## Goal

Phase 2H.4 converts the Artemis II communications reconstruction into evidence-backed operational threads.

The purpose is to distinguish between:

```text
planned readiness activity
expected communications constraints
unexpected communications anomalies
```

while preserving the timing and provenance rules established in Phase 2H.1.

The phase does not attempt to reconstruct private NASA console traffic or undocumented Flight Director decision logic.

The permanent operational rule is:

```text
public operational sequence
!=
complete mission-control decision record
```

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_communications_operational_threads.json
```

Dataset identifier:

```text
phase2h4_artemis_ii_communications_operational_threads
```

Provenance:

```text
NASA_REPORTED_WITH_MISSIONLAB_DERIVED_CORRELATIONS
```

The reference dataset contains:

```text
source-backed operational threads
thread classifications
expected-versus-unexpected state
event identities
precision rules
operational sequence
decision-evidence boundaries
interpretation guardrails
```

---

# Thread Model

Phase 2H.4 defines three operational threads.

```text
1.
Emergency communications readiness

2.
Lunar occultation blackout and reacquisition

3.
Flight Day 9 return-link loss and recovery
```

The threads are not interchangeable.

They represent three fundamentally different operational situations.

---

# Thread 1 — Emergency Communications Readiness

Thread ID:

```text
emergency_communications_readiness
```

Classification:

```text
CONTINGENCY_READINESS
```

Expectedness:

```text
PLANNED_TEST_ACTIVITY
```

Anomaly:

```text
FALSE
```

NASA reported that Orion's emergency communications system was tested in deep space.

Associated event:

```text
dsn_emergency_communications_test
```

Date:

```text
2026-04-03
```

Precision:

```text
DATE_LEVEL
```

State:

```text
OBSERVED_REPORTED
```

Exact test time:

```text
NONE
```

MissionLab does not create a time-of-day value because the public evidence does not support one.

---

# Readiness-Test Interpretation

The emergency communications test is not classified as:

```text
an anomaly
```

or:

```text
communications failure
```

It is represented as contingency readiness activity.

This distinction matters operationally because a mission-control system should separate:

```text
testing contingency capability
```

from:

```text
responding to an actual contingency
```

---

# Thread 2 — Lunar Occultation Blackout and Reacquisition

Thread ID:

```text
lunar_occultation_blackout_and_reacquisition
```

Classification:

```text
EXPECTED_OPERATIONAL_CONSTRAINT
```

Expectedness:

```text
EXPECTED
```

Anomaly:

```text
FALSE
```

This is a critical Phase 2H.4 distinction.

The lunar-flyby loss of communications was expected.

It must not be represented as a communications failure.

---

# Planned Lunar Blackout

Planned blackout:

```text
2026-04-06T22:44:00Z
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
PLANNED
```

---

# Reported Lunar Blackout

Reported blackout:

```text
2026-04-06T22:44:00Z
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
OBSERVED_REPORTED
```

Reported minus planned blackout:

```text
0 seconds
```

At the precision available in NASA's public reporting:

```text
reported blackout minute
=
planned blackout minute
```

This does not imply second-level agreement.

Both remain:

```text
MINUTE_LEVEL
```

---

# Planned Earthrise

Planned Earthrise:

```text
2026-04-06T23:25:00Z
```

Precision:

```text
MINUTE_LEVEL
```

---

# Reported Earthrise

Reported Earthrise:

```text
2026-04-06T23:24:00Z
```

Precision:

```text
MINUTE_LEVEL
```

Reported minus planned Earthrise:

```text
-60 seconds
```

Therefore NASA reported Earthrise one minute earlier than the previously published planned value.

This is a comparison between minute-level public timestamps.

It is not a second-level navigation measurement.

---

# Planned DSN Reacquisition

Planned DSN reacquisition:

```text
2026-04-06T23:25:00Z
```

Precision:

```text
MINUTE_LEVEL
```

State:

```text
PLANNED
```

---

# Live DSN Reacquisition

Live NASA reporting states that DSN reacquisition occurred:

```text
MOMENTS_AFTER_REPORTED_EARTHRISE
```

Precision:

```text
SEQUENCE_ONLY
```

Exact UTC:

```text
NONE
```

Approximate UTC anchor:

```text
NONE
```

MissionLab does not replace the live sequence-only report with:

```text
23:25 UTC
```

simply because 23:25 UTC had been the planned reacquisition time.

That would incorrectly convert a planned event into an observed event.

---

# Planned Blackout Window

Planned blackout:

```text
22:44 UTC
```

Planned AOS:

```text
23:25 UTC
```

Difference:

```text
2460 seconds
41.0 minutes
```

---

# Reported Blackout to Reported Earthrise

Reported blackout:

```text
22:44 UTC
```

Reported Earthrise:

```text
23:24 UTC
```

Difference:

```text
2400 seconds
40.0 minutes
```

This is a geometric-context interval.

The actual live DSN reacquisition remains untimed because the public source only establishes sequence.

---

# Flight Day 6 Operational Sequence

The evidence-backed sequence is:

```text
planned blackout
        ↓
reported blackout
        ↓
reported Earthrise
        ↓
live DSN reacquisition
```

with the parallel planned recovery context:

```text
planned Earthrise
planned DSN AOS
```

The sequence demonstrates the distinction between:

```text
planned operations
reported geometric context
reported communications state
```

---

# Flight Day 6 Classification

Permanent classification:

```text
EXPECTED_OPERATIONAL_CONSTRAINT
```

Anomaly:

```text
FALSE
```

This remains true even though communications were temporarily unavailable.

The reason is that the loss of communication was expected as part of lunar occultation.

---

# Thread 3 — Flight Day 9 Return-Link Loss and Recovery

Thread ID:

```text
flight_day_9_return_link_loss_and_recovery
```

Classification:

```text
UNEXPECTED_COMMUNICATIONS_ANOMALY
```

Expectedness:

```text
UNEXPECTED
```

Anomaly:

```text
TRUE
```

This thread is operationally different from the lunar blackout.

---

# Flight Day 9 Anomaly Detection

NASA reported:

```text
unexpected return-link loss of signal
```

Context:

```text
DURING_DATA_RATE_CHANGE
```

Event state:

```text
REPORTED
```

Precision:

```text
APPROXIMATE
```

Approximate computational anchor:

```text
~2026-04-10T00:53:00Z
```

Anchor exact:

```text
FALSE
```

The anchor is constructed from:

```text
RTC2 timestamp
minus
approximately two hours
```

It is not an observed loss-of-signal timestamp.

---

# RTC2 Anchor

RTC2:

```text
2026-04-10T02:53:00Z
```

Approximate loss anchor:

```text
~2026-04-10T00:53:00Z
```

Difference:

```text
~7200 seconds
~2.000 hours
```

The approximation comes from NASA's public phrase:

```text
about two hours before the burn
```

rather than from telemetry.

---

# Data-Rate-Change Context

NASA reported that the return-link loss occurred:

```text
during a data-rate change
```

MissionLab permanently represents this as:

```text
context = DURING_DATA_RATE_CHANGE
```

Causal relationship:

```text
NOT_ESTABLISHED
```

This is an important engineering distinction.

The evidence supports:

```text
event occurred during data-rate change
```

but does not support:

```text
data-rate change caused the event
```

---

# Supported Affected Direction

Supported direction:

```text
RETURN_LINK
```

The public reporting supports impact to information traveling:

```text
Orion
→
ground
```

including:

```text
communications
telemetry
```

MissionLab does not generalize the event into an unsupported total communications failure.

---

# Two-Way-Outage Guardrail

Complete simultaneous two-way outage established:

```text
FALSE
```

The anomaly was described as a:

```text
return-link loss
```

Therefore the initial anomaly is not automatically interpreted as:

```text
both uplink and downlink completely unavailable
```

The later statement that two-way communications were reestablished does not change the precision of the original anomaly description.

---

# Recovery

NASA subsequently reported:

```text
two-way communications reestablished
```

Associated event:

```text
two_way_communications_reestablished
```

Precision:

```text
SEQUENCE_ONLY
```

Ordering:

```text
SHORTLY_AFTER_UNEXPECTED_RETURN_LINK_LOSS_BEFORE_RTC2
```

Exact recovery UTC:

```text
NONE
```

Approximate recovery UTC:

```text
NONE
```

Anomaly duration:

```text
UNKNOWN
```

MissionLab does not turn:

```text
shortly afterward
```

into a numeric duration.

---

# Operations Resumed

NASA reported that flight controllers resumed preparation for RTC2 with the crew after communications were restored.

Permanent operational step:

```text
burn_preparation_resumed
```

Precision:

```text
SEQUENCE_ONLY
```

Timestamp:

```text
NONE
```

Ordering:

```text
AFTER_COMMUNICATIONS_REESTABLISHED_BEFORE_RTC2
```

This allows MissionLab to represent the operational consequence without inventing a console timestamp.

---

# Flight Day 9 Operational Sequence

The evidence-backed sequence is:

```text
unexpected return-link loss
        ↓
two-way communications reestablished
        ↓
burn preparation resumed
        ↓
RTC2
```

Only the final RTC2 event has a source-reported timestamp precise enough to use as a timed burn anchor.

The anomaly and recovery stages retain their weaker public precision.

---

# Root Cause

Public root cause available:

```text
FALSE
```

MissionLab does not identify:

```text
hardware failure
software failure
ground-system failure
spacecraft subsystem failure
modem failure
antenna failure
network failure
configuration error
operator error
```

because the available public evidence does not establish any of those explanations.

---

# Failed Subsystem

Failed subsystem identified:

```text
FALSE
```

The reconstruction intentionally stops at the supported event description.

---

# Anomaly Duration

Duration known:

```text
FALSE
```

The public evidence establishes sequence:

```text
loss
↓
recovery
```

but does not provide both endpoints with defensible timestamps.

Therefore no anomaly-duration calculation is performed.

---

# Decision-Evidence Boundary

Phase 2H.4 explicitly records the difference between information available publicly and information that would normally exist inside mission operations.

Public event sequence:

```text
TRUE
```

Public planned-versus-reported timing:

```text
TRUE
```

Public full console transcript:

```text
FALSE
```

Public Flight Director rationale tree:

```text
FALSE
```

Public fault-isolation sequence:

```text
FALSE
```

Public root-cause analysis:

```text
FALSE
```

Public failed-subsystem identification:

```text
FALSE
```

---

# Mission-Control Reconstruction Boundary

MissionLab can reconstruct:

```text
what was planned
what was publicly reported
event order
approximate relationship to major mission events
whether an event was expected
whether an event was anomalous
whether normal operations resumed
```

MissionLab cannot reconstruct from the current public evidence:

```text
console calls
Flight Director polling
internal troubleshooting hypotheses
fault isolation
private telemetry interpretation
command history
decision rationale
GO / NO-GO logic
root cause
```

Those boundaries are features of the reconstruction rather than missing rigor.

---

# Permanent Analyzer

Created:

```text
scripts/analysis/analyze_communications_operational_threads.py
```

The analyzer validates:

```text
three operational-thread identities
classification semantics
expected-versus-unexpected state
anomaly flags
source precision
planned-versus-reported timing
lunar blackout window
Flight Day 9 approximate anchor
recovery sequence
burn-preparation resumption
RTC2 relationship
decision-evidence boundaries
non-causation guardrails
```

---

# Permanent Processed Thread Product

Generated:

```text
data/processed/communications/communications_operational_threads.csv
```

Rows:

```text
3
```

Each row preserves:

```text
thread ID
thread name
classification
expectedness
anomaly flag
precision pattern
primary source
public decision-rationale availability
public console-log availability
```

This file remains reproducibly generated and ignored from Git.

---

# Permanent Summary Product

Generated:

```text
data/processed/communications/communications_operational_threads_summary.json
```

Product identifier:

```text
phase2h4_communications_operational_threads_analysis
```

The summary contains:

```text
thread counts
anomaly counts
classification counts
derived timing metrics
Flight Day 6 operational context
Flight Day 9 anomaly context
decision-evidence boundary
guardrails
output paths
```

This file remains ignored from Git.

---

# Operational Threads Figure

Created:

```text
docs/assets/communications/phase2h4_communications_operational_threads.svg
```

The figure visualizes the three operational threads separately.

Thread 1:

```text
Emergency communications test
```

Thread 2:

```text
planned blackout
→
reported blackout
→
reported Earthrise
→
planned AOS
→
sequence-only live reacquisition
```

Thread 3:

```text
approximate return-link loss
→
sequence-only recovery
→
sequence-only burn preparation
→
RTC2
```

The figure explicitly states that the sequence-only events are not assigned invented times.

---

# Derived Operational Metrics

Permanent metrics:

```text
blackout reported minus planned:
0 s

Earthrise reported minus planned:
-60 s

planned blackout to planned AOS:
2460 s
41.0 min

reported blackout to reported Earthrise:
2400 s
40.0 min

approximate Flight Day 9 loss anchor to RTC2:
7200 s
2.000 h
```

---

# Operational Thread Counts

Total threads:

```text
3
```

Anomaly threads:

```text
1
```

Non-anomaly threads:

```text
2
```

Classification distribution:

```text
CONTINGENCY_READINESS:
1

EXPECTED_OPERATIONAL_CONSTRAINT:
1

UNEXPECTED_COMMUNICATIONS_ANOMALY:
1
```

---

# Independent Validator

Created:

```text
scripts/validation/validate_communications_operational_threads.py
```

The validator independently checks:

```text
reference dataset ID
summary product ID
thread identity
thread order
thread classification
anomaly flags
emergency-test precision
Flight Day 6 timing
live reacquisition precision
Flight Day 9 loss precision
Flight Day 9 recovery precision
RTC2 relationship
non-causation rule
supported affected direction
two-way-outage boundary
root-cause boundary
failed-subsystem boundary
anomaly-duration boundary
burn-preparation sequence
CSV integrity
summary integrity
SVG integrity
guardrail preservation
```

---

# Independent Validation Result

Threads:

```text
total:
3

non-anomaly:
2

anomaly:
1
```

Thread classifications:

```text
contingency readiness:
PASS

expected lunar constraint:
PASS

unexpected Flight Day 9 anomaly:
PASS
```

Flight Day 6:

```text
reported - planned blackout:
+0 s

reported - planned Earthrise:
-60 s

planned blackout -> planned AOS:
2460 s
41.0 min

reported blackout -> reported Earthrise:
2400 s
40.0 min

live reacquisition:
SEQUENCE_ONLY

exact reacquisition UTC:
NONE
```

Flight Day 9:

```text
loss precision:
APPROXIMATE

loss anchor exact:
FALSE

causal relationship:
NOT_ESTABLISHED

supported affected direction:
RETURN_LINK

complete two-way outage established:
FALSE

recovery:
SEQUENCE_ONLY

exact recovery UTC:
NONE

anomaly duration known:
FALSE

burn preparation resumed:
TRUE

approximate loss anchor -> RTC2:
~7200 s
~2.000 h
```

Decision-evidence boundary:

```text
public event sequence:
TRUE

full console transcript:
FALSE

Flight Director rationale tree:
FALSE

fault-isolation sequence:
FALSE

root-cause analysis:
FALSE

failed subsystem identification:
FALSE
```

Products:

```text
operational threads CSV rows:
3

summary:
PASS

operational threads figure:
PASS
```

Final validation:

```text
PASS
```

---

# Interpretation Guardrails

## Guardrail 1

```text
planned lunar blackout
!=
anomaly
```

---

## Guardrail 2

```text
reported blackout minute
=
planned blackout minute
```

does not imply exact second-level agreement.

---

## Guardrail 3

```text
reported Earthrise one minute early
!=
exact live DSN reacquisition time
```

---

## Guardrail 4

```text
planned 23:25 AOS
!=
observed 23:25 reacquisition
```

---

## Guardrail 5

```text
MOMENTS_AFTER_REPORTED_EARTHRISE
=
SEQUENCE_ONLY
```

No exact UTC is assigned.

---

## Guardrail 6

```text
~00:53 UTC Flight Day 9 anchor
!=
observed exact LOS timestamp
```

---

## Guardrail 7

```text
during a data-rate change
!=
caused by a data-rate change
```

---

## Guardrail 8

```text
return-link loss
!=
proven complete two-way outage
```

---

## Guardrail 9

```text
shortly afterward
!=
known anomaly duration
```

---

## Guardrail 10

```text
two-way communications restored
!=
identified failed subsystem
```

---

## Guardrail 11

```text
public event sequence
!=
full console decision log
```

---

## Guardrail 12

MissionLab does not fabricate:

```text
Flight Director decisions
console commands
controller dialogue
fault trees
internal troubleshooting
root cause
failed subsystem
recovery duration
undocumented timestamps
```

---

# Engineering Significance

Phase 2H.4 changes the communications reconstruction from a collection of communications facts into a mission-operations representation.

The project can now distinguish:

```text
TEST
EXPECTED CONSTRAINT
ANOMALY
RECOVERY
RETURN TO PLANNED OPERATIONS
```

This is important because mission control does not treat every loss of signal the same way.

For example:

```text
Flight Day 6 LOS
=
expected geometry-driven constraint

Flight Day 9 LOS
=
unexpected operational anomaly
```

Those events may superficially both look like:

```text
communications unavailable
```

but operationally they mean very different things.

The completed communications reconstruction now connects:

```text
network architecture
        +
lunar geometry
        +
ground-station geometry
        +
mission timing
        +
optical communications
        +
expected communications constraints
        +
unexpected anomaly recovery
```

while maintaining clear evidence boundaries.

---

# Phase 2H Communications Reconstruction Summary

Phase 2H now consists of four completed subphases.

```text
2H.1
Operational Communications Event Catalog

2H.2
Mission-Clock Communications Correlation

2H.3
O2O Optical Communications Reconstruction

2H.4
Communications Operational Threads
```

Together they provide:

```text
NASA-reported event catalog
planned-versus-reported timing
shared mission clock
lunar blackout sequence
geocentric communications geometry
topocentric DSN geometry
optical communications architecture
O2O performance
contingency readiness
unexpected communications anomaly
recovery sequence
decision-evidence boundary
```

---

# Phase 2H.4 Status

Operational thread dataset:

```text
PASS
```

Expected-versus-unexpected classification:

```text
PASS
```

Flight Day 6 operational thread:

```text
PASS
```

Flight Day 9 anomaly thread:

```text
PASS
```

Recovery sequence:

```text
PASS
```

Decision-evidence boundary:

```text
PASS
```

Non-causation guardrail:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2H.4 implementation status:

```text
COMPLETE
```

Phase 2H overall implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2I.1 — Maneuver Plan vs Execution

## Goal

Phase 2I.1 reconstructs the Artemis II trajectory-correction maneuver plan and compares planned maneuvers with actual mission execution.

The central operational question is not simply:

```text
What burns occurred?
```

It is:

```text
What burns were planned?
Which were still required after trajectory evaluation?
Which were cancelled?
Which executed?
What quantities are actually public?
```

The phase distinguishes:

```text
PLANNED
CANCELLED
EXECUTED
```

and preserves a critical mission-operations principle:

```text
cancelled correction
!=
failed correction
```

A planned trajectory correction can be removed because navigation performance made the burn unnecessary.

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_maneuver_plan_execution.json
```

Dataset identifier:

```text
phase2i1_artemis_ii_maneuver_plan_execution
```

Provenance:

```text
NASA_AND_ESA_REPORTED_WITH_MISSIONLAB_DERIVED_AGGREGATES
```

The dataset contains:

```text
planned outbound corrections
cancellation decisions
executed correction burns
reported durations
reported delta-v magnitudes
postflight TLI context
RTC2 communications context
propulsion-assignment boundaries
interpretation guardrails
```

---

# Maneuver Inventory

Phase 2I.1 contains six trajectory-correction maneuver records:

```text
OTC1
OTC2
OTC3
RTC1
RTC2
RTC3
```

Total:

```text
6
```

Executed:

```text
4
```

Cancelled:

```text
2
```

---

# Outbound Trajectory Correction Plan

NASA planned three outbound trajectory correction opportunities:

```text
OTC1
OTC2
OTC3
```

Final mission disposition:

```text
OTC1    CANCELLED
OTC2    CANCELLED
OTC3    EXECUTED
```

Therefore:

```text
planned:
3

cancelled:
2

executed:
1
```

Cancellation fraction:

```text
2 / 3
=
0.666666...
=
66.667%
```

This fraction describes the disposition of planned outbound trajectory corrections.

It is not a propulsion-system failure rate.

---

# OTC1 — Planned Maneuver

Maneuver:

```text
Outbound Trajectory Correction 1
```

Planned UTC:

```text
2026-04-03T22:49:00Z
```

Precision:

```text
MINUTE_LEVEL
```

Planned duration:

```text
approximately 8 seconds
```

Planned velocity change:

```text
0.7 ft/s
```

Quantity semantics:

```text
PLANNED
```

These numbers must not be presented as executed maneuver performance.

---

# OTC1 — Cancellation Decision

Status:

```text
CANCELLED
```

Executed:

```text
FALSE
```

Reason classification:

```text
TRAJECTORY_ALREADY_ON_CORRECT_FLIGHT_PATH
```

Exact cancellation timestamp known:

```text
FALSE
```

Executed firing duration:

```text
NONE
```

Executed delta-v:

```text
NONE
```

The planned:

```text
0.7 ft/s
```

is therefore not an executed Orion velocity change.

---

# OTC1 Operational Interpretation

The cancellation indicates that the correction was not needed after flight controllers evaluated Orion's actual trajectory.

Permanent interpretation:

```text
cancelled burn
!=
failed burn
```

and:

```text
cancelled burn
!=
propulsion anomaly
```

This is an important mission-operations distinction.

A correction-burn plan contains opportunities to remove navigation error.

If the error is already sufficiently small, executing the originally planned correction can be unnecessary.

---

# OTC2

Maneuver:

```text
Outbound Trajectory Correction 2
```

Status:

```text
CANCELLED
```

Executed:

```text
FALSE
```

Planning precision retained by Phase 2I.1:

```text
DATE_LEVEL
```

Decision reason:

```text
TRAJECTORY_REMAINED_ON_TRACK
```

Exact cancellation UTC:

```text
NONE
```

Public planned duration:

```text
NONE
```

Public planned delta-v retained by this dataset:

```text
NONE
```

MissionLab does not manufacture missing planned quantities.

---

# OTC2 Parallel Operational Activity

NASA reporting also described a spacecraft-attitude adjustment associated with clearing a wastewater vent line.

MissionLab records this contextual activity as:

```text
ATTITUDE_ADJUSTMENT_FOR_WASTEWATER_VENT_CLEARING
```

This activity is retained as operational context.

It is not interpreted as:

```text
an executed OTC2
```

and it is not assigned an invented trajectory-correction delta-v.

---

# OTC3

Maneuver:

```text
Outbound Trajectory Correction 3
```

Alternate description:

```text
Final Outbound Trajectory Correction
```

Status:

```text
EXECUTED
```

UTC:

```text
2026-04-06T03:03:00Z
```

Precision:

```text
MINUTE_LEVEL
```

Reported duration:

```text
17.5 seconds
```

Purpose classification:

```text
REFINE_TRAJECTORY_TOWARD_MOON
```

Phase 2I.1 public delta-v:

```text
NONE
```

---

# OTC3 Missing Delta-v Boundary

The absence of a public delta-v value in the Phase 2I.1 execution source means:

```text
delta-v not publicly reported in this source set
```

It does not mean:

```text
delta-v = 0
```

Therefore:

```text
OTC3 missing delta-v
!=
zero delta-v
```

MissionLab keeps the value null rather than inserting an unsupported estimate.

---

# Outbound Plan vs Execution

The outbound sequence is therefore:

```text
OTC1
planned
↓
trajectory evaluated
↓
cancelled

OTC2
planned
↓
trajectory evaluated
↓
cancelled

OTC3
planned
↓
required
↓
executed
```

The sequence provides a useful mission-operations example of trajectory correction as an adaptive process rather than a fixed sequence of mandatory firings.

---

# Postflight TLI Context

Postflight ESA reporting provides broader context for the outbound cancellations.

Translunar injection duration:

```text
350.0 seconds
```

Engine classification:

```text
EUROPEAN_SERVICE_MODULE_MAIN_ENGINE
```

Planned outbound corrections:

```text
3
```

Corrections made unnecessary:

```text
2
```

Postflight attribution:

```text
PRECISE TLI
```

MissionLab preserves this as postflight context.

It does not replace NASA's live operational cancellation reasons.

The two evidence layers answer slightly different questions:

```text
LIVE NASA REPORTING
Why did controllers cancel each maneuver at the time?

POSTFLIGHT ESA CONTEXT
Why were so few outbound corrections ultimately necessary?
```

---

# Return Trajectory Correction Sequence

Three return corrections were represented:

```text
RTC1
RTC2
RTC3
```

All three executed.

```text
planned:
3

executed:
3
```

---

# RTC1

Maneuver:

```text
Return Trajectory Correction 1
```

UTC:

```text
2026-04-08T00:03:00Z
```

Duration:

```text
15 seconds
```

Reported delta-v magnitude:

```text
1.6 ft/s
```

Purpose classification:

```text
REFINE_TRAJECTORY_TOWARD_EARTH
```

---

# RTC2

Maneuver:

```text
Return Trajectory Correction 2
```

UTC:

```text
2026-04-10T02:53:00Z
```

Duration:

```text
9 seconds
```

Reported delta-v magnitude:

```text
5.3 ft/s
```

Purpose classification:

```text
REFINE_TRAJECTORY_FOR_EARTH_RETURN
```

---

# RTC2 Cross-Phase Communications Context

Phase 2H established an unexpected return-link communications anomaly before RTC2.

Preburn communications-loss precision:

```text
APPROXIMATE
```

Communications recovery precision:

```text
SEQUENCE_ONLY
```

The operational sequence established in Phase 2H is:

```text
unexpected return-link loss
↓
communications restored
↓
burn preparation resumed
↓
RTC2 executed
```

Phase 2I.1 cross-checks that context.

RTC2 executed after communications recovery:

```text
TRUE
```

Communications anomaly implied burn failure:

```text
FALSE
```

Therefore:

```text
preburn communications anomaly
!=
failed RTC2
```

and:

```text
preburn communications anomaly
!=
cancelled RTC2
```

---

# RTC3

Maneuver:

```text
Return Trajectory Correction 3
```

UTC:

```text
2026-04-10T18:53:00Z
```

Duration:

```text
8 seconds
```

Reported delta-v magnitude:

```text
4.2 ft/s
```

Purpose classification:

```text
FINAL_TRAJECTORY_REFINEMENT_BEFORE_ENTRY
```

---

# Return Burn Duration Aggregate

Reported return correction durations:

```text
RTC1    15 s
RTC2     9 s
RTC3     8 s
```

Scalar duration sum:

```text
15 + 9 + 8
=
32 seconds
```

Therefore:

```text
combined reported return correction firing time:
32.0 s
```

This is a valid scalar duration aggregate.

---

# Return Delta-v Magnitude Aggregate

Reported return correction delta-v magnitudes:

```text
RTC1    1.6 ft/s
RTC2    5.3 ft/s
RTC3    4.2 ft/s
```

Scalar magnitude sum:

```text
1.6 + 5.3 + 4.2
=
11.1 ft/s
```

Conversion:

```text
11.1 × 0.3048
=
3.38328 m/s
```

Therefore:

```text
scalar sum of reported return delta-v magnitudes:

11.1 ft/s
3.38328 m/s
```

---

# Scalar vs Vector Delta-v

The quantity:

```text
11.1 ft/s
```

is not Orion's net vector velocity change.

Each trajectory correction has direction.

Without the complete burn-direction vectors:

```text
Δv1
Δv2
Δv3
```

MissionLab cannot compute:

```text
Δv_net
=
Δv1 + Δv2 + Δv3
```

as a vector sum.

Therefore the permanent label is:

```text
SCALAR SUM OF REPORTED DELTA-V MAGNITUDES
```

not:

```text
NET DELTA-V
```

---

# All Executed Correction-Burn Firing Time

Executed correction burns represented in Phase 2I.1:

```text
OTC3    17.5 s
RTC1    15.0 s
RTC2     9.0 s
RTC3     8.0 s
```

Known combined firing time:

```text
17.5 + 15 + 9 + 8
=
49.5 seconds
```

Therefore:

```text
known combined executed correction-burn firing time:
49.5 s
```

---

# Why No All-Burn Delta-v Total Is Reported

OTC3 has no public delta-v retained by the Phase 2I.1 source set.

Therefore MissionLab does not calculate:

```text
OTC3 + RTC1 + RTC2 + RTC3
```

delta-v.

Combined executed-correction delta-v computed:

```text
FALSE
```

Reason:

```text
OTC3 DELTA-V NOT PUBLIC IN PHASE 2I.1 SOURCE SET
```

Even if OTC3 later receives a source-backed magnitude, a scalar total would still require explicit labeling as a magnitude sum rather than a vector net.

---

# Propulsion Assignment Boundary

Phase 2I.1 intentionally does not assign exact propulsion hardware to the executed trajectory corrections.

OTC3 engine assignment:

```text
UNRESOLVED
```

RTC1 engine assignment:

```text
UNRESOLVED
```

RTC2 engine assignment:

```text
UNRESOLVED
```

RTC3 engine assignment:

```text
UNRESOLVED
```

This is deliberate.

Generic Orion / European Service Module propulsion architecture does not prove which engine or thruster set executed a specific burn.

---

# Engine-Assignment Rule

Permanent rule:

```text
propulsion architecture capability
!=
burn-specific as-flown assignment
```

Similarly:

```text
"thrusters ignited"
!=
specific engine identification
```

Phase 2I.2 will investigate the propulsion architecture and burn-selection evidence separately rather than injecting unsupported assignments into Phase 2I.1.

---

# Permanent Analyzer

Created:

```text
scripts/analysis/analyze_maneuver_plan_execution.py
```

The analyzer validates:

```text
maneuver identities
maneuver ordering
planned/executed status
OTC1 planned quantities
OTC1 cancellation semantics
OTC2 cancellation semantics
Phase 1 executed-burn consistency
return-burn duration aggregate
return delta-v magnitude aggregate
SI conversion
known combined firing time
RTC2 communications context
postflight TLI context
engine-assignment boundary
missing-value semantics
```

---

# Processed Maneuver Table

Generated:

```text
data/processed/maneuvers/maneuver_plan_execution.csv
```

Rows:

```text
6
```

Columns preserve:

```text
maneuver identity
name
mission leg
sequence
planned flag
status
executed flag
timestamp
timestamp precision
duration
duration semantics
delta-v
delta-v semantics
```

The file is reproducibly generated and remains ignored from Git.

---

# Processed Summary

Generated:

```text
data/processed/maneuvers/maneuver_plan_execution_summary.json
```

Product identifier:

```text
phase2i1_maneuver_plan_execution_analysis
```

The summary preserves:

```text
maneuver counts
status counts
outbound cancellation metrics
return execution metrics
scalar delta-v sums
known firing-time totals
OTC1 planned-versus-cancelled state
OTC2 operational context
RTC2 communications context
postflight TLI context
propulsion-assignment boundary
guardrails
```

The processed summary remains ignored from Git.

---

# Plan / Execution Figure

Created:

```text
docs/assets/maneuvers/phase2i1_maneuver_plan_execution.svg
```

The figure presents:

```text
OUTBOUND

OTC1      OTC2      OTC3
  X         X         ●
CANCEL    CANCEL    EXECUTE


RETURN

RTC1      RTC2      RTC3
  ●         ●         ●
EXECUTE   EXECUTE   EXECUTE
```

with the associated duration and delta-v evidence.

The figure also states that:

```text
cancelled != failed
```

and that the:

```text
11.1 ft/s
```

return quantity is a scalar magnitude sum rather than a vector net.

---

# Independent Validator

Created:

```text
scripts/validation/validate_maneuver_plan_execution.py
```

The validator independently checks:

```text
dataset identity
summary identity
maneuver count
maneuver order
status flags
OTC1 planned timestamp
OTC1 approximate-duration semantics
OTC1 planned delta-v semantics
OTC1 cancellation status
OTC1 missing executed delta-v
OTC2 cancellation semantics
executed burn timestamps
executed burn durations
RTC delta-v magnitudes
Phase 1 maneuver consistency
outbound cancellation fraction
return duration aggregate
return scalar delta-v aggregate
SI conversion
all-executed firing duration
RTC2 communications context
summary integrity
CSV integrity
missing-value semantics
SVG integrity
guardrail preservation
```

---

# Independent Validation Result

Maneuvers:

```text
total:
6

executed:
4

cancelled:
2
```

Outbound:

```text
planned:
3

cancelled:
2

executed:
1

cancellation fraction:
0.666667

cancellation percent:
66.667%
```

OTC1:

```text
planned duration:
~8 s

planned delta-v:
0.7 ft/s

executed:
FALSE

exact cancellation UTC:
NONE
```

OTC2:

```text
executed:
FALSE

exact cancellation UTC:
NONE
```

OTC3:

```text
executed:
TRUE

duration:
17.5 s

public delta-v:
NONE
```

Return:

```text
executed:
3 of 3

combined firing time:
32.0 s

scalar delta-v magnitude sum:
11.1 ft/s
3.38328 m/s

net vector delta-v:
NOT COMPUTED
```

All executed corrections:

```text
known firing time:
49.5 s

combined delta-v:
NOT COMPUTED
```

RTC2 cross-phase context:

```text
communications loss:
APPROXIMATE

communications recovery:
SEQUENCE_ONLY

RTC2 executed afterward:
TRUE

burn failure inferred:
FALSE
```

Propulsion assignment:

```text
OTC3:
UNRESOLVED

RTC1:
UNRESOLVED

RTC2:
UNRESOLVED

RTC3:
UNRESOLVED
```

Products:

```text
maneuver CSV rows:
6

summary:
PASS

plan/execution figure:
PASS
```

Final validation:

```text
PASS
```

---

# Interpretation Guardrails

## Guardrail 1

```text
cancelled correction
!=
failed correction
```

---

## Guardrail 2

```text
cancelled correction
!=
propulsion anomaly
```

---

## Guardrail 3

```text
OTC1 planned 0.7 ft/s
!=
executed delta-v
```

because OTC1 did not execute.

---

## Guardrail 4

```text
OTC1 planned ~8 s
!=
executed firing duration
```

---

## Guardrail 5

```text
OTC3 missing reported delta-v
!=
zero delta-v
```

---

## Guardrail 6

```text
11.1 ft/s
=
scalar sum of RTC delta-v magnitudes
```

not:

```text
net vector delta-v
```

---

## Guardrail 7

```text
3.38328 m/s
```

is only the SI conversion of the same scalar magnitude sum.

---

## Guardrail 8

```text
49.5 s
```

is a combined firing-duration total, not a delta-v quantity.

---

## Guardrail 9

Minute-level timestamps represented with:

```text
:00 seconds
```

do not imply second-level source precision.

---

## Guardrail 10

Exact OTC1 and OTC2 cancellation timestamps remain:

```text
UNKNOWN
```

---

## Guardrail 11

```text
generic ESM propulsion capability
!=
burn-specific engine assignment
```

---

## Guardrail 12

```text
Flight Day 9 communications anomaly
!=
RTC2 failure
```

---

# Engineering Significance

Phase 2I.1 changes the maneuver reconstruction from a simple list of burn timestamps into a plan-versus-execution model.

The mission sequence now captures:

```text
planned maneuver
        ↓
trajectory evaluation
        ↓
operational decision
        ↓
cancel or execute
```

This matters because trajectory correction is fundamentally adaptive.

A mission plan may contain several correction opportunities without requiring all of them to fire.

For Artemis II:

```text
3 outbound opportunities
↓
2 became unnecessary
↓
1 executed
```

while the return leg required:

```text
3 planned corrections
↓
3 executed
```

The result gives MissionLab a much stronger mission-operations representation than treating every planned burn as though it necessarily occurred.

---

# Phase 2I.1 Status

Reference dataset:

```text
PASS
```

Plan-versus-execution reconstruction:

```text
PASS
```

Outbound cancellation semantics:

```text
PASS
```

Executed-burn cross-check:

```text
PASS
```

Return duration aggregate:

```text
PASS
```

Scalar delta-v aggregate:

```text
PASS
```

RTC2 communications integration:

```text
PASS
```

Missing-value handling:

```text
PASS
```

Propulsion-assignment boundary:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2I.1 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2I.2 — European Service Module Propulsion Architecture and Burn-Selection Evidence

## Goal

Phase 2I.2 reconstructs the Artemis II Orion European Service Module propulsion architecture and establishes the evidence boundary for assigning propulsion hardware to individual trajectory correction burns.

The central engineering question is:

```text
What propulsion hardware exists?
What is each propulsion class designed to do?
What does public mission-planning guidance say?
What does operational guidance say?
What propulsion hardware can actually be confirmed as flown?
```

The permanent evidence rule is:

```text
architecture capability
!=
burn-specific as-flown assignment
```

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_esm_propulsion_architecture.json
```

Dataset identifier:

```text
phase2i2_artemis_ii_esm_propulsion_architecture
```

Provenance:

```text
NASA_AND_ESA_REPORTED_WITH_MISSIONLAB_DERIVED_ARCHITECTURE_METRICS
```

The dataset preserves:

```text
ESM propulsion architecture
engine classes
engine counts
nominal thrust
hardware roles
confirmed major-maneuver assignments
NASA premission correction-burn planning evidence
ESA operational correction-selection guidance
as-flown correction-burn wording
selection boundaries
source-layer differences
derived architecture ratios
interpretation guardrails
```

---

# Orion European Service Module Propulsion Architecture

The Artemis II European Service Module propulsion system is represented with:

```text
3 engine classes
33 engines total
```

Composition:

```text
1 main engine
8 auxiliary engines
24 reaction-control engines
```

Arithmetic:

```text
1 + 8 + 24
=
33
```

---

# Main Engine

Engine class:

```text
main_engine_oms_e
```

Display name:

```text
Orbital Maneuvering System Engine
```

Short name:

```text
OMS-E
```

Count:

```text
1
```

Nominal thrust:

```text
25,700 N
25.7 kN
```

Gimballed:

```text
TRUE
```

Primary role:

```text
MAJOR_IN_SPACE_MANEUVERS
```

Artemis II role classification:

```text
LARGE_VELOCITY_CHANGE
```

The main engine provides the highest per-engine thrust of the three ESM propulsion classes represented here.

---

# Auxiliary Engines

Engine class:

```text
auxiliary_r4d11
```

Model:

```text
R-4D-11
```

Count:

```text
8
```

Nominal thrust per engine:

```text
490 N
```

Fixed:

```text
TRUE
```

Primary role:

```text
ORBITAL_AND_TRAJECTORY_CORRECTIONS
```

Main-engine backup:

```text
TRUE
```

The auxiliary engines therefore occupy an intermediate propulsion role between:

```text
large main-engine maneuvers
```

and:

```text
fine reaction-control corrections
```

---

# Reaction Control System

Engine class:

```text
reaction_control_system
```

Count:

```text
24
```

Pod count:

```text
6
```

Engines per pod:

```text
4
```

Arithmetic:

```text
6 × 4
=
24
```

Nominal thrust per engine:

```text
220 N
```

Primary role:

```text
ATTITUDE_AND_FINE_CONTROL
```

The RCS architecture supports spacecraft orientation and fine-control activity.

Phase 2I.2 does not treat all 24 engines as simultaneously producing thrust in one direction.

---

# Per-Engine Nominal Thrust Ratios

MissionLab derives architecture-level per-engine comparisons.

## Main vs Auxiliary

```text
25,700 / 490
=
52.448979...
```

Therefore:

```text
52.449x
```

---

# Auxiliary vs RCS

```text
490 / 220
=
2.227272...
```

Therefore:

```text
2.227x
```

---

# Main vs RCS

```text
25,700 / 220
=
116.818181...
```

Therefore:

```text
116.818x
```

---

# Thrust-Ratio Interpretation

These values are:

```text
PER-ENGINE NOMINAL THRUST RATIOS
```

They are architecture context only.

They are not:

```text
spacecraft acceleration ratios
maneuver delta-v ratios
burn impulse ratios
flight-performance ratios
```

because those would require additional information including:

```text
actual engine selection
number of engines fired
thrust direction
spacecraft mass
burn duty cycle
burn duration
```

---

# Confirmed As-Flown Main-Engine Example 1 — Perigee Raise

Maneuver:

```text
PERIGEE_RAISE
```

Engine:

```text
MAIN_ENGINE_OMS_E
```

Assignment status:

```text
CONFIRMED_AS_FLOWN
```

Duration:

```text
43.0 seconds
```

This is a burn-specific public identification.

Therefore Phase 2I.2 may confidently assign:

```text
Perigee Raise -> OMS-E
```

---

# Confirmed As-Flown Main-Engine Example 2 — Translunar Injection

Maneuver:

```text
TLI
```

Engine:

```text
MAIN_ENGINE_OMS_E
```

Assignment status:

```text
CONFIRMED_AS_FLOWN
```

Duration:

```text
350.0 seconds
```

This is also burn-specific as-flown evidence.

Therefore:

```text
TLI -> OMS-E
```

is confirmed.

---

# Correction-Burn Selection Evidence

Trajectory correction burns have a weaker and more complicated public evidence chain.

Phase 2I.2 preserves two important but different source layers.

---

# NASA Premission Outbound-Correction Plan

Evidence stage:

```text
PREMISSION_PLAN
```

Scope:

```text
THREE_PLANNED_OUTBOUND_TRAJECTORY_CORRECTIONS
```

NASA premission engine claim:

```text
OMS_E
```

Burn-specific as-flown assignment:

```text
FALSE
```

This source describes the planned propulsion approach before execution.

It does not establish what actually fired during OTC3.

OTC1 and OTC2 were ultimately cancelled, so their premission engine plan cannot become an executed engine assignment.

---

# ESA Mission Operational Explanation

Evidence stage:

```text
MISSION_OPERATIONAL_EXPLANATION
```

Scope:

```text
TRAJECTORY_CORRECTION_MANEUVERS
```

ESA operational selection rule:

```text
larger correction
→
AUXILIARY

finer correction
→
RCS
```

Selection mechanism:

```text
FLIGHT_RULES_AND_REQUIRED_CORRECTION
```

Burn-specific as-flown assignment:

```text
FALSE
```

This provides operational logic for how propulsion classes can be selected.

It does not provide an as-flown propulsion record for OTC3, RTC1, RTC2, or RTC3.

---

# NASA / ESA Source Relationship

Permanent classification:

```text
SOURCE_SCOPE_OR_PLAN_DIFFERENCE_PRESERVED
```

NASA premission claim:

```text
THREE_PLANNED_OUTBOUND_CORRECTIONS_USE_OMS_E
```

ESA operational claim:

```text
CORRECTION_ENGINE_SELECTED_FROM_SMALLER_ENGINES
BY_FLIGHT_RULES_AND_REQUIRED_CORRECTION
```

Treated as identical:

```text
FALSE
```

Forced reconciliation:

```text
FALSE
```

Burn-specific resolution available:

```text
FALSE
```

MissionLab intentionally preserves both source descriptions.

Possible explanations could include:

```text
different source scope
different planning assumptions
different mission-planning maturity
different operational description level
evolving execution planning
```

but Phase 2I.2 does not claim which explanation is correct because the public evidence does not establish that.

---

# Why the Sources Are Not Silently Reconciled

It would be tempting to choose one of these statements:

```text
all outbound corrections use OMS-E
```

or:

```text
trajectory corrections use auxiliary/RCS
```

and apply it to the executed mission.

That would overstate the evidence.

Instead MissionLab maintains:

```text
NASA PREMISSION PLAN
        ↓
planned engine concept

ESA OPERATIONAL GUIDANCE
        ↓
selection logic / capability

NASA AS-FLOWN REPORT
        ↓
actual burn execution wording
```

Only the last category can resolve a specific executed burn if it names the actual engine class.

---

# OTC3 As-Flown Assignment

Maneuver:

```text
OTC3
```

Duration:

```text
17.5 seconds
```

Public delta-v retained from Phase 2I.1:

```text
NONE
```

As-flown engine class:

```text
UNRESOLVED
```

Assignment status:

```text
UNRESOLVED_AS_FLOWN
```

The public execution report does not provide enough burn-specific evidence to resolve the engine class.

---

# RTC1 As-Flown Assignment

Maneuver:

```text
RTC1
```

Duration:

```text
15 seconds
```

Reported delta-v:

```text
1.6 ft/s
```

NASA wording:

```text
IGNITED_ITS_THRUSTERS
```

Exact engine class:

```text
UNRESOLVED
```

The term:

```text
thrusters
```

does not prove:

```text
AUXILIARY
```

and does not prove:

```text
RCS
```

---

# RTC2 As-Flown Assignment

Maneuver:

```text
RTC2
```

Duration:

```text
9 seconds
```

Reported delta-v:

```text
5.3 ft/s
```

NASA wording:

```text
IGNITED_ITS_THRUSTERS
```

Exact engine class:

```text
UNRESOLVED
```

The larger reported delta-v compared with RTC1 does not establish a different propulsion class.

---

# RTC3 As-Flown Assignment

Maneuver:

```text
RTC3
```

Duration:

```text
8 seconds
```

Reported delta-v:

```text
4.2 ft/s
```

NASA wording:

```text
IGNITED_ITS_THRUSTERS
```

Exact engine class:

```text
UNRESOLVED
```

Again, neither burn duration nor reported delta-v independently identifies the engine hardware.

---

# Correction Assignment Totals

Correction burns represented:

```text
4
```

Resolved engine assignments:

```text
0
```

Unresolved engine assignments:

```text
4
```

Therefore:

```text
OTC3    UNRESOLVED
RTC1    UNRESOLVED
RTC2    UNRESOLVED
RTC3    UNRESOLVED
```

---

# Burn-Selection Public Boundary

Flight rules influence engine selection:

```text
TRUE
```

Required correction magnitude influences engine selection:

```text
TRUE
```

Larger corrections may use:

```text
AUXILIARY
```

Finer corrections may use:

```text
RCS
```

Exact public selection threshold:

```text
NONE
```

Exact public selection algorithm:

```text
NONE
```

Therefore MissionLab cannot derive rules such as:

```text
if Δv > X ft/s
use auxiliary
```

or:

```text
if burn duration < Y seconds
use RCS
```

No public threshold of that kind has been established.

---

# Burn Duration Is Not Engine Identification

Observed durations:

```text
OTC3    17.5 s
RTC1    15 s
RTC2     9 s
RTC3     8 s
```

These values alone cannot determine the engine class.

For example:

```text
short burn
!=
RCS proof
```

and:

```text
longer correction burn
!=
auxiliary proof
```

because firing duration depends on more than engine class.

---

# Delta-v Is Not Engine Identification

Reported return correction magnitudes:

```text
RTC1    1.6 ft/s
RTC2    5.3 ft/s
RTC3    4.2 ft/s
```

Those values also cannot independently identify engine class.

The missing information includes:

```text
vehicle mass
thrust-vector geometry
number of engines fired
duty cycle
exact commanded impulse
flight-rule threshold
```

Therefore:

```text
delta-v magnitude alone
!=
engine assignment
```

---

# Impulse Calculation Boundary

Phase 2I.2 deliberately does not compute maneuver impulse using:

```text
nominal thrust × reported burn duration
```

for OTC3 or RTC1–3.

That calculation would first require knowing:

```text
which engine class fired
how many engines fired
whether firing was continuous
whether nominal thrust applies to the entire event
thrust-vector orientation
```

Those values are unresolved.

Permanent rule:

```text
unresolved engine assignment
→
no burn-specific nominal-thrust impulse estimate
```

---

# Installed RCS Thrust Boundary

The ESM has:

```text
24 RCS engines
```

at:

```text
220 N each
```

But MissionLab does not calculate:

```text
24 × 220 N
=
5280 N
```

and call that usable translational thrust.

The RCS engines are distributed around the service module for different control directions.

Therefore:

```text
installed engine count × per-engine thrust
!=
simultaneous one-direction available thrust
```

---

# Confirmed vs Unresolved Engine Assignment Model

The architecture now supports two clearly separated categories.

## Confirmed

```text
Perigee Raise
→ OMS-E

TLI
→ OMS-E
```

## Unresolved

```text
OTC3
→ UNKNOWN

RTC1
→ UNKNOWN

RTC2
→ UNKNOWN

RTC3
→ UNKNOWN
```

This prevents architecture knowledge from being promoted into unsupported as-flown claims.

---

# Permanent Analyzer

Created:

```text
scripts/analysis/analyze_esm_propulsion_architecture.py
```

The analyzer verifies:

```text
engine-class count
total engine count
RCS pod arithmetic
engine identity
nominal thrust
OMS-E gimbal property
R-4D-11 identity
derived per-engine thrust ratios
confirmed perigee-raise assignment
confirmed TLI assignment
NASA premission evidence layer
ESA operational evidence layer
source relationship
Phase 2I.1 correction consistency
four unresolved correction assignments
public engine-selection boundary
derived-metric guardrails
```

---

# Processed Architecture Table

Generated:

```text
data/processed/maneuvers/esm_propulsion_architecture.csv
```

Rows:

```text
3
```

Each row represents one propulsion class:

```text
OMS-E
Auxiliary R-4D-11
RCS
```

The processed file remains ignored from Git.

---

# Processed Burn-Selection Evidence Table

Generated:

```text
data/processed/maneuvers/burn_selection_evidence.csv
```

Rows:

```text
6
```

Evidence rows include:

```text
NASA premission outbound plan
ESA operational selection explanation
OTC3 as-flown report
RTC1 as-flown report
RTC2 as-flown report
RTC3 as-flown report
```

This provides a direct comparison between:

```text
planning evidence
operational guidance
as-flown evidence
```

The processed file remains ignored from Git.

---

# Processed Summary

Generated:

```text
data/processed/maneuvers/esm_propulsion_architecture_summary.json
```

Product identifier:

```text
phase2i2_esm_propulsion_architecture_analysis
```

The summary preserves:

```text
architecture counts
nominal thrust values
derived thrust ratios
confirmed major-maneuver assignments
correction-selection evidence
source relationship
resolved/unresolved assignment counts
selection boundary
derived-metric policy
guardrails
output paths
```

The file remains ignored from Git.

---

# Propulsion Architecture Figure

Created:

```text
docs/assets/maneuvers/phase2i2_esm_propulsion_architecture.svg
```

The figure presents:

```text
OMS-E
1 × 25.7 kN

Auxiliary
8 × 490 N

RCS
24 × 220 N
6 pods × 4
```

along with the derived per-engine nominal thrust ratios.

The figure explicitly marks the ratios as:

```text
ARCHITECTURE CONTEXT ONLY
```

---

# Burn-Selection Evidence Figure

Created:

```text
docs/assets/maneuvers/phase2i2_burn_selection_evidence.svg
```

The figure compares:

```text
NASA premission planning
ESA operational guidance
NASA as-flown OTC3
NASA as-flown RTC1
NASA as-flown RTC2
NASA as-flown RTC3
```

and shows that the exact correction-burn engine assignments remain unresolved.

---

# Independent Validator

Created:

```text
scripts/validation/validate_esm_propulsion_architecture.py
```

The validator independently checks:

```text
reference dataset ID
summary product ID
engine-class count
total engine count
engine-class identity
1 / 8 / 24 counts
RCS 6 × 4 pod arrangement
OMS-E thrust
auxiliary thrust
RCS thrust
OMS-E gimbal property
R-4D-11 identity
derived thrust ratios
perigee-raise OMS-E assignment
perigee-raise duration
TLI OMS-E assignment
TLI duration
NASA premission evidence semantics
ESA operational evidence semantics
source-layer separation
unresolved OTC3 assignment
unresolved RTC1 assignment
unresolved RTC2 assignment
unresolved RTC3 assignment
Phase 2I.1 burn consistency
public-selection boundary
derived-metric guardrails
architecture CSV
selection CSV
summary
architecture SVG
selection-evidence SVG
guardrail preservation
```

---

# Independent Validation Result

Architecture:

```text
engine classes:
3

total engines:
33

main engine:
1

auxiliary engines:
8

RCS engines:
24

RCS arrangement:
6 pods × 4
```

Nominal thrust:

```text
OMS-E:
25.7 kN

auxiliary:
490 N each

RCS:
220 N each
```

Per-engine ratios:

```text
main / auxiliary:
52.449x

auxiliary / RCS:
2.227x

main / RCS:
116.818x
```

Architecture-only interpretation:

```text
PASS
```

Confirmed major maneuvers:

```text
perigee raise -> OMS-E:
PASS

perigee raise duration -> 43.0 s:
PASS

TLI -> OMS-E:
PASS

TLI duration -> 350.0 s:
PASS
```

Correction-selection evidence:

```text
NASA premission OMS-E plan:
PASS

ESA auxiliary/RCS flight-rule explanation:
PASS

evidence layers kept separate:
PASS

forced reconciliation:
FALSE
```

As-flown corrections:

```text
OTC3:
UNRESOLVED

RTC1:
UNRESOLVED

RTC2:
UNRESOLVED

RTC3:
UNRESOLVED
```

Totals:

```text
resolved:
0

unresolved:
4
```

Public selection boundary:

```text
flight rules influence selection:
TRUE

required correction influences selection:
TRUE

exact public thresholds:
NONE

exact public algorithm:
NONE
```

Products:

```text
architecture CSV rows:
3

selection-evidence CSV rows:
6

summary:
PASS

architecture figure:
PASS

selection-evidence figure:
PASS
```

Final validation:

```text
PASS
```

---

# Interpretation Guardrails

## Guardrail 1

```text
propulsion architecture
!=
burn-specific assignment
```

---

## Guardrail 2

```text
NASA premission OMS-E plan
!=
proof OTC3 used OMS-E
```

---

## Guardrail 3

```text
ESA auxiliary/RCS flight-rule guidance
!=
proof of a specific executed engine class
```

---

## Guardrail 4

```text
"ignited its thrusters"
!=
auxiliary-engine identification
```

---

## Guardrail 5

```text
"ignited its thrusters"
!=
RCS identification
```

---

## Guardrail 6

```text
burn duration
!=
engine-class identification
```

---

## Guardrail 7

```text
delta-v magnitude
!=
engine-class identification
```

---

## Guardrail 8

```text
nominal thrust ratio
!=
spacecraft acceleration ratio
```

---

## Guardrail 9

```text
24 × 220 N
!=
one-direction usable RCS thrust
```

---

## Guardrail 10

```text
nominal thrust × burn duration
```

is not computed for unresolved correction burns.

---

## Guardrail 11

NASA and ESA source differences are:

```text
PRESERVED
```

not hidden.

---

## Guardrail 12

Confirmed OMS-E use for:

```text
Perigee Raise
TLI
```

must not automatically be generalized to:

```text
OTC3
RTC1
RTC2
RTC3
```

---

# Engineering Significance

Phase 2I.2 establishes an evidence hierarchy for propulsion reconstruction.

The project can now answer:

```text
What propulsion classes exist?
What are their thrust levels?
What roles are they designed for?
Which major burns are confirmed OMS-E?
What public rules influence correction-engine selection?
Which correction-burn assignments remain unknown?
```

without falsely claiming information that public reporting does not reveal.

The resulting hierarchy is:

```text
SYSTEM ARCHITECTURE
        ↓
what hardware exists

MISSION PLANNING
        ↓
what was expected to be used

OPERATIONAL GUIDANCE
        ↓
how propulsion may be selected

AS-FLOWN REPORT
        ↓
what can actually be confirmed
```

This is especially important for a mission-operations reconstruction because operational configuration should not be inferred solely from vehicle capability.

---

# Phase 2I.2 Status

ESM architecture:

```text
PASS
```

Engine counts:

```text
PASS
```

Nominal thrust values:

```text
PASS
```

Confirmed OMS-E major maneuvers:

```text
PASS
```

NASA premission evidence:

```text
PASS
```

ESA operational evidence:

```text
PASS
```

Source-layer separation:

```text
PASS
```

As-flown correction assignment boundary:

```text
PASS
```

Derived thrust-ratio boundary:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2I.2 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2I.3 — Maneuver Mission-Clock and Trajectory-Solution Correlation

## Goal

Phase 2I.3 correlates the executed Artemis II trajectory correction maneuvers with:

```text
mission elapsed time
geometric mission phase
lunar SOI geometry
pericynthion
entry timing
splashdown timing
communications context
public OEM trajectory-solution evolution
```

The phase deliberately separates:

```text
maneuver execution evidence
```

from:

```text
public trajectory-solution evolution
```

because a difference between two public OEM products is not direct propulsion telemetry.

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_maneuver_trajectory_correlation.json
```

Dataset identifier:

```text
phase2i3_artemis_ii_maneuver_trajectory_correlation
```

Provenance:

```text
MISSIONLAB_DERIVED_FROM_NASA_REPORTED_EVENTS_AND_NASA_FLIGHT_DERIVED_PUBLIC_OEM_PRODUCTS
```

The dataset integrates:

```text
Phase 2I.1 maneuver execution
Phase 2I.2 propulsion-assignment boundaries
Phase 1 lunar geometry
Phase 1 public OEM archive
Phase 2H communications context
Phase 2 entry-event references
mission-clock configuration
```

---

# Mission Clock

Configured launch epoch:

```text
2026-04-01T22:35:12Z
```

Primary public OEM:

```text
Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.csv
```

The public correction-burn timestamps remain minute-level source anchors.

Seconds represented as:

```text
:00
```

do not imply second-level source precision.

---

# Mission Geometry Anchors

Derived lunar SOI entry:

```text
2026-04-06T04:38:07.532302Z
```

Derived pericynthion:

```text
2026-04-06T23:00:46.177998Z
```

Derived lunar SOI exit:

```text
2026-04-07T17:23:41.922211Z
```

NASA-reported Entry Interface anchor:

```text
2026-04-10T23:53:00Z
```

Precision:

```text
MINUTE_LEVEL
```

NASA-reported splashdown anchor:

```text
2026-04-11T00:07:00Z
```

Precision:

```text
MINUTE_LEVEL
```

---

# OTC3 Mission-Clock Correlation

Maneuver:

```text
OTC3
```

UTC:

```text
2026-04-06T03:03:00Z
```

MET anchor:

```text
04:04:27:48.000
```

Geometric mission phase:

```text
OUTBOUND_TRANSIT
```

Duration:

```text
17.5 s
```

Reported delta-v in the Phase 2I source set:

```text
NONE
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

# OTC3 to Lunar SOI Entry

Interval:

```text
5707.532302 s
```

Equivalent:

```text
1 h 35 min 07.532 s
```

Therefore OTC3 occurred approximately:

```text
1 hour 35 minutes
```

before derived lunar SOI entry.

The interval combines:

```text
minute-level NASA burn timing
+
MissionLab-derived geometry
```

and must retain those precision boundaries.

---

# OTC3 to Pericynthion

Interval:

```text
71866.177998 s
```

Equivalent:

```text
19 h 57 min 46.178 s
```

OTC3 therefore occurred approximately twenty hours before derived lunar closest approach.

---

# RTC1 Mission-Clock Correlation

Maneuver:

```text
RTC1
```

UTC:

```text
2026-04-08T00:03:00Z
```

MET anchor:

```text
06:01:27:48.000
```

Geometric mission phase:

```text
TRANS_EARTH_RETURN
```

Duration:

```text
15 s
```

Reported delta-v magnitude:

```text
1.6 ft/s
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

# Lunar SOI Exit to RTC1

Interval:

```text
23958.077789 s
```

Equivalent:

```text
6 h 39 min 18.078 s
```

RTC1 therefore occurred after Orion had already exited the MissionLab-derived NASA lunar SOI boundary.

Sequence:

```text
lunar SOI exit
↓
6 h 39 min
↓
RTC1
```

---

# RTC1 to RTC2

Interval:

```text
183000 s
```

Equivalent:

```text
2 d 2 h 50 min
```

This interval is derived from two minute-level NASA public maneuver anchors.

---

# RTC2 Mission-Clock Correlation

Maneuver:

```text
RTC2
```

UTC:

```text
2026-04-10T02:53:00Z
```

MET anchor:

```text
08:04:17:48.000
```

Geometric mission phase:

```text
TRANS_EARTH_RETURN
```

Duration:

```text
9 s
```

Reported delta-v magnitude:

```text
5.3 ft/s
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

# RTC2 Communications Context

Phase 2H established an unexpected return-link loss approximately two hours before RTC2.

MissionLab approximate reference anchor:

```text
2026-04-10T00:53:00Z
```

Precision:

```text
APPROXIMATE
```

Exact anchor:

```text
FALSE
```

Approximate interval to RTC2:

```text
~7200 s
~2.000 h
```

This interval must not be promoted into an exact anomaly duration or exact anomaly start time.

---

# RTC2 to RTC3

Interval:

```text
57600 s
```

Equivalent:

```text
16 h
```

---

# RTC3 Mission-Clock Correlation

Maneuver:

```text
RTC3
```

UTC:

```text
2026-04-10T18:53:00Z
```

MET anchor:

```text
08:20:17:48.000
```

Geometric mission phase:

```text
TRANS_EARTH_RETURN
```

Duration:

```text
8 s
```

Reported delta-v magnitude:

```text
4.2 ft/s
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

# RTC3 to Entry Interface

Interval:

```text
18000 s
```

Equivalent:

```text
5 h
```

Sequence:

```text
RTC3
↓
5 hours
↓
Entry Interface
```

The interval inherits the minute-level precision of the public RTC3 and Entry Interface event anchors.

It must not be represented as a second-accurate physical interval.

---

# RTC3 to Splashdown

Interval:

```text
18840 s
```

Equivalent:

```text
5 h 14 min
```

Again, the interval inherits minute-level public-event timing.

---

# Public OEM Archive

The standard public trajectory archive contains:

```text
9 OEM products
```

Phase 2I.3 audited the metadata of the maneuver-adjacent products.

Observed standard metadata fields include:

```text
CCSDS_OEM_VERS
CREATION_DATE
ORIGINATOR
OBJECT_NAME
OBJECT_ID
CENTER_NAME
REF_FRAME
TIME_SYSTEM
START_TIME
USEABLE_START_TIME
USEABLE_STOP_TIME
STOP_TIME
```

No explicit field was observed for:

```text
maneuver assimilated
post-maneuver solution
navigation cutoff
measurement cutoff
maneuver incorporation
maneuver update epoch
```

Therefore:

```text
explicit maneuver-assimilation metadata:
NONE
```

---

# OEM Creation-Time Brackets

Phase 2I.3 defines a chronological bracket around each maneuver using:

```text
latest covering OEM created at or before maneuver
```

and:

```text
earliest covering OEM created after maneuver
```

This is called a:

```text
CREATION-TIME BRACKET
```

It is not called a:

```text
PRE-BURN / POST-BURN ASSIMILATION BRACKET
```

because creation time alone does not prove whether a maneuver was incorporated into the solution.

---

# OTC3 OEM Creation-Time Bracket

Latest covering OEM created before OTC3:

```text
Artemis_II_OEM_2026_04_04_to_EI.csv
```

Creation:

```text
2026-04-03T23:45:26Z
```

Creation offset from OTC3:

```text
-184654 s
```

Earliest covering OEM created after OTC3:

```text
Artemis_II_OEM_2026_04_06_Pre-OTC3_to_EI.csv
```

Creation:

```text
2026-04-06T12:18:50Z
```

Creation offset from OTC3:

```text
+33350 s
```

Equivalent:

```text
9 h 15 min 50 s after reported OTC3 minute
```

---

# OTC3 Metadata Contradiction / Lifecycle Boundary

The later-created product is explicitly named:

```text
Pre-OTC3
```

despite having a metadata creation time after the reported OTC3 execution minute.

Therefore:

```text
CREATION_DATE after maneuver
!=
proof maneuver was assimilated
```

This is one of the most important findings of Phase 2I.3.

The filename and metadata creation timestamp may describe different aspects of the public OEM product lifecycle.

MissionLab does not silently reinterpret either one.

---

# OTC3 Same-Epoch OEM Solution Difference

Both creation-time-bracketing products cover the OTC3 epoch.

Their states were independently interpolated to:

```text
2026-04-06T03:03:00Z
```

Position difference magnitude:

```text
169.098527 km
```

Velocity difference magnitude:

```text
1.893541 m/s
```

Interpretation:

```text
SOLUTION_TO_SOLUTION_DIFFERENCE_AT_COMMON_MANEUVER_EPOCH
```

Maneuver assimilation:

```text
NOT_ESTABLISHED
```

Measured burn delta-v:

```text
FALSE
```

Navigation error:

```text
FALSE
```

---

# RTC1 OEM Creation-Time Bracket

Latest covering OEM created before RTC1:

```text
Artemis_II_OEM_2026_04_07_Pre-Lunar-Flyby_to_EI.csv
```

Creation:

```text
2026-04-07T12:47:44Z
```

Creation offset:

```text
-40516 s
```

Earliest covering OEM created after RTC1:

```text
Artemis_II_OEM_2026_04_08_Post-ICPS-Sep_to_EI.csv
```

Creation:

```text
2026-04-08T01:49:15Z
```

Creation offset:

```text
+6375 s
```

---

# RTC1 Same-Epoch OEM Solution Difference

Position difference:

```text
1.443975 km
```

Velocity difference:

```text
0.068048 m/s
```

Interpretation:

```text
SOLUTION_TO_SOLUTION_DIFFERENCE_AT_COMMON_MANEUVER_EPOCH
```

Maneuver assimilation:

```text
NOT_ESTABLISHED
```

Measured RTC1 delta-v from this comparison:

```text
FALSE
```

---

# RTC2 OEM Creation-Time Bracket

Latest covering OEM created before RTC2:

```text
Artemis_II_OEM_2026_04_09_Post-ICPS-Sep_to_EI.csv
```

Creation:

```text
2026-04-08T22:20:54Z
```

Creation offset:

```text
-102726 s
```

Earliest covering OEM created after RTC2:

```text
Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.csv
```

Creation:

```text
2026-04-10T03:22:19Z
```

Creation offset:

```text
+1759 s
```

Equivalent:

```text
29 min 19 s
```

after the minute-level RTC2 anchor.

---

# RTC2 Same-Epoch OEM Solution Difference

Position difference:

```text
34.536691 km
```

Velocity difference:

```text
0.381837 m/s
```

Interpretation:

```text
SOLUTION_TO_SOLUTION_DIFFERENCE_AT_COMMON_MANEUVER_EPOCH
```

Maneuver assimilation:

```text
NOT_ESTABLISHED
```

Measured RTC2 delta-v from this comparison:

```text
FALSE
```

The NASA-reported RTC2 maneuver magnitude remains independently:

```text
5.3 ft/s
```

The OEM velocity-solution difference is not used as a replacement or validation measurement for that reported burn magnitude.

---

# RTC3 OEM Creation-Time Bracket

Latest public OEM created before RTC3:

```text
Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.csv
```

Creation:

```text
2026-04-10T03:22:19Z
```

Creation offset:

```text
-55841 s
```

Later standard public OEM:

```text
NONE
```

Therefore:

```text
direct creation-time bracket comparison:
NOT AVAILABLE
```

MissionLab does not manufacture a post-RTC3 trajectory product.

---

# What an OEM Solution Difference Means

For two public OEMs evaluated at the same epoch:

```text
Δr_solution
=
r_solution_B
-
r_solution_A
```

and:

```text
Δv_solution
=
v_solution_B
-
v_solution_A
```

MissionLab reports the magnitudes:

```text
|Δr_solution|
|Δv_solution|
```

These quantities measure differences between two released trajectory solutions.

They do not identify why the solutions differ.

---

# What an OEM Solution Difference Does Not Mean

A same-epoch solution difference may contain effects from:

```text
navigation estimation updates
new tracking data
changed modeling
maneuver planning updates
maneuver incorporation
prediction changes
solution generation changes
other unavailable flight-dynamics updates
```

The public OEM archive does not allow those components to be uniquely separated.

Therefore:

```text
OEM Δstate
!=
navigation error
```

and:

```text
OEM Δstate
!=
measured burn Δv
```

---

# Creation Date vs Maneuver Assimilation

Permanent rule:

```text
OEM CREATION_DATE
!=
maneuver assimilation proof
```

A product created after a maneuver may still represent a solution with labels or assumptions associated with a pre-maneuver state.

The OTC3 product provides direct evidence that creation chronology and maneuver-assimilation semantics cannot be treated as equivalent.

---

# Product Filename Semantics

Filename labels such as:

```text
PRE_OTC3
PRE_LUNAR_FLYBY
POST_ICPS_SEP
TO_EI
```

are preserved exactly as product-label evidence.

They are not silently converted into:

```text
confirmed navigation-estimation state
confirmed maneuver assimilation
confirmed measurement cutoff
```

unless an authoritative source explicitly defines them that way.

---

# Propulsion Boundary

Phase 2I.2 established that exact engine assignments remain unresolved for:

```text
OTC3
RTC1
RTC2
RTC3
```

Phase 2I.3 preserves that result.

Therefore it does not compute:

```text
thrust-derived acceleration
burn impulse
propellant usage
specific impulse performance
engine efficiency
```

for these correction burns.

---

# No Nominal-Thrust Impulse Calculation

Phase 2I.3 does not use:

```text
nominal engine thrust × burn duration
```

because the actual engine class and firing configuration remain unresolved.

Therefore:

```text
burn impulse from nominal thrust:
NOT COMPUTED
```

---

# Processed Mission-Clock Table

Generated:

```text
data/processed/maneuvers/maneuver_mission_clock_correlation.csv
```

Rows:

```text
4
```

The table contains:

```text
maneuver ID
UTC
timestamp precision
MET anchor
geometric mission phase
duration
reported delta-v
engine assignment status
```

The file remains ignored from Git.

---

# Processed OEM Bracket Table

Generated:

```text
data/processed/maneuvers/maneuver_oem_solution_brackets.csv
```

Rows:

```text
4
```

The table preserves:

```text
maneuver epoch
latest OEM created at/before maneuver
creation time
creation offset
filename semantics
earliest OEM created after maneuver
creation time
creation offset
filename semantics
same-epoch position difference
same-epoch velocity difference
comparison semantics
maneuver-assimilation status
measured-delta-v flag
navigation-error flag
```

The file remains ignored from Git.

---

# Processed Summary

Generated:

```text
data/processed/maneuvers/maneuver_trajectory_correlation_summary.json
```

Product identifier:

```text
phase2i3_maneuver_trajectory_correlation_analysis
```

The summary includes:

```text
mission-clock correlations
mission-event intervals
RTC2 communications context
OEM archive audit
creation-time brackets
same-epoch solution comparisons
analysis boundaries
interpretation guardrails
```

The file remains ignored from Git.

---

# Mission-Clock Figure

Created:

```text
docs/assets/maneuvers/phase2i3_maneuver_mission_clock.svg
```

The figure places:

```text
OTC3
RTC1
RTC2
RTC3
```

against:

```text
SOI entry
pericynthion
SOI exit
Entry Interface
splashdown
```

on the common Artemis II mission clock.

---

# OEM Solution-Bracket Figure

Created:

```text
docs/assets/maneuvers/phase2i3_oem_solution_brackets.svg
```

The figure compares the chronological public OEM brackets for each maneuver and explicitly states:

```text
creation-time bracket
!=
maneuver-assimilation bracket
```

and:

```text
OEM solution difference
!=
navigation error
!=
measured burn delta-v
```

---

# Independent Validator

Created:

```text
scripts/validation/validate_maneuver_trajectory_correlation.py
```

The validator independently checks:

```text
dataset identity
summary identity
launch epoch
lunar SOI anchors
pericynthion
Entry Interface anchor
splashdown anchor
event precision
RTC2 communications precision
maneuver identities
maneuver timestamps
MET anchors
mission phases
durations
reported delta-v values
unresolved engine assignments
mission-event intervals
nine-product OEM archive
creation-time bracket identities
OEM creation offsets
independent Hermite interpolation
same-epoch position differences
same-epoch velocity differences
RTC3 missing later OEM
OTC3 PRE_OTC3 contradiction
metadata-assimilation boundary
CSV integrity
summary integrity
SVG integrity
guardrail preservation
```

---

# Independent Validation Result

Mission phases:

```text
OTC3:
OUTBOUND_TRANSIT

RTC1:
TRANS_EARTH_RETURN

RTC2:
TRANS_EARTH_RETURN

RTC3:
TRANS_EARTH_RETURN
```

Mission intervals:

```text
OTC3 -> SOI entry:
5707.532302 s

OTC3 -> pericynthion:
71866.177998 s

SOI exit -> RTC1:
23958.077789 s

RTC1 -> RTC2:
183000.0 s

RTC2 -> RTC3:
57600.0 s

RTC3 -> Entry Interface:
18000.0 s

RTC3 -> splashdown:
18840.0 s

approximate communications-loss anchor -> RTC2:
~7200.0 s
```

OEM archive:

```text
standard products:
9

explicit maneuver-assimilation field:
NONE

CREATION_DATE proves assimilation:
FALSE
```

Same-epoch public OEM differences:

```text
OTC3:
169.098527 km
1.893541 m/s
assimilation NOT_ESTABLISHED

RTC1:
1.443975 km
0.068048 m/s
assimilation NOT_ESTABLISHED

RTC2:
34.536691 km
0.381837 m/s
assimilation NOT_ESTABLISHED

RTC3:
later public OEM NONE
comparison NOT AVAILABLE
```

OTC3 audit:

```text
later-created OEM label:
PRE_OTC3

creation time proves assimilation:
FALSE
```

Interpretation boundary:

```text
OEM difference = solution-to-solution:
PASS

OEM difference = navigation error:
FALSE

OEM difference = measured burn delta-v:
FALSE

unresolved engine assignments preserved:
PASS

thrust-derived performance computed:
FALSE

nominal-thrust impulse computed:
FALSE
```

Products:

```text
mission-clock CSV rows:
4

OEM bracket CSV rows:
4

summary:
PASS

mission-clock figure:
PASS

OEM bracket figure:
PASS
```

Final validation:

```text
PASS
```

---

# Interpretation Guardrails

## Guardrail 1

```text
OEM solution difference
!=
navigation error
```

---

## Guardrail 2

```text
OEM solution difference
!=
measured burn delta-v
```

---

## Guardrail 3

```text
CREATION_DATE after burn
!=
maneuver assimilation proof
```

---

## Guardrail 4

The later-created OTC3-adjacent product remains explicitly labeled:

```text
PRE_OTC3
```

and this contradiction is preserved rather than hidden.

---

## Guardrail 5

```text
product creation time
!=
maneuver execution time
```

---

## Guardrail 6

```text
later-created solution evaluated at maneuver epoch
!=
raw maneuver telemetry
```

---

## Guardrail 7

Filename semantics are retained but are not automatically converted into navigation-state semantics.

---

## Guardrail 8

Minute-level public event anchors do not gain second-level precision merely because calculations produce decimal seconds.

---

## Guardrail 9

The RTC2 communications anchor remains:

```text
APPROXIMATE
```

---

## Guardrail 10

```text
OTC3
RTC1
RTC2
RTC3
```

engine assignments remain unresolved.

---

## Guardrail 11

No thrust-derived:

```text
acceleration
impulse
propellant consumption
performance efficiency
```

is inferred for the correction burns.

---

## Guardrail 12

RTC3 has no later standard public OEM and therefore no direct chronological two-product bracket.

---

# Engineering Significance

Phase 2I.3 connects propulsion operations to the mission timeline without overstating what the public trajectory products reveal.

The project can now answer:

```text
When did each executed correction occur?

Where was Orion in the mission geometry?

How long before or after major mission events did each burn occur?

How did chronologically adjacent public trajectory solutions differ
at the maneuver epoch?

What can those differences legitimately tell us?
```

The answer to the final question is deliberately constrained:

```text
They show public solution evolution.
```

They do not independently reveal:

```text
measured maneuver performance
navigation error
engine identity
burn impulse
```

This makes the maneuver reconstruction suitable for mission-operations analysis while preserving the distinction between public flight-derived ephemeris products and unavailable onboard or ground-system telemetry.

---

# Phase 2I.3 Status

Mission-clock correlation:

```text
PASS
```

Geometric-phase correlation:

```text
PASS
```

Communications correlation:

```text
PASS
```

Entry timing correlation:

```text
PASS
```

OEM archive audit:

```text
PASS
```

Creation-time bracket reconstruction:

```text
PASS
```

Independent same-epoch state comparison:

```text
PASS
```

OTC3 metadata contradiction handling:

```text
PASS
```

Maneuver-assimilation uncertainty:

```text
PASS
```

Propulsion non-inference boundary:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2I.3 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2I.4 — Maneuver Operational Threads and Phase 2I Closure

## Goal

Phase 2I.4 integrates the maneuver, propulsion, communications, trajectory, and entry-context work from Phases 2I.1 through 2I.3 into evidence-backed mission-operations threads.

The purpose is not to reconstruct an undocumented Mission Control transcript.

The purpose is to establish:

```text
what was planned
what was cancelled
what was executed
what public evidence says about why
where the spacecraft was in the mission
what communications context existed
what propulsion information is known
what propulsion information remains unknown
what trajectory-solution evolution is visible
what conclusions cannot be made from public evidence
```

The permanent operational boundary is:

```text
public operational sequence
!=
console transcript
!=
Flight Director rationale tree
!=
root-cause analysis
```

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_maneuver_operational_threads.json
```

Dataset identifier:

```text
phase2i4_artemis_ii_maneuver_operational_threads
```

Provenance:

```text
NASA_AND_ESA_REPORTED_WITH_MISSIONLAB_DERIVED_OPERATIONAL_CORRELATIONS
```

The dataset integrates:

```text
Phase 2I.1 maneuver plan/execution evidence
Phase 2I.2 propulsion architecture
Phase 2I.2 burn-selection evidence boundary
Phase 2I.3 mission-clock correlations
Phase 2I.3 OEM solution evolution
Phase 2H communications operational threads
lunar geometry context
entry and splashdown timing
```

---

# Correction Opportunity Accounting

Total planned correction opportunities:

```text
6
```

Executed:

```text
4
```

Cancelled:

```text
2
```

---

# Outbound Correction Accounting

Planned outbound corrections:

```text
3
```

Cancelled:

```text
2
```

Executed:

```text
1
```

Cancellation fraction:

```text
2 / 3
=
0.666666...
=
66.667%
```

This does not represent a failure rate.

The two cancelled maneuvers were intentionally not executed because public reporting stated that Orion's trajectory already satisfied the required flight path.

---

# Return Correction Accounting

Planned return corrections:

```text
3
```

Executed:

```text
3
```

Execution fraction:

```text
3 / 3
=
100%
```

Executed return corrections:

```text
RTC1
RTC2
RTC3
```

---

# Operational Thread 1 — Outbound Adaptive Trajectory Management

Thread ID:

```text
outbound_adaptive_trajectory_management
```

Classification:

```text
NOMINAL_ADAPTIVE_TRAJECTORY_MANAGEMENT
```

Anomaly:

```text
FALSE
```

Sequence:

```text
OTC1 planned
↓
OTC1 cancelled
↓
OTC2 planned
↓
OTC2 cancelled
↓
OTC3 executed
↓
lunar SOI entry
↓
pericynthion
```

---

# OTC1

Status:

```text
CANCELLED
```

Reason classification:

```text
TRAJECTORY_ALREADY_ON_CORRECT_FLIGHT_PATH
```

Failed burn:

```text
FALSE
```

Propulsion anomaly:

```text
FALSE
```

The burn was never executed.

Therefore:

```text
cancelled correction
!=
failed burn
```

---

# OTC2

Status:

```text
CANCELLED
```

Reason classification:

```text
TRAJECTORY_REMAINED_ON_TRACK
```

Failed burn:

```text
FALSE
```

Propulsion anomaly:

```text
FALSE
```

Parallel operational activity:

```text
ATTITUDE_ADJUSTMENT_FOR_WASTEWATER_VENT_CLEARING
```

The schedule change did not establish a propulsion problem.

---

# OTC3

Status:

```text
EXECUTED
```

Timestamp:

```text
2026-04-06T03:03:00Z
```

Precision:

```text
MINUTE_LEVEL
```

Duration:

```text
17.5 s
```

Mission phase:

```text
OUTBOUND_TRANSIT
```

Reported public delta-v in the Phase 2I source set:

```text
NONE
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

# OTC3 to Lunar SOI Entry

Interval:

```text
5707.532302 s
```

Equivalent:

```text
1 h 35 min 07.532 s
```

Sequence:

```text
OTC3
↓
~1 h 35 min
↓
lunar SOI entry
```

The interval combines:

```text
minute-level public burn timing
+
MissionLab-derived lunar geometry
```

---

# OTC3 to Pericynthion

Interval:

```text
71866.177998 s
```

Equivalent:

```text
19 h 57 min 46.178 s
```

This connects the final outbound correction to the lunar-flyby geometry without implying that public timing alone reconstructs the targeting algorithm.

---

# Postflight Outbound Context

ESA postflight reporting provides the context that the translunar injection was sufficiently precise that two of the three planned outbound corrections were unnecessary.

MissionLab preserves this as:

```text
POSTFLIGHT REPORTED CONTEXT
```

It does not reconstruct:

```text
full console decision logic
Flight Director rationale tree
targeting threshold logic
navigation covariance threshold
go/no-go criteria
```

because those are not present in the public evidence set.

---

# Operational Thread 2 — Lunar Flyby Expected Communications Constraint

Thread ID:

```text
lunar_flyby_expected_communications_constraint
```

Classification:

```text
EXPECTED_OPERATIONAL_CONSTRAINT
```

Anomaly:

```text
FALSE
```

Propulsion anomaly:

```text
FALSE
```

Sequence:

```text
expected lunar blackout
↓
Earthrise
↓
DSN reacquisition sequence
```

The lunar blackout is caused by known lunar occultation geometry and was expected operationally.

Therefore:

```text
expected lunar blackout
!=
communications anomaly
```

and:

```text
expected lunar blackout
!=
propulsion anomaly
```

---

# Lunar Reacquisition Precision Boundary

Reported Earthrise:

```text
2026-04-06T23:24:00Z
```

Precision:

```text
MINUTE_LEVEL
```

Live DSN reacquisition:

```text
MOMENTS AFTER EARTHRISE
```

Precision:

```text
SEQUENCE_ONLY
```

Exact live reacquisition UTC:

```text
NOT PUBLIC
```

MissionLab does not assign the planned 23:25 UTC value as an observed live reacquisition time.

---

# Operational Thread 3 — Return Trajectory Refinement

Thread ID:

```text
return_trajectory_refinement
```

Classification:

```text
NOMINAL_RETURN_TRAJECTORY_MANAGEMENT
```

Anomaly:

```text
FALSE
```

Sequence:

```text
lunar SOI exit
↓
RTC1
↓
RTC2 after communications recovery
↓
RTC3
↓
Entry Interface
```

---

# Lunar SOI Exit to RTC1

Derived lunar SOI exit:

```text
2026-04-07T17:23:41.922211Z
```

RTC1:

```text
2026-04-08T00:03:00Z
```

Interval:

```text
23958.077789 s
```

Equivalent:

```text
6 h 39 min 18.078 s
```

RTC1 therefore occurred during the trans-Earth return after Orion exited the MissionLab-derived lunar SOI.

---

# RTC1

Status:

```text
EXECUTED
```

Duration:

```text
15.0 s
```

Reported delta-v magnitude:

```text
1.6 ft/s
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

# RTC2

Status:

```text
EXECUTED
```

Duration:

```text
9.0 s
```

Reported delta-v magnitude:

```text
5.3 ft/s
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

Communications had been restored before the burn and burn preparation resumed.

---

# RTC3

Status:

```text
EXECUTED
```

Duration:

```text
8.0 s
```

Reported delta-v magnitude:

```text
4.2 ft/s
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

# Operational Thread 4 — RTC2 Communications Interruption and Recovery

Thread ID:

```text
rtc2_communications_interruption_and_recovery
```

Classification:

```text
UNEXPECTED_COMMUNICATIONS_ANOMALY_WITH_MISSION_CONTINUATION
```

Anomaly:

```text
TRUE
```

Operational sequence:

```text
unexpected return-link loss
↓
two-way communications reestablished
↓
burn preparation resumed
↓
RTC2 executed
```

---

# RTC2 Return-Link Loss

Approximate computational anchor:

```text
2026-04-10T00:53:00Z
```

Precision:

```text
APPROXIMATE
```

Observed exact anomaly timestamp:

```text
FALSE
```

Supported affected direction:

```text
RETURN_LINK
```

The event affected communication and telemetry transmission from spacecraft to ground.

---

# Data-Rate Change Boundary

NASA reported the communications event occurred:

```text
DURING_DATA_RATE_CHANGE
```

This establishes context.

It does not establish:

```text
DATA_RATE_CHANGE CAUSED FAILURE
```

Therefore:

```text
context
!=
causation
```

Permanent causal classification:

```text
NOT_ESTABLISHED
```

---

# Two-Way Outage Boundary

The public evidence supports:

```text
return-link loss
```

It does not establish:

```text
complete simultaneous two-way outage
```

Therefore:

```text
complete_two_way_outage_established:
FALSE
```

---

# RTC2 Mission Continuation

Public sequence:

```text
return-link loss
↓
communications restored
↓
burn preparation resumed
↓
RTC2 executed
```

Burn executed after recovery:

```text
TRUE
```

Burn failure:

```text
FALSE
```

Propulsion anomaly inferred:

```text
FALSE
```

This distinction is critical.

The communications anomaly and subsequent maneuver are operationally connected in sequence but are not evidence of a propulsion failure.

---

# Operational Thread 5 — Final Correction to Entry Handoff

Thread ID:

```text
final_correction_to_entry_handoff
```

Classification:

```text
NOMINAL_ENTRY_TARGETING_HANDOFF
```

Anomaly:

```text
FALSE
```

Sequence:

```text
RTC3
↓
5-hour public clock interval
↓
Entry Interface
↓
splashdown
```

---

# RTC3 to Entry Interface

RTC3:

```text
2026-04-10T18:53:00Z
```

Entry Interface:

```text
2026-04-10T23:53:00Z
```

Interval:

```text
18000 s
```

Equivalent:

```text
5 h
```

The interval inherits minute-level public timing precision.

It does not expose the complete entry-targeting algorithm.

---

# RTC3 to Splashdown

Splashdown:

```text
2026-04-11T00:07:00Z
```

RTC3-to-splashdown interval:

```text
18840 s
```

Equivalent:

```text
5 h 14 min
```

---

# Final Navigation / Guidance Boundary

The final-correction thread establishes:

```text
RTC3
→
Entry Interface
→
splashdown
```

on the public mission clock.

It does not establish:

```text
final navigation state vector
final targeting covariance
entry targeting algorithm
guidance command history
bank-command history
flight-control command history
```

Those belong to future guidance/GNC reconstruction only where public evidence supports them.

---

# Propulsion Assignment Boundary

Phase 2I.2 remains authoritative for burn-specific propulsion assignment.

Resolved correction-burn engine assignments:

```text
0
```

Unresolved:

```text
4
```

Unresolved burns:

```text
OTC3
RTC1
RTC2
RTC3
```

---

# Confirmed OMS-E Uses

Confirmed as-flown major maneuvers:

```text
Perigee Raise
TLI
```

Engine:

```text
OMS-E
```

This does not imply:

```text
OTC3 -> OMS-E
RTC1 -> OMS-E
RTC2 -> OMS-E
RTC3 -> OMS-E
```

Permanent rule:

```text
confirmed major-burn engine assignment
!=
correction-burn engine assignment
```

---

# Correction Firing-Time Aggregate

Known executed correction durations:

```text
OTC3   17.5 s
RTC1   15.0 s
RTC2    9.0 s
RTC3    8.0 s
```

Sum:

```text
17.5 + 15 + 9 + 8
=
49.5 s
```

Therefore:

```text
known executed correction firing time:
49.5 s
```

This is a duration sum only.

It is not propulsion impulse.

---

# Return Scalar Delta-v Magnitude Sum

Reported return magnitudes:

```text
RTC1   1.6 ft/s
RTC2   5.3 ft/s
RTC3   4.2 ft/s
```

Scalar magnitude sum:

```text
1.6 + 5.3 + 4.2
=
11.1 ft/s
```

Conversion:

```text
11.1 × 0.3048
=
3.38328 m/s
```

Therefore:

```text
11.1 ft/s
3.38328 m/s
```

---

# Scalar vs Vector Delta-v Boundary

The quantity above is:

```text
SUM OF REPORTED SCALAR MAGNITUDES
```

It is not:

```text
NET VECTOR DELTA-V
```

because burn-vector directions are not present in the public source set.

Therefore:

```text
net vector delta-v:
NOT COMPUTED
```

---

# All-Correction Delta-v Boundary

OTC3 public delta-v in the Phase 2I source set:

```text
MISSING
```

Therefore MissionLab does not compute:

```text
OTC3 + RTC1 + RTC2 + RTC3
```

as an all-correction scalar delta-v total.

Reason:

```text
OTC3_PUBLIC_DELTA_V_MISSING
AND
VECTOR_DIRECTIONS_UNAVAILABLE
```

---

# OEM Trajectory-Solution Boundary

Standard public OEM products:

```text
9
```

Same-epoch creation-bracket comparisons available:

```text
3
```

Available:

```text
OTC3
RTC1
RTC2
```

Unavailable:

```text
RTC3
```

because no later standard public OEM exists in the current archive.

---

# Maneuver Assimilation Boundary

Maneuver assimilation established from public OEM metadata:

```text
FALSE
```

for:

```text
OTC3
RTC1
RTC2
RTC3
```

Permanent rule:

```text
CREATION_DATE
!=
maneuver assimilation
```

---

# OEM Interpretation Boundary

Permanent rules:

```text
OEM solution difference
!=
navigation error
```

and:

```text
OEM solution difference
!=
measured burn delta-v
```

The OEM comparisons represent public trajectory-solution evolution only.

---

# Operational Thread Product

Generated:

```text
data/processed/maneuvers/maneuver_operational_threads.csv
```

Rows:

```text
5
```

Each row contains:

```text
thread ID
thread name
classification
anomaly flag
step count
sequence
```

The processed product remains ignored from Git.

---

# Operational Thread Summary

Generated:

```text
data/processed/maneuvers/maneuver_operational_threads_summary.json
```

Product identifier:

```text
phase2i4_maneuver_operational_threads_analysis
```

The summary preserves:

```text
maneuver accounting
propulsion boundary
correction aggregates
OEM solution boundary
five operational threads
Phase 2I closure criteria
guardrails
output paths
```

The processed product remains ignored from Git.

---

# Operational Thread Figure

Created:

```text
docs/assets/maneuvers/phase2i4_maneuver_operational_threads.svg
```

The figure presents the five integrated operational threads:

```text
Outbound adaptive trajectory management
Lunar flyby expected communications constraint
Return trajectory refinement
RTC2 communications interruption and recovery
Final correction to entry handoff
```

The figure also preserves the explicit warning that operational threads are not:

```text
console logs
Flight Director rationale trees
root-cause analyses
burn telemetry
complete targeting logic
```

---

# Independent Validator

Created:

```text
scripts/validation/validate_maneuver_operational_threads.py
```

The validator independently checks:

```text
dataset identity
summary identity
six correction opportunities
four executed corrections
two cancelled corrections
OTC1 cancellation semantics
OTC2 cancellation semantics
four unresolved correction engine assignments
OMS-E non-generalization
mission-phase classification
OEM comparison count
maneuver-assimilation boundary
communications thread classification
RTC2 causality boundary
RTC2 outage-scope boundary
five operational-thread identities
five operational-thread classifications
anomaly flags
RTC2 mission-continuation semantics
49.5-second firing-time aggregate
11.1 ft/s return scalar magnitude sum
3.38328 m/s SI conversion
net-vector non-computation
all-correction scalar non-computation
OEM interpretation boundary
CSV integrity
summary integrity
SVG integrity
all Phase 2I closure criteria
```

---

# Independent Validation Result

Correction accounting:

```text
planned:
6

executed:
4

cancelled:
2

outbound:
2 cancelled / 1 executed

return:
3 executed / 3 planned
```

Operational threads:

```text
outbound_adaptive_trajectory_management:
PASS

lunar_flyby_expected_communications_constraint:
PASS

return_trajectory_refinement:
PASS

rtc2_communications_interruption_and_recovery:
PASS

final_correction_to_entry_handoff:
PASS
```

Outbound cancellation semantics:

```text
OTC1 cancelled != failed burn:
PASS

OTC2 cancelled != failed burn:
PASS

propulsion anomaly inferred:
FALSE
```

Lunar blackout:

```text
EXPECTED_OPERATIONAL_CONSTRAINT:
PASS

anomaly:
FALSE
```

RTC2 integration:

```text
communications anomaly:
PASS

causal relationship:
NOT_ESTABLISHED

complete two-way outage:
NOT_ESTABLISHED

burn executed after recovery:
TRUE

burn failure:
FALSE

propulsion anomaly inferred:
FALSE
```

Propulsion assignment boundary:

```text
resolved correction assignments:
0

unresolved correction assignments:
4

confirmed OMS-E major burns generalized:
FALSE
```

Correction aggregates:

```text
known firing time:
49.5 s

return scalar delta-v sum:
11.1 ft/s

return scalar delta-v sum:
3.38328 m/s

net vector delta-v:
NOT COMPUTED

all-correction scalar delta-v:
NOT COMPUTED
```

OEM boundary:

```text
standard products:
9

common-epoch comparisons:
3

RTC3 later OEM:
NONE

maneuver assimilation established:
FALSE

navigation-error interpretation:
FALSE

measured-burn-delta-v interpretation:
FALSE
```

Products:

```text
thread CSV rows:
5

summary:
PASS

operational-thread figure:
PASS
```

---

# Phase 2I Closure Criteria

Maneuver plan vs execution:

```text
PASS
```

Cancelled vs failed semantics:

```text
PASS
```

Propulsion architecture:

```text
PASS
```

Burn-specific engine-assignment boundary:

```text
PASS
```

Mission-clock correlation:

```text
PASS
```

Lunar geometry correlation:

```text
PASS
```

Communications cross-phase context:

```text
PASS
```

Entry handoff correlation:

```text
PASS
```

OEM solution evolution:

```text
PASS
```

OEM-not-telemetry boundary:

```text
PASS
```

OEM-assimilation uncertainty:

```text
PASS
```

Scalar-vs-vector delta-v boundary:

```text
PASS
```

No unsupported thrust performance:

```text
PASS
```

Operational threads complete:

```text
PASS
```

Phase ready to close:

```text
PASS
```

---

# Permanent Interpretation Guardrails

## Guardrail 1

```text
cancelled correction
!=
failed burn
```

## Guardrail 2

```text
cancelled correction
!=
propulsion anomaly
```

## Guardrail 3

```text
expected lunar blackout
!=
anomaly
```

## Guardrail 4

```text
RTC2 communications anomaly
!=
propulsion anomaly
```

## Guardrail 5

```text
RTC2 communications anomaly
!=
failed burn
```

## Guardrail 6

```text
data-rate-change context
!=
causation
```

## Guardrail 7

```text
return-link loss
!=
proven complete two-way outage
```

## Guardrail 8

```text
propulsion architecture
!=
burn-specific engine assignment
```

## Guardrail 9

```text
confirmed OMS-E major maneuvers
!=
correction-burn engine assignment
```

## Guardrail 10

```text
scalar delta-v magnitude sum
!=
net vector delta-v
```

## Guardrail 11

```text
OEM solution difference
!=
navigation error
```

## Guardrail 12

```text
OEM solution difference
!=
measured burn delta-v
```

## Guardrail 13

```text
CREATION_DATE
!=
maneuver assimilation
```

## Guardrail 14

```text
public operational sequence
!=
full console log
```

## Guardrail 15

```text
public operational sequence
!=
Flight Director rationale tree
```

## Guardrail 16

```text
public operational sequence
!=
root-cause analysis
```

## Guardrail 17

No unsupported:

```text
thrust-derived acceleration
burn impulse
propellant consumption
engine efficiency
```

is inferred for the trajectory corrections.

---

# Engineering Significance

Phase 2I now provides a complete public-evidence reconstruction of Artemis II maneuver and propulsion operations.

The project can answer:

```text
What trajectory corrections were planned?

Which were cancelled?

Why did public reporting say they were cancelled?

Which corrections actually executed?

Where did they occur in the mission?

What correction magnitudes were publicly reported?

What propulsion architecture was available?

Which engine assignments can actually be confirmed?

How did communications context interact with maneuver operations?

How did public trajectory solutions evolve around maneuver epochs?

What cannot be inferred from those trajectory solutions?

How did the final correction lead into entry?
```

without manufacturing unavailable mission-control or propulsion telemetry.

---

# Phase 2I Final Status

Phase 2I.1:

```text
MANEUVER PLAN VS EXECUTION
COMPLETE
```

Phase 2I.2:

```text
ESM PROPULSION ARCHITECTURE / BURN SELECTION
COMPLETE
```

Phase 2I.3:

```text
MISSION-CLOCK / TRAJECTORY-SOLUTION CORRELATION
COMPLETE
```

Phase 2I.4:

```text
MANEUVER OPERATIONAL THREADS
COMPLETE
```

Overall Phase 2I:

```text
READY TO CLOSE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2J.1 — GNC Architecture and Evidence Model

## Goal

Phase 2J.1 establishes the public-evidence architecture for Artemis II guidance, navigation, and control.

The objective is to distinguish three different functions:

```text
NAVIGATION
Where am I, how am I moving, and which way am I pointed?

GUIDANCE
Where should the spacecraft go or point next?

CONTROL
How does the spacecraft make the commanded motion happen?
```

This phase also establishes what public Artemis II evidence is actually available before later phases attempt any deeper navigation, piloting, or guidance reconstruction.

The most important boundary is:

```text
SYSTEM CAPABILITY
!=
AS-FLOWN MEASUREMENT HISTORY
```

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_gnc_architecture.json
```

Dataset identifier:

```text
phase2j1_artemis_ii_gnc_architecture
```

Provenance:

```text
NASA_REPORTED_WITH_MISSIONLAB_CROSS_PHASE_ARCHITECTURE_CORRELATION
```

The dataset contains:

```text
GNC domain model
GNC&P flight-software architecture
onboard navigation sensors
external navigation support
manual-control interfaces
control effectors
Artemis II operational anchors
public-source availability boundaries
cross-phase interpretation boundaries
guardrails
```

---

# GNC Domain Separation

## Navigation

Question:

```text
Where am I?
How am I moving?
Which way am I pointed?
```

MissionLab classification:

```text
ESTIMATE_SPACECRAFT_POSITION_VELOCITY_ATTITUDE_AND_RELEVANT_RELATIVE_GEOMETRY
```

Navigation is not guidance.

Navigation is not control.

---

## Guidance

Question:

```text
Where should Orion go or point next?
```

MissionLab classification:

```text
DETERMINE_OR_RECEIVE_TRAJECTORY_ATTITUDE_AND_MISSION_OBJECTIVES
```

Guidance can consume navigation knowledge and produce objectives or commands, but Phase 2J.1 does not claim access to the complete Orion guidance algorithm.

---

## Control

Question:

```text
How does Orion follow the commanded trajectory or attitude?
```

MissionLab classification:

```text
CONVERT_COMMANDS_AND_ERRORS_INTO_EFFECTOR_ACTION
```

Control can include:

```text
crew hand-controller inputs
flight-software command processing
thruster or engine effectors
automated spacecraft control
```

but public system architecture does not expose the complete as-flown control-command history.

---

# GNC&P Flight Software

The public architecture supports:

```text
navigation-sensor inputs:
TRUE

pilot-control inputs:
TRUE

crew commands:
TRUE

ground commands:
TRUE

manual mode:
TRUE

automated mode:
TRUE

spacecraft-effector commanding:
TRUE
```

The software executes on:

```text
VEHICLE_MANAGEMENT_COMPUTERS
```

---

# Flight-Software Evidence Boundary

The current public MissionLab source set does not contain:

```text
flight-software source code
complete guidance algorithm
complete control law
complete guidance target history
complete controller input history
```

Therefore:

```text
public GNC architecture
!=
flight-software implementation
```

and:

```text
manual-control mode name
!=
control-law reconstruction
```

---

# Onboard Navigation Architecture

Phase 2J.1 identifies six onboard navigation sensor classes:

```text
1. Star Tracker
2. Inertial Measurement Unit
3. GPS Receiver
4. Barometric Altimeter Assembly
5. Optical Navigation Camera
6. Sun Sensor
```

The architecture is publicly documented.

The raw Artemis II histories from these systems are not present in the current curated source set.

---

# Star Tracker

Sensor ID:

```text
star_tracker
```

Measurement domain:

```text
ATTITUDE
```

Role:

```text
COMPARE_STAR_FIELD_IMAGES_WITH_STAR_CATALOG_TO_ESTIMATE_SPACECRAFT_ORIENTATION
```

Public architecture:

```text
AVAILABLE
```

Raw Artemis II star-tracker measurement history:

```text
NOT AVAILABLE IN CURRENT SOURCE SET
```

Therefore:

```text
star-tracker capability
!=
as-flown attitude measurement history
```

---

# Inertial Measurement Unit

Sensor ID:

```text
imu
```

Measurement domain:

```text
ROTATION_RATE_AND_BODY_ACCELERATION
```

Each public-described IMU includes:

```text
3 gyro axes
3 accelerometer axes
```

The inertial measurements support onboard navigation quantities including:

```text
position
velocity
attitude
```

Raw Artemis II IMU history:

```text
NOT AVAILABLE IN CURRENT SOURCE SET
```

Therefore MissionLab does not reconstruct:

```text
gyro time history
accelerometer time history
IMU biases
navigation filter propagation
IMU covariance
```

from architecture descriptions alone.

---

# GPS Receiver

Sensor ID:

```text
gps_receiver
```

Measurement domain:

```text
POSITION_AND_VELOCITY
```

Public mission-phase role includes:

```text
ASCENT
LOW_EARTH_ORBIT
REENTRY
```

Deep-space primary-navigation role:

```text
FALSE
```

Raw Artemis II GPS history:

```text
NOT AVAILABLE IN CURRENT SOURCE SET
```

---

# Barometric Altimeter Assembly

Sensor ID:

```text
barometric_altimeter
```

Measurement domain:

```text
ALTITUDE_FROM_ATMOSPHERIC_PRESSURE
```

Role:

```text
BACKUP_ALTITUDE_VALUE_FOR_ENTRY_DEPLOYMENT_EVENTS
```

Mission contexts include:

```text
ASCENT
REENTRY
```

Raw Artemis II barometric-altimeter history:

```text
NOT AVAILABLE IN CURRENT SOURCE SET
```

This sensor is part of the public navigation architecture but is not used in Phase 2J.1 to reconstruct an entry altitude profile.

Detailed entry reconstruction remains separated from this architectural phase.

---

# Optical Navigation Camera

Sensor ID:

```text
optical_navigation_camera
```

Measurement domain:

```text
CELESTIAL_RANGE_AND_BEARING
```

Public role:

```text
USE_EARTH_AND_MOON_IMAGE_SIZE_AND_POSITION_FOR_RANGE_AND_BEARING_INFORMATION
```

Emergency-return role:

```text
TRUE
```

Autonomous lost-communications role reported:

```text
TRUE
```

Raw Artemis II optical-navigation measurements:

```text
NOT AVAILABLE IN CURRENT SOURCE SET
```

Therefore MissionLab does not derive an as-flown optical-navigation solution from architecture documentation.

---

# Sun Sensor

Sensor ID:

```text
sun_sensor
```

Measurement domain:

```text
SUN_DIRECTION
```

Role:

```text
DETERMINE_SUN_DIRECTION_DURING_EMERGENCY_SAFE_MODE_FOR_POWER_POSITIVE_POINTING
```

Primary trajectory navigation sensor:

```text
FALSE
```

Raw Artemis II Sun-sensor history:

```text
NOT AVAILABLE IN CURRENT SOURCE SET
```

---

# External Navigation Support

System:

```text
DEEP_SPACE_NETWORK_TRACKING
```

Measurement domain:

```text
GROUND_BASED_DEEP_SPACE_ORBIT_DETERMINATION
```

Onboard sensor:

```text
FALSE
```

Public role:

```text
SENSITIVE_COMMUNICATION_SIGNAL_MEASUREMENTS_SUPPORT_SPACECRAFT_LOCATION_DETERMINATION_OUTSIDE_GPS_RANGE
```

Raw Artemis II DSN tracking observables in the current curated source set:

```text
NOT AVAILABLE
```

Permanent boundary:

```text
DSN orbit determination
!=
onboard sensor measurement
```

---

# AROW / OEM Navigation Boundary

MissionLab already contains NASA flight-derived public OEM trajectory products.

These products provide:

```text
public trajectory state solutions
```

They do not provide:

```text
Orion onboard navigation filter state history
```

Permanent rule:

```text
AROW/OEM state vector
!=
onboard navigation-filter state vector
```

This distinction is critical for future Phase 2J.3 work.

---

# Manual-Control Architecture

Two crew control interfaces are represented.

---

# Rotational Hand Controller

Short name:

```text
RHC
```

Command domain:

```text
ATTITUDE
```

Commanded axes:

```text
ROLL
PITCH
YAW
```

The RHC is not modeled as a direct thruster switch.

Instead:

```text
RHC input
↓
GNC flight software
↓
effector selection
```

---

# Translational Hand Controller

Short name:

```text
THC
```

Command domain:

```text
TRANSLATION
```

Commanded axes:

```text
FORWARD / BACK
UP / DOWN
LEFT / RIGHT
```

Again:

```text
THC input
!=
direct individual thruster command
```

The command is processed through GNC flight software.

---

# Manual-Control Command Path

MissionLab represents the public architecture as:

```text
CREW_CONTROLLER_INPUT
↓
GNC_FLIGHT_SOFTWARE
↓
EFFECTOR_SELECTION
↓
RCS_THRUSTER_COMMAND
```

This architecture does not provide:

```text
controller deflection time history
individual thruster command history
control-law gains
control-error history
attitude-error history
```

---

# Control Effectors

Phase 2J.1 cross-checks Phase 2I propulsion architecture.

## Main Engine

```text
OMS-E
count = 1
```

Role:

```text
MAJOR_IN_SPACE_VELOCITY_CHANGE
```

Burn-specific trajectory-correction assignment implied:

```text
FALSE
```

---

## Auxiliary Engines

```text
R-4D-11
count = 8
```

Role:

```text
ORBITAL_AND_TRAJECTORY_CORRECTION_CAPABILITY
```

Burn-specific correction assignment implied:

```text
FALSE
```

---

## Reaction-Control System

```text
RCS
count = 24
```

Role:

```text
ATTITUDE_TRANSLATION_AND_FINE_CONTROL
```

Exact as-flown thruster sequence available:

```text
FALSE
```

---

# Phase 2I Boundary Preservation

Phase 2I ended with four unresolved correction-burn engine assignments:

```text
OTC3
RTC1
RTC2
RTC3
```

Phase 2J.1 does not resolve them.

Permanent rule:

```text
GNC architecture
!=
burn-specific propulsion assignment
```

Therefore:

```text
correction-burn engine assignment resolved by GNC architecture:
FALSE
```

---

# Artemis II Operational Anchor 1 — Proximity Operations

Event:

```text
proximity_operations_demonstration
```

Execution:

```text
COMPLETED
```

Date:

```text
2026-04-01
```

Duration:

```text
APPROXIMATELY 70 MINUTES
```

Authority:

```text
CREW_MANUAL_CONTROL
```

Reference target:

```text
DETACHED ICPS
```

Activities:

```text
CONTROLLED APPROACH
CONTROLLED RETREAT
```

Onboard navigation sensors used:

```text
TRUE
```

Reaction-control thrusters used:

```text
TRUE
```

Automated departure burn afterward:

```text
TRUE
```

---

# Proximity-Operations Evidence Boundary

The public report establishes that:

```text
manual relative maneuvering occurred
onboard navigation sensors were used
RCS thrusters were used
automated departure followed
```

It does not expose:

```text
sensor measurement history
relative-state filter history
exact controller inputs
exact individual thruster sequence
complete approach guidance law
complete departure guidance law
```

---

# Docking-Camera Measurement Context

The proximity-operations public evidence also includes docking-camera measurements during departure.

MissionLab classifies this as:

```text
ENGINEERING POSITIONING MEASUREMENT CONTEXT
```

for future rendezvous-navigation knowledge.

Phase 2J.1 does not promote the docking camera to:

```text
CONFIRMED PRIMARY CLOSED_LOOP ARTEMIS II NAVIGATION SENSOR
```

without explicit evidence that it served that role.

Permanent boundary:

```text
engineering measurement context
!=
confirmed closed-loop navigation input
```

---

# Artemis II Operational Anchor 2 — Flight Day 4 Manual Piloting

Event:

```text
flight_day_4_manual_piloting
```

Execution:

```text
COMPLETED
```

Date:

```text
2026-04-04
```

Duration:

```text
41 MINUTES
```

Crew participants represented in the source-backed dataset:

```text
Christina Koch
Jeremy Hansen
```

Control modes tested:

```text
SIX_DEGREES_OF_FREEDOM
THREE_DEGREES_OF_FREEDOM
```

---

# 6-DOF / 3-DOF Boundary

The public event establishes that these control modes were tested.

It does not expose:

```text
mode implementation
control-law gains
rate-command logic
attitude-command logic
translation-command logic
thruster allocation algorithm
individual firing sequence
```

Therefore:

```text
6-DOF / 3-DOF mode name
!=
reconstructed control algorithm
```

---

# Artemis II Operational Anchor 3 — Flight Day 8

Event:

```text
flight_day_8_manual_piloting
```

Planned date:

```text
2026-04-08
```

Planned objectives included:

```text
CENTER_DESIGNATED_TARGET
GUIDE_TO_TAIL_TO_SUN_ATTITUDE
```

Execution status:

```text
FOREGONE
```

Performed:

```text
FALSE
```

Permanent rule:

```text
planned activity
!=
executed activity
```

MissionLab must never present this manual-control demonstration as flown.

---

# Current Public Source-Set Availability

Available:

```text
sensor architecture
sensor roles
GNC&P flight-software architecture
manual-control architecture
as-flown manual-control event sequence
6-DOF / 3-DOF execution evidence
```

Not available in the current curated source set:

```text
exact thruster command history
attitude time series
raw IMU history
raw star-tracker history
raw GPS history
raw barometric-altimeter history
raw optical-navigation history
raw Sun-sensor history
raw DSN tracking observables
full navigation-filter state history
navigation covariance history
guidance-target history
complete flight-control law
manual controller input history
Flight Director GNC rationale tree
```

---

# Important Meaning of "Not Available"

In Phase 2J.1:

```text
NOT AVAILABLE
```

means:

```text
NOT ESTABLISHED IN THE CURRENT CURATED MISSIONLAB PUBLIC SOURCE SET
```

It does not mean:

```text
NO SUCH RECORD EXISTS ANYWHERE
```

This distinction is preserved in the evidence-boundary figure.

---

# Cross-Phase Boundaries

## Boundary 1

```text
AROW/OEM state vector
!=
onboard navigation-filter state
```

Status:

```text
FALSE equivalence
```

---

## Boundary 2

```text
DSN orbit determination
!=
onboard sensor measurement
```

Status:

```text
FALSE equivalence
```

---

## Boundary 3

```text
propulsion architecture
!=
exact as-flown control-effector history
```

Status:

```text
FALSE equivalence
```

---

## Boundary 4

```text
trajectory-correction outcome
!=
guidance-command history
```

Status:

```text
FALSE equivalence
```

---

## Boundary 5

```text
GNC architecture
!=
correction-burn engine assignment
```

Status:

```text
FALSE equivalence
```

---

# Processed Architecture Table

Generated:

```text
data/processed/gnc/gnc_architecture_components.csv
```

Rows:

```text
13
```

Composition:

```text
1 GNC&P flight-software architecture row
6 onboard navigation sensor rows
1 external DSN support row
2 crew controller rows
3 control-effector rows
```

The processed file remains ignored from Git.

---

# Evidence-Boundary Table

Generated:

```text
data/processed/gnc/gnc_evidence_boundaries.csv
```

Rows:

```text
21
```

Each row records whether a particular evidence category is available in the current public MissionLab source set.

The processed file remains ignored from Git.

---

# Processed Summary

Generated:

```text
data/processed/gnc/gnc_architecture_summary.json
```

Product identifier:

```text
phase2j1_gnc_architecture_analysis
```

The summary contains:

```text
domain counts
sensor counts
external-support counts
manual-controller counts
effector counts
operational anchors
source-set boundaries
cross-phase boundaries
guardrails
output paths
```

The processed file remains ignored from Git.

---

# GNC Architecture Figure

Created:

```text
docs/assets/gnc/phase2j1_gnc_architecture.svg
```

The figure separates:

```text
NAVIGATION
GUIDANCE
CONTROL
```

and shows the high-level information flow:

```text
navigation knowledge
↓
guidance objectives
↓
control / effector action
```

It explicitly states that architecture does not establish the complete as-flown histories.

---

# Evidence-Boundary Figure

Created:

```text
docs/assets/gnc/phase2j1_gnc_evidence_boundary.svg
```

The figure displays the availability status for the 21 evidence categories used in this phase.

It also explicitly defines:

```text
NOT AVAILABLE
```

as referring only to the current curated public MissionLab source set.

---

# Independent Validator

Created:

```text
scripts/validation/validate_gnc_architecture.py
```

The validator independently checks:

```text
dataset identity
summary identity
seven curated NASA sources
canonical NASA URLs
GNC domain decomposition
flight-software architecture
six onboard sensor classes
GPS deep-space boundary
OpNav emergency-return role
Sun-sensor role
DSN external-navigation boundary
RHC command domain
THC command domain
manual-controller software path
propulsion-effector counts
OMS-E non-generalization
three operational anchors
proximity-operations completion
proximity-operations duration semantics
Flight Day 4 completion
41-minute manual test
6-DOF / 3-DOF evidence
Flight Day 8 foregone status
docking-camera evidence boundary
21 evidence-availability categories
Phase 2I engine-assignment preservation
component CSV integrity
boundary CSV integrity
summary integrity
SVG integrity
cross-phase non-inference guardrails
```

---

# Independent Validation Result

GNC decomposition:

```text
navigation:
PASS

guidance:
PASS

control:
PASS
```

GNC&P flight software:

```text
navigation-sensor inputs:
PASS

pilot-control inputs:
PASS

crew commands:
PASS

ground commands:
PASS

manual + automated modes:
PASS

effector commanding:
PASS
```

Onboard navigation architecture:

```text
sensor classes:
6

star tracker:
PASS

IMU:
PASS

GPS:
PASS

barometric altimeter:
PASS

optical navigation camera:
PASS

Sun sensor:
PASS
```

External support:

```text
DSN tracking:
PASS

onboard sensor:
FALSE
```

Manual control:

```text
RHC -> attitude:
PASS

THC -> translation:
PASS

direct thruster switches:
FALSE

exact controller history public:
FALSE

exact thruster history public:
FALSE
```

Control-effectors cross-check:

```text
OMS-E:
1

auxiliary:
8

RCS:
24

correction engine assignment inferred:
FALSE
```

Operational anchors:

```text
Proximity operations:
COMPLETED
approximately 70 min

Flight Day 4:
COMPLETED
41 min
6-DOF / 3-DOF PASS

Flight Day 8:
FOREGONE
```

Evidence boundaries:

```text
raw sensor histories:
NOT AVAILABLE

attitude time series:
NOT AVAILABLE

navigation-filter state history:
NOT AVAILABLE

navigation covariance:
NOT AVAILABLE

guidance-target history:
NOT AVAILABLE

complete control law:
NOT AVAILABLE

manual controller time history:
NOT AVAILABLE
```

Cross-phase interpretation:

```text
AROW/OEM state = onboard filter state:
FALSE

DSN tracking = onboard sensor:
FALSE

propulsion architecture = exact effector history:
FALSE

maneuver outcome = guidance command history:
FALSE

Phase 2I unresolved assignments preserved:
PASS
```

Products:

```text
architecture component CSV rows:
13

evidence boundary CSV rows:
21

summary:
PASS

architecture figure:
PASS

evidence-boundary figure:
PASS
```

Final validation:

```text
PASS
```

---

# Phase 2J.1 Permanent Guardrails

## Guardrail 1

```text
sensor capability
!=
as-flown sensor measurement
```

## Guardrail 2

```text
AROW/OEM state vector
!=
onboard navigation-filter state
```

## Guardrail 3

```text
DSN orbit determination
!=
onboard sensor measurement
```

## Guardrail 4

```text
crew controller command
!=
published thruster-firing history
```

## Guardrail 5

```text
RCS architecture
!=
exact as-flown thruster sequence
```

## Guardrail 6

```text
manual piloting demonstration
!=
complete control-law disclosure
```

## Guardrail 7

```text
6-DOF / 3-DOF mode name
!=
reconstructed control algorithm
```

## Guardrail 8

```text
planned Flight Day 8 manual demonstration
!=
executed demonstration
```

## Guardrail 9

```text
trajectory-correction result
!=
public guidance-command history
```

## Guardrail 10

```text
public GNC architecture
!=
flight-software source code
```

## Guardrail 11

```text
public sensor descriptions
!=
navigation covariance history
```

## Guardrail 12

```text
public mission sequence
!=
Flight Director GNC rationale tree
```

## Guardrail 13

```text
docking-camera engineering measurements
!=
confirmed primary closed-loop navigation input
```

## Guardrail 14

```text
GNC architecture
!=
OTC3 / RTC1 / RTC2 / RTC3 engine assignment
```

---

# Engineering Significance

Phase 2J.1 gives MissionLab a defensible systems-level GNC model.

The project can now explain:

```text
what Navigation does
what Guidance does
what Control does
which sensors Orion carries
which navigation support comes from the ground
how crew controllers interface with the flight software
which propulsion effectors are available
which manual-control demonstrations actually occurred
which planned demonstration did not occur
what public evidence remains unavailable
```

without pretending to possess:

```text
raw sensor telemetry
onboard navigation-filter state history
flight-software internals
navigation covariance
guidance-target history
controller histories
individual thruster firing logs
```

This is the required evidence foundation for the next two GNC subphases.

---

# Phase 2J.1 Status

GNC domain model:

```text
PASS
```

GNC&P architecture:

```text
PASS
```

Onboard navigation architecture:

```text
PASS
```

External DSN boundary:

```text
PASS
```

Manual-control architecture:

```text
PASS
```

Propulsion cross-phase integration:

```text
PASS
```

Operational anchors:

```text
PASS
```

Evidence-availability model:

```text
PASS
```

Cross-phase interpretation boundaries:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2J.1 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2J.2 — Manual Piloting and Control-Mode Reconstruction

## Goal

Phase 2J.2 reconstructs the publicly documented Artemis II manual-control demonstrations and their relationship to Orion's Guidance, Navigation, and Control architecture.

The phase addresses four questions:

```text
What manual-control interfaces did the crew use?

What proximity-operations sequence was planned?

What parts of that sequence are actually confirmed as flown?

What can and cannot be inferred from the public 6-DOF / 3-DOF control-mode evidence?
```

The governing evidence boundary is:

```text
PREMISSION PLAN
!=
AS-FLOWN EVENT LOG
```

and:

```text
CONTROL-MODE LABEL
!=
CONTROL-LAW DISCLOSURE
```

---

# Permanent Reference Dataset

Created:

```text
data/reference/artemis_ii_manual_piloting_control_modes.json
```

Dataset identifier:

```text
phase2j2_artemis_ii_manual_piloting_control_modes
```

Provenance:

```text
NASA_REPORTED_WITH_MISSIONLAB_DERIVED_CLOCK_CORRELATION
```

Dependencies:

```text
data/config/mission.json

data/reference/artemis_ii_gnc_architecture.json

data/reference/artemis_ii_esm_propulsion_architecture.json
```

---

# Manual-Control Architecture

The manual-control architecture remains consistent with Phase 2J.1.

## Rotational Hand Controller

Short name:

```text
RHC
```

Command domain:

```text
ATTITUDE
```

Axes:

```text
ROLL
PITCH
YAW
```

---

## Translational Hand Controller

Short name:

```text
THC
```

Command domain:

```text
TRANSLATION
```

Axes:

```text
FORWARD / BACK
UP / DOWN
LEFT / RIGHT
```

---

# Manual-Control Command Path

The public architecture is represented as:

```text
CREW_CONTROLLER_INPUT
↓
GNC_FLIGHT_SOFTWARE
↓
EFFECTOR_SELECTION
↓
RCS_THRUSTER_COMMAND
```

Therefore:

```text
hand controller
!=
direct thruster switch
```

The crew requests vehicle motion through the controller interface.

The GNC flight software remains part of the command path and determines effector commanding.

---

# Manual-Control History Boundary

The current public source set does not contain:

```text
exact RHC input history
exact THC input history
exact individual thruster command history
complete control-law state history
thruster-allocation history
```

Therefore:

```text
controller command
!=
published individual thruster-firing history
```

and:

```text
reported RCS use
!=
exact RCS allocation sequence
```

---

# Premission Proximity-Operations Reference Sequence

The Artemis II public reference material provides a 17-step premission proximity-operations sequence.

MissionLab preserves it explicitly as:

```text
PREMISSION_PLAN
```

It is not classified as an as-flown event log.

The 17 reference steps are:

```text
01. PRE-SEPARATION
02. SEPARATION / DRIFT
03. 180° PITCH MANEUVER
04. NULL SEPARATION ΔV
05. COARSE HQ
06. APPROACH
07. HQ 10m EVAL #1
08. BACK AWAY
09. STATIONKEEP
10. ICPS MANEUVER
11. APPROACH #2
12. HQ 15m EVAL #2
13. MULTI-AXIS TEST
14. MANUAL BACK-OUT
15. TURN TO ATT BURN
16. AUX DEPARTURE
17. LONG RANGE FTO
```

---

# Premission Proximity Geometry

The source material contains several planned geometry statements.

The mission-update narrative includes:

```text
approximately 300 ft
```

for manual-control takeover context.

It also describes:

```text
about 30 ft
```

for close-range handling-quality evaluation context.

The SLS reference sequence separately contains:

```text
HQ 10m EVAL #1

HQ 15m EVAL #2
```

These values are preserved separately.

MissionLab does not force:

```text
30 ft
=
10 m
```

or:

```text
30 ft
=
15 m
```

because the sources use different descriptions and planning representations.

---

# Premission Geometry Boundary

All of the following are planning values:

```text
~300 ft
~30 ft
10 m
15 m
```

They are not promoted to:

```text
measured Artemis II as-flown relative range
```

Permanent rule:

```text
planned range gate
!=
measured achieved range
```

---

# As-Flown Proximity Operations

The public as-flown evidence confirms:

```text
execution:
COMPLETED

duration:
APPROXIMATELY 70 MINUTES

controlled approach:
CONFIRMED

controlled retreat:
CONFIRMED

onboard navigation sensors:
USED

reaction-control thrusters:
USED

automated departure:
CONFIRMED
```

Reference target:

```text
DETACHED ICPS
```

---

# As-Flown Sequence Boundary

The broader proximity demonstration was successfully completed.

That does not establish that every premission reference-guide step executed exactly as planned.

Permanent status:

```text
all 17 planned steps individually confirmed as flown:
FALSE
```

Therefore:

```text
successful demonstration completion
!=
proof of each planned step
```

---

# As-Flown Geometry Boundary

The current public evidence does not provide a complete relative-range time series.

Therefore the project does not claim that the spacecraft actually reached or stopped at measured values of:

```text
300 ft
30 ft
10 m
15 m
```

based solely on the planning documents.

Permanent statuses:

```text
planned 300 ft gate confirmed as measured flight value:
FALSE

planned 30 ft gate confirmed as measured flight value:
FALSE

planned 10 m evaluation confirmed as measured flight value:
FALSE

planned 15 m evaluation confirmed as measured flight value:
FALSE
```

---

# Unavailable As-Flown Proximity Histories

The current curated source set does not contain:

```text
exact relative-range time history
exact relative-velocity time history
exact attitude time history
exact RHC input history
exact THC input history
exact individual RCS-thruster history
```

This prevents MissionLab from reconstructing a second-by-second piloting trajectory or exact crew control-input sequence.

---

# Control-Authority Reconstruction

Phase 2J.2 represents three evidence-backed control-authority states.

## State 1

```text
AUTOMATED_PRE_MANUAL_PROXIMITY_OPERATIONS
```

Evidence scope:

```text
PREMISSION_ARCHITECTURE_AND_PLAN
```

Exact transition UTC:

```text
NOT AVAILABLE
```

---

## State 2

```text
CREW_MANUAL_PROXIMITY_OPERATIONS
```

Evidence scope:

```text
AS_FLOWN_CONFIRMED
```

Exact transition UTC:

```text
NOT AVAILABLE
```

---

## State 3

```text
AUTOMATED_DEPARTURE
```

Evidence scope:

```text
AS_FLOWN_CONFIRMED
```

Exact transition UTC:

```text
NOT AVAILABLE
```

The authority transition can therefore be reconstructed qualitatively:

```text
automated context
↓
crew manual proximity operations
↓
automated departure
```

but not with second-level transition timestamps.

---

# Automated Departure Boundary

The automated departure is confirmed as flown.

However:

```text
automated departure confirmed
!=
exact automation-transition timestamp
```

The public source set does not provide the exact instant when manual control ended and automated departure authority began.

---

# Docking-Camera Context

The proximity-operations planning material describes docking-camera positioning measurements during departure.

MissionLab classifies these as:

```text
FUTURE_RENDEZVOUS_NAVIGATION_ENGINEERING_KNOWLEDGE
```

The docking camera is not promoted in this phase to:

```text
CONFIRMED CLOSED-LOOP ARTEMIS II NAVIGATION INPUT
```

Permanent boundary:

```text
engineering positioning measurement
!=
confirmed closed-loop navigation input
```

---

# Flight Day 4 Manual Piloting

Execution:

```text
COMPLETED
```

Reported local start:

```text
2026-04-04 21:09 EDT
```

Source precision:

```text
MINUTE_LEVEL
```

NASA explicitly reported the local timezone as:

```text
EDT
```

The fixed source offset is:

```text
UTC-04:00
```

---

# Flight Day 4 UTC Conversion

Using the source-reported EDT offset:

```text
2026-04-04 21:09 EDT
+
4 hours
=
2026-04-05T01:09:00Z
```

Derived UTC:

```text
2026-04-05T01:09:00Z
```

---

# Flight Day 4 Mission Elapsed Time

Configured launch epoch:

```text
2026-04-01T22:35:12Z
```

Derived manual-piloting start MET:

```text
03:02:33:48
```

Interpretation:

```text
3 days
2 hours
33 minutes
48 seconds
after launch
```

---

# Flight Day 4 Duration

Reported duration:

```text
41 MINUTES
```

Derived end UTC:

```text
2026-04-05T01:50:00Z
```

Derived end MET:

```text
03:03:14:48
```

The end time is derived from:

```text
reported minute-level start
+
reported 41-minute duration
```

It is therefore not an independently observed source timestamp.

---

# Flight Day 4 Crew

The public source-backed dataset identifies:

```text
Christina Koch
Jeremy Hansen
```

as the crew members who took turns controlling Orion during this demonstration.

---

# Flight Day 4 Control Modes

Publicly reported mode labels:

```text
SIX_DEGREES_OF_FREEDOM

THREE_DEGREES_OF_FREEDOM
```

These mode labels are preserved exactly as evidence categories.

MissionLab does not use the labels to manufacture undocumented control behavior.

---

# 6-DOF Boundary

The public source confirms that a six-degrees-of-freedom thruster mode was tested.

The source set does not expose:

```text
complete six-DOF control algorithm
controller gains
axis-coupling logic
rate-command law
attitude-command law
translation-command law
thruster-allocation logic
individual firing history
```

Therefore:

```text
6-DOF mode label
!=
reconstructed 6-DOF control law
```

---

# 3-DOF Boundary

The public source also confirms that a three-degrees-of-freedom thruster mode was tested.

The source set does not disclose the implementation sufficiently to reconstruct:

```text
which state variables were explicitly controlled
complete axis-selection logic
control-law gains
thruster-allocation rules
command shaping
```

Therefore:

```text
3-DOF mode label
!=
reconstructed 3-DOF control law
```

---

# Flight Day 8 Planned Manual Demonstration

A later manual piloting demonstration was planned.

Reported planned local time:

```text
2026-04-08 22:55 EDT
```

Source precision:

```text
MINUTE_LEVEL_PLANNED_ANCHOR
```

Planned objectives represented in MissionLab:

```text
CENTER_DESIGNATED_TARGET

GUIDE_TO_TAIL_TO_SUN_ATTITUDE

COMPARE_SIX_DOF_AND_THREE_DOF_ATTITUDE_CONTROL_MODES
```

---

# Flight Day 8 Planned UTC Conversion

Using the source-reported EDT offset:

```text
2026-04-08 22:55 EDT
+
4 hours
=
2026-04-09T02:55:00Z
```

Derived planned UTC:

```text
2026-04-09T02:55:00Z
```

Derived planned MET:

```text
07:04:19:48
```

---

# Flight Day 8 Execution Status

Final status:

```text
FOREGONE
```

Performed:

```text
FALSE
```

Therefore:

```text
planned timestamp
!=
executed GNC event timestamp
```

and:

```text
planned demonstration
!=
as-flown manual-control data
```

No as-flown controller history can be generated from this event because the event was not performed.

---

# Time Conversion Policy

The initial inspection attempted to use:

```text
zoneinfo.ZoneInfo("America/New_York")
```

The local Windows / Anaconda environment did not have the external IANA tzdata package available.

Observed error:

```text
ZoneInfoNotFoundError:
No time zone found with key America/New_York
```

No repository change resulted from the failure.

The implementation was corrected to preserve the source's explicitly reported timezone label directly.

NASA reported:

```text
EDT
```

Therefore MissionLab uses:

```text
EDT = UTC-04:00
```

through Python's fixed-offset timezone support.

IANA tzdata dependency:

```text
FALSE
```

This is preferable for these particular source timestamps because it preserves the timezone semantics stated by the source and avoids an unnecessary dependency.

---

# Mission-Clock Correlation

Flight Day 4:

```text
reported:
2026-04-04 21:09 EDT

derived UTC:
2026-04-05T01:09:00Z

derived MET:
03:02:33:48

duration:
41 min

derived end UTC:
2026-04-05T01:50:00Z

derived end MET:
03:03:14:48

execution:
COMPLETED
```

Flight Day 8:

```text
reported planned:
2026-04-08 22:55 EDT

derived planned UTC:
2026-04-09T02:55:00Z

derived planned MET:
07:04:19:48

execution:
FOREGONE
```

---

# Processed Manual-Piloting Event Table

Generated:

```text
data/processed/gnc/manual_piloting_events.csv
```

Rows:

```text
3
```

Events:

```text
proximity_operations_demonstration

flight_day_4_manual_piloting

flight_day_8_manual_piloting
```

The processed file remains ignored from Git.

---

# Processed Proximity Plan Table

Generated:

```text
data/processed/gnc/proximity_plan_vs_as_flown.csv
```

Rows:

```text
17
```

Each row preserves:

```text
planned step number
source label
normalized identifier
premission-plan status
individual as-flown confirmation status
interpretation class
```

Every row remains:

```text
individually_confirmed_as_flown:
false
```

because the public as-flown report confirms the broader demonstration rather than each individual reference-guide step.

The processed file remains ignored from Git.

---

# Processed Summary

Generated:

```text
data/processed/gnc/manual_piloting_control_modes_summary.json
```

Product identifier:

```text
phase2j2_manual_piloting_control_modes_analysis
```

The summary preserves:

```text
premission step count
as-flown proximity status
Flight Day 4 clock correlation
Flight Day 8 planned clock correlation
evidence boundaries
guardrails
output paths
```

The processed file remains ignored from Git.

---

# Manual-Piloting Timeline Figure

Created:

```text
docs/assets/gnc/phase2j2_manual_piloting_timeline.svg
```

The figure distinguishes:

```text
Proximity Operations
COMPLETED

Flight Day 4 Manual Piloting
COMPLETED

Flight Day 8 Manual Piloting
FOREGONE
```

It also shows the control architecture:

```text
crew controller
↓
GNC flight software
↓
effector selection
↓
RCS
```

---

# Proximity Plan-vs-As-Flown Figure

Created:

```text
docs/assets/gnc/phase2j2_proximity_plan_vs_as_flown.svg
```

The figure explicitly separates:

```text
PREMISSION REFERENCE SEQUENCE
```

from:

```text
AS-FLOWN CONFIRMED EVIDENCE
```

This prevents the planned 17-step sequence from being visually or analytically misrepresented as an observed step-by-step flight log.

---

# Independent Validator

Created:

```text
scripts/validation/validate_manual_piloting_control_modes.py
```

The validator independently checks:

```text
dataset identity
Phase 2J.1 dependency identity
six NASA source records
canonical NASA URLs
EDT fixed-offset time policy
Flight Day 4 UTC conversion
Flight Day 4 MET conversion
Flight Day 4 derived end time
Flight Day 8 planned UTC conversion
Flight Day 8 planned MET conversion
Flight Day 8 foregone status
RHC command domain
THC command domain
manual command path
direct-thruster-switch boundary
17-step proximity reference sequence
source labels
300 ft planning context
30 ft planning context
10 m reference evaluation
15 m reference evaluation
geometry non-equivalence
as-flown proximity completion
70-minute duration semantics
approach / retreat evidence
navigation-sensor use
RCS use
automated departure
planned-vs-flown boundary
control-authority sequence
exact-transition-time boundary
6-DOF label
3-DOF label
control-law non-inference
event CSV integrity
proximity CSV integrity
summary integrity
SVG integrity
```

---

# Independent Validation Result

Manual-control architecture:

```text
RHC -> attitude:
PASS

THC -> translation:
PASS

direct thruster switching:
FALSE
```

Premission proximity reference:

```text
17 steps:
PASS

300 ft planning context:
PASS

30 ft planning context:
PASS

10 m evaluation:
PASS

15 m evaluation:
PASS

planning geometry treated as measured flight data:
FALSE

30 ft forced equal to 10 m / 15 m:
FALSE
```

As-flown proximity operations:

```text
completed:
PASS

approximately 70 minutes:
PASS

approach / retreat:
PASS

onboard navigation sensors:
PASS

RCS:
PASS

automated departure:
PASS

all 17 steps individually confirmed:
FALSE
```

Control authority:

```text
automated pre-manual context:
PASS

crew manual proximity operations:
PASS

automated departure:
PASS

exact transition times public:
FALSE
```

Flight Day 4:

```text
start UTC:
2026-04-05T01:09:00Z

start MET:
03:02:33:48

duration:
41 min

derived end UTC:
2026-04-05T01:50:00Z

derived end MET:
03:03:14:48

six-DOF label:
PASS

three-DOF label:
PASS

underlying algorithms reconstructed:
FALSE
```

Flight Day 8:

```text
planned UTC:
2026-04-09T02:55:00Z

planned MET:
07:04:19:48

execution:
FOREGONE

performed:
FALSE

planned timestamp treated as executed:
FALSE
```

Generated products:

```text
manual-piloting event CSV rows:
3

proximity reference CSV rows:
17

summary:
PASS

timeline figure:
PASS

plan-vs-as-flown figure:
PASS
```

Independent validation:

```text
PASS
```

---

# Permanent Phase 2J.2 Guardrails

## Guardrail 1

```text
premission proximity sequence
!=
as-flown step-by-step event log
```

## Guardrail 2

```text
planned range value
!=
measured as-flown range
```

## Guardrail 3

```text
~70-minute duration
!=
exact proximity start / stop timestamps
```

## Guardrail 4

```text
manual control
!=
direct individual-thruster switching
```

## Guardrail 5

```text
crew controller input
!=
individual thruster-firing history
```

## Guardrail 6

```text
reported RCS use
!=
exact thruster-allocation history
```

## Guardrail 7

```text
6-DOF mode label
!=
6-DOF control-law disclosure
```

## Guardrail 8

```text
3-DOF mode label
!=
3-DOF control-law disclosure
```

## Guardrail 9

```text
successful proximity demonstration
!=
proof all 17 planned steps executed
```

## Guardrail 10

```text
~300 ft / ~30 ft / 10 m / 15 m planning geometry
!=
confirmed as-flown relative-range history
```

## Guardrail 11

```text
30 ft narrative value
!=
silently forced equivalence with 10 m or 15 m reference step
```

## Guardrail 12

```text
automated departure confirmed
!=
exact manual-to-automatic transition time
```

## Guardrail 13

```text
Flight Day 8 planned demonstration
!=
executed demonstration
```

## Guardrail 14

```text
Flight Day 8 planned timestamp
!=
executed GNC event timestamp
```

## Guardrail 15

```text
docking-camera engineering measurement
!=
confirmed closed-loop navigation input
```

---

# Engineering Significance

Phase 2J.2 provides the first mission-operations-level reconstruction of how crew manual control fits inside Orion's broader GNC architecture.

MissionLab can now answer:

```text
Which controller governs rotation?

Which controller governs translation?

Does the crew directly switch individual thrusters?

What was the planned proximity-operations sequence?

What range gates were planning values?

What parts of proximity operations are actually confirmed as flown?

When did the Flight Day 4 manual demonstration begin?

How long did it last?

Which control-mode labels were tested?

Was the later Flight Day 8 demonstration executed?

Where did manual authority transition back to automation conceptually?

What control details remain unavailable publicly?
```

without inventing:

```text
controller deflections
attitude histories
relative-state histories
control gains
guidance laws
individual RCS firings
thruster-allocation logic
```

---

# Phase 2J.2 Status

Manual-control architecture:

```text
PASS
```

Premission proximity reference:

```text
PASS
```

Planning-geometry boundaries:

```text
PASS
```

As-flown proximity evidence:

```text
PASS
```

Control-authority reconstruction:

```text
PASS
```

Flight Day 4 mission-clock correlation:

```text
PASS
```

6-DOF / 3-DOF evidence boundary:

```text
PASS
```

Flight Day 8 plan/execution distinction:

```text
PASS
```

Independent validation:

```text
PASS
```

Phase 2J.2 implementation status:

```text
COMPLETE
```

Git workflow closure remains pending until the documented implementation is committed, pushed, and the working tree is verified clean.

---

# Phase 2J.3 — Navigation & State-Estimation Reconstruction

## Goal

Phase 2J.3 reconstructs the public Artemis II / Orion navigation architecture and the boundaries between:

```text
onboard navigation
ground navigation support
public trajectory products

@'

---

# Phase 2J.4 — GNC Operational Threads & Closure

## Goal

Phase 2J.4 integrates the completed Phase 2J architecture, manual-control, and navigation reconstructions into mission-facing Artemis II GNC operational threads.

The phase connects:

```text
navigation
guidance
control
crew manual authority
ground navigation support
propulsion context
trajectory corrections
entry handoff

```
---

# Documentation Repair Note — Phase 2J.3 / 2J.4 Tail

The previous append operation left the Engineering Log in a malformed Markdown state immediately after the Phase 2J.2 closure.

The malformed tail contained:

- an unclosed `text` code fence inside the beginning of Phase 2J.3;
- a literal PowerShell here-string marker;
- a partial Phase 2J.4 section;
- no complete Phase 2J.3 record;
- no complete Phase 2J.4 record;
- no Phase 2K integration record.

The malformed material above is retained as part of the historical file rather than deleted.

For documentation purposes, the malformed Phase 2J.3 / 2J.4 tail above is superseded by the corrected sections below.

The technical implementation itself was not invalidated by this Markdown formatting problem. Phase 2J.3 and Phase 2J.4 both passed their dedicated analyzers and independent validators before this documentation repair.

---

# Phase 2J.3 — Navigation & State-Estimation Reconstruction

## Goal

Phase 2J.3 reconstructs the publicly supportable Artemis II / Orion navigation architecture and establishes strict evidence boundaries between:

```text
ONBOARD NAVIGATION
GROUND NAVIGATION SUPPORT
PUBLIC MISSION TRAJECTORY PRODUCTS
```

The central objective is not to manufacture an Orion navigation-filter solution.

Instead, the phase establishes what can actually be demonstrated from public NASA, PDS, and AROW evidence and what remains unavailable.

The permanent state-product distinction is:

```text
ONBOARD_NAVIGATION_STATE
!=
GROUND_ORBIT_DETERMINATION
!=
AROW_PUBLIC_STATE_VECTOR
```

---

## Dependencies

Phase 2J.3 depends on three completed products:

```text
Phase 2J.1 — GNC Architecture & Evidence Model
Phase 2J.2 — Manual Piloting & Control-Mode Reconstruction
Phase 2I.3 — Maneuver / Public OEM Trajectory Correlation
```

Observed dependency checks:

```text
Phase 2J.1 GNC architecture: PASS
Phase 2J.2 manual-control reconstruction: PASS
Phase 2I.3 OEM trajectory correlation: PASS
```

---

## Reference Dataset

Created:

```text
data/reference/artemis_ii_navigation_state_estimation.json
```

Dataset identifier:

```text
phase2j3_artemis_ii_navigation_state_estimation
```

The reference dataset records:

- onboard navigation sensor architecture;
- external ground-navigation support;
- navigation-state product taxonomy;
- Artemis II as-flown optical-navigation evidence;
- proximity-operations navigation evidence;
- selected trajectory-correction navigation-monitoring evidence;
- AROW / OEM product interpretation boundaries;
- reconstructable and non-reconstructable state-estimation evidence;
- permanent anti-overclaim guardrails.

---

## Navigation Architecture

Six onboard navigation sensor classes are preserved from the Orion avionics architecture:

```text
star_tracker
imu
gps_receiver
barometric_altimeter
optical_navigation_camera
sun_sensor
```

Count:

```text
6
```

These are architecture-level sensor classes.

Their public existence and documented functions do not imply that complete raw Artemis II sensor histories are publicly available.

---

## Sensor Roles

### Star Tracker

Role:

```text
ATTITUDE KNOWLEDGE
```

The star tracker provides inertial attitude-reference information.

Public architecture documentation does not expose the complete Artemis II star-tracker measurement history.

---

### Inertial Measurement Unit

Role:

```text
ROTATION / ACCELERATION INPUTS
POSITION-VELOCITY-ATTITUDE PROPAGATION SUPPORT
```

The IMU supplies inertial measurements used by onboard navigation.

Not public:

```text
complete raw IMU history
bias-state history
filter innovation history
measurement accept/reject history
```

---

### GPS Receiver

Role:

```text
EARTH-PROXIMATE POSITION / VELOCITY INFORMATION
```

GPS is an onboard navigation capability.

It is not treated as the primary navigation source throughout deep-space flight.

---

### Barometric Altimeter

Role:

```text
PRESSURE-ALTITUDE INFORMATION
ENTRY / DEPLOYMENT BACKUP CONTEXT
```

Its inclusion in the architecture does not establish a complete as-flown barometric-altimeter time history.

---

### Optical Navigation Camera

Role:

```text
EARTH / MOON IMAGING
RANGE / BEARING NAVIGATION SUPPORT
EMERGENCY RETURN NAVIGATION CAPABILITY
```

The camera is identified publicly as:

```text
Pixelink Prometheus PL-D725
```

Installation context:

```text
starboard lower Crew Module Adapter
```

Artemis II public reporting confirms optical-navigation imagery of:

```text
Earth
Moon
```

A Flight Day 1 Earth image was publicly identified as optical-navigation imagery.

Permanent interpretation rule:

```text
IMAGE CAPTURE
!=
PROOF OF A SPECIFIC FILTER UPDATE
```

and:

```text
IMAGE
!=
ESTIMATOR RESIDUAL
!=
FILTER INNOVATION
```

---

### Sun Sensor

Role:

```text
SAFE-MODE SUN-DIRECTION KNOWLEDGE
```

The public architecture establishes capability.

It does not provide the complete Artemis II sun-sensor measurement history.

---

# Deep Space Network Boundary

External navigation support:

```text
DEEP_SPACE_NETWORK_TRACKING
```

Onboard sensor:

```text
FALSE
```

The Deep Space Network supports ground-based determination of spacecraft location using communication-signal measurements.

Permanent boundary:

```text
DSN GROUND TRACKING
!=
ONBOARD NAVIGATION SENSOR
```

and:

```text
GROUND NAVIGATION SUPPORT
!=
ORION ONBOARD NAVIGATION FILTER
```

---

# Navigation-State Product Taxonomy

Phase 2J.3 defines three separate evidence categories.

## 1. ONBOARD_NAVIGATION_STATE

Producer context:

```text
ORION_VEHICLE_MANAGEMENT_COMPUTERS
```

Role:

```text
Onboard spacecraft position, velocity, and attitude knowledge
computed from navigation inputs.
```

The complete Artemis II onboard navigation-state history is not publicly reconstructed.

---

## 2. GROUND_ORBIT_DETERMINATION

Producer context:

```text
GROUND_NAVIGATION_SUPPORT
```

Role:

```text
Ground-based determination of spacecraft location or trajectory
using measurements such as Deep Space Network observations.
```

Important terminology rule:

```text
GROUND_ORBIT_DETERMINATION
```

is a MissionLab normalized taxonomy category.

It is not claimed to be the exact official name of a released Artemis II NASA data product.

---

## 3. AROW_PUBLIC_STATE_VECTOR

Producer context:

```text
NASA_PUBLIC_MISSION_DATA_PRODUCT
```

Role:

```text
Public downloadable trajectory and state-vector information
describing Orion's location and motion.
```

AROW provides valuable public trajectory information.

However:

```text
AROW_PUBLIC_STATE_VECTOR
!=
PROVEN_ORION_ONBOARD_FILTER_STATE
```

and:

```text
AROW_PUBLIC_STATE_VECTOR
!=
PROVEN_COMPLETE_GROUND_NAVIGATION_SOLUTION
```

---

# Optical Navigation As-Flown Evidence

Artemis II public evidence supports:

```text
Earth optical-navigation imagery captured: TRUE
Moon optical-navigation imagery captured: TRUE
```

Not established:

```text
image capture proves estimator update: FALSE
```

Unavailable publicly:

```text
complete raw optical-navigation measurement history
measurement residual history
innovation history
filter update sequence
measurement weighting
measurement accept/reject history
```

---

# Proximity-Operations Navigation Evidence

The Artemis II proximity-operations demonstration provides an important as-flown navigation anchor.

Public reporting confirms:

```text
onboard navigation sensors used: TRUE
```

Public reporting does not establish:

```text
specific sensor set used at every instant
complete relative-position history
complete relative-velocity history
complete relative-state estimator history
```

Therefore:

```text
ARCHITECTURE + AS-FLOWN SENSOR USE
```

is supported.

A complete proximity-navigation solution is not.

---

# Trajectory-Correction Navigation Monitoring

Phase 2J.3 distinguishes confirmed as-flown monitoring from pre-burn planning/context.

## Confirmed As-Flown Examples

```text
RTC1
RTC3
```

Public reporting supports crew monitoring of spacecraft configuration and navigation information in connection with these correction operations.

---

## Pre-Burn / Planned Monitoring Context

```text
OTC3
RTC2
```

The public evidence for these cases is planning or pre-burn operational context.

This evidence is not silently promoted into a complete as-flown crew-display history.

---

## Display Boundary

Public evidence does not establish:

```text
exact displayed navigation variables
complete navigation-display time history
display values == complete onboard filter state
```

Permanent rule:

```text
CREW MONITORING NAVIGATION DATA
!=
COMPLETE ONBOARD NAVIGATION STATE
```

---

# AROW / OEM Solution-Evolution Boundary

Phase 2J.3 reuses the Phase 2I.3 public OEM maneuver audit.

Audited maneuver brackets:

```text
4
```

Maneuvers:

```text
OTC3
RTC1
RTC2
RTC3
```

Same-epoch public solution comparisons available:

```text
3
```

Each available comparison remains explicitly classified as:

```text
SOLUTION-TO-SOLUTION DIFFERENCE
```

and not:

```text
navigation error
measured burn delta-v
```

---

## OTC3 Creation-Time Guardrail

A particularly important evidence boundary comes from the public product:

```text
Artemis_II_OEM_2026_04_06_Pre-OTC3_to_EI.csv
```

Its creation timing relative to the maneuver does not prove that OTC3 was assimilated into that public solution.

Permanent rule:

```text
OEM CREATION TIME
!=
PROOF OF MANEUVER ASSIMILATION
```

Maneuver assimilation status from public evidence:

```text
NOT ESTABLISHED
```

---

# State-Estimation Evidence Boundary

## Publicly Supported

Phase 2J.3 records eight supported evidence categories:

```text
onboard navigation architecture
onboard sensor roles
DSN ground-tracking role
AROW public state vectors
AROW public ephemeris
as-flown Artemis II optical-navigation imagery
as-flown proximity-operations onboard navigation-sensor use
selected as-flown trajectory-correction navigation monitoring
```

Count:

```text
8
```

---

## Not Publicly Available / Not Established

Phase 2J.3 records twenty-one unavailable or unestablished categories:

```text
complete onboard navigation-state history
complete ground orbit-determination solution history
raw IMU history
raw star-tracker history
raw GPS history
raw barometric-altimeter history
raw sun-sensor history
complete raw optical-navigation measurement history
optical-navigation residual history
navigation-filter innovation history
navigation covariance history
filter-gain history
filter-bias-state history
sensor-selection history
measurement accept/reject history
complete crew navigation-display history
AROW == onboard filter state
AROW == complete ground navigation solution
OEM difference == navigation error
OEM difference == measured burn delta-v
OEM creation time == measurement or burn assimilation proof
```

Count:

```text
21
```

---

# What Phase 2J.3 Can Reconstruct

```text
NAVIGATION_ARCHITECTURE
SENSOR_MEASUREMENT_ROLES
MISSION_PHASE_CAPABILITY_CONTEXT
ONBOARD_VS_GROUND_NAVIGATION_BOUNDARY
PUBLIC_AROW_PRODUCT_BOUNDARY
AS_FLOWN_OPNAV_IMAGERY_EXISTENCE
AS_FLOWN_PROXIMITY_NAV_SENSOR_USE
SELECTED_AS_FLOWN_CREW_NAVIGATION_DATA_MONITORING_CONTEXT
OEM_SOLUTION_EVOLUTION_WITH_NON_INFERENCE_GUARDRAILS
```

---

# What Phase 2J.3 Cannot Reconstruct

```text
COMPLETE_ONBOARD_FILTER_STATE_HISTORY
COMPLETE_GROUND_ORBIT_DETERMINATION_SOLUTION_HISTORY
FILTER_COVARIANCE_HISTORY
FILTER_GAIN_HISTORY
MEASUREMENT_INNOVATION_HISTORY
SENSOR_BIAS_STATE_HISTORY
MEASUREMENT_ACCEPT_REJECT_HISTORY
EXACT_SENSOR_SELECTION_HISTORY
EXACT_OPNAV_ESTIMATOR_UPDATES
EXACT_DSN_NAVIGATION_SOLUTION_HISTORY
COMPLETE_CREW_NAVIGATION_DISPLAY_HISTORY
```

---

# Generated Products

Analyzer:

```text
scripts/analysis/analyze_navigation_state_estimation.py
```

Validator:

```text
scripts/validation/validate_navigation_state_estimation.py
```

Processed products:

```text
data/processed/gnc/navigation_state_product_taxonomy.csv
data/processed/gnc/navigation_evidence_boundaries.csv
data/processed/gnc/navigation_state_estimation_summary.json
```

Documentation figures:

```text
docs/assets/gnc/phase2j3_navigation_architecture.svg
docs/assets/gnc/phase2j3_state_product_boundaries.svg
```

Processed products remain ignored by Git.

---

# Validation

Observed analyzer completion:

```text
PHASE 2J.3 ANALYSIS COMPLETE
```

Independent validator result:

```text
Reference dataset: PASS
Phase 2J.1 dependency: PASS
Phase 2J.2 dependency: PASS
Phase 2I.3 dependency: PASS
Navigation sensor architecture: PASS
Deep Space Network boundary: PASS
Navigation-state product taxonomy: PASS
ONBOARD != GROUND != AROW boundary: PASS
AROW evidence boundary: PASS
Optical-navigation evidence: PASS
Proximity navigation evidence: PASS
Trajectory-correction monitoring boundary: PASS
OEM solution-evolution boundary: PASS
Generated taxonomy CSV: PASS
Generated evidence-boundary CSV: PASS
Generated summary JSON: PASS
Navigation architecture SVG: PASS
State-product boundary SVG: PASS
```

Final validator output:

```text
PHASE 2J.3 VALIDATION PASSED
```

A copy-artifact audit also explicitly checked for known fused-word corruption patterns in the permanent reference dataset and returned no matches.

`git diff --check` subsequently returned no errors.

A clean working tree was observed after Phase 2J.3 closure.

---

# Permanent Phase 2J.3 Guardrails

1. Navigation architecture is not navigation time history.
2. Sensor capability is not raw sensor telemetry.
3. DSN tracking is not an onboard sensor.
4. Ground navigation support is not Orion's onboard navigation filter.
5. AROW public state vectors are not proven onboard filter states.
6. AROW public state vectors are not proven complete ground-navigation solutions.
7. An optical-navigation image is not a filter innovation.
8. Image capture does not prove a specific estimator update.
9. Crew navigation monitoring does not expose the complete onboard state.
10. Public OEM products are not raw spacecraft telemetry.
11. OEM solution differences are not navigation error.
12. OEM solution differences are not measured burn delta-v.
13. OEM creation time does not prove maneuver assimilation.
14. Public product naming does not expose internal filter architecture.
15. Missing public residuals are not reconstructed synthetically.
16. Missing covariance histories are not inferred.
17. Missing bias states are not inferred.
18. Missing sensor-selection histories are not inferred.
19. Missing measurement accept/reject histories are not inferred.
20. Absence from the curated public evidence set is not proof that an operational record never existed.

---

# Engineering Significance

Phase 2J.3 establishes one of the most important scientific boundaries in MissionLab:

```text
PUBLIC TRAJECTORY PRODUCT
!=
ONBOARD NAVIGATION SOLUTION
```

This prevents later analyses from treating a convenient public trajectory file as hidden spacecraft telemetry.

The result is less sensational but substantially more defensible.

---

# Phase 2J.3 Status

```text
COMPLETE
```

---

# Phase 2J.4 — GNC Operational Threads & Closure

## Goal

Phase 2J.4 integrates the completed GNC architecture, manual-control reconstruction, navigation reconstruction, and maneuver context into mission-facing operational threads.

The purpose is to answer:

```text
How did navigation, guidance, control,
crew actions, ground support, and propulsion
interact during publicly reconstructable
Artemis II operations?
```

without manufacturing:

```text
filter histories
guidance algorithms
control laws
controller deflection histories
individual thruster histories
complete targeting logic
console decision histories
Flight Director rationale
```

---

# Dependencies

Integrated products:

```text
Phase 2J.1 — GNC Architecture & Evidence Model
Phase 2J.2 — Manual Piloting & Control-Mode Reconstruction
Phase 2J.3 — Navigation & State-Estimation Reconstruction
Phase 2I.4 — Maneuver Operational Threads
```

Observed:

```text
Dependencies: PASS
```

---

# Reference Dataset

Created:

```text
data/reference/artemis_ii_gnc_operational_threads.json
```

Dataset identifier:

```text
phase2j4_artemis_ii_gnc_operational_threads
```

---

# GNC Domain Model

Phase 2J preserves the fundamental decomposition:

## Navigation

Question:

```text
WHERE AM I?
HOW AM I MOVING?
HOW AM I POINTED?
```

Status:

```text
RECONSTRUCTED TO PUBLIC-EVIDENCE LIMIT
```

---

## Guidance

Question:

```text
WHERE SHOULD I GO OR POINT NEXT?
```

Status:

```text
ARCHITECTURE AND OPERATIONAL CONTEXT ONLY
```

Complete as-flown algorithm publicly available:

```text
FALSE
```

---

## Control

Question:

```text
HOW DO I COMMAND THE REQUIRED MOTION?
```

Status:

```text
ARCHITECTURE AND SELECTED AS-FLOWN CONTEXT ONLY
```

Complete as-flown control law publicly available:

```text
FALSE
```

---

# Core Architecture Preserved

Onboard navigation sensor classes:

```text
star_tracker
imu
gps_receiver
barometric_altimeter
optical_navigation_camera
sun_sensor
```

Count:

```text
6
```

External support:

```text
DEEP_SPACE_NETWORK_TRACKING
```

Onboard sensor:

```text
FALSE
```

Manual control path:

```text
CREW_CONTROLLER_INPUT
→
GNC_FLIGHT_SOFTWARE
→
EFFECTOR_SELECTION
→
RCS_THRUSTER_COMMAND
```

Hand controllers are not modeled as direct individual-thruster switches.

---

# Control Effectors

European Service Module / Orion control-effectors represented in the integrated GNC architecture:

```text
OMS-E main engine:             1
R-4D-11 auxiliary engines:    8
reaction-control engines:    24
```

Correction-burn engine assignments resolved:

```text
0
```

Unresolved:

```text
OTC3
RTC1
RTC2
RTC3
```

---

# Operational Thread 1 — Proximity Operations GNC

Classification:

```text
CREW_MANUAL_FLIGHT_TEST_WITH_AUTOMATED_DEPARTURE
```

Execution:

```text
COMPLETED
```

Approximate duration:

```text
70 min
```

Reference target:

```text
DETACHED ICPS
```

Publicly supportable operational progression:

```text
automated pre-manual context
→
onboard navigation-sensor use
→
crew-controlled approach
→
crew-controlled retreat
→
crew input through GNC flight software
→
RCS control
→
automated departure
```

Supported as flown:

```text
onboard navigation sensors used: TRUE
controlled approach: TRUE
controlled retreat: TRUE
reaction-control thrusters used: TRUE
automated departure: TRUE
```

Not publicly reconstructable:

```text
exact relative range history
exact relative velocity history
exact attitude history
exact RHC history
exact THC history
individual thruster-firing history
exact manual-to-automatic transition time
```

The 17-step premission proximity sequence remains planning/reference evidence and is not promoted into an as-flown event log.

---

# Operational Thread 2 — Flight Day 4 Manual Piloting

Execution:

```text
COMPLETED
```

Crew:

```text
Christina Koch
Jeremy Hansen
```

Reported local start:

```text
2026-04-04 21:09 EDT
```

Derived UTC:

```text
2026-04-05T01:09:00Z
```

Derived MET:

```text
03:02:33:48
```

Duration:

```text
41 min
```

Derived end:

```text
2026-04-05T01:50:00Z
```

Public mode labels:

```text
SIX_DEGREES_OF_FREEDOM
THREE_DEGREES_OF_FREEDOM
```

These mode names do not expose:

```text
controller gains
axis-coupling logic
command shaping
thruster-allocation logic
controller-deflection history
individual thruster history
```

---

# Operational Thread 3 — Deep-Space Navigation

This thread integrates:

```text
onboard inertial / attitude navigation
optical navigation
Deep Space Network support
public AROW trajectory products
```

Public evidence confirms:

```text
Earth optical-navigation imagery: TRUE
Moon optical-navigation imagery: TRUE
```

Deep Space Network:

```text
GROUND NAVIGATION SUPPORT
```

Onboard sensor:

```text
FALSE
```

Permanent boundary:

```text
ONBOARD_NAVIGATION_STATE
!=
GROUND_ORBIT_DETERMINATION
!=
AROW_PUBLIC_STATE_VECTOR
```

Unavailable:

```text
complete onboard filter-state history
complete ground OD solution history
navigation covariance history
filter gain history
measurement innovation history
sensor bias-state history
measurement accept/reject history
exact sensor-selection history
exact optical-navigation update history
```

---

# Operational Thread 4 — Trajectory-Correction GNC

Executed corrections integrated:

```text
OTC3
RTC1
RTC2
RTC3
```

## OTC3

Public time:

```text
2026-04-06T03:03:00Z
```

Duration:

```text
17.5 s
```

Public delta-v:

```text
UNAVAILABLE
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

Monitoring evidence:

```text
PRE-BURN OPERATIONAL CONTEXT
```

---

## RTC1

Public time:

```text
2026-04-08T00:03:00Z
```

Duration:

```text
15 s
```

Reported delta-v:

```text
1.6 ft/s
```

Navigation monitoring:

```text
AS_FLOWN CONFIRMED
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

## RTC2

Public time:

```text
2026-04-10T02:53:00Z
```

Duration:

```text
9 s
```

Reported delta-v:

```text
5.3 ft/s
```

Monitoring evidence:

```text
PRE-BURN GNC / PROPULSION CONTEXT
```

Communications were recovered before execution.

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

## RTC3

Public time:

```text
2026-04-10T18:53:00Z
```

Duration:

```text
8 s
```

Reported delta-v:

```text
4.2 ft/s
```

Navigation monitoring:

```text
AS_FLOWN CONFIRMED
```

Engine assignment:

```text
UNRESOLVED_AS_FLOWN
```

---

# Public OEM Context

Maneuver brackets audited:

```text
4
```

Same-epoch solution comparisons available:

```text
3
```

Permanent interpretation:

```text
OEM DIFFERENCE
!=
NAVIGATION ERROR
```

```text
OEM DIFFERENCE
!=
MEASURED BURN DELTA-V
```

```text
OEM CREATION TIME
!=
PROOF OF MANEUVER ASSIMILATION
```

Assimilation status:

```text
NOT ESTABLISHED
```

---

# Operational Thread 5 — Final Correction to Entry Handoff

RTC3:

```text
2026-04-10T18:53:00Z
```

Entry Interface public anchor:

```text
2026-04-10T23:53:00Z
```

Derived public-clock interval:

```text
18,000 s
5 h 00 min
```

This establishes a mission-clock relationship.

It does not establish:

```text
final onboard navigation state
entry-targeting covariance
entry-targeting algorithm
entry guidance-command history
bank-command history
entry control-command history
```

Detailed entry reconstruction remains downstream scope.

---

# Phase 2J.4 Reconstructable Scope

Count:

```text
17
```

Includes:

```text
GNC domain decomposition
onboard navigation-sensor architecture
DSN external-support role
onboard-vs-ground-vs-public-state boundary
manual controller command domains
crew-controller-to-GNC-to-RCS command path
control-effector architecture
proximity control-authority sequence
as-flown proximity navigation-sensor use
as-flown RCS use
Flight Day 4 manual-piloting context
6-DOF and 3-DOF public mode labels
as-flown optical-navigation imagery
selected correction navigation monitoring
trajectory-correction operational sequence
public OEM solution-evolution boundary
final correction-to-entry public-clock handoff
```

---

# Phase 2J.4 Non-Reconstructable Scope

Count:

```text
24
```

Includes:

```text
complete onboard filter history
complete ground OD history
raw navigation-sensor histories
filter covariance / gain / innovation / bias histories
measurement accept/reject history
exact sensor-selection history
complete guidance algorithm
complete guidance-command history
complete manual control law
complete automatic control law
controller-gain history
controller-deflection history
thruster-allocation logic
individual thruster-firing history
correction-burn engine assignments
complete maneuver-targeting logic
burn-vector directions
complete crew navigation-display history
flight-control console decision history
Flight Director rationale tree
detailed as-flown entry guidance
```

---

# Generated Products

Analyzer:

```text
scripts/analysis/analyze_gnc_operational_threads.py
```

Validator:

```text
scripts/validation/validate_gnc_operational_threads.py
```

Processed products:

```text
data/processed/gnc/gnc_operational_threads.csv
data/processed/gnc/phase2j_closure_matrix.csv
data/processed/gnc/gnc_operational_threads_summary.json
```

Figures:

```text
docs/assets/gnc/phase2j4_gnc_operational_threads.svg
docs/assets/gnc/phase2j4_phase2j_closure.svg
```

---

# Validation

Observed analyzer result:

```text
Dependencies: PASS
GNC domains: PASS
Six-sensor navigation architecture: PASS
DSN ground-support boundary: PASS
ONBOARD != GROUND != AROW boundary: PASS
Manual-control architecture: PASS
Proximity-operations GNC thread: PASS
Flight Day 4 manual-piloting thread: PASS
Deep-space navigation thread: PASS
Trajectory-correction GNC thread: PASS
Final correction-to-entry handoff: PASS
Correction-engine assignment uncertainty: PASS
OEM non-inference boundary: PASS
Phase 4 entry-guidance deferral: PASS
Phase 7 mission-control deferral: PASS
```

Observed counts:

```text
Operational threads: 5
Reconstructable items: 17
Not reconstructable items: 24
```

Analyzer completion:

```text
PHASE 2J.4 ANALYSIS COMPLETE
```

Independent validator:

```text
Reference dataset: PASS
2J.1 architecture integration: PASS
2J.2 manual/proximity integration: PASS
2J.3 navigation integration: PASS
2I.4 maneuver integration: PASS
Five GNC operational threads: PASS
State-product boundary: PASS
Correction-engine uncertainty: PASS
OEM non-inference boundary: PASS
Final correction-to-entry boundary: PASS
Phase 4 / Phase 7 deferred scope: PASS
Processed products: PASS
Documentation figures: PASS
```

Final result:

```text
PHASE 2J.4 VALIDATION PASSED
```

Observed commit:

```text
190d7e9 Complete Artemis II GNC operational reconstruction
```

The first push attempt reported that the local branch did not yet have an upstream tracking branch.

No claim about the subsequent remote-push result is made here until that output is explicitly observed.

---

# Phase 2J Closure

Subphases:

```text
2J.1 — GNC Architecture & Evidence Model
COMPLETE

2J.2 — Manual Piloting & Control-Mode Reconstruction
COMPLETE

2J.3 — Navigation & State-Estimation Reconstruction
COMPLETE

2J.4 — GNC Operational Threads & Closure
COMPLETE
```

Overall Phase 2J status:

```text
COMPLETE
```

Phase 2J establishes an evidence-backed bridge between:

```text
spacecraft GNC architecture
→
navigation capability
→
crew manual authority
→
ground navigation support
→
maneuver operations
→
entry handoff
```

without pretending that public mission reporting exposes Orion's complete onboard navigation or control implementation.

---

# Phase 2K — Phase 2 Integration & Closure

## Goal

Phase 2K integrates the completed Phase 2 mission-operations work across:

```text
FLIGHT DYNAMICS
COMMUNICATIONS
PROPULSION
MANEUVERS
GUIDANCE / NAVIGATION / CONTROL
```

The purpose is to verify that these domains form one internally consistent Artemis II mission-operations reconstruction on a common mission clock.

Phase 2K does not create hidden flight data.

It connects already validated products and checks that the evidence boundaries established in earlier work remain intact when those products are combined.

---

# Reference Dataset

Created:

```text
data/reference/artemis_ii_phase2_integrated_operations.json
```

Dataset identifier:

```text
phase2k_artemis_ii_phase2_integrated_operations
```

Phase:

```text
2K
```

Phase name:

```text
Phase 2 Integration & Closure
```

---

# Integrated Dependencies

Phase 2K integrates:

```text
data/reference/artemis_ii_maneuver_trajectory_correlation.json

data/reference/artemis_ii_communications_operational_threads.json

data/reference/artemis_ii_esm_propulsion_architecture.json

data/reference/artemis_ii_maneuver_operational_threads.json

data/reference/artemis_ii_gnc_operational_threads.json
```

These represent the completed Phase 2 domains:

```text
flight dynamics
communications
propulsion
maneuvers
GNC
```

---

# Phase 2 Domain Status

Each integrated domain reached:

```text
COMPLETE_TO_PHASE2_SCOPE
```

## Flight Dynamics

Integrated capabilities include:

```text
shared mission clock
Earth-Moon-Orion trajectory context
lunar sphere-of-influence context
pericynthion geometry
public OEM solution evolution
trajectory-correction event correlation
entry-handoff clock context
```

---

## Communications

Integrated capabilities include:

```text
communications event catalog
mission-clock correlation
lunar-occultation context
DSN geometric context
optical-communications context
expected blackout thread
unexpected return-link anomaly thread
communications recovery / mission-continuation thread
```

---

## Propulsion

Integrated capabilities include:

```text
ESM propulsion architecture
OMS-E architecture
auxiliary-engine architecture
RCS architecture
confirmed major-maneuver assignments
correction-burn assignment boundary
```

---

## Maneuvers

Integrated capabilities include:

```text
planned-vs-executed corrections
cancellation decisions
executed-correction timeline
return delta-v magnitude context
public OEM correlation
operational maneuver threads
```

---

## GNC

Integrated capabilities include:

```text
GNC domain model
onboard navigation architecture
ground-navigation support boundary
manual-control architecture
proximity-operations GNC
manual-piloting context
optical-navigation context
trajectory-correction navigation monitoring
final correction-to-entry handoff
```

---

# Shared Mission Clock

Phase 2K integrates eleven mission-clock anchors:

```text
1. Launch
2. OTC3
3. Lunar SOI entry
4. Pericynthion
5. Reported Earthrise
6. Lunar SOI exit
7. RTC1
8. RTC2
9. RTC3
10. Entry Interface
11. Splashdown
```

---

## Launch

```text
2026-04-01T22:35:12Z
```

Provenance:

```text
NASA REPORTED / configured public mission epoch
```

---

## OTC3

```text
2026-04-06T03:03:00Z
```

Precision:

```text
MINUTE LEVEL
```

---

## Lunar SOI Entry

```text
2026-04-06T04:38:07.532302Z
```

Provenance:

```text
MISSIONLAB DERIVED GEOMETRY
```

---

## Pericynthion

```text
2026-04-06T23:00:46.177998Z
```

Provenance:

```text
MISSIONLAB DERIVED GEOMETRY
```

---

## Reported Earthrise

```text
2026-04-06T23:24:00Z
```

Provenance:

```text
NASA REPORTED
```

---

## Lunar SOI Exit

```text
2026-04-07T17:23:41.922211Z
```

Provenance:

```text
MISSIONLAB DERIVED GEOMETRY
```

---

## RTC1

```text
2026-04-08T00:03:00Z
```

---

## RTC2

```text
2026-04-10T02:53:00Z
```

---

## RTC3

```text
2026-04-10T18:53:00Z
```

---

## Entry Interface

```text
2026-04-10T23:53:00Z
```

---

## Splashdown

```text
2026-04-11T00:07:00Z
```

---

# Phase 2 Integrated Operational Threads

Six mission-level cross-domain threads were constructed.

---

## Thread 1 — Earth Departure and Adaptive Outbound Trajectory Management

Domains:

```text
FLIGHT DYNAMICS
MANEUVERS
PROPULSION
GNC
```

Sequence:

```text
launch
→
proximity operations
→
perigee-raise context
→
translunar-injection context
→
OTC1 cancelled
→
OTC2 cancelled
→
OTC3 executed
→
lunar SOI entry
```

Interpretation:

The outbound trajectory demonstrates adaptive trajectory management.

Three correction opportunities existed.

Two were cancelled.

One was executed.

Permanent boundaries:

```text
CANCELLED CORRECTION
!=
FAILED BURN
```

and:

```text
CANCELLED CORRECTION
!=
PROPULSION ANOMALY
```

OTC3 engine assignment remains unresolved from current public evidence.

---

## Thread 2 — Proximity Operations Manual Control and Navigation

Domains:

```text
GNC
PROPULSION
FLIGHT DYNAMICS
```

Approximate duration:

```text
70 min
```

Sequence:

```text
automated pre-manual context
→
onboard navigation-sensor use
→
crew-controlled approach
→
crew-controlled retreat
→
RCS control
→
automated departure
```

Permanent boundaries:

```text
premission reference sequence
!=
as-flown event log
```

```text
planned range
!=
measured as-flown range
```

```text
crew controller input
!=
direct individual-thruster switching
```

---

## Thread 3 — Deep-Space Navigation and Lunar Communications Constraint

Domains:

```text
FLIGHT DYNAMICS
COMMUNICATIONS
GNC
```

Sequence:

```text
lunar SOI entry
→
onboard deep-space navigation context
→
optical-navigation imagery
→
DSN ground-navigation support
→
lunar flyby
→
expected lunar communications blackout
→
reported Earthrise
→
DSN reacquisition sequence
→
lunar SOI exit
```

The lunar communications blackout remains classified as:

```text
EXPECTED_OPERATIONAL_CONSTRAINT
```

Anomaly:

```text
FALSE
```

Permanent navigation-state boundary:

```text
ONBOARD_NAVIGATION_STATE
!=
GROUND_ORBIT_DETERMINATION
!=
AROW_PUBLIC_STATE_VECTOR
```

---

## Thread 4 — Return Trajectory Refinement

Domains:

```text
FLIGHT DYNAMICS
MANEUVERS
PROPULSION
GNC
```

Sequence:

```text
lunar SOI exit
→
RTC1 navigation monitoring
→
RTC1
→
RTC2 pre-burn GNC context
→
RTC2
→
RTC3 navigation monitoring
→
RTC3
→
Entry Interface
```

The public evidence establishes maneuver timing, duration, selected scalar delta-v magnitudes, and selected crew navigation-monitoring context.

It does not establish:

```text
complete maneuver-targeting logic
burn-vector directions
complete guidance commands
correction-burn engine assignments
```

---

## Thread 5 — RTC2 Communications Anomaly, Recovery, and Mission Continuation

Classification:

```text
UNEXPECTED_COMMUNICATIONS_ANOMALY_WITH_MISSION_CONTINUATION
```

This is the only Phase 2 integrated thread classified as an anomaly.

Domains:

```text
COMMUNICATIONS
MANEUVERS
GNC
PROPULSION
```

Public sequence:

```text
unexpected return-link loss
→
communications recovery
→
burn preparation resumed
→
RTC2 executed
```

Approximate computational loss anchor:

```text
2026-04-10T00:53:00Z
```

This anchor is explicitly:

```text
NOT EXACT
```

RTC2:

```text
2026-04-10T02:53:00Z
```

Supported:

```text
unexpected return-link anomaly occurred
communications were restored
burn preparation resumed
RTC2 executed after recovery
```

Not established:

```text
exact loss time
exact recovery time
complete two-way outage
root cause
failed subsystem
communications-caused maneuver problem
communications-caused propulsion problem
```

Causal relationship:

```text
NOT ESTABLISHED
```

Permanent rule:

```text
SEQUENCE
!=
CAUSATION
```

---

## Thread 6 — Final Correction to Entry Handoff

Domains:

```text
FLIGHT DYNAMICS
MANEUVERS
GNC
```

RTC3:

```text
2026-04-10T18:53:00Z
```

Entry Interface:

```text
2026-04-10T23:53:00Z
```

Interval:

```text
18,000 s
5 h
```

Splashdown public anchor:

```text
2026-04-11T00:07:00Z
```

This closes the Phase 2 mission-operations chain at the entry boundary.

It does not reconstruct the detailed entry guidance law.

---

# Quantitative Phase 2 Summary

Planned trajectory-correction opportunities:

```text
6
```

Executed trajectory corrections:

```text
4
```

Cancelled trajectory corrections:

```text
2
```

Outbound:

```text
3 planned
2 cancelled
1 executed
```

Return:

```text
3 planned
3 executed
```

Known executed correction firing-time sum:

```text
49.5 s
```

Reported return scalar delta-v magnitude sum:

```text
11.1 ft/s
3.38328 m/s
```

Important:

```text
11.1 ft/s
!=
net vector delta-v
```

because the public vector directions required for vector summation are unavailable.

OTC3 public delta-v remains unavailable.

Therefore a complete scalar sum for all four corrections is also not computed.

---

# Propulsion Integration Boundary

European Service Module propulsion architecture:

```text
1 OMS-E main engine
8 R-4D-11 auxiliary engines
24 reaction-control engines
33 engines total
```

Confirmed major OMS-E maneuver assignments:

```text
perigee raise
translunar injection
```

Correction-burn engine assignments publicly resolved:

```text
0
```

Unresolved:

```text
OTC3
RTC1
RTC2
RTC3
```

Permanent rule:

```text
CONFIRMED MAJOR-MANEUVER ENGINE ASSIGNMENT
!=
CORRECTION-BURN ENGINE ASSIGNMENT
```

---

# OEM Integration Boundary

Maneuver creation-time brackets audited:

```text
4
```

Same-epoch public solution comparisons available:

```text
3
```

Permanent rules:

```text
OEM SOLUTION DIFFERENCE
!=
NAVIGATION ERROR
```

```text
OEM SOLUTION DIFFERENCE
!=
MEASURED BURN DELTA-V
```

```text
OEM CREATION TIME
!=
PROOF OF MANEUVER ASSIMILATION
```

Assimilation status:

```text
NOT ESTABLISHED
```

---

# Navigation Integration Boundary

Onboard navigation sensor classes:

```text
6
```

```text
star tracker
IMU
GPS receiver
barometric altimeter
optical navigation camera
sun sensor
```

DSN onboard sensor:

```text
FALSE
```

Permanent state-product boundary:

```text
ONBOARD_NAVIGATION_STATE
!=
GROUND_ORBIT_DETERMINATION
!=
AROW_PUBLIC_STATE_VECTOR
```

Unavailable:

```text
complete onboard navigation-filter history
complete ground OD solution history
raw sensor histories
```

---

# Phase 2 Reconstructable Scope

Count:

```text
22
```

The integrated Phase 2 evidence supports reconstruction of:

```text
shared mission clock
Earth-Moon-Orion trajectory context
lunar SOI transitions
pericynthion geometry
public OEM solution evolution
trajectory-correction plan versus execution
trajectory-correction operational threads
propulsion architecture
confirmed major-maneuver propulsion assignments
communications event sequence
expected lunar communications constraint
unexpected return-link anomaly sequence
optical-communications context
GNC domain architecture
onboard navigation-sensor architecture
ground-navigation support boundary
manual-control architecture
proximity-operations GNC context
Flight Day 4 manual-piloting context
optical-navigation imagery existence
selected trajectory-correction navigation monitoring
final correction-to-entry public-clock handoff
```

---

# Phase 2 Non-Reconstructable Scope

Count:

```text
25
```

Not reconstructable from the current curated public evidence:

```text
complete flight-control console log
complete Flight Director decision tree
complete onboard navigation-filter history
complete ground orbit-determination history
raw navigation-sensor histories
filter covariance history
filter gain history
filter innovation history
filter bias history
measurement accept/reject history
complete guidance algorithm
complete guidance-command history
complete manual-control law
complete automatic-control law
controller-deflection history
individual thruster-firing history
complete thruster-allocation logic
correction-burn engine assignments
complete maneuver-targeting logic
trajectory-correction burn vectors
OTC3 public delta-v
complete crew navigation-display history
Flight Day 9 communications root cause
Flight Day 9 failed subsystem
detailed as-flown entry guidance
```

---

# Downstream Phase Handoffs

Phase 2K establishes that the following downstream domains are ready for dedicated work.

## Vehicle Systems / ECLSS / Thermal / Materials

Ready scope:

```text
cabin and environmental trends
ECLSS
toilet and wastewater events
thermal / materials
heat-shield risk-mitigation chain
```

---

## Entry / Descent / Splashdown / Recovery

Entry anchor:

```text
2026-04-10T23:53:00Z
```

Ready scope:

```text
detailed entry timeline
entry guidance where public evidence supports it
atmospheric-entry modeling
communications blackout
parachute sequence
splashdown accuracy
recovery timeline
```

---

## Space Weather / Radiation

Ready scope:

```text
space-weather context
OMNI / CDAWeb correlation
NAIRAS trajectory input
radiation environment
external environment versus crew-dose boundary
```

---

## Lunar Science / Crew Observations

Ready scope:

```text
crew imagery
Orion imagery
mission audio / transcripts
lunar-target correlation
crew-observation threads
```

---

## Mission Control / Engineering Perspectives

Ready scope:

```text
flight-control discipline lenses
FDO / FAO perspectives
EECOM / COMM perspectives
decision threads
postflight engineering timeline
```

---

# Generated Phase 2K Products

Analyzer:

```text
scripts/analysis/analyze_phase2_integrated_operations.py
```

Validator:

```text
scripts/validation/validate_phase2_integrated_operations.py
```

Processed products:

```text
data/processed/phase2/phase2_integrated_operational_threads.csv
data/processed/phase2/phase2_domain_closure.csv
data/processed/phase2/phase2_integrated_operations_summary.json
```

Documentation figures:

```text
docs/assets/phase2/phase2k_integrated_operational_threads.svg
docs/assets/phase2/phase2k_domain_closure.svg
```

Processed products remain ignored by Git.

---

# Phase 2K Validation

Observed analyzer checks:

```text
Flight dynamics integration: PASS
Communications integration: PASS
Propulsion integration: PASS
Maneuver integration: PASS
GNC integration: PASS
Shared mission clock: PASS
Expected constraint vs anomaly boundary: PASS
Propulsion assignment boundary: PASS
ONBOARD != GROUND != AROW boundary: PASS
OEM non-inference boundary: PASS
RTC2 communications non-causation boundary: PASS
Final correction-to-entry handoff: PASS
Downstream phase handoffs: PASS
```

Observed integrated counts:

```text
Integrated mission-clock anchors: 11
Integrated operational threads: 6
Reconstructable Phase 2 items: 22
Not reconstructable Phase 2 items: 25
```

Analyzer result:

```text
PHASE 2K ANALYSIS COMPLETE
```

Independent validation:

```text
Reference dataset: PASS
Flight dynamics integration: PASS
Communications integration: PASS
Propulsion integration: PASS
Maneuver integration: PASS
GNC integration: PASS
Shared mission clock: PASS
Mission-clock anchors: PASS
Expected blackout classification: PASS
RTC2 anomaly/recovery boundary: PASS
Correction-engine assignment boundary: PASS
OEM solution-evolution boundary: PASS
Navigation state-product boundary: PASS
Six integrated operational threads: PASS
Final correction-to-entry handoff: PASS
Downstream phase handoffs: PASS
Processed products: PASS
Documentation figures: PASS
```

Final validator output:

```text
PHASE 2K VALIDATION PASSED
```

---

# Phase 2K Current Closure State

The Phase 2K implementation and independent validation have passed.

At the time of this documentation repair, the observed validation run was performed while the Phase 2 integration reference still carried:

```text
IMPLEMENTATION_IN_PROGRESS
```

as its explicit closure-status field.

Therefore this log does not retroactively claim that the final Phase 2 status update, final validation rerun, commit, push, or clean-tree verification has already occurred.

Those final repository-closure steps must be observed before recording:

```text
PHASE 2 COMPLETE
```

as a committed repository state.

Current evidence-supported status:

```text
Phase 2K implementation: COMPLETE
Phase 2K validation: PASS
Final Phase 2 repository closure: PENDING
```

---

# Phase 2 Permanent Integration Guardrails

1. A public mission timeline is not a complete flight-control console log.
2. A public operational sequence is not a complete Flight Director rationale tree.
3. A planned maneuver is not an executed maneuver.
4. A cancelled correction is not a failed burn.
5. A cancelled correction is not a propulsion anomaly.
6. Propulsion capability does not establish burn-specific engine assignment.
7. Confirmed OMS-E use for major maneuvers does not establish correction-burn OMS-E use.
8. Correction-burn engine assignments remain unresolved for OTC3, RTC1, RTC2, and RTC3.
9. A public OEM trajectory is not raw spacecraft telemetry.
10. An OEM solution difference is not navigation error.
11. An OEM solution difference is not measured maneuver delta-v.
12. OEM creation time does not prove maneuver assimilation.
13. Navigation architecture is not raw navigation-sensor history.
14. DSN is ground support and not an onboard navigation sensor.
15. Ground navigation is not the Orion onboard navigation filter.
16. AROW state vectors are not proven Orion onboard filter states.
17. Optical-navigation imagery is not filter residual or innovation data.
18. Crew navigation monitoring is not a complete onboard navigation-state history.
19. A manual-control mode label does not disclose a complete control law.
20. Reported RCS use does not disclose individual thruster-firing history.
21. Expected lunar occultation communications loss is not an anomaly.
22. Return-link loss does not by itself prove a complete two-way outage.
23. Temporal sequence between a communications anomaly and RTC2 does not establish causation.
24. The RTC3-to-Entry-Interface clock relationship does not reconstruct entry guidance.
25. Absence from the current curated public evidence set is not proof that an operational record never existed.

---

# Phase 2 — Full Reproducibility and Final Closure

## Goal

Close the complete implemented Artemis II Phase 2 technical stack only after proving that every Phase 2 analysis and validator from Phase 2A through Phase 2K can be executed successfully from the repository in dependency order.

Phase 2 closure therefore requires more than the Phase 2K mission-operations integration.

The complete closure scope includes:

```text
entry trajectory
reference-frame reconstruction
Earth-fixed and geodetic geometry
entry dynamics
entry and recovery events
atmospheric environment
dynamic pressure
Mach reconstruction
rarefaction / continuum analysis
convective heating
thermal-protection-system evidence
entry-profile heritage
loft / rebound heating
lunar occultation geometry
Deep Space Network geometry
communications
optical communications
maneuvers
propulsion
flight dynamics
guidance
navigation
control
cross-domain mission operations
```

---

## Full Phase 2 Reproducibility Runner

Created:

```text
scripts/run_phase2.py
```

The runner executes the complete Phase 2 dependency chain using the active project Python environment.

Successful execution used:

```text
.venv\Scripts\python.exe
```

Pipeline size:

```text
58 steps
```

Observed execution time:

```text
33.56 s
```

Final runner result:

```text
PHASE 2 PIPELINE COMPLETE
```

Final coverage statement:

```text
Phase 2A through Phase 2K regenerated and validated successfully.
```

---

## Phase 2 Reproducibility Coverage

```text
Phase 2A
High-rate entry trajectory

Phase 2B
Frame transformation and Earth-fixed geometry

Phase 2C
Entry dynamics

Phase 2D
Entry / recovery events

Phase 2E
Atmosphere, Mach, rarefaction, and heating

Phase 2F
TPS evidence, heritage, and heating-history analysis

Phase 2G
Lunar occultation and DSN geometry

Phase 2H
Communications

Phase 2I
Maneuvers and propulsion

Phase 2J
Guidance, navigation, and control

Phase 2K
Cross-domain integration
```

Every stage in the complete run executed successfully.

No Phase 2 stage was skipped after the successful full-run start.

---

## Phase 2K Final Integration Validation

Phase 2K analyzer result:

```text
Flight dynamics integration: PASS
Communications integration: PASS
Propulsion integration: PASS
Maneuver integration: PASS
GNC integration: PASS
Shared mission clock: PASS
Expected constraint vs anomaly boundary: PASS
Propulsion assignment boundary: PASS
ONBOARD != GROUND != AROW boundary: PASS
OEM non-inference boundary: PASS
RTC2 communications non-causation boundary: PASS
Final correction-to-entry handoff: PASS
Downstream phase handoffs: PASS
```

Integrated mission-clock anchors:

```text
11
```

Integrated operational threads:

```text
6
```

Reconstructable Phase 2 mission-operations items:

```text
22
```

Not reconstructable from the current curated public evidence:

```text
25
```

Analyzer result:

```text
PHASE 2K ANALYSIS COMPLETE
```

Independent validator result:

```text
Reference dataset: PASS
Flight dynamics integration: PASS
Communications integration: PASS
Propulsion integration: PASS
Maneuver integration: PASS
GNC integration: PASS
Shared mission clock: PASS
Mission-clock anchors: PASS
Expected blackout classification: PASS
RTC2 anomaly/recovery boundary: PASS
Correction-engine assignment boundary: PASS
OEM solution-evolution boundary: PASS
Navigation state-product boundary: PASS
Six integrated operational threads: PASS
Final correction-to-entry handoff: PASS
Downstream phase handoffs: PASS
Processed products: PASS
Documentation figures: PASS
```

Final result:

```text
PHASE 2K VALIDATION PASSED
```

Phase 2K integration status:

```text
COMPLETE
```

---

## Full Phase 2 Closure Manifest

Created:

```text
data/reference/artemis_ii_phase2_closure_manifest.json
```

Dataset identifier:

```text
phase2_artemis_ii_full_closure_manifest
```

The closure manifest records the complete implemented Phase 2 hierarchy:

```text
2A

2B.1
2B.2

2C

2D

2E.1
2E.2
2E.3
2E.4

2F.1
2F.2
2F.3
2F.4

2G.1
2G.2

2H.1
2H.2
2H.3
2H.4

2I.1
2I.2
2I.3
2I.4

2J.1
2J.2
2J.3
2J.4

2K
```

Total closure entries:

```text
28
```

All 28 entries are recorded as:

```text
COMPLETE
```

The manifest intentionally separates:

```text
Phase 2K
=
cross-domain mission-operations integration
```

from:

```text
Phase 2 closure
=
complete technical closure of every implemented
Phase 2 subphase from 2A through 2K
```

---

## Independent Full Phase 2 Closure Validator

Created:

```text
scripts/validation/validate_phase2_closure.py
```

The validator independently verifies:

```text
closure manifest identity
Phase 2 COMPLETE status
Phase 2A through 2K coverage
28 subphase closure entries
all declared validators exist
all declared validators are represented in the Phase 2 runner
all key tracked reference products exist
all required local reproducibility inputs exist
Phase 2K integration closure
Phase 2J closure
Phase 2I closure readiness
permanent evidence-boundary policy
full reproducibility-run requirement
58-step successful-run record
Phase 3 handoff
```

Observed result:

```text
Closure manifest identity: PASS
Phase 2 status COMPLETE: PASS
Phase 2A through 2K coverage: PASS
28 subphase closure entries: PASS
All declared validators exist: PASS
All declared validators in runner: PASS
All key tracked reference products exist: PASS
All local reproducibility inputs exist: PASS
Phase 2K integration COMPLETE: PASS
Phase 2J closure COMPLETE: PASS
Phase 2I closure readiness: PASS
Evidence-boundary policy: PASS
Full reproducibility-run requirement: PASS
58-step successful-run record: PASS
Phase 3 handoff: PASS
```

Final result:

```text
PHASE 2 FULL CLOSURE VALIDATION PASSED
```

---

## Reproducibility Inputs

The successful Phase 2 preflight verified the required local mission-data and SPICE inputs, including:

```text
NASA AROW OEM archive

de440s.bsp

naif0012.tls

pck00011.tpc

earth_1962_260806_2126_combined.bpc
```

The runner also verified the tracked MissionLab reference products required by the Phase 2 analyses.

---

## Permanent Evidence Boundaries

The Phase 2 closure preserves all major evidence-discipline rules established throughout the phase.

### Entry Frames

```text
NASA M50 source label
!=
automatic proof of exact SPICE B1950 file-level equivalence
```

The B1950 representation remains an analysis mapping validated against the public trajectory handoff.

### Atmosphere

```text
MODELED ATMOSPHERIC QUANTITIES
!=
RAW ORION FLIGHT TELEMETRY
```

### Dynamic Pressure

```text
MODELED DYNAMIC PRESSURE
!=
RECORDED ORION SENSOR CHANNEL
```

### Mach

```text
MODELED MACH
!=
RECORDED ORION SENSOR CHANNEL
```

### Rarefaction

```text
MODELED RAREFACTION / KNUDSEN REGIME
!=
RECORDED ORION SENSOR CHANNEL
```

### Convective Heating

```text
MODELED CONVECTIVE HEATING
!=
MEASURED ORION SURFACE HEAT FLUX
```

### Thermal Protection System

```text
PUBLIC TPS EVIDENCE
!=
INTERNAL THERMAL TELEMETRY
```

### Expected Lunar Communications Constraint

```text
EXPECTED LUNAR OCCULTATION BLACKOUT
!=
ANOMALY
```

### Communications Causation

```text
OPERATIONAL SEQUENCE
!=
CAUSATION
```

The Flight Day 9 communications anomaly does not establish a causal relationship to RTC2.

### Maneuver Cancellation

```text
CANCELLED TRAJECTORY CORRECTION
!=
FAILED BURN
```

and:

```text
CANCELLED TRAJECTORY CORRECTION
!=
PROPULSION ANOMALY
```

### Propulsion Assignment

```text
PROPULSION ARCHITECTURE
!=
BURN-SPECIFIC ENGINE ASSIGNMENT
```

Correction-burn engine assignments remain unresolved for:

```text
OTC3
RTC1
RTC2
RTC3
```

### Public OEM Products

```text
PUBLIC OEM
!=
RAW SPACECRAFT TELEMETRY
```

```text
OEM SOLUTION DIFFERENCE
!=
NAVIGATION ERROR
```

```text
OEM SOLUTION DIFFERENCE
!=
MEASURED BURN DELTA-V
```

```text
OEM CREATION TIME
!=
PROOF OF MANEUVER ASSIMILATION
```

### Navigation State Products

```text
ONBOARD_NAVIGATION_STATE
!=
GROUND_ORBIT_DETERMINATION
!=
AROW_PUBLIC_STATE_VECTOR
```

### Deep Space Network

```text
DSN GROUND TRACKING
!=
ONBOARD NAVIGATION SENSOR
```

### Manual Control

```text
PUBLIC MANUAL-MODE LABEL
!=
COMPLETE CONTROL-LAW DISCLOSURE
```

and:

```text
REPORTED RCS USE
!=
INDIVIDUAL THRUSTER-FIRING HISTORY
```

### Entry Handoff

```text
RTC3 TO ENTRY-INTERFACE CLOCK CORRELATION
!=
DETAILED ENTRY-GUIDANCE RECONSTRUCTION
```

### Missing Public Evidence

```text
ABSENCE FROM THE CURRENT CURATED PUBLIC SOURCE SET
!=
PROOF THAT AN OPERATIONAL RECORD NEVER EXISTED
```

---

## Phase 2 Closure Artifacts

The final Phase 2 closure adds:

```text
data/reference/artemis_ii_phase2_integrated_operations.json

data/reference/artemis_ii_phase2_closure_manifest.json

scripts/analysis/analyze_phase2_integrated_operations.py

scripts/validation/validate_phase2_integrated_operations.py

scripts/validation/validate_phase2_closure.py

scripts/run_phase2.py

docs/assets/phase2/phase2k_integrated_operational_threads.svg

docs/assets/phase2/phase2k_domain_closure.svg
```

The complete reproducibility run also regenerated existing Phase 2J documentation figures from their validated source products.

---

## Repository Quality Check

Observed:

```text
git diff --check
```

No whitespace errors were reported.

---

# Final Phase 2 Status

```text
Phase 2A: COMPLETE
Phase 2B: COMPLETE
Phase 2C: COMPLETE
Phase 2D: COMPLETE
Phase 2E: COMPLETE
Phase 2F: COMPLETE
Phase 2G: COMPLETE
Phase 2H: COMPLETE
Phase 2I: COMPLETE
Phase 2J: COMPLETE
Phase 2K: COMPLETE
```

Overall:

```text
PHASE 2 COMPLETE
```

Closure basis:

```text
58 / 58 reproducibility steps passed

28 / 28 implemented subphase closure entries complete

Phase 2K analysis complete

Phase 2K validation passed

Full Phase 2 closure validation passed

Evidence-boundary policy passed

Phase 3 handoff passed
```

---

# Phase 3 Handoff

Next major phase:

```text
Phase 3 — ECLSS, Vehicle Systems, Thermal, and Materials
```

Phase 2 now provides the mission-clock, trajectory, entry, communications, maneuver, propulsion, and GNC backbone required to correlate Phase 3 spacecraft-system evidence against one defensible Artemis II operational timeline.

Phase 3 will begin with inspection of the existing repository and current public evidence before creating any new permanent datasets or analyses.

---

---

# Phase 3A.1 — Orion Environment Data Ingestion and Normalization

## Goal

Establish the first Artemis II Phase 3 spacecraft-environment dataset by ingesting the publicly released NASA Planetary Data System Orion environmental logger products and normalizing them against the MissionLab Artemis II mission clock.

The Phase 3A.1 scope is limited to direct measurements released in the Artemis II PDS Orion Environment Data collection.

The measurements characterize local storage-locker environments inside Orion.

They are not interpreted as a complete reconstruction of the Orion cabin environment or the Environmental Control and Life Support System telemetry stream.

---

## NASA PDS Source Acquisition

Created:

```text
scripts/ingestion/download_orion_environment_data.py
```

Source:

```text
NASA Planetary Data System
Artemis II Mission Bundle
Orion Environment Data
```

Released environmental loggers:

```text
SN 1104
SN 1105
```

Instrument class:

```text
Onset HOBO MX1101
```

Measured quantities:

```text
temperature
relative humidity
dew point
```

Nominal sampling cadence:

```text
60 seconds
```

The downloader retrieved:

```text
art002_086-162546_111-205046_hobo1104_raw_v01.csv
art002_086-162546_111-205046_hobo1104_raw_v01.xml

art002_086-162926_111-203826_hobo1105_raw_v01.csv
art002_086-162926_111-203826_hobo1105_raw_v01.xml

collection_data_orion_environment.xml
collection_data_orion_environment_inventory.csv
```

The NASA PDS bundle checksum manifest was also retrieved:

```text
urn-nasa-pds-artemis2_mission.md5
```

---

## Source Integrity Validation

All six downloaded products passed checksum validation against the NASA PDS bundle manifest.

Observed MD5 values:

```text
SN 1104 CSV
ef6a42e7d2189ab2329121995d8446f1

SN 1104 XML
8b32527433bed7cb659a7778f9893c12

SN 1105 CSV
f5ed3754e04d8a216955d5dea838986a

SN 1105 XML
d5ef9dd100cf3a5320e321f6d482264d

Collection XML
a8a8bc216ccc0bff37b57d9c0f90d183

Collection inventory CSV
ea7e81b6d9733ce6a6bda8c75d60b74f
```

Downloader result:

```text
ORION ENVIRONMENT DOWNLOAD COMPLETE
```

Products downloaded:

```text
6 / 6
```

---

## Environment Normalization

Created:

```text
scripts/processing/normalize_orion_environment.py
```

Generated:

```text
data/processed/eclss/orion_environment_normalized.csv

data/processed/eclss/orion_environment_metadata.json
```

The normalization layer converts the released logger timestamps into UTC and correlates every sample with the existing Artemis II MissionLab launch epoch:

```text
2026-04-01T22:35:12Z
```

The normalized dataset preserves:

```text
logger serial number

source sample number

original CDT timestamp

normalized UTC timestamp

Mission Elapsed Time in seconds

formatted Mission Elapsed Time

mission-period classification

temperature in degrees Celsius

relative humidity in percent

dew point in degrees Celsius

source provenance

source filename
```

---

## Logger SN 1104

Normalized records:

```text
37,706
```

Start:

```text
2026-03-26T16:25:46Z
```

Stop:

```text
2026-04-21T20:50:46Z
```

Sample-number discontinuities:

```text
0
```

Non-60-second sampling intervals:

```text
0
```

Result:

```text
CONTINUOUS 60-SECOND SERIES
```

---

## Logger SN 1105

Normalized records:

```text
37,690
```

Start:

```text
2026-03-26T16:29:26Z
```

Stop:

```text
2026-04-21T20:38:26Z
```

Sample-number discontinuities:

```text
0
```

Non-60-second sampling intervals:

```text
0
```

Result:

```text
CONTINUOUS 60-SECOND SERIES
```

---

## Combined Dataset

Combined normalized records:

```text
75,396
```

Mission-period distribution:

```text
PRELAUNCH
18,016 records

IN_FLIGHT
26,104 records

POSTFLIGHT
31,276 records
```

Total:

```text
75,396 records
```

Mission-period labels are MissionLab-derived classifications based on the normalized UTC timestamp relative to the Artemis II mission clock.

They are not fields contained in the original PDS CSV files.

---

## Independent Validation

Created:

```text
scripts/validation/validate_orion_environment_normalization.py
```

Independent validation result:

```text
Metadata identity: PASS
Raw NASA PDS source counts: PASS
Normalized CSV schema: PASS
Combined record count: PASS
Record-level numeric fields: PASS
CDT to UTC conversion: PASS
Mission elapsed time: PASS
Mission-period classification: PASS
Provenance preservation: PASS
Combined temporal ordering: PASS
```

Logger SN 1104:

```text
record count: PASS
start/stop UTC: PASS
60-second cadence: PASS
sample continuity: PASS
```

Logger SN 1105:

```text
record count: PASS
start/stop UTC: PASS
60-second cadence: PASS
sample continuity: PASS
```

Source and mission metadata:

```text
NASA PDS source metadata: PASS
Mission-clock metadata: PASS
```

Generated products:

```text
normalized CSV: PASS
metadata JSON: PASS
```

Final validator result:

```text
PHASE 3A.1 VALIDATION PASSED
```

---

# Phase 3A.1 Evidence Boundaries

## Direct Measurements

The following fields originate directly from the released NASA PDS logger records:

```text
temperature
relative humidity
dew point
sample number
source timestamp
```

These values retain:

```text
NASA_PDS_FLIGHT_SENSOR_DATA
```

provenance.

---

## MissionLab-Derived Fields

The following fields are derived by MissionLab:

```text
UTC conversion

Mission Elapsed Time

mission-period classification
```

Therefore:

```text
MISSIONLAB-DERIVED TIME CONTEXT
!=
NASA-REPORTED SENSOR FIELD
```

---

## Storage-Locker Environment

The HOBO instruments characterize environmental conditions at their physical logger locations.

Therefore:

```text
HOBO STORAGE-LOCKER ENVIRONMENT
!=
COMPLETE ORION CABIN ENVIRONMENT
```

and:

```text
HOBO STORAGE-LOCKER ENVIRONMENT
!=
COMPLETE ORION ECLSS TELEMETRY
```

The dataset may be used to analyze publicly released local environmental trends and their relationship to mission events.

It must not be presented as a full spacecraft atmospheric-control telemetry record.

---

## Measurement versus Interpretation

Direct temperature, relative-humidity, and dew-point values are public sensor measurements.

Any later:

```text
change point

anomaly score

trend classification

event correlation

operational interpretation
```

must be explicitly labeled as MissionLab-derived analysis unless independently supported by a NASA source.

---

# Phase 3A.1 Status

```text
DOWNLOAD: COMPLETE

NASA PDS CHECKSUM VALIDATION: PASS

NORMALIZATION: COMPLETE

75,396 RECORDS NORMALIZED

LOGGER CONTINUITY: PASS

MISSION-CLOCK CORRELATION: PASS

INDEPENDENT VALIDATION: PASS

PHASE 3A.1: COMPLETE
```

Next:

```text
Phase 3A.2
Orion Environmental Trend Reconstruction
```

Phase 3A.2 will quantify the released environmental measurements across prelaunch, inflight, and postflight periods and establish the baseline environmental behavior required before any project-derived change-point or anomaly analysis.

---

---

# Phase 3A.2 — Orion Environmental Trend Reconstruction

## Goal

Establish the baseline behavior of the publicly released Artemis II Orion environmental logger measurements before performing any change-point or anomaly analysis.

Phase 3A.2 uses the validated Phase 3A.1 normalized dataset to characterize:

```text
temperature

relative humidity

dew point
```

across:

```text
PRELAUNCH

IN_FLIGHT

POSTFLIGHT
```

for both released HOBO MX1101 environmental loggers.

The phase also compares the two inflight logger records using an explicit near-synchronous pairing method while preserving the fact that their timestamp grids do not match exactly.

---

## Dependency

Validated Phase 3A.1 dataset:

```text
data/processed/eclss/orion_environment_normalized.csv
```

Input records:

```text
75,396
```

Dependency status:

```text
PASS
```

---

## Analysis

Created:

```text
scripts/analysis/analyze_orion_environment_trends.py
```

Generated:

```text
data/processed/eclss/orion_environment_period_summary.csv

data/processed/eclss/orion_environment_daily_summary.csv

data/processed/eclss/orion_environment_logger_comparison.csv

data/processed/eclss/orion_environment_trend_summary.json
```

Documentation figures:

```text
docs/assets/eclss/phase3a2_temperature_trends.svg

docs/assets/eclss/phase3a2_humidity_trends.svg

docs/assets/eclss/phase3a2_dew_point_trends.svg

docs/assets/eclss/phase3a2_logger_temperature_difference.svg
```

---

# Mission-Period Environmental Statistics

## Logger SN 1104

### Prelaunch

Temperature mean:

```text
21.275 °C
```

Temperature range:

```text
20.860 to 22.150 °C
```

Relative humidity mean:

```text
27.269 %
```

Dew-point mean:

```text
1.673 °C
```

### In Flight

Temperature mean:

```text
23.954 °C
```

Temperature range:

```text
21.010 to 25.570 °C
```

Relative humidity mean:

```text
23.509 %
```

Dew-point mean:

```text
1.830 °C
```

### Postflight

Temperature mean:

```text
20.934 °C
```

Temperature range:

```text
17.770 to 23.520 °C
```

Relative humidity mean:

```text
57.498 %
```

Dew-point mean:

```text
12.215 °C
```

---

## Logger SN 1105

### Prelaunch

Temperature mean:

```text
21.327 °C
```

Temperature range:

```text
21.010 to 22.490 °C
```

Relative humidity mean:

```text
26.999 %
```

Dew-point mean:

```text
1.571 °C
```

### In Flight

Temperature mean:

```text
22.614 °C
```

Temperature range:

```text
20.460 to 26.040 °C
```

Relative humidity mean:

```text
25.717 %
```

Dew-point mean:

```text
1.918 °C
```

### Postflight

Temperature mean:

```text
21.421 °C
```

Temperature range:

```text
16.820 to 27.110 °C
```

Relative humidity mean:

```text
48.671 %
```

Dew-point mean:

```text
10.100 °C
```

---

# Inflight Logger Comparison

The two logger streams each contain:

```text
13,052 inflight measurements
```

The two timestamp grids do not match exactly.

Observed sampling-grid relationship:

```text
SN 1104 sample second: :46

SN 1105 sample second: :26
```

Therefore:

```text
SN 1105 - SN 1104
=
-20 seconds
```

for the complete inflight overlap.

Exact timestamp matching is therefore not possible.

Phase 3A.2 uses:

```text
one-to-one nearest-time pairing
```

with:

```text
±30 second tolerance
```

Observed pairing result:

```text
SN 1104 inflight records: 13,052

SN 1105 inflight records: 13,052

paired records: 13,052

unmatched SN 1104 records: 0

unmatched SN 1105 records: 0
```

Maximum absolute pairing offset:

```text
20 seconds
```

Mean signed pairing offset:

```text
-20 seconds
```

Therefore all inflight samples were paired one-to-one without interpolation.

---

# Inflight Logger Differences

For the complete 13,052-pair inflight comparison:

Mean temperature difference:

```text
SN 1105 - SN 1104
=
-1.341 °C
```

Mean relative-humidity difference:

```text
SN 1105 - SN 1104
=
+2.208 %
```

Mean dew-point difference:

```text
SN 1105 - SN 1104
=
+0.089 °C
```

These differences are descriptive relationships between two local sensor locations.

They are not interpreted as spacecraft-wide environmental gradients.

---

# Near-Synchronous Pairing Boundary

The comparison is explicitly classified as:

```text
MISSIONLAB_DERIVED_NEAR_SYNCHRONOUS_COMPARISON
```

The paired measurements are not simultaneous.

Therefore:

```text
NEAR-SYNCHRONOUS
!=
SIMULTANEOUS
```

and:

```text
LOGGER DIFFERENCE
!=
SPACECRAFT-WIDE ENVIRONMENTAL GRADIENT
```

and:

```text
LOGGER DIFFERENCE
!=
ECLSS PERFORMANCE METRIC
```

---

# Descriptive Statistics Boundary

The direct environmental measurements remain:

```text
NASA PDS FLIGHT SENSOR DATA
```

The following Phase 3A.2 products are MissionLab-derived:

```text
period statistics

daily statistics

percentiles

standard deviations

logger differences

near-time pairing

mission-period comparisons
```

Therefore:

```text
DIRECT SENSOR MEASUREMENT
!=
DERIVED STATISTIC
```

---

# Anomaly Boundary

Phase 3A.2 performs no anomaly detection.

Specifically:

```text
change-point detection: FALSE

anomaly detection: FALSE

causal inference: FALSE
```

Therefore:

```text
ENVIRONMENTAL TREND
!=
ANOMALY
```

and:

```text
LOGGER DIFFERENCE
!=
ECLSS ANOMALY
```

No temperature, relative-humidity, or dew-point excursion identified in this phase is classified as a spacecraft anomaly solely from the environmental logger data.

---

# Independent Validation

Created:

```text
scripts/validation/validate_orion_environment_trends.py
```

Validation result:

```text
Dependency dataset: PASS

Analysis identity: PASS

Mission-period statistics: PASS

Summary JSON statistics: PASS

Daily aggregation: PASS

Near-synchronous pairing: PASS

Pair-by-pair derived differences: PASS

Logger time-grid offset: PASS

Logger comparison summary: PASS

Analysis-scope boundaries: PASS

Evidence-boundary policy: PASS

Documentation figures: PASS
```

Validated products:

```text
normalized records: 75,396

period-summary rows: 18

daily-summary rows: 54

inflight logger pairs: 13,052

logger offset: -20.0 s
```

Validated inflight differences:

```text
temperature
SN 1105 - SN 1104
=
-1.341 °C

relative humidity
SN 1105 - SN 1104
=
+2.208 %

dew point
SN 1105 - SN 1104
=
+0.089 °C
```

Final result:

```text
PHASE 3A.2 VALIDATION PASSED
```

---

# Phase 3A.2 Status

```text
DEPENDENCY VALIDATION: PASS

DESCRIPTIVE STATISTICS: COMPLETE

MISSION-PERIOD RECONSTRUCTION: COMPLETE

DAILY AGGREGATION: COMPLETE

NEAR-SYNCHRONOUS LOGGER COMPARISON: COMPLETE

13,052 / 13,052 INFLIGHT PAIRS RECONSTRUCTED

LOGGER CLOCK OFFSET: VERIFIED

EVIDENCE BOUNDARIES: PASS

DOCUMENTATION FIGURES: PASS

INDEPENDENT VALIDATION: PASS

PHASE 3A.2: COMPLETE
```

Next:

```text
Phase 3A.3
Environmental Change-Point and Anomaly-Evidence Analysis
```

Phase 3A.3 may now use the validated Phase 3A.2 baseline to search for statistically meaningful environmental changes.

Any detected change point or anomaly candidate must remain explicitly:

```text
MISSIONLAB DERIVED
```

unless a NASA operational source independently identifies the same event.

---

---

# Phase 3A.3 — Environmental Change-Point and Anomaly-Evidence Analysis

## Goal

Extend the validated Artemis II environmental reconstruction from descriptive trends into statistically derived change-point and anomaly-evidence candidates while maintaining strict separation between:

```text
NASA PDS SENSOR MEASUREMENT

MISSIONLAB-DERIVED STATISTICAL SIGNAL

NASA-REPORTED OPERATIONAL EVENT

CONFIRMED SPACECRAFT ANOMALY
```

Phase 3A.3 does not convert statistical excursions into spacecraft anomaly claims.

Its purpose is to identify statistically unusual environmental behavior that can later be compared against independently documented mission events.

---

## Dependencies

Phase 3A.3 depends on the completed environmental reconstruction stack:

```text
Phase 3A.1
Orion Environment Data Ingestion and Normalization

Phase 3A.2
Orion Environmental Trend Reconstruction
```

Validated normalized records:

```text
75,396
```

Dependency status:

```text
Phase 3A.1: PASS

Phase 3A.2: PASS
```

---

# Statistical Analysis

Created:

```text
scripts/analysis/analyze_orion_environment_changes.py
```

Generated:

```text
data/processed/eclss/orion_environment_change_candidates.csv

data/processed/eclss/orion_environment_anomaly_candidates.csv

data/processed/eclss/orion_environment_change_analysis.json
```

Documentation figures:

```text
docs/assets/eclss/phase3a3_change_point_scores.svg

docs/assets/eclss/phase3a3_anomaly_scores.svg
```

---

# Analysis Grid

The original NASA PDS measurements remain unchanged.

For statistical analysis, the 60-second measurements were reduced to:

```text
15-minute median bins
```

Observed aggregate-bin counts:

```text
SN 1104
2,515 bins

SN 1105
2,514 bins
```

This aggregation is:

```text
MISSIONLAB DERIVED
```

and exists only for statistical analysis.

It does not replace or alter the original PDS measurements.

---

# Change-Point Evidence Method

Change-point evidence compares:

```text
1 hour before candidate boundary

versus

1 hour after candidate boundary
```

using median environmental values.

The score is based on:

```text
absolute pre/post median change

divided by

robust first-difference scale
```

Configured statistical threshold:

```text
8.0
```

Minimum separation between retained candidates:

```text
180 minutes
```

Classification:

```text
STATISTICAL_CHANGE_CANDIDATE_ONLY
```

Provenance:

```text
MISSIONLAB_DERIVED
```

---

# Change-Point Results

Total statistical change candidates:

```text
107
```

Public-context classifications:

```text
MISSION_BOUNDARY_LAUNCH_CONTEXT
2

MISSION_BOUNDARY_SPLASHDOWN_CONTEXT
7

NASA_REPORTED_CARGO_HANDOVER_CONTEXT
4

NASA_REPORTED_LOGGER_RELOCATION_CONTEXT
2

NO_MATCHING_PUBLIC_CONTEXT_IN_CURATED_SET
92
```

Therefore:

```text
15 candidates
```

occur near one of the currently encoded mission or operational context boundaries.

The remaining:

```text
92 candidates
```

have no matching context in the current curated event set.

This does not imply that those 92 candidates represent spacecraft anomalies.

---

# Local Anomaly-Evidence Method

Local anomaly evidence uses a robust local baseline around each 15-minute aggregate.

Method:

```text
LOCAL MEDIAN + MAD
```

Local half-window:

```text
180 minutes
```

Candidate threshold:

```text
absolute robust score >= 6.0
```

Nearby threshold crossings are clustered into single candidate events.

Classification:

```text
STATISTICAL_ANOMALY_CANDIDATE_ONLY
```

Provenance:

```text
MISSIONLAB_DERIVED
```

---

# Anomaly-Evidence Results

Total retained statistical anomaly-evidence candidates:

```text
13
```

Current public-context classifications:

```text
NO_MATCHING_PUBLIC_CONTEXT_IN_CURATED_SET
13
```

No anomaly-evidence candidate currently overlaps one of the limited operational-context windows encoded in Phase 3A.3.

This result must not be interpreted as:

```text
13 confirmed Orion anomalies
```

or:

```text
13 undocumented spacecraft failures
```

Instead:

```text
13 STATISTICALLY UNUSUAL ENVIRONMENTAL CANDIDATES
```

were identified for potential later mission-context correlation.

---

# SN 1105 Logger Relocation Context

NASA-reported location history constrains SN 1105 as follows.

Initial location:

```text
Locker D
Bag L_022
```

Later location:

```text
Locker F
Bag R_027
```

Reported transfer window:

```text
2026-04-09T18:00:00Z
through
2026-04-09T21:00:00Z
```

Exact relocation time:

```text
UNKNOWN
```

Two change candidates occur within the relocation context window.

Therefore:

```text
SN 1105 STATISTICAL CHANGE
NEAR
LOGGER RELOCATION
```

does not establish:

```text
ECLSS EVENT
```

or:

```text
SPACECRAFT ENVIRONMENTAL ANOMALY
```

A local environmental change could reflect the sensor's change in physical surroundings.

---

# Mission and Recovery Context

The Phase 3A.3 context layer includes the following boundaries.

Launch:

```text
2026-04-01T22:35:12Z
```

Splashdown:

```text
2026-04-11T00:07:00Z
```

Orion power down:

```text
2026-04-11T00:30:00Z
```

Recovery well-deck context:

```text
2026-04-11T08:14:00Z
```

Cargo-handover context boundary:

```text
2026-04-14T19:00:00Z
```

These timestamps provide operational context for environmental transitions.

They do not establish causal explanations for statistical changes merely because a candidate occurs nearby.

---

# Public-Context Boundary

A candidate with:

```text
NO_MATCHING_PUBLIC_CONTEXT_IN_CURATED_SET
```

means only that the candidate does not overlap an event currently encoded in this MissionLab analysis.

It does not mean:

```text
NASA reported no event
```

and does not mean:

```text
no public explanation exists
```

and does not mean:

```text
the candidate represents a spacecraft failure
```

Therefore:

```text
ABSENCE FROM CURATED CONTEXT
!=
ABSENCE FROM PUBLIC RECORD
```

and:

```text
ABSENCE FROM CURATED CONTEXT
!=
ANOMALY CONFIRMATION
```

---

# Statistical Candidate Boundary

A change-point candidate indicates:

```text
STATISTICALLY MEANINGFUL LOCAL CHANGE
```

under the chosen MissionLab analysis method.

It does not establish:

```text
SPACECRAFT ANOMALY
```

Therefore:

```text
STATISTICAL CHANGE CANDIDATE
!=
SPACECRAFT ANOMALY
```

Likewise:

```text
STATISTICAL ANOMALY CANDIDATE
!=
CONFIRMED SPACECRAFT ANOMALY
```

The term anomaly in the statistical artifact refers only to deviation from a local statistical baseline.

---

# Causal-Inference Boundary

Phase 3A.3 performs:

```text
NO CAUSAL INFERENCE
```

Temporal proximity alone does not establish causation.

Therefore:

```text
EVENT A OCCURS NEAR EVENT B
!=
EVENT A CAUSED EVENT B
```

This applies to:

```text
launch

splashdown

power down

recovery operations

cargo handover

logger relocation

future operational events added to MissionLab
```

---

# Postflight Boundary

The environmental logger records continue well beyond splashdown.

Postflight measurements may reflect changing physical conditions associated with:

```text
spacecraft recovery

power-down state

recovery-ship environment

hardware access

cargo movement

sensor relocation

ground handling
```

Therefore:

```text
POSTFLIGHT LOGGER ENVIRONMENT
!=
INFLIGHT ORION ENVIRONMENT
```

Postflight changes must not automatically be interpreted using inflight spacecraft-system assumptions.

---

# Independent Validation

Created:

```text
scripts/validation/validate_orion_environment_changes.py
```

Validation independently reproduced:

```text
15-minute aggregation

change-point candidate detection

candidate separation

local robust anomaly detection

candidate clustering

public-context correlation

candidate values

method configuration

NASA-reported context metadata

evidence boundaries
```

Validation results:

```text
Phase 3A.1 dependency: PASS

Phase 3A.2 dependency: PASS

Analysis identity: PASS

15-minute aggregation: PASS

Change-point reconstruction: PASS

Change-point candidate values: PASS

Local anomaly reconstruction: PASS

Anomaly candidate values: PASS

Public-context correlation: PASS

Candidate totals: PASS

Statistical method metadata: PASS

NASA-reported context metadata: PASS

Evidence-boundary policy: PASS

Documentation figures: PASS
```

Validated aggregate bins:

```text
SN 1104
2,515

SN 1105
2,514
```

Validated change candidates:

```text
107
```

Validated anomaly-evidence candidates:

```text
13
```

Validated change contexts:

```text
MISSION_BOUNDARY_LAUNCH_CONTEXT
2

MISSION_BOUNDARY_SPLASHDOWN_CONTEXT
7

NASA_REPORTED_CARGO_HANDOVER_CONTEXT
4

NASA_REPORTED_LOGGER_RELOCATION_CONTEXT
2

NO_MATCHING_PUBLIC_CONTEXT_IN_CURATED_SET
92
```

Validated anomaly contexts:

```text
NO_MATCHING_PUBLIC_CONTEXT_IN_CURATED_SET
13
```

Final validation result:

```text
PHASE 3A.3 VALIDATION PASSED
```

---

# Phase 3A Environmental Reconstruction Status

Phase 3A now provides a complete public-data environmental analysis chain:

```text
NASA PDS SOURCE PRODUCTS
        ↓
CHECKSUM VALIDATION
        ↓
60-SECOND LOGGER NORMALIZATION
        ↓
UTC + MISSION ELAPSED TIME
        ↓
MISSION-PERIOD RECONSTRUCTION
        ↓
DESCRIPTIVE ENVIRONMENTAL STATISTICS
        ↓
NEAR-SYNCHRONOUS LOGGER COMPARISON
        ↓
15-MINUTE STATISTICAL ANALYSIS GRID
        ↓
CHANGE-POINT EVIDENCE
        ↓
LOCAL ANOMALY EVIDENCE
        ↓
PUBLIC-CONTEXT CORRELATION
        ↓
STRICT EVIDENCE BOUNDARIES
```

Phase 3A status:

```text
Phase 3A.1: COMPLETE

Phase 3A.2: COMPLETE

Phase 3A.3: COMPLETE

NASA PDS SOURCE INTEGRITY: PASS

75,396 RAW-NORMALIZED RECORDS

13,052 INFLIGHT LOGGER PAIRS

107 STATISTICAL CHANGE CANDIDATES

13 STATISTICAL ANOMALY-EVIDENCE CANDIDATES

CAUSAL INFERENCE: FALSE

SPACECRAFT ANOMALY CLAIMS FROM LOGGER DATA: NONE

PHASE 3A: COMPLETE
```

---

# Next

```text
Phase 3B
Orion Waste Management Operational Reconstruction
```

Phase 3B will move from passive environmental measurements into documented spacecraft operations and reconstruct the public evidence surrounding:

```text
Orion toilet / waste-management fault

wastewater system behavior

wastewater venting

crew response

ground response

operational constraints

resolution / mission outcome
```

using mission-source evidence rather than inferring these events from the environmental logger data.

---

---

# Phase 3B.1 — Artemis II Waste Management Public Evidence Reconstruction

## Goal

Establish a source-grounded Artemis II waste-management evidence base before constructing any derived operational interpretation.

Phase 3B.1 reconstructs two separate publicly documented Orion Universal Waste Management System threads:

```text
Flight Day 1
Toilet fault indication and recovery

Flight Day 4
Urine / wastewater vent-line issue
```

These threads are deliberately kept separate.

No relationship between them is inferred unless supported by public evidence.

---

# Reference Product

Created:

```text
data/reference/artemis_ii_waste_management_evidence.json
```

Validated by:

```text
scripts/validation/validate_waste_management_evidence.py
```

Reference dataset:

```text
phase3b1_artemis_ii_waste_management_evidence
```

Mission:

```text
Artemis II
```

System:

```text
Orion Universal Waste Management System
UWMS
```

---

# Public System Architecture

The public NASA evidence supports the following high-level waste-management architecture.

## Urine Collection

Publicly reconstructable functions:

```text
crew urine collection

airflow-assisted transport

urine pretreatment

dedicated urine storage

overboard urine venting
```

NASA describes overboard urine venting as a normal recurring crew activity.

---

## Fecal Collection

Solid waste is handled separately using:

```text
fecal canisters
```

The Flight Day 4 urine / wastewater vent-line issue does not establish a failure in the fecal collection path.

Therefore:

```text
URINE VENT ISSUE
!=
FECAL COLLECTION FAILURE
```

---

## Contingency Collection

NASA publicly documented the availability of backup collection devices.

Therefore:

```text
BACKUP COLLECTION AVAILABLE
```

does not establish:

```text
COMPLETE UWMS FAILURE
```

---

# Flight Day 1 — Toilet Fault and Recovery

## Initial Event

NASA reported that during toilet-system checkout ahead of the apogee raise burn, the Artemis II crew observed:

```text
a blinking fault light
```

Mission Control assessed available data and coordinated troubleshooting with the crew.

The public record does not provide:

```text
exact fault UTC

internal UWMS fault code

identified failed component

confirmed root cause
```

Therefore:

```text
BLINKING FAULT LIGHT
!=
IDENTIFIED FAILED COMPONENT
```

and:

```text
FAULT INDICATION
!=
COMPLETE UWMS FAILURE
```

---

## Return to Normal Operations

NASA subsequently reported that:

```text
crew + Mission Control troubleshooting
```

restored Orion's toilet to:

```text
NORMAL OPERATIONS
```

The successful recovery establishes operational restoration.

It does not establish the mechanism that originally produced the fault indication.

Therefore:

```text
NORMAL OPERATIONS RESTORED
!=
ROOT CAUSE PUBLICLY KNOWN
```

Phase 3B.1 preserves:

```text
root cause = unresolved in curated public evidence
```

---

# Flight Day 4 — Wastewater Vent-Line Issue

NASA reported that wastewater was vented overboard to create additional waste-system tank capacity.

The vent activity:

```text
ENDED EARLIER THAN EXPECTED
```

At the time NASA reported:

```text
wastewater tank was NOT full

toilet remained operational
```

This distinction is critical.

Therefore:

```text
EARLY VENT TERMINATION
!=
TOILET FAILURE
```

and:

```text
TANK NOT FULL
!=
NOMINAL VENT PATH
```

and:

```text
TOILET OPERATIONAL
!=
NOMINAL URINE VENT PATH
```

---

# Possible Ice Hypothesis

NASA publicly discussed:

```text
possible ice obstructing the vent line
```

as one hypothesis under evaluation.

NASA also stated that teams were considering other possible causes.

Therefore:

```text
POSSIBLE ICE
!=
CONFIRMED ICE
```

and:

```text
WORKING HYPOTHESIS
!=
FINAL ROOT CAUSE
```

---

# Vent Heater Response

NASA reported that engineers used:

```text
vent heaters
```

to attempt to melt any possible ice affecting the vent line.

This is an operational troubleshooting action.

It does not establish that ice was present.

Therefore:

```text
VENT HEATER USE
!=
PROOF OF ICE
```

No public reconstruction is made here of:

```text
heater duty cycle

heater temperature

vent-line internal temperature

vent pressure

vent flow rate
```

---

# Sun-Pointing Response

NASA also reported that Orion was oriented so the vent could face the Sun.

Purpose:

```text
support vent-line troubleshooting
```

NASA reported that the associated change to the trajectory-correction schedule did not impact Orion's current trajectory.

Therefore:

```text
SUN POINTING
!=
CONFIRMED ROOT CAUSE
```

and:

```text
SUN POINTING
!=
UNPLANNED TRAJECTORY MANEUVER
```

The action is preserved as an operational spacecraft-attitude response to a waste-management troubleshooting problem.

---

# Backup Collection Posture

During Flight Day 4 troubleshooting:

```text
toilet remained operational

wastewater tank was not full

backup collection devices were available if needed
```

Therefore:

```text
BACKUP COLLECTION AVAILABLE
!=
TOILET INOPERATIVE
```

The public evidence does not establish complete loss of toilet function.

---

# Postflight Investigation

NASA's initial Artemis II postflight assessment reported continued investigation of the:

```text
urine vent-line issue
```

The assessment included:

```text
hardware evaluation

data gathering

continued postflight investigation
```

Therefore:

```text
POSTFLIGHT INVESTIGATION
!=
FINAL ROOT CAUSE
```

Phase 3B.1 does not assign:

```text
confirmed ice blockage

hardware failure

software failure

sensor failure

procedural error

crew error
```

as the cause of the vent-line issue.

---

# Two Separate Operational Threads

## Thread 1

```text
Toilet-system checkout
        ↓
Blinking fault light
        ↓
Mission Control data assessment
        ↓
Crew + ground troubleshooting
        ↓
Normal toilet operations restored
```

Public outcome:

```text
RESOLVED IN FLIGHT
```

Root cause:

```text
NOT PUBLICLY ESTABLISHED
```

---

## Thread 2

```text
Wastewater vent activity
        ↓
Vent ended earlier than expected
        ↓
Possible ice considered
        ↓
Vent heaters used
        ↓
Vent pointed toward Sun
        ↓
Other causes reviewed
        ↓
Tank remained not full
        ↓
Toilet remained operational
        ↓
Backup collection posture available
        ↓
Postflight investigation continued
```

Public outcome:

```text
MANAGED IN FLIGHT
WITH
POSTFLIGHT INVESTIGATION
```

Root cause:

```text
NOT PUBLICLY ESTABLISHED
```

---

# Temporal Precision Boundary

The public sources used in Phase 3B.1 do not provide exact UTC timestamps for the principal waste-management events.

Therefore the reference product preserves:

```text
date

flight-day context

relative event order
```

without inventing:

```text
exact UTC timestamps
```

Therefore:

```text
PUBLIC EVENT ORDER
!=
EXACT EVENT TIME
```

---

# Reconstructable Public Evidence

Phase 3B.1 supports reconstruction of:

```text
UWMS high-level architecture

Flight Day 1 fault indication

crew + Mission Control troubleshooting

return to normal toilet operations

Flight Day 4 wastewater vent ending early

tank-not-full status

toilet-operational status

possible-ice hypothesis

vent-heater response

Sun-pointing response

backup collection posture

postflight urine vent-line investigation
```

---

# Not Reconstructable from Current Public Evidence

The current source set does not support reconstruction of:

```text
exact Flight Day 1 fault UTC

internal UWMS fault code

exact failed component

Flight Day 1 root cause

exact wastewater vent start UTC

exact wastewater vent stop UTC

exact wastewater quantity vented

vent-line pressure telemetry

vent-line temperature telemetry

vent flow telemetry

exact heater duty cycle

confirmed ice presence

final vent-line root cause from early mission updates

complete crew waste-management usage history

complete Orion ECLSS telemetry
```

These remain explicitly unresolved.

---

# Critical Non-Equivalences

Phase 3B.1 enforces the following evidence boundaries:

```text
BLINKING_FAULT_LIGHT
!=
IDENTIFIED_FAILED_COMPONENT
```

```text
TOILET_FAULT_INDICATION
!=
COMPLETE_UWMS_FAILURE
```

```text
TOILET_RETURNED_TO_NORMAL
!=
ROOT_CAUSE_PUBLICLY_KNOWN
```

```text
VENT_ENDED_EARLY
!=
CONFIRMED_COMPLETE_BLOCKAGE
```

```text
POSSIBLE_ICE
!=
CONFIRMED_ICE
```

```text
VENT_HEATER_USE
!=
PROOF_OF_ICE
```

```text
SUN_POINTING
!=
ROOT_CAUSE_CONFIRMATION
```

```text
BACKUP_COLLECTION_AVAILABLE
!=
TOILET_INOPERATIVE
```

```text
TANK_NOT_FULL
!=
NOMINAL_VENT_LINE
```

```text
TOILET_OPERATIONAL
!=
NOMINAL_URINE_VENT_PATH
```

```text
POSTFLIGHT_INVESTIGATION
!=
FINAL_ROOT_CAUSE
```

```text
WASTEWATER_VENT_ISSUE
!=
FECAL_COLLECTION_FAILURE
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_waste_management_evidence.py
```

Validation result:

```text
Reference identity: PASS

Phase 3B.1 scope: PASS

UWMS architecture model: PASS

NASA source registry: PASS

NASA source URLs: PASS

Event registry: PASS

Event-source resolution: PASS

No fabricated exact UTCs: PASS
```

Flight Day 1:

```text
toilet fault evidence: PASS

restoration evidence: PASS

root-cause boundary: PASS
```

Flight Day 4:

```text
early vent termination evidence: PASS

tank-not-full status: PASS

toilet-operational status: PASS

vent-heater response: PASS

ice-confirmation boundary: PASS

Sun-pointing response: PASS

backup collection posture: PASS

postflight investigation status: PASS
```

Cross-product validation:

```text
Operational thread reconstruction: PASS

Critical non-equivalences: PASS

Public evidence limits: PASS

Evidence-boundary policy: PASS

Cross-thread chronology: PASS

FD1 / FD4 issue separation: PASS
```

Validated reference content:

```text
NASA sources
7

events
7

operational threads
2
```

Final result:

```text
PHASE 3B.1 VALIDATION PASSED
```

---

# Phase 3B.1 Status

```text
NASA SOURCE SET: ASSEMBLED

UWMS ARCHITECTURE: RECONSTRUCTED

FLIGHT DAY 1 TOILET FAULT THREAD: RECONSTRUCTED

FLIGHT DAY 1 RECOVERY: RECONSTRUCTED

FLIGHT DAY 4 WASTEWATER VENT THREAD: RECONSTRUCTED

VENT-HEATER RESPONSE: RECONSTRUCTED

SUN-POINTING RESPONSE: RECONSTRUCTED

BACKUP COLLECTION POSTURE: RECONSTRUCTED

POSTFLIGHT INVESTIGATION STATUS: RECONSTRUCTED

EXACT UNREPORTED EVENT UTCs: NOT FABRICATED

FINAL ROOT CAUSE: NOT CLAIMED

NASA SOURCE RESOLUTION: PASS

EVIDENCE BOUNDARIES: PASS

INDEPENDENT VALIDATION: PASS

PHASE 3B.1: COMPLETE
```

Next:

```text
Phase 3B.2
Waste Management Operational Decision Reconstruction
```

Phase 3B.2 will transform the validated NASA-reported evidence into explicit mission-operations decision threads:

```text
observation
↓
constraint
↓
available evidence
↓
crew / ground options
↓
selected response
↓
operational outcome
↓
remaining uncertainty
```

without converting public operational reporting into unavailable internal Mission Control rationale or telemetry.

---

---

# Phase 3B.2 — Waste Management Operational Decision Reconstruction

## Goal

Transform the validated Phase 3B.1 NASA-reported waste-management evidence into explicit mission-operations decision threads without reconstructing unavailable internal console logic, flight-rule reasoning, telemetry, or root-cause determinations.

Phase 3B.2 models the public operational sequence as:

```text
observation
↓
constraint / evidence state
↓
NASA-reported response
↓
operational outcome
↓
remaining uncertainty
```

This structure is MissionLab-derived.

It is not presented as an internal Mission Control decision log.

---

# Dependency

Phase 3B.2 depends directly on:

```text
data/reference/artemis_ii_waste_management_evidence.json
```

Dependency dataset:

```text
phase3b1_artemis_ii_waste_management_evidence
```

Validated Phase 3B.1 evidence:

```text
NASA sources
7

events
7

operational threads
2
```

Dependency validation:

```text
PASS
```

---

# Analysis

Created:

```text
scripts/analysis/analyze_waste_management_operations.py
```

Generated:

```text
data/processed/eclss/waste_management_operational_threads.json

data/processed/eclss/waste_management_operational_steps.csv
```

Documentation figure:

```text
docs/assets/eclss/phase3b2_waste_management_decision_threads.svg
```

---

# Reconstruction Scope

Phase 3B.2 reconstructs two independent operational threads:

```text
Flight Day 1
Toilet Fault and Recovery

Flight Day 4
Urine / Wastewater Vent-Line Issue
```

Total derived operational steps:

```text
16
```

Breakdown:

```text
Flight Day 1
6 steps

Flight Day 4
10 steps
```

---

# Flight Day 1 Operational Thread

Thread:

```text
flight_day_1_toilet_fault_and_recovery
```

Classification:

```text
IN_FLIGHT_OPERATIONAL_ISSUE_RESOLVED
```

Outcome:

```text
RESOLVED_IN_FLIGHT_WITH_ROOT_CAUSE_UNRESOLVED
```

---

## Step 1 — Observation

```text
Toilet-system checkout
↓
Blinking fault light reported
```

Evidence class:

```text
NASA_REPORTED
```

The public record establishes a fault indication.

It does not establish the internal failure mechanism.

---

## Step 2 — Operational Constraint

The public evidence supports:

```text
fault indication exists
```

but does not support:

```text
internal fault code

failed component

complete UWMS failure

root cause
```

Therefore:

```text
FAULT INDICATION
!=
COMPLETE UWMS FAILURE
```

---

## Step 3 — Evidence Assessment

NASA reported:

```text
Mission Control assessed available data
```

while working with the crew.

This is directly reported.

The specific telemetry, internal console products, fault trees, and decision criteria remain unavailable.

---

## Step 4 — Response

NASA reported:

```text
crew + Mission Control troubleshooting
```

Phase 3B.2 preserves the existence of troubleshooting.

It does not invent:

```text
specific corrective procedure

internal troubleshooting branch

console recommendation chain

flight-rule trigger

fault-code interpretation
```

Therefore:

```text
PUBLIC TROUBLESHOOTING REPORT
!=
COMPLETE INTERNAL DECISION TREE
```

---

## Step 5 — Outcome

NASA reported:

```text
NORMAL TOILET OPERATIONS RESTORED
```

Therefore:

```text
normal_operations_restored = TRUE
```

and:

```text
complete_uwms_failure_established = FALSE
```

---

## Step 6 — Remaining Uncertainty

The public record does not establish:

```text
failed component

fault code

specific repair action

root cause
```

Therefore:

```text
RESTORED OPERATION
!=
KNOWN ROOT CAUSE
```

Final Flight Day 1 boundary:

```text
root_cause_publicly_established = FALSE
```

---

# Flight Day 4 Operational Thread

Thread:

```text
flight_day_4_urine_wastewater_vent_line_issue
```

Classification:

```text
IN_FLIGHT_OPERATIONAL_ISSUE_MANAGED
```

Outcome:

```text
MANAGED_IN_FLIGHT_WITH_POSTFLIGHT_INVESTIGATION
```

---

## Step 1 — Planned Operation

NASA reported normal waste-management activity involving:

```text
wastewater venting overboard
```

Purpose:

```text
create additional tank capacity
```

---

## Step 2 — Observation

NASA reported:

```text
vent activity ended earlier than expected
```

This establishes an off-nominal operational observation.

It does not establish a complete blockage.

Therefore:

```text
VENT ENDED EARLY
!=
CONFIRMED BLOCKAGE
```

---

## Step 3 — Operational State

NASA explicitly reported:

```text
wastewater tank was not full

toilet remained operational
```

This significantly constrains interpretation.

Therefore:

```text
VENT-LINE ISSUE
!=
COMPLETE TOILET FAILURE
```

and:

```text
TANK NOT FULL
!=
NOMINAL VENT PATH
```

---

## Step 4 — Evidence Assessment

NASA publicly considered:

```text
possible ice
```

as one potential cause.

NASA also reported:

```text
other causes under review
```

Therefore:

```text
possible_ice_considered = TRUE

ice_confirmed = FALSE

other_causes_reviewed = TRUE
```

and:

```text
POSSIBLE ICE
!=
CONFIRMED ICE
```

---

## Step 5 — Vent-Heater Response

NASA reported:

```text
vent heaters used
```

as part of troubleshooting.

This is preserved as a reported response.

It does not establish:

```text
actual ice presence

successful ice removal

vent-line internal temperature

vent flow restoration
```

Therefore:

```text
VENT HEATER USE
!=
PROOF OF ICE
```

---

## Step 6 — Sun-Pointing Response

NASA reported that Orion was oriented so the vent faced the Sun.

Phase 3B.2 preserves this as:

```text
NASA_REPORTED_RESPONSE
```

The action supports troubleshooting.

It does not establish the physical root cause.

Therefore:

```text
SUN POINTING
!=
ROOT CAUSE CONFIRMATION
```

---

## Step 7 — Contingency Posture

NASA reported:

```text
backup collection devices available if needed
```

while also reporting:

```text
toilet remained operational
```

Therefore:

```text
CONTINGENCY AVAILABLE
!=
TOILET INOPERATIVE
```

---

## Step 8 — Inflight Outcome

The public evidence supports the following MissionLab operational synthesis:

```text
issue managed in flight

toilet operation continued

operational workarounds existed

complete loss of waste-management capability not established
```

This synthesis is:

```text
MISSIONLAB_DERIVED_OPERATIONAL_SYNTHESIS
```

It is not a verbatim NASA console conclusion.

The evidence does not establish that the vent-line issue was fully resolved during flight.

---

## Step 9 — Postflight Follow-Up

NASA's initial postflight assessment reported:

```text
hardware assessment

data gathering

continued investigation
```

related to the urine vent-line issue.

Therefore:

```text
postflight_investigation_continued = TRUE
```

---

## Step 10 — Remaining Uncertainty

The curated public record does not establish:

```text
confirmed ice

specific failed hardware

software fault

sensor fault

procedural root cause

final root cause
```

Therefore:

```text
root_cause_publicly_established = FALSE
```

and:

```text
POSTFLIGHT INVESTIGATION
!=
FINAL ROOT CAUSE
```

---

# Flight Day 1 / Flight Day 4 Separation

Phase 3B.2 explicitly preserves:

```text
FD1 issue == FD4 issue
FALSE
```

Shared system domain:

```text
Orion waste management
```

Shared root cause:

```text
NOT ESTABLISHED
```

Causal relationship:

```text
NOT ESTABLISHED
```

Therefore:

```text
SAME SPACECRAFT SYSTEM DOMAIN
!=
SAME FAILURE
```

and:

```text
FD1 PRECEDES FD4
!=
FD1 CAUSED FD4
```

---

# Internal Decision-Rationale Boundary

Phase 3B.2 reconstructs:

```text
public observation

publicly stated system condition

NASA-reported troubleshooting action

public operational outcome

remaining public uncertainty
```

Phase 3B.2 does not reconstruct:

```text
internal console loops

flight-controller discipline assignments

private voice loops

internal fault-tree logic

flight-rule triggers

telemetry thresholds

engineering backroom discussions

exact option ranking

internal risk trades
```

Therefore:

```text
MISSIONLAB OPERATIONAL THREAD
!=
MISSION CONTROL CONSOLE LOG
```

and:

```text
MISSIONLAB OPERATIONAL THREAD
!=
FLIGHT RULE LOGIC
```

---

# Temporal Boundary

None of the Phase 3B.2 operational steps assign exact event UTC values.

Therefore:

```text
exact_utc_known = FALSE
```

for every derived operational step.

This preserves the Phase 3B.1 evidence limit:

```text
relative order known

exact event timing unresolved
```

No timestamps are fabricated.

---

# Root-Cause Boundary

Every operational step enforces:

```text
root_cause_claim = FALSE
```

Both operational threads enforce:

```text
root_cause_publicly_established = FALSE
```

Therefore:

```text
OPERATIONAL RESPONSE
!=
ROOT CAUSE DETERMINATION
```

and:

```text
SUCCESSFUL TROUBLESHOOTING
!=
KNOWN FAILURE MECHANISM
```

---

# Traceability

Every Phase 3B.2 operational step includes:

```text
source event IDs

NASA source IDs

evidence class

public status

MissionLab provenance
```

Derived-step provenance:

```text
MISSIONLAB_DERIVED_OPERATIONAL_RECONSTRUCTION
```

This maintains a traceable chain:

```text
NASA SOURCE
↓
PHASE 3B.1 REFERENCE EVENT
↓
PHASE 3B.2 OPERATIONAL STEP
↓
MISSIONLAB INTERPRETATION BOUNDARY
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_waste_management_operations.py
```

Validation result:

```text
Analysis identity: PASS

Phase 3B.1 dependency: PASS

Reconstruction model: PASS
```

Operational structure:

```text
Operational thread set: PASS

Step ordering and numbering: PASS

16-step reconstruction: PASS
```

Flight Day 1:

```text
fault thread: PASS

recovery: PASS

root-cause boundary: PASS
```

Flight Day 4:

```text
vent thread: PASS

tank-not-full status: PASS

toilet-operational status: PASS

possible-ice hypothesis: PASS

ice-confirmation boundary: PASS

postflight investigation: PASS

root-cause boundary: PASS
```

Traceability:

```text
Step-event traceability: PASS

Step-source traceability: PASS

No inferred internal rationale: PASS

No fabricated exact UTCs: PASS

No root-cause claims: PASS

Reference evidence alignment: PASS
```

Cross-thread boundaries:

```text
FD1 / FD4 issue separation: PASS

Shared-root-cause boundary: PASS

Cross-thread causality boundary: PASS
```

Product validation:

```text
Evidence-boundary policy: PASS

Operational CSV / JSON consistency: PASS

Documentation figure: PASS
```

Validated reconstruction:

```text
operational threads
2

Flight Day 1 steps
6

Flight Day 4 steps
10

total operational steps
16
```

Final result:

```text
PHASE 3B.2 VALIDATION PASSED
```

---

# Phase 3B.2 Status

```text
PHASE 3B.1 DEPENDENCY: PASS

OPERATIONAL THREADS: 2

TOTAL DECISION STEPS: 16

FLIGHT DAY 1 THREAD: COMPLETE

FLIGHT DAY 4 THREAD: COMPLETE

PUBLIC OBSERVATIONS: PRESERVED

PUBLIC RESPONSES: PRESERVED

PUBLIC OUTCOMES: PRESERVED

EVENT TRACEABILITY: PASS

SOURCE TRACEABILITY: PASS

INTERNAL CONSOLE RATIONALE: NOT RECONSTRUCTED

EXACT UNREPORTED UTCs: NOT INVENTED

ROOT CAUSES: NOT INFERRED

FD1 / FD4 CAUSAL LINK: NOT ESTABLISHED

INDEPENDENT VALIDATION: PASS

PHASE 3B.2: COMPLETE
```

Next:

```text
Phase 3B.3
Waste Management Mission-Impact and Cross-Domain Correlation
```

Phase 3B.3 will connect the validated waste-management operations to mission-level effects that are actually supported publicly, including:

```text
spacecraft attitude response

trajectory-correction scheduling interaction

crew contingency posture

mission continuation

postflight investigation
```

while explicitly preventing unsupported claims that the waste-management issues caused trajectory changes, propulsion anomalies, ECLSS-wide failures, or mission-risk outcomes not stated in the public record.

---

---

# Phase 3B.3 — Waste Management Mission-Impact and Cross-Domain Correlation

## Goal

Integrate the validated Artemis II waste-management operational reconstruction with independently validated mission-level products while preventing temporal or operational correlation from being converted into unsupported causal claims.

Phase 3B.3 connects the Phase 3B waste-management evidence to:

```text
crew-ground operations

spacecraft attitude operations

trajectory-correction scheduling

crew contingency posture

downstream mission continuation

postflight engineering investigation
```

The analysis preserves actual cross-domain interaction without claiming unavailable mission impact, failure propagation, or root cause.

---

# Dependencies

Phase 3B.3 depends on:

```text
Phase 3B.1
Artemis II Waste Management Public Evidence Reconstruction

Phase 3B.2
Waste Management Operational Decision Reconstruction

Phase 2I.4
Maneuver Operational Threads

Phase 2K
Integrated Phase 2 Mission Operations
```

Validated dependency products:

```text
data/reference/artemis_ii_waste_management_evidence.json

data/processed/eclss/waste_management_operational_threads.json

data/reference/artemis_ii_maneuver_operational_threads.json

data/reference/artemis_ii_phase2_integrated_operations.json
```

Dependency status:

```text
PASS
```

---

# Analysis

Created:

```text
scripts/analysis/analyze_waste_management_mission_impact.py
```

Generated:

```text
data/processed/eclss/waste_management_cross_domain_correlations.csv

data/processed/eclss/waste_management_mission_impact.json
```

Documentation figure:

```text
docs/assets/eclss/phase3b3_waste_management_cross_domain.svg
```

Total validated cross-domain correlations:

```text
6
```

---

# Correlation 1 — Flight Day 1 Crew-Ground Recovery

Domain:

```text
CREW SYSTEMS + MISSION OPERATIONS
```

Public sequence:

```text
toilet checkout
↓
blinking fault indication
↓
Mission Control data assessment
↓
crew-ground troubleshooting
↓
normal toilet operations restored
```

Cross-domain relationship:

```text
CREW_GROUND_TROUBLESHOOTING
```

NASA reported the crew and Mission Control worked together to restore normal operations.

Therefore:

```text
crew_ground_recovery_interaction = TRUE
```

However:

```text
ROOT CAUSE PUBLIC = FALSE
```

and:

```text
MISSION-ENDING IMPACT ESTABLISHED = FALSE
```

Successful recovery does not reveal the internal troubleshooting tree or original failure mechanism.

---

# Correlation 2 — Flight Day 4 Spacecraft Attitude Support

Domain:

```text
GNC / ATTITUDE OPERATIONS
```

NASA reported that Orion's attitude was changed so the wastewater vent faced the Sun during troubleshooting.

The independent Phase 2 maneuver product also records:

```text
ATTITUDE_ADJUSTMENT_FOR_WASTEWATER_VENT_CLEARING
```

as parallel operational activity on April 4.

Therefore:

```text
SPACECRAFT ATTITUDE INTERACTION = TRUE
```

This establishes a real cross-domain interaction between:

```text
waste-management troubleshooting

and

spacecraft attitude operations
```

It does not establish:

```text
GNC anomaly
```

Therefore:

```text
ATTITUDE RESPONSE
!=
GNC ANOMALY
```

---

# Correlation 3 — Trajectory Scheduling Interaction

The Phase 2 maneuver reconstruction records OTC2 as:

```text
date
2026-04-04

status
CANCELLED

reason
TRAJECTORY_REMAINED_ON_TRACK
```

The same Phase 2 operational record separately identifies:

```text
parallel operational activity
ATTITUDE_ADJUSTMENT_FOR_WASTEWATER_VENT_CLEARING
```

Therefore Phase 3B.3 establishes:

```text
trajectory scheduling interaction = TRUE
```

but explicitly preserves:

```text
waste_issue_caused_otc2_cancellation = FALSE
```

The evidence supports:

```text
OTC2 cancelled because trajectory remained on track
```

not:

```text
OTC2 cancelled because of wastewater problem
```

Therefore:

```text
PARALLEL ACTIVITY
!=
CANCELLATION CAUSE
```

---

# OTC2 Failure Boundaries

Phase 2 already established:

```text
OTC2 failed burn
FALSE

OTC2 propulsion anomaly
FALSE
```

Phase 3B.3 preserves those boundaries.

Therefore:

```text
OTC2 CANCELLATION
!=
FAILED BURN
```

and:

```text
OTC2 CANCELLATION
!=
PROPULSION ANOMALY
```

No propulsion malfunction is inferred from the April 4 scheduling interaction.

---

# Correlation 4 — Crew Contingency Posture

Domain:

```text
CREW SYSTEMS + CONTINGENCY OPERATIONS
```

NASA reported that:

```text
backup collection devices were available if needed
```

while also reporting:

```text
toilet operational = TRUE

tank full = FALSE
```

Therefore the crew possessed a contingency path without evidence of complete UWMS loss.

Thus:

```text
CONTINGENCY AVAILABLE
!=
COMPLETE SYSTEM FAILURE
```

and:

```text
BACKUP CAPABILITY
!=
TOILET INOPERATIVE
```

---

# Correlation 5 — Downstream Mission Continuation

Following the April 4 waste-management issue, independently validated mission products preserve later mission operations including:

```text
OTC3

lunar flyby / pericynthion

Earth return

Entry Interface

splashdown
```

Validated downstream anchors:

```text
OTC3
2026-04-06T03:03:00Z

Pericynthion
2026-04-06T23:00:46.177998Z

Entry Interface
2026-04-10T23:53:00Z

Splashdown
2026-04-11T00:07:00Z
```

Therefore the public mission record establishes:

```text
later mission operations continued
```

after the waste-management issue.

However:

```text
MISSION CONTINUATION
!=
ZERO OPERATIONAL IMPACT
```

and:

```text
MISSION CONTINUATION
!=
ZERO RISK
```

Phase 3B.3 does not calculate or infer a quantitative mission-risk contribution from the waste-management issue.

---

# Correlation 6 — Postflight Engineering Follow-Up

Domain:

```text
POSTFLIGHT ENGINEERING
```

NASA's initial postflight assessment continued:

```text
hardware assessment

data gathering

urine vent-line investigation
```

Therefore:

```text
POSTFLIGHT INVESTIGATION CONTINUED = TRUE
```

This establishes engineering follow-up after mission completion.

It does not establish the investigation's eventual root-cause conclusion.

Therefore:

```text
POSTFLIGHT INVESTIGATION
!=
FINAL ROOT CAUSE
```

---

# Mission-Impact Assessment — Flight Day 1

Validated state:

```text
fault indication reported
TRUE

crew-ground troubleshooting reported
TRUE

normal toilet operations restored
TRUE

mission-ending impact established
FALSE

root cause public
FALSE
```

The evidence supports operational recovery.

It does not support an assertion that the issue had no operational cost, no crew workload impact, or no engineering consequence.

---

# Mission-Impact Assessment — Flight Day 4

Validated state:

```text
vent activity ended early
TRUE

spacecraft attitude response reported
TRUE

trajectory schedule interaction present
TRUE

waste issue caused OTC2 cancellation
FALSE

OTC2 cancelled for trajectory reason
TRUE

tank full
FALSE

toilet operational
TRUE

crew contingency available
TRUE

later mission operations recorded
TRUE

mission-ending impact established
FALSE

postflight investigation continued
TRUE

root cause public
FALSE
```

---

# Cross-Domain Correlation Boundary

Phase 3B.3 uses correlation to connect independently supported mission facts.

It does not automatically interpret temporal or operational proximity as causation.

Therefore:

```text
CROSS-DOMAIN CORRELATION
!=
CAUSATION
```

Examples:

```text
wastewater troubleshooting near OTC2 scheduling
!=
wastewater issue caused OTC2 cancellation
```

```text
attitude adjustment during troubleshooting
!=
GNC anomaly
```

```text
mission continued afterward
!=
issue had zero effect
```

```text
postflight investigation continued
!=
root cause known
```

---

# Temporal Precision Boundary

The exact UTC of the principal Flight Day 4 vent-line event remains unresolved in the public evidence.

Therefore Phase 3B.3 does not calculate:

```text
precise FD4 issue → OTC3 interval
```

even though OTC3 itself has a validated UTC anchor.

Thus:

```text
precise_interval_from_fd4_issue_to_otc3_computable
FALSE
```

This prevents date-level waste-management evidence from being falsely promoted to exact timing.

---

# Failure-Propagation Boundary

Phase 3B.3 does not infer that the waste-management issue propagated into:

```text
GNC

propulsion

trajectory-control performance

navigation

communications

thermal systems

complete ECLSS failure
```

unless public evidence explicitly establishes such a relationship.

Therefore:

```text
unreported_failure_propagation_inferred
FALSE
```

---

# Risk Boundary

No quantitative mission-risk calculation is derived from the public waste-management evidence.

Therefore:

```text
quantitative_mission_risk_inferred
FALSE
```

The existence of contingency equipment or continued mission operations cannot independently establish:

```text
zero risk

zero operational burden

zero crew impact

zero engineering concern
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_waste_management_mission_impact.py
```

Validation results:

```text
Analysis identity: PASS

Dependency registry: PASS

Phase 3B.1 evidence dependency: PASS

Phase 3B.2 operational dependency: PASS
```

Phase 2 cross-check:

```text
Phase 2 maneuver cross-reference: PASS

OTC2 cancellation reason: PASS

OTC2 wastewater parallel activity: PASS

OTC2 failed-burn boundary: PASS

OTC2 propulsion-anomaly boundary: PASS

Downstream mission anchors: PASS
```

Cross-domain products:

```text
Cross-domain correlation set: PASS

Correlation thread traceability: PASS

Correlation event traceability: PASS

Phase 2 anchor traceability: PASS

Correlation provenance: PASS
```

Mission-impact validation:

```text
Flight Day 1 mission-impact assessment: PASS

Flight Day 4 mission-impact assessment: PASS

Cross-domain boundary policy: PASS

Evidence-boundary policy: PASS

Correlation CSV / JSON consistency: PASS

Documentation figure: PASS
```

Validated correlations:

```text
crew-ground recovery
PASS

spacecraft attitude interaction
PASS

trajectory scheduling interaction
PASS

crew contingency posture
PASS

downstream mission continuation
PASS

postflight engineering follow-up
PASS
```

Final result:

```text
PHASE 3B.3 VALIDATION PASSED
```

---

# Phase 3B Complete Reconstruction Chain

Phase 3B now provides:

```text
NASA PUBLIC SYSTEM EVIDENCE
        ↓
SOURCE-TRACEABLE EVENTS
        ↓
TWO SEPARATE WASTE-MANAGEMENT THREADS
        ↓
OPERATIONAL DECISION RECONSTRUCTION
        ↓
16 TRACEABLE OPERATIONAL STEPS
        ↓
CROSS-DOMAIN MISSION CORRELATION
        ↓
PHASE 2 MANEUVER CROSS-CHECK
        ↓
MISSION-CONTINUATION CONTEXT
        ↓
POSTFLIGHT ENGINEERING FOLLOW-UP
        ↓
STRICT CAUSAL / ROOT-CAUSE BOUNDARIES
```

---

# Phase 3B Status

```text
Phase 3B.1
PUBLIC EVIDENCE RECONSTRUCTION
COMPLETE

Phase 3B.2
OPERATIONAL DECISION RECONSTRUCTION
COMPLETE

Phase 3B.3
MISSION-IMPACT / CROSS-DOMAIN CORRELATION
COMPLETE
```

Validated Phase 3B totals:

```text
NASA sources
7

NASA-reported events
7

primary operational threads
2

derived operational steps
16

cross-domain correlations
6
```

Evidence status:

```text
FLIGHT DAY 1 TOILET FAULT
RECONSTRUCTED

FLIGHT DAY 1 RECOVERY
RECONSTRUCTED

FLIGHT DAY 4 VENT-LINE ISSUE
RECONSTRUCTED

VENT-HEATER RESPONSE
RECONSTRUCTED

SUN-POINTING RESPONSE
RECONSTRUCTED

CREW CONTINGENCY POSTURE
RECONSTRUCTED

OTC2 CROSS-DOMAIN CONTEXT
VALIDATED

MISSION CONTINUATION
CORRELATED

POSTFLIGHT INVESTIGATION
RECONSTRUCTED

FD1 / FD4 SAME ISSUE
FALSE

SHARED ROOT CAUSE
NOT ESTABLISHED

OTC2 FAILURE
FALSE

PROPULSION ANOMALY FROM OTC2 CANCELLATION
FALSE

GNC ANOMALY FROM SUN-POINTING
FALSE

FINAL WASTE-MANAGEMENT ROOT CAUSE
NOT CLAIMED

EXACT UNREPORTED EVENT UTCs
NOT INVENTED

QUANTITATIVE MISSION RISK
NOT INFERRED

PHASE 3B
COMPLETE
```

---

# Next Phase 3 Work

The remaining Phase 3 roadmap scope now shifts away from waste management and into Orion thermal protection and materials:

```text
Artemis I heat-shield root cause
        ↓
Artemis II risk mitigation
        ↓
Artemis II as-flown / postflight evidence
        ↓
thermal protection and materials engineering synthesis
```

The next implementation package will begin the heat-shield evidence chain while preserving separation between:

```text
Artemis I heritage evidence

Artemis II preflight mitigation

Artemis II as-flown evidence

Artemis II postflight findings
```

---

---

# Phase 3C.1 — Artemis I → Artemis II TPS Heritage-to-Flight Risk Closure

## Goal

Promote the validated Phase 2F thermal-protection evidence into an explicit Phase 3 risk-closure chain connecting:

```text
Artemis I anomaly
↓
NASA root-cause determination
↓
entry-environment interaction
↓
Artemis II mitigation
↓
Artemis II as-flown configuration
↓
initial Artemis II postflight result
↓
bounded mitigation-effectiveness conclusion
```

Phase 3C.1 does not duplicate the Phase 2F thermal-protection evidence.

It uses the existing validated Phase 2F products as authoritative project dependencies and reorganizes them into the Phase 3 engineering-risk lifecycle required by the roadmap.

---

# Dependencies

Phase 3C.1 depends on:

```text
Phase 2F.1
Orion TPS Heritage Evidence

Phase 2F.2
Artemis Entry Profile Heritage

Phase 2F.4
TPS Physics Boundary
```

Dependency products:

```text
data/reference/artemis_tps_evidence.json

data/reference/artemis_entry_profile_heritage.json

data/reference/artemis_tps_physics_boundary.json
```

Dependency validation:

```text
PASS
```

---

# Analysis

Created:

```text
scripts/analysis/analyze_tps_risk_closure.py
```

Generated:

```text
data/processed/thermal/artemis_tps_risk_closure.json

data/processed/thermal/artemis_tps_risk_closure_steps.csv
```

Documentation figure:

```text
docs/assets/thermal/phase3c1_tps_risk_closure.svg
```

---

# Seven-Step Risk Closure Chain

Phase 3C.1 reconstructs seven evidence-backed stages:

```text
1. Artemis I anomaly

2. Artemis I root cause

3. entry-environment interaction

4. Artemis II mitigation

5. Artemis II as-flown configuration

6. initial Artemis II postflight outcome

7. evidence closure boundary
```

All seven stages are traceable to Phase 2F NASA evidence.

---

# Step 1 — Artemis I Heritage Anomaly

NASA reported unexpected Orion Avcoat char loss following Artemis I.

Phase 3C.1 preserves this as:

```text
HERITAGE_ANOMALY
```

The observed phenomenon was:

```text
unexpected char loss
```

across portions of the Artemis I Orion heat shield.

This observation identifies the heritage risk requiring investigation.

It does not by itself establish:

```text
complete heat-shield failure

crew safety failure

peak heat-flux exceedance

single-variable cause
```

Therefore:

```text
ARTEMIS I CHAR LOSS
!=
HEAT-SHIELD FAILURE
```

---

# Step 2 — NASA Root-Cause Determination

NASA's investigation identified the central material mechanism as:

```text
Avcoat heating
↓
pyrolysis / ablation gases generated
↓
low-permeability material restricts gas escape
↓
internal gas pressure increases
↓
cracking forms
↓
charred material is liberated
```

Validated mechanism:

```text
low permeability
TRUE

restricted gas escape
TRUE

internal pressure buildup
TRUE

cracking
TRUE

char liberation
TRUE
```

This mechanism is:

```text
NASA_REPORTED_ROOT_CAUSE
```

MissionLab preserves the mechanism as NASA-reported causal evidence.

MissionLab does not independently derive it.

---

# Permeability Evidence

NASA's investigation found that more permeable Avcoat regions did not exhibit the same behavior as the low-permeability material.

This supports:

```text
permeability
```

as a central variable in the Artemis I mechanism.

Therefore the project preserves:

```text
LOW PERMEABILITY
→
RESTRICTED GAS ESCAPE
→
PRESSURE BUILDUP
```

as NASA-reported material-response physics.

---

# Ground Replication

NASA reproduced the Artemis I-type behavior through ground testing.

Phase 3C.1 preserves:

```text
GROUND REPLICATION
```

as evidence supporting the identified causal mechanism.

This distinguishes the root-cause determination from a purely observational postflight hypothesis.

---

# Thermal Test Campaign

The inherited Phase 2F evidence preserves NASA's extensive investigation campaign:

```text
thermal test campaigns
8

individual tests
121
```

These tests are retained as investigation evidence.

MissionLab does not substitute its own external-heating model for NASA's material test campaign.

---

# Step 3 — Entry-Environment Interaction

NASA reported that the Artemis I skip-entry thermal history contributed to the conditions relevant to the Avcoat mechanism.

During the skip sequence:

```text
external heating decreased between atmospheric dips
```

while:

```text
thermal energy remained within the Avcoat
```

This condition contributed to continued gas generation and accumulation in low-permeability material.

Therefore the investigation chain contains both:

```text
material property

and

entry thermal history
```

The project does not simplify the root cause to:

```text
too much peak heating
```

Therefore:

```text
ARTEMIS I ROOT CAUSE
!=
SIMPLE PEAK HEAT-FLUX EXCEEDANCE
```

---

# Step 4 — Artemis II Risk Mitigation

NASA retained the already-integrated Artemis II heat shield and modified the entry environment to reduce conditions associated with the Artemis I cracking mechanism.

Phase 3C.1 preserves:

```text
existing_heat_shield_retained
TRUE
```

and:

```text
entry_environment_modified
TRUE
```

The mitigation strategy therefore targeted the environment experienced by the existing heat shield rather than replacing the integrated Artemis II TPS.

---

# Artemis II Entry Classification

NASA technical reporting establishes:

```text
MODIFIED_TRAJECTORY_WITHOUT_SKIP_ENTRY
```

for Artemis II.

Therefore:

```text
Artemis I-style skip entry used
FALSE
```

The project must not relabel Artemis II as a skip-entry mission.

---

# Loft / Rebound Boundary

Phase 2F already reconstructs a vertical rebound in the Artemis II entry trajectory.

That geometric behavior does not override NASA's authoritative entry classification.

Therefore:

```text
NO SKIP ENTRY
!=
NO ALTITUDE REBOUND
```

MissionLab may describe the Artemis II structure as:

```text
loft

rebound

lofted entry sequence
```

while preserving:

```text
NOT ARTEMIS I-STYLE SKIP ENTRY
```

---

# Step 5 — Artemis II As-Flown Configuration

Phase 3C.1 distinguishes:

```text
planned mitigation
```

from:

```text
mitigation actually flown
```

NASA technical evidence states that Artemis II flew the modified trajectory without the Artemis I-style skip entry.

Therefore:

```text
modified_no_skip_trajectory_flown
TRUE
```

This closes the implementation link:

```text
identified heritage mechanism
↓
defined mitigation
↓
mitigation executed in flight
```

---

# Guidance-Design Boundary

The public record supports the high-level entry-profile mitigation.

It does not expose the complete internal Artemis II guidance design.

Therefore:

```text
full_internal_guidance_design_public
FALSE
```

MissionLab does not infer:

```text
guidance gains

trajectory optimization weights

internal entry targeting constraints

private flight-rule thresholds

complete onboard guidance-law implementation
```

---

# Step 6 — Initial Artemis II Postflight Outcome

NASA's initial Artemis II assessment reported that the thermal protection system:

```text
performed as expected
```

with:

```text
no unusual TPS conditions identified initially
```

Phase 3C.1 preserves:

```text
initial_tps_performance_expected
TRUE
```

and:

```text
unusual_tps_conditions_identified_initially
FALSE
```

---

# Artemis I-Type Char Loss

NASA reported that Artemis I-type char loss on Artemis II was:

```text
significantly reduced
```

in:

```text
quantity

and

size
```

Therefore:

```text
artemis_i_type_char_loss_reduced
TRUE
```

This supports the conclusion that the flight mitigation reduced the previously observed phenomenon.

---

# Quantitative Char-Loss Boundary

NASA's public description is qualitative.

MissionLab does not possess a public calibrated flight damage map suitable for deriving a percentage reduction.

Therefore:

```text
char_loss_reduction_quantified_publicly
FALSE
```

and:

```text
SIGNIFICANTLY REDUCED
!=
KNOWN REDUCTION PERCENTAGE
```

MissionLab does not invent:

```text
percent char-loss reduction

lost material mass

lost area

local recession depth

failure probability
```

---

# Arc-Jet Consistency

NASA reported that Artemis II heat-shield performance was consistent with post-Artemis I arc-jet testing.

Phase 3C.1 preserves:

```text
consistent_with_post_artemis_i_arcjet_testing
TRUE
```

This provides a direct link between:

```text
post-Artemis I ground test campaign

and

Artemis II flight performance
```

without implying that MissionLab itself reproduces the arc-jet material-response solution.

---

# Step 7 — Evidence Closure Boundary

Phase 3C.1 supports the following closure level:

```text
INITIAL_FLIGHT_MITIGATION_EFFECTIVENESS_SUPPORTED
```

The chain now contains:

```text
heritage anomaly identified
TRUE

heritage root cause identified
TRUE

mitigation defined
TRUE

mitigation flown
TRUE

initial postflight outcome available
TRUE

initial postflight outcome supports mitigation
TRUE
```

However:

```text
final_material_analysis_publicly_complete
FALSE
```

Therefore the project does not describe this stage as complete final sample-level material closure.

---

# MissionLab Quantitative Frontier

The Phase 2F physics boundary remains unchanged.

MissionLab quantitatively reconstructs:

```text
trajectory

Earth-relative entry state

atmospheric density

Mach

Knudsen number

external convective heating

integrated external heat load

loft / rebound geometry

heating-history segmentation
```

The quantitative frontier ends at:

```text
EXTERNAL CONVECTIVE HEATING
```

---

# Material-Response Boundary

The material-response boundary begins at:

```text
SURFACE / INTERNAL THERMAL RESPONSE
```

MissionLab does not calculate:

```text
Avcoat surface temperature

through-thickness temperature

thermal gradients

pyrolysis rate

gas-generation rate

gas transport

local permeability field

internal gas pressure

thermal stress

mechanical stress

strain

crack initiation

crack propagation

char-layer structural response

recession depth

char-loss mass

char-loss area
```

Therefore:

```text
EXTERNAL HEATING MODEL
!=
AVCOAT DAMAGE MODEL
```

---

# Prohibited Model Bridges

Phase 3C.1 preserves the Phase 2F prohibition against directly converting:

```text
external Sutton-Graves heat flux
→
internal Avcoat temperature
```

```text
external heat load
→
pyrolysis rate
```

```text
external heat load
→
internal gas pressure
```

```text
loft / rebound geometry
→
crack probability
```

```text
external heating history
→
char-loss quantity
```

```text
Artemis I / Artemis II trajectory difference
→
numerical char-loss reduction percentage
```

These bridges remain unsupported by the current MissionLab model and public quantitative data.

---

# Critical Evidence Boundaries

Phase 3C.1 enforces:

```text
ARTEMIS I CHAR LOSS
!=
HEAT-SHIELD FAILURE
```

```text
ARTEMIS I ROOT CAUSE
!=
SIMPLE PEAK HEAT-FLUX EXCEEDANCE
```

```text
ARTEMIS II NO-SKIP
!=
NO ALTITUDE REBOUND
```

```text
ARTEMIS I / ARTEMIS II PROFILE DIFFERENCE
!=
ENTIRELY CAUSED BY TPS CONSIDERATIONS
```

```text
EXTERNAL HEATING MODEL
!=
INTERNAL AVCOAT TEMPERATURE MODEL
```

```text
EXTERNAL HEATING MODEL
!=
INTERNAL GAS-PRESSURE MODEL
```

```text
EXTERNAL HEATING MODEL
!=
CRACKING MODEL
```

```text
EXTERNAL HEATING MODEL
!=
CHAR-LOSS MODEL
```

```text
SIGNIFICANTLY REDUCED
!=
KNOWN NUMERICAL REDUCTION PERCENTAGE
```

```text
INITIAL POSTFLIGHT ASSESSMENT
!=
FINAL MATERIAL CLOSURE
```

---

# Traceability

Every Phase 3C.1 risk-closure step includes:

```text
step order

closure stage

mission context

Phase 2F evidence IDs

evidence class

engineering statement

closure role

root-cause claim flag

quantitative-damage claim flag

final-closure claim flag

MissionLab provenance
```

Derived-step provenance:

```text
MISSIONLAB_DERIVED_TPS_RISK_CLOSURE
```

Traceability chain:

```text
NASA TECHNICAL / MISSION EVIDENCE
↓
PHASE 2F EVIDENCE ITEM
↓
PHASE 3C.1 CLOSURE STEP
↓
RISK-CLOSURE INTERPRETATION
↓
EXPLICIT MODEL / EVIDENCE BOUNDARY
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_tps_risk_closure.py
```

Initial validator run exposed a validator-only indexing error:

```text
PHASE 3C.1 VALIDATION FAILED:
Artemis II no-skip guardrail missing
```

Cause:

```text
interpretation_guardrails
```

exist at the top level of:

```text
artemis_entry_profile_heritage.json
```

while the validator incorrectly attempted to retrieve them from the indexed evidence-item dictionary.

The reference data and Phase 3C.1 analysis products were correct.

The validator was corrected to inspect the top-level entry-heritage product.

---

# Final Independent Validation

Final validation:

```text
Analysis identity: PASS

Dependency registry: PASS
```

Phase 2F evidence:

```text
Phase 2F.1 TPS evidence set: PASS

Artemis I anomaly evidence: PASS

Artemis I root-cause evidence: PASS

Permeability evidence: PASS

Ground-replication evidence: PASS

Thermal-test campaign evidence: PASS

Artemis II mitigation evidence: PASS

Artemis II postflight evidence: PASS
```

Physics boundary:

```text
TPS quantitative frontier: PASS

Material-response boundary: PASS

Forbidden model bridges: PASS

No Avcoat damage model: PASS
```

Entry heritage:

```text
Artemis I skip-entry classification: PASS

Artemis II no-skip classification: PASS

Entry-profile interpretation guardrails: PASS
```

Closure-chain validation:

```text
Seven-step closure chain: PASS

Closure ordering: PASS

Evidence traceability: PASS

NASA root-cause claim boundary: PASS

No quantitative damage claims: PASS

No final material-closure claim: PASS
```

Summary validation:

```text
Artemis I root-cause mechanism summary: PASS

Artemis II mitigation summary: PASS

Artemis II initial postflight summary: PASS

Closure-level assessment: PASS

Evidence-boundary policy: PASS
```

Product validation:

```text
Closure CSV / JSON consistency: PASS

Documentation figure: PASS
```

Final result:

```text
PHASE 3C.1 VALIDATION PASSED
```

---

# Validated Risk-Closure Chain

```text
1
ARTEMIS I ANOMALY
PASS

2
ARTEMIS I ROOT CAUSE
PASS

3
ENTRY-ENVIRONMENT ROLE
PASS

4
ARTEMIS II MITIGATION
PASS

5
ARTEMIS II AS-FLOWN CONFIGURATION
PASS

6
INITIAL ARTEMIS II POSTFLIGHT OUTCOME
PASS

7
EVIDENCE CLOSURE BOUNDARY
PASS
```

---

# Phase 3C.1 Status

```text
PHASE 2F TPS EVIDENCE DEPENDENCY
PASS

PHASE 2F PHYSICS BOUNDARY DEPENDENCY
PASS

ENTRY HERITAGE DEPENDENCY
PASS

ARTEMIS I ANOMALY
PRESERVED

ARTEMIS I ROOT CAUSE
PRESERVED

LOW-PERMEABILITY MECHANISM
PRESERVED

GROUND REPLICATION
PRESERVED

THERMAL TEST CAMPAIGN
PRESERVED

ARTEMIS II MITIGATION
PRESERVED

ARTEMIS II NO-SKIP CLASSIFICATION
PRESERVED

ARTEMIS II MITIGATION AS-FLOWN
CONFIRMED

INITIAL TPS PERFORMANCE
EXPECTED

ARTEMIS I-TYPE CHAR LOSS
SIGNIFICANTLY REDUCED

PUBLIC NUMERICAL CHAR-LOSS REDUCTION
NOT AVAILABLE

ARC-JET CONSISTENCY
PRESERVED

AVCOAT INTERNAL MATERIAL MODEL
NOT CREATED

QUANTITATIVE DAMAGE MODEL
NOT CREATED

FINAL SAMPLE-LEVEL MATERIAL CLOSURE
NOT CLAIMED

INITIAL FLIGHT MITIGATION EFFECTIVENESS
SUPPORTED

INDEPENDENT VALIDATION
PASS

PHASE 3C.1
COMPLETE
```

---

# Next

```text
Phase 3C.2
Thermal Protection and Materials Engineering Synthesis
```

Phase 3C.2 will build the engineering explanation layer that connects:

```text
external entry heating

Avcoat ablative behavior

pyrolysis

gas transport

permeability

pressure buildup

fracture / char liberation

trajectory mitigation

arc-jet testing

Artemis II flight evidence
```

while preserving the distinction between:

```text
NASA-reported material physics

MissionLab-modeled external aerothermodynamics

MissionLab-derived engineering synthesis
```

The goal is to produce the roadmap's thermal-protection/material-science explainer without inventing proprietary Avcoat properties or extending the existing Sutton-Graves model beyond its defensible quantitative boundary.

---

---

# Phase 3C.2 — Artemis II Thermal Protection and Materials Engineering Synthesis

## Goal

Complete the Phase 3 thermal-protection and materials-science requirement by connecting the validated Artemis II entry environment, Orion Avcoat architecture, Artemis I material-response investigation, Artemis II risk mitigation, and Artemis II postflight evidence into one engineering synthesis.

Phase 3C.2 explicitly separates:

```text
MissionLab quantitative external aerothermodynamics

NASA-reported internal material physics

NASA-reported flight observations

MissionLab-derived engineering synthesis
```

The purpose is not to create an unavailable Avcoat material-response model.

The purpose is to explain the full engineering chain while maintaining a strict quantitative boundary at the external entry environment.

---

# Dependencies

Phase 3C.2 depends on:

```text
Phase 2E.4
Sutton-Graves Convective Heating Reconstruction

Phase 2F.1
Orion TPS Heritage Evidence

Phase 2F.4
TPS Physics Boundary

Phase 3C.1
Artemis I → Artemis II TPS Heritage-to-Flight Risk Closure
```

Dependency products:

```text
data/reference/artemis_ii_convective_heating_model.json

data/reference/artemis_tps_evidence.json

data/reference/artemis_tps_physics_boundary.json

data/processed/thermal/artemis_tps_risk_closure.json
```

Dependency validation:

```text
PASS
```

---

# Analysis

Created:

```text
scripts/analysis/analyze_tps_materials_synthesis.py
```

Generated:

```text
data/processed/thermal/artemis_tps_materials_synthesis.json

data/processed/thermal/artemis_tps_materials_synthesis_stages.csv
```

Documentation figure:

```text
docs/assets/thermal/phase3c2_tps_materials_synthesis.svg
```

---

# Synthesis Structure

Phase 3C.2 reconstructs:

```text
9 engineering stages

7 engineering relations
```

The nine stages are:

```text
1. Orion heat-shield architecture

2. external entry environment

3. ablative surface response

4. pyrolysis and gas generation

5. permeability and gas transport

6. internal gas-pressure response

7. cracking and char liberation

8. trajectory-based risk mitigation

9. Artemis II flight evidence
```

---

# Stage 1 — Orion Heat-Shield Architecture

Material:

```text
Avcoat
```

Validated architecture context:

```text
heat-shield diameter
16.5 ft

Avcoat blocks
186
```

Primary engineering role:

```text
ABLATIVE THERMAL PROTECTION
```

The heat shield protects the Orion crew module from the energy associated with lunar-return atmospheric entry.

The Avcoat material is designed to undergo controlled ablative response.

Therefore:

```text
EXPECTED MATERIAL LOSS THROUGH ABLATION
=
NORMAL TPS FUNCTION
```

while:

```text
UNEXPECTED CHAR LIBERATION
!=
NORMAL ABLATION
```

This distinction is fundamental to interpreting the Artemis I heat-shield investigation.

---

# Stage 2 — External Entry Environment

MissionLab quantitatively reconstructs:

```text
trajectory

Earth-relative flow conditions

atmospheric density

Mach

Knudsen number

external convective heating

integrated external heat load
```

The external heating model is based on:

```text
Sutton-Graves stagnation-point convective heating correlation
```

Provenance:

```text
MODEL_DERIVED
```

The result is an engineering estimate of:

```text
external stagnation-point convective heat flux
```

It is not:

```text
measured Artemis II heat flux
```

and is not:

```text
an internal Avcoat material-response solution
```

---

# Sutton-Graves Model Boundary

The Phase 2E.4 heating model explicitly preserves:

```text
cold-wall approximation

radiative heating not included

finite wall temperature not modeled

Avcoat ablation not modeled

pyrolysis not modeled

blowing not modeled

surface recession not modeled

detailed nonequilibrium chemistry not modeled
```

Therefore:

```text
MODEL-DERIVED EXTERNAL HEATING
!=
FLIGHT-MEASURED HEATING
```

and:

```text
EXTERNAL HEATING MODEL
!=
TPS MATERIAL-RESPONSE MODEL
```

---

# Stage 3 — Ablative Surface Response

NASA evidence establishes Avcoat as an ablative TPS material.

Its thermal-protection function involves controlled material response under severe heating.

Phase 3C.2 preserves that qualitative engineering behavior.

MissionLab does not calculate:

```text
surface temperature

wall temperature

surface recession

local ablation rate

material mass loss

char thickness
```

Therefore:

```text
can_missionlab_calculate
FALSE
```

for the ablative material-response stage.

---

# Normal Ablation / Abnormal Char-Loss Boundary

Phase 3C.2 explicitly distinguishes:

```text
expected controlled ablation
```

from:

```text
unexpected Artemis I char liberation
```

Therefore:

```text
EXPECTED ABLATION
!=
UNEXPECTED CHAR LIBERATION
```

The Artemis I phenomenon must not be described simply as the expected operation of an ablative heat shield.

---

# Stage 4 — Pyrolysis and Gas Generation

NASA's Artemis I investigation establishes that as Avcoat heats:

```text
material response occurs
↓
pyrolysis / ablation generates gases
```

The internal material state may continue evolving even as the external heating environment changes.

This is important because the Artemis I mechanism cannot be represented by:

```text
peak external heat flux only
```

The relevant behavior depends on:

```text
thermal history

internal energy

gas generation

gas transport

material permeability
```

MissionLab preserves this physics as:

```text
NASA_REPORTED_MECHANISM
```

MissionLab does not calculate:

```text
pyrolysis rate

gas-generation rate

internal stored thermal energy

chemical decomposition rate
```

---

# Stage 5 — Permeability and Gas Transport

NASA identified:

```text
low Avcoat permeability
```

as a central factor in the Artemis I root-cause mechanism.

The engineering sequence is:

```text
gases generated internally
↓
gases attempt to escape through material
↓
low permeability restricts venting
```

NASA also reported that more permeable regions did not exhibit the same behavior.

Therefore:

```text
LOW PERMEABILITY
→
RESTRICTED GAS TRANSPORT
```

is preserved as NASA-reported material physics.

MissionLab does not possess:

```text
public flight permeability field

sample-by-sample permeability distribution

gas-transport coefficients

porous-flow material model
```

Therefore:

```text
permeability field calculated by MissionLab
FALSE
```

---

# Stage 6 — Internal Gas-Pressure Response

NASA's root-cause investigation established:

```text
restricted gas escape
↓
internal gas-pressure buildup
```

The internal pressure described here is a material-response quantity.

It is not the same quantity as:

```text
external static pressure

external dynamic pressure

aerodynamic pressure reconstructed from trajectory
```

Therefore:

```text
EXTERNAL DYNAMIC PRESSURE
!=
AVCOAT INTERNAL GAS PRESSURE
```

MissionLab does not calculate:

```text
pore pressure

internal gas pressure

pressure gradients inside Avcoat
```

---

# Stage 7 — Cracking and Char Liberation

NASA's Artemis I root-cause chain continues:

```text
internal gas-pressure buildup
↓
cracking
↓
charred material liberation
```

Phase 3C.2 preserves this as:

```text
NASA_REPORTED_CAUSAL_OUTCOME
```

MissionLab does not calculate:

```text
stress

strain

fracture mechanics

crack initiation

crack propagation

crack probability

char-loss area

char-loss mass

recession depth
```

Therefore:

```text
OBSERVED / NASA-REPORTED MATERIAL RESPONSE
!=
MISSIONLAB DAMAGE PREDICTION
```

---

# Stage 8 — Trajectory-Based Risk Mitigation

Phase 3C.1 established the Artemis II mitigation chain.

NASA retained the already-integrated Artemis II heat shield and changed the entry environment.

The mitigation included flying:

```text
MODIFIED TRAJECTORY WITHOUT ARTEMIS I-STYLE SKIP ENTRY
```

Therefore:

```text
Artemis II entry environment modified
TRUE
```

```text
Artemis I-style skip entry flown
FALSE
```

```text
modified no-skip profile flown
TRUE
```

The engineering strategy reduced exposure to conditions associated with the Artemis I cracking mechanism.

---

# Thermal-History Risk Management

The mitigation connects:

```text
entry trajectory
↓
external thermal history
↓
material-response environment
```

without implying that trajectory alone constitutes the material model.

Therefore:

```text
TRAJECTORY MITIGATION
!=
COMPLETE MATERIAL-RESPONSE MODEL
```

The public evidence supports the mitigation strategy.

It does not expose:

```text
complete internal trajectory optimization

all entry guidance constraints

guidance gains

private TPS limits

flight-rule logic
```

---

# Stage 9 — Artemis II Flight Evidence

NASA's initial Artemis II postflight assessment reported:

```text
TPS performed as expected
```

and:

```text
no unusual TPS conditions identified initially
```

NASA also reported that Artemis I-type char loss was:

```text
significantly reduced
```

in:

```text
quantity

and

size
```

NASA further reported consistency with:

```text
post-Artemis I arc-jet testing
```

Therefore the flight record supports:

```text
INITIAL FLIGHT MITIGATION EFFECTIVENESS
```

---

# Quantitative Postflight Boundary

NASA's public description does not supply a calibrated numerical flight damage map.

Therefore MissionLab does not calculate:

```text
percent char-loss reduction

lost char mass

lost char area

local recession map

crack-density reduction

failure probability
```

Thus:

```text
SIGNIFICANTLY REDUCED
!=
KNOWN NUMERICAL PERCENTAGE
```

---

# Artemis I Investigation Context

Phase 3C.2 preserves the scale of NASA's Artemis I investigation.

Instrumentation included:

```text
pressure sensors

strain gauges

thermocouples
```

Material campaign:

```text
approximate Avcoat samples
200
```

Thermal test campaign:

```text
campaigns
8

individual tests
121
```

Ground reproduction of the behavior:

```text
REPORTED
```

---

# Investigation Data Boundary

MissionLab does not possess the complete raw investigation dataset.

It does not contain complete public time-series products for:

```text
pressure sensors

strain gauges

internal thermocouple depths

material sample measurements

full arc-jet facility instrumentation

full coupled material-response model
```

Therefore:

```text
NASA INVESTIGATION EVIDENCE
!=
MISSIONLAB RAW MATERIAL TEST DATASET
```

and:

```text
MissionLab reproduces NASA material test campaign
FALSE
```

---

# Nine-Stage Engineering Chain

Phase 3C.2 now provides:

```text
ORION HEAT-SHIELD ARCHITECTURE
        ↓
EXTERNAL ENTRY ENVIRONMENT
        ↓
ABLATIVE SURFACE RESPONSE
        ↓
PYROLYSIS / GAS GENERATION
        ↓
PERMEABILITY / GAS TRANSPORT
        ↓
INTERNAL GAS-PRESSURE RESPONSE
        ↓
CRACKING / CHAR LIBERATION
        ↓
TRAJECTORY-BASED RISK MITIGATION
        ↓
ARTEMIS II FLIGHT EVIDENCE
```

---

# Seven Engineering Relations

Phase 3C.2 defines seven explicit engineering relations:

```text
1.
external flow
→
heating / material boundary
```

```text
2.
heating / material response
→
pyrolysis and gas generation
```

```text
3.
gas generation
→
gas transport through material
```

```text
4.
restricted transport
→
internal pressure buildup
```

```text
5.
internal pressure
→
cracking and char liberation
```

```text
6.
entry environment
→
trajectory-based risk mitigation
```

```text
7.
mitigation
→
Artemis II flight outcome
```

---

# Quantitative Bridge Policy

Every Phase 3C.2 engineering relation enforces:

```text
quantitative_bridge_allowed = FALSE
```

This means the synthesis may explain NASA-reported physics but may not fabricate equations linking MissionLab external quantities to unavailable internal material states.

Examples:

```text
Sutton-Graves heat flux
!=
Avcoat surface temperature
```

```text
external heat load
!=
pyrolysis rate
```

```text
external dynamic pressure
!=
internal Avcoat gas pressure
```

```text
external heating history
!=
crack probability
```

```text
external heating history
!=
char-loss quantity
```

---

# MissionLab Quantitative Frontier

Validated quantitative reconstruction:

```text
trajectory / external flow
TRUE

external convective heating
TRUE
```

Validated non-quantitative material stages:

```text
surface temperature
FALSE

internal Avcoat temperature
FALSE

pyrolysis rate
FALSE

permeability field
FALSE

internal gas pressure
FALSE

cracking / fracture
FALSE

char-loss quantity
FALSE
```

Total quantitative internal material stages:

```text
0
```

This is intentional.

It is an evidence-quality boundary rather than a missing implementation.

---

# Material Mechanism Summary

Validated mechanism:

```text
external entry heating
↓
Avcoat thermal response
↓
pyrolysis and gas generation
↓
gas transport through material
↓
restricted venting in low-permeability regions
↓
internal gas-pressure buildup
↓
cracking
↓
char liberation
```

Mechanism provenance:

```text
NASA_REPORTED
```

MissionLab quantitative material model:

```text
FALSE
```

---

# Engineering Boundaries

Phase 3C.2 explicitly enforces:

```text
EXPECTED ABLATION
!=
UNEXPECTED CHAR LIBERATION
```

```text
EXTERNAL HEAT FLUX
!=
SURFACE TEMPERATURE
```

```text
EXTERNAL HEAT FLUX
!=
INTERNAL AVCOAT TEMPERATURE
```

```text
EXTERNAL HEAT LOAD
!=
PYROLYSIS RATE
```

```text
EXTERNAL DYNAMIC PRESSURE
!=
INTERNAL GAS PRESSURE
```

```text
EXTERNAL HEAT LOAD
!=
CRACK PROBABILITY
```

```text
EXTERNAL HEATING HISTORY
!=
CHAR-LOSS QUANTITY
```

```text
NO-SKIP ENTRY
!=
NO ALTITUDE REBOUND
```

```text
TRAJECTORY MITIGATION
!=
COMPLETE MATERIAL MODEL
```

```text
SIGNIFICANTLY REDUCED
!=
KNOWN REDUCTION PERCENTAGE
```

```text
INITIAL POSTFLIGHT RESULT
!=
FINAL MATERIAL CLOSURE
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_tps_materials_synthesis.py
```

Validation results:

```text
Analysis identity: PASS

Dependency registry: PASS
```

Materials evidence:

```text
Materials evidence set: PASS

Orion heat-shield architecture: PASS

Artemis I instrumentation: PASS

Artemis I sample campaign: PASS

Artemis I thermal testing: PASS
```

External aerothermal model:

```text
Sutton-Graves model identity: PASS

External-heating interpretation limits: PASS
```

Physics boundary:

```text
TPS quantitative frontier: PASS

Material-response boundary: PASS

Internal material stages remain non-quantitative: PASS

Forbidden material-model assertions: PASS
```

Materials synthesis:

```text
Nine-stage materials synthesis: PASS

Stage ordering: PASS

Stage evidence traceability: PASS

Stage physics traceability: PASS

Quantitative frontier enforcement: PASS
```

Engineering relations:

```text
Seven engineering relations: PASS

Relation topology: PASS

Unsupported quantitative bridges prohibited: PASS

NASA-supported causal relations preserved: PASS
```

Summary products:

```text
Architecture summary: PASS

External-model boundary summary: PASS

Artemis I investigation summary: PASS

Material-mechanism summary: PASS

Artemis II mitigation / flight summary: PASS

Engineering-boundary policy: PASS
```

Roadmap and artifact validation:

```text
Phase 3 roadmap coverage: PASS

Synthesis CSV / JSON consistency: PASS

Documentation figure: PASS
```

Final result:

```text
PHASE 3C.2 VALIDATION PASSED
```

---

# Validated Phase 3C.2 Totals

```text
materials synthesis stages
9

engineering relations
7

quantitative internal material stages
0

approximate Artemis I Avcoat samples
200

Artemis I thermal test campaigns
8

individual Artemis I thermal tests
121
```

---

# Phase 3C Complete Reconstruction Chain

Phase 3C now provides:

```text
ARTEMIS I HEAT-SHIELD ANOMALY
        ↓
NASA ROOT-CAUSE INVESTIGATION
        ↓
LOW-PERMEABILITY AVCOAT MECHANISM
        ↓
ENTRY THERMAL-HISTORY INTERACTION
        ↓
ARTEMIS II RISK MITIGATION
        ↓
MODIFIED NO-SKIP PROFILE FLOWN
        ↓
INITIAL ARTEMIS II POSTFLIGHT RESULT
        ↓
SIGNIFICANTLY REDUCED ARTEMIS I-TYPE CHAR LOSS
        ↓
NASA ARC-JET CONSISTENCY
        ↓
THERMAL / MATERIALS ENGINEERING SYNTHESIS
        ↓
STRICT QUANTITATIVE MODEL BOUNDARY
```

---

# Phase 3C Status

```text
Phase 3C.1
TPS HERITAGE-TO-FLIGHT RISK CLOSURE
COMPLETE

Phase 3C.2
THERMAL PROTECTION / MATERIALS ENGINEERING SYNTHESIS
COMPLETE

PHASE 3C
COMPLETE
```

---

# Phase 3 Roadmap Closure Assessment

The Phase 3 roadmap requires:

```text
cabin / environmental trends from released sensors

toilet fault and wastewater vent decision threads

change-point / anomaly analysis labeled project-derived

Artemis I heat-shield root cause
→
Artemis II risk mitigation
→
postflight closure chain

thermal protection / material-science explainer
```

Current implementation status:

```text
environmental sensor normalization
COMPLETE

environmental trend reconstruction
COMPLETE

environmental change-point / anomaly analysis
COMPLETE

waste-management public evidence reconstruction
COMPLETE

waste-management operational decision reconstruction
COMPLETE

waste-management cross-domain correlation
COMPLETE

TPS heritage-to-flight risk closure
COMPLETE

thermal protection / materials engineering synthesis
COMPLETE
```

Therefore:

```text
PHASE 3A
COMPLETE

PHASE 3B
COMPLETE

PHASE 3C
COMPLETE
```

and:

```text
PHASE 3 ROADMAP DELIVERABLES
COMPLETE
```

---

# Phase 3 Evidence Boundaries Preserved

Phase 3 completion does not imply reconstruction of unavailable internal spacecraft telemetry or proprietary engineering models.

The following remain intentionally unresolved or non-quantitative:

```text
complete Orion cabin atmosphere telemetry

complete ECLSS telemetry

internal UWMS fault codes

final public waste-management root causes

exact unreported waste-management UTCs

complete internal Mission Control reasoning

internal Avcoat temperature fields

pyrolysis rates

gas-generation rates

permeability fields

internal gas-pressure fields

stress / strain fields

fracture mechanics

crack probabilities

char-loss mass

char-loss area

numerical char-loss reduction percentage

final sample-level Artemis II material closure
```

These boundaries are part of the project methodology.

---

# Phase 3 Final Status

```text
PHASE 3 — ECLSS, VEHICLE SYSTEMS, THERMAL, MATERIALS

Environmental data
COMPLETE

Environmental trends
COMPLETE

Derived change-point / anomaly analysis
COMPLETE

Waste-management evidence
COMPLETE

Waste-management operational threads
COMPLETE

Waste-management cross-domain reconstruction
COMPLETE

Artemis I TPS root-cause chain
COMPLETE

Artemis II TPS mitigation chain
COMPLETE

Initial Artemis II TPS postflight closure
COMPLETE

Thermal / materials engineering explainer
COMPLETE

Evidence boundaries
PRESERVED

Independent subphase validation
PASS

PHASE 3
COMPLETE
```

---

---

# Phase 4A.1 — Artemis II Entry, Descent, Splashdown, and Recovery Public Evidence Reconstruction

## Goal

Establish the public evidence foundation for Artemis II:

```text
entry preparation
↓
atmospheric entry
↓
planned communications blackout
↓
parachute descent
↓
splashdown
↓
crew recovery
↓
spacecraft recovery
```

Phase 4A.1 deliberately reuses the validated Phase 2 quantitative entry reconstruction rather than rebuilding:

```text
trajectory

atmosphere

Mach

rarefaction

convective heating

entry-event trajectory correlations

TPS physics
```

The new Phase 4 scope extends the mission record beyond the Phase 2 entry analysis into the full operational return and recovery sequence.

---

# Reference Product

Created:

```text
data/reference/artemis_ii_entry_descent_recovery_evidence.json
```

Dataset:

```text
phase4a1_artemis_ii_entry_descent_recovery_evidence
```

Status:

```text
REFERENCE_EVIDENCE_ASSEMBLED
```

---

# Evidence Sources

Validated NASA / NASA-reference sources:

```text
5
```

Source registry:

```text
NASA_A2_FLIGHT_DAY_10_LIVE_REENTRY_2026_04_10

NASA_A2_PRESS_KIT

NASA_ORION_FUN_FACTS

NASA_ARTEMIS_II_REFERENCE_GUIDE_2026

NASA_ORION_CREW_MODULE_REFERENCE
```

Primary as-flown source:

```text
Artemis II Flight Day 10:
Live Re-Entry Updates
```

The primary live mission source provides the public operational timeline from final return preparation through crew and spacecraft recovery.

---

# Time Interpretation

NASA live-update timestamps are preserved as:

```text
PUBLIC UPDATE MINUTES
```

They are not promoted into:

```text
exact second-level telemetry epochs
```

Timezone interpretation:

```text
Eastern Daylight Time
UTC - 4
```

The UTC date rollover after midnight is preserved.

Example:

```text
Entry Interface
2026-04-10T23:53:00Z

communications reacquisition
2026-04-11T00:00:00Z

drogues
2026-04-11T00:03:00Z

mains
2026-04-11T00:04:00Z

splashdown
2026-04-11T00:07:00Z
```

Validation:

```text
UTC midnight rollover
PASS
```

---

# Phase 2 Reuse Boundary

Phase 4A.1 explicitly depends on:

```text
data/reference/artemis_ii_entry_events.json
```

and the existing Phase 2 entry analysis stack:

```text
scripts/analysis/analyze_entry_dynamics.py

scripts/analysis/build_entry_atmosphere.py

scripts/analysis/build_entry_mach.py

scripts/analysis/build_entry_rarefaction.py

scripts/analysis/build_entry_heating.py

scripts/analysis/correlate_entry_events.py
```

Already reconstructed in Phase 2:

```text
Entry Interface trajectory state

atmospheric density

Mach

rarefaction

external convective heating

drogue altitude correlation

main-parachute altitude correlation

derived zero-altitude surface crossing

splashdown public-minute correlation
```

Therefore:

```text
PHASE 4 REUSES PHASE 2 ENTRY PHYSICS
```

and:

```text
PHASE 4 DOES NOT RECOMPUTE PHASE 2 ENTRY PHYSICS
```

---

# Orion Parachute Architecture

NASA reference material establishes the Orion parachute system architecture.

Total:

```text
11 parachutes
```

Architecture:

```text
3 forward bay cover parachutes
7 ft each

2 drogue parachutes
23 ft each

3 pilot parachutes
11 ft each

3 main parachutes
116 ft each
```

Functional sequence:

```text
forward bay cover parachutes
↓
forward bay cover removal
↓
drogue parachutes
↓
stabilization / deceleration
↓
pilot parachutes
↓
main parachute deployment
↓
three main parachutes
↓
final descent
↓
ocean splashdown
```

---

# Architecture / As-Flown Boundary

The 11-parachute system description is:

```text
NASA_REPORTED_SYSTEM_ARCHITECTURE
```

It is not itself:

```text
an Artemis II as-flown event log
```

Therefore:

```text
PLANNED / SYSTEM ARCHITECTURE
!=
AS-FLOWN DEPLOYMENT CONFIRMATION
```

The primary live mission record explicitly confirms:

```text
drogue deployment
TRUE

three main parachutes deployed
TRUE
```

It does not separately timestamp:

```text
forward bay cover parachutes

pilot parachutes
```

Therefore their exact Artemis II deployment times are not inferred.

---

# Public Operational Evidence Set

Validated public events:

```text
15
```

Chronological evidence sequence:

```text
1.
DSN → NSN handover

2.
crew module / service module separation

3.
crew module raise burn

4.
Entry Interface

5.
planned plasma communications blackout

6.
communications reacquisition

7.
drogue deployment

8.
three main parachutes deployed

9.
splashdown

10.
post-splashdown spacecraft powerdown

11.
recovery-team approach

12.
crew extracted

13.
helicopter transfer

14.
crew aboard USS John P. Murtha

15.
Orion secured in recovery-ship well deck
```

---

# Final Communications Network Handover

NASA reported completion of the transition from:

```text
Deep Space Network
```

to:

```text
Near Space Network /
Tracking and Data Relay Satellite system
```

Public minute:

```text
2026-04-10T23:15:00Z
```

This marks the communications transition associated with the final return phase.

---

# Crew Module / Service Module Separation

Public minute:

```text
2026-04-10T23:33:00Z
```

NASA reported:

```text
crew module separated from service module
```

Operational consequence:

```text
crew module continues toward entry

service module no longer part of crew-module entry configuration

heat shield exposed for atmospheric return
```

Exact separation second:

```text
NOT PUBLICLY ESTABLISHED
```

---

# Crew Module Raise Burn

Public minute:

```text
2026-04-10T23:37:00Z
```

NASA reported the crew module raise burn as part of entry preparation.

Public interpretation:

```text
spacecraft orientation adjusted
↓
heat shield aligned for re-entry
```

Not publicly established:

```text
burn duration

delta-v

complete guidance law

private targeting logic
```

---

# Entry Interface

Public minute:

```text
2026-04-10T23:53:00Z
```

NASA reported:

```text
altitude
400,000 ft

speed description
approximately Mach 35

distance to splashdown site
about 1,956 statute miles
```

This event already exists in the Phase 2 trajectory reconstruction and Phase 4 preserves exact traceability to it.

Phase 2 cross-reference:

```text
entry_interface
PASS
```

---

# Planned Plasma Communications Blackout

NASA reported a planned entry communications blackout beginning shortly after Entry Interface.

Reported expected duration:

```text
about 6 minutes
```

Cause classification:

```text
PLASMA COMMUNICATIONS BLOCKAGE DURING ENTRY
```

Operational classification:

```text
PLANNED
```

Anomaly classification:

```text
FALSE
```

Therefore:

```text
PLASMA BLACKOUT
!=
COMMUNICATIONS ANOMALY
```

---

# Blackout Precision Boundary

The public evidence does not provide:

```text
exact blackout start second

exact blackout end second
```

Therefore MissionLab does not manufacture them.

The reported phrase:

```text
about six minutes
```

is preserved as an approximate public mission statement.

Thus:

```text
EXPECTED SIX-MINUTE BLACKOUT
!=
EXACT MEASURED SIX-MINUTE INTERVAL
```

---

# Communications Reacquisition

Public minute:

```text
2026-04-11T00:00:00Z
```

NASA reported communications contact with Orion reestablished.

The existence of:

```text
Entry Interface at 23:53

reacquisition update at 00:00
```

does not justify deriving an exact seven-minute blackout because the public event times are minute-resolution mission updates rather than exact telemetry epochs.

Therefore:

```text
blackout_exact_duration_derivable
FALSE
```

---

# Drogue Deployment

Public minute:

```text
2026-04-11T00:03:00Z
```

NASA reported:

```text
drogue deployment
23,400 ft

reported speed
479 ft/s

reported distance from splashdown
0.8 statute miles
```

Architecture:

```text
2 drogue parachutes
```

Operational role:

```text
slow and stabilize Orion
```

Phase 2 cross-reference:

```text
drogue_deploy
PASS
```

---

# Drogue Data Precision Boundary

The NASA live update reports several associated conditions around the drogue event.

MissionLab does not assume that:

```text
23,400 ft

479 ft/s

0.8 miles from splashdown
```

all represent one identical sub-second spacecraft state.

Therefore:

```text
PUBLIC EVENT UPDATE VALUES
!=
SYNCHRONIZED SUB-SECOND TELEMETRY SAMPLE
```

---

# Main Parachute Deployment

Public minute:

```text
2026-04-11T00:04:00Z
```

NASA reported:

```text
drogues cut
5,400 ft

three main parachutes deployed

velocity reduced to
less than 200 ft/s
```

Architecture:

```text
3 main parachutes
```

As-flown deployment confirmation:

```text
TRUE
```

Reported deployed count:

```text
3
```

Phase 2 cross-reference:

```text
main_deploy
PASS
```

---

# Individual Parachute Telemetry Boundary

Public confirmation of parachute deployment does not expose:

```text
individual canopy inflation histories

reefing-stage timing

individual suspension-line loads

individual canopy loads

individual deployment seconds

parachute sensor telemetry
```

Therefore:

```text
PARACHUTE DEPLOYMENT REPORT
!=
INDIVIDUAL PARACHUTE PERFORMANCE TELEMETRY
```

---

# Splashdown

Public minute:

```text
2026-04-11T00:07:00Z
```

NASA reported successful parachute-assisted splashdown:

```text
Pacific Ocean
off the coast of San Diego
```

Phase 2 cross-reference:

```text
splashdown
PASS
```

The curated public source does not establish precise coordinates.

Therefore:

```text
PARACHUTE-ASSISTED SPLASHDOWN REPORT
!=
EXACT SPLASHDOWN COORDINATES
```

No coordinates are invented.

---

# Post-Splashdown Powerdown

NASA reported Orion entering crew-module powerdown after splashdown.

Flight controllers:

```text
shut down nonessential systems
```

and transitioned Orion toward:

```text
recovery configuration
```

Exact UTC:

```text
NOT PUBLICLY ESTABLISHED
```

The event is therefore preserved as:

```text
AFTER_SPLASHDOWN
```

rather than assigned an invented timestamp.

---

# Recovery-Team Approach

Public minute:

```text
2026-04-11T00:12:00Z
```

NASA reported that:

```text
NASA and U.S. military recovery personnel
```

began approaching Orion in inflatable boats at the direction of the NASA recovery director.

This begins the direct recovery-team interaction with the spacecraft.

---

# Crew Extraction

Public minute:

```text
2026-04-11T01:34:00Z
```

NASA reported:

```text
all four Artemis II crewmembers
safely extracted
```

Crew status:

```text
SAFELY_EXTRACTED
```

The crew was reported on the inflatable recovery raft known as:

```text
the front porch
```

---

# Crew Extraction Boundary

Safe extraction establishes:

```text
successful crew removal from spacecraft
```

It does not establish:

```text
complete postflight medical results
```

Therefore:

```text
CREW SAFELY EXTRACTED
!=
COMPLETE MEDICAL ASSESSMENT
```

---

# Helicopter Transfer

Public minute:

```text
2026-04-11T01:56:00Z
```

NASA reported the Artemis II crew hoisted into U.S. military helicopters for transport to:

```text
USS John P. Murtha
```

---

# Crew Aboard Recovery Ship

Public minute:

```text
2026-04-11T01:58:00Z
```

NASA reported:

```text
Artemis II crew safely aboard
USS John P. Murtha
```

Crew status:

```text
ABOARD_RECOVERY_SHIP
```

Post-mission medical evaluation followed aboard the ship.

---

# Spacecraft Recovery

NASA's public recovery architecture describes:

```text
recovery-team approach

diver operations

winch-line attachment

tending lines

spacecraft tow

well-deck positioning

placement over recovery cradle

well-deck drainage

spacecraft securing
```

These procedural elements explain the recovery process.

They are not automatically assigned exact timestamps unless NASA separately reports them.

Therefore:

```text
RECOVERY PROCEDURE DESCRIPTION
!=
EXACT AS-FLOWN EVENT TIMELINE
```

---

# Orion Secured in Well Deck

Public minute:

```text
2026-04-11T08:27:00Z
```

NASA reported:

```text
Orion secured in the well deck
of USS John P. Murtha
```

Spacecraft status:

```text
SECURED_IN_RECOVERY_SHIP_WELL_DECK
```

This closes the Phase 4A.1 operational evidence sequence.

---

# Recovery Completion Boundary

Securing Orion aboard the recovery ship does not mean:

```text
postflight spacecraft analysis complete
```

Therefore:

```text
SPACECRAFT RECOVERY
!=
POSTFLIGHT ENGINEERING CLOSURE
```

Orion postflight transport and engineering analysis occur downstream.

---

# Operational Threads

Phase 4A.1 defines five evidence-backed operational threads:

```text
1.
entry_preparation_and_configuration

2.
entry_communications_blackout

3.
parachute_descent_and_splashdown

4.
crew_recovery

5.
spacecraft_recovery
```

Total:

```text
5
```

---

# Thread 1 — Entry Preparation and Configuration

Sequence:

```text
DSN → NSN handover
↓
crew module / service module separation
↓
crew module raise burn
↓
Entry Interface
```

Interpretation:

```text
Orion transitioned from deep-space return configuration
to crew-module atmospheric-entry configuration
```

---

# Thread 2 — Entry Communications Blackout

Sequence:

```text
Entry Interface
↓
planned plasma blackout
↓
communications reacquisition
```

Interpretation:

```text
planned communications interruption
during atmospheric entry
```

No anomaly is inferred.

---

# Thread 3 — Parachute Descent and Splashdown

Sequence:

```text
drogue deployment
↓
main parachute deployment
↓
splashdown
```

NASA explicitly confirmed:

```text
drogues

all three main parachutes

successful splashdown
```

---

# Thread 4 — Crew Recovery

Sequence:

```text
splashdown
↓
spacecraft powerdown
↓
recovery-team approach
↓
crew extraction
↓
helicopter transfer
↓
crew aboard recovery ship
```

---

# Thread 5 — Spacecraft Recovery

Sequence:

```text
splashdown
↓
recovery-team operations
↓
Orion secured in ship well deck
```

This separates:

```text
crew recovery
```

from:

```text
spacecraft recovery
```

while preserving their shared operational context.

---

# Critical Non-Equivalences

Phase 4A.1 explicitly preserves ten non-equivalences.

```text
PLANNED PARACHUTE ARCHITECTURE
!=
AS-FLOWN DEPLOYMENT CONFIRMATION
```

```text
PUBLIC UPDATE MINUTE
!=
EXACT TELEMETRY EPOCH
```

```text
EXPECTED SIX-MINUTE BLACKOUT
!=
EXACT SIX-MINUTE MEASURED BLACKOUT
```

```text
COMMUNICATIONS BLACKOUT
!=
COMMUNICATIONS ANOMALY
```

```text
DROGUE DEPLOYMENT REPORT
!=
INDIVIDUAL DROGUE PERFORMANCE TELEMETRY
```

```text
THREE MAIN PARACHUTES REPORTED DEPLOYED
!=
COMPLETE MAIN-PARACHUTE LOAD TELEMETRY
```

```text
PARACHUTE-ASSISTED SPLASHDOWN
!=
EXACT SPLASHDOWN COORDINATES
```

```text
RECOVERY PROCEDURE DESCRIPTION
!=
EXACT AS-FLOWN RECOVERY EVENT TIME
```

```text
CREW SAFELY EXTRACTED
!=
COMPLETE POSTFLIGHT MEDICAL RESULT
```

```text
ORION SECURED IN WELL DECK
!=
POSTFLIGHT SPACECRAFT ANALYSIS COMPLETE
```

---

# Public Evidence Limits

Not publicly reconstructed from the curated evidence:

```text
exact second-level CM/SM separation time

raise-burn duration

raise-burn delta-v

complete raise-burn guidance law

exact plasma-blackout start second

exact plasma-blackout end second

exact measured blackout duration

complete communications signal-strength history

individual forward bay cover parachute deployment times

individual drogue deployment times

individual pilot parachute deployment times

individual main parachute deployment times

individual canopy inflation histories

individual suspension-line loads

reefing telemetry

exact splashdown coordinates

exact water-impact velocity

complete post-splashdown attitude history

exact powerdown start / completion seconds

complete recovery command timeline

complete crew medical data

exact Orion winch-line attachment time

exact well-deck ingress start time
```

These remain deliberately unresolved.

---

# Evidence Boundary Policy

Validated:

```text
Phase 2 quantitative entry products reused
TRUE

Phase 4 recomputes Phase 2 entry physics
FALSE

public event minutes preserved
TRUE

exact unreported seconds invented
FALSE

planned blackout treated as anomaly
FALSE

parachute architecture treated as as-flown log
FALSE

forward bay cover deployment time inferred
FALSE

pilot parachute deployment time inferred
FALSE

individual parachute loads inferred
FALSE

exact splashdown coordinates inferred
FALSE

recovery procedure converted into invented timestamps
FALSE

private console rationale inferred
FALSE
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_entry_descent_recovery_evidence.py
```

Validation results:

```text
Reference identity: PASS

Scope definition: PASS

Source registry: PASS

Public time-resolution policy: PASS

Phase 2 reuse boundary: PASS
```

Parachute architecture:

```text
Orion parachute architecture: PASS

11-parachute architecture: PASS

Architecture / as-flown separation: PASS
```

Event set:

```text
15-event public evidence set: PASS

Event chronology: PASS

UTC midnight rollover: PASS
```

Communications blackout:

```text
Plasma-blackout evidence: PASS

Planned blackout / anomaly boundary: PASS

No fabricated blackout seconds: PASS
```

Entry / descent:

```text
Entry Interface evidence: PASS

Drogue deployment evidence: PASS

Main-parachute deployment evidence: PASS

Splashdown evidence: PASS

Phase 2 event cross-reference: PASS
```

Parachute evidence boundaries:

```text
Forward bay cover evidence boundary: PASS

Drogue as-flown confirmation: PASS

Pilot-parachute evidence boundary: PASS

Three-main as-flown confirmation: PASS
```

Recovery:

```text
Post-splashdown powerdown evidence: PASS

Recovery-team approach: PASS

Crew extraction: PASS

Helicopter transfer: PASS

Crew aboard recovery ship: PASS

Orion secured in well deck: PASS
```

Evidence integrity:

```text
Operational-thread set: PASS

Operational event traceability: PASS

Critical non-equivalences: PASS

Evidence-boundary policy: PASS
```

Final result:

```text
PHASE 4A.1 VALIDATION PASSED
```

---

# Validated Phase 4A.1 Totals

```text
NASA / NASA-reference sources
5

public operational events
15

operational threads
5

Orion parachute architecture
11 parachutes

critical non-equivalences
10
```

---

# Phase 4A.1 Status

```text
ENTRY PREPARATION PUBLIC EVIDENCE
COMPLETE

ENTRY INTERFACE CROSS-REFERENCE
COMPLETE

PLASMA BLACKOUT PUBLIC EVIDENCE
COMPLETE

DROGUE PUBLIC EVIDENCE
COMPLETE

MAIN PARACHUTE PUBLIC EVIDENCE
COMPLETE

SPLASHDOWN PUBLIC EVIDENCE
COMPLETE

CREW RECOVERY PUBLIC EVIDENCE
COMPLETE

SPACECRAFT RECOVERY PUBLIC EVIDENCE
COMPLETE

PARACHUTE ARCHITECTURE
DOCUMENTED

ARCHITECTURE / AS-FLOWN SEPARATION
PRESERVED

PHASE 2 ENTRY REUSE BOUNDARY
PRESERVED

EXACT UNREPORTED EVENT SECONDS
NOT INVENTED

PHASE 4A.1
COMPLETE
```

---

# Next

```text
Phase 4A.2
Entry-to-Recovery Operational Timeline Reconstruction
```

Phase 4A.2 will transform the validated 15-event evidence set into a unified operational timeline with:

```text
event ordering

public-minute intervals

relative-duration relationships

Phase 2 entry-state cross-links

communications-state transitions

parachute-state transitions

crew-recovery state transitions

spacecraft-recovery state transitions
```

while preserving:

```text
minute-resolution public evidence
!=
second-level telemetry
```

and avoiding reconstruction of unavailable parachute or recovery telemetry.

---

---

# Phase 4A.2 — Artemis II Entry-to-Recovery Operational Timeline Reconstruction

## Goal

Transform the validated Phase 4A.1 public evidence set into one operational timeline spanning:

```text
final return preparation
↓
crew-module entry configuration
↓
atmospheric entry
↓
planned plasma blackout
↓
communications reacquisition
↓
parachute descent
↓
splashdown
↓
crew recovery
↓
spacecraft recovery
```

Phase 4A.2 integrates:

```text
NASA-reported public event minutes

relative-order-only public events

Phase 2 derived entry states

MissionLab-derived operational states
```

without converting public mission updates into second-level telemetry.

---

# Analysis

Created:

```text
scripts/analysis/analyze_entry_to_recovery_timeline.py
```

Generated:

```text
data/processed/recovery/entry_to_recovery_operational_timeline.json

data/processed/recovery/entry_to_recovery_operational_timeline.csv
```

Documentation figure:

```text
docs/assets/recovery/phase4a2_entry_to_recovery_timeline.svg
```

Dataset:

```text
phase4a2_artemis_ii_entry_to_recovery_operational_timeline
```

Status:

```text
ENTRY_TO_RECOVERY_TIMELINE_COMPLETE
```

---

# Dependencies

Phase 4A.2 depends on:

```text
Phase 4A.1
public entry / descent / splashdown / recovery evidence

Phase 2
entry event trajectory correlations
```

Validated:

```text
Phase 4A.1 public evidence
PASS

Phase 2 entry correlations
PASS
```

---

# Operational Timeline

Total operational events:

```text
15
```

Public-minute anchored events:

```text
13
```

Relative-order-only events:

```text
2
```

Public-minute intervals:

```text
12
```

Operational state transitions:

```text
36
```

Phase 2 trajectory-state crosslinks:

```text
4
```

---

# Unified Event Sequence

The reconstructed operational timeline is:

```text
1.
DSN → NSN handover

2.
crew module / service module separation

3.
crew module raise burn

4.
Entry Interface

5.
planned plasma communications blackout

6.
communications reacquisition

7.
drogue parachute deployment

8.
three main parachutes deployed

9.
splashdown

10.
post-splashdown spacecraft powerdown

11.
recovery-team approach

12.
crew extracted

13.
helicopter transfer

14.
crew aboard USS John P. Murtha

15.
Orion secured in well deck
```

---

# Time Basis

Thirteen events contain:

```text
NASA_REPORTED_PUBLIC_MINUTE
```

Two events deliberately remain without fabricated exact timestamps:

```text
A2_ENTRY_PLASMA_BLACKOUT

A2_POST_SPLASHDOWN_POWERDOWN
```

Their time bases are:

```text
NASA_REPORTED_RELATIVE_ORDER_APPROXIMATE_DURATION

NASA_REPORTED_RELATIVE_ORDER
```

respectively.

Therefore:

```text
RELATIVE-ORDER EVENT
!=
FABRICATED TIMESTAMP
```

---

# Public-Minute Relationship Policy

Phase 4A.2 calculates differences between NASA public-update minute anchors.

These are:

```text
MISSIONLAB_DERIVED_PUBLIC_MINUTE_DIFFERENCE
```

They are not:

```text
exact operational durations
```

Every interval enforces:

```text
exact_operational_duration = FALSE
```

Therefore:

```text
PUBLIC-MINUTE DIFFERENCE
!=
EXACT TELEMETRY DURATION
```

---

# Entry Preparation Timing Relationships

Validated public-minute differences:

```text
DSN → NSN handover
to
CM / SM separation

18 minutes
```

```text
CM / SM separation
to
crew module raise burn

4 minutes
```

```text
crew module raise burn
to
Entry Interface

16 minutes
```

These values describe the spacing between public mission-update minute anchors.

They are not promoted to exact maneuver timing.

---

# Entry Communications Relationship

Validated public-minute difference:

```text
Entry Interface
to
communications reacquisition

7 minutes
```

NASA separately described the planned blackout as:

```text
about 6 minutes
```

These are not inconsistent measurements of one exact quantity because:

```text
Entry Interface public minute
!=
exact blackout-start second
```

and:

```text
reacquisition public minute
!=
exact blackout-end second
```

Therefore:

```text
7-MINUTE PUBLIC UPDATE DIFFERENCE
!=
EXACT BLACKOUT DURATION
```

---

# Post-Reacquisition Descent Relationships

Validated public-minute relationships:

```text
communications reacquisition
to
drogue deployment

3 minutes
```

```text
drogue deployment
to
main parachute deployment

1 minute
```

```text
main parachute deployment
to
splashdown

3 minutes
```

Again, these are public-minute relationships rather than exact telemetry durations.

---

# Recovery Relationships

Validated public-minute relationships:

```text
splashdown
to
recovery-team approach

5 minutes
```

```text
splashdown
to
crew extraction

87 minutes
```

```text
splashdown
to
crew aboard recovery ship

111 minutes
```

```text
splashdown
to
Orion secured in well deck

500 minutes
```

Additional recovery relationships:

```text
crew extraction
to
helicopter transfer

22 minutes
```

```text
helicopter transfer
to
crew aboard recovery ship

2 minutes
```

```text
crew aboard recovery ship
to
Orion secured in well deck

389 minutes
```

These provide a public operational-scale view of recovery without inventing unavailable second-level recovery logs.

---

# Operational State Model

Phase 4A.2 tracks six state dimensions:

```text
mission_phase

communications_state

vehicle_configuration

parachute_state

crew_state

recovery_state
```

Total derived state transitions:

```text
36
```

Provenance:

```text
MISSIONLAB_DERIVED_OPERATIONAL_STATE_TRANSITION
```

---

# Mission-Phase Progression

Mission phase progresses through:

```text
ENTRY_PREPARATION
↓
ATMOSPHERIC_ENTRY
↓
PARACHUTE_DESCENT
↓
SPLASHDOWN
↓
POST_SPLASHDOWN_RECOVERY
↓
CREW_RECOVERY
↓
SPACECRAFT_RECOVERY
```

---

# Communications-State Progression

Operational communications state progresses through:

```text
NSN_HANDOVER_COMPLETE
↓
ENTRY_COMMUNICATIONS_AVAILABLE
↓
CONTACT_BEFORE_PLASMA_BLACKOUT
↓
PLANNED_PLASMA_BLACKOUT
↓
CONTACT_REACQUIRED
↓
CONTACT_AVAILABLE
↓
POST_ENTRY_CONTACT_AVAILABLE
↓
POST_SPLASHDOWN_CONTACT
↓
RECOVERY_OPERATIONS
```

The blackout remains classified as:

```text
PLANNED
```

rather than:

```text
ANOMALY
```

---

# Vehicle-Configuration Progression

Vehicle configuration progresses through:

```text
CREW_MODULE_SERVICE_MODULE_INTEGRATED
↓
CREW_MODULE_ONLY
↓
ENTRY_ATTITUDE_CONFIGURED
↓
CREW_MODULE_ATMOSPHERIC_ENTRY
↓
CREW_MODULE_DESCENT
↓
CREW_MODULE_AFLOAT
↓
RECOVERY_CONFIGURATION_TRANSITION
↓
SECURED_IN_WELL_DECK
```

---

# Parachute-State Progression

Parachute state progresses through:

```text
STOWED
↓
DROGUES_DEPLOYED
↓
THREE_MAIN_PARACHUTES_DEPLOYED
↓
PARACHUTE_DESCENT_COMPLETE
↓
DESCENT_SYSTEM_COMPLETE
```

No individual canopy telemetry is inferred.

---

# Crew-State Progression

Crew state progresses through:

```text
ABOARD_ORION
↓
EXTRACTED_TO_FRONT_PORCH_RAFT
↓
HELICOPTER_TRANSFER
↓
ABOARD_RECOVERY_SHIP
```

This preserves the operational distinction between:

```text
spacecraft splashdown
```

and:

```text
crew recovery completion
```

---

# Recovery-State Progression

Recovery state progresses through:

```text
NOT_STARTED
↓
SPLASHDOWN_COMPLETE
↓
SPACECRAFT_SAFING
↓
RECOVERY_TEAM_APPROACH
↓
CREW_EXTRACTED
↓
CREW_TRANSFER_TO_SHIP
↓
CREW_RECOVERY_AT_SHIP_COMPLETE
↓
SPACECRAFT_RECOVERY_AT_SHIP_COMPLETE
```

This provides a clear distinction between:

```text
crew recovery
```

and:

```text
spacecraft recovery
```

---

# Phase 2 Trajectory-State Integration

Phase 4A.2 preserves four existing Phase 2 derived trajectory states.

Crosslinked events:

```text
Entry Interface

drogue deployment

main parachute deployment

splashdown
```

Crosslink count:

```text
4
```

---

# Entry Interface Phase 2 Crosslink

Phase 2 section:

```text
entry_interface
```

Phase 2 state:

```text
derived
```

Provenance:

```text
PHASE2_DERIVED_FROM_NASA_FLIGHT_DERIVED_EPHEMERIS
```

This preserves the reconstructed trajectory state at Entry Interface without reclassifying it as direct telemetry.

---

# Drogue Phase 2 Crosslink

Phase 2 section:

```text
drogue_deploy
```

Phase 2 state:

```text
altitude_anchor
```

This preserves the Phase 2 trajectory-derived state associated with NASA's reported drogue deployment altitude.

---

# Main Parachute Phase 2 Crosslink

Phase 2 section:

```text
main_deploy
```

Phase 2 state:

```text
altitude_anchor
```

This preserves the Phase 2 derived state associated with the reported 5,400-ft main-parachute event.

---

# Splashdown Phase 2 Crosslink

Phase 2 section:

```text
splashdown
```

Phase 2 state:

```text
derived_surface_crossing
```

This is preserved as:

```text
DERIVED_SPLASHDOWN_CORRELATED_SURFACE_CROSSING
```

rather than:

```text
official NASA exact splashdown telemetry epoch
```

---

# Derived-State Boundary

The operational timeline explicitly preserves:

```text
PHASE 2 DERIVED STATE
!=
NASA-REPORTED TELEMETRY
```

The trajectory states originate from:

```text
NASA flight-derived ephemeris
+
MissionLab reconstruction
```

They remain:

```text
DERIVED
```

---

# Phase 2 Reuse Boundary

Phase 4A.2 does not recompute:

```text
entry geometry

Earth-relative speed

atmospheric model

Mach

rarefaction

convective heating

entry trajectory

surface crossing
```

Instead:

```text
Phase 2 results
→
Phase 4 operational crosslinks
```

Therefore:

```text
PHASE 4 REUSE
!=
PHASE 2 PHYSICS RECOMPUTATION
```

---

# Operational Timeline Figure

Created:

```text
docs/assets/recovery/phase4a2_entry_to_recovery_timeline.svg
```

The figure displays the public-minute timeline relative to Entry Interface.

It includes:

```text
DSN → NSN

CM / SM separation

raise burn

Entry Interface

communications reacquisition

drogues

mains

splashdown

recovery approach

crew extraction

helicopter transfer

crew aboard ship

Orion secured
```

The figure explicitly notes that:

```text
public-minute differences
are not exact telemetry durations
```

---

# Timeline Evidence Boundaries

Phase 4A.2 enforces:

```text
PUBLIC UPDATE MINUTE
!=
EXACT EVENT EPOCH
```

```text
PUBLIC-MINUTE DIFFERENCE
!=
EXACT OPERATIONAL DURATION
```

```text
ENTRY INTERFACE → REACQUISITION PUBLIC DIFFERENCE
!=
EXACT BLACKOUT DURATION
```

```text
PHASE 2 DERIVED STATE
!=
NASA-REPORTED TELEMETRY
```

```text
PARACHUTE ARCHITECTURE
!=
INDIVIDUAL DEPLOYMENT TELEMETRY
```

```text
POST-SPLASHDOWN POWERDOWN
!=
KNOWN EXACT PUBLIC TIMESTAMP
```

```text
RECOVERY PROCEDURE DESCRIPTION
!=
UNREPORTED EXACT EVENT TIMES
```

```text
PHASE 4 OPERATIONAL INTEGRATION
!=
PHASE 2 ENTRY-PHYSICS RECOMPUTATION
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_entry_to_recovery_timeline.py
```

Validation results:

```text
Analysis identity: PASS

Dependency registry: PASS
```

Timeline structure:

```text
15-event operational timeline: PASS

Timeline ordering: PASS

Timeline provenance: PASS
```

Time basis:

```text
13 public-minute anchors: PASS

2 relative-order-only events: PASS

Blackout timing boundary: PASS

Powerdown timing boundary: PASS
```

Public-minute relationships:

```text
12 public-minute intervals: PASS

Exact-duration prohibition: PASS

Public-minute relationship summary: PASS
```

Phase 2 integration:

```text
Phase 2 trajectory-state crosslinks: PASS

Entry Interface state crosslink: PASS

Drogue state crosslink: PASS

Main-parachute state crosslink: PASS

Splashdown-correlated state crosslink: PASS

Derived-state / telemetry boundary: PASS
```

Operational state reconstruction:

```text
Mission-phase progression: PASS

Communications-state progression: PASS

Vehicle-configuration progression: PASS

Parachute-state progression: PASS

Crew-state progression: PASS

Recovery-state progression: PASS
```

Transition validation:

```text
36 operational state transitions: PASS

State-transition topology: PASS
```

Evidence integrity:

```text
Timeline evidence-boundary policy: PASS

No Phase 2 physics recomputation: PASS

No fabricated event epochs: PASS
```

Artifacts:

```text
Timeline CSV / JSON consistency: PASS

Documentation figure: PASS
```

Final result:

```text
PHASE 4A.2 VALIDATION PASSED
```

---

# Validated Phase 4A.2 Totals

```text
operational events
15

public-minute anchors
13

relative-order-only events
2

public-minute intervals
12

operational state transitions
36

Phase 2 trajectory-state crosslinks
4
```

---

# Phase 4A Status

```text
Phase 4A.1
PUBLIC EVIDENCE RECONSTRUCTION
COMPLETE

Phase 4A.2
ENTRY-TO-RECOVERY OPERATIONAL TIMELINE
COMPLETE
```

Current reconstructed chain:

```text
RETURN COMMUNICATIONS HANDOVER
↓
CM / SM SEPARATION
↓
ENTRY CONFIGURATION
↓
ENTRY INTERFACE
↓
PLANNED PLASMA BLACKOUT
↓
COMMUNICATIONS REACQUISITION
↓
DROGUE DESCENT
↓
MAIN PARACHUTE DESCENT
↓
SPLASHDOWN
↓
SPACECRAFT SAFING
↓
RECOVERY APPROACH
↓
CREW EXTRACTION
↓
HELICOPTER TRANSFER
↓
CREW ABOARD RECOVERY SHIP
↓
ORION SECURED IN WELL DECK
```

---

# Phase 4A.2 Status

```text
ENTRY-TO-RECOVERY EVENT INTEGRATION
COMPLETE

PUBLIC-MINUTE TIMELINE
COMPLETE

OPERATIONAL STATE MODEL
COMPLETE

PHASE 2 ENTRY CROSS-LINKING
COMPLETE

COMMUNICATIONS TRANSITIONS
COMPLETE

PARACHUTE TRANSITIONS
COMPLETE

CREW-RECOVERY TRANSITIONS
COMPLETE

SPACECRAFT-RECOVERY TRANSITIONS
COMPLETE

SECOND-LEVEL TELEMETRY CLAIMS
NOT MADE

PHASE 4A.2
COMPLETE
```

---

---

# Phase 4B — Splashdown Accuracy and Recovery Closure

## Goal

Close the remaining Phase 4 roadmap requirement:

```text
splashdown accuracy
```

without inventing unavailable targeting data.

Phase 4B integrates:

```text
Phase 4A.1
public entry / descent / recovery evidence

Phase 4A.2
entry-to-recovery operational timeline

Phase 2
flight-derived terminal trajectory reconstruction
```

to determine exactly what can and cannot be said about Artemis II splashdown accuracy from public evidence.

---

# Analysis

Created:

```text
scripts/analysis/analyze_splashdown_accuracy_recovery_closure.py
```

Generated:

```text
data/processed/recovery/splashdown_accuracy_recovery_closure.json

data/processed/recovery/splashdown_accuracy_metrics.csv
```

Documentation figure:

```text
docs/assets/recovery/phase4b_splashdown_accuracy_boundary.svg
```

Dataset:

```text
phase4b_artemis_ii_splashdown_accuracy_recovery_closure
```

Status:

```text
PHASE4_PUBLIC_EVIDENCE_CLOSURE_COMPLETE
```

---

# Dependencies

Validated:

```text
Phase 4A.1 public evidence
PASS

Phase 4A.2 operational timeline
PASS

Phase 2 entry correlations
PASS
```

---

# Splashdown Public-Time Consistency

NASA public splashdown minute:

```text
2026-04-11T00:07:00Z
```

Phase 2 derived WGS84 surface crossing:

```text
2026-04-11T00:07:08.823676Z
```

Derived offset from the start of NASA's reported public minute:

```text
8.824 seconds
```

The derived crossing lies within the publicly reported splashdown minute.

Classification:

```text
PUBLIC_MINUTE_CONSISTENT
```

Validation:

```text
Splashdown public-minute consistency
PASS

Derived surface crossing within reported minute
PASS
```

---

# Timing Accuracy Boundary

The 8.824-second value is:

```text
a consistency diagnostic
```

It is not:

```text
an exact splashdown timing error
```

because the NASA event report is only minute-resolution.

Therefore:

```text
PUBLIC-MINUTE OFFSET
!=
EXACT EVENT TIMING ERROR
```

Validation:

```text
Exact timing-error prohibition
PASS
```

---

# Derived Terminal State

Phase 2 derived terminal surface state:

```text
UTC
2026-04-11T00:07:08.823676Z

latitude
32.340599 deg

longitude
-117.763095 deg
```

Classification:

```text
DERIVED_SPLASHDOWN_CORRELATED_SURFACE_CROSSING
```

Provenance:

```text
PHASE2_DERIVED_FROM_NASA_FLIGHT_DERIVED_EPHEMERIS
```

Validation:

```text
Derived terminal state
PASS

Terminal-state provenance
PASS
```

---

# Terminal Coordinate Boundary

The derived coordinate is a MissionLab reconstruction from the flight-derived trajectory.

It is not claimed as:

```text
official NASA actual splashdown coordinate
```

and it is not:

```text
official NASA target coordinate
```

Therefore:

```text
DERIVED TERMINAL COORDINATE
!=
OFFICIAL ACTUAL SPLASHDOWN COORDINATE
```

and:

```text
DERIVED TERMINAL COORDINATE
!=
OFFICIAL TARGET COORDINATE
```

---

# Public Splashdown Location

NASA public location description:

```text
Pacific Ocean off the coast of San Diego
```

This establishes regional location.

It does not provide:

```text
numerical target latitude / longitude

numerical official actual splashdown latitude / longitude
```

---

# Spatial Targeting Accuracy

Publicly available official numerical target coordinate:

```text
NO
```

Publicly available official numerical actual splashdown coordinate:

```text
NO
```

Therefore:

```text
official target-to-actual miss distance
NOT PUBLICLY QUANTIFIABLE
```

Classification:

```text
TARGETING_MISS_DISTANCE_NOT_PUBLICLY_QUANTIFIABLE
```

No target miss distance is invented.

Validation:

```text
Official target-coordinate boundary
PASS

Official actual-coordinate boundary
PASS

Target-to-actual miss-distance boundary
PASS

No fabricated landing-accuracy metric
PASS
```

---

# Splashdown Accuracy Closure

The roadmap requirement:

```text
splashdown accuracy
```

is therefore closed as:

```text
COMPLETE_WITH_PUBLIC_EVIDENCE_BOUNDARY
```

MissionLab can defensibly quantify:

```text
derived terminal state

consistency with the NASA splashdown minute
```

MissionLab cannot defensibly quantify:

```text
official target-to-actual landing miss distance
```

because the required public target and official actual coordinate pair is unavailable.

---

# Drogue Distance Diagnostic

NASA-reported approximate distance to splashdown:

```text
0.800 statute miles
```

MissionLab-derived surface distance to the reconstructed terminal point at the drogue altitude anchor:

```text
1.159 statute miles
```

This difference is preserved as a diagnostic.

It is not interpreted as:

```text
targeting error
```

because the NASA value is approximate and the values do not represent a proven common exact telemetry epoch.

Therefore:

```text
DROGUE DISTANCE DIFFERENCE
!=
LANDING TARGETING MISS
```

Validation:

```text
Drogue distance diagnostic
PASS

Drogue diagnostic / targeting-error boundary
PASS
```

---

# Recovery Closure

Crew recovery completion state:

```text
CREW_RECOVERY_AT_SHIP_COMPLETE
```

Completion event:

```text
A2_CREW_ABOARD_RECOVERY_SHIP
```

Splashdown-to-crew-aboard-ship public-minute relationship:

```text
111 minutes
```

This remains:

```text
PUBLIC-MINUTE DIFFERENCE
```

not an exact operational duration.

---

# Spacecraft Recovery Closure

Spacecraft recovery completion state:

```text
SPACECRAFT_RECOVERY_AT_SHIP_COMPLETE
```

Completion event:

```text
A2_ORION_SECURED_IN_WELL_DECK
```

Splashdown-to-Orion-secured public-minute relationship:

```text
500 minutes
```

Again:

```text
PUBLIC-MINUTE DIFFERENCE
!=
EXACT OPERATIONAL DURATION
```

---

# Crew Recovery / Spacecraft Recovery Boundary

MissionLab explicitly preserves:

```text
CREW RECOVERY COMPLETE
!=
SPACECRAFT RECOVERY COMPLETE
```

Crew recovery closes when:

```text
crew aboard recovery ship
```

Spacecraft recovery closes when:

```text
Orion secured in well deck
```

Validation:

```text
Crew recovery closure
PASS

Spacecraft recovery closure
PASS

Crew / spacecraft recovery separation
PASS
```

---

# Recovery / Postflight Analysis Boundary

Securing Orion aboard the recovery ship does not establish:

```text
postflight spacecraft analysis complete
```

Therefore:

```text
SPACECRAFT RECOVERY COMPLETE
!=
POSTFLIGHT ENGINEERING ANALYSIS COMPLETE
```

Validation:

```text
Recovery / postflight-analysis separation
PASS
```

---

# Phase 4 Roadmap Closure

Original Phase 4 roadmap requirements:

```text
return geometry and entry timeline

public entry events

communications blackout

modeled atmospheric quantities where raw telemetry unavailable

parachute sequence

splashdown accuracy and recovery timeline

explicit separation of public data and model outputs
```

Validated closure:

```text
return geometry / entry timeline
COMPLETE

public entry events
COMPLETE

communications blackout
COMPLETE

modeled atmospheric quantities
COMPLETE

parachute sequence
COMPLETE

splashdown accuracy
COMPLETE WITH PUBLIC EVIDENCE BOUNDARY

recovery timeline
COMPLETE

public / model separation
COMPLETE
```

Validation:

```text
Phase 4 roadmap coverage
PASS
```

---

# Phase 4 Evidence Boundaries

Validated:

```text
derived surface crossing
!=
official actual splashdown coordinate
```

```text
derived surface crossing
!=
official target coordinate
```

```text
public-minute offset
!=
exact timing error
```

```text
drogue distance difference
!=
targeting error
```

```text
regional splashdown description
!=
precise miss distance
```

```text
absence of public coordinates
!=
evidence that landing was inaccurate
```

```text
crew recovery complete
!=
spacecraft recovery complete
```

```text
spacecraft recovery complete
!=
postflight analysis complete
```

Validation:

```text
Phase 4 evidence-boundary policy
PASS
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_splashdown_accuracy_recovery_closure.py
```

Validation results:

```text
Analysis identity
PASS

Dependency registry
PASS
```

Splashdown timing:

```text
Splashdown public-minute consistency
PASS

Derived surface crossing within reported minute
PASS

Exact timing-error prohibition
PASS
```

Terminal state:

```text
Derived terminal state
PASS

Terminal-state provenance
PASS
```

Spatial accuracy:

```text
Official target-coordinate boundary
PASS

Official actual-coordinate boundary
PASS

Target-to-actual miss-distance boundary
PASS

No fabricated landing-accuracy metric
PASS
```

Drogue diagnostic:

```text
Drogue distance diagnostic
PASS

Drogue diagnostic / targeting-error boundary
PASS
```

Recovery:

```text
Crew recovery closure
PASS

Spacecraft recovery closure
PASS

Crew / spacecraft recovery separation
PASS

Recovery / postflight-analysis separation
PASS
```

Roadmap:

```text
Return geometry / entry timeline
PASS

Public entry events
PASS

Communications blackout
PASS

Modeled atmospheric quantities
PASS

Parachute sequence
PASS

Splashdown accuracy boundary closure
PASS

Recovery timeline
PASS

Public / model separation
PASS

Phase 4 roadmap coverage
PASS
```

Artifacts:

```text
Metrics CSV consistency
PASS

Documentation figure
PASS
```

Final validator result:

```text
PHASE 4B VALIDATION PASSED

PHASE 4 ROADMAP COVERAGE PASSED
```

---

# Phase 4 Final Status

```text
PHASE 4 — ENTRY, DESCENT, SPLASHDOWN, RECOVERY
```

Return geometry:

```text
COMPLETE
```

Entry timeline:

```text
COMPLETE
```

Public entry evidence:

```text
COMPLETE
```

Entry communications blackout:

```text
COMPLETE
```

Atmospheric reconstruction:

```text
COMPLETE
```

Entry heating / rarefaction / Mach context:

```text
COMPLETE
```

Parachute architecture:

```text
COMPLETE
```

As-flown drogue / main sequence:

```text
COMPLETE
```

Splashdown reconstruction:

```text
COMPLETE
```

Splashdown public-time consistency:

```text
COMPLETE
```

Official target-to-actual miss distance:

```text
NOT PUBLICLY QUANTIFIABLE
```

Splashdown-accuracy roadmap requirement:

```text
COMPLETE WITH PUBLIC EVIDENCE BOUNDARY
```

Crew recovery:

```text
COMPLETE
```

Spacecraft recovery:

```text
COMPLETE
```

Public-data / derived-model separation:

```text
PRESERVED
```

Independent Phase 4 validation:

```text
PASS
```

Overall:

```text
PHASE 4
COMPLETE RELATIVE TO DEFENSIBLE PUBLIC EVIDENCE
```

---

# Phase 5 Handoff

Next roadmap phase:

```text
PHASE 5 — SPACE WEATHER AND RADIATION
```

Required work:

```text
OMNI / CDAWeb-compatible heliophysics quantities

mission-clock space-weather correlation

Artemis II trajectory preparation for NAIRAS 3.0

NAIRAS run ingestion / export where permitted

explicit shielding assumptions

external radiation environment
!=
astronaut absorbed / effective dose
```

---

---

# Phase 5A — Artemis II Mission Space-Weather Context

## Goal

Establish a mission-clock-aligned near-Earth space-weather context for the complete Artemis II mission window using NASA SPDF / CDAWeb OMNI data.

Phase 5A covers:

```text
NASA OMNI ingestion
↓
mission-window normalization
↓
UTC / MET correlation
↓
parameter completeness accounting
↓
mission-window extrema
↓
space-weather visualization
↓
explicit radiation / spacecraft interpretation boundaries
```

---

# Analysis

Created:

```text
scripts/analysis/analyze_space_weather_context.py
```

Created independent validator:

```text
scripts/validation/validate_space_weather_context.py
```

Generated processed products:

```text
data/processed/space_weather/omni_hro2_1min_artemis_ii.csv

data/processed/space_weather/artemis_ii_space_weather_context.json
```

Raw downloaded product:

```text
data/raw/space_weather/omni_hro2_1min_artemis_ii.json
```

Documentation figure:

```text
docs/assets/space_weather/phase5a_space_weather_context.svg
```

Dataset:

```text
phase5a_artemis_ii_space_weather_context
```

Status:

```text
MISSION_SPACE_WEATHER_CONTEXT_COMPLETE
```

---

# Mission Window

Mission launch:

```text
2026-04-01T22:35:12Z
```

Public splashdown minute:

```text
2026-04-11T00:07:00Z
```

OMNI query interval:

```text
start
2026-04-01T22:35:00Z

stop
2026-04-11T00:08:00Z
```

The query therefore spans the entire Artemis II mission window at one-minute cadence.

Validation:

```text
Mission-window alignment
PASS
```

---

# NASA Space-Weather Source

Source organization:

```text
NASA GSFC Space Physics Data Facility
```

Service:

```text
CDAWeb HAPI
```

Dataset:

```text
OMNI_HRO2_1MIN
```

Cadence:

```text
1 minute
```

Context:

```text
Combined definitive IMF and plasma data
time-shifted to the nose of Earth's bow shock
plus geomagnetic indices
```

Validation:

```text
NASA SPDF / CDAWeb source
PASS

OMNI_HRO2_1MIN dataset
PASS

Requested parameter registry
PASS
```

---

# Requested Quantities

Phase 5A ingested:

```text
F

BX_GSE

BY_GSM

BZ_GSM

flow_speed

proton_density

T

Pressure

E

Beta

Mach_num

AE_INDEX

SYM_H
```

These provide:

```text
interplanetary magnetic-field context

solar-wind plasma context

solar-wind pressure context

solar-wind electric-field context

geomagnetic activity context
```

---

# Mission-Window Data Volume

Downloaded mission-window rows:

```text
13,053
```

Nominal mission-window minute slots:

```text
13,053
```

Temporal coverage:

```text
2026-04-01T22:35:00Z
through
2026-04-11T00:07:00Z
```

Validation:

```text
13,053 mission-window minute rows
PASS

Mission-window temporal coverage
PASS
```

---

# Coverage Policy

MissionLab does not silently interpret:

```text
missing OMNI parameter value
```

as:

```text
quiet space-weather conditions
```

Parameter-level completeness is preserved explicitly.

Continuous complete parameter coverage is therefore:

```text
NOT ASSUMED
```

Validation:

```text
No silent continuous-coverage assumption
PASS
```

---

# Parameter Completeness

Validated:

```text
BZ_GSM
12,438 / 13,053
95.3%
```

```text
flow_speed
7,828 / 13,053
60.0%
```

```text
proton_density
7,828 / 13,053
60.0%
```

```text
Pressure
7,828 / 13,053
60.0%
```

```text
E
7,745 / 13,053
59.3%
```

```text
AE_INDEX
13,053 / 13,053
100%
```

```text
SYM_H
13,053 / 13,053
100%
```

Validation:

```text
Bz GSM completeness
PASS

Solar-wind speed completeness
PASS

Proton-density completeness
PASS

Flow-pressure completeness
PASS

Electric-field completeness
PASS

AE-index completeness
PASS

SYM/H completeness
PASS
```

---

# Mission-Clock Bz Minimum

Strongest southward Bz in the mission-window dataset:

```text
BZ_GSM
-14.460 nT
```

UTC:

```text
2026-04-02T07:09:00Z
```

Mission elapsed time:

```text
00:08:33:48
```

Provenance:

```text
MISSIONLAB_DERIVED_FROM_NASA_OMNI_HRO2_1MIN
```

Validation:

```text
Mission-clock Bz minimum
PASS
```

---

# Mission-Clock Solar-Wind-Speed Maximum

Maximum available solar-wind speed:

```text
789.700 km/s
```

UTC:

```text
2026-04-03T15:52:00Z
```

MET:

```text
01:17:16:48
```

Validation:

```text
Mission-clock solar-wind-speed maximum
PASS
```

---

# Mission-Clock Proton-Density Maximum

Maximum available proton density:

```text
35.880 n/cc
```

UTC:

```text
2026-04-10T07:16:00Z
```

MET:

```text
08:08:40:48
```

Validation:

```text
Mission-clock proton-density maximum
PASS
```

---

# Mission-Clock Flow-Pressure Maximum

Maximum available flow pressure:

```text
11.750 nPa
```

UTC:

```text
2026-04-10T07:16:00Z
```

MET:

```text
08:08:40:48
```

The coincidence with the proton-density maximum is preserved from the source data.

No spacecraft consequence is inferred solely from that coincidence.

Validation:

```text
Mission-clock flow-pressure maximum
PASS
```

---

# Mission-Clock Electric-Field Maximum

Maximum available electric-field quantity:

```text
8.490 mV/m
```

UTC:

```text
2026-04-02T07:04:00Z
```

MET:

```text
00:08:28:48
```

Validation:

```text
Mission-clock electric-field maximum
PASS
```

---

# Mission-Clock AE Maximum

Maximum AE index:

```text
3266 nT
```

UTC:

```text
2026-04-03T16:47:00Z
```

MET:

```text
01:18:11:48
```

Validation:

```text
Mission-clock AE maximum
PASS
```

---

# Mission-Clock SYM/H Minimum

Minimum SYM/H:

```text
-104 nT
```

UTC:

```text
2026-04-02T08:41:00Z
```

MET:

```text
00:10:05:48
```

Validation:

```text
Mission-clock SYM/H minimum
PASS
```

---

# Mission Clock Integration

Each normalized OMNI row contains:

```text
UTC timestamp

MET seconds

MET DD:HH:MM:SS
```

This aligns the external near-Earth space-weather environment with the same Artemis II mission clock used throughout MissionLab.

Validation:

```text
UTC / MET correlation
PASS
```

---

# Near-Earth Context Boundary

OMNI_HRO2_1MIN data are time-shifted near-Earth measurements.

They are not:

```text
Orion-local environmental measurements
```

Therefore:

```text
OMNI BOW-SHOCK CONTEXT
!=
ORION-LOCAL ENVIRONMENT
```

Validation:

```text
Near-Earth / Orion-local boundary
PASS
```

---

# Radiation Boundary

Solar-wind plasma and IMF quantities describe heliophysical conditions.

They do not directly establish:

```text
ionizing-radiation flux at Orion

absorbed dose

dose equivalent

effective dose

individual astronaut exposure
```

Therefore:

```text
SOLAR-WIND PARAMETERS
!=
IONIZING-RADIATION DOSE
```

Validation:

```text
Solar-wind / radiation-dose boundary
PASS
```

---

# Geomagnetic Activity Boundary

Geomagnetic indices such as:

```text
AE_INDEX

SYM_H
```

describe terrestrial magnetic activity.

They are not:

```text
astronaut radiation dose
```

Therefore:

```text
GEOMAGNETIC ACTIVITY
!=
ASTRONAUT EFFECTIVE DOSE
```

Validation:

```text
Geomagnetic-index / crew-dose boundary
PASS
```

---

# Anomaly Boundary

Large mission-window extrema are environmental context.

They are not automatically:

```text
spacecraft anomalies
```

Therefore:

```text
SPACE-WEATHER EXTREMUM
!=
SPACECRAFT ANOMALY
```

Validation:

```text
Extrema / spacecraft-anomaly boundary
PASS
```

---

# Causality Boundary

Temporal overlap between a mission event and space-weather condition does not prove:

```text
causal spacecraft effect
```

Therefore:

```text
MISSION-WINDOW CORRELATION
!=
CAUSAL SPACECRAFT EFFECT
```

---

# Data-Gap Boundary

Unavailable OMNI values are preserved as missing.

Therefore:

```text
OMNI DATA GAP
!=
QUIET SPACE WEATHER
```

MissionLab does not interpolate missing environmental evidence into an unsupported physical conclusion.

---

# Critical Non-Equivalences

Phase 5A validates five explicit non-equivalences:

```text
OMNI_BOW_SHOCK_CONTEXT
!=
ORION_LOCAL_ENVIRONMENT
```

```text
SOLAR_WIND_PARAMETERS
!=
IONIZING_RADIATION_DOSE
```

```text
GEOMAGNETIC_ACTIVITY
!=
ASTRONAUT_EFFECTIVE_DOSE
```

```text
MISSION_WINDOW_CORRELATION
!=
CAUSAL_SPACECRAFT_EFFECT
```

```text
OMNI_DATA_GAP
!=
QUIET_SPACE_WEATHER
```

Validation:

```text
Critical non-equivalences
PASS
```

---

# Visualization

Created:

```text
docs/assets/space_weather/phase5a_space_weather_context.svg
```

The figure provides mission-window context for:

```text
Bz GSM

solar-wind speed

flow pressure

SYM/H
```

The visualization explicitly states that the OMNI series represent:

```text
near-Earth space-weather context
```

and not:

```text
Orion-local radiation measurements

crew dose
```

Validation:

```text
Documentation figure
PASS
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_space_weather_context.py
```

Validation result:

```text
Analysis identity
PASS

Mission-window alignment
PASS

NASA SPDF / CDAWeb source
PASS

OMNI_HRO2_1MIN dataset
PASS

Requested parameter registry
PASS

13,053 mission-window minute rows
PASS

Mission-window temporal coverage
PASS

No silent continuous-coverage assumption
PASS

Parameter completeness
PASS

Mission-clock extrema
PASS

Near-Earth / Orion-local boundary
PASS

Solar-wind / radiation-dose boundary
PASS

Geomagnetic-index / crew-dose boundary
PASS

Extrema / spacecraft-anomaly boundary
PASS

Critical non-equivalences
PASS

Normalized CSV row count
PASS

Normalized CSV schema
PASS

UTC / MET correlation
PASS

Documentation figure
PASS
```

Final result:

```text
PHASE 5A VALIDATION PASSED
```

---

# Phase 5A Status

```text
NASA OMNI INGESTION
COMPLETE

MISSION-WINDOW NORMALIZATION
COMPLETE

UTC / MET CORRELATION
COMPLETE

PARAMETER COMPLETENESS ACCOUNTING
COMPLETE

SPACE-WEATHER EXTREMA
COMPLETE

SPACE-WEATHER VISUALIZATION
COMPLETE

NEAR-EARTH / ORION-LOCAL BOUNDARY
PRESERVED

SOLAR-WIND / RADIATION-DOSE BOUNDARY
PRESERVED

GEOMAGNETIC / CREW-DOSE BOUNDARY
PRESERVED

CORRELATION / CAUSATION BOUNDARY
PRESERVED

DATA-GAP / QUIET-CONDITION BOUNDARY
PRESERVED

PHASE 5A
COMPLETE
```

---

# Next

```text
Phase 5B — Radiation Environment and NAIRAS Integration Boundary
```

Phase 5B will close the remaining Phase 5 roadmap requirements:

```text
prepare Artemis II trajectory input for NAIRAS 3.0

define trajectory / radiation-environment interface

define explicit shielding assumptions

separate external environment from absorbed dose

separate absorbed dose from dose equivalent / effective dose

record NAIRAS Runs-on-Request workflow without fabricating a run

close Phase 5 relative to defensible public evidence
```

---

---

# Phase 5B — Artemis II Radiation Environment and NAIRAS Interface

## Goal

Close the remaining Phase 5 roadmap requirements by preparing Artemis II flight-derived trajectory geometry for the NASA NAIRAS 3.0 trajectory interface while preserving strict boundaries between:

```text
space-weather context

external radiation environment

material / shielding transport

absorbed dose

dose equivalent

effective dose

model output

crew dosimetry measurement
```

Phase 5B deliberately does not fabricate:

```text
Orion shielding depth

NAIRAS run execution

NAIRAS run ID

NAIRAS model output

crew radiation dose
```

---

# Analysis

Created:

```text
scripts/analysis/prepare_nairas_radiation_interface.py
```

Created independent validator:

```text
scripts/validation/validate_nairas_radiation_interface.py
```

Generated:

```text
data/processed/radiation/artemis_ii_nairas_trajectory_fields.csv

data/processed/radiation/artemis_ii_nairas_radiation_interface.json
```

Reference manifest:

```text
data/reference/artemis_ii_nairas_interface.json
```

Documentation figure:

```text
docs/assets/radiation/phase5b_nairas_radiation_interface.svg
```

Dataset:

```text
phase5b_artemis_ii_nairas_radiation_interface
```

Status:

```text
NAIRAS_TRAJECTORY_INTERFACE_PREPARED
```

---

# Dependencies

Validated dependencies:

```text
Artemis II mission configuration
PASS

Phase 5A mission space-weather context
PASS

flight-derived mission trajectory
PASS
```

---

# Flight-Derived Source Trajectory

Source:

```text
data/processed/trajectory/trajectory_with_mission_phases.csv
```

Provenance:

```text
NASA_FLIGHT_DERIVED_OEM_WITH_MISSIONLAB_DERIVED_GEOMETRY
```

Source state count:

```text
3262
```

Validated:

```text
Flight-derived source trajectory
PASS

3,262 source states
PASS
```

---

# Public OEM Coverage Boundary

Trajectory start:

```text
2026-04-02T01:57:37.084Z
```

Trajectory stop:

```text
2026-04-10T23:53:16.723Z
```

Therefore:

```text
complete launch-to-splashdown trajectory coverage
NO
```

MissionLab does not extend the public OEM outside the available trajectory states.

Therefore:

```text
PUBLIC OEM COVERAGE
!=
FABRICATED FULL-MISSION TRAJECTORY
```

Validation:

```text
Public OEM coverage boundary
PASS
```

---

# NAIRAS Model Interface

Model:

```text
NAIRAS
```

Version family:

```text
3.0
```

Trajectory run support:

```text
YES
```

Spacecraft trajectory support:

```text
YES
```

Validated:

```text
NAIRAS model identity
PASS

Trajectory-run capability
PASS
```

---

# NAIRAS Required Trajectory Fields

Prepared fields:

```text
date

time

geocentric_latitude_deg

geocentric_longitude_deg

altitude_km
```

Output:

```text
data/processed/radiation/artemis_ii_nairas_trajectory_fields.csv
```

Output trajectory points:

```text
3262
```

Validated:

```text
3,262 NAIRAS trajectory points
PASS

NAIRAS field schema
PASS

Trajectory start / stop coverage
PASS
```

---

# Portal Syntax Boundary

MissionLab prepares the published trajectory field content.

MissionLab does not claim knowledge of an undocumented parser-specific upload syntax.

Therefore:

```text
REQUIRED FIELD CONTENT
!=
UNDOCUMENTED PORTAL FILE FORMAT
```

Validation:

```text
Portal-syntax non-claim
PASS
```

---

# Coordinate Transformation

Input frame:

```text
J2000
```

Output frame:

```text
IAU_EARTH
```

Transformation:

```text
J2000 inertial position
↓
SPICE Earth-fixed transformation
↓
geocentric latitude
↓
geocentric longitude
↓
Earth-center radius
↓
mean-radius altitude
```

Validated:

```text
J2000 -> IAU_EARTH transformation
PASS

Geocentric latitude range
PASS

Geocentric longitude range
PASS

Mean-radius altitude range
PASS
```

---

# Prepared Geometry Range

Minimum derived geocentric altitude:

```text
143.951 km
```

Maximum derived geocentric altitude:

```text
406,773.436 km
```

These quantities describe trajectory geometry.

They are not radiation quantities.

Therefore:

```text
TRAJECTORY GEOMETRY
!=
RADIATION DOSE
```

---

# NAIRAS Radiation Sources

The model interface is documented around radiation sources including:

```text
GCR

SEP

TRP where model applicability permits
```

MissionLab records these as model radiation-source categories.

It does not infer actual Orion exposure merely from their availability in the model.

---

# Dosimetric Quantities Available Through NAIRAS

Recorded model output classes:

```text
absorbed dose in silicon

absorbed dose in tissue

dose equivalent

ambient dose equivalent

effective dose
```

Count:

```text
5
```

Validation:

```text
Dosimetric-output registry
PASS
```

---

# Radiation Response Chain

Phase 5B explicitly models the conceptual chain:

```text
external radiation environment
↓
transport through material / shielding
↓
absorbed dose
↓
dose-equivalent / effective-dose response quantities
```

Validated:

```text
Radiation-response chain
PASS

External environment / absorbed-dose separation
PASS

Absorbed-dose / response-quantity separation
PASS
```

---

# External Environment Boundary

External radiation fields such as:

```text
GCR

SEP

trapped particles where applicable
```

describe the radiation environment.

They do not directly equal:

```text
absorbed dose
```

Therefore:

```text
EXTERNAL RADIATION ENVIRONMENT
!=
ABSORBED DOSE
```

---

# Absorbed Dose Boundary

Absorbed dose is not automatically equivalent to:

```text
dose equivalent
```

Therefore:

```text
ABSORBED DOSE
!=
DOSE EQUIVALENT
```

---

# Effective Dose Boundary

Dose equivalent does not automatically equal:

```text
effective dose
```

Therefore:

```text
DOSE EQUIVALENT
!=
EFFECTIVE DOSE
```

---

# Shielding Input Boundary

NAIRAS accepts user-selectable aluminum-equivalent shielding depths.

However, Phase 5B does not establish an Orion-specific effective shielding depth at a crew location.

Therefore:

```text
Orion-specific effective aluminum-equivalent depth established
NO
```

MissionLab shielding assumptions used:

```text
NONE
```

Shielding-depth list used:

```text
[]
```

Dose calculation performed:

```text
NO
```

Validated:

```text
No unsupported Orion shielding depth
PASS

No shielding assumption used
PASS

No dose calculation performed
PASS
```

---

# Shielding Evidence Rule

MissionLab preserves:

```text
ASSUMED SHIELDING DEPTH
!=
ORION CREW-LOCATION SHIELDING
```

A shielding value cannot be promoted to an Orion crew dose model unless supported by defensible vehicle-specific evidence.

---

# Phase 5A Relationship

Phase 5A dataset:

```text
phase5a_artemis_ii_space_weather_context
```

Phase 5A provides:

```text
mission-clock-aligned near-Earth OMNI context
```

Phase 5B does not manually feed that OMNI dataset into NAIRAS.

Therefore:

```text
PHASE 5A OMNI CONTEXT
!=
NAIRAS INTERNAL RADIATION ENVIRONMENT DRIVER
```

Validated:

```text
Phase 5A OMNI crosslink
PASS

OMNI / NAIRAS-driver separation
PASS
```

---

# OMNI / Orion Radiation Boundary

Phase 5A OMNI quantities are:

```text
near-Earth solar-wind

IMF

plasma

geomagnetic context
```

They are not:

```text
Orion-local radiation field
```

Therefore:

```text
PHASE5A OMNI CONTEXT
!=
ORION LOCAL RADIATION
```

---

# NAIRAS Execution Boundary

MissionLab currently has:

```text
trajectory interface prepared
YES
```

MissionLab currently has not:

```text
submitted a NAIRAS run
```

Run submitted:

```text
NO
```

Run ID:

```text
NONE
```

Run output ingested:

```text
NO
```

Dose values reported:

```text
NO
```

Status:

```text
TRAJECTORY_PREPARED_NO_RUN_CLAIMED
```

Validated:

```text
NAIRAS interface prepared
PASS

No fabricated NAIRAS run
PASS

No fabricated NAIRAS run ID
PASS

No fabricated NAIRAS dose
PASS
```

---

# Future NAIRAS Execution Path

The prepared trajectory product can support a future authenticated CCMC Runs-on-Request execution.

Required future chain:

```text
prepared Artemis II trajectory fields
↓
explicit shielding-depth choice
↓
authenticated NAIRAS Runs-on-Request execution
↓
actual run identifier
↓
exported model result
↓
MissionLab ingestion
↓
model-output analysis
```

Until that chain occurs:

```text
NO NAIRAS-DERIVED ARTEMIS II DOSE IS CLAIMED
```

---

# Model Output / Measurement Boundary

A future NAIRAS result would remain:

```text
MODEL OUTPUT
```

It would not automatically become:

```text
CREW DOSIMETER MEASUREMENT
```

Therefore:

```text
NAIRAS MODEL OUTPUT
!=
CREW DOSIMETER MEASUREMENT
```

---

# Critical Non-Equivalences

Phase 5B validates eight critical non-equivalences:

```text
PHASE5A_OMNI_CONTEXT
!=
ORION_LOCAL_RADIATION_FIELD
```

```text
EXTERNAL_RADIATION_ENVIRONMENT
!=
ABSORBED_DOSE
```

```text
ABSORBED_DOSE
!=
DOSE_EQUIVALENT
```

```text
DOSE_EQUIVALENT
!=
EFFECTIVE_DOSE
```

```text
TRAJECTORY_GEOMETRY
!=
RADIATION_DOSE
```

```text
ASSUMED_SHIELDING_DEPTH
!=
ORION_CREW_LOCATION_SHIELDING
```

```text
NAIRAS_INTERFACE_PREPARED
!=
NAIRAS_RUN_EXECUTED
```

```text
NAIRAS_MODEL_OUTPUT
!=
CREW_DOSIMETER_MEASUREMENT
```

Validation:

```text
8 critical non-equivalences
PASS
```

---

# Phase 5 Evidence Boundaries

Validated false equivalences:

```text
trajectory fields
!=
radiation dose
```

```text
OMNI context
!=
Orion-local radiation
```

```text
unsupported shielding depth
!=
valid Orion shielding input
```

```text
interface preparation
!=
NAIRAS run execution
```

```text
model output
!=
dosimeter measurement
```

```text
external environment
!=
absorbed dose
```

```text
absorbed dose
!=
effective dose
```

```text
available OEM states
!=
fabricated full mission trajectory
```

Validation:

```text
Phase 5 evidence-boundary policy
PASS
```

---

# Documentation Figure

Created:

```text
docs/assets/radiation/phase5b_nairas_radiation_interface.svg
```

The figure shows:

```text
mission elapsed time

flight-derived geocentric altitude

flight-derived geocentric latitude
```

and explicitly preserves:

```text
trajectory geometry
!=
radiation dose
```

Validation:

```text
Documentation figure
PASS
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_nairas_radiation_interface.py
```

Validation:

```text
Analysis identity
PASS

Processed / reference manifest consistency
PASS

Phase 5A dependency
PASS

Flight-derived source trajectory
PASS

3,262 source states
PASS

Public OEM coverage boundary
PASS

NAIRAS model identity
PASS

Trajectory-run capability
PASS

Required trajectory fields
PASS

Dosimetric-output registry
PASS

User-selectable shielding input
PASS

3,262 NAIRAS trajectory points
PASS

NAIRAS field schema
PASS

Trajectory start / stop coverage
PASS

Portal-syntax non-claim
PASS

J2000 -> IAU_EARTH transformation
PASS

Geocentric latitude range
PASS

Geocentric longitude range
PASS

Mean-radius altitude range
PASS

No unsupported Orion shielding depth
PASS

No shielding assumption used
PASS

No dose calculation performed
PASS

Phase 5A OMNI crosslink
PASS

OMNI / NAIRAS-driver separation
PASS

Radiation-response chain
PASS

External environment / absorbed-dose separation
PASS

Absorbed-dose / response-quantity separation
PASS

NAIRAS interface prepared
PASS

No fabricated NAIRAS run
PASS

No fabricated NAIRAS run ID
PASS

No fabricated NAIRAS dose
PASS

8 critical non-equivalences
PASS

OMNI / CDAWeb roadmap item
PASS

Mission-clock correlation roadmap item
PASS

NAIRAS trajectory preparation roadmap item
PASS

NAIRAS execution boundary roadmap item
PASS

Shielding-assumption roadmap item
PASS

External environment / astronaut-dose boundary
PASS

Phase 5 roadmap coverage
PASS

Phase 5 evidence-boundary policy
PASS

Documentation figure
PASS
```

Final result:

```text
PHASE 5B VALIDATION PASSED

PHASE 5 ROADMAP COVERAGE PASSED
```

---

# Phase 5 Roadmap Closure

Phase 5 roadmap requirements:

```text
ingest OMNI / CDAWeb-compatible heliophysics quantities

correlate space-weather data with the mission clock

prepare Artemis II trajectory for NAIRAS 3.0

ingest / export NAIRAS runs where permitted

make shielding assumptions explicit

separate external radiation environment from astronaut dose
```

Validated status:

```text
OMNI / CDAWeb ingestion
COMPLETE

mission-clock space-weather correlation
COMPLETE

NAIRAS trajectory preparation
COMPLETE

NAIRAS interface
PREPARED

NAIRAS run execution
NOT CLAIMED

NAIRAS run output ingestion
NOT CLAIMED

shielding assumptions
EXPLICIT

shielding assumption actually used
NONE

external radiation environment vs absorbed dose
SEPARATED

absorbed dose vs dose equivalent
SEPARATED

dose equivalent vs effective dose
SEPARATED
```

---

# Phase 5 Final Status

```text
PHASE 5 — SPACE WEATHER AND RADIATION
```

NASA OMNI ingestion:

```text
COMPLETE
```

Mission-window space-weather normalization:

```text
COMPLETE
```

Mission-clock correlation:

```text
COMPLETE
```

OMNI parameter completeness accounting:

```text
COMPLETE
```

Space-weather extrema:

```text
COMPLETE
```

OMNI / Orion-local boundary:

```text
PRESERVED
```

NAIRAS trajectory preparation:

```text
COMPLETE
```

J2000 to Earth-fixed conversion:

```text
COMPLETE
```

NAIRAS required trajectory fields:

```text
COMPLETE
```

Orion-specific shielding depth:

```text
NOT ASSUMED
```

NAIRAS run:

```text
NOT CLAIMED
```

NAIRAS run ID:

```text
NONE
```

NAIRAS dose result:

```text
NOT CLAIMED
```

External environment / dose separation:

```text
PRESERVED
```

Model / measurement separation:

```text
PRESERVED
```

Independent validation:

```text
PASS
```

Overall:

```text
PHASE 5
COMPLETE WITH NAIRAS EXECUTION BOUNDARY
```

---

# Phase 6 Handoff

Next roadmap phase:

```text
PHASE 6 — LUNAR SCIENCE AND CREW OBSERVATIONS
```

Next work will focus on:

```text
Artemis II lunar science objectives

crew observation opportunities

lunar flyby geometry integration

Earth / Moon observation timing

candidate illumination and viewing geometry

publicly reported crew observations

science opportunity vs confirmed observation

mission-clock correlation of observation windows
```

---

---

# Phase 6A — Artemis II Lunar Science Archive and Evidence Index

## Goal

Establish the authoritative public-evidence layer for Phase 6 before performing observation reconstruction.

Phase 6A indexes:

```text
NASA lunar-science release evidence

PDS crew-camera archive structure

PDS Orion-camera archive structure

PDS mission-audio / transcript / annotation archive structure

initial public observation evidence

source-evolution conflicts that must remain unresolved until stronger evidence exists
```

Phase 6A does not claim:

```text
complete download of the 800+ GB archive

exact PDS product counts from NASA summary figures

product-level image / transcript correlation

LRO target integration

complete observation reconstruction
```

Those remain Phase 6B work.

---

# Analysis

Created:

```text
scripts/analysis/build_lunar_science_archive_index.py
```

Created independent validator:

```text
scripts/validation/validate_lunar_science_archive_index.py
```

Generated:

```text
data/reference/artemis_ii_lunar_science_archive_index.json

data/processed/lunar_science/artemis_ii_lunar_science_archive_summary.json

data/processed/lunar_science/artemis_ii_lunar_science_collections.csv

docs/assets/lunar_science/phase6a_lunar_science_archive_index.svg
```

Dataset:

```text
phase6a_artemis_ii_lunar_science_archive_index
```

Status:

```text
PUBLIC_LUNAR_SCIENCE_ARCHIVE_INDEXED
```

---

# NASA Public Lunar-Science Release

Release date:

```text
2026-10-07
```

NASA public summary reports:

```text
archive volume
>800 GB

full-resolution images / video
>11,000

science audio
8.5 hours
```

These values are preserved as public summary figures.

They are not treated as exact archive product counts.

Therefore:

```text
NASA RELEASE SUMMARY COUNT
!=
EXACT PDS PRODUCT COUNT
```

Validation:

```text
October 7 public release summary
PASS

800+ GB non-exact boundary
PASS

11,000+ image/video non-exact boundary
PASS

8.5-hour science-audio summary
PASS
```

---

# Source Registry

Authoritative source records indexed:

```text
8
```

Sources include:

```text
NASA October 7 Artemis II lunar-science data release

NASA Artemis II crew Moon photo annotations

NASA Artemis II official Moon flyby imagery release

NASA Artemis II Lunar Targeting Plan

PDS Artemis II crew-camera bundle

PDS Artemis II Orion-camera bundle

PDS Artemis II mission-audio bundle

NASA preliminary lunar-science report page
```

Validation:

```text
8-source registry
PASS

NASA source identities
PASS

PDS source identities
PASS
```

---

# PDS Bundle Registry

Indexed PDS bundles:

```text
3
```

Bundles:

```text
crew_camera

orion_camera

mission_audio
```

Validation:

```text
3 PDS bundles
PASS
```

---

# Crew Camera Bundle

PDS identifier:

```text
urn:nasa:pds:artemis2_crew_camera::1.0
```

DOI:

```text
10.17189/x52v-tb80
```

Coverage:

```text
2026-04-02T11:35:16.960Z
through
2026-04-09T04:28:31.990Z
```

Targets:

```text
Earth

Moon
```

Indexed collections:

```text
4
```

Collections:

```text
native source imagery

raw imagery

processed imagery

browse imagery
```

Validation:

```text
Crew-camera bundle metadata
PASS

Crew-camera 4-collection set
PASS
```

---

# Orion Camera Bundle

PDS identifier:

```text
urn:nasa:pds:artemis2_orion_camera::1.0
```

DOI:

```text
10.17189/hzev-nq50
```

Coverage:

```text
2026-04-02T12:49:07.000Z
through
2026-04-10T08:13:18.000Z
```

Targets:

```text
Earth

Moon
```

Indexed collections:

```text
3
```

Collections:

```text
raw imagery

video

browse imagery
```

Validation:

```text
Orion-camera bundle metadata
PASS

Orion-camera 3-collection set
PASS
```

---

# Mission Audio Bundle

PDS identifier:

```text
urn:nasa:pds:artemis2_mission_audio::1.0
```

DOI:

```text
10.17189/4a29-dz64
```

Coverage:

```text
2026-04-05T05:36:35.000Z
through
2026-04-07T11:59:59.000Z
```

Targets:

```text
Earth

Moon
```

Indexed collections:

```text
5
```

Collections:

```text
crew audio

crew audio transcripts

mission voice-loop audio

mission voice-loop transcripts

crew annotations
```

Validation:

```text
Mission-audio bundle metadata
PASS

Mission-audio 5-collection set
PASS
```

---

# PDS Collection Index

Total indexed collections:

```text
12
```

Breakdown:

```text
crew camera
4

Orion camera
3

mission audio
5
```

Output:

```text
data/processed/lunar_science/artemis_ii_lunar_science_collections.csv
```

Validation:

```text
12 PDS collections
PASS

Collection CSV schema
PASS

Collection ID uniqueness
PASS
```

---

# Archive Index Boundary

Phase 6A indexes archive metadata.

It does not download the complete media archive.

Therefore:

```text
PDS COLLECTION INDEX
!=
FULL MEDIA DOWNLOAD
```

Validation:

```text
No full-media-download claim
PASS
```

---

# Initial Observation Evidence Registry

Indexed public observation evidence records:

```text
5
```

Observation classes:

```text
Earth imagery

terminator observation

eclipse / corona observation

impact-flash observation
```

Validation:

```text
5 observation evidence records
PASS
```

---

# Earthset Observation

Observation ID:

```text
A2_LUNAR_EARTHSET
```

Class:

```text
EARTH_IMAGERY
```

NASA-reported time:

```text
2026-04-06T22:41:00Z
```

Timing precision:

```text
MINUTE
```

Reported image ID:

```text
art002e009288
```

Interpretation:

```text
Earthset behind the lunar limb during the far-side flyby
```

Evidence state:

```text
NASA_REPORTED
```

Validation:

```text
Earthset evidence
PASS
```

---

# Earthrise Observation

Observation ID:

```text
A2_LUNAR_EARTHRISE
```

Class:

```text
EARTH_IMAGERY
```

NASA-reported time:

```text
2026-04-06T23:22:00Z
```

Timing precision:

```text
MINUTE
```

Reported image ID:

```text
art002e021278
```

Interpretation:

```text
Earthrise photographed through an Orion spacecraft window
```

Evidence state:

```text
NASA_REPORTED
```

Validation:

```text
Earthrise evidence
PASS
```

---

# Terminator / Vavilov Observation

Observation ID:

```text
A2_LUNAR_TERMINATOR_VAVILOV
```

Class:

```text
TERMINATOR_OBSERVATION
```

Target context:

```text
Vavilov Crater / Hertzsprung basin region
```

Reported date:

```text
2026-04-06
```

Exact UTC in curated source:

```text
NONE
```

Timing classification:

```text
DATE_ONLY_IN_CURATED_SOURCE
```

Reported image ID:

```text
art002e009282
```

Evidence state:

```text
NASA_REPORTED
```

MissionLab does not invent an exact timestamp.

Validation:

```text
Terminator / Vavilov evidence
PASS
```

---

# Solar Eclipse Observation

Observation ID:

```text
A2_LUNAR_SOLAR_ECLIPSE
```

Class:

```text
ECLIPSE_CORONA_OBSERVATION
```

Reported date:

```text
2026-04-06
```

Exact public start / stop times in the curated evidence:

```text
NONE
```

Reported totality duration:

```text
nearly 54 minutes
```

Reported image ID:

```text
art002e009301
```

Evidence state:

```text
NASA_REPORTED
```

NASA reported that the visible halo was under investigation as:

```text
solar corona

zodiacal light

or a combination
```

Therefore:

```text
VISIBLE ECLIPSE HALO
!=
CONFIRMED SOLAR CORONA ONLY
```

Validation:

```text
Solar eclipse evidence
PASS

Eclipse-halo / corona-only boundary
PASS
```

---

# Impact-Flash Observation Evidence

Observation ID:

```text
A2_LUNAR_IMPACT_FLASH_REPORT
```

Class:

```text
IMPACT_FLASH_OBSERVATION
```

Target:

```text
lunar night side
```

Individual flash timestamps established in the Phase 6A curated source:

```text
NO
```

Evidence state:

```text
SOURCE_EVOLUTION_REQUIRES_RECONCILIATION
```

---

# Impact-Flash Source Evolution

Early public NASA report:

```text
publication date
2026-04-07

reported flash count
6

status
EARLY_PUBLIC_REPORT
```

Later postflight NASA annotation release:

```text
publication date
2026-10-07

reported flash count
5

status
POSTFLIGHT_DATA_RELEASE_REPORT
```

MissionLab-selected final count:

```text
NONE
```

MissionLab intentionally preserves:

```text
6
vs
5
```

rather than silently selecting one value.

Therefore:

```text
EARLY PUBLIC FLASH COUNT
!=
FINAL RECONCILED FLASH COUNT
```

Validation:

```text
Impact-flash evidence
PASS

Apr 7 early public report
6

Oct 7 postflight report
5

MissionLab selected count
NONE

silent reconciliation prohibition
PASS
```

---

# Image-Time / Crew-Remark Boundary

Image capture time and crew remark time may represent different timestamps.

Therefore:

```text
IMAGE CAPTURE TIME
!=
CREW REMARK TIME
```

Phase 6B must correlate them independently where public transcript evidence permits.

Validation:

```text
Image-time / remark-time boundary
PASS
```

---

# Observation Opportunity Boundary

A scientifically favorable geometry or target opportunity does not prove that the crew actually observed or photographed it.

Therefore:

```text
OBSERVATION OPPORTUNITY
!=
CONFIRMED OBSERVATION
```

Validation:

```text
Opportunity / confirmed-observation boundary
PASS
```

---

# Critical Non-Equivalences

Phase 6A validates six explicit non-equivalences:

```text
NASA_RELEASE_SUMMARY_COUNT
!=
EXACT_PDS_PRODUCT_COUNT
```

```text
PDS_COLLECTION_INDEX
!=
FULL_MEDIA_DOWNLOAD
```

```text
IMAGE_CAPTURE_TIME
!=
CREW_REMARK_TIME
```

```text
OBSERVATION_OPPORTUNITY
!=
CONFIRMED_OBSERVATION
```

```text
EARLY_PUBLIC_FLASH_COUNT
!=
FINAL_RECONCILED_FLASH_COUNT
```

```text
VISIBLE_ECLIPSE_HALO
!=
CONFIRMED_SOLAR_CORONA_ONLY
```

Validation:

```text
6 critical non-equivalences
PASS
```

---

# Phase 6 Roadmap Mapping After 6A

Crew imagery metadata:

```text
COLLECTION LEVEL
COMPLETE

PRODUCT LEVEL
PENDING
```

Orion imagery metadata:

```text
COLLECTION LEVEL
COMPLETE

PRODUCT LEVEL
PENDING
```

Mission audio / transcripts / annotations:

```text
COLLECTION LEVEL
COMPLETE

PRODUCT LEVEL
PENDING
```

Observation time / view / image / remark / target correlation:

```text
PARTIAL

PHASE 6B REQUIRED
```

LRO context:

```text
PENDING PHASE 6B
```

Impact-flash reconstruction:

```text
PENDING PHASE 6B
```

Terminator reconstruction:

```text
PENDING PHASE 6B
```

Eclipse / corona reconstruction:

```text
PENDING PHASE 6B
```

Earth imagery reconstruction:

```text
PENDING PHASE 6B
```

Validation:

```text
Collection-level crew imagery indexing
PASS

Collection-level Orion imagery indexing
PASS

Collection-level audio/transcript indexing
PASS

Phase 6B product-level handoff
PASS

LRO context correctly left to 6B
PASS

Observation reconstruction correctly left to 6B
PASS
```

---

# Documentation Figure

Created:

```text
docs/assets/lunar_science/phase6a_lunar_science_archive_index.svg
```

The figure records the collection-level structure:

```text
Crew camera
4 collections

Orion camera
3 collections

Mission audio
5 collections
```

and explicitly preserves the distinction between:

```text
archive summary figures

and

exact PDS product counts
```

Validation:

```text
Documentation figure
PASS
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_lunar_science_archive_index.py
```

Validation result:

```text
Analysis identity
PASS

Reference / processed manifest consistency
PASS

October 7 public release summary
PASS

800+ GB non-exact boundary
PASS

11,000+ image/video non-exact boundary
PASS

8.5-hour science-audio summary
PASS

8-source registry
PASS

NASA source identities
PASS

PDS source identities
PASS

3 PDS bundles
PASS

Crew-camera bundle metadata
PASS

Orion-camera bundle metadata
PASS

Mission-audio bundle metadata
PASS

12 PDS collections
PASS

Crew-camera 4-collection set
PASS

Orion-camera 3-collection set
PASS

Mission-audio 5-collection set
PASS

Collection CSV schema
PASS

Collection ID uniqueness
PASS

No full-media-download claim
PASS

5 observation evidence records
PASS

Earthset evidence
PASS

Earthrise evidence
PASS

Terminator / Vavilov evidence
PASS

Solar eclipse evidence
PASS

Impact-flash evidence
PASS

silent impact-flash reconciliation prohibition
PASS

Collection-level crew imagery indexing
PASS

Collection-level Orion imagery indexing
PASS

Collection-level audio/transcript indexing
PASS

Phase 6B product-level handoff
PASS

LRO context correctly left to 6B
PASS

Observation reconstruction correctly left to 6B
PASS

6 critical non-equivalences
PASS

Summary-count / product-count boundary
PASS

Archive-index / full-download boundary
PASS

Image-time / remark-time boundary
PASS

Opportunity / confirmed-observation boundary
PASS

Flash-count reconciliation boundary
PASS

Eclipse-halo / corona-only boundary
PASS

Documentation figure
PASS
```

Final result:

```text
PHASE 6A VALIDATION PASSED
```

---

# Phase 6A Final Status

```text
AUTHORITATIVE SOURCE REGISTRY
COMPLETE

PDS BUNDLE REGISTRY
COMPLETE

PDS COLLECTION REGISTRY
COMPLETE

INITIAL OBSERVATION EVIDENCE
COMPLETE

CREW CAMERA COLLECTION INDEX
COMPLETE

ORION CAMERA COLLECTION INDEX
COMPLETE

MISSION AUDIO / TRANSCRIPT / ANNOTATION COLLECTION INDEX
COMPLETE

EARTHSET PUBLIC EVIDENCE
INDEXED

EARTHRISE PUBLIC EVIDENCE
INDEXED

TERMINATOR / VAVILOV PUBLIC EVIDENCE
INDEXED

ECLIPSE PUBLIC EVIDENCE
INDEXED

IMPACT-FLASH SOURCE EVOLUTION
PRESERVED

PRODUCT-LEVEL CORRELATION
PENDING 6B

LRO CONTEXT
PENDING 6B

OBSERVATION RECONSTRUCTION
PENDING 6B

PHASE 6A
COMPLETE
```

---

# Phase 6B Handoff

Next:

```text
PHASE 6B — LUNAR OBSERVATION RECONSTRUCTION AND PHASE 6 CLOSURE
```

Phase 6B must complete:

```text
product-level observation indexing where publicly accessible

mission audio / transcript / annotation correlation

observation time
+
view direction
+
image
+
crew remark
+
science target

Earthset / Earthrise geometry correlation

terminator / Vavilov observation reconstruction

eclipse geometry and halo interpretation boundary

impact-flash source reconciliation or explicit unresolved closure

selected LRO target context

Phase 6 roadmap validation
```

---

---

# Phase 6B — Artemis II Lunar Observation Reconstruction and Phase 6 Closure

## Goal

Complete Phase 6 by connecting the public Artemis II lunar-science archive to reconstructed mission geometry, selected imagery, science audio, crew annotations, lunar targets, and LRO context.

Phase 6B completes:

```text
selected public science-product indexing

science audio / annotation correlation

observation time / view / image / remark / target linkage

Earthset / Earthrise geometry reconstruction

lunar terminator reconstruction

solar-eclipse / corona reconstruction

impact-flash source reconciliation

selected LRO context integration

Phase 6 roadmap closure
```

---

# Analysis

Created:

```text
scripts/analysis/reconstruct_lunar_science_observations.py
```

Created independent validator:

```text
scripts/validation/validate_lunar_science_observations.py
```

Generated:

```text
data/reference/artemis_ii_lunar_observation_reconstruction.json

data/processed/lunar_science/artemis_ii_lunar_observation_reconstruction.json

data/processed/lunar_science/artemis_ii_lunar_observation_correlations.csv

docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg
```

Dataset:

```text
phase6b_artemis_ii_lunar_observation_reconstruction
```

Status:

```text
LUNAR_SCIENCE_OBSERVATION_RECONSTRUCTION_COMPLETE
```

---

# Dependencies

Validated:

```text
Phase 6A lunar-science archive index
PASS

flight-derived Artemis II trajectory
PASS

SPICE geometry dependencies
PASS
```

Trajectory states available to the reconstruction:

```text
3262
```

---

# Selected Science Products

Selected image products:

```text
6
```

Selected science-audio / annotation records:

```text
7
```

Reconstructed science-observation records:

```text
8
```

Validation:

```text
6 selected image products
PASS

7 audio / annotation records
PASS

8 reconstructed observation records
PASS
```

---

# Selected Image Registry

Indexed selected image products include:

```text
art002e009288
Earthset
```

```text
art002e021278
Earthrise
```

```text
art002e009282
Vavilov / Hertzsprung terminator observation
```

```text
art002e009301
solar eclipse
```

```text
015A9930.NEF
postflight terminator science image
```

```text
019A0860.NEF
postflight eclipse / corona science image
```

Validation:

```text
Earthset image/time linkage
PASS

Earthrise image/time linkage
PASS

Vavilov exact-time non-inference
PASS

Eclipse exact-time non-inference
PASS
```

---

# Product Timing Boundary

For products where the curated public source does not provide an exact timestamp, MissionLab preserves that limitation.

Therefore:

```text
DATE-ONLY PUBLIC PRODUCT
!=
EXACT IMAGE CAPTURE UTC
```

MissionLab does not manufacture exact timestamps for:

```text
Vavilov imagery

selected eclipse imagery

selected postflight science-highlight products
```

---

# Science Audio and Annotation Registry

Selected public science-audio / annotation records include:

```text
Observing Earthset

Vavilov Crater: Color and Terrain

Terminator: Craters and Elevation

Ruminations on the Terminator

Searching for Impact Flashes and Lofted Dust

crew tablet impact-flash annotation

crew tablet solar-corona annotation
```

Validation:

```text
Earthset audio linkage
PASS

Vavilov audio linkage
PASS

Impact-flash audio linkage
PASS

Impact-flash annotation linkage
PASS

Corona annotation linkage
PASS
```

---

# Audio / Image Timing Boundary

A science audio timestamp or crew remark timestamp is not automatically identical to the image capture time.

Therefore:

```text
IMAGE CAPTURE TIME
!=
CREW REMARK TIME
```

Likewise:

```text
REFERENCE ANNOTATION TIME
!=
INDIVIDUAL IMPACT-FLASH TIME
```

Validation:

```text
Annotation-time / flash-time boundary
PASS
```

---

# Earthset Observation

NASA-reported Earthset time:

```text
2026-04-06T22:41:00Z
```

Reported image:

```text
art002e009288
```

MissionLab-derived geometry state at that reported time:

```text
PARTIAL_LIMB_OVERLAP
```

Interpretation:

```text
Earth was already intersecting the apparent lunar limb
at the NASA-reported Earthset observation time.
```

Validation:

```text
Earthset partial-limb geometry
PASS
```

---

# Full Earth Occultation

MissionLab-derived full Earth-occultation start:

```text
2026-04-06T22:43:22.462Z
```

MissionLab-derived full Earth-occultation stop:

```text
2026-04-06T23:19:56.488Z
```

Duration:

```text
36.57 minutes
```

Provenance:

```text
MISSIONLAB_DERIVED_FROM_NASA_FLIGHT_DERIVED_OEM_AND_SPICE
```

This interval is derived from:

```text
NASA flight-derived OEM geometry

linear interpolation between public trajectory states

SPICE body ephemerides

apparent angular radii and separation
```

It is not onboard Orion event telemetry.

Validation:

```text
Full Earth-occultation interval
PASS

Earth-occultation duration
PASS
```

---

# Earthrise Observation

NASA-reported Earthrise time:

```text
2026-04-06T23:22:00Z
```

Reported image:

```text
art002e021278
```

MissionLab-derived geometry state:

```text
PARTIAL_LIMB_OVERLAP
```

Interpretation:

```text
Earth had begun re-emerging across the lunar limb
at the NASA-reported Earthrise observation time.
```

Validation:

```text
Earthrise partial-limb geometry
PASS
```

---

# Reported-Time / Derived-Contact Boundary

NASA image timestamps are observations.

MissionLab-derived occultation contacts are geometric calculations.

Therefore:

```text
REPORTED IMAGE TIME
!=
DERIVED GEOMETRIC CONTACT TIME
```

MissionLab does not substitute the derived contact time for NASA's published image time.

Validation:

```text
Reported-time / contact-time separation
PASS
```

---

# Pericynthion Crosslink

Previously derived pericynthion:

```text
2026-04-06T23:00:46.177998Z
```

Mission elapsed time:

```text
05:00:25:34
```

The lunar-science reconstruction preserves this previously derived geometric anchor.

Validation:

```text
Pericynthion crosslink
PASS
```

---

# Solar Eclipse Geometry

MissionLab-derived total solar-eclipse start:

```text
2026-04-07T00:34:27.220Z
```

MissionLab-derived totality stop:

```text
2026-04-07T01:28:53.125Z
```

Derived totality duration:

```text
54.43 minutes
```

NASA public description:

```text
nearly 54 minutes
```

The close agreement provides an independent geometry consistency check.

Validation:

```text
Total solar-eclipse interval
PASS

54.43-minute derived totality
PASS

NASA nearly-54-minute comparison
PASS
```

---

# Eclipse Geometry Evidence Boundary

The derived interval is not treated as:

```text
onboard Orion eclipse telemetry
```

Therefore:

```text
MISSIONLAB-DERIVED ECLIPSE GEOMETRY
!=
ONBOARD ORION TELEMETRY
```

Similarly:

```text
DERIVED 54.43-MINUTE INTERVAL
!=
NASA'S PUBLISHED APPROXIMATE DURATION
```

Both are retained independently.

Validation:

```text
Derived-geometry / NASA-report separation
PASS
```

---

# Terminator / Vavilov Reconstruction

Selected observation:

```text
A2_LUNAR_TERMINATOR_VAVILOV
```

Target:

```text
Vavilov Crater / Hertzsprung Basin
```

Public image:

```text
art002e009282
```

Science-audio context:

```text
Vavilov Crater: Color and Terrain
```

Observation interpretation:

```text
crew observations of farside terrain under
low-angle terminator illumination
```

Relevant visual properties include:

```text
terrain relief

crater morphology

color

albedo

surface structure
```

Exact product timestamp inferred:

```text
NO
```

Validation:

```text
Terminator reconstruction
PASS
```

---

# General Terminator Observation

Selected postflight image:

```text
015A9930.NEF
```

Observation class:

```text
TERMINATOR_OBSERVATION
```

Associated public science-audio records:

```text
Terminator: Craters and Elevation

Ruminations on the Terminator
```

The reconstruction connects:

```text
target geometry

selected imagery

public crew observation summaries

low-angle illumination science value
```

without manufacturing an exact image or remark timestamp.

---

# Vavilov Target Context

Selected target:

```text
Vavilov Crater
```

Center latitude:

```text
-0.87 deg
```

Center longitude:

```text
-138.77 deg
```

Diameter:

```text
98.22 km
```

Context relationship:

```text
Vavilov is superimposed on the older
Hertzsprung basin and was an Artemis II
terminator observation target.
```

Validation:

```text
Vavilov target coordinates
PASS
```

---

# Hertzsprung LRO Context

Selected context:

```text
Hertzsprung Basin
```

LRO product:

```text
LROC NAC M112421089RE
```

Purpose:

```text
high-resolution contextual imaging
of the Hertzsprung inner-ring region
```

Validation:

```text
Hertzsprung LROC NAC context
PASS
```

---

# Orientale LRO Context

Selected target:

```text
Orientale Basin
```

Integrated public LRO context includes:

```text
LROC WAC
global imaging context

LOLA
topography / roughness context

Diviner
rock-abundance context

LOLA-derived / LRO-derived surface brightness context
```

The postflight Artemis II science analysis compares crew imagery with orbital context products.

Validation:

```text
Orientale LROC / LOLA / Diviner context
PASS
```

---

# LRO / Artemis II Product Boundary

LRO context imagery and measurements describe the lunar surface from an independent orbital mission.

They are not Artemis II imagery.

Therefore:

```text
LRO CONTEXT PRODUCT
!=
ARTEMIS II CREW IMAGE
```

Validation:

```text
LRO-context / Artemis-image boundary
PASS
```

---

# Impact-Flash Source Evolution

Early NASA public report:

```text
publication date
2026-04-07

reported flash count
6
```

Later postflight science report:

```text
publication date
2026-10-07

reported flash count
5
```

Phase 6A intentionally left this unresolved.

Phase 6B now resolves the science result using the later postflight evidence.

MissionLab final postflight science count:

```text
5
```

Status:

```text
RESOLVED_BY_LATER_POSTFLIGHT_SCIENCE_REPORT
```

The earlier six-flash report is retained.

It is not deleted or rewritten.

Validation:

```text
Early six-flash report preserved
PASS

Postflight five-flash result
PASS

Impact-flash source reconciliation
PASS
```

---

# Impact-Flash Selection Basis

MissionLab uses:

```text
5
```

as the postflight science result because the later science report states that five flashes were reported and that other candidate causes were ruled out.

The source history remains:

```text
early public evidence
6

later postflight science result
5
```

Therefore:

```text
EARLY SIX-FLASH REPORT
!=
POSTFLIGHT FIVE-FLASH RESULT
```

This difference represents evidence evolution rather than an error that should be hidden.

Validation:

```text
Six-flash / five-flash source-evolution boundary
PASS
```

---

# Individual Impact-Flash Timing Boundary

Reference annotation visualization time:

```text
2026-04-07T01:04:00Z
```

That time is not interpreted as the timestamp of any individual impact flash.

Therefore:

```text
REFERENCE ANNOTATION TIME
!=
INDIVIDUAL IMPACT-FLASH TIME
```

Individual flash timestamps fabricated:

```text
NO
```

Validation:

```text
No fabricated individual flash times
PASS
```

---

# Eclipse / Corona Source Evolution

Early public evidence state:

```text
HALO UNDER INVESTIGATION
```

Possible interpretations included:

```text
solar corona

zodiacal light

combination of multiple faint-light sources
```

Later postflight science result:

```text
CORONAL STRUCTURE
+
ZODIACAL LIGHT
```

MissionLab preserves both states of knowledge.

---

# Corona Observation

Selected postflight image:

```text
019A0860.NEF
```

Selected crew annotation:

```text
ANNOTATION_CORONA_STREAMER
```

Postflight interpretation:

```text
crew observed coronal structure

a changing coronal streamer was documented

zodiacal light was separately reported
```

Validation:

```text
Postflight coronal interpretation
PASS
```

---

# Eclipse Interpretation Boundary

The earlier uncertainty is not retroactively removed.

Therefore:

```text
EARLY HALO UNCERTAINTY
!=
POSTFLIGHT CORONAL INTERPRETATION
```

Evidence sequence:

```text
initial observation
↓
uncertain physical interpretation
↓
postflight analysis
↓
coronal structure + zodiacal light reported
```

Validation:

```text
Early halo uncertainty preserved
PASS

Eclipse interpretation reconciliation
PASS
```

---

# Observation Opportunity Boundary

The preflight targeting plan represents:

```text
observation opportunities
```

Postflight imagery, audio, and annotations establish:

```text
confirmed observations
```

Therefore:

```text
TARGETING PLAN OPPORTUNITY
!=
CONFIRMED OBSERVATION
```

Validation:

```text
Opportunity / observation boundary
PASS
```

---

# Time / View / Image / Remark / Target Integration

Phase 6 now connects, where public evidence permits:

```text
observation time

view direction

selected image product

science-audio / crew annotation

science target

mission geometry

LRO context
```

Reconstructed records include:

```text
Earthset

Earthrise

Vavilov / Hertzsprung terminator observation

general terminator science observation

solar eclipse

eclipse / corona observation

impact flashes

Orientale / LRO context integration
```

Validation:

```text
Time / view / image / remark / target linkage
PASS
```

---

# Observation Correlation Product

Generated:

```text
data/processed/lunar_science/artemis_ii_lunar_observation_correlations.csv
```

Rows:

```text
8
```

Validation:

```text
Observation correlation CSV
PASS

Observation CSV schema
PASS
```

---

# Critical Non-Equivalences

Phase 6B validates eight critical boundaries:

```text
REPORTED_IMAGE_TIME
!=
DERIVED_GEOMETRIC_CONTACT_TIME
```

```text
IMAGE_CAPTURE_TIME
!=
CREW_REMARK_TIME
```

```text
TARGETING_PLAN_OPPORTUNITY
!=
CONFIRMED_OBSERVATION
```

```text
REFERENCE_ANNOTATION_TIME
!=
INDIVIDUAL_IMPACT_FLASH_TIME
```

```text
EARLY_SIX_FLASH_REPORT
!=
POSTFLIGHT_FIVE_FLASH_RESULT
```

```text
EARLY_HALO_UNCERTAINTY
!=
POSTFLIGHT_CORONAL_INTERPRETATION
```

```text
LRO_CONTEXT_PRODUCT
!=
ARTEMIS_II_CREW_IMAGE
```

```text
MISSIONLAB_GEOMETRY
!=
ONBOARD_ORION_TELEMETRY
```

Validation:

```text
8 critical non-equivalences
PASS
```

---

# Documentation Figure

Created:

```text
docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg
```

The figure correlates:

```text
derived full Earth occultation

derived total solar eclipse

NASA-reported Earthset

NASA-reported Earthrise

MissionLab-derived pericynthion
```

while explicitly preserving the difference between:

```text
NASA-reported observations

and

MissionLab-derived geometric contacts
```

Validation:

```text
Documentation figure
PASS
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_lunar_science_observations.py
```

Validation result:

```text
Analysis identity
PASS

Reference / processed manifest consistency
PASS

Phase 6A dependency
PASS

Flight-derived trajectory dependency
PASS

SPICE kernel registry
PASS

6 selected image products
PASS

Earthset image/time linkage
PASS

Earthrise image/time linkage
PASS

Vavilov exact-time non-inference
PASS

Eclipse exact-time non-inference
PASS

7 audio / annotation records
PASS

Earthset audio linkage
PASS

Vavilov audio linkage
PASS

Impact-flash audio linkage
PASS

Impact-flash annotation linkage
PASS

Corona annotation linkage
PASS

Annotation-time / flash-time boundary
PASS

Earthset partial-limb geometry
PASS

Earthrise partial-limb geometry
PASS

Full Earth-occultation interval
PASS

Earth-occultation duration
PASS

Reported-time / contact-time separation
PASS

Total solar-eclipse interval
PASS

54.43-minute derived totality
PASS

NASA nearly-54-minute comparison
PASS

Derived-geometry / NASA-report separation
PASS

Pericynthion crosslink
PASS

8 reconstructed observation records
PASS

Earth imagery reconstruction
PASS

Terminator reconstruction
PASS

Eclipse reconstruction
PASS

LRO-context observation linkage
PASS

Early six-flash report preserved
PASS

Postflight five-flash result
PASS

Impact-flash source reconciliation
PASS

No fabricated individual flash times
PASS

Early halo uncertainty preserved
PASS

Postflight coronal interpretation
PASS

Eclipse interpretation reconciliation
PASS

3 LRO / target context records
PASS

Orientale LROC / LOLA / Diviner context
PASS

Hertzsprung LROC NAC context
PASS

Vavilov target coordinates
PASS

Observation correlation CSV
PASS

Observation CSV schema
PASS

Crew imagery roadmap item
PASS

Orion imagery roadmap item
PASS

Audio / transcript / annotation roadmap item
PASS

Time / view / image / remark / target linkage
PASS

LRO context roadmap item
PASS

Impact-flash roadmap item
PASS

Terminator roadmap item
PASS

Eclipse / corona roadmap item
PASS

Earth-imagery roadmap item
PASS

Phase 6 roadmap coverage
PASS

8 critical non-equivalences
PASS

Image-time / contact-time boundary
PASS

Image-time / remark-time boundary
PASS

Opportunity / observation boundary
PASS

Annotation-time / flash-time boundary
PASS

Six-flash / five-flash source-evolution boundary
PASS

Halo-uncertainty / postflight-interpretation boundary
PASS

LRO-context / Artemis-image boundary
PASS

Derived-geometry / onboard-telemetry boundary
PASS

Documentation figure
PASS
```

Final result:

```text
PHASE 6B VALIDATION PASSED

PHASE 6 ROADMAP COVERAGE PASSED
```

---

# Phase 6 Roadmap Closure

Roadmap requirement:

```text
index PDS crew imagery and Orion imagery metadata
```

Status:

```text
COMPLETE
```

Crew imagery:

```text
collection-level archive index
COMPLETE

selected science-product indexing
COMPLETE
```

Orion imagery:

```text
collection-level archive index
COMPLETE

selected science-product indexing
COMPLETE
```

---

Roadmap requirement:

```text
index mission audio / transcripts / annotations
```

Status:

```text
COMPLETE
```

Coverage:

```text
PDS collection indexing

selected public science-audio records

selected crew annotations

observation crosslinks
```

---

Roadmap requirement:

```text
connect observation time,
view direction,
image,
crew remark,
and target
```

Status:

```text
COMPLETE FOR RECONSTRUCTED SCIENCE OBSERVATIONS
```

---

Roadmap requirement:

```text
integrate public LRO context products
for selected targets
```

Status:

```text
COMPLETE
```

Selected context:

```text
Orientale Basin

Hertzsprung Basin

Vavilov Crater
```

---

Roadmap requirement:

```text
reconstruct impact-flash observations
```

Status:

```text
COMPLETE
```

Final postflight result:

```text
5 flashes
```

Earlier report retained:

```text
6 flashes
```

---

Roadmap requirement:

```text
reconstruct terminator observations
```

Status:

```text
COMPLETE
```

Includes:

```text
Vavilov / Hertzsprung

general terminator terrain

low-angle illumination context

science audio

selected imagery
```

---

Roadmap requirement:

```text
reconstruct eclipse / corona observations
```

Status:

```text
COMPLETE
```

Includes:

```text
MissionLab-derived totality geometry

NASA nearly-54-minute comparison

postflight coronal structure

zodiacal light

source-evolution boundary
```

---

Roadmap requirement:

```text
reconstruct Earth imagery analysis
```

Status:

```text
COMPLETE
```

Includes:

```text
Earthset

full Earth occultation

Earthrise

reported-image / derived-contact separation
```

---

# Phase 6 Final Status

```text
PHASE 6 — LUNAR SCIENCE AND CREW OBSERVATIONS
```

PDS crew-camera archive:

```text
COMPLETE
```

PDS Orion-camera archive:

```text
COMPLETE
```

PDS mission-audio archive:

```text
COMPLETE
```

Selected science-product indexing:

```text
COMPLETE
```

Science audio / annotation indexing:

```text
COMPLETE
```

Observation linkage:

```text
COMPLETE
```

Earthset reconstruction:

```text
COMPLETE
```

Earthrise reconstruction:

```text
COMPLETE
```

Full Earth-occultation geometry:

```text
COMPLETE
```

Terminator science reconstruction:

```text
COMPLETE
```

Vavilov / Hertzsprung context:

```text
COMPLETE
```

Solar-eclipse reconstruction:

```text
COMPLETE
```

Corona / zodiacal-light interpretation:

```text
COMPLETE
```

Impact-flash source reconciliation:

```text
COMPLETE
```

Final postflight flash result:

```text
5
```

Early six-flash report:

```text
PRESERVED
```

LRO context integration:

```text
COMPLETE
```

Image-time / contact-time boundary:

```text
PRESERVED
```

Image-time / crew-remark boundary:

```text
PRESERVED
```

Targeting-opportunity / confirmed-observation boundary:

```text
PRESERVED
```

MissionLab geometry / onboard telemetry boundary:

```text
PRESERVED
```

Independent validation:

```text
PASS
```

Overall:

```text
PHASE 6
COMPLETE RELATIVE TO DEFENSIBLE PUBLIC POSTFLIGHT EVIDENCE
```

---

# Phase 7 Handoff

Next roadmap phase:

```text
PHASE 7 — MISSION CONTROL / ENGINEERING PERSPECTIVES
```

Phase 7 will build discipline-specific mission views around the shared evidence spine.

Roadmap work:

```text
FLIGHT perspective

FDO perspective

FAO perspective

EECOM perspective

COMM perspective

SCIENCE perspective

engineering-support perspective

shared timeline with discipline-specific prioritization

decision threads:
detection
→ evidence
→ constraint
→ options
→ decision
→ action
→ outcome

postflight engineering timeline
```

---

---

# Phase 7A — Artemis II Mission Control Discipline Perspectives

## Goal

Build discipline-specific Mission Control / engineering perspectives over the already validated Artemis II evidence spine.

Phase 7A does not reconstruct private console loops.

It creates analytical views for:

```text
FLIGHT

FDO

FAO

EECOM

COMM

SCIENCE

ENGINEERING_SUPPORT
```

using the same underlying public and MissionLab-derived mission evidence.

---

# Analysis

Created:

```text
scripts/analysis/build_mission_control_perspectives.py
```

Created independent validator:

```text
scripts/validation/validate_mission_control_perspectives.py
```

Generated:

```text
data/reference/artemis_ii_mission_control_perspectives.json

data/processed/mission_control/artemis_ii_mission_control_perspectives.json

data/processed/mission_control/artemis_ii_discipline_prioritized_timeline.csv

docs/assets/mission_control/phase7a_discipline_priority_matrix.svg
```

Dataset:

```text
phase7a_artemis_ii_mission_control_perspectives
```

Status:

```text
DISCIPLINE_LENSES_AND_SHARED_TIMELINE_COMPLETE
```

---

# Cross-Phase Evidence Dependencies

Phase 7A integrates six previously validated evidence products:

```text
PHASE2_INTEGRATED_OPERATIONS

WASTE_MANAGEMENT_EVIDENCE

TPS_EVIDENCE

PHASE4_ENTRY_RECOVERY_EVIDENCE

PHASE5_RADIATION_INTERFACE

PHASE6_LUNAR_OBSERVATIONS
```

These provide:

```text
flight dynamics

maneuvers

GNC

communications

propulsion

crew-environment troubleshooting

thermal-protection evidence

entry / descent / recovery

space-weather / radiation boundaries

lunar science observations
```

Validation:

```text
6 cross-phase dependencies
PASS
```

---

# Public Mission-Control Role Grounding

Phase 7A records four NASA role-source references supporting the discipline framework.

Validated source categories include:

```text
NASA JSC Mission Control Center

NASA Artemis I Mission Control at a Glance

NASA Artemis II Science Officers

NASA Artemis II flight-control leadership material
```

Validation:

```text
4 public role sources
PASS

NASA mission-control role grounding
PASS
```

---

# FLIGHT Perspective

Classification:

```text
OFFICIAL_MISSION_CONTROL_ROLE_USED_AS_MISSIONLAB_LENS
```

MissionLab focus:

```text
overall mission state

crew safety

mission objectives

cross-discipline integration

risk and constraint visibility

decision readiness
```

The FLIGHT lens asks primarily:

```text
What changed in the integrated mission state?

Does the condition threaten crew safety or mission success?

Which disciplines require coordination?

Is a decision or contingency posture required?
```

Validation:

```text
FLIGHT role classification
PASS

FLIGHT prioritized view
PASS
```

---

# FDO Perspective

Classification:

```text
OFFICIAL_MISSION_CONTROL_ROLE_USED_AS_MISSIONLAB_LENS
```

MissionLab focus:

```text
trajectory

maneuver timing

orbit-determination context

lunar geometry

entry-targeting context

dynamic flight phases
```

Validation:

```text
FDO role classification
PASS

FDO prioritized view
PASS
```

---

# FAO Perspective

Classification:

```text
OFFICIAL_MISSION_CONTROL_ROLE_USED_AS_MISSIONLAB_LENS
```

MissionLab focus:

```text
mission timeline

crew activities

schedule changes

science windows

contingency activities

planned-activity handoffs
```

Validation:

```text
FAO role classification
PASS

FAO prioritized view
PASS
```

---

# EECOM Perspective

Classification:

```text
ORION_FLIGHT_CONTROL_ROLE_USED_AS_MISSIONLAB_LENS
```

MissionLab focus:

```text
crew environment

life support

waste management

consumables

thermal state

crew habitability

contingency posture
```

This lens is especially important for:

```text
Flight Day 1 toilet fault indication

restoration to normal toilet operations

Flight Day 4 wastewater vent-line issue

entry crew-environment context
```

Validation:

```text
EECOM role classification
PASS

EECOM prioritized view
PASS
```

---

# COMM Perspective

Classification:

```text
MISSIONLAB_ANALYTICAL_LENS
```

MissionLab does not claim:

```text
COMM
```

as an exact Artemis II console call sign derived from private staffing records.

Instead, the COMM lens groups public evidence concerning:

```text
DSN

network transitions

expected lunar occultation

entry plasma blackout

unexpected return-link loss

reacquisition

communications availability
```

Validation:

```text
COMM analytical-lens boundary
PASS

COMM prioritized view
PASS

COMM call-sign non-claim
PASS
```

---

# SCIENCE Perspective

Classification:

```text
OFFICIAL_ARTEMIS_II_CONSOLE_ROLE_USED_AS_MISSIONLAB_LENS
```

MissionLab focus:

```text
lunar targeting

crew observations

science imagery

impact flashes

terminator terrain

eclipse observations

LRO context
```

Validation:

```text
SCIENCE Artemis II console classification
PASS

SCIENCE prioritized view
PASS
```

---

# ENGINEERING_SUPPORT Perspective

Classification:

```text
MISSIONLAB_ANALYTICAL_LENS
```

This lens represents cross-system technical support rather than an asserted single front-room console call sign.

MissionLab focus:

```text
system troubleshooting

root-cause evidence

model limitations

thermal protection

hardware behavior

postflight investigation

engineering closure
```

Validation:

```text
ENGINEERING_SUPPORT analytical-lens boundary
PASS

ENGINEERING_SUPPORT prioritized view
PASS

ENGINEERING_SUPPORT call-sign non-claim
PASS
```

---

# Shared Mission Timeline

Phase 7A created one shared timeline containing:

```text
24 mission events
```

Each event carries priority values for all seven analytical lenses.

Priority scale:

```text
0
CONTEXT

1
AWARENESS

2
HIGH

3
PRIMARY
```

Validation:

```text
24 shared-timeline events
PASS

Contiguous event ordering
PASS

Timeline event-ID uniqueness
PASS

Complete 7-discipline priority registry
PASS

4-level priority scale
PASS
```

---

# Timing Policy

Phase 7A preserves original evidence precision.

Events without defensible exact UTC remain untimed.

Therefore:

```text
DATE-ONLY OR RELATIVE EVENT
!=
EXACT UTC EVENT
```

No fabricated UTC or MET is assigned.

Validation:

```text
No fabricated UTC for untimed events
PASS

No fabricated MET for untimed events
PASS
```

---

# Selected Cross-Discipline Anchors

## Flight Day 4 Waste-System Issue

Primary lenses:

```text
FLIGHT

FAO

EECOM

ENGINEERING_SUPPORT
```

Interpretation:

```text
crew-system condition
+
timeline implications
+
environment / habitability responsibility
+
technical troubleshooting
```

Validation:

```text
Waste-system cross-discipline anchor
PASS
```

---

## OTC3

Primary lenses:

```text
FLIGHT

FDO

FAO
```

Interpretation:

```text
mission trajectory decision

flight-dynamics relevance

mission timeline execution
```

Validation:

```text
OTC3 cross-discipline anchor
PASS
```

---

## Pericynthion

Primary lenses:

```text
FLIGHT

FDO

COMM

SCIENCE
```

Interpretation:

```text
major mission geometry milestone

flight-dynamics anchor

lunar communications geometry

science-observation context
```

Validation:

```text
Pericynthion cross-discipline anchor
PASS
```

---

## Total Solar Eclipse

Primary lenses:

```text
FDO

FAO

SCIENCE
```

Interpretation:

```text
derived geometry window

planned / scheduled science opportunity

confirmed science-observation context
```

Validation:

```text
Solar-eclipse cross-discipline anchor
PASS
```

---

## Unexpected Return-Link Loss

Primary lenses:

```text
FLIGHT

FAO

COMM

ENGINEERING_SUPPORT
```

Interpretation:

```text
mission-status awareness

timeline consequences

communications recovery

technical investigation
```

Validation:

```text
Return-link anomaly cross-discipline anchor
PASS
```

---

## RTC2

Primary lenses:

```text
FLIGHT

FDO

FAO

COMM

ENGINEERING_SUPPORT
```

The public sequence establishes:

```text
unexpected return-link loss

communications recovery

burn preparation resumed

RTC2 executed successfully
```

It does not establish:

```text
communications event caused a maneuver problem
```

Validation:

```text
RTC2 cross-discipline anchor
PASS
```

---

## Entry Interface

Primary lenses:

```text
FLIGHT

FDO

FAO

EECOM

COMM

ENGINEERING_SUPPORT
```

Entry Interface is one of the strongest integrated mission-control anchors because it simultaneously affects:

```text
flight-phase transition

trajectory

timeline

crew environment

communications

thermal / entry engineering
```

Validation:

```text
Entry Interface cross-discipline anchor
PASS
```

---

## Splashdown

Primary lenses:

```text
FLIGHT

FAO

EECOM

ENGINEERING_SUPPORT
```

Splashdown marks the transition from:

```text
flight operations
```

to:

```text
crew recovery

spacecraft recovery

postflight engineering
```

Validation:

```text
Splashdown cross-discipline anchor
PASS
```

---

# Mission-Clock Preservation

Validated anchors retain their established public or derived timing.

Examples:

```text
Launch
2026-04-01T22:35:12Z

OTC3
2026-04-06T03:03:00Z

Pericynthion
2026-04-06T23:00:46.177998Z

Derived eclipse start
2026-04-07T00:34:27.220Z

RTC2
2026-04-10T02:53:00Z

Entry Interface
2026-04-10T23:53:00Z

Splashdown
2026-04-11T00:07:00Z
```

Validation:

```text
Mission-clock anchor preservation
PASS

Derived lunar geometry preservation
PASS
```

---

# Communications Timing Boundaries

Unexpected return-link loss:

```text
2026-04-10T00:53:00Z
```

remains:

```text
APPROXIMATE_PUBLIC_ANCHOR
```

It is not silently promoted to exact telemetry.

Validation:

```text
Approximate return-link timing boundary
PASS
```

Entry plasma blackout retains:

```text
relative timing

approximate duration

no invented exact start

no invented exact end
```

Validation:

```text
Entry-blackout exact-time non-inference
PASS
```

---

# Priority Interpretation Boundary

MissionLab discipline priorities are analytical synthesis.

They are not NASA console logs.

Therefore:

```text
MISSIONLAB DISCIPLINE PRIORITY
!=
NASA PRIVATE CONSOLE ACTION
```

A discipline marked PRIMARY means:

```text
the event is highly relevant to that analytical perspective
```

It does not mean:

```text
a specific controller issued a command

a specific console owned the decision

a private flight-loop exchange occurred
```

Validation:

```text
MissionLab-priority / console-action boundary
PASS
```

---

# Role / Staffing Boundary

A public NASA role description defines a discipline's general function.

It does not establish:

```text
exact Artemis II shift staffing

specific controller identity

specific real-time action

private console responsibility at a specific second
```

Therefore:

```text
MISSIONLAB DISCIPLINE LENS
!=
EXACT ARTEMIS II CONSOLE STAFFING
```

Validation:

```text
Analytical-lens / staffing-record boundary
PASS
```

---

# Relevance / Authority Boundary

An event may be important to several disciplines.

That does not mean every discipline had decision authority.

Therefore:

```text
CROSS-DISCIPLINE RELEVANCE
!=
DECISION AUTHORITY
```

Validation:

```text
Cross-discipline relevance / authority boundary
PASS
```

---

# Public Sequence / Flight Loop Boundary

Public event reporting can reconstruct:

```text
event sequence

mission state changes

reported responses

reported outcomes
```

It cannot reconstruct the entire private Mission Control loop.

Therefore:

```text
PUBLIC EVENT SEQUENCE
!=
COMPLETE FLIGHT LOOP HISTORY
```

Validation:

```text
Public-sequence / full-loop-history boundary
PASS
```

---

# Expected Constraint / Anomaly Boundary

Phase 7A continues the established communications distinction:

```text
expected lunar occultation
!=
communications anomaly
```

and:

```text
planned entry plasma blackout
!=
communications anomaly
```

while:

```text
unexpected return-link loss
=
communications anomaly
```

Validation:

```text
Expected-constraint / anomaly boundary
PASS
```

---

# Troubleshooting / Root-Cause Boundary

Public engineering actions such as:

```text
vent heaters

Sun-pointing

crew troubleshooting

communications recovery actions
```

do not themselves establish a final physical root cause.

Therefore:

```text
PUBLIC TROUBLESHOOTING ACTION
!=
CONFIRMED ROOT CAUSE
```

Validation:

```text
Troubleshooting-action / root-cause boundary
PASS
```

---

# Geometry / Telemetry Boundary

MissionLab-derived geometry includes:

```text
lunar SOI transitions

pericynthion

Earth occultation

solar eclipse geometry
```

These are not onboard Orion telemetry.

Therefore:

```text
MISSIONLAB DERIVED GEOMETRY
!=
ONBOARD TELEMETRY
```

Validation:

```text
Derived-geometry / telemetry boundary
PASS
```

---

# Critical Non-Equivalences

Phase 7A validates:

```text
MISSIONLAB_DISCIPLINE_PRIORITY
!=
NASA_PRIVATE_CONSOLE_ACTION
```

```text
MISSIONLAB_DISCIPLINE_LENS
!=
EXACT_ARTEMIS_II_CONSOLE_STAFFING
```

```text
PUBLIC_EVENT_SEQUENCE
!=
COMPLETE_FLIGHT_LOOP_HISTORY
```

```text
CROSS_DISCIPLINE_RELEVANCE
!=
DECISION_AUTHORITY
```

```text
EXPECTED_COMMUNICATIONS_CONSTRAINT
!=
COMMUNICATIONS_ANOMALY
```

```text
PUBLIC_TROUBLESHOOTING_ACTION
!=
CONFIRMED_ROOT_CAUSE
```

```text
MISSIONLAB_DERIVED_GEOMETRY
!=
ONBOARD_TELEMETRY
```

Validation:

```text
7 critical non-equivalences
PASS
```

---

# Discipline-Prioritized Timeline Product

Generated:

```text
data/processed/mission_control/artemis_ii_discipline_prioritized_timeline.csv
```

Rows:

```text
24
```

Each row includes:

```text
event identity

UTC or preserved untimed state

date

MET where defensible

evidence class

event classification

source dependency

primary analytical lenses

seven discipline priority scores

event summary
```

Validation:

```text
Discipline-prioritized timeline CSV
PASS

Timeline CSV schema
PASS

Timeline CSV priority values
PASS
```

---

# Documentation Figure

Created:

```text
docs/assets/mission_control/phase7a_discipline_priority_matrix.svg
```

The matrix compares:

```text
24 mission events
x
7 discipline lenses
```

using:

```text
CONTEXT

AWARENESS

HIGH

PRIMARY
```

The figure explicitly states that priorities are MissionLab analytical synthesis rather than private NASA console activity.

Validation:

```text
Documentation figure
PASS
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_mission_control_perspectives.py
```

Validation result:

```text
Analysis identity
PASS

Reference / processed manifest consistency
PASS

4 public role sources
PASS

NASA mission-control role grounding
PASS

7 discipline lenses
PASS

FLIGHT role classification
PASS

FDO role classification
PASS

FAO role classification
PASS

EECOM role classification
PASS

COMM analytical-lens boundary
PASS

SCIENCE Artemis II console classification
PASS

ENGINEERING_SUPPORT analytical-lens boundary
PASS

4-level priority scale
PASS

6 cross-phase dependencies
PASS

24 shared-timeline events
PASS

Contiguous event ordering
PASS

Timeline event-ID uniqueness
PASS

Complete 7-discipline priority registry
PASS

No fabricated UTC for untimed events
PASS

No fabricated MET for untimed events
PASS

Selected cross-discipline anchors
PASS

Mission-clock anchor preservation
PASS

Derived lunar geometry preservation
PASS

Approximate return-link timing boundary
PASS

Entry-blackout exact-time non-inference
PASS

All seven prioritized discipline views
PASS

MissionLab-priority / console-action boundary
PASS

Analytical-lens / staffing-record boundary
PASS

COMM call-sign non-claim
PASS

ENGINEERING_SUPPORT call-sign non-claim
PASS

Derived-geometry / reported-event separation
PASS

7 critical non-equivalences
PASS

All seven roadmap lenses
PASS

Shared discipline-prioritized timeline
PASS

Decision threads correctly left to 7B
PASS

Postflight engineering timeline correctly left to 7B
PASS

Timeline CSV
PASS

Documentation figure
PASS
```

Final result:

```text
PHASE 7A VALIDATION PASSED
```

---

# Phase 7A Final Status

```text
FLIGHT LENS
COMPLETE

FDO LENS
COMPLETE

FAO LENS
COMPLETE

EECOM LENS
COMPLETE

COMM LENS
COMPLETE

SCIENCE LENS
COMPLETE

ENGINEERING_SUPPORT LENS
COMPLETE

SHARED MISSION TIMELINE
COMPLETE

DISCIPLINE PRIORITIZATION
COMPLETE

ROLE / STAFFING EVIDENCE BOUNDARIES
PRESERVED

PRIVATE CONSOLE-ACTION BOUNDARY
PRESERVED

EXPECTED-CONSTRAINT / ANOMALY BOUNDARY
PRESERVED

DERIVED-GEOMETRY / TELEMETRY BOUNDARY
PRESERVED

DECISION-THREAD SYNTHESIS
PENDING 7B

POSTFLIGHT ENGINEERING TIMELINE
PENDING 7B

PHASE 7A
COMPLETE
```

---

# Phase 7B Handoff

Next:

```text
PHASE 7B — DECISION THREADS, POSTFLIGHT ENGINEERING TIMELINE, AND PHASE 7 CLOSURE
```

Phase 7B will convert validated mission evidence into the roadmap decision structure:

```text
detection
↓
evidence
↓
constraint
↓
options
↓
decision
↓
action
↓
outcome
```

Priority threads will include:

```text
outbound correction cancellation / OTC3 execution

Flight Day 1 UWMS troubleshooting

Flight Day 4 wastewater vent-line response

lunar communications constraint

lunar science execution

unexpected return-link anomaly and RTC2 continuation

Artemis I TPS evidence → Artemis II mitigation → postflight result

final correction → entry handoff

entry blackout → reacquisition

descent → splashdown → recovery
```

Phase 7B will also create:

```text
postflight engineering timeline

open-vs-closed investigation registry

decision-evidence maturity states

Phase 7 roadmap validation
```

---

---

# Phase 7B — Artemis II Mission Control Decision Threads and Phase 7 Closure

## Goal

Complete Phase 7 by converting the validated Artemis II mission evidence spine into disciplined Mission Control / engineering decision threads.

Each decision thread uses the common structure:

```text
detection
↓
evidence
↓
constraint
↓
options
↓
decision
↓
action
↓
outcome
```

Phase 7B also adds:

```text
postflight engineering timeline

open-investigation registry

decision-evidence maturity tracking

Phase 7 roadmap closure
```

The reconstruction remains explicitly bounded by public evidence.

MissionLab does not reconstruct:

```text
private Mission Control transcripts

private console dialogue

complete internal option trees

undisclosed decision authority

unpublished flight-loop history

unknown root causes
```

---

# Analysis

Created:

```text
scripts/analysis/build_mission_control_decision_threads.py
```

Created independent validator:

```text
scripts/validation/validate_mission_control_decision_threads.py
```

Generated:

```text
data/reference/artemis_ii_decision_threads.json

data/processed/mission_control/artemis_ii_decision_threads.json

data/processed/mission_control/artemis_ii_decision_threads.csv

data/processed/mission_control/artemis_ii_postflight_engineering_timeline.csv

docs/assets/mission_control/phase7b_decision_thread_matrix.svg
```

Dataset:

```text
phase7b_artemis_ii_mission_control_decision_threads
```

Status:

```text
MISSION_CONTROL_DECISION_SYNTHESIS_COMPLETE
```

---

# Dependencies

Validated cross-phase dependencies:

```text
PHASE7A

PHASE2

WASTE_MANAGEMENT

TPS_EVIDENCE

ENTRY_RECOVERY

LUNAR_SCIENCE
```

Validation:

```text
6 cross-phase dependencies
PASS
```

---

# Decision-Thread Model

Decision threads:

```text
10
```

Stages per thread:

```text
7
```

Required sequence:

```text
detection
→
evidence
→
constraint
→
options
→
decision
→
action
→
outcome
```

Validation:

```text
Seven-stage decision model
PASS

Detection -> evidence -> constraint -> options -> decision -> action -> outcome
PASS

Seven stages present in every thread
PASS
```

---

# Decision Evidence States

Each stage is explicitly classified as one of:

```text
PUBLICLY_ESTABLISHED

MISSIONLAB_SYNTHESIS

NOT_PUBLICLY_ENUMERATED

NOT_APPLICABLE
```

This prevents MissionLab interpretation from being silently promoted into NASA-reported fact.

Validation:

```text
Stage evidence classifications
PASS

Decision-maturity accounting
PASS

No complete private-decision-history claim
PASS
```

---

# Decision Thread 1 — Outbound Trajectory Adaptation

Thread ID:

```text
OUTBOUND_TRAJECTORY_ADAPTATION
```

Classification:

```text
NOMINAL_ADAPTIVE_MISSION_OPERATIONS
```

Anomaly:

```text
NO
```

Primary lenses:

```text
FLIGHT

FDO

FAO
```

Evidence sequence:

```text
trajectory remained sufficiently on course
↓
earlier outbound correction opportunities cancelled
↓
OTC3 retained
↓
OTC3 executed
↓
mission continued into lunar encounter
```

OTC3:

```text
2026-04-06T03:03:00Z
```

MissionLab-derived lunar SOI entry:

```text
2026-04-06T04:38:07.532302Z
```

Decision maturity:

```text
5 publicly established stages

1 MissionLab synthesis stage

1 not-publicly-enumerated stage

0 N/A stages
```

Critical boundaries:

```text
CANCELLED_CORRECTION
!=
FAILED_BURN
```

```text
CANCELLED_CORRECTION
!=
PROPULSION_ANOMALY
```

```text
PUBLIC_CORRECTION_SEQUENCE
!=
COMPLETE_TARGETING_LOGIC
```

Validation:

```text
Outbound correction adaptation thread
PASS
```

---

# Decision Thread 2 — Flight Day 1 UWMS Fault Recovery

Thread ID:

```text
FD1_UWMS_FAULT_RECOVERY
```

Classification:

```text
IN_FLIGHT_SYSTEM_TROUBLESHOOTING
```

Anomaly:

```text
YES
```

Primary lenses:

```text
FLIGHT

FAO

EECOM

ENGINEERING_SUPPORT
```

Public sequence:

```text
toilet-system checkout
↓
blinking fault light
↓
Mission Control data assessment
↓
crew / ground troubleshooting
↓
normal toilet operation restored
```

Publicly established final root cause:

```text
NO
```

Decision maturity:

```text
5 public

1 MissionLab synthesis

1 not-public

0 N/A
```

Critical boundaries:

```text
FAULT_LIGHT
!=
IDENTIFIED_FAILED_COMPONENT
```

```text
RESTORED_OPERATION
!=
KNOWN_ROOT_CAUSE
```

```text
TOILET_FAULT
!=
COMPLETE_UWMS_FAILURE
```

Validation:

```text
Flight Day 1 UWMS recovery thread
PASS
```

---

# Decision Thread 3 — Flight Day 4 Wastewater Vent-Line Response

Thread ID:

```text
FD4_WASTEWATER_VENT_RESPONSE
```

Classification:

```text
MANAGED_IN_FLIGHT_SYSTEM_ANOMALY
```

Anomaly:

```text
YES
```

Primary lenses:

```text
FLIGHT

FAO

EECOM

ENGINEERING_SUPPORT
```

Detection:

```text
wastewater venting ended earlier than expected
```

Public evidence:

```text
tank not full

toilet operational

possible ice considered

other possible causes under review
```

Actions:

```text
vent heaters used

vent oriented toward Sun

other potential causes reviewed

backup collection capability maintained
```

Outcome:

```text
toilet remained operational

mission continued

postflight investigation remained open
```

Decision maturity:

```text
6 public

0 synthesis

1 not-public

0 N/A
```

Critical boundaries:

```text
POSSIBLE_ICE
!=
CONFIRMED_ICE
```

```text
HEATER_USE
!=
PROOF_OF_ICE
```

```text
SUN_POINTING
!=
ROOT_CAUSE_CONFIRMATION
```

```text
BACKUP_COLLECTION
!=
TOILET_INOPERATIVE
```

Validation:

```text
Flight Day 4 vent-line response thread
PASS
```

---

# Decision Thread 4 — Lunar Communications Constraint

Thread ID:

```text
LUNAR_COMMUNICATIONS_CONSTRAINT
```

Classification:

```text
EXPECTED_OPERATIONAL_CONSTRAINT
```

Anomaly:

```text
NO
```

Primary lenses:

```text
FLIGHT

FDO

COMM

SCIENCE
```

Evidence chain:

```text
Earthset

lunar occultation geometry

far-side operations

Earthrise

communications return
```

The loss of direct Earth line of sight is treated as:

```text
expected lunar geometry
```

not:

```text
communications failure
```

Decision maturity:

```text
5 public

1 synthesis

0 not-public

1 N/A
```

Critical boundaries:

```text
EXPECTED_LUNAR_BLACKOUT
!=
COMMUNICATIONS_ANOMALY
```

```text
EARTHRISE_IMAGE_TIME
!=
EXACT_LINK_REACQUISITION_TIME
```

Validation:

```text
Lunar communications constraint thread
PASS
```

---

# Decision Thread 5 — Lunar Science Execution

Thread ID:

```text
LUNAR_SCIENCE_EXECUTION
```

Classification:

```text
MISSION_SCIENCE_EXECUTION
```

Primary lenses:

```text
FLIGHT

FDO

FAO

SCIENCE
```

Science opportunity chain:

```text
preflight targeting plan
↓
mission geometry
↓
science observation window
↓
crew imaging / observations
↓
audio / annotation evidence
↓
postflight science interpretation
```

Confirmed science products include:

```text
Earthset

Earthrise

terminator terrain

Vavilov / Hertzsprung observations

solar eclipse

impact flashes

coronal structure

zodiacal light
```

Decision maturity:

```text
5 public

1 synthesis

1 not-public

0 N/A
```

Critical boundaries:

```text
TARGETING_OPPORTUNITY
!=
CONFIRMED_OBSERVATION
```

```text
IMAGE_TIME
!=
CREW_REMARK_TIME
```

```text
LRO_CONTEXT
!=
ARTEMIS_II_IMAGE
```

Validation:

```text
Lunar science decision thread
PASS
```

---

# Decision Thread 6 — Return-Link Anomaly and RTC2

Thread ID:

```text
RETURN_LINK_ANOMALY_RTC2
```

Classification:

```text
COMMUNICATIONS_ANOMALY_WITH_MISSION_CONTINUATION
```

Anomaly:

```text
YES
```

Primary lenses:

```text
FLIGHT

FDO

FAO

COMM

ENGINEERING_SUPPORT
```

Public sequence:

```text
unexpected return-link loss
↓
communications recovery
↓
burn preparation resumed
↓
RTC2 executed
↓
return mission continued
```

RTC2:

```text
2026-04-10T02:53:00Z
```

Decision maturity:

```text
6 public

0 synthesis

1 not-public

0 N/A
```

Critical boundary:

```text
TEMPORAL_SEQUENCE
!=
CAUSATION
```

MissionLab does not claim:

```text
return-link loss caused RTC2

communications anomaly caused a propulsion problem

communications anomaly changed maneuver targeting
```

Additional boundaries:

```text
RETURN_LINK_LOSS
!=
PROVEN_COMPLETE_TWO_WAY_OUTAGE
```

```text
COMMUNICATIONS_ANOMALY
!=
PROPULSION_ANOMALY
```

```text
RTC2_SUCCESS
!=
PUBLIC_ROOT_CAUSE
```

Validation:

```text
Return-link anomaly / RTC2 thread
PASS
```

---

# Decision Thread 7 — TPS Risk Mitigation and Closure

Thread ID:

```text
TPS_RISK_MITIGATION_CLOSURE
```

Classification:

```text
ENGINEERING_RISK_MITIGATION_THREAD
```

Primary lenses:

```text
FLIGHT

FDO

ENGINEERING_SUPPORT
```

Decision maturity:

```text
7 publicly established

0 synthesis

0 not-public

0 N/A
```

This is the most publicly mature Phase 7 decision thread.

Evidence chain:

```text
Artemis I unexpected Avcoat char loss
↓
postflight investigation
↓
low-permeability material mechanism identified
↓
gas-pressure / cracking mechanism established
↓
skip-entry thermal history recognized as contributing condition
↓
Artemis II entry environment changed
↓
Artemis II flew modified entry without Artemis I-style skip
↓
postflight inspection showed expected TPS performance
↓
char-loss behavior significantly reduced
```

Critical boundaries:

```text
REDUCED_CHAR_LOSS
!=
ZERO_CHAR_LOSS
```

```text
INITIAL_POSTFLIGHT_ASSESSMENT
!=
COMPLETE_MATERIAL_DATASET
```

```text
MISSIONLAB_HEATING_MODEL
!=
TPS_SENSOR_TELEMETRY
```

Validation:

```text
TPS mitigation and closure thread
PASS
```

---

# Decision Thread 8 — Final Correction to Entry Handoff

Thread ID:

```text
FINAL_CORRECTION_ENTRY_HANDOFF
```

Classification:

```text
NOMINAL_DYNAMIC_PHASE_HANDOFF
```

Primary lenses:

```text
FLIGHT

FDO

FAO

ENGINEERING_SUPPORT
```

Public anchors:

```text
RTC3
2026-04-10T18:53:00Z
```

```text
Entry Interface
2026-04-10T23:53:00Z
```

Elapsed public anchor separation:

```text
5 hours
```

Decision maturity:

```text
5 public

1 synthesis

1 not-public

0 N/A
```

Critical boundaries:

```text
FINAL_PUBLIC_CORRECTION
!=
FINAL_ONBOARD_NAVIGATION_STATE
```

```text
PUBLIC_HANDOFF
!=
ENTRY_GUIDANCE_LAW
```

---

# Decision Thread 9 — Entry Blackout and Reacquisition

Thread ID:

```text
ENTRY_BLACKOUT_REACQUISITION
```

Classification:

```text
EXPECTED_ENTRY_COMMUNICATIONS_CONSTRAINT
```

Anomaly:

```text
NO
```

Primary lenses:

```text
FLIGHT

FDO

EECOM

COMM

ENGINEERING_SUPPORT
```

Sequence:

```text
Entry Interface
↓
plasma formation
↓
planned communications blackout
↓
public communications reacquisition
↓
parachute descent
```

Public reacquisition minute:

```text
2026-04-11T00:00:00Z
```

Decision maturity:

```text
5 public

1 synthesis

0 not-public

1 N/A
```

Critical boundaries:

```text
PLANNED_ENTRY_BLACKOUT
!=
COMMUNICATIONS_ANOMALY
```

```text
PUBLIC_REACQUISITION_MINUTE
!=
EXACT_BLACKOUT_END_SECOND
```

Validation:

```text
Entry blackout / reacquisition thread
PASS
```

---

# Decision Thread 10 — Descent, Splashdown, and Recovery

Thread ID:

```text
DESCENT_SPLASHDOWN_RECOVERY
```

Classification:

```text
NOMINAL_RETURN_AND_RECOVERY_SEQUENCE
```

Primary lenses:

```text
FLIGHT

FDO

FAO

EECOM

ENGINEERING_SUPPORT
```

Public sequence:

```text
entry communications reacquisition
↓
drogue deployment
↓
main deployment
↓
splashdown
↓
recovery-team approach
↓
crew extraction
↓
crew transfer
↓
spacecraft recovery
```

Decision maturity:

```text
4 public

2 synthesis

1 not-public

0 N/A
```

Critical boundaries:

```text
PARACHUTE_ARCHITECTURE
!=
INDIVIDUAL_PARACHUTE_TELEMETRY
```

```text
PUBLIC_RECOVERY_SEQUENCE
!=
PRIVATE_RECOVERY_DECISION_LOG
```

Validation:

```text
Descent / splashdown / recovery decision thread
PASS
```

---

# Overall Decision-Thread Maturity

Validated:

```text
OUTBOUND_TRAJECTORY_ADAPTATION
5 public / 1 synthesis / 1 not-public / 0 N/A

FD1_UWMS_FAULT_RECOVERY
5 public / 1 synthesis / 1 not-public / 0 N/A

FD4_WASTEWATER_VENT_RESPONSE
6 public / 0 synthesis / 1 not-public / 0 N/A

LUNAR_COMMUNICATIONS_CONSTRAINT
5 public / 1 synthesis / 0 not-public / 1 N/A

LUNAR_SCIENCE_EXECUTION
5 public / 1 synthesis / 1 not-public / 0 N/A

RETURN_LINK_ANOMALY_RTC2
6 public / 0 synthesis / 1 not-public / 0 N/A

TPS_RISK_MITIGATION_CLOSURE
7 public / 0 synthesis / 0 not-public / 0 N/A

FINAL_CORRECTION_ENTRY_HANDOFF
5 public / 1 synthesis / 1 not-public / 0 N/A

ENTRY_BLACKOUT_REACQUISITION
5 public / 1 synthesis / 0 not-public / 1 N/A

DESCENT_SPLASHDOWN_RECOVERY
4 public / 2 synthesis / 1 not-public / 0 N/A
```

Validation:

```text
Decision-maturity accounting
PASS
```

---

# Postflight Engineering Timeline

Phase 7B reconstructs six postflight engineering records.

---

## April 11, 2026 — Recovery Transition

Record:

```text
POSTFLIGHT_RECOVERY_TRANSITION
```

Status:

```text
COMPLETE
```

Mission state transition:

```text
flight operations
↓
crew / spacecraft recovery
↓
inspection
↓
postflight engineering
```

---

## April 20, 2026 — Initial Orion Assessment

Record:

```text
POSTFLIGHT_INITIAL_ORION_ASSESSMENT
```

Status:

```text
INITIAL_ASSESSMENT
```

NASA reported initial evidence that:

```text
Orion TPS performed as expected

Artemis I-type char loss was significantly reduced
```

This remains an initial assessment rather than the complete engineering dataset.

---

## April 20, 2026 — Urine Vent-Line Investigation

Record:

```text
POSTFLIGHT_URINE_VENT_INVESTIGATION
```

Status:

```text
OPEN_IN_CURATED_PUBLIC_EVIDENCE
```

NASA reported:

```text
hardware assessment

data gathering

root-cause investigation

future corrective-action support
```

Publicly confirmed root cause:

```text
NO
```

Validation:

```text
Urine vent-line investigation remains open
PASS

No fabricated urine vent-line root cause
PASS
```

---

## April 21, 2026 — Mission and Fault Management Analysis

Record:

```text
POSTFLIGHT_MISSION_FAULT_MANAGEMENT_ANALYSIS
```

Status:

```text
POSTFLIGHT_ANALYSIS_ONGOING
```

NASA Ames publicly described continuing analysis of Mission and Fault Management performance.

Final public result in the curated source:

```text
NOT ESTABLISHED
```

Validation:

```text
Mission/Fault Management analysis remains ongoing
PASS

No fabricated final Mission/Fault Management result
PASS
```

---

## September 24, 2026 — TPS Engineering Knowledge Update

Record:

```text
POSTFLIGHT_TPS_ENGINEERING_KNOWLEDGE_UPDATE
```

Status:

```text
ENGINEERING_KNOWLEDGE_INTEGRATED
```

The updated public Orion engineering record connects:

```text
Artemis I root-cause knowledge

Avcoat permeability

Artemis II entry mitigation

Artemis II successful entry experience

future heat-shield manufacturing knowledge
```

Validation:

```text
TPS engineering knowledge update
PASS
```

---

## October 7, 2026 — Lunar Science Release

Record:

```text
POSTFLIGHT_LUNAR_SCIENCE_RELEASE
```

Status:

```text
PRELIMINARY_SCIENCE_RESULTS_RELEASED
```

Public postflight results included:

```text
lunar-science archive release

five impact flashes

coronal structure

zodiacal light

crew imagery

science audio

crew annotations
```

Validation:

```text
October lunar-science release
PASS
```

---

# Open Engineering Issue Registry

Phase 7 closes without forcing unresolved engineering questions into false certainty.

Open issues:

```text
URINE_VENT_LINE_ROOT_CAUSE
```

Status:

```text
OPEN_IN_CURATED_PUBLIC_EVIDENCE
```

Publicly confirmed final root cause:

```text
NO
```

Second open item:

```text
MISSION_AND_FAULT_MANAGEMENT_POSTFLIGHT_ANALYSIS
```

Status:

```text
ANALYSIS_REPORTED_ONGOING
```

Publicly confirmed final result:

```text
NO
```

Validation:

```text
2-item open engineering issue registry
PASS

Open-investigation preservation
PASS
```

---

# Public Source Registry

Phase 7B added five public postflight source records covering:

```text
initial Artemis II postflight assessment

NASA Ames postflight Mission and Fault Management analysis

updated Orion testing / TPS engineering knowledge

October 7 lunar-science results

NASA technical heat-shield success reporting
```

Validation:

```text
5 postflight public source records
PASS
```

---

# Decision Reconstruction Policy

Phase 7B enforces:

```text
public evidence
!=
MissionLab synthesis
```

MissionLab records the difference explicitly at every decision stage.

The following are prohibited:

```text
inventing private console dialogue

inventing complete option trees

assigning undisclosed decision authority

turning hypotheses into confirmed root causes

turning expected constraints into anomalies

turning temporal adjacency into causation

forcing open investigations closed
```

Validation:

```text
Public evidence / MissionLab synthesis separation
PASS

Private console dialogue non-reconstruction
PASS

Private option-tree non-reconstruction
PASS

Controller decision-authority non-inference
PASS

Unknown root-cause non-promotion
PASS

Expected-constraint / anomaly separation
PASS

Temporal-sequence / causation separation
PASS

Open-investigation preservation
PASS
```

---

# Critical Non-Equivalences

Phase 7B validates nine mission-operations evidence boundaries:

```text
MISSIONLAB_DECISION_THREAD
!=
NASA_PRIVATE_CONSOLE_TRANSCRIPT
```

```text
PUBLIC_SEQUENCE
!=
COMPLETE_INTERNAL_DECISION_LOGIC
```

```text
PUBLIC_ACTION
!=
COMPLETE_OPTION_SET
```

```text
DISCIPLINE_RELEVANCE
!=
DECISION_AUTHORITY
```

```text
TEMPORAL_SEQUENCE
!=
CAUSATION
```

```text
TROUBLESHOOTING_ACTION
!=
CONFIRMED_ROOT_CAUSE
```

```text
EXPECTED_OPERATIONAL_CONSTRAINT
!=
ANOMALY
```

```text
INITIAL_POSTFLIGHT_ASSESSMENT
!=
FINAL_ENGINEERING_DATASET
```

```text
OPEN_PUBLIC_INVESTIGATION
!=
RESOLVED_ROOT_CAUSE
```

Validation:

```text
9 critical non-equivalences
PASS
```

---

# Decision Thread CSV

Generated:

```text
data/processed/mission_control/artemis_ii_decision_threads.csv
```

Records:

```text
10
```

Each row contains:

```text
thread identity

classification

anomaly state

primary discipline lenses

anchor mission events

all seven decision-stage evidence states

decision maturity totals
```

Validation:

```text
Decision-thread CSV
PASS

Decision-thread CSV schema
PASS
```

---

# Postflight Engineering CSV

Generated:

```text
data/processed/mission_control/artemis_ii_postflight_engineering_timeline.csv
```

Records:

```text
6
```

Open records:

```text
2
```

Validation:

```text
Postflight engineering CSV
PASS

Postflight engineering CSV schema
PASS
```

---

# Documentation Figure

Created:

```text
docs/assets/mission_control/phase7b_decision_thread_matrix.svg
```

The figure compares:

```text
10 decision threads
x
7 decision stages
```

Evidence-state values distinguish:

```text
publicly established

MissionLab synthesis

not publicly enumerated

not applicable
```

The figure explicitly states that these are evidence reconstructions rather than private NASA decision logs.

Validation:

```text
Documentation figure
PASS
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_mission_control_decision_threads.py
```

Validation result:

```text
Analysis identity
PASS

Reference / processed manifest consistency
PASS

Phase 7A dependency
PASS

Seven-stage decision model
PASS

Detection -> evidence -> constraint -> options -> decision -> action -> outcome
PASS

6 cross-phase dependencies
PASS

5 postflight public source records
PASS

10 decision threads
PASS

Decision-thread ID uniqueness
PASS

Seven stages present in every thread
PASS

Stage evidence classifications
PASS

Decision-maturity accounting
PASS

No complete private-decision-history claim
PASS

Outbound correction adaptation thread
PASS

Flight Day 1 UWMS recovery thread
PASS

Flight Day 4 vent-line response thread
PASS

Lunar communications constraint thread
PASS

Return-link anomaly / RTC2 thread
PASS

TPS mitigation and closure thread
PASS

Entry blackout / reacquisition thread
PASS

6-record postflight engineering timeline
PASS

Recovery transition
PASS

Initial Orion postflight assessment
PASS

Urine vent-line investigation remains open
PASS

Mission/Fault Management analysis remains ongoing
PASS

TPS engineering knowledge update
PASS

October lunar-science release
PASS

2-item open engineering issue registry
PASS

No fabricated urine vent-line root cause
PASS

No fabricated final Mission/Fault Management result
PASS

Public evidence / MissionLab synthesis separation
PASS

Private console dialogue non-reconstruction
PASS

Private option-tree non-reconstruction
PASS

Controller decision-authority non-inference
PASS

Unknown root-cause non-promotion
PASS

Expected-constraint / anomaly separation
PASS

Temporal-sequence / causation separation
PASS

Open-investigation preservation
PASS

9 critical non-equivalences
PASS

Decision-thread / private-transcript boundary
PASS

Public-sequence / internal-logic boundary
PASS

Public-action / complete-option-set boundary
PASS

Discipline-relevance / decision-authority boundary
PASS

Temporal-sequence / causation boundary
PASS

Troubleshooting / root-cause boundary
PASS

Expected-constraint / anomaly boundary
PASS

Initial-assessment / final-dataset boundary
PASS

Open-investigation / resolved-root-cause boundary
PASS

All seven discipline lenses
PASS

Shared prioritized mission timeline
PASS

Decision-thread roadmap coverage
PASS

Postflight engineering timeline roadmap coverage
PASS

Phase 7 roadmap coverage
PASS

Decision-thread CSV
PASS

Postflight engineering CSV
PASS

Documentation figure
PASS
```

Final result:

```text
PHASE 7B VALIDATION PASSED

PHASE 7 ROADMAP COVERAGE PASSED
```

---

# Phase 7 Roadmap Closure

## FLIGHT Perspective

```text
COMPLETE
```

---

## FDO Perspective

```text
COMPLETE
```

---

## FAO Perspective

```text
COMPLETE
```

---

## EECOM Perspective

```text
COMPLETE
```

---

## COMM Perspective

```text
COMPLETE
```

---

## SCIENCE Perspective

```text
COMPLETE
```

---

## ENGINEERING_SUPPORT Perspective

```text
COMPLETE
```

---

## Shared Discipline-Prioritized Timeline

```text
COMPLETE
```

Coverage:

```text
24 mission events

7 discipline lenses

4 priority levels
```

---

## Decision Threads

Roadmap structure:

```text
detection
→
evidence
→
constraint
→
options
→
decision
→
action
→
outcome
```

Status:

```text
COMPLETE
```

Decision threads:

```text
10
```

---

## Postflight Engineering Timeline

Status:

```text
COMPLETE
```

Records:

```text
6
```

Open public engineering issues preserved:

```text
2
```

---

# Phase 7 Final Status

```text
PHASE 7 — MISSION CONTROL / ENGINEERING PERSPECTIVES
```

FLIGHT lens:

```text
COMPLETE
```

FDO lens:

```text
COMPLETE
```

FAO lens:

```text
COMPLETE
```

EECOM lens:

```text
COMPLETE
```

COMM lens:

```text
COMPLETE
```

SCIENCE lens:

```text
COMPLETE
```

ENGINEERING_SUPPORT lens:

```text
COMPLETE
```

Shared prioritized mission timeline:

```text
COMPLETE
```

Decision-thread synthesis:

```text
COMPLETE
```

Seven-stage decision model:

```text
COMPLETE
```

Postflight engineering timeline:

```text
COMPLETE
```

Decision-evidence maturity:

```text
COMPLETE
```

Open investigation preservation:

```text
COMPLETE
```

Private console-dialogue boundary:

```text
PRESERVED
```

Private option-tree boundary:

```text
PRESERVED
```

Decision-authority boundary:

```text
PRESERVED
```

Root-cause evidence boundary:

```text
PRESERVED
```

Expected-constraint / anomaly boundary:

```text
PRESERVED
```

Temporal-sequence / causation boundary:

```text
PRESERVED
```

Independent validation:

```text
PASS
```

Overall:

```text
PHASE 7
COMPLETE RELATIVE TO DEFENSIBLE PUBLIC EVIDENCE
```

---

# Phase 8 Handoff

Next roadmap phase:

```text
PHASE 8 — EVIDENCE-GROUNDED MISSION ANALYST
```

Phase 8 should build the analytical layer that can answer mission questions directly from the validated evidence spine.

The work should focus on:

```text
cross-phase evidence retrieval

mission-event lookup

mission-clock reasoning

discipline-aware analysis

decision-thread retrieval

provenance-aware answers

NASA-reported vs MissionLab-derived distinction

known vs unknown state handling

evidence confidence

source traceability

anti-hallucination guardrails

analyst-ready outputs
```

Phase 8 should consume the validated products from Phases 1 through 7 rather than recreating them.

---

---

# Phase 8A — Artemis II Evidence-Grounded Mission Analyst: Structured Retrieval and Deterministic Tools

## Goal

Build the deterministic evidence-access layer for the Artemis II MissionLab analyst.

Phase 8A implements the first half of the Phase 8 roadmap:

```text
structured retrieval over events / data / sources

deterministic calculations exposed as tools

citation-bearing retrieval

zero paid-model dependency
```

Phase 8A intentionally does not yet implement:

```text
citation-first natural-language answer composition

optional local / browser LLM integration
```

Those remain Phase 8B.

---

# Analyst Runtime

Created:

```text
scripts/analyst/mission_analyst.py
```

Created independent validator:

```text
scripts/validation/validate_mission_analyst.py
```

Generated:

```text
data/reference/artemis_ii_mission_analyst_index.json

data/processed/analyst/artemis_ii_mission_analyst_index.json
```

Dataset:

```text
phase8a_artemis_ii_mission_analyst_index
```

Status:

```text
STRUCTURED_RETRIEVAL_AND_DETERMINISTIC_TOOLS_COMPLETE
```

---

# Core Dependencies

Phase 8A directly consumes:

```text
phase7a_artemis_ii_mission_control_perspectives

phase7b_artemis_ii_mission_control_decision_threads
```

These provide:

```text
shared mission timeline

discipline priorities

mission-event identities

decision threads

postflight engineering records

evidence boundaries
```

Validation:

```text
Phase 7A dependency
PASS

Phase 7B dependency
PASS
```

---

# Mission Clock

Authoritative mission configuration:

```text
data/config/mission.json
```

Launch epoch:

```text
2026-04-01T22:35:12Z
```

The analyst uses this mission configuration as the only UTC / MET conversion anchor.

Validation:

```text
Mission clock configuration
PASS

Launch epoch preservation
PASS
```

---

# Structured Dataset Registry

Phase 8A indexed:

```text
25 reference datasets
```

The registry includes major validated MissionLab products across:

```text
Phase 2
flight dynamics
GNC
propulsion
communications
navigation

Phase 3
waste-management
thermal / TPS evidence

Phase 4
entry
descent
recovery

Phase 5
space weather / radiation interface

Phase 6
lunar science and observations

Phase 7
mission-control perspectives
decision threads
```

Each dataset record contains:

```text
dataset_id

mission

phase

status

title / purpose

reference path

top-level keys

local artifact citation
```

The Phase 8A index excludes itself from its own input dataset registry.

Validation:

```text
25 reference datasets
PASS

Dataset-ID uniqueness
PASS

Major Phase 2-7 products indexed
PASS

Analyst self-index exclusion
PASS

Dataset citations
PASS
```

---

# Normalized Public Source Registry

Phase 8A normalized:

```text
81 public sources
```

The analyst scans validated reference datasets and consolidates source metadata by:

```text
source_id
```

Normalized fields include:

```text
publisher

title

publication date

URL

source type

role / claim

local dataset occurrences
```

Where available, original public URLs are preserved.

Validation:

```text
81 normalized public sources
PASS

Source-ID uniqueness
PASS

Public source occurrence tracking
PASS

Source URL preservation
PASS
```

---

# Shared Mission Event Registry

Phase 8A indexed:

```text
24 mission events
```

These are inherited from the validated Phase 7A shared mission timeline.

Each event includes:

```text
event_id

order

name

timestamp UTC when defensible

date

MET when defensible

time precision

evidence class

classification

summary

source dependency

primary discipline lenses

discipline priorities

citation
```

Validation:

```text
24 shared mission events
PASS

Event-ID uniqueness
PASS

Mission-event ordering
PASS

Event citations
PASS
```

---

# Evidence Precision Preservation

Phase 8A preserves the evidence-state and timing boundaries established in earlier phases.

Examples:

```text
A2_PERICYNTHION
=
MISSIONLAB_DERIVED_GEOMETRY
```

It is not relabeled:

```text
NASA_REPORTED
```

Entry blackout retains:

```text
timestamp_utc = null
```

because no exact public UTC was defensibly established.

Unexpected return-link loss retains:

```text
APPROXIMATE_PUBLIC_ANCHOR
```

rather than being promoted to exact telemetry.

Validation:

```text
Reported timing preservation
PASS

Derived geometry labeling preservation
PASS

Unknown-time non-inference
PASS

Approximate-time precision preservation
PASS
```

---

# Decision Thread Registry

Phase 8A indexed:

```text
10 decision threads
```

Each thread contains:

```text
thread_id

title

classification

anomaly state

primary discipline lenses

anchor mission events

seven decision stages

guardrails

decision maturity

citation
```

Validated examples include:

```text
OUTBOUND_TRAJECTORY_ADAPTATION

FD1_UWMS_FAULT_RECOVERY

FD4_WASTEWATER_VENT_RESPONSE

LUNAR_COMMUNICATIONS_CONSTRAINT

LUNAR_SCIENCE_EXECUTION

RETURN_LINK_ANOMALY_RTC2

TPS_RISK_MITIGATION_CLOSURE

FINAL_CORRECTION_ENTRY_HANDOFF

ENTRY_BLACKOUT_REACQUISITION

DESCENT_SPLASHDOWN_RECOVERY
```

Validation:

```text
10 decision threads
PASS

Decision-thread ID uniqueness
PASS

Decision-thread citations
PASS
```

---

# Decision Boundary Preservation

Phase 8A successfully preserves the critical Phase 7 distinctions.

Unexpected return-link thread:

```text
RETURN_LINK_ANOMALY_RTC2
```

remains:

```text
anomaly = true
```

and retains:

```text
TEMPORAL_SEQUENCE
!=
CAUSATION
```

Lunar communications occultation remains:

```text
anomaly = false
```

Entry plasma blackout remains:

```text
anomaly = false
```

TPS thread retains:

```text
7 publicly established stages
```

Validation:

```text
RTC2 anomaly boundary preservation
PASS

Lunar communications constraint boundary
PASS

Entry blackout constraint boundary
PASS

TPS decision maturity preservation
PASS
```

---

# Postflight Engineering Registry

Phase 8A indexed:

```text
6 postflight engineering records
```

These include:

```text
recovery transition

initial Orion postflight assessment

urine vent-line investigation

Mission and Fault Management analysis

TPS engineering knowledge update

October lunar-science release
```

Open public investigations remain open.

Urine vent-line investigation:

```text
open_issue = true
```

Mission and Fault Management analysis:

```text
open_issue = true
```

Validation:

```text
6 postflight records
PASS

Urine vent investigation remains open
PASS

Mission/Fault Management analysis remains open
PASS

October lunar-science record
PASS
```

---

# Unified Retrieval Index

Phase 8A combines:

```text
events

decision threads

postflight records

public sources

reference datasets
```

into one structured searchable registry.

Unified searchable records:

```text
146
```

Record types:

```text
event

decision_thread

postflight_record

source

dataset
```

The count is exactly equal to:

```text
24 events
+
10 decision threads
+
6 postflight records
+
81 sources
+
25 datasets
=
146 unified records
```

Validation:

```text
146 unified searchable records
PASS

Unified record-count arithmetic
PASS

5 analyst record types
PASS
```

---

# Search Tokenization

Each unified record receives normalized search tokens derived from:

```text
record identity

title

summary

payload content
```

Search tokens are:

```text
deduplicated

lowercase

sorted
```

Validation:

```text
Normalized search-token registry
PASS
```

---

# Citation-Bearing Retrieval

Every indexed record carries an explicit local artifact citation.

Citation structure:

```text
dataset_id

path

locator

evidence_class

citation_text
```

Example:

```text
data/reference/artemis_ii_decision_threads.json
::
decision_threads[thread_id=RETURN_LINK_ANOMALY_RTC2]
```

Event example:

```text
data/reference/artemis_ii_mission_control_perspectives.json
::
shared_timeline[event_id=A2_RTC2]
```

The citation is returned directly with retrieval output rather than being generated afterward.

Validation:

```text
Citation payload on every unified record
PASS

Citation-return policy
PASS
```

---

# Retrieval Tools

Phase 8A exposes eight deterministic analyst tools:

```text
search

event_lookup

decision_thread_lookup

source_lookup

dataset_lookup

utc_to_met

met_to_utc

elapsed_time
```

Validation:

```text
8 deterministic analyst tools
PASS

Search tool registry
PASS

Exact lookup tool registry
PASS

Mission-time calculation tool registry
PASS
```

---

# Exact Event Lookup

Tool:

```text
event_lookup
```

Exact-ID retrieval can return events such as:

```text
A2_RTC2
```

Validated RTC2 UTC:

```text
2026-04-10T02:53:00Z
```

The returned object includes its local evidence citation.

Validation:

```text
event_lookup execution
PASS
```

---

# Exact Decision-Thread Lookup

Tool:

```text
decision_thread_lookup
```

Validated lookup:

```text
RETURN_LINK_ANOMALY_RTC2
```

Returned anomaly state:

```text
true
```

Validation:

```text
decision_thread_lookup execution
PASS
```

---

# Exact Dataset Lookup

Tool:

```text
dataset_lookup
```

Validated lookup:

```text
phase7b_artemis_ii_mission_control_decision_threads
```

Resolved artifact:

```text
data/reference/artemis_ii_decision_threads.json
```

Validation:

```text
dataset_lookup execution
PASS
```

---

# Exact Source Lookup

Tool:

```text
source_lookup
```

Validated example:

```text
NASA_INITIAL_POSTFLIGHT_ASSESSMENT_2026_04_20
```

The analyst returns:

```text
normalized source metadata

public URL

local reference occurrence

local citation
```

Validation:

```text
source_lookup execution
PASS
```

---

# Keyword Search

Tool:

```text
search
```

Search operates across all unified records.

Smoke-test query:

```text
return link RTC2
```

Retrieved:

```text
RETURN_LINK_ANOMALY_RTC2

A2_RTC2

FINAL_CORRECTION_ENTRY_HANDOFF
```

Top result:

```text
decision_thread
RETURN_LINK_ANOMALY_RTC2
```

Citation:

```text
data/reference/artemis_ii_decision_threads.json
::
decision_threads[thread_id=RETURN_LINK_ANOMALY_RTC2]
```

Validation:

```text
Unified keyword search execution
PASS

Return-link / RTC2 retrieval
PASS
```

---

# Record-Type Filtering

Search can be constrained to:

```text
event

decision_thread

postflight_record

source

dataset
```

Validated filtered search:

```text
query:
entry interface

record_type:
event
```

Result includes:

```text
A2_ENTRY_INTERFACE
```

and excludes non-event records.

Validation:

```text
Record-type filtered search
PASS
```

---

# Deterministic Mission-Time Tool — UTC to MET

Tool:

```text
utc_to_met
```

Input:

```text
2026-04-06T03:03:00Z
```

Launch:

```text
2026-04-01T22:35:12Z
```

Result:

```text
MET
04:04:27:48
```

Elapsed seconds:

```text
361668
```

Validation:

```text
UTC -> MET execution
PASS

OTC3 MET = 04:04:27:48
PASS
```

---

# Deterministic Mission-Time Tool — MET to UTC

Tool:

```text
met_to_utc
```

Input:

```text
04:04:27:48
```

Result:

```text
2026-04-06T03:03:00Z
```

Validation:

```text
MET -> UTC execution
PASS

UTC/MET round-trip
PASS
```

---

# Pericynthion Mission Clock Test

Input:

```text
2026-04-06T23:00:46.177998Z
```

Calculated MET:

```text
05:00:25:34.178
```

Validation:

```text
Pericynthion MET calculation
PASS
```

---

# Deterministic Elapsed-Time Tool

Tool:

```text
elapsed_time
```

Smoke test:

```text
Earthset
2026-04-06T22:41:00Z

Earthrise
2026-04-06T23:22:00Z
```

Elapsed:

```text
2460 seconds

41 minutes

00:00:41:00
```

Validation:

```text
Elapsed-time execution
PASS

Earthset -> Earthrise = 41 minutes
PASS
```

---

# Retrieval Policy

Phase 8A enforces:

```text
structured local artifacts first
```

Supported:

```text
exact ID lookup

keyword search

record-type filtering

citation return

source URL preservation
```

Forbidden:

```text
invent unsupported facts

promote MissionLab-derived values to NASA-reported

assign exact UTC to events without exact public timing
```

Validation:

```text
Structured-local-artifact-first policy
PASS

Exact-ID retrieval policy
PASS

Keyword retrieval policy
PASS

Record-type filtering policy
PASS

Citation-return policy
PASS

Unsupported-fact invention prohibition
PASS

MissionLab/NASA provenance separation
PASS

Unknown-time exact-UTC prohibition
PASS
```

---

# Deterministic Calculation Policy

Phase 8A calculation rules:

```text
UTC / MET conversion uses mission.json

elapsed-time calculation is deterministic

network access is not required

LLM access is not required

paid model access is not required
```

Validation:

```text
Mission-clock deterministic calculation policy
PASS

Elapsed-time deterministic policy
PASS

No calculation network dependency
PASS

No paid-model dependency
PASS

No LLM dependency
PASS
```

---

# Zero-Cost Runtime Boundary

The Phase 8A analyst has no dependency on:

```text
OpenAI SDK

Anthropic SDK

Gemini SDK
```

Validation:

```text
No OpenAI SDK dependency
PASS

No Anthropic SDK dependency
PASS

No Gemini SDK dependency
PASS
```

The deterministic analyst therefore remains usable without:

```text
API keys

paid inference

external model subscriptions
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_mission_analyst.py
```

Validation result:

```text
Analysis identity
PASS

Reference / processed index consistency
PASS

Mission clock configuration
PASS

Launch epoch preservation
PASS

Phase 7A dependency
PASS

Phase 7B dependency
PASS

25 reference datasets
PASS

Dataset-ID uniqueness
PASS

Major Phase 2-7 products indexed
PASS

Analyst self-index exclusion
PASS

Dataset citations
PASS

81 normalized public sources
PASS

Source-ID uniqueness
PASS

Public source occurrence tracking
PASS

Source URL preservation
PASS

24 shared mission events
PASS

Event-ID uniqueness
PASS

Mission-event ordering
PASS

Reported timing preservation
PASS

Derived geometry labeling preservation
PASS

Unknown-time non-inference
PASS

Approximate-time precision preservation
PASS

Event citations
PASS

10 decision threads
PASS

Decision-thread ID uniqueness
PASS

RTC2 anomaly boundary preservation
PASS

Lunar communications constraint boundary
PASS

Entry blackout constraint boundary
PASS

TPS decision maturity preservation
PASS

Decision-thread citations
PASS

6 postflight records
PASS

Urine vent investigation remains open
PASS

Mission/Fault Management analysis remains open
PASS

October lunar-science record
PASS

146 unified searchable records
PASS

Unified record-count arithmetic
PASS

5 analyst record types
PASS

Normalized search-token registry
PASS

Citation payload on every unified record
PASS

8 deterministic analyst tools
PASS

Search tool registry
PASS

Exact lookup tool registry
PASS

Mission-time calculation tool registry
PASS

No network-required analyst tools
PASS

Structured-local-artifact-first policy
PASS

Exact-ID retrieval policy
PASS

Keyword retrieval policy
PASS

Record-type filtering policy
PASS

Citation-return policy
PASS

Unsupported-fact invention prohibition
PASS

MissionLab/NASA provenance separation
PASS

Unknown-time exact-UTC prohibition
PASS

Mission-clock deterministic calculation policy
PASS

Elapsed-time deterministic policy
PASS

No calculation network dependency
PASS

No paid-model dependency
PASS

No LLM dependency
PASS

event_lookup execution
PASS

decision_thread_lookup execution
PASS

dataset_lookup execution
PASS

source_lookup execution
PASS

Unified keyword search execution
PASS

Return-link / RTC2 retrieval
PASS

Record-type filtered search
PASS

Search-result citation return
PASS

UTC -> MET execution
PASS

MET -> UTC execution
PASS

UTC/MET round-trip
PASS

Elapsed-time execution
PASS

OTC3 MET = 04:04:27:48
PASS

Earthset -> Earthrise = 41 minutes
PASS

Pericynthion MET calculation
PASS

No OpenAI SDK dependency
PASS

No Anthropic SDK dependency
PASS

No Gemini SDK dependency
PASS

Structured retrieval roadmap item
PASS

Deterministic-tools roadmap item
PASS

Citation-first answers correctly left to 8B
PASS

Optional local/browser LLM correctly left to 8B
PASS

No-paid-model roadmap requirement
PASS

Output registry
PASS
```

Final result:

```text
PHASE 8A VALIDATION PASSED
```

---

# Phase 8A Final Status

Structured retrieval:

```text
COMPLETE
```

Reference datasets indexed:

```text
25
```

Normalized public sources:

```text
81
```

Shared mission events:

```text
24
```

Decision threads:

```text
10
```

Postflight records:

```text
6
```

Unified searchable records:

```text
146
```

Deterministic analyst tools:

```text
8
```

Citation-bearing retrieval:

```text
COMPLETE
```

Mission-clock calculations:

```text
COMPLETE
```

Exact-ID lookup:

```text
COMPLETE
```

Keyword search:

```text
COMPLETE
```

Record-type filtering:

```text
COMPLETE
```

Provenance preservation:

```text
COMPLETE
```

Unknown-time protection:

```text
COMPLETE
```

Open-investigation preservation:

```text
COMPLETE
```

Network dependency:

```text
NONE
```

LLM dependency:

```text
NONE
```

Paid-model dependency:

```text
NONE
```

Overall:

```text
PHASE 8A
COMPLETE
```

---

# Phase 8B Handoff

Remaining Phase 8 roadmap items:

```text
citation-first answers

optional local/browser LLM

no paid model dependency
```

Phase 8B should build the answer layer on top of the validated deterministic analyst rather than bypassing it.

Required architecture:

```text
user question
↓
structured analyst retrieval
↓
evidence bundle
↓
claim selection
↓
provenance / known-unknown enforcement
↓
citation-first answer composition
↓
optional local/browser LLM presentation
```

The deterministic MissionLab index remains authoritative.

Any optional LLM must operate only on retrieved evidence bundles and must not become a required dependency.

Phase 8B should include:

```text
citation-first answer composer

question-class routing

mission-event answers

decision-thread answers

discipline-aware answers

mission-clock calculation answers

known / unknown responses

provenance labels

local evidence citations

optional browser-compatible LLM handoff

optional local-model handoff

deterministic fallback with no LLM

Phase 8 closure validation
```

---

---

# Phase 8B — Artemis II Citation-First Mission Analyst and Phase 8 Closure

## Goal

Complete the Evidence-Grounded Mission Analyst by adding a deterministic question router, citation-first answer composition, known/unknown handling, causation guardrails, discipline-aware answers, and optional local/browser LLM presentation handoff.

Phase 8B builds on the validated Phase 8A retrieval layer.

Architecture:

```text
user question
↓
deterministic question classification
↓
structured MissionLab retrieval
↓
validated evidence bundle
↓
claim construction
↓
provenance enforcement
↓
claim-level citations
↓
deterministic answer
↓
optional locked-claim LLM presentation handoff
```

The deterministic MissionLab evidence layer remains authoritative.

An LLM is never required for retrieval, calculations, routing, factual reasoning, or answer generation.

---

# Phase 8B Runtime

Created:

```text
scripts/analyst/answer_mission_question.py
```

Created independent validator:

```text
scripts/validation/validate_mission_analyst_interface.py
```

Generated:

```text
data/reference/artemis_ii_mission_analyst_interface.json

data/processed/analyst/artemis_ii_mission_analyst_interface.json

data/processed/analyst/phase8b_smoke_answers.json
```

Dataset:

```text
phase8b_artemis_ii_mission_analyst_interface
```

Status:

```text
CITATION_FIRST_MISSION_ANALYST_COMPLETE
```

---

# Dependencies

Phase 8B consumes:

```text
phase8a_artemis_ii_mission_analyst_index

phase7a_artemis_ii_mission_control_perspectives

phase7b_artemis_ii_mission_control_decision_threads
```

Roles:

```text
Phase 8A
structured retrieval and deterministic tools

Phase 7A
discipline registry and shared mission priorities

Phase 7B
decision threads and known / unknown evidence boundaries
```

Validation:

```text
Phase 8A dependency
PASS

Phase 7A dependency
PASS

Phase 7B dependency
PASS
```

---

# Deterministic Question Router

Phase 8B implements eight routes:

```text
EVENT_TIME

EVENT

DECISION_THREAD

DECISION_THREAD_CAUSATION

DISCIPLINE

DETERMINISTIC_ELAPSED_TIME

KNOWN_UNKNOWN

SEARCH_SYNTHESIS
```

Routing is deterministic.

No LLM participates in classification.

Validation:

```text
8-route deterministic question router
PASS

EVENT_TIME route
PASS

EVENT route
PASS

DECISION_THREAD route
PASS

DECISION_THREAD_CAUSATION route
PASS

DISCIPLINE route
PASS

DETERMINISTIC_ELAPSED_TIME route
PASS

KNOWN_UNKNOWN route
PASS

SEARCH_SYNTHESIS route
PASS

LLM-free routing
PASS
```

---

# Routing Correction During Validation

Initial validation identified one narrow routing defect.

The router correctly classified:

```text
What happened at Entry Interface?
```

as:

```text
EVENT
```

but the answer-composition function changed the route to:

```text
EVENT_TIME
```

solely because the event contained a timestamp.

This violated separation between:

```text
question intent
```

and:

```text
available event metadata
```

The implementation was corrected so that:

```text
classifier chooses route
↓
answer composer preserves route
```

Now:

```text
What happened at Entry Interface?
→ EVENT
```

while:

```text
When was Entry Interface?
→ EVENT_TIME
```

Independent validation after the correction:

```text
Runtime event answer execution
PASS
```

---

# Citation-First Answer Contract

Every factual claim must include at least one citation.

Answer objects contain:

```text
question

route

answer_status

answer_text

claims

citations

evidence_bundle

deterministic_tools

citation_first

unsupported_fact_invention

llm_required

paid_model_required
```

Every claim contains:

```text
statement

provenance

confidence

citation_ids
```

Validation:

```text
Citation-first answer contract
PASS

Claim-level citation requirement
PASS

Provenance-label requirement
PASS

Known/unknown answer support
PASS

Unsupported-fact invention prohibition
PASS

No LLM requirement
PASS

No paid-model requirement
PASS
```

---

# Citation Rendering

Citation identifiers are generated deterministically:

```text
[C1]

[C2]

[C3]
...
```

Each citation maps to:

```text
dataset_id

local artifact path

structured locator

evidence class

optional public URL
```

Example event locator:

```text
data/reference/artemis_ii_mission_control_perspectives.json
::
shared_timeline[event_id=A2_RTC2]
```

Example decision-thread locator:

```text
data/reference/artemis_ii_decision_threads.json
::
decision_threads[thread_id=RETURN_LINK_ANOMALY_RTC2]
```

The textual answer must contain every citation ID used by its claims.

Validation:

```text
Smoke-answer citation integrity
PASS

Citation-preserving handoff
PASS
```

---

# EVENT_TIME Answers

Example question:

```text
When was RTC2?
```

Route:

```text
EVENT_TIME
```

Validated answer anchor:

```text
RTC2
2026-04-10T02:53:00Z
```

The answer also preserves its MissionLab mission-clock context and supporting event summary.

Validation:

```text
RTC2 event-time smoke answer
PASS

Runtime EVENT_TIME answer execution
PASS
```

---

# EVENT Answers

Example:

```text
What happened at Entry Interface?
```

Route:

```text
EVENT
```

The answer provides the event summary rather than treating the question as merely a request for timestamp information.

Validation:

```text
Runtime event answer execution
PASS
```

This preserves the distinction:

```text
EVENT QUESTION
!=
EVENT TIME QUESTION
```

---

# DECISION_THREAD Answers

Example:

```text
What happened with the Artemis II heat shield?
```

Route:

```text
DECISION_THREAD
```

Retrieved thread:

```text
TPS_RISK_MITIGATION_CLOSURE
```

The answer is constructed from:

```text
thread classification

detection

action

outcome
```

and preserves the established Phase 7 engineering evidence chain.

Validation:

```text
TPS decision-thread smoke answer
PASS

Runtime decision-thread answer execution
PASS
```

---

# DECISION_THREAD_CAUSATION Answers

Example:

```text
Did the return link loss cause RTC2?
```

Route:

```text
DECISION_THREAD_CAUSATION
```

Answer status:

```text
SUPPORTED_WITH_CAUSATION_BOUNDARY
```

The analyst states:

```text
public evidence does not establish
that return-link loss caused RTC2
or changed its targeting
```

Supported public sequence:

```text
return-link interruption
↓
communications recovery
↓
burn preparation resumed
↓
RTC2 execution
```

MissionLab guardrail:

```text
TEMPORAL_SEQUENCE
!=
CAUSATION
```

Validation:

```text
RTC2 causation-boundary smoke answer
PASS

Runtime causation answer execution
PASS

return-link loss -> RTC2 causation claimed
NO

temporal sequence != causation
PRESERVED
```

---

# KNOWN_UNKNOWN Answers

MissionLab can answer questions whose correct answer is:

```text
not publicly known
```

rather than fabricating a conclusion.

Example:

```text
What was the root cause of the urine vent-line issue?
```

Route:

```text
KNOWN_UNKNOWN
```

Status:

```text
UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE
```

The answer preserves:

```text
POSSIBLE_ICE
!=
CONFIRMED_ICE
```

and:

```text
troubleshooting action
!=
confirmed root cause
```

Validation:

```text
Vent-line known/unknown smoke answer
PASS

Runtime KNOWN_UNKNOWN answer execution
PASS

urine vent-line root cause
UNKNOWN

possible ice != confirmed ice
PRESERVED
```

---

# Open Investigation Protection

Known/unknown policy requires:

```text
unknowns are answerable
```

but:

```text
unknown answer must state the evidence boundary
```

Forbidden:

```text
hypothesis → fact promotion

open investigation → forced closure

missing exact time → invented exact time
```

Validation:

```text
Known/unknown policy
PASS

Unknown boundary requirement
PASS

Hypothesis / fact separation
PASS

Open-investigation preservation
PASS

Missing-time non-inference
PASS
```

---

# Deterministic Calculation Answers

Phase 8B can call Phase 8A deterministic tools when a question requires calculation.

Example:

```text
How long was it between Earthset and Earthrise?
```

Inputs:

```text
Earthset
2026-04-06T22:41:00Z

Earthrise
2026-04-06T23:22:00Z
```

Result:

```text
41 minutes
```

Formatted:

```text
00:00:41:00
```

The answer also preserves the evidence boundary:

```text
reported-image interval
!=
full-occultation duration
```

Validation:

```text
Earthset/Earthrise calculation smoke answer
PASS

Runtime deterministic elapsed-time answer
PASS

Earthset -> Earthrise reported-image interval
41 min

reported-image interval != full-occultation duration
PASS
```

---

# DISCIPLINE Answers

Example:

```text
What does the SCIENCE perspective focus on?
```

Route:

```text
DISCIPLINE
```

The analyst returns:

```text
discipline role context

MissionLab focus areas

selected PRIMARY-priority mission events

supporting citations
```

SCIENCE focus includes:

```text
lunar targeting

crew observations

science imaging

impact flashes

terminator terrain

eclipse observations

LRO context
```

Validation:

```text
SCIENCE discipline smoke answer
PASS

Runtime discipline answer execution
PASS
```

---

# SEARCH_SYNTHESIS Fallback

Questions that do not match a specialized route use:

```text
SEARCH_SYNTHESIS
```

The analyst queries the Phase 8A unified evidence index.

If matching evidence exists:

```text
top evidence records
→ cited synthesis
```

If no sufficient indexed evidence exists:

```text
INSUFFICIENT_INDEXED_EVIDENCE
```

with an explicit boundary statement.

The fallback does not invent facts merely because a question was asked.

Validation:

```text
Runtime search-synthesis fallback
PASS
```

---

# Deterministic Retrieval Authority

Phase 8 establishes a strict authority hierarchy.

Authoritative:

```text
validated MissionLab reference artifacts

deterministic retrieval

deterministic calculations
```

Optional presentation layer:

```text
local LLM

browser LLM
```

The optional presentation layer may:

```text
rewrite locked claims for readability
```

It may not:

```text
add facts

override evidence boundaries

change provenance

invent citations
```

Validation:

```text
Deterministic retrieval authority
PASS

Deterministic calculation authority
PASS

LLM new-fact prohibition
PASS

LLM provenance-change prohibition
PASS

LLM citation-invention prohibition
PASS

LLM evidence-boundary override prohibition
PASS
```

---

# Optional Local LLM Handoff

Adapter:

```text
LOCAL_LLM_PROMPT_HANDOFF
```

The adapter exports:

```text
question

locked claims

claim provenance

claim confidence

citation IDs

citation registry

deterministic answer

strict formatting rules
```

It does not execute a model.

Properties:

```text
optional = true

execution_performed = false

network_call_performed = false

API key required = false

paid model required = false
```

Validation:

```text
Local LLM handoff adapter
PASS

Live local LLM handoff construction
PASS
```

---

# Optional Browser LLM Handoff

Adapter:

```text
BROWSER_LLM_PROMPT_HANDOFF
```

The same locked evidence bundle can be exported for optional browser-side presentation.

Properties:

```text
optional = true

execution_performed = false

network_call_performed = false

API key required = false

paid model required = false
```

Validation:

```text
Browser LLM handoff adapter
PASS

Live browser LLM handoff construction
PASS
```

---

# Locked-Claim LLM Policy

Optional LLM prompt explicitly requires:

```text
Use ONLY supplied locked claims and citations.

Do not add facts.

Do not invent timestamps.

Do not invent causes.

Do not invent root causes.

Do not infer private controller actions.

Do not infer private Mission Control dialogue.

Do not convert MissionLab-derived information
into NASA-reported fact.

Preserve evidence limitations.

Every factual sentence must use
the supplied citations.
```

Additional handoff guardrails:

```text
Do not infer undisclosed decision authority.

Do not convert temporal order into causation.

Do not promote hypotheses to root causes.

Preserve MissionLab-derived vs NASA-reported provenance.
```

Validation:

```text
Locked-claim handoff
PASS

Citation-preserving handoff
PASS

No handoff model execution
PASS

No handoff network call
PASS
```

---

# Zero-Cost Runtime

Phase 8B contains no dependency on:

```text
OpenAI SDK

Anthropic SDK

Gemini SDK
```

and performs no embedded HTTP model request.

Validation:

```text
No OpenAI SDK dependency
PASS

No Anthropic SDK dependency
PASS

No Gemini SDK dependency
PASS

No embedded HTTP model call
PASS
```

Therefore:

```text
API key required
NONE

paid model dependency
NONE

embedded model execution
NONE
```

---

# Persisted Smoke Answers

Phase 8B stores six smoke-test answers.

Questions:

```text
When was RTC2?

Did the return link loss cause RTC2?

What was the root cause of the urine vent-line issue?

How long was it between Earthset and Earthrise?

What does the SCIENCE perspective focus on?

What happened with the Artemis II heat shield?
```

Validated routes:

```text
EVENT_TIME

DECISION_THREAD_CAUSATION

KNOWN_UNKNOWN

DETERMINISTIC_ELAPSED_TIME

DISCIPLINE

DECISION_THREAD
```

Validation:

```text
6 persisted smoke answers
PASS

Smoke-answer citation integrity
PASS

RTC2 event-time smoke answer
PASS

RTC2 causation-boundary smoke answer
PASS

Vent-line known/unknown smoke answer
PASS

Earthset/Earthrise calculation smoke answer
PASS

SCIENCE discipline smoke answer
PASS

TPS decision-thread smoke answer
PASS
```

---

# Persisted LLM Handoff Tests

The smoke artifact also contains:

```text
local_llm_handoff

browser_llm_handoff
```

Validation:

```text
Persisted local LLM handoff
PASS

Persisted browser LLM handoff
PASS
```

---

# Critical Non-Equivalences

Phase 8B validates eight critical analyst boundaries.

```text
LLM_PRESENTATION
!=
EVIDENCE_AUTHORITY
```

```text
RETRIEVAL_MATCH
!=
FACT_NOT_SUPPORTED_BY_RECORD
```

```text
MISSIONLAB_DERIVED
!=
NASA_REPORTED
```

```text
TEMPORAL_SEQUENCE
!=
CAUSATION
```

```text
HYPOTHESIS
!=
CONFIRMED_ROOT_CAUSE
```

```text
UNKNOWN_PUBLIC_FACT
!=
PERMISSION_TO_INVENT
```

```text
DISCIPLINE_RELEVANCE
!=
DECISION_AUTHORITY
```

```text
OPTIONAL_LLM_HANDOFF
!=
REQUIRED_MODEL_DEPENDENCY
```

Validation:

```text
8 critical non-equivalences
PASS

LLM presentation / evidence authority boundary
PASS

Retrieval match / unsupported fact boundary
PASS

MissionLab-derived / NASA-reported boundary
PASS

Temporal-sequence / causation boundary
PASS

Hypothesis / root-cause boundary
PASS

Unknown-public-fact / invention boundary
PASS

Discipline-relevance / authority boundary
PASS

Optional-handoff / required-model boundary
PASS
```

---

# Independent Validation

Created:

```text
scripts/validation/validate_mission_analyst_interface.py
```

Final validation:

```text
Analysis identity
PASS

Reference / processed interface consistency
PASS

Phase 8A dependency
PASS

Phase 7A dependency
PASS

Phase 7B dependency
PASS

8-route deterministic question router
PASS

EVENT_TIME route
PASS

EVENT route
PASS

DECISION_THREAD route
PASS

DECISION_THREAD_CAUSATION route
PASS

DISCIPLINE route
PASS

DETERMINISTIC_ELAPSED_TIME route
PASS

KNOWN_UNKNOWN route
PASS

SEARCH_SYNTHESIS route
PASS

LLM-free routing
PASS

Citation-first answer contract
PASS

Claim-level citation requirement
PASS

Provenance-label requirement
PASS

Known/unknown answer support
PASS

Unsupported-fact invention prohibition
PASS

No LLM requirement
PASS

No paid-model requirement
PASS

Deterministic retrieval authority
PASS

Deterministic calculation authority
PASS

LLM new-fact prohibition
PASS

LLM provenance-change prohibition
PASS

LLM citation-invention prohibition
PASS

LLM evidence-boundary override prohibition
PASS

Known/unknown policy
PASS

Unknown boundary requirement
PASS

Hypothesis / fact separation
PASS

Open-investigation preservation
PASS

Missing-time non-inference
PASS

2 optional LLM handoff adapters
PASS

Local LLM handoff adapter
PASS

Browser LLM handoff adapter
PASS

Embedded model execution disabled
PASS

API-key requirement
NONE

Paid-model requirement
NONE

6 persisted smoke answers
PASS

Smoke-answer citation integrity
PASS

RTC2 event-time smoke answer
PASS

RTC2 causation-boundary smoke answer
PASS

Vent-line known/unknown smoke answer
PASS

Earthset/Earthrise calculation smoke answer
PASS

SCIENCE discipline smoke answer
PASS

TPS decision-thread smoke answer
PASS

Persisted local LLM handoff
PASS

Persisted browser LLM handoff
PASS

Runtime EVENT_TIME answer execution
PASS

Runtime causation answer execution
PASS

Runtime KNOWN_UNKNOWN answer execution
PASS

Runtime deterministic elapsed-time answer
PASS

Runtime discipline answer execution
PASS

Runtime decision-thread answer execution
PASS

Runtime event answer execution
PASS

Runtime search-synthesis fallback
PASS

Live local LLM handoff construction
PASS

Live browser LLM handoff construction
PASS

Locked-claim handoff
PASS

Citation-preserving handoff
PASS

No handoff model execution
PASS

No handoff network call
PASS

No OpenAI SDK dependency
PASS

No Anthropic SDK dependency
PASS

No Gemini SDK dependency
PASS

No embedded HTTP model call
PASS

8 critical non-equivalences
PASS

Structured retrieval roadmap coverage
PASS

Deterministic tools roadmap coverage
PASS

Citation-first answers roadmap coverage
PASS

Optional local/browser LLM roadmap coverage
PASS

No-paid-model roadmap coverage
PASS

Phase 8 roadmap coverage
PASS

Output registry
PASS
```

Final result:

```text
PHASE 8B VALIDATION PASSED

PHASE 8 ROADMAP COVERAGE PASSED
```

---

# Phase 8 Architecture Final State

Deterministic retrieval:

```text
AUTHORITATIVE
```

Deterministic calculations:

```text
AUTHORITATIVE
```

Citation-first answer composer:

```text
COMPLETE
```

Claim-level citations:

```text
COMPLETE
```

Known/unknown handling:

```text
COMPLETE
```

Causation guardrails:

```text
COMPLETE
```

Discipline-aware answers:

```text
COMPLETE
```

Mission-event answers:

```text
COMPLETE
```

Decision-thread answers:

```text
COMPLETE
```

Mission-clock answers:

```text
COMPLETE
```

Search fallback:

```text
COMPLETE
```

Optional local LLM handoff:

```text
COMPLETE
```

Optional browser LLM handoff:

```text
COMPLETE
```

Embedded LLM execution:

```text
NONE
```

Network model dependency:

```text
NONE
```

API-key dependency:

```text
NONE
```

Paid-model dependency:

```text
NONE
```

---

# Phase 8 Roadmap Closure

## Structured Retrieval Over Events / Data / Sources

```text
COMPLETE
```

Implemented in:

```text
Phase 8A
```

Coverage:

```text
25 datasets

81 normalized public sources

24 mission events

10 decision threads

6 postflight records

146 unified searchable records
```

---

## Deterministic Calculations Exposed as Tools

```text
COMPLETE
```

Tools include:

```text
UTC -> MET

MET -> UTC

elapsed time
```

plus deterministic retrieval tools.

---

## Citation-First Answers

```text
COMPLETE
```

Every claim requires citations.

Unsupported facts cannot be silently introduced.

---

## Optional Local / Browser LLM

```text
COMPLETE AS OPTIONAL HANDOFF
```

The LLM layer is:

```text
presentation-only

non-authoritative

optional

zero-cost compatible
```

---

## No Paid Model Dependency

```text
COMPLETE
```

Required paid APIs:

```text
NONE
```

---

# Phase 8 Final Status

```text
PHASE 8 — EVIDENCE-GROUNDED MISSION ANALYST
```

Structured retrieval:

```text
COMPLETE
```

Deterministic tools:

```text
COMPLETE
```

Citation-bearing retrieval:

```text
COMPLETE
```

Citation-first answers:

```text
COMPLETE
```

Known / unknown handling:

```text
COMPLETE
```

Provenance enforcement:

```text
COMPLETE
```

Causation protection:

```text
COMPLETE
```

Root-cause protection:

```text
COMPLETE
```

MissionLab-derived / NASA-reported separation:

```text
COMPLETE
```

Discipline-aware analysis:

```text
COMPLETE
```

Optional LLM presentation:

```text
COMPLETE
```

Zero-cost deterministic fallback:

```text
COMPLETE
```

Independent validation:

```text
PASS
```

Overall:

```text
PHASE 8
COMPLETE RELATIVE TO VALIDATED MISSIONLAB EVIDENCE
```

---

# Phase 9 Handoff

Next roadmap phase:

```text
PHASE 9 — PUBLICATION QUALITY
```

Phase 9 should not add major new mission reconstruction.

Its role is to turn the validated MissionLab engineering system into a publication-quality public project.

The work should focus on:

```text
repository architecture documentation

final README

mission-data provenance guide

methodology documentation

validation summary

engineering-boundary documentation

Phase 1-8 results summary

key figures and visual products

analyst usage guide

reproducibility instructions

installation instructions

public demo workflow

final technical narrative

portfolio / recruiter-facing project explanation

repository cleanup

final cross-phase validation

publication-quality release
```

The Phase 9 publication layer must preserve all established evidence boundaries and should consume the validated Phase 1-8 products rather than recreate them.

---

---

# Phase 9A — Publication Documentation Pack

## Goal

Replace stale Phase 0-facing documentation with publication-grade documentation generated from the validated Phase 0-8 MissionLab evidence stack.

## Generated

```text
README.md
docs/METHODOLOGY.md
docs/VALIDATION_REPORT.md
docs/ANALYST_GUIDE.md
docs/PUBLICATION_SUMMARY.md
data/reference/artemis_ii_publication_manifest.json
```

Builder:

```text
scripts/publication/build_publication_pack.py
```

Validator:

```text
scripts/validation/validate_publication_pack.py
```

## Publication Metrics

```text
indexed reference datasets: 25
normalized public sources: 81
shared mission events: 24
decision threads: 10
postflight engineering records: 6
unified searchable analyst records: 146
deterministic analyst tools: 8
deterministic answer routes: 8
```

## Documentation Coverage

```text
README stale Phase 0 status removed: PASS
README current project status: PASS
README Mission Analyst coverage: PASS
README evidence boundaries: PASS

Methodology evidence classes: PASS
Methodology mission-clock policy: PASS
Methodology reconstruction boundaries: PASS
Methodology known/unknown policy: PASS

Phase 0-8 validation summary: PASS
No-paid-model validation boundary: PASS
Preserved unknowns documentation: PASS

Analyst guide commands: PASS
8 analyst routes documented: PASS
Optional LLM handoff documented: PASS

Publication summary scope: PASS
Publication engineering philosophy: PASS
```

## Publication Boundaries

```text
no new mission reconstruction: PASS
public evidence only: PASS
unknowns remain unknown: PASS
no paid-model dependency: PASS
no private NASA material: PASS
```

Critical boundaries remain:

```text
MISSIONLAB DERIVED
!=
NASA REPORTED
```

```text
PUBLIC EVENT SEQUENCE
!=
COMPLETE PRIVATE FLIGHT LOOP
```

```text
TEMPORAL SEQUENCE
!=
CAUSATION
```

```text
TROUBLESHOOTING ACTION
!=
CONFIRMED ROOT CAUSE
```

```text
UNKNOWN PUBLIC FACT
!=
PERMISSION TO INVENT
```

## Validation

```text
Manifest identity: PASS
Mission identity: PASS
Phase identity: PASS
Publication status: PASS

25 indexed datasets: PASS
81 normalized public sources: PASS
24 shared mission events: PASS
10 decision threads: PASS
6 postflight records: PASS
146 searchable records: PASS
8 deterministic tools: PASS
8 deterministic answer routes: PASS

Phase 9A documentation coverage: PASS
Phase 9B handoff state: PASS
Phase 9C handoff state: PASS
```

Final result:

```text
PHASE 9A VALIDATION PASSED
```

## Phase 9 Status

```text
Phase 9A — publication documentation
COMPLETE

Phase 9B — accessibility, responsive behavior, tests/CI, performance, deployment readiness
NEXT

Phase 9C — final cross-phase publication validation
PENDING
```

---

---

# Phase 9B — Public Web, Accessibility, CI, and Deployment Readiness

## Goal

Replace the obsolete Phase 0 public interface with a publication-ready web experience driven by validated Phase 7A and Phase 9A artifacts.

## Generated / Updated

```text
index.html
app.js
styles.css
.github/workflows/ci.yml
.github/workflows/pages.yml
scripts/publication/build_publication_web.py
scripts/validation/validate_publication_web.py
data/reference/artemis_ii_publication_web_manifest.json
```

## Public Web

```text
validated Phase 7A shared timeline: 24 events
Phase 0 seed timeline frontend dependency: REMOVED
Phase 9 project status: CURRENT
publication metrics integration: COMPLETE
validated event timing / precision handling: COMPLETE
```

## Accessibility

```text
skip navigation: PASS
semantic navigation: PASS
ARIA live regions: PASS
keyboard-focusable detail panel: PASS
visible keyboard focus: PASS
44 px minimum interactive targets: PASS
reduced-motion support: PASS
```

## Responsive Behavior

```text
desktop layout: PASS
tablet breakpoint: PASS
mobile breakpoint: PASS
responsive event timeline: PASS
responsive metrics / detail grids: PASS
```

## Evidence Integrity

```text
validated timeline frontend source: PASS
Phase 0 seed dependency removed: PASS
missing vs exact timing distinction: PASS
HTML output escaping: PASS
no new mission reconstruction: PASS
```

Critical publication boundaries remain:

```text
MISSIONLAB DERIVED
!=
NASA REPORTED
```

```text
TEMPORAL SEQUENCE
!=
CAUSATION
```

```text
UNKNOWN PUBLIC FACT
!=
PERMISSION TO INVENT
```

## CI

GitHub Actions workflow created:

```text
.github/workflows/ci.yml
```

Validated CI coverage:

```text
Python source compilation: PASS
Phase 9A publication validator: INCLUDED
Phase 9B public-web validator: INCLUDED
```

## Deployment Readiness

GitHub Pages workflow created:

```text
.github/workflows/pages.yml
```

Deployment model:

```text
static zero-framework site
GitHub Pages artifact deployment
main-branch deployment trigger
manual workflow dispatch available
```

Validation:

```text
GitHub Pages workflow: PASS
static-site artifact deployment: PASS
Pages permission model: PASS
```

## Performance

```text
static zero-framework architecture: COMPLETE
no frontend framework runtime: PASS
small HTML / CSS / JavaScript surface: PASS
validated JSON artifacts loaded directly: PASS
```

## Phase 9B Validation

```text
Phase 7A validated timeline dependency: PASS
24-event shared timeline: PASS
Phase 9A publication dependency: PASS
Phase 9B web manifest identity: PASS

Skip navigation: PASS
Semantic main navigation: PASS
ARIA live regions: PASS
Keyboard-focusable detail panel: PASS
Current Phase 9 status: PASS
Stale Phase 0 status removed: PASS

Validated timeline frontend source: PASS
Phase 0 seed dependency removed: PASS
Missing/exact timing distinction: PASS
HTML output escaping: PASS

Visible keyboard focus: PASS
44px interactive targets: PASS
Tablet responsive breakpoint: PASS
Mobile responsive breakpoint: PASS
Reduced-motion support: PASS

GitHub Actions CI workflow: PASS
Python syntax check in CI: PASS
Phase 9A validator in CI: PASS
Phase 9B validator in CI: PASS

GitHub Pages workflow: PASS
Static-site artifact deployment: PASS
Pages permission model: PASS

Validated timeline only: PASS
No Phase 0 seed dependency: PASS
No new mission reconstruction: PASS
```

Final result:

```text
PHASE 9B VALIDATION PASSED
```

## Phase 9 Status

```text
Phase 9A — publication documentation
COMPLETE

Phase 9B — public web, accessibility, responsive behavior, CI, performance, deployment readiness
COMPLETE

Phase 9C — final cross-phase publication validation
NEXT
```

---

---

# Phase 9C — Final Cross-Phase Release Validation

## Goal

Close the A2 MissionLab roadmap with final publication validation across the validated Phase 0-9 project state.

## Finalization Outputs

```text
README.md
docs/ROADMAP.md
docs/assets/a2-missionlab-release-overview.svg
.github/workflows/ci.yml
scripts/publication/finalize_release.py
scripts/validation/validate_release.py
data/reference/artemis_ii_release_manifest.json
```

## Release State

```text
Phase 0: COMPLETE
Phase 1: COMPLETE
Phase 2: COMPLETE
Phase 3: COMPLETE
Phase 4: COMPLETE
Phase 5: COMPLETE
Phase 6: COMPLETE
Phase 7: COMPLETE
Phase 8: COMPLETE
Phase 9: COMPLETE
```

## Validated Release Scale

```text
indexed reference datasets: 25
normalized public sources: 81
shared mission events: 24
decision threads: 10
postflight engineering records: 6
unified searchable records: 146
deterministic analyst tools: 8
deterministic answer routes: 8
```

## Publication Closure

```text
README final status: PASS
README demo media: PASS
release overview SVG: PASS

roadmap phases 0-9 present: PASS
roadmap Phase 9 closure: PASS
demo-media roadmap requirement: PASS

public interface current status: PASS
validated timeline source: PASS
Phase 0 seed dependency absent: PASS
```

## CI and Deployment

```text
Phase 9A validation in CI: PASS
Phase 9B validation in CI: PASS
final release validation in CI: PASS
GitHub Pages main-branch deployment: PASS
```

## Evidence Boundaries

```text
public evidence only: PASS
unknowns remain unknown: PASS
no paid-model dependency: PASS
no private NASA material: PASS
no new Phase 9 mission reconstruction: PASS
core evidence boundaries preserved: PASS
```

Critical rules remain:

```text
MISSIONLAB DERIVED
!=
NASA REPORTED
```

```text
TEMPORAL SEQUENCE
!=
CAUSATION
```

```text
UNKNOWN PUBLIC FACT
!=
PERMISSION TO INVENT
```

## Final Validation

```text
Mission identity and launch epoch: PASS
Phase 8 analyst dependency: PASS
Phase 9A documentation dependency: PASS
Phase 9B web/CI dependency: PASS
Phase 9C release manifest identity: PASS

25 indexed datasets: PASS
81 normalized sources: PASS
24 mission events: PASS
10 decision threads: PASS
6 postflight records: PASS
146 searchable records: PASS
8 deterministic tools: PASS
8 answer routes: PASS

README final status: PASS
README demo media: PASS
Release overview SVG: PASS

Roadmap phases 0-9 present: PASS
Roadmap Phase 9 closure: PASS
Demo-media roadmap requirement: PASS

Public interface current status: PASS
Validated timeline source: PASS
Phase 0 seed dependency absent: PASS

Phase 9A validation in CI: PASS
Phase 9B validation in CI: PASS
Final release validation in CI: PASS
GitHub Pages main-branch deployment: PASS

Public evidence only: PASS
Unknowns remain unknown: PASS
No paid-model dependency: PASS
No private NASA material: PASS
No new Phase 9 mission reconstruction: PASS

Core evidence boundaries preserved: PASS
```

Final result:

```text
PHASE 9C RELEASE VALIDATION PASSED
MISSIONLAB RELEASE CANDIDATE COMPLETE
```

## Project Status

```text
A2 MissionLab Phase 0-9 roadmap:
COMPLETE

Release candidate:
COMPLETE

Next repository action:
merge phase-9-publication-quality into main
```

---

## Phase H — Space Weather Redesign

**Status:** COMPLETE — VALIDATED ON REAL WINDOWS CHROME + EDGE

### Objective

Replace the shallow normalized Space Weather heuristic with a defensible public-data-grounded educational experience that answers why a crewed lunar mission cares by teaching:

`space phenomenon → measurement → physical consequence → mission/crew implication`

The redesign preserves all completed Phase F/G work, the Mission multi-page architecture, the canonical evidence taxonomy, zero-cost static deployment, and all protected Mission Explorer, Through Orion's Windows, GNC, Mission Control, PSI, and Trajectory Correction behavior.

### Immutable starting state

- Repository: `C:\Users\prakh\Documents\a2-missionlab`
- Branch: `phase-10-quality-recovery`
- Starting HEAD: `c283e104d92e9d587d50d0879d3965243a1dcd20`
- Starting parent: `ccf6ad0db89f9c68c551776e6a55556b23e334d1`
- Starting tree: `83bdbea2b99daeafc43ecfaf8a4a26273e1ccb71`
- Starting subject: `Redesign trajectory correction lab`
- `origin/main` protected baseline: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- The real `phase-10-quality-recovery` branch remains intentionally local-only/unpublished unless the user explicitly publishes it.

### Repository archaeology and historical findings

- The Phase H starting Space Weather experience lived at `mission.html#space-weather` with its runtime embedded in `js/mission.js`.
- Its primary scenario inputs were generic normalized `solar activity 0–100` and `conceptual shielding 0–100` controls feeding a deliberately conceptual qualitative heuristic.
- The strongest historical pre-split build around `718abc5e18403ba26eff3a68cfd208690ce6dbaf` did not contain a materially stronger Space Weather model worth restoring unchanged.
- Existing Phase 5A/5B analytical work was retained and reused rather than replaced:
  - `scripts/analysis/analyze_space_weather_context.py`
  - `scripts/analysis/prepare_nairas_radiation_interface.py`
  - `scripts/validation/validate_space_weather_context.py`
  - `scripts/validation/validate_nairas_radiation_interface.py`
  - `data/reference/artemis_ii_nairas_interface.json`
  - existing Space Weather / radiation figures, Library material, and Technical Report material
- Phase 5A had already aligned 13,053 one-minute NASA OMNI rows to the Artemis II mission clock.
- The historical Phase 5B NAIRAS artifact prepared 3,262 public-trajectory rows for a NAIRAS 3.0 interface but explicitly recorded no submitted MissionLab run, no run output, no established Orion shielding depth, and no NAIRAS-derived Artemis II dose.

### NAIRAS version-resolution finding

Phase H resolved the repository's cross-layer version inconsistency instead of silently changing either side.

- Current NASA CCMC documentation identifies the model family as **NAIRAS Version 4**.
- The current CCMC change log records **Version 4.15 released for production use on June 8, 2026**.
- The CCMC page was rechecked during Phase H and was marked **Last Updated October 13, 2026**.
- MissionLab's older Phase 5B artifact remains correctly identified as a **NAIRAS 3.0 interface preparation**.
- No historical artifact was relabeled as a Version 4 run.
- No MissionLab Version 4 run is claimed.

Authoritative public references used for the resolution:

- NASA CCMC NAIRAS Version 4: `https://ccmc.gsfc.nasa.gov/models/NAIRAS~4/`
- NOAA Solar Radiation Storm S-scale: `https://www.spaceweather.gov/noaa-scales-explanation`
- NOAA GOES proton-flux product: `https://www.spaceweather.gov/products/goes-proton-flux`
- NASA Artemis II radiation sensors: `https://www.nasa.gov/general/artemis-ii-crew-both-subjects-and-scientists-in-nasa-deep-space-research/`

### Exact changed-file allowlist

Phase H changed exactly these 15 repository-relative paths:

1. `data/reference/artemis_ii_space_weather_phase_h.json` — added
2. `data/sources/source_catalog.json` — modified
3. `docs/SPACE_WEATHER_QA.md` — added
4. `js/mission.js` — modified
5. `js/space-weather-model.js` — added
6. `js/space-weather.js` — added
7. `library.js` — modified
8. `mission.html` — modified
9. `scripts/validate_public_experience.py` — modified
10. `scripts/validation/space_weather_regression.html` — added
11. `scripts/validation/validate_space_weather_model.js` — added
12. `scripts/validation/validate_space_weather_regression.py` — added
13. `scripts/validation/validate_text_integrity.py` — modified
14. `space-weather.css` — added
15. `technical-report.html` — modified

No Phase F/G production paths outside this allowlist were rewritten.

### Restored / redesigned capability

The generic normalized primary controls were removed from the public experience.

The new primary scenario quantity is:

- integral proton flux for energies `≥10 MeV`
- unit: `pfu`
- `1 pfu = 1 proton / (cm² · s · sr)`
- logarithmic scenario axis
- public NOAA S-scale reference presets:
  - Below S1: `1 pfu`
  - S1: `10 pfu`
  - S2: `100 pfu`
  - S3: `1,000 pfu`
  - S4: `10,000 pfu`
  - S5: `100,000 pfu`

Location context remains selectable for:

- LEO
- Deep space
- Lunar vicinity

Location deliberately changes explanatory mission context only. It does **not** numerically alter the measured proton flux, NOAA classification, or manufacture a shielding/dose result.

### Public educational architecture

Dedicated Phase H modules now separate the feature from the large Mission runtime:

- `js/space-weather-model.js` — pure classification/evidence-boundary model
- `js/space-weather.js` — interaction and event-driven visualization runtime
- `space-weather.css` — dedicated responsive styling
- `mission.html#space-weather` — existing Mission-route host retained
- `data/reference/artemis_ii_space_weather_phase_h.json` — explicit evidence/version manifest
- `scripts/validation/validate_space_weather_model.js` — pure model/evidence regression
- `scripts/validation/space_weather_regression.html` — browser harness
- `scripts/validation/validate_space_weather_regression.py` — Chrome/Edge browser driver
- `docs/SPACE_WEATHER_QA.md` — Phase H model/evidence/test contract

The public hierarchy teaches:

1. **PHENOMENON** — solar eruption / energetic-particle event
2. **MEASUREMENT** — energetic proton flux and onboard radiation sensors
3. **PHYSICAL CONSEQUENCE** — ionization, energy deposition, electronics effects
4. **MISSION / CREW IMPLICATION** — awareness, assessment, and protective decision-making

### Mission-window public context

Phase H surfaces selected validated Phase 5A NASA OMNI mission-window extrema as **MISSIONLAB DERIVED FROM NASA OMNI**, not as Orion-local radiation measurements:

- maximum solar-wind speed: `789.7 km/s` at `2026-04-03 15:52 UTC`, MET `01:17:16:48`
- minimum BZ GSM: `−14.46 nT` at `2026-04-02 07:09 UTC`, MET `00:08:33:48`
- maximum flow pressure: `11.75 nPa` at `2026-04-10 07:16 UTC`, MET `08:08:40:48`
- minimum SYM/H: `−104 nT` at `2026-04-02 08:41 UTC`, MET `00:10:05:48`

The public copy explicitly states that NASA OMNI's near-Earth/bow-shock context is not proof of an Orion-local radiation event, spacecraft anomaly, or crew dose.

### Artemis II radiation-monitoring context

Public NASA documentation supports the following mission context used by Phase H:

- six active Hybrid Electronic Radiation Assessor sensors inside Orion
- a Crew Active Dosimeter assigned to each crewmember
- radiation measurements can support mission-control protective decisions

MissionLab does not claim access to private/as-flown individual crew dosimetry or internal NASA action thresholds.

### Canonical evidence boundaries

Phase H preserves and makes explicit:

- proton flux ≠ absorbed dose
- proton flux ≠ crew effective dose
- NOAA S-scale ≠ Artemis II flight rule
- location selection ≠ Orion shielding model
- NASA OMNI near-Earth context ≠ Orion-local radiation field
- external environment ≠ crew exposure
- model output ≠ dosimeter measurement
- Phase 5B NAIRAS 3.0 interface ≠ NAIRAS Version 4 run
- prepared trajectory fields ≠ radiation dose
- no Orion shielding depth is invented
- no NAIRAS run is claimed without actual run output
- no crew dosimetry is fabricated
- public OEM coverage is not extended beyond public states

### Protected-system integration

- The Space Weather host remains on the existing Mission route rather than creating a needless new top-level route.
- The old Space Weather heuristic was removed from `js/mission.js`; the new model/runtime is modular.
- A QA-only static-canvas guard recognizes `trajectory-qa=1` and `space-weather-qa=1` so unrelated continuously animated Mission/Entry canvases do not consume browser-regression resources during those dedicated harnesses.
- Production animation behavior remains unchanged when those QA query parameters are absent.
- No Trajectory Correction model/runtime logic was changed.
- No PSI model/runtime logic was changed.

### Performance notes

- Space Weather no longer owns a continuous requestAnimationFrame simulation loop.
- The new visualization renders on initialization, scenario/location changes, and queued resize events.
- This reduces unnecessary Mission-route animation work without weakening the visual explanation.
- The project remains static HTML/CSS/JavaScript with repository-local assets and zero required ongoing operating cost.

### Dedicated Phase H regression contract

The pure model/evidence regression verifies:

- physically meaningful `≥10 MeV` proton-flux axis
- NOAA S1–S5 threshold behavior
- exact threshold boundary behavior
- location-context independence from measured flux/classification
- `pfu` can never become crew dose
- Phase 5A NASA OMNI mission-window anchors remain intact
- Artemis II HERA monitoring context remains intact
- historical NAIRAS 3.0 interface is separated from current Version 4 documentation
- no MissionLab NAIRAS run or crew dosimetry is fabricated
- retired generic `solar activity 0–100` / `shielding 0–100` public controls do not return

The dedicated browser harness verifies:

- baseline render/state
- Below-S1 and S1–S5 presets
- threshold behavior
- location invariance
- dose boundary
- evidence anchors
- finite state
- canvas rendering
- phone horizontal-overflow containment

### Real Windows validation — FINAL PASS

The final Phase H installer completed successfully on the user's real Windows repository.

Pre-stage/static/model gates passed:

- JavaScript syntax validation
- Python compile validation
- public-experience validation
- strict UTF-8/public-text integrity
- HTML structural/accessibility hygiene
- Phase H pure-model/evidence regression
- protected Trajectory pure-model regression
- protected PSI pure-model regression
- celestial asset/provenance validation
- existing release validation

Phase H Space Weather browser regression:

- Chrome: PASS
- Edge: PASS
- physical baseline: PASS
- NOAA S1-S5 thresholds: PASS
- location invariance: PASS
- dose boundary: PASS
- evidence boundary: PASS
- canvas rendering: PASS
- mobile overflow: PASS
- finite outputs: PASS

Protected Trajectory Correction browser regression:

- Chrome: PASS
- Edge: PASS
- RTC2 baseline: PASS
- timing sensitivity: PASS
- RTN direction response: PASS
- RTC1/RTC2/RTC3 preset fidelity: PASS
- evidence boundaries: PASS
- canvas rendering: PASS
- mobile overflow: PASS
- finite outputs: PASS

Protected PSI browser regression:

- Chrome: PASS
- Edge: PASS
- cant direction: PASS
- spread divergence: PASS
- altitude response: PASS
- thrust proxy: PASS
- surface sensitivity: PASS
- hardware screening: PASS
- canvas rendering: PASS
- mobile overflow: PASS
- finite outputs: PASS

Protected Mission Explorer regression:

- Chrome: PASS
- Edge: PASS
- 8 viewport cases per browser
- max page-scroll delta: `0 px`
- max shell-height delta: `0 px`
- max stage-height delta: `0 px`
- max controls-top delta: `0 px`
- max client-width delta: `0 px`
- max control overflow: `0 px`

Protected Through Orion's Windows regression:

- Edge: PASS
- iPhone `390×844`: PASS
- iPhone `430×932`: PASS
- mobile landscape `844×390`: PASS
- desktop `1440×900`: PASS
- max scroll delta: `0 px`
- max viewer-top delta: `0 px`

Protected GNC deterministic AUTO/MANUAL regression:

- Chrome: PASS
- Edge: PASS
- browser-driven AUTO capture: `17 simulation seconds`
- cadence range: `16.7833 to 17 seconds`
- cadence spread: `0.21669999999999945 s`
- maximum deterministic disturbance recovery: `10 s`
- manual THC/RHC: PASS
- manual disturbance: PASS
- AUTO disturbance: PASS
- canvas render path: PASS

Protected Mission Control regression:

- Edge: PASS
- Chrome: PASS
- 6 viewport cases per browser
- 28 scenario/lens combinations per viewport
- 168 interactions per browser
- 336 total scenario/lens interactions
- 7 decision-model stages
- failures: `0`
- max horizontal overflow: `0 px`
- max layout delta: `0 px`
- max page-scroll delta: `0 px`
- max fixed-context content overflow: `0 px`
- minimum scenario/role touch target: `64 px`

Global responsive browser matrix:

- Edge: PASS
- Chrome: PASS
- 8 routes
- 6 viewports per browser
- 48 cases per browser
- 96 total cases
- failures: `0`
- max horizontal overflow: `0 px`

Exact staged-candidate rerun passed:

- public experience validation
- text integrity validation
- Phase H pure-model regression
- Phase H Chrome browser regression
- Phase H Edge browser regression
- exact deterministic tree verification before and after the focused rerun

The full protected browser matrix was intentionally not duplicated after staging, preserving the Phase G browser-resource-exhaustion safeguard.

### Git safety / rollback

The successful Windows installer:

- requires the exact repository path
- requires branch `phase-10-quality-recovery`
- requires starting HEAD `c283e104d92e9d587d50d0879d3965243a1dcd20`
- requires starting parent `ccf6ad0db89f9c68c551776e6a55556b23e334d1`
- requires starting tree `83bdbea2b99daeafc43ecfaf8a4a26273e1ccb71`
- fetches and verifies `origin/main = d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- treats the recovery remote-tracking ref as optional because the branch is intentionally local-only
- creates a timestamped `safety/phase-h-space-weather-*` branch before mutation
- validates the patch ZIP SHA-256
- validates the exact ZIP path set
- validates SHA-256 for every payload file
- refuses unexpected changed/staged paths
- stages only the 15 approved paths
- verifies the exact staged tree before commit
- creates a deterministic local commit only after validation
- verifies final HEAD/parent/tree and a clean worktree
- rolls back to the completed Phase G start on failure after mutation begins
- never runs `git push`

### Final Phase H Git state

- Final local commit: `85bce6ae711cc60bebd714a0a02f9734626ef665`
- Commit subject: `Redesign space weather lab`
- Parent: `c283e104d92e9d587d50d0879d3965243a1dcd20`
- Tree: `62bcb0f96d7b835d74d64165ece8d7a779c76f9f`
- Safety branch: `safety/phase-h-space-weather-20261014-111401219`
- Final worktree: clean
- Remote recovery branch: still unpublished
- Push performed: **NO**

### Delivery artifacts

- `A2_PhaseH_SpaceWeather_Patch_FINAL_v1.zip`
  - SHA-256: `34033eff9eef338b6ab0cde010290ac13669cdc83b946545fcd5d11572f80737`
- `Install_A2_PhaseH_SpaceWeather_v1.ps1`
  - SHA-256: `961fc41e985c9c333d5a8f7ffb850cab5892281a730b4f45a1a3d9fc702f7149`
- `A2_PhaseH_SpaceWeather_Delivery_20261014_v1.zip`
- `PHASE_H_LOCAL_VALIDATION_OUTPUT_FINAL.txt`
- `PHASE_H_PROJECT_LOG_APPEND.md`

### Current limitations / unknowns preserved

- No private Artemis II radiation telemetry is available here.
- No private/as-flown individual crew dosimetry is claimed.
- No Orion-specific effective shielding depth is established by the retained Phase 5B artifact.
- No MissionLab NAIRAS Version 3.0 or Version 4 run output is claimed.
- The NOAA S-scale is an external public reference, not an Artemis II flight-rule model.
- The scenario visualization is qualitative and does not perform particle transport or dose calculation.
- Exact NASA internal operational thresholds and protective-action criteria remain unknown/not public unless separately established by public evidence.

### Phase closure

Phase H — Space Weather Redesign is complete.

The final implementation:

- replaces generic normalized controls with physically meaningful public quantities
- resolves the NAIRAS 3.0 versus current Version 4 evidence distinction
- preserves the no-fabricated-dose boundary
- strengthens mission relevance for crew and electronics
- reduces unnecessary animation work
- preserves all Phase F/G protected systems
- passes dedicated Chrome and Edge regression
- passes the full protected browser matrix
- passes the global responsive matrix
- finishes in the exact intended local commit
- leaves the recovery branch unpublished
- performs no push

## Phase I — Entry / Descent / Recovery Upgrade

**Status:** COMPLETE — APPENDED ONLY AFTER REAL WINDOWS CHROME + EDGE RELEASE GATES PASS

### Objective

Upgrade the existing Entry / Descent / Recovery experience without rebuilding it from scratch or restoring the historical monolithic application.

The protected narrative remains:

`deep space → Earth approach → Entry Interface → atmospheric interaction → plasma/heating → guidance context → descent → parachutes → splashdown → recovery`

Phase I adds synchronized technical depth from the existing Phase 2 and Phase 4 reconstruction while keeping the story understandable before exposing engineering detail.

### Immutable starting state

- Repository: `C:\Users\prakh\Documents\a2-missionlab`
- Branch: `phase-10-quality-recovery`
- Starting HEAD: `7adc22831845095dc35f40c88832f73a55319d20`
- Starting parent: `85bce6ae711cc60bebd714a0a02f9734626ef665`
- Starting tree: `0c45d9c059159c0d07f58ea140e2398b49f04fbe`
- Starting subject: `Document completed Phase H`
- Protected Phase H implementation parent: `85bce6ae711cc60bebd714a0a02f9734626ef665`
- Protected `origin/main` baseline: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- The real recovery branch remains intentionally local-only unless the user explicitly publishes it.

### Repository archaeology / historical findings

- The public Entry experience remained on `mission.html#entry-lab` with its legacy runtime embedded inside `js/mission.js`.
- The existing public story was fundamentally correct but relied heavily on seven discrete states and educational visual interpolation.
- The strongest historical pre-split build around `718abc5e18403ba26eff3a68cfd208690ce6dbaf` did not contain a materially stronger Entry implementation worth restoring.
- The real technical opportunity was already present in the repository rather than in the historical UI:
  - high-rate flight-derived entry trajectory processing
  - M50-to-analysis-frame transformation work
  - WGS 84 geometry reconstruction
  - kinematic dynamics
  - NRLMSIS atmosphere
  - modeled Mach and rarefaction history
  - Sutton–Graves modeled convective heating
  - loft/rebound analysis
  - Artemis I / Artemis II heritage comparison
  - Phase 4 entry/descent/recovery evidence and recovery closure
- Phase I therefore reuses existing validated engineering products instead of inventing a new simplified entry model disconnected from the analysis.

### Exact implementation changed-file allowlist

The validated Phase I implementation commit changes exactly these 11 repository-relative paths:

1. `data/reference/artemis_ii_entry_phase_i.json` — added
2. `docs/ENTRY_RECOVERY_QA.md` — added
3. `entry.css` — added
4. `js/entry-model.js` — added
5. `js/entry.js` — added
6. `js/mission.js` — minimally modified
7. `mission.html` — upgraded Entry host
8. `scripts/validate_public_experience.py` — updated Phase I public contract
9. `scripts/validation/entry_regression.html` — added
10. `scripts/validation/validate_entry_model.js` — added
11. `scripts/validation/validate_entry_regression.py` — added

The later documentation-only commit changes only:

- `docs/ENGINEERING_LOG.md`

### Restored / redesigned capability

The Entry route now presents one synchronized continuous mission progression instead of snapping between a handful of public states.

The browser experience exposes:

- reconstructed WGS 84 altitude
- reconstructed Earth-relative speed
- modeled free-stream Mach
- modeled dynamic pressure within the protected Phase 2 window
- modeled Sutton–Graves external convective heat flux within the protected Phase 2 window
- a clearly labeled speed-squared energy-removal proxy
- the Artemis II loft/rebound geometry
- planned blackout context without invented exact blackout seconds
- NASA-reported public-minute communications reacquisition
- NASA-reported drogue/main public-minute milestones
- derived surface crossing bounded against the NASA public splashdown minute
- crew-recovery and spacecraft-recovery closure after splashdown

### Two-clock evidence architecture

Phase I makes two different time systems visible on purpose.

**Analysis time** is referenced to the first state in the 819-record high-rate source:

- source start: `2026-04-10T23:53:30.866000Z`
- source stop: `2026-04-11T00:07:08.841000Z`
- source duration: `817.975 s`

**NASA public event time** remains at the precision supported by the live-update evidence:

- Entry Interface: `23:53 UTC`
- communications reacquisition: `00:00 UTC`
- drogues: `00:03 UTC`
- mains: `00:04 UTC`
- splashdown: `00:07 UTC`

Public minute labels are not promoted to private second-level telemetry epochs.

The browser visual interpolates curated Phase 2 checkpoints for continuity. It does not pretend to replay every one of the 819 source records and is not an Orion onboard-navigation replay.

### High-rate source boundary

The protected source identity remains:

- format: `PROP_MAN 11.0`
- frame label: `M50`
- position units: `FT`
- velocity units: `FPS`
- time units: `SEC`
- records: `819`

The eighth raw numeric field remains unresolved and is not assigned a fabricated physical meaning.

### Aerothermal model integration

Phase I reuses the existing low-fidelity Sutton–Graves stagnation-point convective-heating correlation:

`q_dot = k * sqrt(rho / Rn) * V^3`

with the existing Phase 2 assumptions:

- modeled NRLMSIS 2.0 density
- reconstructed Earth-relative speed as free-stream velocity approximation
- Orion EFT-1 heritage/reference nose radius `6.035 m`
- cold-wall engineering correlation

Primary public interpretation remains limited to:

`Kn < 0.01 AND Mach >= 5`

Protected modeled peak:

- analysis `+85 s`
- altitude `61.878469 km`
- Earth-relative speed `9.984103 km/s`
- Mach `32.285653`
- modeled Sutton–Graves heat flux `109.641953 W/cm²`

Protected modeled integrated convective heat load:

- primary domain: `162.686370921 MJ/m²`
- stronger-continuum sensitivity: `159.150073328 MJ/m²`

No heat-flux or dynamic-pressure value is extrapolated in the public UI beyond the protected Phase 2 hypersonic interpretation window ending at the final Mach 5 crossing.

### Dynamic pressure versus heating lesson

Phase I explicitly surfaces a high-value Phase 2 relationship:

Early dominant modeled dynamic-pressure peak:

- analysis `+95 s`
- `12.798779 kPa`
- modeled Sutton–Graves heat flux `104.975953 W/cm²`

Later/global modeled dynamic-pressure peak:

- analysis `+431 s`
- `12.808389 kPa`
- modeled Sutton–Graves heat flux `7.596440 W/cm²`

The modeled pressure peaks differ by only about `0.075%`, while modeled heating differs by more than an order of magnitude because:

- dynamic pressure scales as `rho*V^2`
- Sutton–Graves heating scales approximately as `sqrt(rho)*V^3`

Selected intermediate dynamic-pressure support checkpoints used by the browser are deterministic algebraic re-expressions of the same existing Phase 2 Sutton–Graves inputs. They are not independent evidence or measured load telemetry.

### Artemis II loft / rebound

The public experience now makes the non-monotonic trajectory understandable instead of hiding it inside an engineering plot.

Protected landmarks:

- descent-to-climb: analysis `+112.294128 s`
  - altitude `60.350128 km`
  - speed `8.993741 km/s`
- rebound top / climb-to-descent: analysis `+239.647374 s`
  - altitude `64.211808 km`
  - speed `6.479165 km/s`
- duration: `127.353246 s`
- altitude recovery: `3.861680 km`
- speed loss during rebound: approximately `2.514577 km/s`
- stronger-continuum modeled heat-load fraction accumulated during this interval: `37.978839%`

Permanent terminology boundary:

`ARTEMIS II LOFT / REBOUND != ARTEMIS I SKIP ENTRY`

### Communications / blackout boundary

NASA publicly described a planned plasma communications blackout shortly after Entry Interface, expected to last about six minutes, and reported communications reacquisition at `00:00 UTC`.

Phase I deliberately does not invent exact blackout-start or blackout-end seconds.

The public product preserves:

- expected entry blackout != communications anomaly
- blackout event != measured plasma density
- public reacquisition minute != exact telemetry second

### Parachute architecture

The public experience surfaces the NASA-reported Orion parachute system architecture:

- 3 forward-bay-cover parachutes, approximately `7 ft` each
- 2 drogues, approximately `23 ft` each
- 3 pilot parachutes, approximately `11 ft` each
- 3 mains, approximately `116 ft` each

This is a system-architecture reference, not an exact individual as-flown canopy performance log.

### Splashdown / recovery closure

MissionLab's derived WGS 84 surface crossing remains:

- `2026-04-11T00:07:08.823676Z`
- latitude `32.340599 deg`
- longitude `-117.763095 deg`

It falls within NASA's public `00:07 UTC` splashdown minute.

The `8.824 s` offset from the beginning of that public minute remains a consistency diagnostic only. It is not an exact splashdown timing error.

No official numerical target-coordinate + official actual-coordinate pair is established in the curated evidence, therefore:

`OFFICIAL TARGET-TO-ACTUAL MISS DISTANCE = NOT PUBLICLY QUANTIFIABLE`

Recovery closure now remains visible beyond splashdown:

- recovery-team approach: `00:12 UTC`
- crew extracted: `01:34 UTC`
- crew aboard recovery ship: `01:58 UTC`
- Orion secured in well deck: `08:27 UTC`

Public-minute relationships:

- splashdown → crew aboard recovery ship: `111 min`
- splashdown → Orion secured in well deck: `500 min`

Crew recovery, spacecraft recovery, and postflight engineering closure remain separate concepts.

### Canonical evidence boundaries

Phase I preserves and exposes at minimum:

- NASA-reported public minute != exact second-level telemetry
- educational interpolation != measured trajectory state
- flight-derived trajectory reconstruction != private onboard navigation state
- M50 source data != EME2000/J2000 until validated transformation is applied
- unresolved PROP_MAN eighth field != invented physical quantity
- modeled atmosphere != measured local atmospheric telemetry
- modeled dynamic pressure != measured aerodynamic-load telemetry
- modeled Sutton–Graves heating != measured TPS telemetry
- modeled heating != TPS material damage
- modeled heating != crew thermal exposure
- kinematic deceleration / g0-equivalent != crew sensed g-load
- plasma blackout public event != measured plasma density
- expected entry blackout != communications anomaly
- Artemis II loft/rebound != Artemis I skip entry
- parachute architecture != exact as-flown individual-canopy performance log
- derived surface crossing != official NASA actual splashdown coordinate
- derived surface crossing != official NASA target coordinate
- public-minute consistency != exact timing error
- derived terminal state != official landing-targeting accuracy
- crew recovery != spacecraft recovery != postflight engineering closure

### Product architecture / protected-system integration

Phase I retains the correct Phase 10 multi-page architecture.

Entry remains on the Mission route, but the new code is isolated into:

- `js/entry-model.js` — deterministic continuous state / evidence model
- `js/entry.js` — interaction and canvas runtime
- `entry.css` — dedicated responsive visual system
- `data/reference/artemis_ii_entry_phase_i.json` — explicit Phase I evidence/model manifest
- `docs/ENTRY_RECOVERY_QA.md` — Phase I model/evidence/test contract

The legacy Entry runtime inside `js/mission.js` is preserved but bypassed only when the Phase I root marker is present. This avoids an uncontrolled rewrite of the shared Mission runtime.

No PSI, Trajectory Correction, Space Weather, GNC, Windows, Mission Control, or Mission Explorer production model was rewritten.

### Performance notes

- Phase I does not add a perpetual Entry animation loop.
- Continuous animation runs only after the visitor explicitly presses Play.
- A paused Entry view redraws on state changes and responsive geometry changes.
- `entry-qa=1` joins the existing static Mission QA guard so unrelated Mission animation does not consume dedicated regression resources.
- The project remains static HTML/CSS/JavaScript with zero required ongoing operating cost.

### Validation — static / evidence / analytical

The release installer requires all of the following before commit:

- `git diff --check`
- JavaScript syntax validation
- Python compile validation
- strict JSON parse validation
- final public-experience validation
- public text / markup integrity validation
- Phase I pure model/evidence regression
- protected Trajectory Correction pure-model regression
- protected PSI pure-model regression
- celestial asset/provenance validation
- existing release validation
- existing Artemis entry-profile heritage validation
- existing Phase 4 entry/descent/recovery evidence validation
- existing high-rate entry trajectory validation
- entry frame-transform validation
- entry geometry validation
- entry dynamics validation
- entry event-correlation validation
- entry atmosphere validation
- entry Mach validation
- entry rarefaction validation
- entry heating validation
- Artemis I / Artemis II entry-profile comparison validation
- loft/rebound heating-history validation
- entry-to-recovery operational-timeline validation
- splashdown-accuracy / recovery-closure validation

The exact staged Phase I candidate reruns the critical public/evidence/model checks plus the dedicated Entry browser gate before the deterministic implementation commit is created.

### Real Windows browser / responsive release gate

This section is appended only after the installer has required and passed both Chrome and Edge on the user's real Windows repository.

Dedicated Phase I Entry regression:

- Chrome: PASS
- Edge: PASS
- continuous reconstruction checkpoints: PASS
- loft/rebound behavior and terminology: PASS
- exact loft/rebound geometry validated from protected model landmarks; rounded gauge text is tested only as UI presentation: PASS
- heating-versus-dynamic-pressure relationship: PASS
- blackout evidence boundary: PASS
- recovery closure: PASS
- event-rail interaction: PASS
- canvas rendering: PASS
- finite outputs: PASS
- phone portrait `390×844`: PASS
- phone portrait `430×932`: PASS
- mobile landscape `844×390`: PASS
- desktop `1440×900`: PASS
- horizontal overflow: `0 px` within the tested Phase I viewports

Protected release gates are also required to pass in Chrome and Edge before commit:

- Trajectory Correction
- PSI
- Mission Explorer
- Through Orion's Windows
- deterministic GNC AUTO / MANUAL
- Mission Control
- Space Weather
- global responsive browser QA

The full protected browser matrix runs once before staging. After the exact staged tree is verified, only the Phase I-critical Entry browser regression is repeated, preserving the Phase G/H browser-resource safeguard rather than needlessly duplicating the full matrix.

### Git safety / rollback

The Phase I release installer:

- requires the exact repository path
- requires branch `phase-10-quality-recovery`
- requires starting HEAD `7adc22831845095dc35f40c88832f73a55319d20`
- requires starting parent `85bce6ae711cc60bebd714a0a02f9734626ef665`
- requires starting tree `0c45d9c059159c0d07f58ea140e2398b49f04fbe`
- fetches and verifies `origin/main = d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- accepts the recovery remote-tracking ref as absent because the branch is intentionally local-only
- creates a timestamped `safety/phase-i-entry-*` branch before mutation
- validates the patch ZIP SHA-256
- validates the exact patch path set
- validates SHA-256 for every payload file
- rejects unexpected changed or staged paths
- stages only the 11 approved implementation paths
- verifies the exact staged implementation tree
- creates a deterministic local implementation commit only after all release gates pass
- appends this complete Phase I record to `docs/ENGINEERING_LOG.md` without rewriting prior log content
- creates a separate documentation-only local commit with the validated implementation commit as its parent
- verifies final HEAD / parent / tree and a clean worktree
- rolls back to the immutable completed Phase H documentation start on failure after mutation begins
- never runs `git push`

### Final Phase I implementation Git state

- Implementation commit: `31f37ee0c6ea27775d8621de29b6f0d31d618564`
- Commit subject: `Upgrade entry descent and recovery`
- Parent: `7adc22831845095dc35f40c88832f73a55319d20`
- Implementation tree: `be114211d78e458e9f6779db13a310041e09eea0`
- Documentation commit: separate local commit created only after the successful release gates and log append
- Final worktree after documentation commit: clean
- Remote recovery branch: still unpublished
- Push performed: **NO**

### Current limitations / unknowns preserved

- The 819-state source is flight-derived public/repository evidence, not private Orion onboard-navigation telemetry.
- The exact operational meaning of `PROP_MAN 11.0` is not asserted beyond what authoritative evidence establishes.
- The eighth raw numeric field remains unresolved.
- Exact blackout-start and blackout-end seconds are not public in the curated evidence.
- The atmosphere, Mach, dynamic pressure, and Sutton–Graves heating products remain models/reconstructions rather than direct vehicle telemetry.
- Sutton–Graves omits radiative heating, finite wall temperature, Avcoat ablation/pyrolysis, blowing, recession, catalytic-wall effects, and detailed shock-layer nonequilibrium.
- The public reconstruction does not provide private guidance commands, lift-vector history, navigation covariance, or NASA entry-targeting products.
- The parachute architecture is not an individual canopy performance log.
- The derived surface crossing is not an official NASA actual coordinate or target coordinate.
- Official target-to-actual landing miss distance remains not publicly quantifiable.
- Recovery public times remain minute-resolution reports rather than exact operational telemetry epochs.

### Phase closure

Phase I — Entry / Descent / Recovery Upgrade is complete once the release installer reaches the deterministic local implementation commit and documentation-only commit.

The completed phase:

- preserves the correct existing Entry narrative
- replaces discrete-state snapping with a technically bounded continuous reconstruction view
- surfaces the real Phase 2 loft/rebound and aerothermal relationships
- makes dynamic pressure versus heating understandable visually
- preserves public-minute precision for operational events
- extends the story through crew and spacecraft recovery
- keeps modeled heating explicitly separate from measured TPS telemetry
- keeps Artemis II loft/rebound explicitly separate from Artemis I skip entry
- preserves all completed Phase F/G/H protected systems
- remains zero-cost and static
- ends in local commits only
- leaves the recovery branch unpublished
- performs no push

### Next phase

Proceed to **Phase J — Mission Explorer / Through Orion's Windows / GNC / Mission Control protected subjective polish + QA contract cleanup** only after the successful Phase I installer output is retained.

## Phase J — Mission Explorer / Windows / GNC / Mission Control Protected Polish + QA Contract Cleanup

**Status:** COMPLETE — APPENDED ONLY AFTER REAL WINDOWS CHROME + EDGE RELEASE GATES PASS

### Objective

Perform the protected subjective-quality pass on Mission Explorer, Through Orion's Windows, GNC, and Mission Control without rewriting already strong systems, weakening evidence discipline, or destabilizing the Phase F/G/H/I product contracts.

Phase J follows the repository-first rule: inspect the current protected experiences and the strongest historical pre-split build, identify actual current weaknesses, and mutate only where there is a material clarity or QA benefit.

### Immutable starting state

- Repository: `C:\Users\prakh\Documents\a2-missionlab`
- Branch: `phase-10-quality-recovery`
- Starting HEAD: `7963a9a237a288631789242072816bc16b9588e2`
- Starting parent: `31f37ee0c6ea27775d8621de29b6f0d31d618564`
- Starting tree: `0c8d16542a7cc3f72196ba42e95138afb5083db4`
- Starting subject: `Document completed Phase I`
- Protected `origin/main`: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- Recovery branch remains intentionally local-only / unpublished.

### Design archaeology / current-state findings

The strong historical pre-split build around `718abc5e18403ba26eff3a68cfd208690ce6dbaf` was inspected only for product archaeology.

The current multi-page implementation remains materially stronger and is preserved.

Current inspection found:

- Mission Explorer already preserves stable phase progression, mission clock, geometry, milestone navigation, responsive containment, and zero-scroll-jump behavior. No production mutation was justified.
- Through Orion's Windows already presents 25 curated mission/science moments with direct on-image navigation, filmstrip navigation, keyboard/touch behavior, provenance, geometry context, zoom/lightbox behavior, preload behavior, stable viewer geometry, and evidence-aware captions. No production mutation was justified.
- Mission Control already contains the acronym/discipline onboarding and operational-reasoning structure that the historical complaint requested. The product itself uses approximately `64 px` or larger scenario/discipline targets, but its regression still enforced only `44 px`; that mismatch was a real QA defect.
- GNC retained AUTO, MANUAL, deterministic fixed-step behavior, disturbance injection, THC, RHC, disturbance recovery, and the protected simulator behavior, but the current CSS rendered the inter-block closed-loop connector as a literal `?` rather than an arrow. This was a real visual/diagram defect rather than a historical-only complaint.
- GNC explanatory wording described the loop correctly in broad terms but did not make the desired-state → estimated-state → error → command → response → feedback relationship as explicit as the Phase J product objective requires.

Phase J therefore deliberately avoids a broad visual rewrite.

### Exact implementation changed-file allowlist

The Phase J implementation commit changes exactly these 7 paths:

1. `docs/PHASE_D_MISSION_CONTROL_QA.md`
2. `gnc.css`
3. `gnc.html`
4. `js/gnc.js`
5. `scripts/validate_public_experience.py`
6. `scripts/validation/mission_control_regression.html`
7. `scripts/validation/validate_mission_control_regression.py`

The documentation-only closure commit changes only:

- `docs/ENGINEERING_LOG.md`

### GNC diagram / explanatory polish

The protected GNC simulator behavior is unchanged.

Phase J fixes the diagram connector by replacing the literal mystery `?` CSS content with an explicit Unicode right-arrow escape:

`content: "\\2192";`

This avoids source-encoding ambiguity while restoring intentional direction between the six closed-loop blocks.

The public explanation now states the causal loop explicitly:

`desired state → estimated state → error → guidance / control → command → spacecraft response → feedback`

The six interactive architecture blocks are clarified as:

- SENSE — measure motion
- ESTIMATE — estimated state
- GUIDE — compare to target
- CONTROL — error to command
- FIRE — spacecraft response
- VERIFY — close feedback loop

The corresponding progressive-disclosure explanations in `js/gnc.js` now make the error, command, response, and feedback relationships explicit while preserving the existing evidence boundary around private Orion navigation filters, control laws, gains, allocation logic, and individual thruster histories.

No deterministic physics constant, fixed-step behavior, AUTO timing target, manual THC/RHC behavior, disturbance behavior, canvas model, or protected GNC evidence claim is changed.

### Mission Control QA contract cleanup

Mission Control production CSS already protects `64 px` minimum discipline-lens targets and larger scenario targets.

The dedicated browser regression previously failed only below `44 px`, which under-enforced the real product contract.

Phase J strengthens both layers of that gate:

- browser harness: `minimumTouch < 64` is now a failure
- Python release gate: reported minimum touch target below `64 px` is now a failure
- QA documentation now records the protected `64 px` contract

No Mission Control scenario, discipline lens, seven-stage decision model, narrative/canvas separation, state model, evidence language, or runtime behavior is changed.

### Static contract hardening

`scripts/validate_public_experience.py` now protects the Phase J corrections so they cannot silently regress:

- GNC public copy must retain the desired-state / estimated-state / error / feedback concepts
- GNC CSS must retain the explicit right-arrow escape
- the mystery `?` connector is explicitly forbidden
- Mission Control's browser regression must enforce `64 px`
- Mission Control's Python gate must enforce and report `64 px`

### Evidence / terminology boundaries preserved

Phase J does not alter the canonical evidence taxonomy:

- NASA REPORTED
- MISSIONLAB DERIVED
- MODELED
- INFERRED
- UNKNOWN / NOT PUBLIC

The following protected non-equivalences remain unchanged:

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

GNC continues to state that public evidence establishes architecture, not private filter internals or exact thruster histories.

Mission Control continues to state that `COMM` is MissionLab shorthand and `ENG SUPPORT` is a synthesis lens rather than asserted Artemis II front-room console nomenclature.

### Validation — static / syntax / analytical

Before any commit, the release installer requires:

- exact branch / HEAD / parent / tree verification
- clean worktree verification
- fetched and verified `origin/main`
- exact patch ZIP SHA-256 verification
- exact changed-path allowlist verification
- SHA-256 verification for every payload file
- `git diff --check`
- JavaScript syntax checks for protected public runtimes
- Python compile checks for modified validation scripts
- final public-experience validation
- public text / markup integrity validation
- Trajectory Correction pure-model regression
- PSI pure-model regression
- Phase I Entry pure-model/evidence regression
- celestial asset/provenance validation
- existing release validation

The exact staged candidate reruns the Phase J-critical public/text checks plus the GNC and Mission Control dedicated browser gates before the deterministic implementation commit is created.

### Real Windows browser / responsive release gate

This section is appended only after the release installer requires and passes both Chrome and Edge on the user's real Windows repository.

Protected dedicated regressions required to pass:

- Mission Explorer — Chrome + Edge
- Through Orion's Windows — Chrome + Edge
- deterministic GNC AUTO / MANUAL — Chrome + Edge
- Mission Control — Chrome + Edge
- PSI — Chrome + Edge
- Trajectory Correction — Chrome + Edge
- Space Weather — Chrome + Edge
- Entry / Descent / Recovery — Chrome + Edge
- global responsive browser QA — Chrome + Edge

Phase J-specific browser expectations:

- GNC AUTO capture remains within the protected `15–20 s` simulation-time window
- deterministic cadence spread remains within the protected tolerance
- manual THC/RHC remains functional
- manual and AUTO disturbance paths remain functional
- GNC canvas remains finite and responsive
- Mission Control still exercises all 4 scenarios × 7 discipline lenses
- all 7 decision-model stages remain present
- Mission Control horizontal overflow remains within the protected tolerance
- Mission Control scenario/lens-driven layout and page-scroll drift remain within the protected tolerance
- fixed context panels remain unclipped
- minimum observed Mission Control scenario/discipline target is now required to be at least `64 px`
- global tested horizontal overflow remains within the protected tolerance

The full protected browser matrix runs once before staging. After the exact staged tree is verified, only the Phase J-critical GNC and Mission Control browser regressions are repeated, preserving the existing browser-resource safeguard instead of duplicating the entire matrix.

### Responsive / interaction preservation

Phase J intentionally leaves the Mission Explorer and Windows production implementations untouched because current repository evidence shows their earlier problems have already been solved.

Protected responsive behavior remains:

- Mission Explorer stable geometry and zero-scroll-jump interaction contract
- Windows stable viewer geometry, direct arrows, keyboard/touch navigation, lightbox/zoom, preload behavior, and no-scroll-jump contract
- GNC responsive canvas and deterministic AUTO/MANUAL behavior
- Mission Control no-overflow, no-layout-drift, no-page-scroll-drift, fixed-context containment, and large-target contract

No new global CSS layer, uncontrolled selector churn, route-wide refactor, or architecture merge is introduced.

### Performance / architecture notes

- No new animation loop is added.
- No new network request is added.
- No new image or font dependency is added.
- No backend is added.
- No paid service is added.
- Zero-cost static HTML/CSS/JavaScript architecture remains intact.
- Mission Explorer and Windows production code remain byte-for-byte unchanged by the implementation commit.
- GNC physics/integration behavior remains unchanged; the mutation is explanatory/presentational only.
- Mission Control runtime behavior remains unchanged; the mutation is test-contract/documentation only.

### Git safety / rollback

The Phase J release installer:

- requires the exact repository path
- requires branch `phase-10-quality-recovery`
- requires starting HEAD `7963a9a237a288631789242072816bc16b9588e2`
- requires starting parent `31f37ee0c6ea27775d8621de29b6f0d31d618564`
- requires starting tree `0c8d16542a7cc3f72196ba42e95138afb5083db4`
- fetches and verifies `origin/main = d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- creates a timestamped `safety/phase-j-polish-*` branch before mutation
- validates the patch ZIP and every payload hash
- rejects unexpected changed or staged paths
- stages only the 7 approved implementation paths
- verifies the exact staged implementation tree
- creates a deterministic local implementation commit only after all release gates pass
- appends this complete Phase J record to `docs/ENGINEERING_LOG.md` without rewriting prior log content
- creates a separate documentation-only local commit with the validated implementation commit as its parent
- verifies final HEAD / parent / tree and a clean worktree
- rolls back to the immutable completed Phase I documentation start on any failure after mutation begins
- never runs `git push`

### Final Phase J implementation Git state

- Implementation commit: `e259e311a7c83396c5b8629d2a6d1831e3ef9b25`
- Commit subject: `Polish GNC clarity and Mission Control QA`
- Parent: `7963a9a237a288631789242072816bc16b9588e2`
- Implementation tree: `5d5969a56120e2e91b93e80e435a24c2e29768b9`
- Documentation commit: separate local commit created only after successful release gates and engineering-log append
- Final worktree after documentation commit: clean
- Remote recovery branch: still unpublished
- Push performed: **NO**

### Current limitations / manual release work preserved

- Automated Phase J release coverage is Chrome and Edge on the user's real Windows machine; it does not claim Safari or Firefox coverage.
- Real-device iPhone Safari, Android Chrome, and tablet subjective visual inspection remain part of later final-device release QA.
- Phase J does not attempt a full typography, accessibility, performance, metadata, or publication redesign; those remain governed by later master-prompt phases.
- Subjective polish does not fabricate private Mission Control displays, private flight-control data, proprietary GNC internals, or unpublished mission information.

### Phase closure

Phase J is complete only if the release installer reaches both the deterministic local implementation commit and the separate documentation-only commit after all required static, analytical, Chrome, Edge, and responsive gates pass.

The completed phase:

- preserves Mission Explorer rather than rewriting a solved interaction system
- preserves Through Orion's Windows rather than destabilizing a solved 25-moment mission/science viewer
- fixes the real GNC connector defect
- makes the GNC closed-loop cause/effect relationship easier to understand in seconds
- strengthens Mission Control QA to the real `64 px` product contract
- adds static guards so both Phase J fixes cannot silently regress
- preserves all Phase F/G/H/I product and evidence contracts
- remains zero-cost and static
- ends in local commits only
- leaves the recovery branch unpublished
- performs no push

### Next phase

Proceed to **Phase K — Technical Report + Mission Library** only after the successful Phase J installer output is retained.

## Phase K — Technical Report + Mission Library Publication Upgrade

**Status:** COMPLETE — APPENDED ONLY AFTER REAL WINDOWS CHROME + EDGE RELEASE GATES PASS

### Objective

Upgrade the two publication surfaces that turn A2 MissionLab from a strong interactive engineering project into a serious reviewable technical body of work:

- Technical Report
- Mission Library

Phase K follows the governing publication goals without changing the underlying Artemis II reconstruction, weakening evidence boundaries, or rewriting protected Phase F/G/H/I/J systems.

The publication design target is:

`QUESTION → EXPLANATION → EVIDENCE → SOURCE`

for knowledge discovery, and a formal engineering-report structure for technical review.

### Immutable starting state

- Repository: `C:\Users\prakh\Documents\a2-missionlab`
- Branch: `phase-10-quality-recovery`
- Starting HEAD: `c7758aa415928467da0ebb6e48c276c1082be566`
- Starting subject: `Document completed Phase J`
- Starting parent: `e259e311a7c83396c5b8629d2a6d1831e3ef9b25`
- Starting tree: `6778e63c19c598212457823643f01e5e757ced1e`
- Protected `origin/main`: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- Recovery branch remains local-only / unpublished

### Repository-first audit findings

The Technical Report already contained substantial engineering depth:

- 25 major technical sections plus source ledger
- 13 engineering figures
- 3 technical tables
- public-data methodology
- OEM / SPICE / communications / GNC / maneuver / entry / heating / ECLSS / radiation / lunar-science / Mission Control content
- evidence taxonomy
- reproducibility / validation
- selected quantitative results
- limitations

The primary weakness was publication architecture, not missing engineering substance. It still behaved as one long web article and lacked a compact executive review layer, formal revision identification, indexed/numbered publication apparatus, and dedicated print/PDF presentation. It also still loaded obsolete top-level `app.js`.

The Mission Library already contained 28 deep technical articles. The weakness was information architecture: one search box fed a flat index and every matching full article was rendered into the page simultaneously. Categories, result counts, question-led discovery, related concepts, and focused progressive disclosure were missing.

Phase K therefore preserves the technical content and changes the publication / knowledge-system architecture.

### Phase K implementation changed-path allowlist

The implementation commit changes exactly these 9 paths:

1. `docs/PHASE_K_PUBLICATION_QA.md` — added
2. `library.css` — added
3. `library.html` — modified
4. `library.js` — modified
5. `report.css` — added
6. `technical-report.html` — modified
7. `scripts/validation/phase_k_publication_regression.html` — added
8. `scripts/validation/validate_phase_k_publication.py` — added
9. `scripts/validation/validate_phase_k_regression.py` — added

The later documentation-only commit changes only:

- `docs/ENGINEERING_LOG.md`

No Mission Explorer, Windows, GNC, Mission Control, PSI, Trajectory Correction, Space Weather, or Entry production runtime is modified.

### Technical Report publication upgrade

The Technical Report now includes a formal publication layer without replacing its engineering substance.

Added / strengthened:

- dedicated `report.css`
- publication revision block
- exact study-baseline commit identification
- explicit public-evidence policy
- zero-cost delivery architecture identification
- executive summary
- compact publication-scope metrics
- cross-links from executive summary to methods, validation, and results
- indexed figure/table navigation
- stable anchors for all 13 engineering figures
- numbered figure captions
- stable anchors and formal captions for all 3 tables
- numbered Sutton–Graves equation
- ordered references / artifact ledger
- print/PDF-specific CSS with `@page` and print media rules
- stable repository evidence links pinned to the immutable Phase J study baseline instead of the obsolete `public-experience-v3` branch
- removal of obsolete top-level `app.js` from the report route

The report preserves all existing major technical sections and retains the quantitative reconstruction ledger.

### Publication scope metrics

The executive publication layer exposes repository-validated scope from the tracked publication/release manifests:

- 25 indexed datasets
- 81 normalized public sources
- 24 mission events
- 10 decision threads
- 6 postflight records
- 146 searchable records
- 8 deterministic analyst tools
- 8 answer routes

These metrics are repository publication metrics, not hiring/marketing estimates.

### Current NASA campaign-context verification

The dated future-Artemis paragraph was checked against current NASA public pages on 14 October 2026.

The Phase K report preserves the time-bounded statement that:

- Artemis III is scheduled as a 2027 low-Earth-orbit demonstration mission for critical future landing systems
- NASA continues to target early 2028 for Artemis IV as the first Artemis lunar landing

The report uses current NASA mission/science landing pages and keeps the statement explicitly dated because campaign architecture can change.

Phase K does not reinterpret future-campaign plans as Artemis II flight events.

### Mission Library information architecture

The Mission Library still contains all 28 technical deep dives, but the browsing model is now question-led and progressively disclosed.

Canonical Phase K categories:

1. Flight Dynamics
2. Vehicle & GNC
3. Mission Operations
4. Entry & Recovery
5. Environment & Radiation
6. Lunar Science
7. Data & Software
8. Evidence & Methods
9. Future Artemis

The interface adds:

- `All` + 9 category controls
- live result count
- lightweight question/result cards
- curated engineering question for every deep dive
- search across question, title, domain, method, interpretation, limitations, and capabilities
- one focused full article at a time
- direct deep-link behavior through topic hashes
- explicit four-stage knowledge path:
  - Question
  - Explanation
  - Evidence
  - Source
- related-question discovery
- stable repository-evidence links pinned to the Phase J study baseline
- lazy loading for deep-dive engineering figures
- dedicated `library.css`
- responsive browse/read states

The result is a knowledge system rather than a 28-article document dump.

### Evidence discipline preserved

Phase K does not change the canonical evidence taxonomy:

- NASA REPORTED
- MISSIONLAB DERIVED
- MODELED
- INFERRED
- UNKNOWN / NOT PUBLIC

Permanent boundaries preserved include:

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

Publication polish does not upgrade uncertain evidence into stronger claims.

### Dedicated Phase K static validator

Added:

`scripts/validation/validate_phase_k_publication.py`

It requires at minimum:

- dedicated report/library stylesheets
- executive summary
- exact Phase J study-baseline identity
- 13 stable report figure anchors
- 3 numbered/anchored tables
- numbered Sutton–Graves equation
- formal ordered reference/artifact ledger
- explicit print/PDF CSS
- obsolete report `app.js` absent
- obsolete `public-experience-v3` repository links absent from Phase K publication surfaces
- current NASA science / Artemis IV landing-page paths
- all report figure assets resolvable locally
- all 28 Library deep dives retained
- curated question for every deep dive
- canonical category for every deep dive
- focused one-article rendering
- explicit Question → Explanation → Evidence → Source path
- related-topic discovery
- lazy-loaded deep-dive figures

### Phase K v1 failed-attempt forensic history — not current production state

The first Phase K installer correctly passed the existing protected static, evidence, pure-model, release, Mission Explorer, Windows, GNC, Mission Control, PSI, Trajectory Correction, Space Weather, Entry, and global responsive gates, but the new dedicated Phase K browser regression failed identically in Chrome and Edge at one Library search assertion.

Observed behavior at all four representative viewports in both browsers:

- query: `Sutton`
- actual lightweight Library result cards: `2`
- v1 regression expectation: `1`
- every other Phase K browser assertion: PASS
- horizontal overflow: `0 px`
- initial Library cards: `28`
- focused deep-dive article count: `1`
- report figures: `13`
- report tables: `3`

The browser gate retried once and reproduced the same deterministic failure. The installer then correctly rolled the repository back to immutable Phase J documentation start `c7758aa415928467da0ebb6e48c276c1082be566`, removed all Phase K mutation, returned the worktree clean, retained safety branch `safety/phase-k-publication-20261014-204738324`, and performed no push.

Root cause was in the **new regression expectation**, not the Library search implementation. Phase K search deliberately indexes title, curated question, domain, explanation, method, interpretation, limitations, and capability text. The query `Sutton` therefore correctly matches both:

1. `convective-heating` — the Sutton–Graves convective-heating deep dive
2. `thermal-protection` — whose method explicitly explains the boundary between a Sutton–Graves external-flow estimate and Avcoat material response

Requiring only one result would contradict the intended full-text knowledge-system search semantics.

Phase K v2 therefore strengthens the regression contract instead of weakening the product: `Sutton` must return exactly those two topic IDs. The QA contract records the same invariant. No Library production search logic was changed to make the test pass.

During v2 release reconstruction, an additional **packaging-only deterministic-target defect** was found before delivery: the earlier sandbox used to calculate the v1 expected implementation tree still had a staged `docs/ENGINEERING_LOG.md` index entry from local release preparation. That contaminated the v1 precomputed tree/commit target even though `docs/ENGINEERING_LOG.md` was not in the 9-file implementation allowlist. The user’s failed v1 run never reached staged-tree verification, so this defect never mutated or committed anything in the real repository.

V2 discards those contaminated targets. Its implementation tree and commit are recomputed from a fresh clone of exact Phase J HEAD plus only the exact 9-file patch, and the documentation tree is computed only after a separate append of this log section.

This preserves the project rule established in earlier phases: inspect the first real failure, fix the actual defect, and do not distort correct engineering behavior merely to satisfy a test.

### Dedicated Phase K Chrome / Edge browser regression

Added:

`scripts/validation/phase_k_publication_regression.html`

and:

`scripts/validation/validate_phase_k_regression.py`

Required release browsers:

- Chrome
- Edge

Representative Phase K viewports per browser:

- `390 × 844`
- `844 × 390`
- `768 × 1024`
- `1440 × 900`

The dedicated regression verifies:

- 28 initial Library cards
- 10 category controls (`All` + 9 categories)
- live result count
- Entry & Recovery category filtering
- Sutton search coverage requiring exactly `convective-heating` and `thermal-protection`
- only one focused full article rendered
- four-stage knowledge path
- curated technical question rendering
- related-question discovery
- Library horizontal containment
- four-block report publication metadata
- report executive summary
- all 13 indexed report figures
- all 3 numbered report tables
- obsolete report `app.js` absent
- report horizontal containment

The dedicated harness exercises 64 assertions per browser across the four representative viewports.

### Protected validation matrix

Before Phase K can commit, the release installer requires the existing protected regressions to remain green:

- Mission Explorer — Chrome + Edge
- Through Orion's Windows — Chrome + Edge
- GNC deterministic AUTO/MANUAL — Chrome + Edge
- Mission Control — Chrome + Edge
- PSI — Chrome + Edge
- Trajectory Correction — Chrome + Edge
- Space Weather — Chrome + Edge
- Entry / Descent / Recovery — Chrome + Edge
- global responsive browser QA — Chrome + Edge
- dedicated Phase K publication regression — Chrome + Edge

The full protected browser matrix runs once before staging. After exact staged-tree verification, only the Phase K static publication validator and dedicated Phase K browser regression are repeated, avoiding unnecessary duplicate browser load while still validating the exact candidate tree.

### Non-browser validation

The Phase K candidate also requires:

- JavaScript syntax validation
- Python bytecode compilation for publication validators
- `scripts/validate_public_experience.py`
- `scripts/validation/validate_text_integrity.py`
- `scripts/validation/validate_phase_k_publication.py`
- Trajectory Correction pure-model regression
- PSI pure-model regression
- Space Weather pure-model regression
- Entry pure-model/evidence regression
- celestial rendering asset validation
- final release validation
- `git diff --check`

### Performance / architecture effects

Phase K is intentionally bounded.

- No backend added.
- No database added.
- No API dependency added.
- No paid inference added.
- No analytics dependency added.
- No font dependency added.
- No new network request required for core interaction.
- No protected simulation animation loop changed.
- Technical Report drops an obsolete JavaScript runtime dependency.
- Mission Library no longer renders every full matching deep dive simultaneously.
- Library engineering figures load lazily when a selected article is rendered.

Total required ongoing operating cost remains:

`$0.00`

### Accessibility / responsive behavior

Phase K preserves semantic headings and adds:

- button-based category filters
- `aria-pressed` state
- live result-count announcement
- direct hash navigation
- focused single-article reading
- responsive category controls
- responsive browse cards
- responsive knowledge-path layout
- report table overflow containment inherited from the protected responsive layer
- report print presentation independent of screen-only navigation

The dedicated browser regression checks both Library and Report horizontal containment at phone portrait, phone landscape, tablet, and desktop widths.

### Git safety / rollback

The Phase K release installer:

- requires exact branch `phase-10-quality-recovery`
- requires exact starting HEAD `c7758aa415928467da0ebb6e48c276c1082be566`
- requires exact starting parent `e259e311a7c83396c5b8629d2a6d1831e3ef9b25`
- requires exact starting tree `6778e63c19c598212457823643f01e5e757ced1e`
- verifies protected `origin/main = d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- requires the recovery branch to remain unpublished
- creates a timestamped `safety/phase-k-publication-*` branch before mutation
- validates patch ZIP hash, exact allowlist, and each payload SHA-256
- applies only the 9 approved implementation paths
- runs static, evidence, pure-model, release, protected-browser, and Phase K-specific gates
- stages only the exact allowlist
- verifies the exact candidate tree
- repeats Phase K-critical validation against the exact staged tree
- creates a deterministic local implementation commit
- appends this complete Phase K section without modifying prior engineering-log content
- creates a separate documentation-only local commit
- verifies final HEAD / parent / tree and a clean worktree
- rolls production mutation back to the immutable Phase J documentation start if a required gate fails
- never runs `git push`

### Final Phase K implementation Git state

- Implementation commit: `e39a9fab0c3f62a9aa35da631ec73357e300d434`
- Commit subject: `Upgrade technical publication and mission library`
- Parent: `c7758aa415928467da0ebb6e48c276c1082be566`
- Implementation tree: `560f3d9dbb055e8013bda197998d793437f057a0`
- Documentation commit: separate local commit created only after successful release gates and engineering-log append
- Final worktree after documentation commit: clean
- Remote recovery branch: unpublished
- Push performed: **NO**

### Phase closure

Phase K is complete only after the real Windows release installer passes all required gates and reaches both deterministic local commits.

The completed phase turns:

- the Technical Report into a reviewable engineering publication with formal revision, executive, figure/table/equation, reference, and print structure
- the Mission Library into a categorized, question-led, progressively disclosed technical knowledge system

while preserving the existing mission reconstruction, zero-cost architecture, public-evidence discipline, and all protected F–J experience contracts.

### Next phase

Proceed to **Phase L — Typography + Visual Quality** only after the successful Phase K installer output is retained.

## Phase L — Typography + Visual Quality

**Status:** COMPLETE — APPENDED ONLY AFTER REAL WINDOWS CHROME + EDGE RELEASE GATES PASS

### Objective

Stabilize A2 MissionLab typography across platforms and improve visual hierarchy without repainting the product, weakening evidence discipline, changing simulation behavior, or collapsing the distinct identities of the public routes.

Phase L addresses the typography and visual-quality requirements from the governing project specification:

- remove the unresolved `Inter` dependency
- use a deliberate zero-cost font architecture
- normalize fragile display tracking and line height
- improve heading hierarchy across the public experience
- preserve readable technical metadata, equations, and numerical data
- retain distinct route visual identities
- keep the zero-budget static architecture

### Immutable starting state

- Repository: `C:\Users\prakh\Documents\a2-missionlab`
- Branch: `phase-10-quality-recovery`
- Starting HEAD: `01b7e20101c12604ccd9934488bcf589a0ba16c4`
- Starting subject: `Document completed Phase K`
- Starting parent: `e39a9fab0c3f62a9aa35da631ec73357e300d434`
- Starting tree: `1291c776161b96016f3628fc49e96de50475e7df`
- Protected `origin/main`: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- Recovery branch remains local-only / unpublished

### Phase L v1 failed-attempt forensic history

The first Phase L installer attempt on the real Windows repository correctly failed closed during stage `[6/11]` before any implementation commit was created.

Observed failure:

- every Phase L static typography assertion passed except `no repository font binaries required`
- the failing assertion performed a recursive filesystem census beneath the repository root for `.woff`, `.woff2`, `.ttf`, and `.otf` files
- that assertion was broader than the actual product contract because a developer checkout may contain unrelated third-party font resources inside local tooling/dependency environments while the public static application never loads or requires them
- the public typography architecture had already passed the meaningful dependency checks: no `@font-face`, no remote font service, deliberate system font stacks, and no computed `Inter` dependency in the product design

The v1 installer then correctly:

- reset the repository to immutable completed Phase K HEAD `01b7e20101c12604ccd9934488bcf589a0ba16c4`
- returned the worktree clean
- retained safety branch `safety/phase-l-typography-20261014-210541789`
- created no Phase L implementation or documentation commit
- performed no push

Root cause was the **new static regression contract**, not the typography product change.

Phase L v2 corrects that contract by validating the public dependency graph instead of asserting global filesystem absence: public HTML routes and top-level runtime CSS must not reference `.woff`, `.woff2`, `.ttf`, or `.otf` assets, and the existing `@font-face` / remote-font-service prohibitions remain enforced. Development-only third-party files that are never referenced by the public application are outside this product invariant.

The typography product behavior was not weakened or altered to make the test pass.

### Repository-first typography audit

The audit confirmed the Phase L debt explicitly identified by the master specification:

- `styles.css` requested `Inter`
- no `@font-face` rule existed
- no public route or runtime stylesheet referenced a font binary
- no Google Fonts or other font-service import existed
- therefore `Inter` was not actually delivered and the rendered type depended on the visitor's local environment

The audit also confirmed that the product already has useful route-specific visual identities and does **not** need a global visual repaint.

The principal hierarchy weakness was over-compressed display typography:

- the shared experience hero used approximately `0.78` line height with `-0.075em` tracking
- the homepage-specific hero tightened further in places
- GNC and Mission Control large section titles used approximately `0.87–0.88` line height with `-0.065em` tracking
- Library and Technical Report display titles also used aggressive negative tracking
- Mission, Windows, GNC, and Mission Control introductory H1 elements had no dedicated shared display rule and therefore depended too heavily on inherited/browser defaults

### Final typography architecture

Phase L deliberately chooses a **system-font architecture** instead of adding a bundled or remote font dependency.

Primary sans stack:

`system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI Variable Text", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

Primary monospace stack:

`ui-monospace, "SFMono-Regular", "Cascadia Mono", Consolas, "Liberation Mono", monospace`

Mathematical equations retain a dedicated serif voice using Georgia / Times New Roman fallbacks.

This architecture:

- costs `$0.00`
- makes no paid-font assumption
- makes no locally installed `Inter` assumption
- avoids a remote font-service dependency
- uses native platform typography where available
- keeps technical monospace and mathematical notation visually distinct

### Visual hierarchy changes

A new shared `typography.css` is loaded **after** route-specific CSS on all eight public routes.

The Phase L layer intentionally changes typography only; it does not redefine route backgrounds, colors, imagery, simulation surfaces, or application state.

Key changes:

- explicit display treatment for Mission / Windows / GNC / Mission Control introductory H1 elements
- normalized main experience hero line height and tracking
- normalized GNC and Mission Control large section-title compression
- normalized PSI hero display typography
- normalized Mission Library and Technical Report title typography
- normalized entry/recovery large heading rhythm
- reduced excessive metadata tracking while preserving technical hierarchy
- `text-wrap: balance` for large display headings where appropriate
- `text-wrap: pretty` for selected long-form explanatory text
- tabular lining numerals for important engineering readouts, report tables, and publication metrics
- Technical Report print serif behavior preserved
- mathematical equation serif behavior preserved
- explicit mobile display-type adjustments rather than relying on desktop compression

### Route identity preservation

Phase L preserves the existing route-specific stylesheets and identities:

- Homepage → `landing.css`
- Mission → trajectory / space weather / entry route styling
- Windows → `windows.css`
- GNC → `gnc.css`
- Mission Control → `mission-control.css`
- PSI → `psi.css`
- Mission Library → `library.css`
- Technical Report → `report.css`

The new typography layer does not introduce background or color rules. It is intentionally not a global visual repaint.

### Dedicated Phase L QA

Added:

- `docs/PHASE_L_TYPOGRAPHY_QA.md`
- `scripts/validation/validate_phase_l_typography.py`
- `scripts/validation/phase_l_typography_regression.html`
- `scripts/validation/validate_phase_l_regression.py`

Static Phase L validation enforces:

- unresolved `Inter` request removed
- system-ui-first sans stack present
- deliberate system monospace stack present
- no `@font-face` dependency
- no remote font-service dependency
- public typography requires no repository font binaries
- typography layer does not repaint route identity
- explicit intro H1 hierarchy
- normalized cinematic hero compression
- normalized GNC / Mission Control display hierarchy
- tabular lining numerals on engineering readouts
- mathematical serif voice retained
- Technical Report print serif contract retained
- explicit mobile typography treatment
- every public route loads `typography.css` last
- every public route retains its route-specific visual stylesheet

The Phase L browser regression exercises all eight public routes at representative:

- phone portrait
- phone landscape
- tablet
- desktop

On real Windows release acceptance it requires both Chrome and Edge and verifies:

- typography stylesheet cascade order
- no computed `Inter` dependency
- body readability floor of at least `16 px`
- primary H1 existence and viewport containment
- primary H1 line-height/font-size ratio `>= 0.86`
- primary H1 absolute tracking ratio `<= 0.055`
- section display H2 line-height/font-size ratio `>= 0.92` where present
- no unintended horizontal overflow

### Protected regression contract

Before the Phase L implementation commit is created, the deterministic Windows installer requires the complete protected suite to pass, including:

- public experience validation
- text / markup integrity validation
- Phase L static typography validation
- Trajectory Correction pure-model validation
- PSI pure-model validation
- Space Weather pure-model validation
- Entry pure-model/evidence validation
- celestial asset validation
- final release validation
- Mission Explorer Chrome/Edge regression
- Through Orion's Windows regression
- GNC deterministic Chrome/Edge regression
- Mission Control Chrome/Edge regression
- PSI Chrome/Edge regression
- Trajectory Correction Chrome/Edge regression
- Space Weather Chrome/Edge regression
- Entry Chrome/Edge regression
- global responsive Chrome/Edge QA
- Phase K Mission Library + Technical Report regression
- Phase L typography + visual-quality Chrome/Edge regression

The full protected browser matrix is run before exact staged-tree verification. After the exact Phase L candidate tree is staged, the Phase L-critical static/browser gates are repeated against that staged candidate before commit.

### Evidence and engineering boundaries

Phase L changes presentation only.

It does **not** alter:

- mission data
- mission chronology
- evidence taxonomy
- evidence wording
- quantitative results
- PSI model behavior
- trajectory-correction propagation
- space-weather model behavior
- Entry / Descent / Recovery model behavior
- GNC fixed-step behavior
- Mission Control scenarios or decision model
- Windows mission imagery set
- Mission Explorer phase progression or geometry
- Phase K Mission Library content
- Phase K Technical Report engineering substance

Existing canonical evidence classes remain:

- NASA REPORTED
- MISSIONLAB DERIVED
- MODELED
- INFERRED
- UNKNOWN / NOT PUBLIC

### Phase L implementation allowlist

The implementation changes exactly these 14 paths:

1. `docs/PHASE_L_TYPOGRAPHY_QA.md` — added
2. `gnc.html` — load shared typography layer last
3. `index.html` — load shared typography layer last
4. `library.html` — load shared typography layer last
5. `mission-control.html` — load shared typography layer last
6. `mission.html` — load shared typography layer last
7. `psi.html` — load shared typography layer last
8. `scripts/validation/phase_l_typography_regression.html` — added
9. `scripts/validation/validate_phase_l_regression.py` — added
10. `scripts/validation/validate_phase_l_typography.py` — added
11. `styles.css` — replace unresolved `Inter` request with deliberate system font tokens
12. `technical-report.html` — load shared typography layer last
13. `typography.css` — added shared Phase L typography and hierarchy layer
14. `windows.html` — load shared typography layer last

The documentation-only commit later changes only:

- `docs/ENGINEERING_LOG.md`

### Deterministic implementation identity

- Implementation subject: `Stabilize typography and visual hierarchy`
- Implementation parent: `01b7e20101c12604ccd9934488bcf589a0ba16c4`
- Implementation tree: `1a07f2458077b0cceecc9d64f948bf5703105d80`
- Implementation commit: `7a73b538d6aa3dfa7c8bd24dc08a9b33c0876b46`

The implementation commit is preserved immutably beneath the documentation-only Phase L closure commit.

### Safety / rollback / delivery

The Phase L installer:

- refuses to run unless the real repository is clean at the exact completed Phase K documentation HEAD
- verifies the expected branch, parent, tree, and protected `origin/main`
- verifies the recovery branch remains unpublished
- creates a timestamped `safety/phase-l-typography-*` branch before production mutation
- validates patch SHA-256, exact allowlist, per-file payload hashes, and embedded project-log hash
- applies only the approved Phase L paths
- runs the complete protected analytical + browser release matrix
- verifies the exact staged implementation tree before commit
- repeats Phase L-critical validation against that exact staged tree
- creates the deterministic local implementation commit only after all gates pass
- appends this complete Phase L section without replacing prior engineering-log content
- creates a separate deterministic documentation-only local commit
- verifies exact final HEAD / parent / tree and a clean worktree
- rolls back all production mutation to the immutable Phase K starting commit on any failure before completion
- retains the Phase L safety branch for forensics
- performs no push, merge, deployment, release, or remote publication

### Phase L closure

Phase L resolves the font-delivery ambiguity and stabilizes A2 MissionLab's visual hierarchy without converting the product into a generic design system or sacrificing route identity.

The project remains:

- public-data grounded
- evidence bounded
- deterministic where modeled
- static / zero-cost
- locally committed only
- unpublished on the recovery branch

**NO PUSH WAS PERFORMED.**

## Phase M — Accessibility + Mobile / Responsive Hardening

**Status:** COMPLETE — release documentation is appended only after the deterministic Windows installer passes the full Phase M release gate.

### Objective

Treat mobile as a first-class A2 MissionLab product surface and close real accessibility/responsive gaps without redesigning protected mission experiences, weakening evidence discipline, changing simulation/state models, or compressing the desktop product into a generic mobile shell.

Phase M specifically hardens:

- semantic interaction behavior
- keyboard navigation and Escape handling
- focus return and visible focus
- screen-reader selected/current/value state
- canvas alternatives
- reduced-motion behavior for nonessential autonomous canvas animation
- mobile navigation ownership
- touch-target and safe-area contracts
- expanded responsive release coverage across the required viewport matrix

### Immutable starting state

- Repository: `C:\Users\prakh\Documents\a2-missionlab`
- Branch: `phase-10-quality-recovery`
- Starting HEAD: `e711db684adda507efd973fc6f090fdc50baa841`
- Starting parent: `7a73b538d6aa3dfa7c8bd24dc08a9b33c0876b46`
- Starting tree: `68184cad8052ce1f3decf633c744e8243ae91196`
- Protected `origin/main`: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- Recovery branch remains local-only / unpublished

Phase M starts exactly from the completed Phase L documentation HEAD. Completed Phase F/G/H/I/J/K/L implementation history is not rewritten, squashed, amended, or redone.

### Repository-first audit findings

The current Phase L product already contained substantial responsive hardening, including:

- shared phone/tablet breakpoints
- safe-area inset handling
- a shared `>=44 px` mobile control-height floor
- Mission Control's protected `>=64 px` target contract
- route-specific responsive layouts
- protected Windows viewer geometry and controls
- protected GNC, Mission Control, PSI, Trajectory, Space Weather, and Entry browser/model contracts

Phase M therefore avoids broad CSS churn and addresses only present gaps discovered in the current tree:

1. Shared mobile navigation did not consistently support Escape-to-close with focus return.
2. Mission Library installed duplicate mobile-nav handlers in addition to shared navigation ownership.
3. Several mutually exclusive visual button groups did not expose their selected state to assistive technology.
4. Entry and Windows position controls exposed numeric values without equivalent mission-context text.
5. Entry event and Windows filmstrip current-position state was visual only.
6. The shared hero-star canvas and Mission Explorer's autonomous canvas loop did not consistently honor `prefers-reduced-motion`.
7. Meaningful engineering canvases relied on visual context without a uniform accessible image/text-equivalent contract.
8. Through Orion's Windows assigned button semantics directly to image content instead of using a native action control.
9. Windows and Mission Library had focus styles that could be made more explicit and reliable.
10. The existing protected responsive matrix covered 96 total Chrome/Edge cases; Phase M required the full twelve-viewport matrix without weakening that older suite.
11. The first real Windows Phase M browser gate exposed one remaining touch-target gap: the Through Orion's Windows `#crew-zoom` control inherited a 42 px base minimum outside the `<=760 px` media query and rendered at 42.8 px on 768/844/1024-wide cases. The validator correctly rejected it; the final Phase M rule raises the base minimum to 44 px.

### Implemented accessibility hardening

#### Shared and standalone navigation

`js/core.js` now owns shared disclosure navigation behavior for the standard public-route navigation patterns. The disclosure state remains synchronized through `aria-expanded`; Escape closes an open menu and returns focus to the trigger without forcing a scroll jump.

Mission Library's duplicate nav handlers were removed so one shared owner controls the behavior.

PSI intentionally does not load the shared core runtime, so `js/psi.js` receives the equivalent standalone Escape/focus-return behavior.

#### Screen-reader state

Visual selection state is now synchronized with assistive-technology state where the control semantics are mutually exclusive choices:

- Trajectory Correction maneuver presets and direction controls use `aria-pressed`.
- Space Weather reference presets and mission-location context use `aria-pressed`.
- PSI engine-count and regolith controls use `aria-pressed`.
- GNC explanatory loop controls synchronize `aria-pressed` while preserving the already-protected AUTO/MANUAL state contract.

Current-position semantics use `aria-current` where the meaning is location/progress rather than a toggle:

- Entry event rail
- Through Orion's Windows filmstrip

Entry and Windows scrubbers now expose descriptive `aria-valuetext` that combines the numeric position with mission meaning.

#### Canvas semantics and alternatives

The decorative landing-page star canvas remains hidden from assistive technology.

Meaningful engineering canvases now expose image semantics and accessible naming/text-equivalent references using nearby visible explanatory content. This adds no hidden scientific claim and does not change evidence provenance.

Covered current public surfaces include Mission Explorer, Trajectory Correction, Entry, Space Weather, GNC, PSI, Windows geometry, and the already-protected Mission Control canvas contract.

#### Reduced motion

Nonessential autonomous animation now respects `prefers-reduced-motion` in:

- the shared landing hero-star canvas
- the current Mission Explorer canvas loop

Under reduced motion those surfaces render a stable frame and still redraw when state changes. Visibility handling prevents unnecessary autonomous RAF work while the document is hidden.

User-driven or simulation-essential engineering interactions are not indiscriminately disabled. Entry playback and GNC progression remain explicit mission-learning controls. PSI and Mission Control retain their existing reduced-motion handling.

#### Through Orion's Windows semantics and focus

The current mission photograph remains semantic image content with its descriptive `alt` text.

A separate native `button` now owns the fullscreen action and references the existing dialog. This preserves image meaning and viewer geometry instead of assigning `role="button"` and `tabindex` directly to the image.

Viewer arrows, zoom controls, fullscreen image action, lightbox controls, and Mission Library filters/cards retain explicit visible `:focus-visible` treatment. The Windows fullscreen/zoom trigger now also enforces a 44 px base minimum height across tablet and phone-landscape widths, rather than only inside the narrow-phone media query.

### Responsive/mobile contract

Phase M preserves the existing safe-area and touch-target work instead of rewriting it.

The dedicated Phase M browser matrix adds these twelve viewport classes per browser:

1. `320 × 568`
2. `360 × 800`
3. `375 × 812`
4. `390 × 844`
5. `430 × 932`
6. `844 × 390` phone landscape
7. `768 × 1024` tablet portrait
8. `1024 × 768` tablet landscape
9. `1024 × 800` approximately-1024 class
10. `1280 × 800`
11. `1440 × 900`
12. `1920 × 1080`

Across eight public routes this is 96 route/viewport cases per browser and 192 total cases across Chrome and Edge.

The Phase M browser gate checks, among other protected invariants:

- unintended horizontal overflow
- clipped visible interactive controls
- zero-size canvas failures
- public-route navigation completeness
- mobile menu open/close state
- Escape close + focus return
- nav-link close behavior
- accessible names for visible controls
- engineering canvas accessible naming
- mobile touch-target floor
- selected/current ARIA state
- Windows native image-action/current-filmstrip semantics
- Windows/GNC/Mission Control route-specific contracts
- Mission Control's protected `>=64 px` target invariant

The pre-existing `validate_responsive_browser_qa.py` matrix remains unchanged and mandatory. Phase M adds coverage; it does not replace or weaken protected browser regressions.

### Dedicated Phase M QA

Added:

- `docs/PHASE_M_ACCESSIBILITY_QA.md`
- `scripts/validation/validate_phase_m_accessibility.py`
- `scripts/validation/phase_m_accessibility_regression.html`
- `scripts/validation/validate_phase_m_regression.py`

The static gate verifies the eight public routes for document language, one named main landmark, skip-link resolution, one primary H1, labeled navigation, explicit image alt text, canvas semantics/text alternatives, native Windows image-action semantics, disclosure ownership, Escape/focus return, selected/current/value state, reduced motion, visible focus, touch-target floors, Mission Control's 64 px protected contract, safe-area support, and grouped Space Weather choice semantics.

### Protected product/evidence boundaries

Phase M does **not** alter:

- mission chronology or public evidence
- evidence taxonomy or provenance wording
- Mission Explorer phase progression or geometry
- Windows mission-image set, viewer geometry, preload behavior, lightbox model, or arrow/touch/keyboard navigation contract
- GNC fixed-step model, AUTO/MANUAL behavior, THC/RHC controls, disturbance injection, or educational closed loop
- Mission Control scenarios, lenses, decision model, narrative/canvas separation, or target-size invariant
- PSI model behavior
- Trajectory Correction propagation/model behavior
- Space Weather model/evidence behavior
- Entry / Descent / Recovery model/evidence behavior
- Phase K Mission Library content/focused-rendering model
- Phase K Technical Report engineering substance/print contract
- Phase L typography floors, ratios, font architecture, or route-specific visual identity

Canonical evidence classes remain unchanged:

- NASA REPORTED
- MISSIONLAB DERIVED
- MODELED
- INFERRED
- UNKNOWN / NOT PUBLIC

### Validation and coverage boundary

During deterministic package construction from the Phase M handoff, the available reconstructed tree passed:

- changed-file allowlist verification
- `git diff --check`
- JavaScript syntax checks for shared and protected route runtimes
- `scripts/validate_public_experience.py`
- `scripts/validation/validate_text_integrity.py`
- `scripts/validation/validate_phase_k_publication.py`
- `scripts/validation/validate_phase_l_typography.py`
- `scripts/validation/validate_phase_m_accessibility.py`
- Trajectory Correction pure-model/evidence regression
- PSI pure-model/evidence regression
- Space Weather pure-model/evidence regression
- Entry pure-model/evidence regression
- celestial asset/provenance validation
- final release validation

The handoff reconstruction intentionally does not contain the repository's gitignored `data/processed/...` products, so legacy analytical validators that require those files cannot be truthfully re-executed in the package-build sandbox. The first such observed dependency was `data/processed/entry/entry_trajectory_m50.csv`; Space Weather analytical context similarly requires processed products. Those validators are not marked as passed or weakened.

The deterministic Windows installer therefore keeps the full protected analytical/evidence suite mandatory against the user's real repository, where the processed products exist, before any Phase M implementation commit is accepted.

Likewise, the package-build environment does not provide the required Windows Edge + Chrome execution environment. No Phase M Edge/Chrome pass is claimed from package construction. The installer requires both browsers and fails closed if the protected browser matrix or expanded Phase M matrix does not pass.

The first real Windows release-gate execution validated the full protected analytical/evidence chain and all pre-Phase-M Chrome/Edge browser regressions, then failed closed only on the expanded Phase M matrix: both Edge and Chrome reported four failing `windows.html` cases, each identifying `button#crew-zoom:touch-height-42.8`. The installer rolled the repository back cleanly to the immutable Phase L starting commit. The corrected delivery changes the control's base minimum height to 44 px and leaves the >=44 px validator requirement unchanged.

Physical iPhone Safari, Android Chrome, tablet hardware, and desktop Safari are not claimed by this phase unless actually run; they remain manual release-candidate targets.

### Phase M implementation allowlist

The implementation changes exactly these 20 paths:

1. `docs/PHASE_M_ACCESSIBILITY_QA.md` — added Phase M accessibility/responsive contract
2. `gnc.html` — named/text-equivalent GNC engineering canvas semantics
3. `js/core.js` — shared nav Escape/focus return + reduced-motion hero canvas handling
4. `js/entry.js` — event `aria-current` + mission-context slider value text
5. `js/gnc.js` — synchronized explanatory-loop `aria-pressed` state
6. `js/mission.js` — reduced-motion/visibility handling for the current Mission Explorer canvas
7. `js/psi.js` — selected-state semantics + standalone nav Escape/focus return
8. `js/space-weather.js` — selected-state semantics
9. `js/trajectory.js` — selected-state semantics
10. `js/windows.js` — current-filmstrip/value text + native fullscreen-button event ownership
11. `library.css` — explicit keyboard focus treatment
12. `library.js` — remove duplicate shared navigation ownership
13. `mission.html` — engineering canvas semantics + grouped Space Weather choice semantics
14. `psi.html` — PSI canvas text-equivalent semantics
15. `scripts/validate_public_experience.py` — require Phase M QA artifacts
16. `scripts/validation/phase_m_accessibility_regression.html` — added expanded responsive/accessibility browser harness
17. `scripts/validation/validate_phase_m_accessibility.py` — added static accessibility/mobile contract
18. `scripts/validation/validate_phase_m_regression.py` — added required Chrome/Edge Phase M driver
19. `windows.css` — native image-action overlay + explicit focus-visible treatment + >=44 px base fullscreen/zoom target
20. `windows.html` — native fullscreen button + Windows geometry canvas semantics

The documentation-only closure commit later changes only:

- `docs/ENGINEERING_LOG.md`

### Deterministic implementation identity

- Implementation subject: `Harden accessibility and responsive behavior`
- Implementation parent: `e711db684adda507efd973fc6f090fdc50baa841`
- Implementation tree: `9d2e1541ffd3971d7d4610de7eebbb45e6bc263e`
- Implementation commit: `60cdc7a1be2b081b0fcd7e7105cc4de8806f356a`

The implementation commit is preserved immutably beneath the documentation-only Phase M closure commit.

### Safety / rollback / delivery

The Phase M installer:

- refuses to run unless the real repository is clean at the exact completed Phase L documentation HEAD
- verifies the expected branch, parent, starting tree, and protected `origin/main`
- verifies the recovery branch remains unpublished
- creates a timestamped `safety/phase-m-accessibility-*` branch before production mutation
- validates patch SHA-256, exact allowlist, per-file payload hashes, and embedded project-log hash
- applies only the approved Phase M paths
- runs the protected static/model/evidence gate and the full Entry analytical/evidence suite
- runs the complete protected Chrome/Edge browser matrix plus the expanded 192-case Phase M matrix
- verifies the exact staged implementation tree before commit
- repeats Phase M-critical static/browser validation against that exact staged tree without unnecessarily duplicating every full browser matrix
- creates the deterministic local implementation commit only after all gates pass
- appends this complete Phase M section without replacing prior engineering-log content
- creates a separate deterministic documentation-only local commit
- verifies exact final HEAD / parent / tree and a clean worktree
- rolls back all production mutation to the immutable Phase L starting commit on any failure before completion
- retains the Phase M safety branch for forensics
- performs no push, merge, deployment, release, or remote publication

### Phase M closure

Phase M hardens A2 MissionLab's keyboard, assistive-technology, reduced-motion, and mobile/responsive behavior at the presentation/interaction boundary while preserving the mission-analysis product underneath it.

The project remains:

- public-data grounded
- evidence bounded
- deterministic where modeled
- static / zero-cost
- mobile-aware without desktop compression
- locally committed only
- unpublished on the recovery branch

**NO PUSH WAS PERFORMED.**

## Phase N — Performance + Failure-Quality Hardening

**Status:** COMPLETE — this section is appended only after the deterministic Windows installer passes the full protected analytical/static/browser release gate plus the dedicated Phase N normal-asset and intentional-failure browser passes.

### Objective

Make the completed Phase M product feel more immediate and fail more gracefully without changing protected mission models, evidence boundaries, interaction semantics, or visual identity.

Phase N is deliberately bounded to current-tree performance and failure-quality debt:

- stop paying for Earth/Moon imagery on routes that never draw those bodies,
- suspend autonomous Mission Explorer and GNC animation work when it is not visible,
- remove permanently bypassed legacy Entry code,
- remove duplicate Windows resize redraw ownership,
- defer noncritical image loading/decoding while preserving priority imagery,
- replace broken-image icons and unexplained blank regions with explicit user-facing fallback states,
- prove that missing optional celestial JPEGs do not blank the mission canvases.

### Immutable starting state

- Repository: `C:\Users\prakh\Documents\a2-missionlab`
- Branch: `phase-10-quality-recovery`
- Starting HEAD: `14e161281e733b700159c5a306e970a8de74dea3`
- Starting parent / Phase M implementation: `60cdc7a1be2b081b0fcd7e7105cc4de8806f356a`
- Starting tree: `72f26106a8eccbb5b500e95e74bb54fc9eb5b81b`
- Protected `origin/main`: `d74a88d20f6ff1bd8be2ff0dbe3fb2b44cc13187`
- Recovery branch publication state: local-only / unpublished

Phase N starts exactly from the completed Phase M documentation HEAD. Completed Phase F/G/H/I/J/K/L/M work is preserved and is not restarted, squashed, amended, or reimplemented.

### Repository-first audit findings

The handoff contained only Phase N audit notes; no Phase N production mutation had occurred in the user repository. Re-auditing the exact Phase M tree confirmed the remaining debt was current:

1. `js/core.js` eagerly created Earth and Moon `Image` resources on every route that loaded the shared runtime. The Earth JPEG is 518,573 bytes and the Moon JPEG is 252,499 bytes, for 771,072 bytes (~753 KiB) of optional celestial payload.
2. Mission Explorer already honored reduced motion and `document.hidden`, but it still kept animation ownership while its canvas was offscreen.
3. GNC ran a continuous RAF loop without document-visibility or viewport suspension.
4. `js/mission.js` still shipped a legacy Entry/descent/recovery implementation that the Phase I `data-entry-phase-i` contract permanently bypassed.
5. Through Orion's Windows performed an additional direct crew-geometry redraw on resize after the existing RAF-coalesced resize owner had already been installed.
6. Mission Explorer, GNC, Mission Control, and Technical Report figures were still eager by markup despite being noncritical to first paint.
7. Shared image fallback behavior covered the NASA-photo substitution path but did not provide a universal explicit state for a missing local figure or a failed fallback image.
8. `mission.html`, `gnc.html`, and `mission-control.html` retained NASA image preconnect hints even though those routes do not request remote NASA image resources.

Previously identified Phase E opportunities that were already solved by later phases were not redone: Mission Library focused rendering/lazy figures are protected Phase K behavior, the obsolete Technical Report `app.js` load was already removed, and shared reduced-motion behavior from Phase M remains protected.

### Performance implementation

#### Demand-owned celestial imagery

`js/core.js` now begins Earth and Moon assets in an `idle` state. `drawEarth()` or `drawMoon()` owns the first request for the corresponding JPEG.

The canvas does not wait on the asset. The existing procedural Earth/Moon renderer draws immediately, then a successfully decoded JPEG upgrades a later frame. If a JPEG fails, the procedural body remains the final rendering path.

This removes the previous global eager request from non-celestial routes while preserving meaningful visual quality on routes that actually use celestial imagery.

Celestial completion now emits a targeted `a2:celestialchange` event instead of synthesizing a global `resize` event. Current consumers with celestial canvases subscribe to that event and schedule only the redraw they need:

- Mission Explorer
- Trajectory Correction
- Space Weather
- Mission Control

#### Visibility-aware animation ownership

Mission Explorer now has explicit RAF ownership and a viewport visibility gate using `IntersectionObserver` with a small pre-entry margin. It pauses when:

- its canvas is offscreen,
- the document is hidden,
- reduced motion is requested,
- deterministic static QA mode is active.

It resumes only when needed and exposes `data-a2-animation="running|paused"` for deterministic browser QA.

GNC now uses the same visibility principle while preserving its meaningful control simulation. It pauses when the canvas is offscreen or the document is hidden, cancels the owned RAF, and resets its timestamp so resuming does not apply hidden/offscreen elapsed time as a large simulation step. Reduced motion does not disable the educational GNC control simulation because that progression is meaningful rather than decorative.

#### Dead JavaScript removal

The legacy Entry/descent/recovery implementation inside `js/mission.js` was permanently bypassed by the current Phase I route contract. Phase N removes that unreachable renderer instead of carrying it into every Mission Explorer load.

`js/mission.js` changes from 27,082 bytes to 18,114 bytes, a reduction of 8,968 bytes (~33.1%). The protected current Entry implementation in `js/entry-model.js` and `js/entry.js` is unchanged.

#### Resize work

Through Orion's Windows keeps the existing RAF-coalesced crew-geometry resize owner and removes the second direct resize redraw. Viewer behavior, 25-image navigation, adjacent preload, lightbox, keyboard/touch navigation, and protected geometry remain unchanged.

#### Image loading and decoding policy

The loading policy is now explicit rather than uniformly eager:

- Homepage hero: remains eager and receives `fetchpriority="high"` plus async decoding.
- Remaining homepage imagery: lazy + async decoding.
- Mission Explorer figures: lazy + async decoding.
- GNC static figure: lazy + async decoding.
- Mission Control static figure: lazy + async decoding.
- Technical Report: all 13 engineering figures lazy + async decoding.
- Through Orion's Windows: primary current mission image remains eager; lower-page local figure content is lazy + async while existing adjacent-image preload behavior remains protected.

Unused NASA image preconnects are removed from Mission Explorer, GNC, and Mission Control.

### Failure-quality implementation

The shared runtime now captures image `error` events at document level, including images inserted after startup. It also checks already-completed failed images so a failure that occurs before the shared handler is installed is still converted into a meaningful state.

Failure behavior is layered:

1. If an image declares a local `data-fallback`, that fallback is attempted once.
2. If the fallback fails, or if no fallback exists, the broken image is hidden.
3. A visible `role="status"` replacement is inserted with the message: `Figure unavailable in this build. The surrounding mission context remains available.`

This avoids a browser broken-image icon or unexplained blank region without fabricating replacement mission evidence.

Optional Earth/Moon JPEG failure is handled differently because a scientifically bounded procedural visualization already exists. A failed celestial request moves the shared state to fallback/partial as appropriate and keeps the procedural canvas nonblank.

### Phase N implementation allowlist

The implementation commit changes exactly these 19 paths:

1. `docs/PHASE_N_PERFORMANCE_QA.md`
2. `gnc.html`
3. `index.html`
4. `js/core.js`
5. `js/gnc.js`
6. `js/mission-control.js`
7. `js/mission.js`
8. `js/space-weather.js`
9. `js/trajectory.js`
10. `js/windows.js`
11. `mission-control.html`
12. `mission.html`
13. `scripts/validate_public_experience.py`
14. `scripts/validation/phase_n_performance_regression.html`
15. `scripts/validation/validate_phase_n_performance.py`
16. `scripts/validation/validate_phase_n_regression.py`
17. `styles.css`
18. `technical-report.html`
19. `windows.html`

The documentation-only closure commit later changes only:

- `docs/ENGINEERING_LOG.md`

### Dedicated Phase N QA

Added:

- `docs/PHASE_N_PERFORMANCE_QA.md`
- `scripts/validation/validate_phase_n_performance.py`
- `scripts/validation/phase_n_performance_regression.html`
- `scripts/validation/validate_phase_n_regression.py`

The static Phase N validator locks the current performance/failure contract, including:

- exact 771,072-byte optional celestial baseline,
- idle/demand-owned Earth/Moon resources,
- no eager global celestial image owner,
- targeted celestial redraw event ownership,
- reduced `js/mission.js` runtime and absence of bypassed legacy Entry code,
- visibility-aware Mission Explorer/GNC animation ownership,
- removal of duplicate Windows resize redraw,
- shared explicit image failure behavior,
- procedural celestial fallback availability,
- route-specific lazy/async image policy,
- homepage hero priority,
- removal of unused NASA preconnects,
- inclusion of Phase N artifacts in the public release validator.

The dedicated browser harness runs 20 assertions per mode. It deliberately establishes route-local canvas visibility before testing animation state instead of assuming a canvas is visible at page load. It disables smooth scrolling inside the tested route, computes the canvas document-space position, scrolls the iframe window directly, and couples running/paused assertions to measured viewport geometry. It covers:

- no Earth/Moon request on GNC, Mission Library, or Technical Report,
- no visible `undefined`/`NaN` failure text on those routes,
- exact Earth/Moon demand on Mission Explorer and Mission Control,
- expected celestial state in normal and intentional-404 modes,
- nonblank celestial canvases under asset failure,
- Mission Explorer offscreen RAF pause and resume,
- GNC visible/offscreen/resume RAF behavior,
- explicit local technical-figure failure replacement with no broken-image icon.

The Windows driver runs the same 20 assertions twice per browser: normal assets and intentional Earth/Moon 404 failure. Across Edge and Chrome, the dedicated Phase N gate therefore covers 80 assertions.

### Windows gate qualification history

The first Phase N delivery attempt reached the dedicated Phase N browser gate only after the complete protected stack through Phase M had passed. The new Phase N gate then failed in both Edge and Chrome, in both normal-asset and intentional-celestial-failure modes. The installer retried once, failed closed again, rolled the repository back to the immutable Phase M documentation HEAD `14e161281e733b700159c5a306e970a8de74dea3`, removed the Phase N files, and reported a clean worktree. It retained the forensic safety branch `safety/phase-n-performance-20261014-233419723`.

The repeated failures were limited to the new animation-visibility assertions: Mission Explorer was reported as `running` after the harness attempted to move it offscreen, while GNC alternated between `paused` and `running` at points the harness assumed were visible/offscreen. This inconsistency exposed a harness geometry/synchronization defect rather than a protected simulation/model failure.

Root cause: the original Phase N harness assumed GNC was visible immediately after loading even though the current route places the simulator below its intro and section material. It also used nested-frame scrolling patterns that were already known elsewhere in the repository to be ambiguous: `scrollIntoView()` from a nested iframe can move the outer browsing context, and the site's `scroll-behavior: smooth` can make immediate visibility-state assertions race the actual route position.

The corrected harness does not weaken the requirement. It is stricter and more explicit:

- it disables smooth scrolling only inside the test route,
- computes document-space canvas coordinates,
- scrolls the route window directly to a measured visible position before asserting `running`,
- scrolls the route window to a measured position at least 180 px beyond the viewport before asserting `paused`,
- resumes by directly restoring a measured visible position,
- requires both the expected `data-a2-animation` state and matching measured geometry for each assertion,
- avoids nested-frame `scrollIntoView()` entirely.

No protected Phase F-M runtime/model contract was changed by that correction. The Phase N production runtime behavior from the first package remained intact; the v2 change was confined to the Phase N QA documentation/static contract/browser harness.

The second Windows qualification attempt again passed the complete protected stack through Phase M. The dedicated Phase N driver then failed differently and more narrowly: Edge and Chrome, in both normal and intentional-celestial-failure modes, remained at `Status: RUNNING`, `Cases: 0`, `Failures: 0`. The retry reproduced the same condition. The installer therefore failed closed again, restored the immutable Phase M documentation HEAD, removed all Phase N production/QA mutations, confirmed a clean worktree, and retained the second forensic safety branch `safety/phase-n-performance-20261014-234654498`.

That second failure exposed a completion-protocol defect, not a Phase N assertion failure. The multi-route iframe harness still waited on `frame.onload`, even though current public routes can intentionally contain remote NASA imagery irrelevant to the local regression and `window.load` can remain pending on those requests. The Python driver also used Chromium `--dump-dom` plus virtual-time expiry as its implicit signal that the asynchronous harness had finished. When the first route never reached the harness's `onload` continuation, Chromium could emit the still-initial `RUNNING / 0 cases` DOM before any assertion had executed.

The v3 qualification harness removes both ambiguous dependencies:

- route readiness is based on same-origin pathname + DOM `interactive`/`complete` readiness, not `window.load`,
- route-position settling forces layout and uses bounded real timers rather than waiting on the RAF mechanism being tested,
- all v2 measured visible/offscreen geometry requirements remain intact,
- `scrollIntoView()` remains prohibited in the nested harness,
- the browser produces a completed JSON payload only after the 20 assertions finish,
- that payload is POSTed to a tokenized loopback endpoint owned by the Python driver,
- the Python driver waits for that exact completion event, then terminates the isolated headless browser process tree,
- `--dump-dom` and virtual-time expiry are no longer treated as test-completion signals,
- absence of the completion POST is a hard timeout/failure, never a synthetic pass.

No Phase F-M runtime/model/evidence contract and no Phase N production-runtime optimization was changed to address the second failure. The v3 correction is confined to Phase N QA documentation, static self-validation, the browser harness, and its Python driver.

The third Windows qualification attempt proved that the v3 completion handshake worked: Edge and Chrome completed all 20 assertions in both normal and intentional-celestial-failure modes instead of hanging at `RUNNING / 0 cases`. The protected release stack again passed through Phase M. The dedicated Phase N gate then reported exactly three failures in every browser/mode combination: the intentionally missing Technical Report figure did not produce the explicit fallback node, its broken-image state was not hidden, and the readable `Figure unavailable` status was therefore absent. The retry reproduced the same 3-of-20 failure set. The installer failed closed, restored `14e161281e733b700159c5a306e970a8de74dea3`, removed the Phase N files, confirmed a clean worktree, and retained `safety/phase-n-performance-20261015-000911198`.

That third failure exposed a lazy-loading test-order defect, not a shared image-failure runtime defect. Phase N deliberately marks Technical Report figures `loading="lazy"`. The harness replaced the `src` of `#fig-oem-events` while that figure was still far offscreen, then waited for an image `error` event. Chromium is allowed to defer an offscreen lazy image request, so there was no failed resource request and therefore no `error` event for `js/core.js` to handle.

The v4 qualification harness preserves the production lazy-loading policy and tests the user-visible failure path instead of bypassing it:

- load the Technical Report to DOM readiness,
- position `#fig-oem-events` into the route viewport with the same measured route-local geometry helper already used for RAF assertions,
- only then swap the visible figure to the intentionally missing local resource,
- wait for the existing shared capture-phase image-error handler to hide the image and append the readable failure state,
- preserve the exact 20-case count and all prior normal/celestial-failure requirements.

No Phase N production runtime changed for v4. The correction is confined to Phase N QA documentation, the static self-validation contract, and the browser harness. The tokenized Python completion driver from v3 remains unchanged.

### Protected validation

Package-construction validation against the exact reconstructed handoff tree passed the gates that are truthfully executable in the build sandbox:

- JavaScript syntax for all changed route runtimes
- Python syntax for new/changed Phase N validators
- `git diff --check`
- public experience validation
- public text/markup integrity validation
- Phase K publication/knowledge-system static contract
- Phase L typography/visual-quality static contract
- Phase M accessibility/responsive static contract
- Phase N performance/loading/failure static contract
- Trajectory Correction pure-model/evidence regression
- PSI pure-model/evidence regression
- Space Weather pure-model/evidence regression
- Entry pure-model/evidence regression
- celestial asset/provenance validation

The package-build reconstruction intentionally does not contain the repository's gitignored `data/processed/...` products required by the historical full analytical suite, so those file-dependent analytical validators are not falsely reported as rerun there.

The package-build environment also cannot truthfully execute the required Windows Edge + Chrome headless matrix. Local Chromium cannot establish the loopback HTTP navigation required by these repository browser harnesses in the package-build sandbox, including a trivial immediate-POST page. This is recorded as an environment limitation, not converted into a product pass.

### Deterministic Windows release gate

Before this engineering-log section can be appended, the installer must run against the user's real repository and pass all of the following:

- exact repository path / branch / HEAD / parent / tree checks,
- clean worktree,
- protected `origin/main` verification after fetch/prune,
- proof that `origin/phase-10-quality-recovery` remains unpublished,
- timestamped Phase N safety branch creation,
- patch ZIP SHA-256, exact path allowlist, and per-file SHA-256 verification,
- protected static/model/evidence suite,
- full Entry and Space Weather analytical/evidence validators against the real processed-data products,
- final release validator,
- all protected Chrome/Edge route browser regressions from prior phases,
- the existing responsive browser QA,
- Phase K browser regression,
- Phase L browser regression,
- the protected Phase M 12-viewport × 8-route × 2-browser matrix (192 cases),
- Phase N browser regression in Edge and Chrome, normal + intentional celestial 404 mode (80 assertions total),
- exact staged implementation tree verification,
- a second Phase N-critical staged-candidate validation pass,
- exact deterministic implementation commit verification,
- documentation-only log append and deterministic documentation commit verification,
- exact final HEAD / parent / tree verification,
- clean worktree.

Any failure before completion causes the installer to roll production mutation back to the immutable Phase M documentation starting commit while retaining the safety branch for forensics. No push, merge, deployment, release, or remote publication is performed.

### Responsive and mobile boundary

Phase N does not redesign the responsive system or weaken Phase M. The full Phase M matrix remains mandatory in the installer, including the shared >=44 px interaction floor and Mission Control's protected >=64 px target floor.

The performance changes are intentionally compatible with phone/tablet behavior:

- image lazy loading reduces initial noncritical transfer/decoding pressure,
- offscreen RAF suspension avoids spending frame time on invisible canvases,
- RAF resume resets elapsed time where necessary instead of catching up hidden time,
- existing canvas sizing and route-specific responsive geometry remain untouched.

Physical iPhone Safari, Android Chrome, tablet hardware, and desktop Safari are not claimed unless actually run; they remain manual release-candidate targets.

### Performance result

Measured current-tree effects include:

- Optional celestial JPEG payload: 771,072 bytes, no longer requested merely because `js/core.js` is present.
- `js/mission.js`: 27,082 -> 18,114 bytes (`-8,968 bytes`, about `-33.1%`).
- Non-celestial GNC, Mission Library, and Technical Report are explicitly guarded in browser QA against celestial JPEG requests.
- Mission Explorer and GNC no longer own continuous RAF work while offscreen/hidden.
- Windows no longer performs the duplicate direct crew-geometry resize redraw.
- Below-fold/static figure decode ownership is deferred without lowering the priority of the homepage hero or the current Windows mission image.

Phase N does not introduce a bundler, rewrite historical CSS/JS wholesale, or remove high-value imagery simply to improve a synthetic score.

### Evidence and product boundaries

Phase N does **not** change:

- mission chronology or public evidence,
- evidence taxonomy or provenance wording,
- Trajectory Correction model behavior,
- PSI model behavior,
- Space Weather model/evidence behavior,
- Phase I Entry model/evidence behavior,
- GNC deterministic AUTO/MANUAL model, disturbance behavior, or control semantics,
- Mission Control scenarios, lenses, decision behavior, or mission evidence,
- Through Orion's Windows 25-image content/navigation/lightbox contract,
- Mission Library focused rendering/content model,
- Technical Report engineering substance/print contract,
- Phase L typography hierarchy,
- Phase M accessibility/responsive semantics.

Canonical evidence classes remain unchanged:

- NASA REPORTED
- MISSIONLAB DERIVED
- MODELED
- INFERRED
- UNKNOWN / NOT PUBLIC

### Deterministic implementation identity

- Implementation subject: `Harden performance and failure states`
- Implementation parent: `14e161281e733b700159c5a306e970a8de74dea3`
- Implementation tree: `ab1f9e6b5e50f60226a257dd880cb0785aa3a1c5`
- Implementation commit: `133d7f067a3f49875aa533d40c0f268414387fa2`

The implementation commit is preserved immutably beneath the documentation-only Phase N closure commit.

### Safety / delivery

The corrected Phase N v4 delivery is a deterministic patch ZIP plus PowerShell installer. All three prior qualification attempts left the real branch clean at the immutable Phase M start and retained their safety branches; v4 starts from that exact rollback state. The installer:

- refuses to operate from any repository state other than the exact completed Phase M handoff,
- validates the patch before repository mutation,
- changes only the 19 approved implementation paths,
- fails closed on missing browsers, missing processed evidence products, validation failures, path drift, payload drift, staged-tree drift, or commit drift,
- creates a timestamped `safety/phase-n-performance-*` branch before mutation,
- commits locally only after the complete release gate passes,
- appends this log only after the implementation commit is verified,
- creates a separate deterministic documentation-only commit,
- verifies a clean final worktree,
- performs no push.

### Phase N closure

Phase N closes the performance and failure-quality work defined by the master prompt without reopening completed phases. The current application now avoids a major globally eager optional image payload, stops two important offscreen animation loops, removes obsolete shipped Entry code, reduces duplicate resize work, applies clearer image loading ownership, and turns missing imagery into explicit bounded fallback behavior.

The next planned master-prompt phase is **Phase O — Metadata / Social / README**: deliberate per-route metadata/social presentation plus a hiring-quality repository README, while preserving the completed Phase N runtime/evidence baseline.
