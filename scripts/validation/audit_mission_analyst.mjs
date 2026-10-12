import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { MissionAnalyst } from '../../js/mission-analyst.js';

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), '..', '..');
const REF = path.join(ROOT, 'data', 'reference');

function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(REF, name), 'utf8').replace(/^\uFEFF/, ''));
}

function requireCondition(condition, message) {
  if (!condition) throw new Error(message);
}

const perspectives = readJson('artemis_ii_mission_control_perspectives.json');
const decisions = readJson('artemis_ii_decision_threads.json');
const analystIndex = readJson('artemis_ii_mission_analyst_index.json');
const analystInterface = readJson('artemis_ii_mission_analyst_interface.json');
const lunar = readJson('artemis_ii_lunar_observation_reconstruction.json');
const entry = readJson('artemis_ii_entry_events.json');
const publication = readJson('artemis_ii_publication_manifest.json');
const publicExperience = readJson('artemis_ii_public_experience.json');
const communicationsReference = readJson('artemis_ii_communications_events.json');
const communicationsCatalog = readJson('artemis_ii_communications_event_catalog.json');
const communicationsThreads = readJson('artemis_ii_communications_operational_threads.json');
const gncArchitecture = readJson('artemis_ii_gnc_architecture.json');
const gncThreads = readJson('artemis_ii_gnc_operational_threads.json');
const propulsion = readJson('artemis_ii_esm_propulsion_architecture.json');
const entryRecovery = readJson('artemis_ii_entry_descent_recovery_evidence.json');
const wasteManagement = readJson('artemis_ii_waste_management_evidence.json');
const heatingModel = readJson('artemis_ii_convective_heating_model.json');

const data = {
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

requireCondition(data.events.length === 24, 'Expected 24 mission events');
requireCondition(data.records.length === 146, 'Expected 146 searchable records');
requireCondition(data.decisionThreads.length === 10, 'Expected 10 decision threads');

const CASES = [
  {
    q: 'Why did Orion lose contact behind the Moon?',
    route: 'COMMUNICATIONS_SYNTHESIS',
    includes: ['Deep Space Network', '22:44'],
  },
  {
    q: 'What could Mission Control see while Orion was behind the Moon?',
    route: 'COMMUNICATIONS_SYNTHESIS',
    includes: ['normal live DSN radio path', 'onboard'],
  },
  {
    q: 'What is the difference between Earthrise and DSN reacquisition?',
    route: 'COMPARISON',
    includes: ['not the same event', '23:25'],
  },
  {
    q: 'How long did the lunar communications blackout last?',
    route: 'COMMUNICATIONS_SYNTHESIS',
    includes: ['blackout'],
  },
  {
    q: 'Was the lunar blackout the same as the Flight Day 9 return-link loss?',
    route: 'COMPARISON',
    includes: ['fundamentally different', 'unexpected'],
  },
  {
    q: 'Did the return-link loss cause RTC2?',
    route: 'DECISION_THREAD_CAUSATION',
    includes: ['does not establish', 'RTC2'],
  },
  {
    q: 'Which engine performed RTC2?',
    status: 'UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE',
    includes: ['does not know', 'RTC2'],
  },
  {
    q: 'How did Orion know where it was in deep space?',
    route: 'SYSTEM_SYNTHESIS',
    includes: ['onboard', 'Deep Space Network'],
  },
  {
    q: 'What is the difference between navigation, guidance, and control?',
    route: 'SYSTEM_SYNTHESIS',
    includes: ['Navigation', 'Guidance', 'Control'],
  },
  {
    q: 'What happened during entry?',
    route: 'MISSION_PHASE_SYNTHESIS',
    includes: ['Entry Interface', 'parachute'],
  },
  {
    q: 'How did the parachutes work?',
    route: 'SYSTEM_SYNTHESIS',
    includes: ['drogue', 'main parachutes'],
  },
  {
    q: 'What happened with the heat shield?',
    route: 'DECISION_THREAD',
    includes: ['Artemis I', 'modified trajectory'],
  },
  {
    q: 'What was the root cause of the urine vent-line issue?',
    status: 'UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE',
    includes: ['root cause', 'Possible ice'],
  },
  {
    q: 'What problems happened during Artemis II?',
    route: 'MISSION_ISSUE_SYNTHESIS',
    includes: ['toilet', 'return-link'],
  },
  {
    q: 'What was the most dangerous phase of the mission?',
    status: 'NOT_OBJECTIVELY_RANKED_IN_PUBLIC_EVIDENCE',
    includes: ['cannot honestly rank', 'Entry'],
  },
  {
    q: 'What can MissionLab not know from public data?',
    route: 'EVIDENCE_BOUNDARY',
    includes: ['private Orion telemetry', 'console transcripts'],
  },
  {
    q: 'What happened during the lunar flyby?',
    route: 'MISSION_PHASE_SYNTHESIS',
    includes: ['Earth set', 'closest approach'],
  },
  {
    q: 'What is Artemis II?',
    route: 'MISSION_OVERVIEW',
    includes: ['around the Moon', 'splashdown'],
  },
  {
    q: 'When was RTC2?',
    route: 'EVENT_TIME',
    includes: ['RTC2'],
  },
  {
    q: 'What happened after RTC2?',
    route: 'CHRONOLOGY',
    includes: ['After'],
  },
  {
    q: 'What happened before Earthrise?',
    route: 'CHRONOLOGY',
    includes: ['Before'],
  },
  {
    q: 'How long between Earthset and Earthrise?',
    route: 'DETERMINISTIC_ELAPSED_TIME',
    includes: ['minutes'],
  },
  {
    q: 'Compare RTC1 and RTC2.',
    route: 'COMPARISON',
    includes: ['RTC1', 'RTC2'],
  },
  {
    q: 'What evidence supports closest approach?',
    route: 'EVIDENCE',
    includes: ['evidence'],
  },
  {
    q: 'What does FDO care about?',
    route: 'DISCIPLINE',
    includes: ['Flight Dynamics'],
  },
  {
    q: 'What was Mission Control watching during entry?',
    route: 'MISSION_CONTROL_CONTEXT',
    includes: ['Mission Control relevance'],
  },
  {
    q: 'Tell me about pericynthion.',
    route: 'EVENT',
    includes: ['Pericynthion'],
  },
  {
    q: 'What happend at pericynthon?',
    includes: ['closest', 'Pericynthion'],
  },
  {
    q: 'What is O2O?',
    route: 'SYSTEM_SYNTHESIS',
    includes: ['optical communications', 'separate'],
  },
  {
    q: 'What happened next after closest approach?',
    route: 'CHRONOLOGY',
    includes: ['After'],
  },
];

function normalize(value) {
  return String(value ?? '').toLowerCase();
}

function runCase(testCase, index) {
  const analyst = new MissionAnalyst(data);
  const answer = analyst.answer(testCase.q);

  requireCondition(answer && answer.headline && answer.answer, `Case ${index + 1}: empty answer`);
  requireCondition(answer.status !== 'NEEDS_QUESTION', `Case ${index + 1}: question not interpreted`);

  if (testCase.route) {
    requireCondition(
      answer.route === testCase.route,
      `Case ${index + 1}: expected route ${testCase.route}, got ${answer.route}`
    );
  }

  if (testCase.status) {
    requireCondition(
      answer.status === testCase.status,
      `Case ${index + 1}: expected status ${testCase.status}, got ${answer.status}`
    );
  }

  const combined = normalize([
    answer.headline,
    answer.answer,
    answer.why,
    ...(answer.facts ?? []),
  ].join(' '));

  for (const required of testCase.includes ?? []) {
    requireCondition(
      combined.includes(normalize(required)),
      `Case ${index + 1}: answer missing expected concept "${required}"`
    );
  }

  if (
    !testCase.allowNoCitations &&
    !String(answer.status).includes('UNKNOWN') &&
    answer.status !== 'NEEDS_QUESTION'
  ) {
    requireCondition(
      Array.isArray(answer.citations) && answer.citations.length > 0,
      `Case ${index + 1}: supported answer has no citations`
    );
  }

  console.log(`PASS ${String(index + 1).padStart(2, '0')}  ${testCase.q}`);
  console.log(`     ${answer.route} · ${answer.status} · ${answer.confidence ?? 'HIGH'}`);
}

// Independent prompts
CASES.forEach(runCase);

// Conversational follow-up test
{
  const analyst = new MissionAnalyst(data);
  const first = analyst.answer('Tell me about closest approach.');
  const second = analyst.answer('What happened after that?');

  requireCondition(first.context?.eventId === 'A2_PERICYNTHION', 'Follow-up setup did not resolve closest approach');
  requireCondition(second.route === 'CHRONOLOGY', `Follow-up route mismatch: ${second.route}`);
  requireCondition(
    normalize([second.headline, second.answer].join(' ')).includes('earthrise'),
    'Contextual follow-up did not move from closest approach to Earthrise'
  );

  console.log('PASS FU  Contextual follow-up: "What happened after that?"');
}

console.log();
console.log(`MISSION ANALYST EVIDENCE AUDIT PASSED · ${CASES.length} mission prompts + 1 contextual follow-up`);
