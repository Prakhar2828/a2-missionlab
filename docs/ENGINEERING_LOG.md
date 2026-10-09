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

\[
r = \sqrt{x^2+y^2+z^2}
\]

Inertial speed:

\[
v = \sqrt{v_x^2+v_y^2+v_z^2}
\]

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

\[
r = \sqrt{x^2+y^2+z^2}
\]

Inertial speed:

\[
v = \sqrt{v_x^2+v_y^2+v_z^2}
\]

Earth radial velocity:

\[
v_r = rac{\mathbf r \cdot \mathbf v}{\|\mathbf r\|}
\]

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

```text
spiceypy==8.2.0
numpy==2.5.3
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

\[
\mathbf r_{O/M}=\mathbf r_O-\mathbf r_M
\]

\[
\mathbf v_{O/M}=\mathbf v_O-\mathbf v_M
\]

Moon-center distance:

\[
d_{O/M}=\|\mathbf r_{O/M}\|
\]

Mean-radius lunar altitude:

\[
h=d_{O/M}-R_{Moon,mean}
\]

SPICE mean lunar radius observed:

```text
1737.400 km
```

Moon-relative speed:

\[
v_{rel}=\|\mathbf v_{O/M}\|
\]

Moon radial velocity:

\[
v_{r,M}=
rac{\mathbf r_{O/M}\cdot\mathbf v_{O/M}}
{\|\mathbf r_{O/M}\|}
\]

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

For normalized interval coordinate \(u\):

\[
h_{00}=2u^3-3u^2+1
\]

\[
h_{10}=u^3-2u^2+u
\]

\[
h_{01}=-2u^3+3u^2
\]

\[
h_{11}=u^3-u^2
\]

Position:

\[
\mathbf p(u)=
h_{00}\mathbf p_0
+h_{10}\Delta t\mathbf v_0
+h_{01}\mathbf p_1
+h_{11}\Delta t\mathbf v_1
\]

The derivative gives interpolated velocity.

## Golden-section minimization

We minimize:

\[
d(t)=\|\mathbf r_O(t)-\mathbf r_M(t)\|
\]

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

\[
1\ mile=1.609344\ km
\]

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

\[
\Delta r=\|\mathbf r_A-\mathbf r_B\|
\]

Velocity difference:

\[
\Delta v=\|\mathbf v_A-\mathbf v_B\|
\]

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

# Phase 1F — Planned Next Step

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

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
python scripts\ingestion\parse_oem.py
python scriptsalidationalidate_trajectory.py
python scripts\processinguild_primary_trajectory.py
.\.venv\Scripts\python.exe scripts\ingestion\download_spice_kernels.py
.\.venv\Scripts\python.exe scripts\processingdd_lunar_geometry.py
.\.venv\Scripts\python.exe scriptsnalysisefine_lunar_closest_approach.py
.\.venv\Scripts\python.exe scriptsnalysis\classify_mission_phases.py
.\.venv\Scripts\python.exe scriptsnalysis\compare_oem_products.py
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
3. Why are large portions of Apr 8/9 OEMs identical to Apr 10 while other portions differ?
4. Do solution differences align with documented maneuver decisions/burns?
5. How should the separate high-rate `Post-RTC3 to EI` trajectory be parsed and integrated?
6. Which values should be treated as authoritative flight data vs. derived analytical products?
7. What interpolation/coordinate assumptions require further validation?

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
