const PATHS = Object.freeze({
  perspectives: './data/reference/artemis_ii_mission_control_perspectives.json',
  decisions: './data/reference/artemis_ii_decision_threads.json',
  analystIndex: './data/reference/artemis_ii_mission_analyst_index.json',
  analystInterface: './data/reference/artemis_ii_mission_analyst_interface.json',
  lunar: './data/reference/artemis_ii_lunar_observation_reconstruction.json',
  entry: './data/reference/artemis_ii_entry_events.json',
  publication: './data/reference/artemis_ii_publication_manifest.json',
  publicExperience: './data/reference/artemis_ii_public_experience.json',
  communicationsReference: './data/reference/artemis_ii_communications_events.json',
  communicationsCatalog: './data/reference/artemis_ii_communications_event_catalog.json',
  communicationsThreads: './data/reference/artemis_ii_communications_operational_threads.json',
  gncArchitecture: './data/reference/artemis_ii_gnc_architecture.json',
  gncThreads: './data/reference/artemis_ii_gnc_operational_threads.json',
  propulsion: './data/reference/artemis_ii_esm_propulsion_architecture.json',
  entryRecovery: './data/reference/artemis_ii_entry_descent_recovery_evidence.json',
  wasteManagement: './data/reference/artemis_ii_waste_management_evidence.json',
  heatingModel: './data/reference/artemis_ii_convective_heating_model.json',
});

export const TOUR_CHAPTERS = Object.freeze([
  {
    id: 'launch',
    eventId: 'A2_LAUNCH',
    phase: 'LAUNCH',
    title: 'Leaving Earth',
    body: 'Artemis II begins at Kennedy Space Center. From this moment forward, every public mission event can be placed on one shared mission clock.',
    why: 'A shared clock lets flight dynamics, spacecraft systems, communications, science, and Mission Control evidence line up without pretending that every public source has the same precision.',
    visual: 'earth',
  },
  {
    id: 'near-earth',
    eventId: 'A2_PROXIMITY_OPERATIONS',
    phase: 'EARTH ORBIT',
    title: 'Learning how Orion handles',
    body: 'Before committing fully to the lunar journey, the crew carried out proximity operations and a manual-control demonstration in the publicly reconstructed sequence.',
    why: 'Human lunar missions depend on both automation and the crew’s ability to understand and control the spacecraft. MissionLab keeps the public test evidence separate from unavailable onboard control telemetry.',
    visual: 'earth-orbit',
  },
  {
    id: 'outbound',
    eventId: 'A2_OTC3',
    phase: 'OUTBOUND',
    title: 'Fine-tuning the path to the Moon',
    body: 'Two earlier planned outbound corrections were cancelled because Orion remained sufficiently on track. Outbound Trajectory Correction 3 was retained and executed before the lunar encounter.',
    why: 'A correction burn is not evidence that something went wrong. It is part of managing a trajectory as new navigation knowledge becomes available.',
    visual: 'transfer',
  },
  {
    id: 'earthset',
    eventId: 'A2_EARTHSET',
    phase: 'LUNAR ENCOUNTER',
    title: 'Earth disappears behind the Moon',
    body: 'From Orion, Earth moved behind the lunar limb. NASA’s public Earthset image is timestamped 22:41 UTC. MissionLab keeps that reported image time distinct from its separately derived geometric contact times.',
    why: 'When the Moon blocks the direct line of sight to Earth, losing direct communications is expected geometry, not automatically a communications failure.',
    visual: 'moon',
  },
  {
    id: 'closest',
    eventId: 'A2_PERICYNTHION',
    phase: 'LUNAR ENCOUNTER',
    title: 'Closest approach',
    body: 'MissionLab refines the public trajectory to a closest lunar approach at 23:00:46 UTC, with Orion about 6,545 km above the Moon’s mean-radius surface.',
    why: 'This is the point where the lunar flyby geometry is most dramatic, but the number is MissionLab-derived from public trajectory products rather than onboard Orion telemetry.',
    visual: 'moon-close',
  },
  {
    id: 'earthrise',
    eventId: 'A2_EARTHRISE',
    phase: 'LUNAR ENCOUNTER',
    title: 'Earth returns',
    body: 'NASA’s public Earthrise image is timestamped 23:22 UTC as Earth re-emerged beyond the lunar limb.',
    why: 'The reappearance of Earth closes the occultation story visually. MissionLab does not equate the image timestamp with an exact communications reacquisition epoch unless the public evidence supports that.',
    visual: 'moon',
  },
  {
    id: 'homebound',
    eventId: 'A2_RTC1',
    phase: 'RETURN',
    title: 'Shaping the journey home',
    body: 'After the lunar encounter, return trajectory corrections fine-tuned the path toward Earth. The public sequence includes RTC1, RTC2, and RTC3.',
    why: 'Return corrections connect deep-space navigation to the narrow set of conditions required for a safe atmospheric entry.',
    visual: 'return',
  },
  {
    id: 'entry',
    eventId: 'A2_ENTRY_INTERFACE',
    phase: 'ENTRY',
    title: 'Hitting the atmosphere at lunar-return speed',
    body: 'NASA reported Entry Interface at 23:53 UTC, with Orion reaching the atmosphere at about 400,000 feet altitude.',
    why: 'A lunar-return entry has to shed enormous kinetic energy while protecting the crew, maintaining guidance, and preparing for the parachute sequence.',
    visual: 'entry',
  },
  {
    id: 'blackout',
    eventId: 'A2_ENTRY_BLACKOUT',
    phase: 'ENTRY',
    title: 'The planned radio blackout',
    body: 'NASA expected a plasma communications blackout shortly after Entry Interface, lasting about six minutes in the public sequence.',
    why: 'Ionized gas around a high-speed reentering spacecraft can interfere with radio. Planned silence during this period is different from an unexpected communications anomaly.',
    visual: 'entry-hot',
  },
  {
    id: 'splashdown',
    eventId: 'A2_SPLASHDOWN',
    phase: 'RECOVERY',
    title: 'Back on Earth',
    body: 'Drogues deployed, the three main parachutes followed, and Orion splashed down in the Pacific off the coast of San Diego.',
    why: 'The mission is not finished at atmospheric entry. Descent, splashdown, and recovery close the chain from deep-space navigation to crew return.',
    visual: 'ocean',
  },
]);

export const GALLERY_ASSETS = Object.freeze({
  systems: [
    {
      topic: 'GNC',
      title: 'How Orion knows where it is',
      description: 'Navigation and guidance architecture reconstructed from public Orion references. This is architecture, not a private onboard state history.',
      src: 'docs/assets/gnc/phase2j3_navigation_architecture.svg',
    },
    {
      topic: 'PROPULSION',
      title: 'Which propulsion system can do what',
      description: 'European Service Module propulsion architecture and evidence boundaries around maneuver assignment.',
      src: 'docs/assets/maneuvers/phase2i2_esm_propulsion_architecture.svg',
    },
    {
      topic: 'COMMUNICATIONS',
      title: 'Why the Moon can block Earth',
      description: 'Public lunar-occultation communications geometry correlated with the mission sequence.',
      src: 'docs/assets/communications/phase2g_lunar_occultation_geometry.svg',
    },
    {
      topic: 'MANUAL FLIGHT',
      title: 'Crew piloting and proximity operations',
      description: 'Publicly reconstructed manual-piloting timeline without inventing internal control-law telemetry.',
      src: 'docs/assets/gnc/phase2j2_manual_piloting_timeline.svg',
    },
  ],
  science: [
    {
      topic: 'LUNAR SCIENCE',
      title: 'What the crew observed near the Moon',
      description: 'Earthset, Earthrise, terminator observations, eclipse context, and postflight science reconciliation.',
      src: 'docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg',
    },
    {
      topic: 'SPACE WEATHER',
      title: 'The radiation environment around the mission',
      description: 'Public space-weather context assembled for Artemis II. Model and observational boundaries remain explicit.',
      src: 'docs/assets/space_weather/phase5a_space_weather_context.svg',
    },
    {
      topic: 'ENTRY SCIENCE',
      title: 'How speed changed through entry',
      description: 'MissionLab entry reconstruction visualization. It is an engineering reconstruction, not direct onboard telemetry.',
      src: 'docs/assets/entry/phase2c_entry_speed.svg',
    },
    {
      topic: 'MISSION CONTROL',
      title: 'Which disciplines cared about which events',
      description: 'The validated seven-discipline MissionLab relevance matrix across the 24-event shared timeline.',
      src: 'docs/assets/mission_control/phase7a_discipline_priority_matrix.svg',
    },
  ],
});

async function fetchJson(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Could not load ${path}: HTTP ${response.status}`);
  }
  return response.json();
}

function requireCondition(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

export async function loadMissionData() {
  const [
    perspectives,
    decisions,
    analystIndex,
    analystInterface,
    lunar,
    entry,
    publication,
    publicExperience,
    communicationsReference,
    communicationsCatalog,
    communicationsThreads,
    gncArchitecture,
    gncThreads,
    propulsion,
    entryRecovery,
    wasteManagement,
    heatingModel,
  ] = await Promise.all([
    fetchJson(PATHS.perspectives),
    fetchJson(PATHS.decisions),
    fetchJson(PATHS.analystIndex),
    fetchJson(PATHS.analystInterface),
    fetchJson(PATHS.lunar),
    fetchJson(PATHS.entry),
    fetchJson(PATHS.publication),
    fetchJson(PATHS.publicExperience),
    fetchJson(PATHS.communicationsReference),
    fetchJson(PATHS.communicationsCatalog),
    fetchJson(PATHS.communicationsThreads),
    fetchJson(PATHS.gncArchitecture),
    fetchJson(PATHS.gncThreads),
    fetchJson(PATHS.propulsion),
    fetchJson(PATHS.entryRecovery),
    fetchJson(PATHS.wasteManagement),
    fetchJson(PATHS.heatingModel),
  ]);

  requireCondition(
    perspectives.dataset_id === 'phase7a_artemis_ii_mission_control_perspectives',
    'Mission timeline dataset identity mismatch.'
  );
  requireCondition(
    Array.isArray(perspectives.shared_timeline) && perspectives.shared_timeline.length === 24,
    'MissionLab expected 24 validated shared-timeline events.'
  );
  requireCondition(
    decisions.dataset_id === 'phase7b_artemis_ii_mission_control_decision_threads',
    'Decision-thread dataset identity mismatch.'
  );
  requireCondition(
    analystIndex.dataset_id === 'phase8a_artemis_ii_mission_analyst_index',
    'Mission Analyst index identity mismatch.'
  );
  requireCondition(
    analystInterface.dataset_id === 'phase8b_artemis_ii_mission_analyst_interface',
    'Mission Analyst interface identity mismatch.'
  );
  requireCondition(
    publicExperience.dataset_id === 'public_experience_v2_artemis_ii',
    'Public Experience V2 dataset identity mismatch.'
  );
  requireCondition(
    communicationsReference.dataset_id === 'phase2g1_artemis_ii_communications_reference',
    'Communications reference dataset identity mismatch.'
  );
  requireCondition(
    communicationsCatalog.dataset_id === 'phase2h1_artemis_ii_communications_event_catalog',
    'Communications event catalog dataset identity mismatch.'
  );
  requireCondition(
    communicationsThreads.dataset_id === 'phase2h4_artemis_ii_communications_operational_threads',
    'Communications operational-thread dataset identity mismatch.'
  );

  requireCondition(
    gncArchitecture.dataset_id === 'phase2j1_artemis_ii_gnc_architecture',
    'GNC architecture dataset identity mismatch.'
  );
  requireCondition(
    propulsion.dataset_id === 'phase2i2_artemis_ii_esm_propulsion_architecture',
    'Propulsion architecture dataset identity mismatch.'
  );
  requireCondition(
    entryRecovery.dataset_id === 'phase4a1_artemis_ii_entry_descent_recovery_evidence',
    'Entry/recovery evidence dataset identity mismatch.'
  );

  return {
    perspectives,
    decisions,
    analystIndex,
    analystInterface,
    lunar,
    entry,
    publication,
    publicExperience,
    communicationsReference,
    communicationsCatalog,
    communicationsThreads,
    gncArchitecture,
    gncThreads,
    propulsion,
    entryRecovery,
    wasteManagement,
    heatingModel,
    events: perspectives.shared_timeline.slice().sort((a, b) => a.order - b.order),
    disciplines: perspectives.discipline_registry,
    decisionThreads: decisions.decision_threads,
    records: analystIndex.unified_records ?? [],
    sources: analystIndex.source_registry ?? [],
  };
}

export function getEvent(data, eventId) {
  return data.events.find((event) => event.event_id === eventId) ?? null;
}

export function eventTimeLabel(event) {
  if (!event) return 'No event selected';
  if (event.timestamp_utc) {
    return event.timestamp_utc.replace('T', ' ').replace('Z', ' UTC');
  }
  if (event.date_utc) {
    return `${event.date_utc} · ${humanize(event.time_precision ?? 'public timing only')}`;
  }
  return humanize(event.time_precision ?? 'No exact public time');
}

export function evidenceLabel(value) {
  const raw = String(value ?? 'PUBLIC EVIDENCE BOUNDARY');
  if (raw.includes('NASA') && raw.includes('MISSIONLAB')) return 'NASA + MISSIONLAB';
  if (raw.includes('NASA')) return 'NASA REPORTED';
  if (raw.includes('DERIVED')) return 'MISSIONLAB DERIVED';
  if (raw.includes('MODEL')) return 'MODEL';
  if (raw.includes('SYNTH')) return 'MISSIONLAB SYNTHESIS';
  if (raw.includes('BOUNDARY')) return 'PUBLIC EVIDENCE BOUNDARY';
  return humanize(raw);
}

export function humanize(value) {
  return String(value ?? '')
    .replaceAll('_', ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function formatMet(event) {
  return event?.met ? `MET ${event.met}` : 'MET not assigned at this public precision';
}

export function citationLabel(citation) {
  if (!citation) return 'MissionLab evidence record';
  if (citation.citation_text) return citation.citation_text;
  const parts = [citation.path, citation.locator].filter(Boolean);
  return parts.join(' :: ') || citation.dataset_id || 'MissionLab evidence record';
}
