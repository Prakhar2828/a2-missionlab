# Trajectory Correction Experience QA Contract

## Purpose

The Phase G trajectory-correction experience teaches one primary relationship:

> **Small Δv now can produce a large downstream state change later.**

The public interaction lives in `mission.html#trajectory-lab`. It replaces the historical `Δv × time` sketch with an explicitly educational Earth two-body impulse-response model while retaining the NASA-reported Artemis II maneuver record.

## Evidence boundary

The experience separates:

- **NASA REPORTED** — public maneuver occurrence, cancellation/execution status, public time, reported duration, and reported scalar Δv where available.
- **MISSIONLAB DERIVED** — timing relationships already supported by the shared MissionLab mission clock, such as hours from a return correction to the public Entry Interface minute.
- **MODELED** — the reference Earth-return ellipse, burn direction, RTN impulse, two-body propagation, downstream separation, osculating vacuum-periapsis shift, and modeled arrival-time shift.
- **UNKNOWN / NOT PUBLIC** — complete as-flown targeting vectors, internal targeting states, navigation covariance, execution-error covariance, exact burn-specific propulsion assignment where public evidence does not establish it, and private flight-control targeting products.

The model must never be presented as NASA's as-flown targeting solution.

## Public maneuver record protected by Phase G

| Maneuver | Public state represented in MissionLab |
| --- | --- |
| OTC1 | Cancelled. Planned approximately 0.7 ft/s and approximately 8 s; no executed burn. |
| OTC2 | Cancelled because Orion remained on track; no executed burn. |
| OTC3 | Executed 2026-04-06 03:03 UTC for 17.5 s; scalar flown Δv is not established in the curated MissionLab source set. |
| RTC1 | Executed 2026-04-08 00:03 UTC for 15 s and approximately 1.6 ft/s. |
| RTC2 | Executed 2026-04-10 02:53 UTC for 9 s and approximately 5.3 ft/s. |
| RTC3 | Executed 2026-04-10 18:53 UTC for 8 s and approximately 4.2 ft/s. |

OTC1 and OTC2 cancellations are displayed as valid trajectory-quality decisions, not failed maneuvers.

## Educational dynamics model

The browser model is implemented in `js/trajectory-model.js`.

The reference is an educational Earth-centered ellipse with:

- perigee radius at the public Entry Interface altitude used by MissionLab,
- apogee radius set from MissionLab's derived maximum Earth-center distance,
- Earth point-mass gravity using `μ = 398600.4418 km³/s²`.

A local radial-transverse-normal frame is constructed at the modeled correction opportunity. The interaction supports educational impulses in:

- `+T` along track,
- `−T` reverse along track,
- `+R` outward radial,
- `−R` inward radial,
- `+N` out of plane.

The velocity increment is applied instantaneously and the reference and corrected states are independently propagated with fixed-form RK4 integration under:

`r̈ = − μE r / |r|³`

The model reports:

- 3D separation at the reference Entry Interface epoch,
- radial / along-track / cross-track separation components,
- an osculating **vacuum** periapsis shift,
- modeled time-to-vacuum-periapsis shift,
- a `Δv × time` linear comparison so visitors can see why linear drift is intuition rather than a targeting model.

## Assumptions and omissions

The educational model intentionally omits:

- lunar and solar third-body gravity,
- Earth oblateness and higher-order gravity,
- finite-burn dynamics,
- actual Orion propulsion geometry and pulse sequencing,
- navigation covariance,
- maneuver execution error covariance,
- dispersions,
- atmospheric drag,
- entry lift and guidance,
- real entry targeting constraints,
- NASA flight rules,
- private mission-control products,
- complete as-flown correction vectors.

The reported vacuum-periapsis quantity is not an atmospheric entry target and must never be described as one.

## Public engineering context

NASA's public Artemis II trajectory-correction design publications describe burn placement as an integrated guidance, navigation, and control problem influenced by entry-interface requirements, navigation and maneuver errors, disturbances, tracking geometry, crew schedule, venting, propulsion configuration, thermal constraints, and communications considerations.

Public references surfaced in the experience:

- NASA NTRS 20230000223 — *Optimized Trajectory Correction Burn Placement for the NASA Artemis II Mission*
  https://ntrs.nasa.gov/citations/20230000223
- NASA NTRS 20250000050 — *Performance Impacts to the NASA Artemis II Trajectory Correction Burn Placement*
  https://ntrs.nasa.gov/citations/20250000050
- NASA Artemis II Flight Day 9 RTC2 mission update
  https://www.nasa.gov/blogs/missions/2026/04/10/artemis-ii-flight-day-9-second-return-correction-burn-complete/

These references motivate the engineering context. They do not expose NASA's complete flight targeting solution.

## Pure-model regression contract

`scripts/validation/validate_trajectory_model.js` must verify at minimum:

- zero Δv preserves the reference trajectory,
- increasing coast time increases downstream separation for the protected reference case,
- radial, tangential, and normal directions do not collapse to the same response,
- a normal impulse produces a predominantly cross-track response,
- prograde and retrograde impulses move modeled vacuum periapsis in opposite directions,
- two-body propagation is not silently replaced by the old `Δv × time` scalar,
- OTC cancellation and RTC public magnitude facts remain intact,
- the full tested input envelope produces finite outputs.

## Browser regression contract

`scripts/validation/trajectory_regression.html` and `scripts/validation/validate_trajectory_regression.py` must verify:

- RTC2 initializes as the mission-anchored default,
- mission presets restore RTC1 / RTC2 / RTC3 public magnitude and timing anchors,
- changing a control changes the state to `MODELED WHAT-IF`,
- earlier correction timing produces greater downstream separation in the protected reference case,
- RTN direction controls produce distinct behavior,
- normal-direction separation is predominantly cross-track,
- prograde / retrograde modeled periapsis response changes sign,
- model outputs remain finite,
- the canvas renders,
- the phone-width route has no unintended horizontal overflow,
- engineering assumptions and evidence boundaries remain present.

On Windows release installation, Chrome and Edge are required.

## Protected-experience regression

Phase G must not regress:

- Mission Explorer containment / scroll stability,
- Through Orion's Windows navigation / scroll stability,
- deterministic GNC AUTO / MANUAL behavior,
- Mission Control layout / interaction stability,
- PSI geometry / causality behavior,
- global responsive browser QA.

## Performance contract

The correction visualization must not add a continuous animation loop merely for spectacle. It redraws on state changes and responsive geometry changes. This keeps the route's incremental runtime bounded while preserving the explanatory visualization.
