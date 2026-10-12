import {
  citationLabel,
  evidenceLabel,
  eventTimeLabel,
  formatMet,
  humanize,
} from './mission-data.js';

const DEFAULT_RELATED = Object.freeze([
  'What happened during the lunar flyby?',
  'What was Mission Control watching during entry?',
  'What evidence does MissionLab have for that?',
]);

export const ANALYST_SUGGESTIONS = Object.freeze([
  'What is Artemis II?',
  'What happened during the lunar flyby?',
  'Why did Orion lose contact behind the Moon?',
  'What problems happened during Artemis II?',
  'How did Orion know where it was in deep space?',
  'What was Mission Control watching during entry?',
  'What did the crew observe near the Moon?',
  'What can MissionLab not know from public data?',
]);

const STOP_WORDS = new Set([
  'a','an','and','are','as','at','be','because','by','did','do','does','for',
  'from','get','had','has','have','how','i','in','into','is','it','of','on',
  'or','the','their','there','this','to','was','were','what','when','where',
  'which','who','why','with','would','during','about','mission','artemis','ii',
  'please','tell','me','can','you','could','explain','that','then','than',
]);

const SYNONYMS = Object.freeze({
  comm: ['communication', 'communications', 'radio', 'link', 'signal', 'dsn'],
  blackout: ['occultation', 'loss', 'lost', 'contact', 'signal'],
  moon: ['lunar'],
  closest: ['pericynthion', 'approach'],
  entry: ['reentry', 're-entry', 'atmosphere', 'atmospheric'],
  toilet: ['uwms', 'waste', 'wastewater', 'urine'],
  propulsion: ['engine', 'thruster', 'burn', 'maneuver', 'motor'],
  navigation: ['nav', 'position', 'velocity', 'state', 'tracking', 'where'],
  guidance: ['targeting', 'trajectory'],
  control: ['piloting', 'controller', 'attitude', 'rcs'],
  science: ['observation', 'observed', 'image', 'imagery', 'eclipse', 'flash', 'terrain'],
  heatshield: ['heat', 'shield', 'tps', 'avcoat', 'char'],
});

const EVENT_ALIASES = Object.freeze({
  A2_LAUNCH: ['launch', 'liftoff'],
  A2_UWMS_FD1_FAULT: ['toilet fault', 'flight day 1 toilet', 'uwms fault'],
  A2_UWMS_FD1_RESTORED: ['toilet restored', 'toilet recovery'],
  A2_PROXIMITY_OPERATIONS: ['proximity operations', 'manual flight test', 'manual-control demonstration'],
  A2_UWMS_FD4_VENT_ISSUE: ['wastewater vent', 'vent line', 'urine vent', 'flight day 4 vent'],
  A2_OTC3: ['otc3', 'outbound trajectory correction 3', 'outbound correction'],
  A2_LUNAR_SOI_ENTRY: ['lunar soi entry', 'sphere of influence entry', 'moon soi entry'],
  A2_EARTHSET: ['earthset'],
  A2_PERICYNTHION: ['pericynthion', 'closest approach', 'closest lunar approach'],
  A2_EARTHRISE: ['earthrise'],
  A2_TOTAL_SOLAR_ECLIPSE: ['total solar eclipse', 'lunar eclipse observation', 'solar eclipse'],
  A2_LUNAR_SOI_EXIT: ['lunar soi exit', 'sphere of influence exit', 'moon soi exit'],
  A2_RTC1: ['rtc1', 'first return correction', 'return trajectory correction 1'],
  A2_RETURN_LINK_LOSS: ['return-link loss', 'return link loss', 'flight day 9 signal loss'],
  A2_RTC2: ['rtc2', 'second return correction', 'return trajectory correction 2'],
  A2_RTC3: ['rtc3', 'final return correction', 'return trajectory correction 3'],
  A2_DSN_NSN_HANDOVER: ['dsn nsn handover', 'network handover', 'near space network handover'],
  A2_CM_SM_SEPARATION: ['service module separation', 'crew module separation', 'cm sm separation'],
  A2_ENTRY_INTERFACE: ['entry interface'],
  A2_ENTRY_BLACKOUT: ['entry blackout', 'plasma blackout', 'reentry blackout'],
  A2_ENTRY_REACQUISITION: ['entry reacquisition', 'reentry reacquisition'],
  A2_DROGUE_DEPLOYMENT: ['drogue', 'drogue deployment'],
  A2_MAIN_DEPLOYMENT: ['main parachute', 'main deployment', 'main chute'],
  A2_SPLASHDOWN: ['splashdown', 'water landing'],
});

function normalizeQuestion(value) {
  return String(value ?? '').trim().replace(/\s+/g, ' ');
}

function tokenize(value) {
  return String(value ?? '')
    .toLowerCase()
    .replace(/[’']/g, '')
    .replace(/[^a-z0-9._:-]+/g, ' ')
    .split(/\s+/)
    .map((token) => token.trim())
    .filter((token) => token.length > 1 && !STOP_WORDS.has(token));
}

function expandedTokens(value) {
  const tokens = tokenize(value);
  const expanded = new Set(tokens);
  for (const token of tokens) {
    for (const [key, synonyms] of Object.entries(SYNONYMS)) {
      if (token === key || synonyms.includes(token)) {
        expanded.add(key);
        synonyms.forEach((item) => expanded.add(item));
      }
    }
  }
  return [...expanded];
}


function editDistance(a, b, maxDistance = 2) {
  const left = String(a ?? '');
  const right = String(b ?? '');
  if (Math.abs(left.length - right.length) > maxDistance) return maxDistance + 1;

  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  const current = new Array(right.length + 1).fill(0);

  for (let i = 1; i <= left.length; i += 1) {
    current[0] = i;
    let rowMin = current[0];

    for (let j = 1; j <= right.length; j += 1) {
      const cost = left[i - 1] === right[j - 1] ? 0 : 1;
      current[j] = Math.min(
        previous[j] + 1,
        current[j - 1] + 1,
        previous[j - 1] + cost
      );
      rowMin = Math.min(rowMin, current[j]);
    }

    if (rowMin > maxDistance) return maxDistance + 1;
    for (let j = 0; j <= right.length; j += 1) previous[j] = current[j];
  }

  return previous[right.length];
}

function fuzzyContains(haystack, token) {
  const normalized = String(haystack ?? '').toLowerCase();
  if (normalized.includes(token)) return true;
  if (token.length < 5) return false;

  const words = normalized
    .replace(/[^a-z0-9]+/g, ' ')
    .split(/\s+/)
    .filter((word) => word.length >= 4 && Math.abs(word.length - token.length) <= 2);

  return words.some((word) => editDistance(word, token, token.length >= 8 ? 2 : 1) <= (token.length >= 8 ? 2 : 1));
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function includesAny(question, phrases) {
  return phrases.some((phrase) => question.includes(phrase));
}

function sourceFromCitation(citation, fallbackLabel = 'MissionLab evidence record') {
  if (!citation) {
    return {
      label: fallbackLabel,
      path: null,
      locator: null,
      evidenceClass: null,
      url: null,
    };
  }
  return {
    label: citationLabel(citation),
    path: citation.path ?? null,
    locator: citation.locator ?? null,
    evidenceClass: citation.evidence_class ?? null,
    url: citation.url ?? null,
  };
}

function localCitation(path, locator, evidenceClass, label = null, url = null) {
  return {
    label: label ?? `${path} :: ${locator}`,
    path,
    locator,
    evidenceClass,
    url,
  };
}

function eventCitation(event) {
  return localCitation(
    'data/reference/artemis_ii_mission_control_perspectives.json',
    `shared_timeline[event_id=${event.event_id}]`,
    event.evidence_class,
    `${event.name} · validated shared mission timeline`
  );
}

function threadCitation(thread) {
  return localCitation(
    'data/reference/artemis_ii_decision_threads.json',
    `decision_threads[thread_id=${thread.thread_id}]`,
    'MISSION_CONTROL_DECISION_SYNTHESIS',
    `${thread.title} · MissionLab decision thread`
  );
}

function result({
  route,
  status = 'SUPPORTED',
  headline,
  answer,
  why = '',
  evidence = [],
  facts = [],
  citations = [],
  related = DEFAULT_RELATED,
  records = [],
  context = {},
  confidence = 'HIGH',
  interpretation = '',
}) {
  return {
    route,
    status,
    headline,
    answer,
    why,
    evidence: unique(evidence),
    facts: facts.filter(Boolean),
    citations: dedupeCitations(citations.filter(Boolean)),
    related: unique(related).slice(0, 4),
    records,
    context,
    confidence,
    interpretation,
  };
}

function dedupeCitations(citations) {
  const seen = new Set();
  return citations.filter((citation) => {
    const key = `${citation.path ?? ''}|${citation.locator ?? ''}|${citation.url ?? ''}|${citation.label ?? ''}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function findEvent(data, id) {
  return data.events.find((event) => event.event_id === id) ?? null;
}

function findThread(data, id) {
  return data.decisionThreads.find((thread) => thread.thread_id === id) ?? null;
}

function findDiscipline(data, id) {
  return data.disciplines.find((discipline) => discipline.discipline_id === id) ?? null;
}

function findCommunicationsThread(data, id) {
  return data.communicationsThreads?.threads?.find((thread) => thread.thread_id === id) ?? null;
}

function findCommunicationsEvent(data, id) {
  return data.communicationsCatalog?.events?.find((event) => event.id === id) ?? null;
}

function findCommunicationsSource(data, sourceId) {
  const registries = [
    data.communicationsThreads?.sources ?? [],
    data.communicationsCatalog?.sources ?? [],
    data.communicationsReference?.sources ?? [],
  ];
  for (const registry of registries) {
    const match = registry.find((source) => source.source_id === sourceId);
    if (match) return match;
  }
  return null;
}

function communicationSourceCitation(data, sourceId, label = null) {
  const source = findCommunicationsSource(data, sourceId);
  return {
    label: label ?? source?.title ?? source?.source_title ?? sourceId,
    path: 'data/reference/artemis_ii_communications_operational_threads.json',
    locator: `source_id=${sourceId}`,
    evidenceClass: 'NASA_REPORTED',
    url: source?.url ?? null,
  };
}

function formatUtc(utc) {
  if (!utc) return null;
  return utc.replace('T', ' ').replace('Z', ' UTC');
}

function shortUtc(utc) {
  if (!utc) return null;
  return utc.slice(11, 16);
}

function minutesBetween(a, b) {
  if (!a || !b) return null;
  const delta = new Date(b).getTime() - new Date(a).getTime();
  if (!Number.isFinite(delta)) return null;
  return delta / 60000;
}

function humanDuration(minutes) {
  if (!Number.isFinite(minutes)) return null;
  const abs = Math.abs(minutes);
  if (abs < 1) return `${Math.round(abs * 60)} seconds`;
  if (abs < 60) return `${abs % 1 ? abs.toFixed(1) : Math.round(abs)} minutes`;
  const hours = Math.floor(abs / 60);
  const mins = Math.round(abs % 60);
  return mins ? `${hours} h ${mins} min` : `${hours} hours`;
}

function eventSearchText(event) {
  const aliases = EVENT_ALIASES[event.event_id] ?? [];
  return [
    event.event_id,
    event.name,
    event.summary,
    event.classification,
    event.source_dependency,
    ...(event.primary_lenses ?? []),
    ...aliases,
  ].filter(Boolean).join(' ').toLowerCase();
}

function eventMatchScore(event, question) {
  const q = question.toLowerCase();
  const qTokens = expandedTokens(question);
  const haystack = eventSearchText(event);
  let score = 0;

  for (const alias of EVENT_ALIASES[event.event_id] ?? []) {
    if (q.includes(alias)) score += 30 + alias.length / 5;
  }
  if (q.includes(event.name.toLowerCase())) score += 40;

  for (const token of qTokens) {
    if (haystack.includes(token)) score += token.length >= 5 ? 3 : 1;
    else if (fuzzyContains(haystack, token)) score += token.length >= 6 ? 4 : 1.25;
  }
  return score;
}

function resolveEvents(data, question, limit = 3) {
  return data.events
    .map((event) => ({ event, score: eventMatchScore(event, question) }))
    .filter((item) => item.score > 3)
    .sort((a, b) => b.score - a.score || a.event.order - b.event.order)
    .slice(0, limit)
    .map((item) => item.event);
}

function resolveDiscipline(data, question) {
  const q = question.toLowerCase();
  const mapping = [
    ['flight director', 'FLIGHT'],
    ['flight ', 'FLIGHT'],
    ['fdo', 'FDO'],
    ['flight dynamics', 'FDO'],
    ['fao', 'FAO'],
    ['flight activities', 'FAO'],
    ['eecom', 'EECOM'],
    ['environmental', 'EECOM'],
    ['communications', 'COMM'],
    ['communication', 'COMM'],
    ['comm ', 'COMM'],
    ['science officer', 'SCIENCE'],
    ['science', 'SCIENCE'],
    ['engineering support', 'ENGINEERING_SUPPORT'],
  ];
  for (const [phrase, id] of mapping) {
    if (q.includes(phrase)) return findDiscipline(data, id);
  }
  return null;
}

function threadSearchText(thread) {
  const stageText = Object.values(thread.stages ?? {})
    .map((stage) => stage.summary)
    .filter(Boolean)
    .join(' ');
  return [
    thread.thread_id,
    thread.title,
    thread.classification,
    stageText,
    ...(thread.anchor_event_ids ?? []),
    ...(thread.primary_lenses ?? []),
    ...(thread.guardrails ?? []),
  ].join(' ').toLowerCase();
}

function resolveThreads(data, question, limit = 3) {
  const tokens = expandedTokens(question);
  return data.decisionThreads
    .map((thread) => {
      const haystack = threadSearchText(thread);
      let score = 0;
      const q = question.toLowerCase();
      if (q.includes(thread.title.toLowerCase())) score += 35;
      for (const token of tokens) {
        if (haystack.includes(token)) score += token.length >= 5 ? 4 : 1.5;
      }
      return { thread, score };
    })
    .filter((item) => item.score > 3)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((item) => item.thread);
}

function recordSearchText(record) {
  const payload = record?.payload ?? {};
  const parts = [
    record?.record_type,
    record?.record_id,
    record?.title,
    record?.summary,
    ...(record?.search_tokens ?? []),
    payload?.name,
    payload?.title,
    payload?.classification,
    payload?.summary,
    payload?.role,
    payload?.status,
    ...(payload?.primary_lenses ?? []),
    ...(payload?.anchor_event_ids ?? []),
  ];
  return parts.filter(Boolean).join(' ').toLowerCase();
}

function recordScore(record, tokens, rawQuestion) {
  if (!tokens.length) return 0;
  const title = String(record?.title ?? '').toLowerCase();
  const summary = String(record?.summary ?? '').toLowerCase();
  const id = String(record?.record_id ?? '').toLowerCase();
  const haystack = recordSearchText(record);
  let score = 0;

  for (const token of tokens) {
    if (title.includes(token)) score += 10;
    if (id.includes(token)) score += 8;
    if (summary.includes(token)) score += 6;
    if (haystack.includes(token)) score += 2;
    else if (fuzzyContains(haystack, token)) score += token.length >= 6 ? 2.5 : .75;
  }
  const phrase = rawQuestion.toLowerCase();
  if (title && phrase.includes(title)) score += 24;
  if (record.record_type === 'event') score += 2;
  if (record.record_type === 'decision_thread') score += 2;
  return score;
}

function topRecordMatches(data, question, limit = 6) {
  const tokens = expandedTokens(question);
  return (data.records ?? [])
    .map((record) => ({
      record,
      score: recordScore(record, tokens, question),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

function recordsToCitations(records) {
  return dedupeCitations(
    records
      .map((record) => record?.citation ? sourceFromCitation(record.citation, record.title) : null)
      .filter(Boolean)
  );
}

function formatRecordSummary(record) {
  if (record?.summary) return record.summary;
  const payload = record?.payload ?? {};
  if (payload.summary) return payload.summary;
  if (payload.role) return payload.role;
  if (payload.title) return payload.title;
  return '';
}

function detectIntent(question) {
  const q = question.toLowerCase();
  if (includesAny(q, ['source', 'evidence', 'how do you know', 'where does this come from', 'citation'])) return 'EVIDENCE';
  if (includesAny(q, ['difference between', 'compare ', 'same as', 'different from'])) return 'COMPARE';
  if (includesAny(q, ['what happened before', 'what happened right before', 'what happened immediately before', 'what came before', 'before that', 'right before', 'immediately before'])) return 'BEFORE';
  if (includesAny(q, ['what happened after', 'what happened next', 'what happened right after', 'what happened immediately after', 'what came after', 'after that', 'next event', 'next after', 'right after', 'immediately after'])) return 'AFTER';
  if (includesAny(q, ['how long between', 'time between', 'elapsed between'])) return 'ELAPSED_BETWEEN';
  if (includesAny(q, ['how long', 'duration'])) return 'DURATION';
  if (includesAny(q, ['why ', 'what caused', 'cause ', 'reason'])) return 'WHY';
  if (includesAny(q, ['when ', 'what time', 'date '])) return 'WHEN';
  if (includesAny(q, ['mission control', 'fdo', 'fao', 'eecom', 'flight director', 'science officer'])) return 'MISSION_CONTROL';
  if (includesAny(q, ['navigation', 'guidance', 'gnc', 'propulsion', 'engine', 'thruster', 'sensor', 'heat shield', 'heatshield', 'parachute', 'toilet', 'uwms'])) return 'SYSTEM';
  return 'GENERAL';
}

function isContextualFollowup(question) {
  const q = question.toLowerCase();
  return (
    tokenize(question).length <= 6 &&
    includesAny(q, [
      'that', 'it', 'this', 'then', 'after', 'before', 'why', 'how', 'when',
      'what about', 'what happened next', 'what happened after'
    ])
  );
}

function contextAugmentedQuestion(question, lastContext) {
  if (!lastContext || !isContextualFollowup(question)) return question;
  const pieces = [question];
  if (lastContext.eventId) pieces.push(lastContext.eventName ?? lastContext.eventId);
  if (lastContext.threadId) pieces.push(lastContext.threadTitle ?? lastContext.threadId);
  if (lastContext.topic) pieces.push(lastContext.topic);
  return pieces.join(' ');
}

function neighboringEvents(data, event) {
  if (!event) return { before: null, after: null };
  const index = data.events.findIndex((item) => item.event_id === event.event_id);
  return {
    before: index > 0 ? data.events[index - 1] : null,
    after: index >= 0 && index < data.events.length - 1 ? data.events[index + 1] : null,
  };
}

function threadForEvent(data, eventId) {
  return data.decisionThreads.find((thread) =>
    (thread.anchor_event_ids ?? []).includes(eventId)
  ) ?? null;
}

function answerClosestApproach(data) {
  const closest = data.publicExperience.lunar_encounter.closest_approach;
  const event = findEvent(data, 'A2_PERICYNTHION');
  return result({
    route: 'EVENT',
    headline: 'Closest lunar approach',
    answer:
      `MissionLab refined closest approach to ${closest.mean_radius_altitude_km.toLocaleString(undefined, {maximumFractionDigits: 3})} km above the Moon’s mean-radius surface. ` +
      `The Moon-center distance was ${closest.moon_center_distance_km.toLocaleString(undefined, {maximumFractionDigits: 3})} km at ${formatUtc(closest.utc)}. ` +
      `Moon-relative speed was ${closest.moon_relative_speed_km_s.toFixed(6)} km/s.`,
    why:
      'This is a MissionLab-derived geometry result from public trajectory products, not a private Orion navigation-state or telemetry measurement.',
    evidence: ['MISSIONLAB DERIVED', 'PUBLIC TRAJECTORY PRODUCT'],
    citations: [
      event ? eventCitation(event) : null,
      localCitation(
        'data/reference/artemis_ii_public_experience.json',
        'lunar_encounter.closest_approach',
        'DERIVED',
        'Validated closest-approach projection'
      ),
    ],
    facts: [
      `Closest-approach UTC: ${formatUtc(closest.utc)}`,
      `Moon-center distance: ${closest.moon_center_distance_km.toFixed(3)} km`,
      `Mean-radius altitude: ${closest.mean_radius_altitude_km.toFixed(3)} km`,
      `Moon-relative speed: ${closest.moon_relative_speed_km_s.toFixed(6)} km/s`,
    ],
    related: [
      'What happened immediately before and after closest approach?',
      'Why did Orion lose contact behind the Moon?',
      'What did the crew observe near the Moon?',
    ],
    context: {
      eventId: 'A2_PERICYNTHION',
      eventName: event?.name,
      topic: 'lunar closest approach',
    },
  });
}

function answerLunarCommunicationsBlackout(data) {
  const reference = data.communicationsReference?.public_lunar_occultation_window ?? {};
  const thread = findCommunicationsThread(data, 'lunar_occultation_blackout_and_reacquisition');
  const blackout = findCommunicationsEvent(data, 'lunar_blackout_start_reported');
  const plannedReacq = findCommunicationsEvent(data, 'dsn_reacquisition_planned');
  const earthset = findCommunicationsEvent(data, 'lunar_earthset_reported');
  const earthriseLive = findCommunicationsEvent(data, 'lunar_earthrise_reported');
  const imageEarthrise = findEvent(data, 'A2_EARTHRISE');
  const blackoutStart = blackout?.timestamp_utc ?? reference.loss_of_signal_utc;
  const plannedReacqUtc = plannedReacq?.timestamp_utc ?? reference.acquisition_of_signal_utc;
  const durationMinutes = Number(reference.duration_seconds_from_public_times ?? 0) / 60;

  return result({
    route: 'COMMUNICATIONS_SYNTHESIS',
    headline: 'Orion’s lunar blackout was planned: the Moon blocked the Deep Space Network radio path',
    answer:
      `By the lunar flyby, primary deep-space communications support was through NASA’s Deep Space Network. ` +
      `NASA reported that Orion entered the planned communications blackout at ${shortUtc(blackoutStart) ?? '22:44'} UTC as the spacecraft passed behind the Moon. ` +
      `The Moon physically blocked the Earth-based DSN radio path, so Mission Control temporarily lost the normal direct RF link. ` +
      `NASA’s public plan expected reacquisition at ${shortUtc(plannedReacqUtc) ?? '23:25'} UTC, while the live update reported DSN reacquisition only as occurring moments after reported Earthrise rather than assigning an exact observed reacquisition timestamp.`,
    why:
      'This was an expected geometric communications constraint, not a spacecraft communications failure. Earth-based antennas cannot maintain a direct radio line of sight through the lunar body.',
    evidence: [
      'NASA REPORTED',
      'EXPECTED OPERATIONAL CONSTRAINT',
      'DSN RADIO-FREQUENCY COMMUNICATIONS',
      'MISSIONLAB GEOMETRY USED AS VALIDATION CONTEXT',
    ],
    facts: [
      `Reported blackout start: ${shortUtc(blackoutStart) ?? '22:44'} UTC on April 6`,
      `Public operational window: about ${durationMinutes ? Math.round(durationMinutes) : 41} minutes`,
      `Planned DSN reacquisition: ${shortUtc(plannedReacqUtc) ?? '23:25'} UTC`,
      'Live reacquisition report: moments after the live-update Earthrise; exact observed reacquisition UTC was not published in the curated evidence',
      earthset?.timestamp_utc ? `Live-update Earthset context: ${shortUtc(earthset.timestamp_utc)} UTC` : null,
      earthriseLive?.timestamp_utc ? `Live-update Earthrise context: ${shortUtc(earthriseLive.timestamp_utc)} UTC` : null,
      imageEarthrise?.timestamp_utc
        ? `Separate NASA public Earthrise image product in MissionLab: ${shortUtc(imageEarthrise.timestamp_utc)} UTC; MissionLab preserves the product-specific timing difference`
        : null,
      'O2O was a separate optical-communications demonstration and is not treated as equivalent to the primary DSN RF blackout',
    ],
    citations: [
      communicationSourceCitation(data, 'nasa_flight_day_6_live', 'NASA · Artemis II Flight Day 6: Lunar Flyby Updates'),
      communicationSourceCitation(data, 'nasa_flight_day_6_flyby_plan', 'NASA · Artemis II Flight Day 6: Crew Ready for Lunar Flyby'),
      localCitation(
        'data/reference/artemis_ii_communications_events.json',
        'public_lunar_occultation_window',
        'NASA_REPORTED',
        'MissionLab communications reference · public lunar-occultation window'
      ),
      thread ? localCitation(
        'data/reference/artemis_ii_communications_operational_threads.json',
        'threads[thread_id=lunar_occultation_blackout_and_reacquisition]',
        'NASA_REPORTED_WITH_MISSIONLAB_DERIVED_CORRELATIONS',
        'MissionLab communications operational thread · lunar blackout and reacquisition'
      ) : null,
    ],
    related: [
      'What could Mission Control see while Orion was behind the Moon?',
      'What is the difference between Earthrise and DSN reacquisition?',
      'Compare the lunar blackout with the Flight Day 9 return-link loss.',
      'What happened immediately after the lunar blackout?',
    ],
    context: { topic: 'lunar communications blackout' },
  });
}

function answerReturnLinkCausation(data) {
  const thread = findThread(data, 'RETURN_LINK_ANOMALY_RTC2');
  const linkLoss = findEvent(data, 'A2_RETURN_LINK_LOSS');
  const rtc2 = findEvent(data, 'A2_RTC2');
  return result({
    route: 'DECISION_THREAD_CAUSATION',
    status: 'SUPPORTED_WITH_CAUSATION_BOUNDARY',
    headline: 'The public record does not establish that the return-link loss caused RTC2',
    answer:
      'MissionLab can establish the sequence: NASA reported an unexpected return-link loss during a data-rate change, two-way communications were reestablished, burn preparation resumed, and RTC2 later executed. The curated public evidence does not establish that the signal loss caused RTC2 or changed the maneuver targeting.',
    why:
      '“During a data-rate change” establishes context, not root cause. Likewise, event order does not by itself establish why a trajectory correction was retained or commanded.',
    evidence: ['NASA REPORTED SEQUENCE', 'PUBLIC EVIDENCE BOUNDARY'],
    facts: [
      'Affected direction supported by the public record: return link from spacecraft to ground',
      'Complete simultaneous two-way outage: not established',
      'Exact anomaly duration: unknown in the curated public evidence',
      'Causal relationship to RTC2: not established',
    ],
    citations: [
      thread ? threadCitation(thread) : null,
      linkLoss ? eventCitation(linkLoss) : null,
      rtc2 ? eventCitation(rtc2) : null,
      localCitation(
        'data/reference/artemis_ii_communications_operational_threads.json',
        'threads[thread_id=flight_day_9_return_link_loss_and_recovery]',
        'NASA_REPORTED_WITH_MISSIONLAB_DERIVED_CORRELATIONS',
        'Flight Day 9 return-link loss and recovery thread'
      ),
    ],
    related: [
      'Compare the lunar blackout with the Flight Day 9 return-link loss.',
      'What happened during RTC2?',
      'Which engine performed RTC2?',
    ],
    context: {
      eventId: 'A2_RTC2',
      eventName: rtc2?.name,
      threadId: thread?.thread_id,
      threadTitle: thread?.title,
      topic: 'Flight Day 9 return-link loss and RTC2',
    },
  });
}

function answerVentRootCause(data) {
  const thread = findThread(data, 'FD4_WASTEWATER_VENT_RESPONSE');
  return result({
    route: 'KNOWN_UNKNOWN',
    status: 'UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE',
    headline: 'The confirmed urine vent-line root cause is not established in the curated public evidence',
    answer:
      'NASA publicly reported that wastewater venting ended earlier than expected, that the tank was not full, and that the toilet remained operational. Engineers used vent heaters, Sun-pointing, backup collection readiness, and continued investigation. Possible ice was considered, but MissionLab does not promote that hypothesis into a confirmed root cause.',
    why:
      'A troubleshooting action is evidence of what engineers tried, not proof of the physical failure mechanism.',
    evidence: ['NASA REPORTED', 'KNOWN UNKNOWN'],
    citations: [
      thread ? threadCitation(thread) : null,
      localCitation(
        'data/reference/artemis_ii_decision_threads.json',
        'postflight_open_issue_registry[URINE_VENT_LINE_ROOT_CAUSE]',
        'PUBLIC_EVIDENCE_BOUNDARY',
        'Postflight open-issue registry'
      ),
    ],
    facts: [
      'Toilet remained operational',
      'Possible ice was considered',
      'Heater use and Sun-pointing do not prove ice was the cause',
      'Confirmed root cause: unavailable in the curated public evidence',
    ],
    related: [
      'What did Mission Control do about the vent-line issue?',
      'What does EECOM focus on?',
      'What other engineering issues remained open?',
    ],
    context: {
      eventId: 'A2_UWMS_FD4_VENT_ISSUE',
      eventName: 'Flight Day 4 wastewater vent-line issue',
      threadId: thread?.thread_id,
      threadTitle: thread?.title,
      topic: 'wastewater vent-line issue',
    },
  });
}

function answerHeatShield(data) {
  const thread = findThread(data, 'TPS_RISK_MITIGATION_CLOSURE');
  return result({
    route: 'DECISION_THREAD',
    headline: 'Artemis II changed the entry environment to mitigate the known Artemis I heat-shield mechanism',
    answer:
      'NASA’s Artemis I investigation linked unexpected Avcoat char liberation to material permeability, internal gas-pressure buildup, cracking, and the Artemis I skip-entry thermal history. For Artemis II, NASA changed the entry environment with a modified trajectory rather than repeating the Artemis I-style skip entry. Initial postflight reporting described expected TPS performance and significantly reduced char loss.',
    why:
      'This is a clean engineering-risk story: identify the mechanism, change a controllable condition, fly the mitigation, and compare the postflight outcome.',
    evidence: ['NASA REPORTED', 'NASA POSTFLIGHT REPORTED'],
    citations: [thread ? threadCitation(thread) : null],
    related: [
      'What happened during entry?',
      'What was Mission Control watching during entry?',
      'What does MissionLab model about entry heating?',
    ],
    context: {
      threadId: thread?.thread_id,
      threadTitle: thread?.title,
      topic: 'Artemis II heat shield and entry mitigation',
    },
  });
}

function answerNavigation(data, question) {
  const gnc = data.gncArchitecture ?? {};
  const sensors = gnc.onboard_navigation_architecture?.sensors ?? [];
  const external = gnc.external_navigation_support ?? [];
  const q = question.toLowerCase();

  if (!includesAny(q, ['guidance', 'control', 'difference']) && includesAny(q, ['sensor', 'sensors', 'how did orion know', 'know where', 'navigation'])) {
    const names = sensors.map((sensor) => sensor.display_name);
    return result({
      route: 'SYSTEM_SYNTHESIS',
      headline: 'Orion combined onboard sensors with ground-based deep-space tracking',
      answer:
        `The public GNC architecture identifies ${names.join(', ')} as onboard navigation sensor classes. Near Earth, GPS can supply position and velocity updates. In deep space, Deep Space Network measurements support ground-based orbit determination, while onboard inertial, star-tracker, optical-navigation, and other sensors support the spacecraft’s own state knowledge.`,
      why:
        'Navigation is the “where am I, how am I moving, and which way am I pointed?” part of GNC. MissionLab can reconstruct the architecture, but it does not have Orion’s raw Artemis II sensor measurements or private onboard filter state.',
      evidence: ['NASA REPORTED ARCHITECTURE', 'PUBLIC EVIDENCE BOUNDARY'],
      facts: [
        `${sensors.length} onboard navigation sensor classes in the curated architecture`,
        `${external.length} external navigation-support class in this reconstruction`,
        'Raw Artemis II sensor measurements: not available in the curated public source set',
        'Public OEM trajectory ≠ onboard Orion navigation state',
      ],
      citations: [
        localCitation(
          'data/reference/artemis_ii_gnc_architecture.json',
          'onboard_navigation_architecture',
          gnc.provenance,
          'Orion GNC architecture · onboard navigation sensors'
        ),
        localCitation(
          'data/reference/artemis_ii_gnc_architecture.json',
          'external_navigation_support',
          gnc.provenance,
          'Orion GNC architecture · Deep Space Network tracking support'
        ),
      ],
      related: [
        'What is the difference between navigation, guidance, and control?',
        'How did optical navigation work on Orion?',
        'Did MissionLab reconstruct Orion’s onboard navigation state?',
      ],
      context: { topic: 'Orion navigation architecture' },
    });
  }

  const model = gnc.gnc_domain_model ?? {};
  return result({
    route: 'SYSTEM_SYNTHESIS',
    headline: 'GNC separates three different jobs: know the state, choose the target, control the motion',
    answer:
      'Navigation estimates where the spacecraft is, how it is moving, and how it is oriented. Guidance determines or receives where the spacecraft should go or point next. Control converts commands and errors into effector action such as thruster commands.',
    why:
      'Keeping those jobs separate prevents a common misconception: a trajectory data product is not automatically the onboard navigation state, and a known control capability is not the same as an available as-flown control-command history.',
    evidence: ['NASA REPORTED ARCHITECTURE', 'MISSIONLAB ARCHITECTURE SYNTHESIS'],
    citations: [
      localCitation(
        'data/reference/artemis_ii_gnc_architecture.json',
        'gnc_domain_model',
        gnc.provenance,
        'MissionLab GNC domain model'
      ),
    ],
    facts: Object.keys(model).map((key) => `${humanize(key)}: ${humanize(model[key]?.role ?? '')}`),
    related: [
      'How did Orion know where it was in deep space?',
      'How did the crew manually fly Orion?',
      'What GNC data is not public?',
    ],
    context: { topic: 'Orion guidance navigation and control' },
  });
}

function answerPropulsion(data, question) {
  const propulsion = data.propulsion ?? {};
  const architecture = propulsion.architecture ?? {};
  const classes = architecture.engine_classes ?? [];
  const q = question.toLowerCase();

  const burnMap = [
    ['otc3', 'otc3'],
    ['rtc1', 'rtc1'],
    ['rtc2', 'rtc2'],
    ['rtc3', 'rtc3'],
  ];
  const burn = burnMap.find(([needle]) => q.includes(needle));

  if (burn) {
    const assignment = (propulsion.correction_burn_assignments ?? [])
      .find((item) => item.maneuver_id === burn[1]);
    if (assignment && !assignment.as_flown_engine_class_id) {
      return result({
        route: 'KNOWN_UNKNOWN',
        status: 'UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE',
        headline: `MissionLab does not know which engine class performed ${burn[0].toUpperCase()}`,
        answer:
          `The public as-flown report gives ${burn[0].toUpperCase()} timing and burn performance, but it does not identify the specific propulsion engine class. MissionLab therefore preserves the assignment as unresolved rather than inferring an engine from burn duration or delta-v.`,
        why:
          'The European Service Module has multiple propulsion classes capable of different correction roles. Architecture capability, premission plans, and generic “thruster” wording are not the same as a burn-specific as-flown assignment.',
        evidence: ['NASA REPORTED', 'ESA REPORTED ARCHITECTURE', 'KNOWN UNKNOWN'],
        facts: [
          `Burn duration: ${assignment.duration_seconds} seconds`,
          assignment.reported_delta_v_ft_s != null
            ? `Reported delta-v: ${assignment.reported_delta_v_ft_s} ft/s`
            : 'Reported delta-v: unavailable in this assignment record',
          'As-flown engine class: unresolved',
        ],
        citations: [
          localCitation(
            'data/reference/artemis_ii_esm_propulsion_architecture.json',
            `correction_burn_assignments[maneuver_id=${burn[1]}]`,
            propulsion.provenance,
            `${burn[0].toUpperCase()} propulsion assignment evidence`
          ),
        ],
        related: [
          'What engines does Orion have?',
          'Which maneuvers have confirmed engine assignments?',
          'Why can’t burn duration identify the engine?',
        ],
        context: { topic: `${burn[0].toUpperCase()} propulsion assignment` },
      });
    }
  }

  return result({
    route: 'SYSTEM_SYNTHESIS',
    headline: 'Orion’s European Service Module carried 33 engines in three propulsion classes',
    answer:
      `The public architecture identifies one gimballed main engine for major in-space velocity changes, eight R-4D-11 auxiliary engines for orbital and trajectory corrections, and 24 reaction-control engines for attitude and fine control. MissionLab only assigns a specific class to an as-flown burn when a public source actually supports that assignment.`,
    why:
      'Knowing what a propulsion system can do is different from knowing which exact engine class was used for every maneuver.',
    evidence: ['NASA + ESA REPORTED ARCHITECTURE'],
    facts: classes.map((item) =>
      `${item.display_name}: ${item.count} × ${Number(item.nominal_thrust_newtons_each).toLocaleString()} N`
    ),
    citations: [
      localCitation(
        'data/reference/artemis_ii_esm_propulsion_architecture.json',
        'architecture.engine_classes',
        propulsion.provenance,
        'European Service Module propulsion architecture'
      ),
    ],
    related: [
      'Which engine performed RTC2?',
      'Which maneuvers have confirmed engine assignments?',
      'What is the difference between auxiliary engines and RCS?',
    ],
    context: { topic: 'Orion propulsion architecture' },
  });
}

function answerEntrySystem(data, question) {
  const q = question.toLowerCase();
  const entry = data.entryRecovery ?? {};
  if (includesAny(q, ['parachute', 'drogue', 'main chute', 'main parachute'])) {
    return result({
      route: 'SYSTEM_SYNTHESIS',
      headline: 'Orion used a staged parachute sequence to transition from atmospheric flight to splashdown',
      answer:
        'The validated public sequence reports drogue deployment at 23,400 feet, followed by three main parachutes at 5,400 feet, then splashdown in the Pacific. Drogues slow and stabilize the capsule before the main parachutes take over the final descent.',
      why:
        'Entry does not end when the heat shield survives peak heating. The descent system has to convert the remaining velocity into a survivable water landing.',
      evidence: ['NASA REPORTED'],
      facts: [
        'Drogues: 23,400 ft · 00:03 UTC',
        'Main parachutes: 5,400 ft · 00:04 UTC',
        'Splashdown: 00:07 UTC',
      ],
      citations: [
        localCitation(
          'data/reference/artemis_ii_entry_events.json',
          'events',
          'NASA_REPORTED',
          'Artemis II public entry and splashdown event references'
        ),
      ],
      related: [
        'What happened during Entry Interface?',
        'Why was there a plasma blackout?',
        'What happened with the heat shield?',
      ],
      context: { topic: 'Orion parachute descent and splashdown' },
    });
  }
  return answerHeatShield(data);
}

function answerEvent(data, event) {
  if (!event) return null;
  const neighbors = neighboringEvents(data, event);
  const thread = threadForEvent(data, event.event_id);
  const primary = event.primary_lenses ?? [];

  return result({
    route: 'EVENT',
    headline: event.name,
    answer:
      `${event.summary} ${eventTimeLabel(event)}. ${formatMet(event)}.`,
    why:
      `MissionLab classifies this as ${humanize(event.classification).toLowerCase()} and preserves the public timing precision instead of inventing a more exact timestamp.`,
    evidence: [evidenceLabel(event.evidence_class)],
    facts: [
      primary.length ? `Primary MissionLab lenses: ${primary.join(', ')}` : null,
      neighbors.before ? `Previous shared event: ${neighbors.before.name}` : null,
      neighbors.after ? `Next shared event: ${neighbors.after.name}` : null,
      thread ? `Related decision thread: ${thread.title}` : null,
    ],
    citations: [
      eventCitation(event),
      thread ? threadCitation(thread) : null,
    ],
    related: [
      'What happened immediately before and after this event?',
      'Why did this event matter?',
      'What was Mission Control watching here?',
    ],
    context: {
      eventId: event.event_id,
      eventName: event.name,
      threadId: thread?.thread_id,
      threadTitle: thread?.title,
      topic: event.name,
    },
  });
}

function answerWhen(data, event) {
  if (!event) return null;
  return result({
    route: 'EVENT_TIME',
    headline: `${event.name} (${event.event_id.replace(/^A2_/, "")}) timing`,
    answer: `${event.event_id.replace(/^A2_/, "")}: ${eventTimeLabel(event)}. ${formatMet(event)}.`,
    why:
      `The timing precision is ${humanize(event.time_precision).toLowerCase()}. MissionLab does not silently upgrade minute-level, approximate, or relative timing into second-level telemetry.`,
    evidence: [evidenceLabel(event.evidence_class)],
    citations: [eventCitation(event)],
    related: [
      `What happened during ${event.name}?`,
      'What happened before and after that?',
      'What evidence supports this time?',
    ],
    context: { eventId: event.event_id, eventName: event.name, topic: event.name },
  });
}

function answerChronology(data, event, direction) {
  if (!event) return null;
  const neighbors = neighboringEvents(data, event);
  const target = direction === 'BEFORE' ? neighbors.before : neighbors.after;
  if (!target) {
    return result({
      route: 'CHRONOLOGY',
      headline: direction === 'BEFORE' ? 'No earlier shared event' : 'No later shared event',
      answer: `${event.name} is at the ${direction === 'BEFORE' ? 'start' : 'end'} of the validated 24-event shared mission timeline.`,
      citations: [eventCitation(event)],
      context: { eventId: event.event_id, eventName: event.name, topic: event.name },
    });
  }
  return result({
    route: 'CHRONOLOGY',
    headline: `${direction === 'BEFORE' ? 'Before' : 'After'} ${event.name}: ${target.name}`,
    answer:
      `${target.summary} ${eventTimeLabel(target)}. On MissionLab’s shared evidence spine, this is the immediately ${direction === 'BEFORE' ? 'preceding' : 'following'} validated event.`,
    why:
      'The shared timeline is an evidence spine. Events without a defensible exact time can still appear in sequence without MissionLab inventing a timestamp.',
    evidence: [evidenceLabel(target.evidence_class)],
    citations: [eventCitation(event), eventCitation(target)],
    related: [
      `What happened during ${target.name}?`,
      'What happened next?',
      'How does MissionLab decide event order when exact times are missing?',
    ],
    context: { eventId: target.event_id, eventName: target.name, topic: target.name },
  });
}

function answerElapsedBetween(data, eventA, eventB) {
  if (!eventA || !eventB) return null;
  if (!eventA.timestamp_utc || !eventB.timestamp_utc) {
    return result({
      route: 'DETERMINISTIC_ELAPSED_TIME',
      status: 'PARTIALLY_SUPPORTED',
      headline: 'MissionLab cannot compute an exact elapsed time from these public event anchors',
      answer:
        `At least one of the two selected events does not have a defensible exact or minute-level UTC timestamp in the shared timeline. MissionLab preserves that limitation rather than assigning one.`,
      evidence: ['PUBLIC TIMING BOUNDARY'],
      citations: [eventCitation(eventA), eventCitation(eventB)],
      context: { eventId: eventB.event_id, eventName: eventB.name, topic: `${eventA.name} to ${eventB.name}` },
    });
  }
  const minutes = minutesBetween(eventA.timestamp_utc, eventB.timestamp_utc);
  return result({
    route: 'DETERMINISTIC_ELAPSED_TIME',
    headline: `${humanDuration(minutes)} between ${eventA.name} and ${eventB.name}`,
    answer:
      `${eventA.name} is anchored at ${eventTimeLabel(eventA)}, and ${eventB.name} at ${eventTimeLabel(eventB)}. The deterministic elapsed time between those public anchors is ${humanDuration(minutes)}.`,
    why:
      'The calculation uses the public timestamps exactly as curated. Its precision cannot exceed the precision of those source anchors.',
    evidence: ['DETERMINISTIC CALCULATION', evidenceLabel(eventA.evidence_class), evidenceLabel(eventB.evidence_class)],
    citations: [eventCitation(eventA), eventCitation(eventB)],
    context: { eventId: eventB.event_id, eventName: eventB.name, topic: `${eventA.name} to ${eventB.name}` },
  });
}

function answerCompareEvents(data, eventA, eventB) {
  if (!eventA || !eventB) return null;
  const delta = eventA.timestamp_utc && eventB.timestamp_utc
    ? humanDuration(minutesBetween(eventA.timestamp_utc, eventB.timestamp_utc))
    : null;
  return result({
    route: 'COMPARISON',
    headline: `${eventA.name} (${eventA.event_id.replace(/^A2_/, "")}) vs. ${eventB.name} (${eventB.event_id.replace(/^A2_/, "")})`,
    answer:
      `${eventA.name} is classified as ${humanize(eventA.classification).toLowerCase()}, while ${eventB.name} is classified as ${humanize(eventB.classification).toLowerCase()}. ` +
      `${eventA.summary} ${eventB.summary}`,
    why:
      'MissionLab compares the events by their curated public classification, timing, evidence class, and sequence. It does not infer a causal relationship merely because one happened before the other.',
    evidence: [evidenceLabel(eventA.evidence_class), evidenceLabel(eventB.evidence_class)],
    facts: [
      `${eventA.event_id.replace(/^A2_/, "")} · ${eventA.name}: ${eventTimeLabel(eventA)}`,
      `${eventB.event_id.replace(/^A2_/, "")} · ${eventB.name}: ${eventTimeLabel(eventB)}`,
      delta ? `Elapsed time between public anchors: ${delta}` : null,
      `Primary lenses for ${eventA.name}: ${(eventA.primary_lenses ?? []).join(', ') || 'none assigned'}`,
      `Primary lenses for ${eventB.name}: ${(eventB.primary_lenses ?? []).join(', ') || 'none assigned'}`,
    ],
    citations: [eventCitation(eventA), eventCitation(eventB)],
    related: [
      `Why did ${eventA.name} matter?`,
      `Why did ${eventB.name} matter?`,
      'Does the sequence establish causation?',
    ],
    context: { eventId: eventB.event_id, eventName: eventB.name, topic: `${eventA.name} compared with ${eventB.name}` },
  });
}

function answerMissionControl(data, event, discipline = null) {
  if (discipline && !event) {
    return result({
      route: 'DISCIPLINE',
      headline: discipline.display_name,
      answer:
        `${discipline.public_role_basis} In MissionLab, this lens focuses on ${(discipline.missionlab_focus ?? []).slice(0, 6).join(', ')}.`,
      why:
        (discipline.primary_questions ?? []).length
          ? `A representative question for this lens is: “${discipline.primary_questions[0]}”`
          : 'The lens organizes public evidence by operational relevance.',
      evidence: ['NASA ROLE BASIS', 'MISSIONLAB ANALYTICAL LENS'],
      facts: (discipline.primary_questions ?? []).slice(0, 3),
      citations: [
        localCitation(
          'data/reference/artemis_ii_mission_control_perspectives.json',
          `discipline_registry[discipline_id=${discipline.discipline_id}]`,
          'NASA_REPORTED_WITH_MISSIONLAB_DISCIPLINE_LENS',
          `${discipline.display_name} definition`
        ),
      ],
      related: [
        'Which events mattered most to this discipline?',
        'What was Mission Control watching during entry?',
        'What is the difference between relevance and decision authority?',
      ],
      context: { topic: discipline.display_name },
    });
  }

  if (!event) return null;
  const priorities = Object.entries(event.priorities ?? {})
    .filter(([, value]) => Number(value) >= 2)
    .sort((a, b) => Number(b[1]) - Number(a[1]));
  const relevant = priorities.map(([id, value]) => {
    const item = findDiscipline(data, id);
    return {
      id,
      value,
      name: item?.display_name ?? id,
      focus: item?.missionlab_focus?.slice(0, 3) ?? [],
    };
  });

  return result({
    route: 'MISSION_CONTROL_CONTEXT',
    headline: `Mission Control relevance at ${event.name}`,
    answer:
      `MissionLab marks ${relevant.filter((item) => item.value === 3).map((item) => item.id).join(', ') || 'no disciplines'} as primary lenses at this event. ` +
      `The public-evidence view makes ${relevant.slice(0, 5).map((item) => item.focus[0]).filter(Boolean).join(', ')} especially relevant.`,
    why:
      'These labels describe which flight-control perspectives are useful for interpreting the public evidence. They are not a claim about private console authority, calls, or internal decision rationale.',
    evidence: ['MISSION CONTROL RELEVANCE', 'NASA-BASED ROLE DEFINITIONS'],
    facts: relevant.map((item) => `${item.id}: ${item.value === 3 ? 'PRIMARY' : 'HIGH'} · ${item.focus.join(', ')}`),
    citations: [
      eventCitation(event),
      localCitation(
        'data/reference/artemis_ii_mission_control_perspectives.json',
        'discipline_registry',
        'NASA_REPORTED_WITH_MISSIONLAB_DISCIPLINE_LENSES',
        'Mission Control discipline registry'
      ),
    ],
    related: [
      'What did FDO care about here?',
      'What communications constraints existed here?',
      'What happened immediately after this event?',
    ],
    context: { eventId: event.event_id, eventName: event.name, topic: `Mission Control at ${event.name}` },
  });
}

function answerWhyFromThread(data, thread) {
  if (!thread) return null;
  const stages = thread.stages ?? {};
  const established = ['detection','evidence','constraint','decision','action','outcome']
    .map((key) => stages[key]?.summary)
    .filter(Boolean);
  return result({
    route: 'DECISION_THREAD_SYNTHESIS',
    headline: thread.title,
    answer: established.slice(0, 5).join(' '),
    why:
      'MissionLab uses the public decision-thread stages to explain what is established, what is synthesis, and what options or rationale remain private or unpublished.',
    evidence: unique(
      Object.values(stages).map((stage) => evidenceLabel(stage?.evidence_class))
    ),
    facts: [
      ...(thread.guardrails ?? []).slice(0, 4),
      stages.options?.status === 'NOT_PUBLICLY_ENUMERATED'
        ? 'Complete internal option set: not publicly enumerated'
        : null,
    ],
    citations: [threadCitation(thread)],
    related: [
      'What evidence supports this?',
      'What part of the rationale is not public?',
      'What happened before and after this thread?',
    ],
    context: { threadId: thread.thread_id, threadTitle: thread.title, topic: thread.title },
  });
}

function answerEvidence(data, question, events, threads, matches) {
  const citations = [
    ...events.map(eventCitation),
    ...threads.map(threadCitation),
    ...recordsToCitations(matches.map((item) => item.record)),
  ];
  const evidenceClasses = unique([
    ...events.map((event) => evidenceLabel(event.evidence_class)),
    ...matches.map((item) => evidenceLabel(item.record?.citation?.evidence_class)),
  ]);

  if (!citations.length) {
    return result({
      route: 'EVIDENCE',
      status: 'UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE',
      headline: 'I could not identify a strong evidence target in that question',
      answer:
        'MissionLab has evidence records, but this question does not resolve cleanly to a specific event, thread, system, or source. I would rather expose that ambiguity than pretend I know which claim you mean.',
      evidence: ['KNOWN UNKNOWN'],
      related: ANALYST_SUGGESTIONS.slice(0, 4),
      confidence: 'LOW',
    });
  }

  return result({
    route: 'EVIDENCE',
    headline: 'Here is the evidence MissionLab is using',
    answer:
      `The strongest matches resolve to ${events.map((e) => e.name).concat(threads.map((t) => t.title)).concat(matches.slice(0, 3).map((m) => m.record.title)).filter(Boolean).join('; ')}.`,
    why:
      'MissionLab keeps source metadata, evidence class, dataset path, and locator visible so the answer can be audited instead of accepted on trust.',
    evidence: evidenceClasses,
    citations,
    facts: matches.slice(0, 4).map((item) => `${item.record.record_type}: ${item.record.title ?? item.record.record_id}`),
    related: [
      'Which part of this answer is NASA-reported?',
      'Which part is MissionLab-derived?',
      'What is still unknown?',
    ],
    records: matches.map((item) => item.record),
    confidence: matches[0]?.score > 15 || events.length || threads.length ? 'HIGH' : 'MEDIUM',
  });
}


function looksMissionRelated(question) {
  return includesAny(String(question ?? '').toLowerCase(), [
    'artemis', 'orion', 'nasa', 'moon', 'lunar', 'space', 'mission', 'crew', 'astronaut',
    'launch', 'entry', 'reentry', 'splashdown', 'parachute', 'heat shield', 'avcoat',
    'dsn', 'deep space network', 'near space network', 'o2o', 'communication', 'blackout',
    'rtc', 'trajectory', 'burn', 'maneuver', 'engine', 'propulsion', 'thruster',
    'guidance', 'navigation', 'control', 'gnc', 'mission control', 'flight director', 'fdo',
    'earthrise', 'earthset', 'pericynthion', 'closest approach', 'eclipse', 'occultation',
    'toilet', 'waste', 'vent', 'science', 'radiation', 'space weather',
  ]);
}

function answerFriendlyRedirect() {
  return result({
    route: 'CONVERSATION',
    status: 'OUTSIDE_MISSIONLAB_SCOPE',
    headline: 'I’m mainly your Artemis II copilot',
    answer:
      'I can still chat normally, but this app is built around Artemis II and the public evidence MissionLab reconstructed. If you throw me a mission or spaceflight question — even a super basic one — I’ll take it from there without making you learn special commands.',
    why:
      'Keeping mission-specific answers tied to the validated evidence is what makes MissionLab trustworthy.',
    evidence: [],
    citations: [],
    related: [
      'What is Artemis II?',
      'Tell me something cool.',
      'Why did Orion go behind the Moon?',
      'What did Mission Control care about?',
    ],
    confidence: 'HIGH',
    context: { topic: 'MissionLab scope' },
  });
}

function genericSynthesis(data, question, matches, events, threads) {
  const top = matches.slice(0, 5);
  const strong = top[0]?.score ?? 0;
  const second = top[1]?.score ?? 0;
  const confidence = strong >= 20 ? 'HIGH' : strong >= 10 ? 'MEDIUM' : 'LOW';

  if (!top.length && !events.length && !threads.length) {
    return result({
      route: 'SEARCH_SYNTHESIS',
      status: 'UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE',
      headline: 'MissionLab cannot establish that from the curated public evidence',
      answer:
        'I could not resolve that question to a sufficiently relevant validated MissionLab record. I will not fill the gap with a guess.',
      why:
        'Try naming the event, system, mission phase, Mission Control discipline, or engineering issue you have in mind. If the evidence still does not support an answer, MissionLab will say so.',
      evidence: ['KNOWN UNKNOWN'],
      related: ANALYST_SUGGESTIONS.slice(0, 4),
      confidence: 'LOW',
    });
  }

  if (confidence === 'LOW' || (strong < 12 && Math.abs(strong - second) < 2)) {
    const candidates = unique([
      ...events.map((event) => event.name),
      ...threads.map((thread) => thread.title),
      ...top.slice(0, 4).map((item) => item.record.title ?? item.record.record_id),
    ]);
    return result({
      route: 'SEARCH_SYNTHESIS',
      status: 'RELATED_EVIDENCE_FOUND',
      headline: 'I found related evidence, but not enough to answer that precisely',
      answer:
        `The closest validated MissionLab topics are ${candidates.join('; ')}. I do not have enough confidence to collapse those into one answer without risking a misleading interpretation.`,
      why:
        'MissionLab uses confidence gating so a fuzzy search match does not become a confident scientific claim.',
      evidence: unique(top.map((item) => evidenceLabel(item.record?.citation?.evidence_class))),
      citations: recordsToCitations(top.map((item) => item.record)),
      facts: candidates,
      related: ANALYST_SUGGESTIONS.slice(0, 4),
      records: top.map((item) => item.record),
      confidence: 'LOW',
    });
  }

  const summaries = unique(top.map((item) => formatRecordSummary(item.record)).filter(Boolean)).slice(0, 3);
  const headline = events[0]?.name ?? threads[0]?.title ?? top[0]?.record?.title ?? 'MissionLab evidence synthesis';

  return result({
    route: 'SEARCH_SYNTHESIS',
    status: 'SUPPORTED_RECORD_SYNTHESIS',
    headline,
    answer:
      summaries.length
        ? summaries.join(' ')
        : `The strongest validated matches are ${top.slice(0, 3).map((item) => item.record.title || item.record.record_id).join('; ')}.`,
    why:
      'This answer is synthesized only from matched validated records. Retrieval relevance does not authorize MissionLab to add facts that are not present in those records.',
    evidence: unique(top.map((item) => evidenceLabel(item.record?.citation?.evidence_class))),
    citations: [
      ...events.slice(0, 2).map(eventCitation),
      ...threads.slice(0, 1).map(threadCitation),
      ...recordsToCitations(top.map((item) => item.record)),
    ],
    facts: top.slice(0, 4).map((item) => `${item.record.record_type}: ${item.record.title ?? item.record.record_id}`),
    related: DEFAULT_RELATED,
    records: top.map((item) => item.record),
    confidence,
    context: events[0]
      ? { eventId: events[0].event_id, eventName: events[0].name, topic: events[0].name }
      : threads[0]
        ? { threadId: threads[0].thread_id, threadTitle: threads[0].title, topic: threads[0].title }
        : { topic: headline },
  });
}


function answerLunarMissionControlVisibility(data) {
  const thread = findCommunicationsThread(data, 'lunar_occultation_blackout_and_reacquisition');
  const reference = data.communicationsReference?.public_lunar_occultation_window ?? {};

  return result({
    route: 'COMMUNICATIONS_SYNTHESIS',
    headline: 'Mission Control temporarily lost the normal live DSN radio path — not control of Orion',
    answer:
      'During the planned lunar blackout, the Moon physically blocked the direct radio line of sight between Orion and Earth-based Deep Space Network antennas. That means Mission Control could not receive the normal live DSN radio/telemetry path through the lunar body. It does not mean Orion lost its onboard navigation, guidance, control, or ability to continue the planned flyby.',
    why:
      'Ground contact and spacecraft autonomy are different things. Public evidence establishes the expected communications constraint, but it does not publish every private console display, stored-data behavior, alternate-link status, or internal crew/ground procedure used during the blackout.',
    evidence: [
      'NASA REPORTED',
      'EXPECTED OPERATIONAL CONSTRAINT',
      'PUBLIC CONSOLE-EVIDENCE BOUNDARY',
    ],
    facts: [
      `Public blackout reference: ${shortUtc(reference.loss_of_signal_utc) ?? '22:44'} UTC`,
      `Planned reacquisition reference: ${shortUtc(reference.acquisition_of_signal_utc) ?? '23:25'} UTC`,
      'Normal direct Earth-based DSN RF line of sight: blocked by the Moon',
      'Onboard Orion navigation/control loss: not implied by communications blackout',
      'Exact private Mission Control console state during blackout: not available in the curated public evidence',
    ],
    citations: [
      communicationSourceCitation(
        data,
        'nasa_flight_day_6_live',
        'NASA · Artemis II Flight Day 6: Lunar Flyby Updates'
      ),
      localCitation(
        'data/reference/artemis_ii_communications_events.json',
        'public_lunar_occultation_window',
        'NASA_REPORTED',
        'MissionLab communications reference · lunar occultation window'
      ),
      thread ? localCitation(
        'data/reference/artemis_ii_communications_operational_threads.json',
        'threads[thread_id=lunar_occultation_blackout_and_reacquisition]',
        'NASA_REPORTED_WITH_MISSIONLAB_DERIVED_CORRELATIONS',
        'Lunar blackout and reacquisition operational thread'
      ) : null,
    ],
    related: [
      'What is the difference between Earthrise and DSN reacquisition?',
      'How did Orion know where it was while behind the Moon?',
      'Was O2O available during the lunar blackout?',
      'Compare the lunar blackout with the Flight Day 9 return-link loss.',
    ],
    context: { topic: 'Mission Control during lunar communications blackout' },
  });
}

function answerEarthriseVsReacquisition(data) {
  const imageEarthrise = data.publicExperience?.lunar_encounter?.reported_earthrise_utc;
  const liveEarthrise = findCommunicationsEvent(data, 'lunar_earthrise_reported');
  const plannedReacq = findCommunicationsEvent(data, 'dsn_reacquisition_planned');
  const liveReacq = findCommunicationsEvent(data, 'dsn_reacquisition_live_report');

  return result({
    route: 'COMPARISON',
    headline: 'Earthrise and DSN reacquisition are related, but they are not the same event',
    answer:
      'Earthrise is a viewing/geometry event: Earth re-emerges beyond the lunar limb from Orion’s perspective. DSN reacquisition is an operational communications event: Earth-based Deep Space Network antennas regain the radio link. NASA’s live communications update reports Earthrise at 23:24 UTC and says DSN reacquired Orion moments afterward, while the pre-flyby plan expected reacquisition at 23:25 UTC. Separately, MissionLab preserves a NASA public Earthrise image product timestamped 23:22 UTC.',
    why:
      'Different NASA products can timestamp different aspects of the same encounter. MissionLab keeps image capture, geometric context, planned network timing, and observed communications reacquisition separate instead of forcing them into one artificial exact time.',
    evidence: ['NASA REPORTED', 'PRODUCT-SPECIFIC TIMING', 'PUBLIC TIMING BOUNDARY'],
    facts: [
      imageEarthrise ? `NASA public Earthrise image product: ${shortUtc(imageEarthrise)} UTC` : null,
      liveEarthrise?.timestamp_utc ? `Live communications-update Earthrise: ${shortUtc(liveEarthrise.timestamp_utc)} UTC` : null,
      plannedReacq?.timestamp_utc ? `Planned DSN reacquisition: ${shortUtc(plannedReacq.timestamp_utc)} UTC` : null,
      liveReacq ? 'Observed DSN reacquisition: reported only as moments after Earthrise; no exact UTC assigned' : null,
      'Earthrise ≠ exact DSN reacquisition',
    ],
    citations: [
      communicationSourceCitation(
        data,
        'nasa_flight_day_6_live',
        'NASA · Artemis II Flight Day 6: Lunar Flyby Updates'
      ),
      communicationSourceCitation(
        data,
        'nasa_flight_day_6_flyby_plan',
        'NASA · Artemis II Flight Day 6: Crew Ready for Lunar Flyby'
      ),
      localCitation(
        'data/reference/artemis_ii_lunar_observation_reconstruction.json',
        'observation_records[observation_id=A2_LUNAR_EARTHRISE]',
        'NASA_REPORTED_PLUS_MISSIONLAB_GEOMETRY_CORRELATION',
        'NASA Earthrise image product preserved by MissionLab'
      ),
    ],
    related: [
      'Why did Orion lose contact behind the Moon?',
      'How long did the lunar communications blackout last?',
      'What could Mission Control see while Orion was behind the Moon?',
    ],
    context: { topic: 'Earthrise versus DSN communications reacquisition' },
  });
}

function answerLunarFlybyOverview(data) {
  const ids = [
    'A2_LUNAR_SOI_ENTRY',
    'A2_EARTHSET',
    'A2_PERICYNTHION',
    'A2_EARTHRISE',
    'A2_TOTAL_SOLAR_ECLIPSE',
    'A2_LUNAR_SOI_EXIT',
  ];
  const events = ids.map((id) => findEvent(data, id)).filter(Boolean);
  const closest = data.publicExperience?.lunar_encounter?.closest_approach;

  return result({
    route: 'MISSION_PHASE_SYNTHESIS',
    headline: 'The lunar flyby was a sequence of geometry, communications, and science events',
    answer:
      'Orion entered MissionLab’s derived lunar sphere-of-influence boundary, approached the Moon, watched Earth set behind the lunar limb, passed through the planned DSN communications blackout, reached closest approach, saw Earth return, carried out lunar/eclipse science observations, and later exited the lunar SOI on the homebound leg. The flyby is best understood as one connected operational sequence rather than a single “closest approach” moment.',
    why:
      'The same geometry simultaneously affected trajectory, communications, crew observations, and Mission Control context. MissionLab keeps NASA-reported observations separate from derived geometric milestones while showing how they fit together.',
    evidence: ['NASA REPORTED', 'MISSIONLAB DERIVED GEOMETRY', 'NASA POSTFLIGHT SCIENCE'],
    facts: [
      events[0] ? `Lunar SOI entry: ${eventTimeLabel(events[0])}` : null,
      findEvent(data, 'A2_EARTHSET') ? `Earthset image: ${eventTimeLabel(findEvent(data, 'A2_EARTHSET'))}` : null,
      closest ? `Closest lunar altitude: ${closest.mean_radius_altitude_km.toFixed(3)} km above mean-radius surface` : null,
      findEvent(data, 'A2_EARTHRISE') ? `Earthrise image: ${eventTimeLabel(findEvent(data, 'A2_EARTHRISE'))}` : null,
      events.at(-1) ? `Lunar SOI exit: ${eventTimeLabel(events.at(-1))}` : null,
    ],
    citations: [
      ...events.slice(0, 5).map(eventCitation),
      localCitation(
        'data/reference/artemis_ii_communications_operational_threads.json',
        'threads[thread_id=lunar_occultation_blackout_and_reacquisition]',
        'NASA_REPORTED_WITH_MISSIONLAB_DERIVED_CORRELATIONS',
        'Lunar communications blackout/reacquisition operational thread'
      ),
      localCitation(
        'data/reference/artemis_ii_lunar_observation_reconstruction.json',
        'observation_records',
        'NASA_REPORTED_PLUS_MISSIONLAB_GEOMETRY_CORRELATION',
        'Lunar science observation reconstruction'
      ),
    ],
    related: [
      'Why did Orion lose contact behind the Moon?',
      'How close did Orion get to the Moon?',
      'What did the crew observe near the Moon?',
      'What happened after closest approach?',
    ],
    context: { eventId: 'A2_PERICYNTHION', eventName: 'Pericynthion', topic: 'lunar flyby sequence' },
  });
}

function answerMissionIssuesOverview(data) {
  const anomalyThreads = data.decisionThreads.filter((thread) => thread.anomaly === true);
  const labels = anomalyThreads.map((thread) => thread.title);

  return result({
    route: 'MISSION_ISSUE_SYNTHESIS',
    headline: 'The public record shows a few managed issues — not one mission-wide failure',
    answer:
      'MissionLab’s public evidence captures several non-nominal items: a Flight Day 1 toilet fault indication that was troubleshot and restored, a Flight Day 4 wastewater vent-line issue that was managed while its root cause remained unresolved in the curated public record, and an unexpected Flight Day 9 return-link loss that recovered before RTC2. These should not be conflated with expected constraints such as the lunar or entry communications blackouts.',
    why:
      '“Something went wrong” is too broad for mission engineering. MissionLab separates anomalies, troubleshooting, expected operational constraints, and known unknowns so each issue keeps the right meaning.',
    evidence: ['NASA REPORTED', 'MISSIONLAB DECISION SYNTHESIS', 'KNOWN UNKNOWNS PRESERVED'],
    facts: labels.slice(0, 5),
    citations: anomalyThreads.slice(0, 4).map(threadCitation),
    related: [
      'What was the root cause of the urine vent-line issue?',
      'What happened with the Flight Day 1 toilet fault?',
      'Did the return-link loss cause RTC2?',
      'Which communications blackouts were expected?',
    ],
    context: { topic: 'Artemis II publicly reported anomalies and managed issues' },
  });
}

function answerMissionOverview(data) {
  const launch = findEvent(data, 'A2_LAUNCH');
  const closest = findEvent(data, 'A2_PERICYNTHION');
  const splash = findEvent(data, 'A2_SPLASHDOWN');

  return result({
    route: 'MISSION_OVERVIEW',
    headline: 'Artemis II carried a crew from Earth, around the Moon, and back through a full lunar-return entry',
    answer:
      'MissionLab follows the mission from launch and near-Earth checkout through manual-control/proximity operations, outbound trajectory management, the lunar flyby and science sequence, return corrections, atmospheric entry, communications blackout and reacquisition, parachute descent, and Pacific splashdown. The project then layers Mission Control perspectives, engineering decision threads, and public postflight evidence on top of that shared timeline.',
    why:
      'The mission becomes much easier to understand when trajectory, spacecraft systems, communications, science, and recovery are viewed on one evidence-grounded clock.',
    evidence: ['NASA REPORTED', 'MISSIONLAB DERIVED WHERE LABELED'],
    facts: [
      launch ? `Launch: ${eventTimeLabel(launch)}` : null,
      closest ? `Closest approach: ${eventTimeLabel(closest)}` : null,
      splash ? `Splashdown: ${eventTimeLabel(splash)}` : null,
      `${data.events.length} validated shared mission events`,
      `${data.decisionThreads.length} evidence-grounded decision threads`,
    ],
    citations: [
      launch ? eventCitation(launch) : null,
      closest ? eventCitation(closest) : null,
      splash ? eventCitation(splash) : null,
      localCitation(
        'data/reference/artemis_ii_mission_control_perspectives.json',
        'shared_timeline',
        'NASA_REPORTED_WITH_MISSIONLAB_SYNTHESIS',
        'Validated shared Artemis II mission timeline'
      ),
    ],
    related: [
      'Take me through the lunar flyby.',
      'What problems happened during the mission?',
      'What was Mission Control watching during entry?',
      'What science did the crew do near the Moon?',
    ],
    context: { eventId: 'A2_LAUNCH', eventName: 'Launch', topic: 'Artemis II mission overview' },
  });
}

function answerEntryOverview(data) {
  const ids = [
    'A2_CM_SM_SEPARATION',
    'A2_ENTRY_INTERFACE',
    'A2_ENTRY_BLACKOUT',
    'A2_ENTRY_REACQUISITION',
    'A2_DROGUE_DEPLOYMENT',
    'A2_MAIN_DEPLOYMENT',
    'A2_SPLASHDOWN',
  ];
  const events = ids.map((id) => findEvent(data, id)).filter(Boolean);

  return result({
    route: 'MISSION_PHASE_SYNTHESIS',
    headline: 'Entry converted lunar-return speed into a controlled parachute descent and splashdown',
    answer:
      'Orion separated the crew module from the service module, reached Entry Interface, passed through the expected plasma communications blackout, reacquired communications, deployed drogue parachutes, deployed three main parachutes, and splashed down in the Pacific. The sequence links trajectory targeting, thermal protection, communications, guidance, descent systems, and recovery.',
    why:
      'A successful lunar mission is not complete when the spacecraft reaches Earth. Entry and descent are a tightly coupled safety-critical phase where several systems and Mission Control disciplines matter at once.',
    evidence: ['NASA REPORTED', 'MISSIONLAB ENTRY CONTEXT'],
    facts: events.map((event) => `${event.name}: ${eventTimeLabel(event)}`),
    citations: [
      ...events.map(eventCitation),
      localCitation(
        'data/reference/artemis_ii_entry_events.json',
        'events',
        'NASA_REPORTED',
        'NASA public entry and splashdown event anchors'
      ),
    ],
    related: [
      'Why was there an entry communications blackout?',
      'What happened with the heat shield?',
      'How did the parachutes work?',
      'What was Mission Control watching during entry?',
    ],
    context: { eventId: 'A2_ENTRY_INTERFACE', eventName: 'Entry Interface', topic: 'Artemis II entry sequence' },
  });
}

function answerCommunicationsArchitecture(data) {
  const architecture = data.communicationsReference?.communications_architecture ?? {};
  return result({
    route: 'SYSTEM_SYNTHESIS',
    headline: 'Artemis II used different communications systems as the mission moved from near Earth to deep space',
    answer:
      'NASA’s public architecture identifies the Near Space Network for multiple near-Earth phases and the Deep Space Network as the primary deep-space communications support after translunar injection. Orion also carried O2O, a separate optical communications demonstration. MissionLab does not treat O2O as interchangeable with the mission’s primary RF communications path.',
    why:
      'Network, frequency/medium, geometry, and mission phase all matter. Saying “communications” without distinguishing NSN, DSN, and O2O can hide the engineering story.',
    evidence: ['NASA REPORTED COMMUNICATIONS ARCHITECTURE'],
    facts: [
      architecture.near_earth_network?.role,
      architecture.deep_space_network?.role,
      architecture.optical_demonstration?.role,
      'O2O optical-link availability ≠ DSN RF-link availability',
    ],
    citations: [
      localCitation(
        'data/reference/artemis_ii_communications_events.json',
        'communications_architecture',
        'NASA_REPORTED',
        'Artemis II public communications architecture'
      ),
    ],
    related: [
      'Why did Orion lose contact behind the Moon?',
      'What is O2O?',
      'When did communications transition from NSN to DSN?',
      'What happened during the Flight Day 9 return-link loss?',
    ],
    context: { topic: 'Artemis II communications architecture' },
  });
}

function answerEvidenceBoundaries(data) {
  return result({
    route: 'EVIDENCE_BOUNDARY',
    headline: 'MissionLab is designed to show where the public record stops',
    answer:
      'The project can reconstruct public trajectory geometry, event timing, mission sequence, system architecture, engineering context, and source-backed operational threads. It does not possess private Orion telemetry, raw onboard navigation-filter state, controller gains, internal guidance laws, private console transcripts, complete flight-director rationale trees, or undocumented anomaly root causes.',
    why:
      'A polished visualization can make reconstructed data look more authoritative than it is. MissionLab keeps reported facts, derived calculations, models, synthesis, and unknowns visibly separate so the interface does not turn missing evidence into fake certainty.',
    evidence: ['PUBLIC EVIDENCE BOUNDARY', 'KNOWN UNKNOWNS'],
    facts: [
      'Public trajectory product ≠ onboard navigation state',
      'System capability ≠ as-flown command history',
      'Temporal sequence ≠ causation',
      'Discipline relevance ≠ decision authority',
      'Troubleshooting action ≠ confirmed root cause',
    ],
    citations: [
      localCitation(
        'data/reference/artemis_ii_mission_analyst_index.json',
        'dependency_registry',
        'PUBLIC_EVIDENCE_BOUNDARY',
        'Mission Analyst evidence registry'
      ),
      localCitation(
        'data/reference/artemis_ii_decision_threads.json',
        'critical_non_equivalences',
        'PUBLIC_EVIDENCE_BOUNDARY',
        'MissionLab critical evidence non-equivalences'
      ),
    ],
    related: [
      'Which facts are MissionLab-derived instead of NASA-reported?',
      'What GNC data is not public?',
      'What root causes are still unknown?',
      'How do you know the answers are evidence-grounded?',
    ],
    context: { topic: 'MissionLab evidence boundaries' },
  });
}

function answerRiskQuestion(data) {
  const launch = findEvent(data, 'A2_LAUNCH');
  const entry = findEvent(data, 'A2_ENTRY_INTERFACE');
  return result({
    route: 'EVIDENCE_BOUNDARY',
    status: 'NOT_OBJECTIVELY_RANKED_IN_PUBLIC_EVIDENCE',
    headline: 'MissionLab cannot honestly rank one phase as “the most dangerous” from the curated public evidence',
    answer:
      'Launch and lunar-return entry are clearly high-consequence dynamic phases, and many other phases carry their own hazards and constraints. But the curated public sources do not provide a single quantitative mission-wide risk ranking that would justify declaring one moment the objectively most dangerous.',
    why:
      'A compelling app should not turn engineering intuition into an unsupported ranking. MissionLab can explain the hazards and constraints of each phase without pretending to know NASA’s complete private risk posture.',
    evidence: ['PUBLIC EVIDENCE BOUNDARY', 'MISSION CONTROL RELEVANCE'],
    facts: [
      launch ? `Launch is classified as ${humanize(launch.classification)}` : null,
      entry ? `Entry Interface is classified as ${humanize(entry.classification)}` : null,
      'Private integrated mission-risk ranking: not available in the curated public evidence',
    ],
    citations: [
      launch ? eventCitation(launch) : null,
      entry ? eventCitation(entry) : null,
    ],
    related: [
      'Why is lunar-return entry difficult?',
      'What was Mission Control watching during entry?',
      'What problems actually happened during Artemis II?',
    ],
    confidence: 'HIGH',
    context: { topic: 'mission risk and evidence limits' },
  });
}

function compareLunarAndReturnLink(data) {
  const lunar = findCommunicationsThread(data, 'lunar_occultation_blackout_and_reacquisition');
  const returnLink = findCommunicationsThread(data, 'flight_day_9_return_link_loss_and_recovery');
  return result({
    route: 'COMPARISON',
    headline: 'The lunar blackout and the Flight Day 9 return-link loss were fundamentally different',
    answer:
      'The lunar blackout was expected and geometry-driven: the Moon blocked the Earth-based DSN radio path during the flyby. The Flight Day 9 return-link loss was unexpected, occurred during a data-rate change, affected spacecraft-to-ground communications/telemetry, and recovered before RTC2. The public evidence does not establish its exact root cause.',
    why:
      'MissionLab deliberately separates expected operational constraints from anomalies. Treating both as “communication loss” would erase the engineering distinction.',
    evidence: ['NASA REPORTED', 'EXPECTED CONSTRAINT', 'UNEXPECTED ANOMALY', 'PUBLIC EVIDENCE BOUNDARY'],
    facts: [
      'Lunar blackout: expected, geometry-driven, DSN RF path blocked by Moon',
      'Flight Day 9 return-link loss: unexpected anomaly during data-rate change',
      'Lunar blackout timing: public minute-level operational window',
      'Flight Day 9 exact anomaly duration and failed subsystem: not established',
    ],
    citations: [
      lunar ? localCitation(
        'data/reference/artemis_ii_communications_operational_threads.json',
        'threads[thread_id=lunar_occultation_blackout_and_reacquisition]',
        'NASA_REPORTED_WITH_MISSIONLAB_DERIVED_CORRELATIONS',
        'Lunar occultation blackout and reacquisition thread'
      ) : null,
      returnLink ? localCitation(
        'data/reference/artemis_ii_communications_operational_threads.json',
        'threads[thread_id=flight_day_9_return_link_loss_and_recovery]',
        'NASA_REPORTED_WITH_MISSIONLAB_DERIVED_CORRELATIONS',
        'Flight Day 9 return-link loss and recovery thread'
      ) : null,
    ],
    related: [
      'Why did Orion lose contact behind the Moon?',
      'Did the return-link loss cause RTC2?',
      'What exactly was lost during the Flight Day 9 anomaly?',
    ],
    context: { topic: 'communications-loss comparison' },
  });
}

export function isMissionEvidenceEngine() {
  return true;
}

export class MissionAnalyst {
  constructor(data) {
    this.data = data;
    this.lastContext = null;
    this.history = [];
  }

  remember(question, answer) {
    this.lastContext = answer.context ?? this.lastContext;
    this.history.push({ question, answer });
    if (this.history.length > 12) this.history.shift();
    return answer;
  }

  evidencePacket(rawQuestion, { selectedEventId = null } = {}) {
    const question = normalizeQuestion(rawQuestion);
    const augmented = contextAugmentedQuestion(question, this.lastContext);
    const events = resolveEvents(this.data, augmented, 5);
    const threads = resolveThreads(this.data, augmented, 3);
    const discipline = resolveDiscipline(this.data, augmented);
    const matches = topRecordMatches(this.data, augmented, 10);
    const selectedEvent = selectedEventId
      ? findEvent(this.data, selectedEventId)
      : null;

    const deterministic = this.answer(question);

    const compactEvent = (event) => event ? {
      event_id: event.event_id,
      name: event.name,
      phase: event.phase,
      utc: event.utc,
      met: event.met,
      classification: event.classification,
      provenance: event.provenance,
      public_summary: event.public_summary ?? event.summary ?? null,
    } : null;

    const compactThread = (thread) => thread ? {
      thread_id: thread.thread_id,
      title: thread.title,
      classification: thread.classification,
      anchor_event_ids: thread.anchor_event_ids ?? [],
      primary_lenses: thread.primary_lenses ?? [],
      stages: Object.fromEntries(
        Object.entries(thread.stages ?? {}).map(([key, value]) => [
          key,
          value?.summary ?? value
        ])
      ),
      guardrails: (thread.guardrails ?? []).slice(0, 5),
    } : null;

    const compactRecord = (item) => {
      const record = item.record;
      return {
        score: item.score,
        record_type: record.record_type,
        record_id: record.record_id,
        title: record.title,
        summary: formatRecordSummary(record),
        evidence_class: record?.citation?.evidence_class ?? null,
        source_id: record?.citation?.source_id ?? null,
      };
    };

    return {
      question,
      augmented_question: augmented,
      deterministic_answer: {
        route: deterministic.route,
        status: deterministic.status,
        confidence: deterministic.confidence,
        headline: deterministic.headline,
        answer: deterministic.answer,
        why: deterministic.why ?? null,
        facts: deterministic.facts ?? [],
        evidence: deterministic.evidence ?? [],
        citations: deterministic.citations ?? [],
        related: deterministic.related ?? [],
        interpretation: deterministic.interpretation ?? null,
        context: deterministic.context ?? null,
      },
      retrieval_mode: 'MISSION_EVIDENCE_RETRIEVAL',
      selected_event: compactEvent(selectedEvent),
      matched_events: events.map(compactEvent),
      matched_threads: threads.map(compactThread),
      matched_records: matches.map(compactRecord),
      matched_discipline: discipline ? {
        id: discipline.discipline_id,
        name: discipline.name,
        mission_role: discipline.mission_role,
      } : null,
    };
  }

  answer(rawQuestion) {
    const question = normalizeQuestion(rawQuestion);
    if (!question) {
      return result({
        route: 'SEARCH_SYNTHESIS',
        status: 'NEEDS_QUESTION',
        headline: 'Ask a question about Artemis II',
        answer: 'Type a mission question or choose one of the suggested prompts.',
        evidence: [],
        citations: [],
        related: ANALYST_SUGGESTIONS.slice(0, 4),
      });
    }

    const augmented = contextAugmentedQuestion(question, this.lastContext);
    const q = question.toLowerCase();
    const aq = augmented.toLowerCase();
    const finish = (answer) => this.remember(question, answer);

    const intent = detectIntent(question);
    const events = resolveEvents(this.data, augmented, 4);
    const threads = resolveThreads(this.data, augmented, 3);
    const discipline = resolveDiscipline(this.data, augmented);
    const matches = topRecordMatches(this.data, augmented, 8);


    // Evidence/source questions take priority over topic-specific answer routes.
    // "What evidence supports X?" should explain the evidence for X, not merely answer X.
    if (intent === 'EVIDENCE') {
      return finish(answerEvidence(this.data, augmented, events, threads, matches));
    }

    // Chronology questions take priority over topic-specific event handlers.
    // "What happened after closest approach?" should move along the timeline,
    // not simply describe closest approach again.
    if ((intent === 'BEFORE' || intent === 'AFTER') && events.length) {
      return finish(
        answerChronology(
          this.data,
          events[0],
          intent === 'BEFORE' ? 'BEFORE' : 'AFTER'
        )
      );
    }

    if (
      includesAny(q, ['how close', 'closest approach', 'closest did', 'pericynthion']) &&
      includesAny(aq, ['moon', 'lunar', 'orion', 'closest'])
    ) return finish(answerClosestApproach(this.data));


    if (
      includesAny(q, ['what is artemis ii', 'what was artemis ii', 'tell me about artemis ii',
        'summarize the mission', 'summary of the mission', 'what happened on the mission',
        'what did artemis ii do'])
    ) return finish(answerMissionOverview(this.data));

    if (
      includesAny(q, ['what happened during the lunar flyby', 'take me through the lunar flyby',
        'explain the lunar flyby', 'what happened around the moon', 'what happened near the moon'])
    ) return finish(answerLunarFlybyOverview(this.data));

    if (
      includesAny(q, ['what happened during entry', 'take me through entry', 'explain entry',
        'what happened during reentry', 'what happened on reentry'])
    ) return finish(answerEntryOverview(this.data));

    if (
      includesAny(q, ['what went wrong', 'what problems', 'what issues', 'did anything go wrong',
        'what anomalies', 'problems during the mission', 'issues during the mission'])
    ) return finish(answerMissionIssuesOverview(this.data));

    if (
      includesAny(q, ['most dangerous', 'riskiest', 'most risky', 'most dangerous part',
        'most dangerous phase'])
    ) return finish(answerRiskQuestion(this.data));

    if (
      includesAny(q, ['what can missionlab not know', 'what cant missionlab know',
        "what can't missionlab know", 'what data is not public', 'what is not public',
        'what evidence is missing', 'what do you not know', 'what dont you know',
        "what don't you know"])
    ) return finish(answerEvidenceBoundaries(this.data));

    if (
      includesAny(q, ['what could mission control see', 'what could ground see',
        'what did mission control see']) &&
      includesAny(aq, ['behind the moon', 'lunar blackout', 'moon blackout', 'occultation'])
    ) return finish(answerLunarMissionControlVisibility(this.data));

    if (
      includesAny(q, ['difference between earthrise and dsn', 'earthrise vs dsn',
        'earthrise and dsn reacquisition', 'earthrise vs reacquisition',
        'difference between earthrise and reacquisition'])
    ) return finish(answerEarthriseVsReacquisition(this.data));

    if (
      includesAny(aq, ['o2o', 'optical communication', 'optical communications',
        'near space network', 'deep space network', 'nsn', 'communications architecture']) &&
      !includesAny(aq, ['behind the moon', 'blackout', 'return-link', 'return link'])
    ) return finish(answerCommunicationsArchitecture(this.data));

    if (
      includesAny(q, ['difference', 'compare', 'same as']) &&
      includesAny(aq, ['lunar blackout','moon blackout','behind the moon']) &&
      includesAny(aq, ['return link','return-link','flight day 9'])
    ) return finish(compareLunarAndReturnLink(this.data));

    if (
      includesAny(q, [
        'lose contact','lost contact','loss of contact','communication blackout',
        'communications blackout','comm blackout','radio blackout','loss of signal',
        'lost signal','lose signal','dsn','reacquisition','behind the moon'
      ]) &&
      includesAny(aq, ['moon','lunar','flyby','earthset','earthrise','behind the moon'])
    ) return finish(answerLunarCommunicationsBlackout(this.data));

    if (
      includesAny(q, ['cause rtc2','caused rtc2','link loss cause','did the return']) ||
      (intent === 'WHY' && aq.includes('rtc2') && includesAny(aq, ['link','signal','communication']))
    ) return finish(answerReturnLinkCausation(this.data));

    if (
      includesAny(q, ['root cause','what caused']) &&
      includesAny(aq, ['urine','vent','wastewater','toilet','uwms'])
    ) return finish(answerVentRootCause(this.data));

    if (includesAny(aq, ['heat shield','heatshield','avcoat','char loss'])) {
      return finish(answerHeatShield(this.data));
    }

    if (
      includesAny(aq, ['navigation','guidance','gnc','optical navigation','star tracker','imu','gps']) ||
      includesAny(q, ['how did orion know where','how does orion know where'])
    ) return finish(answerNavigation(this.data, augmented));

    if (
      includesAny(aq, ['propulsion','engine','thruster','oms-e','r-4d','rcs']) ||
      (includesAny(aq, ['rtc1','rtc2','rtc3','otc3']) && includesAny(q, ['which engine','what engine','thruster']))
    ) return finish(answerPropulsion(this.data, augmented));

    if (includesAny(aq, ['parachute','drogue','main chute'])) {
      return finish(answerEntrySystem(this.data, augmented));
    }

    if (intent === 'COMPARE' && events.length >= 2) {
      return finish(answerCompareEvents(this.data, events[0], events[1]));
    }

    if (intent === 'ELAPSED_BETWEEN' && events.length >= 2) {
      return finish(answerElapsedBetween(this.data, events[0], events[1]));
    }

    if (intent === 'BEFORE' && events.length) {
      return finish(answerChronology(this.data, events[0], 'BEFORE'));
    }

    if (intent === 'AFTER' && events.length) {
      return finish(answerChronology(this.data, events[0], 'AFTER'));
    }

    if (intent === 'WHEN' && events.length) {
      return finish(answerWhen(this.data, events[0]));
    }

    if (intent === 'MISSION_CONTROL') {
      if (events.length || discipline) {
        return finish(answerMissionControl(this.data, events[0] ?? null, discipline));
      }
    }

    if (intent === 'EVIDENCE') {
      return finish(answerEvidence(this.data, augmented, events, threads, matches));
    }

    if (intent === 'WHY') {
      const thread =
        threads[0] ??
        (events[0] ? threadForEvent(this.data, events[0].event_id) : null);
      if (thread) return finish(answerWhyFromThread(this.data, thread));
    }

    if (
      events.length &&
      (includesAny(q, ['what should i know about', 'tell me about', 'what happened during']) ||
       matches[0]?.score < 18)
    ) {
      return finish(answerEvent(this.data, events[0]));
    }

    return finish(genericSynthesis(this.data, augmented, matches, events, threads));
  }
}
