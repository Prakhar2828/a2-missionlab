# A2 MissionLab — final authoritative publication audit

Audit date: **2026-10-12**. This release prioritizes postflight/as-flown NASA reporting over preflight assumptions when both exist.

## High-risk facts rechecked for final publication

| Claim | Publication state | Authoritative source / boundary |
|---|---|---|
| Artemis II proximity operations completed for about 70 minutes with controlled approach/retreat and automated departure | NASA REPORTED | NASA, 2026-04-01: https://www.nasa.gov/blogs/missions/2026/04/01/artemis-ii-flight-update-proximity-operations-complete-perigee-raise-burn-up-next/ |
| All 17 planned proximity steps flown exactly, exact range/state history, individual thruster history | UNKNOWN / NOT PUBLIC | MissionLab Phase 2J.2 keeps plan and as-flown evidence separate |
| Flight Day 4 manual piloting lasted 41 minutes and exercised 6-DOF and 3-DOF thruster modes | NASA REPORTED | https://www.nasa.gov/blogs/missions/2026/04/04/artemis-ii-flight-day-4-crew-completes-manual-piloting-demonstration/ |
| Flight Day 8 additional manual piloting demonstration was forgone by flight controllers | NASA REPORTED | https://www.nasa.gov/blogs/missions/2026/04/08/artemis-ii-flight-day-8-crew-conducts-key-tests-on-return-to-earth/ |
| Artemis II toilet fault was troubleshot by crew and Mission Control and normal operation restored | NASA REPORTED | https://www.nasa.gov/blogs/missions/2026/04/02/artemis-ii-flight-update-crew-and-ground-teams-successfully-troubleshoot-orions-toilet/ |
| OTC1 / OTC2 cancelled because trajectory was already sufficiently on track | NASA REPORTED | NASA mission updates and `data/reference/artemis_ii_maneuver_plan_execution.json` |
| OTC3 executed for 17.5 s | NASA REPORTED | NASA Flight Day 5 update / MissionLab maneuver reference |
| RTC1 = 1.6 ft/s, 15 s; RTC2 = 5.3 ft/s, 9 s; RTC3 = 4.2 ft/s, 8 s | NASA REPORTED | NASA Flight Day 7 / 9 / 10 updates / MissionLab maneuver reference |
| Burn-specific main/aux/RCS assignment | UNKNOWN / NOT PUBLIC | ESM architecture does not prove the engine set for each correction |
| ESM has 33 engines: 1 main, 8 auxiliary, 24 RCS | ESA REPORTED | https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/European_Service_Module_engines_powering_Artemis_II |
| Entry interface = 23:53 UTC at 400,000 ft, around Mach 35; planned blackout about six minutes; comms reestablished 00:00 UTC | NASA REPORTED, minute precision | https://www.nasa.gov/blogs/missions/2026/04/10/artemis-ii-flight-day-10-re-entry-live-updates/ |
| Drogues 00:03 UTC at 23,400 ft; mains 00:04 UTC at 5,400 ft; splashdown 00:07 UTC | NASA REPORTED, minute precision | same NASA live re-entry source |
| Sutton–Graves heat flux | MODELED | MissionLab engineering correlation, **not** measured heat-shield telemetry |
| NAIRAS Version 4 models aerospace ionizing-radiation environments, including aircraft/spacecraft exposure and electronics SEE context | NASA MODEL DOCUMENTATION | https://ccmc.gsfc.nasa.gov/models/NAIRAS~4/; MissionLab does not turn model capability into asserted Artemis II personal dosimetry |
| Artemis III role / Artemis IV landing | NASA CURRENT ARCHITECTURE (as of audit date) | Artemis III is a 2027 LEO demonstration; Artemis IV targets the first Artemis lunar landing in early 2028: https://www.nasa.gov/artemis-iii-news-and-updates/ and https://www.nasa.gov/mission/artemis-iv/ |
| Artemis II lunar flyby photo gallery contains the mission imagery used in the 25-moment Orion-window sequence | NASA REPORTED / NASA IMAGE METADATA | https://www.nasa.gov/gallery/lunar-flyby/; exact-event, near-event, same-phase, and derived-context labels remain distinct in `IMAGE_SOURCES.md` |
| Artemis II preliminary lunar science includes five extremely faint impact flashes reported by crew and subsequently evaluated by the science team | NASA PRELIMINARY SCIENCE REPORT | https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/; the public gallery uses an eclipse image as context and does **not** claim a specific flash is visibly captured unless image metadata establishes it |
| FLIGHT/FDO/FAO/EECOM labels and role framing | NASA MISSION CONTROL ROLE CONTEXT | https://www.nasa.gov/missions/artemis/artemis-i-mission-control-at-a-glance/ |
| SCIENCE is an Artemis II console role supporting lunar science/geology integration | NASA REPORTED | https://www.nasa.gov/centers-and-facilities/johnson/science-takes-center-stage-in-mission-control-for-nasas-artemis-ii/ |
| COMM / ENG SUPPORT are exact Artemis II front-room console acronyms | NOT CLAIMED | Final UI explicitly labels COMM as a MissionLab communications lens and ENG SUPPORT as a MissionLab synthesis lens rather than asserting official console nomenclature |
| PSI occurred on Artemis II | FALSE | Artemis II did not land; the final experience labels PSI as future-Artemis conceptual context only |
| NASA Langley plume-surface interaction testing is relevant to future lunar-landing hazard reduction | NASA REPORTED | https://www.nasa.gov/missions/artemis/nasa-begins-moon-mission-plume-surface-interaction-tests/ |

## Permanent evidence rules retained

- public OEM trajectory ≠ onboard navigation state
- ground orbit determination ≠ onboard state estimate
- AROW public state vector ≠ onboard navigation-filter state
- sequence ≠ causation
- temporal correlation ≠ root cause
- action ≠ reason for action unless evidence supports it
- relevance to a console ≠ decision ownership
- modeled heating / atmosphere ≠ spacecraft telemetry
- mission plan ≠ confirmed as-flown sequence
- propulsion architecture ≠ burn-specific engine assignment
