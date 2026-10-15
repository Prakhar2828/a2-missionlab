(() => {
'use strict';

const libraryMenu =
  document.querySelector('.menu-btn');

const libraryNav =
  document.querySelector('.nav-links');

if (libraryMenu && libraryNav) {

  const setLibraryNavOpen =
    open => {

      libraryNav.classList.toggle(
        'open',
        open
      );

      libraryMenu.setAttribute(
        'aria-expanded',
        String(open)
      );
    };

  libraryMenu.addEventListener(
    'click',
    () => {

      setLibraryNavOpen(
        !libraryNav.classList.contains(
          'open'
        )
      );
    }
  );

  libraryNav
    .querySelectorAll('a')
    .forEach(
      link => {

        link.addEventListener(
          'click',
          () => {
            setLibraryNavOpen(false);
          }
        );
      }
    );

  document.addEventListener(
    'keydown',
    event => {

      if (
        event.key === 'Escape' &&
        libraryNav.classList.contains(
          'open'
        )
      ) {

        setLibraryNavOpen(false);

        try {
          libraryMenu.focus({
            preventScroll: true
          });
        }
        catch {
          libraryMenu.focus();
        }
      }
    }
  );
}


const topics = [
{
 id:'mission-overview', title:'Mission overview', domain:'Mission architecture',
 intro:'Artemis II was a crewed lunar flyby and systems-validation mission. MissionLab treats it as one connected engineering problem rather than a sequence of isolated milestones: launch establishes the mission clock, trajectory determines geometry, geometry affects communications and science, vehicle systems constrain operations, return targeting sets entry conditions, and entry physics determines the final descent and recovery timeline.',
 relevance:'The public mission can be reconstructed well enough to teach those dependencies without claiming access to private NASA telemetry. The shared MissionLab timeline begins at 2026-04-01 22:35:12 UTC and carries events through splashdown and postflight recovery. The project combines NASA- and ESA-reported events with MissionLab-derived geometry and engineering models, while keeping those evidence classes separate.',
 method:'The backbone is a normalized mission clock plus structured reference datasets. Public OEM state vectors are parsed and correlated with SPICE ephemerides; communications, maneuver, GNC, ECLSS, lunar-science, entry, and Mission Control evidence are normalized into machine-readable JSON. Phase-specific validation scripts check schema, chronology, physical bounds, and permanent evidence guardrails before publication.',
 interpret:'A reader should see the mission as a chain of handoffs. Flight dynamics hands geometry to communications and science. Maneuver targeting protects later geometry. GNC maps sensing and crew intent into motion. Entry turns orbital-scale kinetic energy into atmospheric heating, load, and parachute descent. Mission Control integrates all of those disciplines while preserving crew safety and mission objectives.',
 ops:'For Mission Control, the value of the shared timeline is not that every console sees the same priority. It is that everyone reasons from the same mission state. FLIGHT integrates, FDO concentrates on trajectory, FAO on activities, EECOM on habitability and consumables, COMM on link availability, SCIENCE on observation opportunities, and engineering support on technical evidence.',
 limits:'The public record does not expose every internal state, flight rule, controller parameter, telemetry channel, or private discussion. MissionLab therefore reconstructs only what can be supported by public evidence and marks model outputs and derived quantities as such.',
 artifacts:['data/reference/artemis_ii_mission_control_perspectives.json','data/reference/artemis_ii_phase2_integrated_operations.json','data/reference/artemis_ii_phase2_closure_manifest.json'], skills:['cross-domain systems thinking','mission timeline synthesis','evidence normalization','reproducible validation']
},
{
 id:'flight-dynamics', title:'Flight dynamics & trajectory reconstruction', domain:'Flight dynamics',
 intro:'Flight dynamics answers a deceptively simple question: where is Orion, how fast is it moving, and how does that state evolve relative to Earth, the Moon, and future targeting constraints? MissionLab starts from NASA public Orbit Ephemeris Message products rather than an invented continuous telemetry feed.',
 relevance:'Those state vectors support nearly every other technical chapter. Lunar closest approach, sphere-of-influence crossings, maximum Earth distance, communications occultation, solar eclipse geometry, maneuver correlation, and entry handoff all depend on an internally consistent trajectory and clock.',
 method:'The ingestion pipeline parses multiple Artemis II OEM ASCII products into structured state histories, validates state count and time coverage, and carries frame metadata rather than silently assuming coordinate equivalence. SPICE kernels provide Earth, Moon, and Sun ephemerides. For lunar geometry, MissionLab computes Moon-relative position and velocity, brackets the closest sampled approach, then numerically refines pericynthion. The refined result is 2026-04-06 23:00:46.177998 UTC, 8,281.938 km from the Moon center, about 6,544.538 km above a mean lunar radius, at roughly 1.381073 km/s Moon-relative speed.',
 interpret:'The result is more than a single closest-approach number. The sign of Moon-relative radial velocity changes around pericynthion, providing a physical check that the range extremum has been bracketed correctly. Sphere-of-influence entry and exit provide a useful campaign convention for segmenting the flyby, but the selected SOI is an analytical boundary rather than a literal discontinuity in gravity.',
 ops:'FDO cares about the predicted future state, not just the current position. A trajectory solution is operationally valuable because it supports targeting and confirms whether a correction opportunity is needed before a later constraint such as lunar aim point or entry corridor.',
 limits:'A public OEM is not proven to be Orion’s exact onboard navigation-filter state. Differences between OEM versions are not automatically navigation error, and OEM creation time does not prove when a maneuver was assimilated into a solution.',
 artifacts:['scripts/ingestion/parse_oem.py','scripts/processing/add_lunar_geometry.py','scripts/analysis/refine_lunar_closest_approach.py','docs/assets/phase1f_oem_with_events.svg'], skills:['ephemeris parsing','coordinate geometry','numerical event refinement','trajectory validation']
},
{
 id:'lunar-flyby', title:'Lunar flyby geometry', domain:'Flight dynamics / science',
 intro:'The lunar flyby is where multiple MissionLab domains converge. Orion’s position relative to the Moon sets closest approach, far-side passage, Earth occultation, illumination, and the crew’s changing view of lunar terrain.',
 relevance:'MissionLab derives lunar SOI entry at 2026-04-06 04:38:07.532302 UTC and exit at 2026-04-07 17:23:41.922211 UTC for the selected 66,099 km boundary, yielding about 36.76 hours inside that analytical region. Maximum Earth-center distance and refined pericynthion occur within the flyby sequence but answer different geometric questions.',
 method:'Orion state vectors are interpolated against SPICE Moon ephemerides. Range, Moon-relative speed, and radial velocity are computed in a consistent inertial frame. Event times are refined from sampled states rather than reported at the sampling cadence. Mission phases are then classified around geometry-derived boundaries and NASA-reported operational events.',
 interpret:'Closest approach does not necessarily coincide with maximum Earth distance, Earthset, loss of RF signal, or a science observation. Those events are related by the same trajectory but correspond to different geometry tests. Treating them separately prevents one convenient time stamp from being reused as if it represented the entire flyby.',
 ops:'FDO uses flyby geometry to understand targeting and downstream free-return conditions. COMM cares about Earth line of sight. SCIENCE cares about target visibility, lighting, and window orientation. FLIGHT integrates those competing objectives and constraints.',
 limits:'The adopted mean lunar radius smooths real topography. A mean-radius altitude is therefore not local terrain clearance. Public timing precision is preserved when correlating reported crew observations.',
 artifacts:['scripts/processing/add_lunar_geometry.py','scripts/analysis/refine_lunar_closest_approach.py','docs/assets/phase1f_oem_with_events.svg'], skills:['SPICE geometry','event bracketing','relative-state analysis','multi-domain correlation']
},
{
 id:'communications', title:'Communications, DSN & lunar occultation', domain:'Communications / geometry',
 intro:'Communications availability is partly a radio system problem and partly a geometry problem. Near Earth, Artemis II used Near Space Network support. After translunar injection, deep-space operations relied on the Deep Space Network. When the Moon physically moved between Orion and Earth, an expected blackout followed.',
 relevance:'NASA’s public reference placed loss of signal near 22:44 UTC and planned acquisition near 23:25 UTC on April 6. MissionLab uses those minute-level operational times as validation targets rather than exact geometric limb contacts.',
 method:'Phase 2G.1 tests Earth-center line of sight against a spherical Moon using public Orion states and SPICE. Phase 2G.2 adds topocentric DSN station geometry, because a ground antenna is displaced from Earth’s center and Earth rotates beneath the trajectory. Communications event catalogs then correlate expected blackout, reacquisition, network transitions, the O2O demonstration, and later anomaly events on the common mission clock.',
 interpret:'Geocentric occultation and operational DSN contact do not have to match to the second. Station elevation, local horizon, lunar topography, antenna patterns, link margin, scheduling, atmospheric propagation, and threshold definitions all matter. The model’s value is showing that the public window is geometrically consistent while explaining why the two quantities are not identical.',
 ops:'COMM must first classify a signal loss: is it expected from lunar geometry or entry plasma, or is it anomalous? On Flight Day 9, an unexpected return-link loss occurred before RTC2. Communications were restored and burn preparation resumed. Temporal sequence does not prove the link event caused, degraded, or changed the burn.',
 limits:'MissionLab does not infer received signal strength, antenna gain, DSN scheduling, or O2O availability from line-of-sight geometry. RF and optical links are kept separate.',
 artifacts:['data/reference/artemis_ii_communications_events.json','data/reference/artemis_ii_communications_event_catalog.json','docs/assets/communications/phase2g2_dsn_topocentric_occultation.svg','docs/assets/communications/phase2h3_o2o_architecture.svg'], skills:['line-of-sight geometry','network-event correlation','topocentric modeling','evidence boundary design']
},
{
 id:'gnc', title:'Guidance, navigation & control architecture', domain:'GNC',
 intro:'Guidance, navigation, and control are three coupled but distinct functions. Navigation estimates where Orion is and how it is moving and pointing. Guidance defines where it should go or point. Control converts the difference into commands that available effectors can execute.',
 relevance:'The architecture matters because Artemis II deliberately exercised manual and automated behavior. Public sources describe star trackers, IMUs, GPS receivers, a barometric altimeter, optical navigation, Sun sensors, DSN support, vehicle management computers, hand controllers, and propulsion effectors.',
 method:'MissionLab creates a source-backed architecture graph rather than a cartoon control loop. It records producer context and evidence boundaries for onboard navigation state, ground orbit determination, and public AROW/OEM state vectors. It maps crew RHC/THC inputs through flight software to effectors while retaining which internal algorithms and time histories are unavailable.',
 interpret:'A sensor name does not mean the sensor is equally useful in every regime. GPS is valuable near Earth; DSN is external deep-space tracking; inertial sensing propagates motion between updates; star tracking supports attitude knowledge; optical navigation can use apparent Earth/Moon geometry. The state product used by a public website is not automatically the same state used onboard.',
 ops:'During proximity operations and the Flight Day 4 manual demonstration, crew commands entered the GNC chain while flight controllers monitored mission and vehicle constraints. Six-degree-of-freedom and three-degree-of-freedom modes describe the allowed motion/control problem, not public disclosure of controller gains or thruster logic.',
 limits:'MissionLab has no raw filter innovations, guidance commands, controller gains, or individual as-flown RCS pulse history. It does not reverse-engineer proprietary flight software.',
 artifacts:['data/reference/artemis_ii_gnc_architecture.json','data/reference/artemis_ii_navigation_state_estimation.json','docs/assets/gnc/phase2j1_gnc_architecture.svg','docs/assets/gnc/phase2j3_state_product_boundaries.svg'], skills:['systems architecture','state-estimation taxonomy','sensor/effector mapping','known-unknown management']
},
{
 id:'manual-piloting', title:'Manual piloting & control modes', domain:'GNC / human factors',
 intro:'Artemis II was not just a passenger ride. The crew performed planned manual piloting demonstrations so NASA could evaluate how humans command Orion in scenarios relevant to future rendezvous, proximity operations, and contingency flying.',
 relevance:'MissionLab reconstructs proximity operations and the Flight Day 4 manual piloting sequence from public sources. The architecture identifies the rotational hand controller (RHC) for roll/pitch/yaw intent and translational hand controller (THC) for forward/back, up/down, and left/right translation.',
 method:'The reconstruction separates planned objectives from completed activities and from later demonstrations that were foregone. Timeline records are cross-referenced with the GNC architecture rather than treated as proof of private controller behavior. The public evidence supports completed manual approach/retreat during proximity operations and a 41-minute Flight Day 4 demonstration that exercised 6-DOF and 3-DOF modes.',
 interpret:'Manual command does not mean “pilot directly fires thruster X.” Hand-controller input is processed by GNC software, which then commands effectors according to the active mode and constraints. Similarly, a 3-DOF label says which motion axes are actively commanded or constrained, not how the underlying flight-control law is implemented.',
 ops:'FLIGHT and FDO care about whether the demonstration stays inside safe relative-motion and trajectory constraints; FAO cares about the test sequence; engineering support cares about handling qualities and system response; crew provide the human assessment that cannot be captured by trajectory alone.',
 limits:'Public sources do not provide continuous hand-controller deflection, control-law gains, or individual thruster-firing telemetry. MissionLab does not synthesize those histories.',
 artifacts:['data/reference/artemis_ii_manual_piloting_control_modes.json','docs/assets/gnc/phase2j2_manual_piloting_timeline.svg','docs/assets/gnc/phase2j2_proximity_plan_vs_as_flown.svg'], skills:['human-in-the-loop systems analysis','plan-vs-flown reconstruction','GNC reasoning','operational timeline synthesis']
},
{
 id:'propulsion', title:'European Service Module propulsion', domain:'Propulsion',
 intro:'Orion’s European Service Module provides propulsion for major maneuvers, trajectory adjustments, and attitude/translation control through multiple engine classes. A public architecture can describe those available effectors without automatically identifying which one fired in every event.',
 relevance:'That distinction is central to technical credibility. The mission record reports certain burns and their duration or velocity change, but generic ESM architecture does not establish the exact engine assignment for OTC3, RTC1, RTC2, or RTC3 unless a source explicitly says so.',
 method:'MissionLab builds a propulsion architecture from ESA/NASA public material and then links it to the maneuver execution dataset through evidence-safe interfaces. The GNC architecture records one main engine, eight auxiliary R4D-11-class engines, and 24 RCS thrusters in the public source model, while the maneuver dataset has explicit nulls for burn-specific assignment where the source set is insufficient.',
 interpret:'This is a useful example of schema design carrying epistemology. A field set to null is not missing work; it is the correct answer when the public record does not prove a value. The site therefore explains propulsion capability and maneuver outcome separately.',
 ops:'For flight operations, propulsion is evaluated as available capability, performance, constraints, and execution. FDO determines the targeting need; GNC/vehicle systems convert that into commands; Mission Control monitors execution and resulting trajectory. Public reporting may summarize the event without exposing the detailed firing sequence.',
 limits:'No unsupported burn-vector decomposition, tank telemetry, valve history, chamber pressure, or exact correction-burn thruster assignment is fabricated.',
 artifacts:['data/reference/artemis_ii_esm_propulsion_architecture.json','docs/assets/maneuvers/phase2i2_esm_propulsion_architecture.svg','docs/assets/maneuvers/phase2i2_burn_selection_evidence.svg'], skills:['propulsion architecture','schema design for uncertainty','cross-system interfaces','source-aware inference']
},
{
 id:'maneuvers', title:'Trajectory correction maneuvers', domain:'Flight dynamics / propulsion',
 intro:'Trajectory correction maneuvers are small deliberate changes in velocity used to protect a future target. Their importance is not proportional to burn duration: a tiny delta-v applied days before a lunar aim point or entry corridor can accumulate into a large positional change later.',
 relevance:'Artemis II planned three outbound corrections. OTC1 and OTC2 were cancelled because the trajectory remained on track. OTC3 executed for 17.5 seconds. Return corrections RTC1, RTC2, and RTC3 executed with reported magnitude changes of 1.6, 5.3, and 4.2 ft/s, respectively.',
 method:'MissionLab stores planned and executed quantities in separate fields, carries source precision, and explicitly labels cancellation reasons. Maneuver events are correlated to the shared mission clock and public OEM solution brackets. The analysis asks whether trajectory products changed around maneuver epochs but does not turn those solution differences into measured burn delta-v.',
 interpret:'Cancellation is a success condition when the predicted trajectory already meets constraints. OTC1’s planned 0.7 ft/s and approximately eight-second duration are therefore not executed performance data. Likewise, the absence of a public OTC3 delta-v in the selected source does not mean zero.',
 ops:'FDO evaluates whether a correction is needed and what future state it should target. FLIGHT integrates risk and mission objectives. Propulsion/GNC execute the command. Afterward, updated orbit determination confirms the trajectory. RTC2’s preceding communications anomaly is operational context, not a proven cause of burn behavior.',
 limits:'Scalar reported delta-v magnitudes must not be added and described as a net vector delta-v. Burn-specific engine selection remains unknown when not publicly sourced.',
 artifacts:['data/reference/artemis_ii_maneuver_plan_execution.json','data/reference/artemis_ii_maneuver_trajectory_correlation.json','docs/assets/maneuvers/phase2i1_maneuver_plan_execution.svg','docs/assets/maneuvers/phase2i3_oem_solution_brackets.svg'], skills:['targeting logic','plan-vs-execution analysis','time-series correlation','precision-aware data modeling']
},
{
 id:'entry-dynamics', title:'Atmospheric entry dynamics', domain:'Entry / EDL',
 intro:'Earth entry is an energy-management problem. Orion arrives with enormous kinetic energy and must dissipate it through aerodynamic interaction with the atmosphere while staying inside structural, thermal, guidance, communications, and recovery constraints.',
 relevance:'MissionLab reconstructs the public entry trajectory into altitude, speed, flight-path angle, and kinematic deceleration histories, then aligns them with public entry/recovery events. That creates the backbone for atmosphere, Mach, rarefaction, heating, blackout, parachute, and splashdown analysis.',
 method:'High-rate entry states are ingested and mapped through validated frame transformations into Earth-fixed/geodetic geometry. Speed is differentiated carefully for kinematic deceleration, and event windows are correlated without manufacturing second-level precision from minute-level reports. The analysis retains a distinction between trajectory-derived quantities and model-derived atmospheric quantities.',
 interpret:'The shape of each curve has a physical story. Altitude falls, speed decays sharply as drag grows, and the flight-path angle evolves through Orion’s guided lifting entry. Deceleration peaks when the atmosphere has become dense enough to remove energy rapidly, then declines as speed is depleted. No single plot is the “entry.” The sequence is coupled.',
 ops:'Entry guidance has to deliver the capsule to the parachute/recovery corridor while respecting thermal and load limits. COMM expects plasma-related signal constraints. Recovery teams depend on the downstream landing footprint. MissionLab can correlate those public events without reconstructing private guidance commands.',
 limits:'Public trajectory is not the same as internal navigation or guidance telemetry. Differentiated deceleration can amplify noise and is presented as a derived kinematic quantity.',
 artifacts:['docs/assets/entry/phase2c_entry_speed.svg','docs/assets/entry/phase2c_entry_altitude.svg','docs/assets/entry/phase2c_entry_flight_path_angle.svg','docs/assets/entry/phase2c_entry_kinematic_deceleration.svg'], skills:['entry trajectory processing','frame transformation','numerical differentiation','event correlation']
},
{
 id:'atmospheric-modeling', title:'Atmosphere, Mach & rarefaction', domain:'Aerothermodynamics',
 intro:'Trajectory states provide position and velocity; they do not directly provide atmospheric density, temperature, speed of sound, Mach number, or continuum validity. Those quantities require an environmental model tied to time and location.',
 relevance:'Dynamic pressure and convective heating depend on density. Mach number depends on local speed of sound. Rarefaction determines when continuum-based engineering correlations become physically credible. MissionLab therefore models the environment before interpreting aerothermal results.',
 method:'Phase 2E uses NRLMSIS 2.0 with curated drivers to estimate atmospheric properties along the reconstructed entry path. Earth-relative speed is combined with modeled speed of sound to estimate Mach. Mean free path and a body-scale characteristic length support Knudsen-number calculation and flow-regime classification. Validation checks physical ranges and ensures modeled quantities are never relabeled as recorded spacecraft channels.',
 interpret:'At very high altitude the atmosphere is so thin that continuum assumptions weaken even though the spacecraft is moving extremely fast. As density increases, the flow transitions toward continuum conditions. This matters because a heating correlation can output a number everywhere numerically while only being physically interpretable in part of the trajectory.',
 ops:'Atmospheric uncertainty propagates into predicted loads and heating. Operationally, entry design uses much higher-fidelity tools and dispersed cases; the public MissionLab model is an explanatory reconstruction showing how the dependencies fit together.',
 limits:'No winds are included in the Earth-relative speed approximation used by the heating model. NRLMSIS output is a model, not local in-situ telemetry around Orion.',
 artifacts:['data/reference/artemis_ii_msis_environment.json','data/reference/artemis_ii_rarefaction_model.json','docs/assets/entry/phase2e_density.svg','docs/assets/entry/phase2e_mach_history.svg','docs/assets/entry/phase2e_knudsen_history.svg'], skills:['environmental modeling','dimensionless flow analysis','model-domain validation','uncertainty communication']
},
{
 id:'convective-heating', title:'Sutton–Graves convective heating', domain:'Aerothermodynamics / TPS',
 intro:'The Sutton–Graves relation is a compact way to estimate stagnation-point convective heat flux for hypersonic entry. MissionLab uses it because it makes the controlling physics visible: density matters, vehicle scale matters, and velocity matters dramatically.',
 relevance:'For Artemis II, the heating estimate connects reconstructed entry speed to the thermal-protection discussion without pretending the project has heat-shield temperature telemetry. The repository’s corrected public figure is phase2e_sutton_graves_heat_flux.svg.',
 method:'MissionLab evaluates q̇ = k √(ρ/Rn) V³ using the Earth constant 1.74153×10⁻⁴, modeled atmospheric density, an Orion EFT-1 heritage/reference nose radius of 6.035 m, and Earth-relative speed. The primary interpretation domain requires hypersonic Mach ≥ 5 and Knudsen number ≤ 0.01, with stricter continuum confidence below 0.001. A ±10% radius sweep is a numerical sensitivity study, not a claim about Artemis II geometry uncertainty.',
 interpret:'Velocity cubed is the central lesson. A 10% change in velocity would change the V³ factor by roughly 33%, before density or radius changes are considered. The peak heat-flux time therefore does not have to match peak dynamic pressure or peak deceleration. Different physics drive each maximum.',
 ops:'TPS/entry engineering cares about heat-flux history, integrated heat load, material response, and margin—not one dramatic peak number. MissionLab pairs the correlation with the loft/rebound heating history to show why the full time history matters.',
 limits:'Cold-wall correlation only. No radiative heating, finite wall temperature, ablation, pyrolysis, blowing, recession, catalytic wall effects, or detailed nonequilibrium chemistry. This is not measured surface heat flux or temperature.',
 artifacts:['data/reference/artemis_ii_convective_heating_model.json','docs/assets/entry/phase2e_sutton_graves_heat_flux.svg','docs/assets/entry/phase2e_sutton_graves_heat_load.svg'], skills:['engineering correlation implementation','domain-of-validity analysis','sensitivity analysis','model-vs-measurement discipline']
},
{
 id:'thermal-protection', title:'Thermal protection & Avcoat evidence', domain:'TPS / materials',
 intro:'A heat shield is not designed from peak temperature alone. The thermal-protection system must survive a coupled history of heat flux, total heat load, pressure, chemistry, material response, and structural/operational constraints.',
 relevance:'MissionLab uses public Orion TPS evidence and entry-profile comparisons to explain why Artemis lunar-return conditions differ from lower-energy entries and why the timing/shape of a lifting entry matters to the heat shield.',
 method:'The repository separates public material evidence from simplified physics. Phase 2F builds a TPS decision thread, compares Artemis entry-profile heritage, partitions heating histories across loft/rebound behavior, and documents the boundary between a Sutton–Graves external-flow estimate and actual Avcoat material response.',
 interpret:'Two trajectories can have similar peak heat flux and still impose different total thermal energy because duration matters. Conversely, a lower integrated load does not automatically mean lower peak surface response. Material ablation and internal temperatures depend on transient conduction and chemistry that the simple external correlation does not resolve.',
 ops:'Entry and TPS engineers care about the complete environment and design margin. FLIGHT cares that entry conditions remain within certified bounds. Public mission reporting rarely exposes full thermal telemetry, so the site focuses on physically defensible explanatory models and source-backed design context.',
 limits:'MissionLab does not infer tile-by-tile/Avcoat thermocouple temperatures, recession, bondline temperature, or private certification margin.',
 artifacts:['data/reference/artemis_tps_evidence.json','data/reference/artemis_tps_physics_boundary.json','docs/assets/entry/phase2f_tps_decision_thread.svg','docs/assets/entry/phase2f_loft_heating_flux.svg'], skills:['thermal systems reasoning','evidence-to-physics separation','time-history interpretation','materials context']
},
{
 id:'parachutes-recovery', title:'Parachutes, splashdown & recovery', domain:'EDL / recovery',
 intro:'After hypersonic entry removes most of Orion’s energy, the mission becomes a terminal-descent and recovery problem. Drogue parachutes stabilize and decelerate the capsule before three main parachutes slow it for water impact.',
 relevance:'MissionLab correlates public entry-interface, communications-reacquisition, drogue, main, splashdown, spacecraft power-down, crew extraction, and shipboard recovery context on one timeline.',
 method:'Phase 2D correlates entry events against the trajectory. Phase 4 extends the sequence into recovery and builds a splashdown-accuracy evidence boundary so that public landing-area descriptions are not converted into unsupported coordinate precision. The recovery timeline is then reused when interpreting postflight environmental logger data.',
 interpret:'Parachute events are not isolated timestamps. Their allowable deployment conditions depend on altitude, speed, attitude, stability, and system logic. The public site therefore shows them after the hypersonic environment has collapsed rather than placing them in a generic checklist.',
 ops:'Recovery has its own handoff chain: flight controllers configure the vehicle, recovery forces approach, crew exit is coordinated, and Orion is secured for transport. Mission success continues beyond water contact.',
 limits:'MissionLab does not reconstruct private parachute sensor thresholds, reefing-force histories, exact wind fields, or a precise splashdown point beyond what public evidence supports.',
 artifacts:['data/reference/artemis_ii_entry_descent_recovery_evidence.json','docs/assets/recovery/phase4a2_entry_to_recovery_timeline.svg','docs/assets/recovery/phase4b_splashdown_accuracy_boundary.svg'], skills:['EDL event correlation','recovery systems thinking','geospatial evidence limits','timeline integration']
},
{
 id:'eclss', title:'ECLSS & waste-management operations', domain:'Vehicle systems / EECOM',
 intro:'Life-support and habitability systems rarely look dramatic from outside the spacecraft, but they are mission-critical. Artemis II public reporting included a Flight Day 1 toilet fault indication and a later wastewater vent-line issue, creating a useful case study in troubleshooting without overclaiming root cause.',
 relevance:'The waste-management evidence connects EECOM-style thinking, crew activities, attitude changes, heaters, contingency posture, and engineering support. MissionLab keeps “system restored” separate from “root cause publicly proven.”',
 method:'Public updates are normalized into evidence and decision-thread records. Environmental datasets are analyzed separately so that statistical changes in temperature/humidity/dew point are not casually attributed to a reported vehicle event. Cross-domain figures show where timelines intersect while preserving causal uncertainty.',
 interpret:'An operational response can be appropriate before root cause is fully known. A heater action or Sun-pointing attitude can mitigate a concern without proving what physically caused it. Likewise, restoring normal operations proves functional recovery, not necessarily engineering closure.',
 ops:'EECOM asks whether the crew environment remains safe, whether required function is available, what backup capability exists, and whether an issue can be carried safely to postflight. FAO considers the schedule impact; FLIGHT integrates mission risk; engineering support evaluates technical evidence.',
 limits:'Private fault codes, internal telemetry, exact hardware condition, and nonpublic troubleshooting dialogue are not fabricated.',
 artifacts:['docs/assets/eclss/phase3b2_waste_management_decision_threads.svg','docs/assets/eclss/phase3b3_waste_management_cross_domain.svg','data/reference/artemis_ii_decision_threads.json'], skills:['operational troubleshooting analysis','causal restraint','vehicle-systems evidence synthesis','mission-control perspective mapping']
},
{
 id:'space-weather', title:'Space weather operations', domain:'Heliophysics / operations',
 intro:'Space weather is the changing particle and electromagnetic environment driven by the Sun. For a crewed mission leaving low Earth orbit, the operational concern is not “space is radioactive” but whether solar conditions produce time-varying hazards along the actual mission timeline and trajectory.',
 relevance:'Solar energetic particle events can change rapidly. Artemis II therefore provides a natural context for connecting solar observations and alerts to mission time, while distinguishing environmental monitoring from vehicle- or crew-specific dose.',
 method:'MissionLab Phase 5A aligns NASA OMNI near-Earth context to the shared mission clock. Phase H adds a separate >=10 MeV proton-flux teaching axis using NOAA pfu/S-scale thresholds. These measurements remain distinct from Orion-local radiation, vehicle transport, and crew dose.',
 interpret:'Space-weather data are multi-scale: solar observations can precede an energetic-particle increase; different particle energies arrive differently; geomagnetic response matters near Earth; deep-space exposure context changes as Orion leaves stronger terrestrial shielding.',
 ops:'Operational teams care about alerts, forecast confidence, mission phase, available sheltering/vehicle orientation options, and cumulative exposure context. Public reporting can show monitoring posture without revealing detailed internal thresholds.',
 limits:'MissionLab does not claim private NASA space-weather console products, internal action limits, or actual astronaut dosimetry.',
 artifacts:['scripts/analysis/analyze_space_weather_context.py','data/reference/artemis_ii_space_weather_phase_h.json','docs/assets/radiation/phase5b_nairas_radiation_interface.svg'], skills:['time-correlated environmental analysis','operational risk context','source normalization','uncertainty handling']
},
{
 id:'radiation', title:'Radiation & NAIRAS interface', domain:'Radiation environment',
 intro:'Crew radiation exposure comes from multiple particle populations and depends on time, location, energy spectrum, vehicle shielding, body geometry, and biological weighting. A lunar mission differs from low Earth orbit because substantial time is spent beyond stronger geomagnetic shielding.',
 relevance:'MissionLab’s Phase 5 radiation work creates an explicit interface between trajectory/time and NAIRAS-style modeled radiation products. That makes the computational boundary visible instead of drawing a simplistic Sun-to-Orion arrow.',
 method:'Phase 5B historically prepared 3,262 trajectory rows for the NAIRAS 3.0 interface but did not submit a run or assume Orion shielding. Phase H records NAIRAS Version 4 as current CCMC documentation while preserving the 3.0 artifact as historical analysis. Modeled dose/flux is never silently relabeled as a personal dosimeter measurement.',
 interpret:'A modeled field can support comparison across mission segments and help explain why geometry matters. It cannot, without shielding and transport detail, establish the exact absorbed/effective dose to a particular crew member. The result is best read as environmental context and analysis infrastructure.',
 ops:'Mission Control and mission planning use radiation awareness as one element of integrated crew risk. The operational question includes both present environment and forecast uncertainty.',
 limits:'No private/as-flown Artemis II crew dosimetry, detailed Orion shielding map, organ dose, NAIRAS run output, or NASA flight-rule threshold is inferred from the public interface.',
 artifacts:['docs/assets/radiation/phase5b_nairas_radiation_interface.svg','data/reference/artemis_ii_nairas_interface.json','data/reference/artemis_ii_space_weather_phase_h.json'], skills:['model-interface design','trajectory/environment correlation','radiation evidence boundaries','risk communication']
},
{
 id:'lunar-science', title:'Lunar science reconstruction', domain:'Planetary science',
 intro:'Artemis II’s lunar observations were not simply sightseeing. The crew used cameras, voice observations, and real-time coordination with a science team to document terrain, color, relief, illumination, an eclipse, and transient phenomena.',
 relevance:'MissionLab builds a curated science registry that connects NASA public images, audio/annotation records, lunar targets, geometry, and later postflight interpretation. It treats those as distinct products rather than flattening them into a gallery.',
 method:'The science layer registers product IDs, observation IDs, target/view direction, time precision, and geometry links. Earthset and Earthrise have minute-level public capture times; some terrain/eclipsed-image products have only date-level timing in curated sources. LRO context is linked where it adds terrain/topography comparison.',
 interpret:'Low-angle terminator lighting exaggerates topographic relief, while subtle color/albedo differences can be geologically meaningful. Human descriptions can call attention to properties that are difficult to prioritize from a preplanned automated sequence. Postflight analysis can then compare those observations with orbital datasets.',
 ops:'SCIENCE uses the mission geometry as a moving opportunity set. The support team can update observation priorities based on what the crew reports, while FAO and FLIGHT protect the wider mission timeline and constraints.',
 limits:'MissionLab does not assign exact times to products when the public archive does not provide them. Image metadata and reconstructed geometry are correlated only at the precision justified by the source.',
 artifacts:['data/reference/artemis_ii_lunar_observation_reconstruction.json','docs/assets/lunar_science/phase6a_lunar_science_archive_index.svg','docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg'], skills:['multimodal evidence curation','science/trajectory correlation','metadata normalization','precision preservation']
},
{
 id:'human-observation', title:'Human observation as a data product', domain:'Science / human systems',
 intro:'A human observer is adaptive. Astronauts can notice subtle color, unexpected relief, a transient flash, or a changing corona feature and immediately redirect attention or describe context. That capability complements, rather than replaces, calibrated robotic imaging.',
 relevance:'Artemis II’s science archive includes crew photography, public science audio, tablet annotations, and postflight interpretation. MissionLab exposes the observation process so the visitor can understand why the crew’s role matters scientifically.',
 method:'Each observation record stores evidence state, time precision, associated images, audio or annotation records, target, view direction, geometry link, and whether the observation is confirmed. Earthset/Earthrise are tied to reconstructed limb geometry; impact-flash annotation is retained without treating its visualization time as the physical flash time.',
 interpret:'Human descriptions are qualitative and context-rich; images are spatially rich; geometry is quantitative; postflight science is interpretive. The strongest reconstruction keeps them separate until there is a justified link. That prevents a later caption or annotation from being treated as raw time-tagged telemetry.',
 ops:'A dedicated science console can translate crew observations into follow-up priorities while mission operations protect attitude, timeline, communications, and crew workload constraints.',
 limits:'The public archive may omit exact audio start times or complete observation sequences. MissionLab does not reconstruct missing speech or private science-room dialogue.',
 artifacts:['data/reference/artemis_ii_lunar_observation_reconstruction.json','docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg'], skills:['human-in-the-loop data analysis','multimodal correlation','metadata schemas','science communication']
},
{
 id:'impact-flashes', title:'Impact flashes during lunar eclipse', domain:'Lunar science',
 intro:'During the extended eclipse, the dark lunar surface created an opportunity to watch for extremely faint flashes from meteoroid impacts. Such events can help characterize the impact environment relevant to future surface operations.',
 relevance:'The public record evolved. Early reporting referenced six candidate flashes; the October 7 postflight preliminary science report states that five flashes were reported after other candidate sources such as cosmic rays or spacecraft reflections were considered. MissionLab adopts the later reconciled count.',
 method:'The observation registry records both the early and postflight counts, the selection basis, participating crew annotations, and a reference visualization time that is explicitly marked as not an individual flash time. The record is placed within the derived eclipse window without inventing exact flash timestamps.',
 interpret:'This is a good example of scientific evidence changing as analysis matures. The later source does not make the earlier report “wrong”; it reflects postflight reconciliation. A serious technical site should show that evolution rather than freeze the first number it encountered.',
 ops:'SCIENCE cares about observation credibility and follow-up analysis. Flight operations mainly provide the geometry, attitude, and crew time that make the observation possible.',
 limits:'MissionLab does not estimate impactor mass, location, energy, or individual flash time unless the public evidence provides the necessary measurements.',
 artifacts:['data/reference/artemis_ii_lunar_observation_reconstruction.json'], skills:['source reconciliation','scientific uncertainty','temporal context','evidence revision handling']
},
{
 id:'mission-control', title:'Mission Control discipline perspectives', domain:'Mission operations',
 intro:'Mission Control is not one person looking at one dashboard. Different disciplines ask different questions about the same event. MissionLab uses public role definitions and a validated shared event spine to make that multi-perspective reasoning visible.',
 relevance:'The Phase 7A dataset defines FLIGHT, FDO, FAO, EECOM, COMM, SCIENCE, and ENGINEERING_SUPPORT lenses. Some are official console roles; others are explicitly labeled MissionLab analytical lenses when the public source does not establish a single call sign.',
 method:'Each discipline has a public role basis, focus areas, primary questions, and event priorities on the shared timeline. Priority levels range from context to primary. That matrix supports an interactive view showing how a trajectory correction, wastewater issue, lunar observation, communications blackout, or entry event changes meaning by discipline.',
 interpret:'Priority is not authority. If EECOM and engineering support are both primary on a life-support issue, that does not prove who made the final decision. If COMM is primary for a link anomaly, that does not prove the physical root cause. The method is a disciplined way to teach operational thinking without fabricating private loops.',
 ops:'The most important concept is integration: FLIGHT needs enough information from specialists to manage the whole mission, while specialists need the shared mission state and constraints to keep their local recommendation relevant.',
 limits:'No private transcript, console log, flight rule, or final decision ownership is invented.',
 artifacts:['data/reference/artemis_ii_mission_control_perspectives.json','docs/assets/mission_control/phase7a_discipline_priority_matrix.svg'], skills:['mission-operations modeling','role-based reasoning','priority matrices','responsibility boundary communication']
},
{
 id:'decision-reconstruction', title:'Public decision reconstruction', domain:'Mission operations / evidence',
 intro:'A public decision thread can be reconstructed without pretending to know the exact words spoken in Mission Control. MissionLab organizes evidence into detection, evidence, constraint, options, decision, action, and outcome.',
 relevance:'That structure is useful for maneuver cancellations, vehicle troubleshooting, communications anomalies, entry constraints, and science operations. It forces the analysis to identify what is actually known at each stage instead of telling a smooth but unsupported story after the fact.',
 method:'Phase 7B links events to source-backed observations, known constraints, publicly described actions, and later outcomes. Where a root cause is unknown, the record stays unknown. Where an operational action is known, it is not promoted into causal proof. Where a discipline is highly relevant, that does not automatically imply decision ownership.',
 interpret:'The framework is deliberately asymmetric: “NASA said controllers cancelled OTC1 because Orion was already on track” supports a decision reason. “A communications loss happened before RTC2” supports sequence only. The evidence strength depends on the claim, not on how plausible the story sounds.',
 ops:'For real flight operations, decisions occur under time pressure and incomplete information. A public reconstruction should reflect that uncertainty rather than erase it.',
 limits:'Private option trades, internal risk matrices, dissent, voice loops, and detailed flight-rule application remain outside the public evidence unless specifically released.',
 artifacts:['data/reference/artemis_ii_decision_threads.json','docs/assets/mission_control/phase7b_decision_thread_matrix.svg'], skills:['decision analysis','causal reasoning','evidence graph design','operational uncertainty']
},
{
 id:'data-engineering', title:'Data engineering architecture', domain:'Software / data',
 intro:'MissionLab is a data pipeline before it is a website. Public files arrive in different formats, clocks, units, precision levels, and evidence states. The project normalizes those inputs into deterministic artifacts that later engineering and publication layers can reuse.',
 relevance:'Without this layer, every analysis would independently parse dates, units, source names, and mission events—creating inconsistency. The normalized architecture gives flight dynamics, entry, communications, science, and Mission Control the same mission clock and provenance vocabulary.',
 method:'Python scripts ingest OEM ASCII, CSV, JSON, public source metadata, and model inputs. Structured reference products carry dataset IDs, provenance, units, assumptions, source URLs, and guardrails. Derived CSV/JSON products feed plotting and validation scripts. Publication pages consume stable generated artifacts instead of scraping live sources at runtime.',
 interpret:'The architecture deliberately favors explicit, inspectable intermediate files over hidden notebook state. That makes results easier to rerun, diff, validate, and review. It also makes evidence boundaries machine-readable—for example, a null engine assignment can be validated as an intentional unknown.',
 ops:'For mission-facing software, determinism and traceability matter as much as visualization. A result should be reproducible from known inputs and traceable to its source or model.',
 limits:'Some raw/processed datasets may be gitignored because of size/licensing. The repository’s manifests and validation scripts document required local inputs and expected products.',
 artifacts:['data/reference/','scripts/ingestion/','scripts/processing/','scripts/analysis/','scripts/validation/'], skills:['ETL design','schema consistency','data lineage','deterministic pipelines']
},
{
 id:'data-science', title:'Robust time-series analysis', domain:'Data science',
 intro:'The Orion environment analysis is a concrete data-science workload: 75,396 normalized records are aggregated and analyzed for changes and local anomalies while accounting for quantized sensors and mission context.',
 relevance:'Temperature, relative humidity, and dew point records span flight and recovery/postflight handling. The question is not merely “find weird points.” It is whether statistical changes can be detected reproducibly and then interpreted cautiously against known mission boundaries and handling events.',
 method:'The script aggregates each logger and measurement into 15-minute medians. Change candidates compare one-hour median windows before and after a boundary, scaled by a robust first-difference MAD converted to sigma with the 1.4826 factor and protected by measurement-specific numerical floors. Local anomaly scores use a ±3-hour neighborhood, robust center/scale, thresholding, and temporal clustering. Mission-context classification then flags proximity to launch, splashdown, power-down, recovery, cargo handover, and a reported logger relocation interval.',
 interpret:'Robust statistics reduce sensitivity to isolated outliers and quantized measurements. A high statistical score still does not prove a spacecraft anomaly. Correlation with mission context is a second analytical stage, and even a close temporal match may indicate handling/environment change rather than vehicle causation.',
 ops:'This is the kind of analysis engineering teams use to triage long time-series records: compress data without destroying structure, identify candidate windows, then bring domain context to the interpretation.',
 limits:'The method is custom robust statistical detection, not automatically “machine learning.” Thresholds and window sizes are analytical choices and must be read with the script’s assumptions.',
 artifacts:['scripts/analysis/analyze_orion_environment_changes.py','docs/assets/eclss/phase3a3_change_point_scores.svg','docs/assets/eclss/phase3a3_anomaly_scores.svg'], skills:['robust statistics','time-series aggregation','change detection','anomaly scoring','context correlation']
},
{
 id:'anomaly-detection', title:'Anomaly detection without buzzword inflation', domain:'Data science',
 intro:'Anomaly detection is a family of methods, not a synonym for machine learning. In this repository, the environmental analysis uses transparent robust statistics and local scoring. The public site names the implemented method rather than advertising algorithms that are not present.',
 relevance:'That choice matters for technical credibility. A hiring manager should be able to open the script and see exactly how a score is computed, which thresholds are used, how candidates are clustered, and how mission context is attached.',
 method:'For each 15-minute aggregate series, MissionLab estimates robust scale using the median absolute deviation with sensor-specific floors. Local deviations are scored relative to a neighborhood, then thresholded and clustered so many adjacent bins do not masquerade as independent events. Separate change scores compare window medians across candidate boundaries.',
 interpret:'A score is evidence of statistical unusualness under the chosen local baseline—not a diagnosis. The pipeline therefore emits candidates with timestamps, measurement identity, magnitude/context, and provenance for later review. This separation between detection and explanation is a core design principle.',
 ops:'An operational analyst wants a manageable set of candidate windows, not a model that simply declares “anomaly.” Transparent scoring helps experts inspect why a point was flagged and relate it to known operations.',
 limits:'No Isolation Forest, PCA, or PELT claim should appear unless a repository script actually implements it. The current public environment-change example is robust statistical analysis.',
 artifacts:['scripts/analysis/analyze_orion_environment_changes.py','docs/assets/eclss/phase3a3_anomaly_scores.svg','docs/assets/eclss/phase3a3_change_point_scores.svg'], skills:['algorithm transparency','candidate clustering','threshold design','model naming discipline']
},
{
 id:'software-architecture', title:'Software & reproducibility architecture', domain:'Software engineering',
 intro:'The project is designed as a chain of scripts and validated artifacts rather than a one-off notebook. That makes a technical result reviewable: a plot can be traced to a processed file, a model configuration, a source dataset, and a validation step.',
 relevance:'Phase 2 alone has a complete reproducibility runner covering 58 observed successful pipeline steps from entry ingestion through cross-domain mission-operations integration. Later phases extend ECLSS, radiation, lunar science, Mission Control, and publication work.',
 method:'Python modules perform deterministic transforms and analyses. NumPy and spiceypy are used where numerical/ephemeris work requires them; Matplotlib generates repository SVG figures; JSON and CSV act as durable interfaces; validation scripts enforce schema and scientific guardrails; static HTML/CSS/JavaScript publishes results as a deterministic, dependency-light public interface.',
 interpret:'The software design makes scientific caution enforceable. A validation rule can fail if a modeled quantity is labeled telemetry, if an expected blackout is labeled an anomaly, or if generic propulsion architecture is used to assert a burn-specific engine. Reproducibility is therefore not only “the code runs”; it includes preserving semantic boundaries.',
 ops:'Mission software and engineering analysis benefit from exactly this property: rerunnable pipelines, explicit artifacts, testable assumptions, and outputs that another person can inspect.',
 limits:'The public web application is a static explanatory layer, not a flight-certified system. It does not claim NASA operational authority.',
 artifacts:['scripts/run_phase2.py','data/reference/artemis_ii_phase2_closure_manifest.json','scripts/validation/','.github/workflows/'], skills:['modular Python','CI/validation','artifact contracts','static web publication']
},
{
 id:'uncertainty', title:'Uncertainty, precision & confidence', domain:'Methods',
 intro:'A technically polished number can still be misleading if its source precision, model uncertainty, or interpretation boundary is hidden. MissionLab carries uncertainty as part of the data model rather than relegating it to a footnote.',
 relevance:'Artemis II public sources mix second-level launch times, minute-level operational events, date-only observations, derived sub-second geometry, and model outputs. Presenting all of them with the same number of decimal places would create false confidence.',
 method:'Records carry time-precision labels, provenance classes, model assumptions, and guardrails. Derived event refinements can have numerical precision finer than the public operational source because they come from an interpolated trajectory, but the site labels that distinction explicitly. Sensitivity analyses are described as sensitivity—not inferred real-world uncertainty—unless the underlying uncertain parameter distribution is actually known.',
 interpret:'Precision answers “how finely is this value represented?” Accuracy answers “how close is it to truth?” Confidence answers “how strongly does evidence support the claim?” Those are different. A refined geometric boundary can be numerically precise while still depending on a mean-radius Moon and a public trajectory product.',
 ops:'Operational decision-making needs margins and uncertainty awareness. Public reconstruction can teach that habit even when it cannot reproduce NASA’s internal covariance or dispersed Monte Carlo analysis.',
 limits:'MissionLab does not invent state covariance, navigation uncertainty, model error bars, or certification margins absent public data.',
 artifacts:['data/reference/artemis_ii_phase2_closure_manifest.json','data/reference/artemis_ii_communications_events.json','data/reference/artemis_ii_convective_heating_model.json'], skills:['uncertainty communication','precision metadata','sensitivity interpretation','scientific guardrails']
},
{
 id:'evidence-methodology', title:'Evidence & provenance methodology', domain:'Methods',
 intro:'MissionLab treats provenance as part of engineering, not bibliography decoration. Every important public claim should answer one of five questions: did an authority report it, did MissionLab derive it, did an engineering model produce it, is it a bounded inference, or is the answer unknown from the public evidence?',
 relevance:'This taxonomy prevents common failure modes in mission analysis: turning a model into “telemetry,” turning sequence into causation, turning a troubleshooting action into root cause, or turning a relevant discipline into a claimed decision owner.',
 method:'NASA_REPORTED facts preserve the wording and precision of the source. MISSIONLAB_DERIVED values are deterministic calculations from identified public inputs. MODELED values expose equations, constants, assumptions, and domains of applicability. INFERRED claims are explicitly bounded reconstructions rather than reported measurements. UNKNOWN / NOT PUBLIC fields remain explicit nulls or explanatory boundaries. Validation manifests encode permanent guardrails so future work cannot silently erase them.',
 interpret:'The methodology is intentionally conservative. “We cannot know from this source set” is often a stronger engineering statement than a plausible guess. It also makes later updates easier: if NASA releases new evidence, an unknown field can change with a clear source trail instead of requiring the project to unwind an old assumption.',
 ops:'Flight operations are built around authoritative data, clear ownership, and disciplined interpretation. A public portfolio cannot replicate operational systems, but it can demonstrate the same evidence habits.',
 limits:'Provenance does not make a public reconstruction complete. It makes the incompleteness visible and auditable.',
 artifacts:['data/reference/artemis_ii_mission_analyst_index.json','data/reference/artemis_ii_phase2_closure_manifest.json','data/reference/artemis_ii_decision_threads.json'], skills:['provenance systems','claim classification','causal restraint','auditable analysis']
},
{
 id:'psi', title:'Plume–surface interaction', domain:'Artemis campaign context',
 intro:'Plume–surface interaction (PSI) is included as future Artemis landing engineering context. Artemis II did not land on the Moon, so PSI is explicitly separated from flown mission events.',
 relevance:'Future lunar landers will operate powerful rocket engines near loose regolith in a near-vacuum. Exhaust can entrain particles, excavate or erode the surface, produce high-speed ejecta, obscure sensors, abrade hardware, and contaminate nearby assets. Those effects matter for landing-site design and multi-asset operations.',
 method:'A serious PSI analysis spans regimes. Near the nozzle and dense core, continuum CFD may be appropriate. As the plume expands into vacuum, rarefied-flow methods such as DSMC become important. Surface response requires particle/granular modeling and material properties. Coupled approaches may be needed because gas flow changes the regolith and moving regolith changes the local boundary condition.',
 interpret:'The right question is not “how big is the plume triangle?” but which physical regime applies, what momentum/energy reaches the surface, what particle-size distribution is mobilized, and where ejecta travel. Validation requires engine conditions, geometry, regolith simulant properties, pressure/flux diagnostics, high-speed imagery, and post-test surface characterization.',
 ops:'For future Artemis surface operations, PSI can affect landing approach, sensor visibility, hardware spacing, protective design, and site reuse. As of the October 2026 audit, NASA schedules Artemis III as a 2027 low-Earth-orbit demonstration and targets Artemis IV in early 2028 for the first Artemis lunar landing. PSI belongs in campaign engineering even though it is not part of Artemis II’s flight record.',
 limits:'MissionLab does not present PSI as an Artemis II event and does not claim a validated Artemis lander plume solution without campaign-specific inputs.',
 artifacts:['docs/','data/reference/'], skills:['multiphysics reasoning','CFD/DSMC context','granular-flow framing','campaign-vs-mission scope discipline']
}
];


const extras = {
  'mission-overview':{timeline:'Launch 2026-04-01 22:35:12 UTC → lunar flyby April 6 → Earth return and splashdown April 10/11 UTC.',inputs:'NASA/ESA event reporting, public OEM trajectory products, MissionLab shared mission clock, Phase 2–7 reference datasets.',outputs:'Cross-domain timeline, integrated operational threads, evidence-aware mission narrative.',figure:'docs/assets/phase2/phase2k_integrated_operational_threads.svg',caption:'Phase 2 closure view: flight dynamics, communications, maneuvers, GNC, and downstream handoffs joined on one mission clock.'},
  'flight-dynamics':{timeline:'OEM solutions span outbound flight, lunar encounter, return, and the final correction-to-entry handoff.',inputs:'Time-tagged OEM position/velocity states, mission clock, frame metadata, event catalog.',outputs:'Parsed trajectory tables, event overlays, frame transforms, solution-to-solution comparisons.',figure:'docs/assets/phase1f_oem_with_events.svg',caption:'Public OEM trajectory with mission events. A public state product is not the same thing as Orion’s onboard navigation state.'},
  'lunar-flyby':{timeline:'Chosen lunar SOI entry 2026-04-06 04:38:07.532 UTC → refined pericynthion 23:00:46.178 UTC → SOI exit 2026-04-07 17:23:41.922 UTC.',inputs:'Public Orion OEM states plus SPICE Sun/Earth/Moon ephemerides and a documented lunar mean radius.',outputs:'Moon-relative range/speed, SOI crossings, refined closest approach, Earth occultation and eclipse geometry.',figure:'docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg',caption:'The observation reconstruction places crew science products beside geometry without pretending photo timestamps are telemetry.'},
  'communications':{timeline:'Lunar LOS/AOS centered on the April 6 flyby; separate Flight Day 9 return-link issue; expected entry blackout and public reacquisition near 00:00 UTC April 11.',inputs:'Public communications event catalog, Orion trajectory, Earth/Moon geometry, DSN station coordinates where applicable.',outputs:'Earth-center and topocentric occultation windows, event correlation, RF-vs-O2O evidence boundaries.',figure:'docs/assets/communications/phase2g2_dsn_topocentric_occultation.svg',caption:'Topocentric DSN geometry explains why a station-level visibility window is not identical to an Earth-center line-of-sight calculation.'},
  'gnc':{timeline:'Architecture applies throughout flight; public examples include proximity operations and Flight Day 4 manual piloting.',inputs:'Public Orion sensor/effector descriptions, GNC reference dataset, navigation-state taxonomy, operational threads.',outputs:'Sensor → navigation → guidance → control → effector architecture with explicit onboard/ground/public-state boundaries.',figure:'assets/public/figures/navigation-state-products.svg',caption:'Navigation architecture separates onboard state estimation, ground orbit determination, external tracking, and the public trajectory product.'},
  'manual-piloting':{timeline:'Flight Day 4 manual-control demonstrations were flown; a later planned demonstration was foregone as documented in the public record.',inputs:'Manual-control mode references, proximity-operations plan/as-flown evidence, RHC/THC descriptions.',outputs:'3-DOF/6-DOF control-mode reconstruction and plan-vs-flown timeline.',figure:'assets/public/figures/gnc-proximity-loop.svg',caption:'Plan versus as-flown reconstruction keeps a planned demonstration separate from a maneuver actually performed.'},
  'propulsion':{timeline:'Propulsion architecture underlies major burns and correction maneuvers; architecture alone does not identify the engine used for each RTC.',inputs:'ESM propulsion architecture, maneuver evidence, public engine-system references.',outputs:'Main/auxiliary/RCS architecture map and burn-assignment evidence boundary.',figure:'assets/public/figures/esm-propulsion-architecture.svg',caption:'The public ESM propulsion architecture is useful without inventing a burn-specific engine assignment.'},
  'maneuvers':{timeline:'OTC1/OTC2 cancelled; OTC3 executed April 6; RTC1 April 8 00:03 UTC; RTC2 April 10 02:53 UTC; RTC3 April 10 18:53 UTC.',inputs:'Public burn reporting, maneuver plan/execution JSON, OEM solution brackets, propulsion architecture.',outputs:'Plan-vs-execution table, delta-v chronology, trajectory-product correlation, targeting/evidence boundaries.',figure:'assets/public/figures/trajectory-correction-plan-execution.svg',caption:'Cancelled opportunities and executed corrections are shown together so “not flown” is not mislabeled as failure.'},
  'entry-dynamics':{timeline:'Entry Interface near 2026-04-10 23:53 UTC → communications reacquisition near 00:00 → drogues ~00:03 → mains ~00:04 → splashdown ~00:07.',inputs:'Public entry trajectory, event evidence, Earth-relative state transformation.',outputs:'Altitude, speed, flight-path angle, kinematic deceleration, and event-correlated entry histories.',figure:'assets/public/figures/entry-recovery-sequence.svg',caption:'Entry events over altitude. Reported event precision and derived trajectory interpolation remain visibly distinct.'},
  'atmospheric-modeling':{timeline:'Atmospheric quantities matter only during the return-to-Earth entry segment and are evaluated along the reconstructed trajectory.',inputs:'Entry position/time, NRLMSIS 2.0 drivers/environment model, velocity and local atmospheric properties.',outputs:'Density, Mach, dynamic pressure, Knudsen number, and flow-regime classification.',figure:'docs/assets/entry/phase2e_density.svg',caption:'Modeled atmospheric density rises rapidly with descent; it is an environmental model output, not a pressure-sensor trace.'},
  'convective-heating':{timeline:'Heating analysis is restricted to the hypersonic/continuum portion of entry where the chosen correlation is appropriate.',inputs:'Modeled density ρ, Earth-relative speed V, reference nose radius Rn, Sutton–Graves Earth constant k.',outputs:'Modeled stagnation-point convective heat-flux and integrated heat-load histories.',equation:'q̇ = k √(ρ / Rₙ) V³',figure:'docs/assets/entry/phase2e_sutton_graves_heat_flux.svg',caption:'Sutton–Graves heat flux. The V³ dependence makes hypersonic velocity disproportionately important.'},
  'thermal-protection':{timeline:'TPS relevance peaks during atmospheric entry; postflight inspection is a separate evidence phase.',inputs:'Modeled heating environment, public Orion TPS/materials evidence, physics-boundary dataset.',outputs:'TPS evidence synthesis, modeled-environment context, and explicit non-telemetry limitations.',figure:'docs/assets/thermal/phase3c1_tps_risk_closure.svg',caption:'TPS risk closure connects public materials evidence to entry modeling while keeping model output separate from measured shield response.'},
  'parachutes-recovery':{timeline:'Public event correlation: drogues ~00:03 UTC, mains ~00:04, splashdown ~00:07, followed by crew/capsule recovery.',inputs:'Entry/descent/recovery evidence, public event times, reconstructed entry state.',outputs:'Entry-to-recovery timeline and splashdown-accuracy evidence boundary.',figure:'assets/public/figures/entry-recovery-sequence.svg',caption:'A single timeline connects hypersonic entry to parachutes, splashdown, and recovery without fabricating sub-minute event precision.'},
  'eclss':{timeline:'Environmental and waste-management evidence spans the full crewed mission and continues through operational troubleshooting/recovery context.',inputs:'75,396 normalized environmental records, public mission events, ECLSS/waste-management evidence.',outputs:'15-minute aggregates, robust change/anomaly candidates, decision threads, cross-domain correlations.',figure:'docs/assets/eclss/phase3a2_temperature_trends.svg',caption:'Environmental trends provide the physical time series that later robust-statistical analysis evaluates for changes.'},
  'space-weather':{timeline:'Space-weather context is correlated across outbound transit, lunar encounter, and return rather than treated as a single static exposure number.',inputs:'Public solar/geomagnetic products, mission time, trajectory context.',outputs:'Mission-correlated space-weather context and operational interpretation boundaries.',figure:'docs/assets/space_weather/phase5a_space_weather_context.svg',caption:'Phase 5 space-weather context aligns external environment products to mission time without claiming onboard measurement.'},
  'radiation':{timeline:'Radiation relevance changes as Orion moves from near-Earth shielding into cislunar space and back.',inputs:'Trajectory/time interface, public NAIRAS products/model definitions, space-weather context.',outputs:'Radiation-model interface, flux/dose context, and model-vs-personal-dosimetry boundary.',figure:'docs/assets/radiation/phase5b_nairas_radiation_interface.svg',caption:'The NAIRAS interface makes clear which inputs are environmental and which missing quantities prevent a claim about actual crew dose.'},
  'lunar-science':{timeline:'Primary flyby observations cluster around April 6–7, including Earthset, far-side terrain, Earthrise, and a later solar eclipse.',inputs:'Crew imagery/audio/annotations, public science releases, LRO context, reconstructed geometry.',outputs:'Archive index, observation reconstruction, impact-flash reconciliation, timing/precision metadata.',figure:'docs/assets/lunar_science/phase6a_lunar_science_archive_index.svg',caption:'The science archive index treats images, audio, annotations, geometry, and later interpretation as distinct but linkable products.'},
  'human-observation':{timeline:'Human observation is most concentrated around the lunar flyby, where targets and illumination changed quickly.',inputs:'Crew photographs, spoken observations, annotations, science-team context, trajectory geometry.',outputs:'Multimodal observation record with source timing and target context preserved.',figure:'docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg',caption:'Human observations are correlated to geometry without assigning false telemetry-grade precision to a photograph or spoken remark.'},
  'impact-flashes':{timeline:'The postflight science record reconciles five impact flashes; exact individual flash times are not assigned where the public source does not establish them.',inputs:'Postflight science reporting, observation metadata, MissionLab lunar-science evidence record.',outputs:'Reconciled count plus explicit unknown timing fields instead of invented timestamps.',figure:'docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg',caption:'The reconstruction shows where impact-flash evidence fits in the observation record while preserving unresolved timing.'},
  'mission-control':{timeline:'FLIGHT, FDO, FAO, EECOM, COMM, SCIENCE, and engineering-support perspectives apply across the shared mission timeline.',inputs:'Public role descriptions, shared timeline, discipline-priority matrix, operational threads.',outputs:'Role-backed analytical lenses showing how the same event creates different questions at different consoles.',figure:'docs/assets/mission_control/phase7a_discipline_priority_matrix.svg',caption:'Priority matrix: relevance to a discipline is an analytical perspective, not proof that the console owned a decision.'},
  'decision-reconstruction':{timeline:'Each public thread follows detection → evidence → constraint → options → decision → action → outcome where the public record supports those stages.',inputs:'NASA-reported events, MissionLab derived context, discipline perspectives, decision-thread dataset.',outputs:'Auditable public decision threads with action, cause, and authority kept separate.',figure:'docs/assets/mission_control/phase7b_decision_thread_matrix.svg',caption:'Decision-thread matrix makes the reconstruction structure explicit without inventing private flight-loop transcripts.'},
  'data-engineering':{timeline:'The pipeline spans ingestion through publication; each phase leaves durable reference artifacts for later stages.',inputs:'OEM text, public source records, images/metadata, reference JSON/CSV, model parameters.',outputs:'Normalized schemas, validated derived products, generated SVGs, manifests, static publication assets.',figure:'docs/assets/phase2/phase2k_domain_closure.svg',caption:'Domain closure figure summarizes deterministic pipeline completion and cross-domain handoffs.'},
  'data-science':{timeline:'75,396 environmental records are normalized over the mission, aggregated to 15-minute windows, then analyzed in mission context.',inputs:'Normalized environment records and event context.',outputs:'Median aggregates, MAD robust scale, anomaly scores, change-point candidates, temporal clusters, event correlations.',figure:'docs/assets/eclss/phase3a3_change_point_scores.svg',caption:'Robust change scores surface candidate transitions; thresholds create candidates for interpretation, not automatic root-cause declarations.'},
  'anomaly-detection':{timeline:'Local anomalies are scored across aggregated environmental time series and then clustered/correlated to mission context.',inputs:'15-minute medians, local robust center/scale, thresholds, temporal neighborhood.',outputs:'Anomaly candidates and clusters with contextual correlation.',figure:'docs/assets/eclss/phase3a3_anomaly_scores.svg',caption:'The method is robust statistical anomaly scoring. MissionLab does not relabel it as machine learning.'},
  'software-architecture':{timeline:'Phases execute as reproducible scripts and validation stages before the static site publishes selected outputs.',inputs:'Versioned Python modules, structured reference data, validation rules, generated engineering artifacts.',outputs:'Deterministic artifacts, manifests, CI checks, and a dependency-light HTML/CSS/JavaScript publication.',figure:'docs/assets/phase2/phase2k_integrated_operational_threads.svg',caption:'Integrated operational threads are a generated interface between analytical work and public explanation.'},
  'uncertainty':{timeline:'Precision varies by source throughout the mission: seconds/sub-seconds for some derived geometry, minutes for many public events, and date-only for some observations.',inputs:'Source precision metadata, model assumptions, interpolation/refinement choices, explicit unknowns.',outputs:'Precision-aware values, sensitivity/limitation statements, and boundaries against invented covariance or telemetry accuracy.',figure:'assets/public/figures/navigation-state-products.svg',caption:'State-product boundaries are a concrete uncertainty lesson: onboard state, ground orbit determination, and public OEM products are not interchangeable.'},
  'evidence-methodology':{timeline:'The evidence taxonomy is applied at ingestion, analysis, interpretation, and publication—not added as a final disclaimer.',inputs:'Authoritative public sources, derived computations, engineering models, unresolved fields.',outputs:'Reported / derived / modeled / unknown classifications, lineage, guardrails, validation manifests.',figure:'docs/assets/phase2/phase2k_domain_closure.svg',caption:'Validation/closure exists partly to ensure a later publication step cannot silently erase known evidence boundaries.'},
  'psi':{timeline:'No Artemis II flown-event timeline exists for plume–surface interaction because Artemis II did not land. This is explicitly future Artemis campaign context.',inputs:'Future lander engine/nozzle conditions, geometry, ambient regime, regolith properties and particle-size distribution would be required.',outputs:'A validated solution would need coupled plume flow, surface erosion/entrainment, ejecta transport, sensor/hardware impact, and test correlation.',caption:'Campaign context only: Artemis II did not land. NASA currently targets Artemis IV in early 2028 for the first Artemis lunar landing; continuum CFD, DSMC, and granular/particle methods would address different parts of PSI.'}
};

const repositoryBaseline='c7758aa415928467da0ebb6e48c276c1082be566';
const sourceCatalogUrl=`https://github.com/Prakhar2828/a2-missionlab/blob/${repositoryBaseline}/data/sources/source_catalog.json`;
const nasaMissionUrl='https://www.nasa.gov/artemis-ii-multimedia/';

const categoryById = {
  'mission-overview':'Mission Operations','flight-dynamics':'Flight Dynamics','lunar-flyby':'Flight Dynamics','communications':'Mission Operations',
  'gnc':'Vehicle & GNC','manual-piloting':'Vehicle & GNC','propulsion':'Vehicle & GNC','maneuvers':'Flight Dynamics',
  'entry-dynamics':'Entry & Recovery','atmospheric-modeling':'Entry & Recovery','convective-heating':'Entry & Recovery','thermal-protection':'Entry & Recovery','parachutes-recovery':'Entry & Recovery',
  'eclss':'Vehicle & GNC','space-weather':'Environment & Radiation','radiation':'Environment & Radiation',
  'lunar-science':'Lunar Science','human-observation':'Lunar Science','impact-flashes':'Lunar Science',
  'mission-control':'Mission Operations','decision-reconstruction':'Mission Operations',
  'data-engineering':'Data & Software','data-science':'Data & Software','anomaly-detection':'Data & Software','software-architecture':'Data & Software',
  'uncertainty':'Evidence & Methods','evidence-methodology':'Evidence & Methods','psi':'Future Artemis'
};

const questionById = {
  'mission-overview':'How do the major Artemis II systems and mission phases connect on one operational timeline?',
  'flight-dynamics':'How can public trajectory products reconstruct Orion’s motion without pretending they are onboard navigation telemetry?',
  'lunar-flyby':'What can public trajectory and ephemeris data establish about Orion’s lunar flyby geometry?',
  'communications':'How do lunar geometry, ground-station visibility, and expected blackout shape communications availability?',
  'gnc':'How do guidance, navigation, and control turn desired spacecraft state into verified motion?',
  'manual-piloting':'What did Orion manual-control demonstrations exercise, and what can public evidence actually establish about them?',
  'propulsion':'What propulsion capability did Orion’s European Service Module provide, and where does public evidence stop?',
  'maneuvers':'Why can small trajectory-correction maneuvers matter so much later in the mission?',
  'entry-dynamics':'How does Orion transition from deep-space return to atmospheric entry, parachutes, splashdown, and recovery?',
  'atmospheric-modeling':'How are density, Mach, dynamic pressure, and rarefaction reconstructed along entry?',
  'convective-heating':'How can Sutton–Graves estimate entry heating without claiming measured heat-shield telemetry?',
  'thermal-protection':'What can public materials evidence and modeled heating say about Orion’s thermal-protection problem?',
  'parachutes-recovery':'How do public event anchors connect parachute deployment, splashdown, crew recovery, and spacecraft recovery?',
  'eclss':'How can public environmental and waste-management evidence be analyzed without overstating spacecraft fault knowledge?',
  'space-weather':'Why does a crewed lunar mission care about energetic-particle and solar-weather conditions?',
  'radiation':'What can public radiation models and mission geometry say about environment without becoming crew dosimetry?',
  'lunar-science':'How can crew imagery, audio, geometry, and later science products be reconstructed as one lunar-observation record?',
  'human-observation':'How does a human observation become a technically useful data product rather than just a photograph or quote?',
  'impact-flashes':'How are possible lunar impact-flash observations reconciled with timing, imagery, and science-team evidence?',
  'mission-control':'How do different Mission Control disciplines reason about the same mission state from different priorities?',
  'decision-reconstruction':'How can public evidence reconstruct operational decision logic without inventing private flight-controller conversations?',
  'data-engineering':'What data architecture makes a multi-domain public mission reconstruction auditable and reproducible?',
  'data-science':'How can robust time-series methods identify meaningful changes without turning statistics into fault claims?',
  'anomaly-detection':'What does anomaly detection legitimately tell us about spacecraft data, and what does it not tell us?',
  'software-architecture':'How does MissionLab keep analysis deterministic, testable, static, and zero-cost?',
  'uncertainty':'How should numerical uncertainty and evidence uncertainty be represented when the public record has mixed precision?',
  'evidence-methodology':'How does MissionLab keep reported facts, derived results, models, inferences, and unknowns from collapsing together?',
  'psi':'What would a defensible plume–surface interaction analysis require for a future Artemis lunar landing?'
};

const categoryOrder=['All','Flight Dynamics','Vehicle & GNC','Mission Operations','Entry & Recovery','Environment & Radiation','Lunar Science','Data & Software','Evidence & Methods','Future Artemis'];

const index = document.querySelector('#library-index');
const content = document.querySelector('#library-content');
const search = document.querySelector('#library-search');
const categories = document.querySelector('#library-categories');
const resultCount = document.querySelector('#library-result-count');
const menu = document.querySelector('.menu-btn');
const nav = document.querySelector('#nav-links');
let activeCategory='All';

if(menu&&nav) menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')==='true';menu.setAttribute('aria-expanded',String(!open));nav.classList.toggle('open',!open)});

const evidenceLegend = `<span class="evidence-pill"><i class="dot reported"></i>reported</span><span class="evidence-pill"><i class="dot"></i>derived</span><span class="evidence-pill"><i class="dot model"></i>modeled</span><span class="evidence-pill"><i class="dot unknown"></i>unknown preserved</span>`;
const searchText=t=>[t.title,t.domain,questionById[t.id],t.intro,t.relevance,t.method,t.interpret,t.ops,t.limits,t.skills.join(' ')].join(' ').toLowerCase();
const topicCategory=t=>categoryById[t.id]||'Evidence & Methods';

function relatedTopics(t){
 const same=topics.filter(other=>other.id!==t.id&&topicCategory(other)===topicCategory(t));
 if(same.length>=3)return same.slice(0,3);
 return same.concat(topics.filter(other=>other.id!==t.id&&!same.includes(other)&&other.domain.split('/')[0].trim()===t.domain.split('/')[0].trim())).slice(0,3);
}

function article(t){
 const x=extras[t.id]||{};
 const category=topicCategory(t);
 const question=questionById[t.id]||`What does ${t.title.toLowerCase()} tell us about Artemis II?`;
 const visual=x.figure?`<figure class="tech-figure deep-visual"><img src="${x.figure}" alt="${t.title} MissionLab engineering figure" loading="lazy"><figcaption><span class="caption-title">Primary MissionLab figure</span>${x.caption||''}</figcaption></figure>`:(x.caption?`<div class="note warning"><strong>Visualization boundary.</strong> ${x.caption}</div>`:'');
 const equation=x.equation?`<div class="equation">${x.equation}</div>`:'';
 const artifacts=t.artifacts.map(a=>{const dir=a.endsWith('/');const clean=dir?a.slice(0,-1):a;const kind=dir?'tree':'blob';return `<li><a class="artifact-link" href="https://github.com/Prakhar2828/a2-missionlab/${kind}/${repositoryBaseline}/${clean}">${a}</a></li>`}).join('');
 const related=relatedTopics(t).map(other=>`<a href="#${other.id}">${questionById[other.id]||other.title}</a>`).join('');
 return `<article class="deep-dive" id="${t.id}" data-category="${category}"><div class="library-back"><a href="#library-results">← Back to library results</a></div><div class="article-grid"><div class="article-main"><span class="library-article-category">${category}</span><div class="kicker">${t.domain}</div><h2>${t.title}</h2><div class="knowledge-path" aria-label="Knowledge path"><span>Question</span><span>Explanation</span><span>Evidence</span><span>Source</span></div><p class="library-question"><b>Question</b>${question}</p><div class="meta">${evidenceLegend}</div><h3>Explanation</h3><p class="lead">${t.intro}</p><h3>Why it mattered to Artemis II</h3><p>${t.relevance}</p><h3>Mission timeline / context</h3><p>${x.timeline||'This topic is correlated to the shared MissionLab mission clock; public source precision is preserved rather than silently upgraded.'}</p><h3>System, physics, or analytical method</h3><p>${t.method}</p>${equation}${visual}<h3>Inputs & outputs</h3><div class="io-grid"><div><b>Inputs</b><p>${x.inputs||'Public source records and the validated MissionLab reference artifacts linked at right.'}</p></div><div><b>Outputs</b><p>${x.outputs||'Evidence-aware derived/reference artifacts and explanatory products linked at right.'}</p></div></div><h3>Evidence and interpretation</h3><p>${t.interpret}</p><h3>Mission Control relevance</h3><p>${t.ops}</p><h3>Assumptions, uncertainty, and limitations</h3><p>${t.limits}</p><div class="library-source-block"><h3>Source and reproducibility</h3><p>Repository artifacts at right are the auditable implementation trail. The <a class="artifact-link" href="${sourceCatalogUrl}">source catalog</a> records public-source provenance; the <a class="artifact-link" href="${nasaMissionUrl}">NASA Artemis II multimedia collection</a> provides mission context. MissionLab-derived and modeled quantities remain separate from authority-reported facts.</p><div class="note"><strong>What this demonstrates technically.</strong> ${t.skills.join(' · ')}</div></div></div><aside class="article-aside"><h4>Repository evidence</h4><ul>${artifacts}</ul><h4>Capabilities</h4><ul>${t.skills.map(s=>`<li>${s}</li>`).join('')}</ul><h4>Related questions</h4><div class="related-topics">${related||'<span>No adjacent topic in this category.</span>'}</div><a class="btn" href="technical-report.html">Open Technical Report</a></aside></div></article>`;
}

function renderCategories(){
 if(!categories)return;
 categories.innerHTML=categoryOrder.map(category=>`<button class="library-filter${category===activeCategory?' active':''}" type="button" data-category="${category}" aria-pressed="${category===activeCategory}">${category}</button>`).join('');
 categories.querySelectorAll('.library-filter').forEach(button=>button.addEventListener('click',()=>{activeCategory=button.dataset.category||'All';renderBrowse();}));
}

function filteredTopics(){
 const q=(search?.value||'').trim().toLowerCase();
 return topics.filter(t=>(activeCategory==='All'||topicCategory(t)===activeCategory)&&(!q||searchText(t).includes(q)));
}

function renderBrowse(){
 renderCategories();
 const shown=filteredTopics();
 if(resultCount)resultCount.textContent=`${shown.length} of ${topics.length} deep dives`;
 if(index){
  index.innerHTML=shown.map(t=>`<a class="library-result-card" href="#${t.id}" data-topic="${t.id}"><span class="result-category">${topicCategory(t)}</span><strong>${t.title}</strong><p>${questionById[t.id]||t.intro}</p></a>`).join('');
  if(!shown.length)index.innerHTML='<div class="library-empty"><strong>No matching engineering question.</strong><p>Try a broader term or choose “All” to clear the category filter.</p></div>';
 }
 renderSelected();
}

function renderSelected(){
 if(!content)return;
 const id=location.hash.slice(1);
 const selected=topics.find(t=>t.id===id);
 if(selected){content.innerHTML=article(selected);return;}
 content.innerHTML='<div class="library-reader-intro"><strong>Select an engineering question above.</strong><p>The Library now opens one focused deep dive at a time so the path from question to explanation, evidence, and source remains clear.</p></div>';
}

search?.addEventListener('input',renderBrowse);
window.addEventListener('hashchange',()=>{renderSelected();const selected=topics.find(t=>t.id===location.hash.slice(1));if(selected){setTimeout(()=>document.getElementById(selected.id)?.scrollIntoView({behavior:'smooth',block:'start'}),20);}});
renderBrowse();
if(topics.find(t=>t.id===location.hash.slice(1)))setTimeout(()=>document.getElementById(location.hash.slice(1))?.scrollIntoView({behavior:'auto',block:'start'}),0);
})();
