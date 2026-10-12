import {
  GALLERY_ASSETS,
  TOUR_CHAPTERS,
  evidenceLabel,
  eventTimeLabel,
  formatMet,
  getEvent,
  humanize,
  loadMissionData,
} from './js/mission-data.js';
import { MissionMap } from './js/mission-map.js';
import { ANALYST_SUGGESTIONS, MissionAnalyst } from './js/mission-analyst.js';

const state = {
  data: null,
  map: null,
  analyst: null,
  selectedIndex: 0,
  chapterIndex: 0,
  explorerView: 'lunar',
  engineeringMode: false,
  selectedDiscipline: 'FLIGHT',
  selectedThread: null,
  askBusy: false,
};

const els = {
  body: document.body,
  appStatus: document.querySelector('#app-status'),
  experienceMode: document.querySelector('#experience-mode'),
  scrubber: document.querySelector('#mission-scrubber'),
  scrubberLabel: document.querySelector('#scrubber-label'),
  scrubberEvents: document.querySelector('#scrubber-events'),
  stagePhase: document.querySelector('#stage-phase'),
  stageEvidence: document.querySelector('#stage-evidence'),
  selectedMet: document.querySelector('#selected-met'),
  selectedTime: document.querySelector('#selected-time'),
  selectedName: document.querySelector('#selected-name'),
  selectedSummary: document.querySelector('#selected-summary'),
  eventDetails: document.querySelector('#event-details-button'),
  askEvent: document.querySelector('#ask-event-button'),
  factDistance: document.querySelector('#fact-distance'),
  factLunarAltitude: document.querySelector('#fact-lunar-altitude'),
  startTour: document.querySelector('#start-tour'),
  chapterList: document.querySelector('#chapter-list'),
  chapterNumber: document.querySelector('#chapter-number'),
  chapterPhase: document.querySelector('#chapter-phase'),
  chapterTitle: document.querySelector('#chapter-title'),
  chapterBody: document.querySelector('#chapter-body'),
  chapterWhy: document.querySelector('#chapter-why'),
  chapterEngineering: document.querySelector('#chapter-engineering'),
  chapterVisual: document.querySelector('#chapter-visual'),
  chapterPrev: document.querySelector('#chapter-prev'),
  chapterNext: document.querySelector('#chapter-next'),
  explorerContent: document.querySelector('#explorer-content'),
  explorerTabs: [...document.querySelectorAll('.explorer-tab')],
  suggestions: document.querySelector('#question-suggestions'),
  chatLog: document.querySelector('#chat-log'),
  analystForm: document.querySelector('#analyst-form'),
  analystQuestion: document.querySelector('#analyst-question'),
  chatEngineBadge: document.querySelector('#chat-engine-badge'),
  missionMap: document.querySelector('#mission-map'),
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function fmt(value, digits = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '—';
  return number.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function shortTime(utc) {
  if (!utc) return 'No exact public time';
  const date = new Date(utc);
  if (Number.isNaN(date.getTime())) return utc;
  return date.toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, ' UTC').replace('Z', ' UTC');
}

function selectedEvent() {
  return state.data?.events?.[state.selectedIndex] ?? null;
}

function currentUrlState() {
  const params = new URLSearchParams(window.location.search);
  return {
    eventId: params.get('event'),
    view: params.get('view'),
  };
}

function writeUrlState({ eventId = null, view = null } = {}) {
  const url = new URL(window.location.href);

  if (eventId) url.searchParams.set('event', eventId);
  else url.searchParams.delete('event');

  if (view) url.searchParams.set('view', view);
  else url.searchParams.delete('view');

  window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
}

function eventToView(event) {
  if (!event) return 'lunar';
  const id = event.event_id;

  if (
    [
      'A2_LUNAR_SOI_ENTRY',
      'A2_EARTHSET',
      'A2_PERICYNTHION',
      'A2_EARTHRISE',
      'A2_TOTAL_SOLAR_ECLIPSE',
      'A2_LUNAR_SOI_EXIT',
    ].includes(id)
  ) return 'lunar';

  if (
    [
      'A2_DSN_NSN_HANDOVER',
      'A2_CM_SM_SEPARATION',
      'A2_ENTRY_INTERFACE',
      'A2_ENTRY_BLACKOUT',
      'A2_ENTRY_REACQUISITION',
      'A2_DROGUE_DEPLOYMENT',
      'A2_MAIN_DEPLOYMENT',
      'A2_SPLASHDOWN',
    ].includes(id)
  ) return 'entry';

  if (
    [
      'A2_OTC3',
      'A2_RTC1',
      'A2_RETURN_LINK_LOSS',
      'A2_RTC2',
      'A2_RTC3',
      'A2_UWMS_FD1_FAULT',
      'A2_UWMS_FD4_VENT_ISSUE',
    ].includes(id)
  ) return 'decisions';

  return 'control';
}

function selectEventById(eventId, { animate = true, updateUrl = true } = {}) {
  const index = state.data.events.findIndex((event) => event.event_id === eventId);
  if (index < 0) return;
  selectEvent(index, { animate, updateUrl });
}

function selectEvent(index, { animate = true, updateUrl = true } = {}) {
  const bounded = Math.max(0, Math.min(state.data.events.length - 1, Number(index)));
  state.selectedIndex = bounded;
  const event = selectedEvent();

  els.scrubber.value = String(bounded);
  els.scrubberLabel.textContent = `EVENT ${bounded + 1} OF ${state.data.events.length}`;
  els.stagePhase.textContent = humanize(event.classification);
  els.stageEvidence.textContent = evidenceLabel(event.evidence_class);
  els.selectedMet.textContent = formatMet(event);
  els.selectedTime.textContent = eventTimeLabel(event);
  els.selectedName.textContent = event.name;
  els.selectedSummary.textContent = event.summary;
  state.map.select(event.event_id, animate);

  [...els.scrubberEvents.children].forEach((node, markerIndex) => {
    node.classList.toggle('active', markerIndex === bounded);
  });

  if (updateUrl) {
    writeUrlState({ eventId: event.event_id, view: state.explorerView });
  }

  els.appStatus.textContent = `Selected ${event.name}. ${eventTimeLabel(event)}.`;
}

function renderScrubberMarkers() {
  els.scrubberEvents.innerHTML = '';
  state.data.events.forEach((event, index) => {
    const marker = document.createElement('span');
    marker.style.left = `${(index / (state.data.events.length - 1)) * 100}%`;
    marker.title = event.name;
    els.scrubberEvents.appendChild(marker);
  });
}

function renderTourTabs() {
  els.chapterList.innerHTML = TOUR_CHAPTERS.map((chapter, index) => `
    <button
      class="chapter-button${index === state.chapterIndex ? ' active' : ''}"
      type="button"
      role="tab"
      aria-selected="${index === state.chapterIndex ? 'true' : 'false'}"
      data-chapter-index="${index}"
    >
      <span>${String(index + 1).padStart(2, '0')}</span>
      <strong>${escapeHtml(chapter.title)}</strong>
    </button>
  `).join('');

  els.chapterList.querySelectorAll('.chapter-button').forEach((button) => {
    button.addEventListener('click', () => {
      setChapter(Number(button.dataset.chapterIndex));
    });
  });
}

function renderChapterEngineering(chapter, event) {
  const lenses = (event.primary_lenses ?? []).join(', ') || 'No primary lens assigned';
  return `
    <dl>
      <div>
        <dt>UTC / public timing</dt>
        <dd>${escapeHtml(eventTimeLabel(event))}</dd>
      </div>
      <div>
        <dt>Mission elapsed time</dt>
        <dd>${escapeHtml(formatMet(event))}</dd>
      </div>
      <div>
        <dt>Evidence</dt>
        <dd>${escapeHtml(evidenceLabel(event.evidence_class))}</dd>
      </div>
      <div>
        <dt>Primary lenses</dt>
        <dd>${escapeHtml(lenses)}</dd>
      </div>
    </dl>
    <p>
      <strong>Evidence dependency:</strong>
      ${escapeHtml(humanize(event.source_dependency))}
    </p>
  `;
}

function setChapter(index, { scroll = false } = {}) {
  const bounded = Math.max(0, Math.min(TOUR_CHAPTERS.length - 1, Number(index)));
  state.chapterIndex = bounded;

  const chapter = TOUR_CHAPTERS[bounded];
  const event = getEvent(state.data, chapter.eventId);

  els.chapterNumber.textContent =
    `${String(bounded + 1).padStart(2, '0')} / ${String(TOUR_CHAPTERS.length).padStart(2, '0')}`;
  els.chapterPhase.textContent = chapter.phase;
  els.chapterTitle.textContent = chapter.title;
  els.chapterBody.textContent = chapter.body;
  els.chapterWhy.textContent = chapter.why;
  els.chapterEngineering.innerHTML = renderChapterEngineering(chapter, event);
  els.chapterVisual.dataset.visual = chapter.visual;
  els.chapterPrev.disabled = bounded === 0;
  els.chapterNext.disabled = bounded === TOUR_CHAPTERS.length - 1;
  els.chapterNext.textContent = bounded === TOUR_CHAPTERS.length - 1 ? 'Tour complete ✓' : 'Next →';

  renderTourTabs();
  selectEventById(chapter.eventId, { animate: true, updateUrl: true });

  if (scroll) {
    document.querySelector('#tour').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function setExplorerTab(view, { updateUrl = true } = {}) {
  const allowed = new Set(['lunar', 'entry', 'control', 'decisions', 'systems', 'science']);
  state.explorerView = allowed.has(view) ? view : 'lunar';

  els.explorerTabs.forEach((tab) => {
    const active = tab.dataset.view === state.explorerView;
    tab.classList.toggle('active', active);
    tab.setAttribute('aria-selected', active ? 'true' : 'false');
  });

  renderExplorer();

  if (updateUrl) {
    writeUrlState({
      eventId: selectedEvent()?.event_id ?? null,
      view: state.explorerView,
    });
  }
}

function infoCard(label, title, body) {
  return `
    <article class="info-card">
      <span>${escapeHtml(label)}</span>
      <h4>${escapeHtml(title)}</h4>
      <p>${escapeHtml(body)}</p>
    </article>
  `;
}

function renderLunarExplorer() {
  const px = state.data.publicExperience;
  const closest = px.lunar_encounter.closest_approach;
  const soi = px.lunar_encounter.lunar_soi;
  const occult = px.lunar_encounter.full_earth_occultation;
  const eclipse = px.lunar_encounter.total_solar_eclipse;

  return `
    <div class="explorer-panel">
      <div class="explorer-intro">
        <h3>Watch Earth disappear behind the Moon.</h3>
        <p class="explain-copy">
          Orion’s path carried the Moon directly between the spacecraft and Earth.
          Move the encounter control and watch the story change from Earthset to blackout,
          closest approach, Earthrise, and communications recovery.
        </p>
        <p class="engineering-copy">
          Correlate NASA-reported communications and image products with MissionLab-derived
          occultation, SOI, pericynthion, and OEM/SPICE geometry. Product-specific public
          timestamps remain distinct from derived geometric contact times.
        </p>
      </div>

      <div class="metric-ribbon">
        <article><small>NASA Earthset image</small><strong>22:41 UTC</strong></article>
        <article><small>Reported DSN blackout</small><strong>22:44 UTC</strong></article>
        <article><small>Closest lunar altitude</small><strong>${fmt(closest.mean_radius_altitude_km)} km</strong></article>
        <article><small>NASA Earthrise image</small><strong>23:22 UTC</strong></article>
      </div>

      <div class="lunar-player">
        <div class="lunar-player-head">
          <div>
            <span class="stage-label">LUNAR ENCOUNTER PLAYER</span>
            <strong id="lunar-player-title">Earthset</strong>
          </div>
          <small id="lunar-player-time">22:41 UTC · NASA-reported image product</small>
        </div>

        <div class="lunar-player-stage" aria-live="polite">
          <div class="lunar-player-earth" aria-hidden="true"></div>
          <div class="lunar-player-los" aria-hidden="true"></div>
          <div class="lunar-player-orbit" aria-hidden="true"></div>
          <div class="lunar-player-moon" aria-hidden="true"></div>
          <div class="lunar-player-orion" id="lunar-player-orion" aria-hidden="true"></div>

          <div class="lunar-player-status">
            <span id="lunar-player-status-label">VISIBLE EARTH · CONTACT TRANSITION</span>
            <strong id="lunar-player-status-title">Earth reaches the lunar limb</strong>
            <p id="lunar-player-status-copy">
              NASA’s public Earthset image is timestamped 22:41 UTC. The communications blackout
              is a separate operational event reported three minutes later.
            </p>
          </div>
        </div>

        <div class="lunar-player-controls">
          <label class="sr-only" for="lunar-encounter-scrubber">Move through the lunar encounter</label>
          <input id="lunar-encounter-scrubber" type="range" min="0" max="4" step="1" value="0">
          <div class="lunar-player-ticks" aria-hidden="true">
            <span>EARTHSET</span>
            <span>BLACKOUT</span>
            <span>CLOSEST</span>
            <span>EARTHRISE</span>
            <span>REACQUIRE</span>
          </div>
        </div>
      </div>

      <div class="mission-imagery-band" aria-label="NASA Artemis II lunar flyby imagery">
        <figure class="mission-photo">
          <div class="mission-photo-frame">
            <img
              src="https://images-assets.nasa.gov/image/art002e021219/art002e021219~orig.jpg"
              data-fallback-src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Earthset_on_the_Far_Side_%28art002e021219%29.jpg"
              alt="Earth setting behind the cratered lunar horizon during the Artemis II lunar flyby"
              loading="lazy"
              referrerpolicy="no-referrer"
            >
            <span>REAL ARTEMIS II IMAGE</span>
          </div>
          <figcaption>
            <strong>Earthset · 22:41 UTC</strong>
            <p>
              Captured by the Artemis II crew as Earth slipped behind the Moon’s far-side horizon.
              NASA photo ID art002e021219.
            </p>
            <a href="https://images.nasa.gov/details/art002e021219" target="_blank" rel="noreferrer">NASA image record ↗</a>
          </figcaption>
        </figure>

        <figure class="mission-photo">
          <div class="mission-photo-frame">
            <img
              src="https://images-assets.nasa.gov/image/art002e009280/art002e009280~orig.jpg"
              data-fallback-src="https://upload.wikimedia.org/wikipedia/commons/0/0b/Art002e009280_%28April_6%2C_2026%29_%E2%80%93_Earthrise_captured_through_the_Orion_spacecraft_window_at_7-22_p.jpg"
              alt="Crescent Earth rising beyond the lunar limb during the Artemis II lunar flyby"
              loading="lazy"
              referrerpolicy="no-referrer"
            >
            <span>REAL ARTEMIS II IMAGE</span>
          </div>
          <figcaption>
            <strong>Earthrise · 23:22 UTC</strong>
            <p>
              Captured through Orion’s window as Earth re-emerged beyond the lunar limb.
              NASA photo ID art002e009280.
            </p>
            <a href="https://images.nasa.gov/details/art002e009280" target="_blank" rel="noreferrer">NASA image record ↗</a>
          </figcaption>
        </figure>

        <div class="mission-imagery-note">
          <strong>IMAGE / EVIDENCE BOUNDARY</strong>
          <p>
            These NASA photographs make the encounter tangible. MissionLab’s geometry,
            communications timing, and science conclusions still come from the curated
            datasets and retain their own evidence classes and timing precision.
          </p>
        </div>
      </div>

      <div class="lunar-layout">
        <div class="lunar-geometry" role="img" aria-label="Schematic lunar flyby geometry showing Earth, Moon, Earthset, closest approach, and Earthrise markers">
          <div class="earth-mini" aria-hidden="true"></div>
          <div class="line-of-sight" aria-hidden="true"></div>
          <div class="moon" aria-hidden="true"></div>
          <div class="lunar-flyby-arc" aria-hidden="true"></div>

          <button class="flyby-marker earthset" type="button" data-event-jump="A2_EARTHSET">
            <strong>EARTHSET</strong><span>22:41 UTC</span>
          </button>
          <button class="flyby-marker closest" type="button" data-event-jump="A2_PERICYNTHION">
            <strong>CLOSEST APPROACH</strong><span>${fmt(closest.mean_radius_altitude_km)} km altitude</span>
          </button>
          <button class="flyby-marker earthrise" type="button" data-event-jump="A2_EARTHRISE">
            <strong>EARTHRISE</strong><span>23:22 UTC image product</span>
          </button>
        </div>

        <div class="info-stack">
          ${infoCard(
            'WHAT AM I LOOKING AT?',
            'Two related stories: geometry and operations',
            'Earthset/Earthrise imagery, DSN blackout/reacquisition, and MissionLab geometric contact times describe related parts of the flyby, but they are not forced into one exact event timestamp.'
          )}
          ${infoCard(
            'WHY DOES THIS MATTER?',
            'The blackout was expected, not a spacecraft failure',
            'The Moon blocked the Earth-based Deep Space Network radio path. That is fundamentally different from the later unexpected Flight Day 9 return-link anomaly.'
          )}
          ${infoCard(
            'FULL EARTH OCCULTATION',
            `${fmt(occult.duration_minutes, 1)} minutes in MissionLab geometry`,
            `Derived from ${shortTime(occult.start_utc)} to ${shortTime(occult.stop_utc)} using public trajectory products and SPICE.`
          )}
          ${infoCard(
            'LUNAR SPHERE OF INFLUENCE',
            `${soi.duration_hours.toFixed(2)} hours inside the project’s ${fmt(soi.boundary_km)} km boundary`,
            `MissionLab derives entry at ${shortTime(soi.entry_utc)} and exit at ${shortTime(soi.exit_utc)}.`
          )}
          ${infoCard(
            'SOLAR ECLIPSE',
            `${fmt(eclipse.duration_minutes, 1)} minutes of derived totality`,
            `NASA described the eclipse as “${eclipse.nasa_reported_duration}.” MissionLab preserves the distinction between that public description and its geometric reconstruction.`
          )}
        </div>
      </div>

      <figure class="visual-card" style="margin-top:1rem">
        <img
          src="docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg"
          alt="MissionLab lunar observation reconstruction showing Artemis II lunar science observations"
          loading="lazy"
        >
        <figcaption>
          Validated MissionLab lunar-observation reconstruction connecting time, geometry,
          crew observations, imagery, and postflight science context.
        </figcaption>
      </figure>
    </div>
  `;
}

function entryStep(index, title, body, data) {
  return `
    <article class="entry-step">
      <span class="entry-step-index">${String(index).padStart(2, '0')}</span>
      <div>
        <h4>${escapeHtml(title)}</h4>
        <p>${escapeHtml(body)}</p>
      </div>
      <div class="entry-step-data">${escapeHtml(data)}</div>
    </article>
  `;
}

function renderEntryExplorer() {
  const entry = state.data.publicExperience.entry;

  return `
    <div class="explorer-panel">
      <div class="explorer-intro">
        <h3>Come home from the Moon at atmospheric-entry speed.</h3>
        <p class="explain-copy">
          Reentry turns enormous speed into heat, drag, and finally a parachute descent.
          Follow the public anchors from Entry Interface to Pacific splashdown.
        </p>
        <p class="engineering-copy">
          Inspect the validated public entry anchors alongside MissionLab entry reconstruction
          plots. Public blog timestamps remain minute-level events and are not treated as
          sub-second telemetry.
        </p>
      </div>

      <div class="metric-ribbon">
        <article><small>Entry Interface</small><strong>400,000 ft</strong></article>
        <article><small>Drogues</small><strong>23,400 ft</strong></article>
        <article><small>Main parachutes</small><strong>5,400 ft</strong></article>
        <article><small>EI → splashdown</small><strong>14 min</strong></article>
      </div>

      <div class="entry-layout">
        <div class="entry-sequence">
          ${entryStep(1, 'Entry Interface', 'Orion reaches the public atmospheric-entry anchor.', 'Apr 10 · 23:53 UTC')}
          ${entryStep(2, 'Plasma blackout', 'Expected ionized-gas communications constraint after entry begins.', '≈ 6 min public expectation')}
          ${entryStep(3, 'Communications reacquisition', 'Public reporting confirms the link returning after blackout.', 'Apr 11 · 00:00 UTC')}
          ${entryStep(4, 'Drogue parachutes', 'Drogues slow and stabilize the capsule.', '23,400 ft · 00:03 UTC')}
          ${entryStep(5, 'Three main parachutes', 'Main parachutes take over the final descent.', '5,400 ft · 00:04 UTC')}
          ${entryStep(6, 'Splashdown', 'Orion returns to the Pacific off the coast of San Diego.', '00:07 UTC')}
        </div>

        <figure class="visual-card">
          <img
            src="docs/assets/entry/phase2d_entry_events_altitude.svg"
            alt="MissionLab entry event altitude reconstruction"
            loading="lazy"
          >
          <figcaption>
            WHAT AM I LOOKING AT? MissionLab’s entry event/altitude reconstruction.
            Engineering reconstruction is kept distinct from direct onboard telemetry.
          </figcaption>
        </figure>
      </div>

      <div class="info-stack" style="grid-template-columns:repeat(2,minmax(0,1fr));margin-top:1rem">
        ${infoCard(
          'WHY DOES THIS MATTER?',
          'The spacecraft has to lose energy without losing control',
          'Entry links trajectory targeting, thermal protection, communications constraints, guidance, parachute deployment, and recovery into one continuous safety-critical sequence.'
        )}
        ${infoCard(
          'HEAT-SHIELD CONTEXT',
          'Artemis II changed the entry environment',
          'NASA publicly connected the Artemis I Avcoat investigation to an Artemis II trajectory mitigation and later reported significantly reduced char loss.'
        )}
      </div>
    </div>
  `;
}

function disciplineEventRows(disciplineId) {
  return state.data.events
    .filter((event) => Number(event.priorities?.[disciplineId] ?? 0) >= 2)
    .sort((a, b) => {
      const priorityDelta =
        Number(b.priorities?.[disciplineId] ?? 0) -
        Number(a.priorities?.[disciplineId] ?? 0);
      return priorityDelta || a.order - b.order;
    })
    .slice(0, 10)
    .map((event) => `
      <button class="console-event" type="button" data-event-jump="${escapeHtml(event.event_id)}">
        <strong>${escapeHtml(event.name)}</strong>
        <span>${escapeHtml(event.priority_labels?.[disciplineId] ?? '')}</span>
      </button>
    `)
    .join('');
}

function renderControlExplorer() {
  const active = state.data.disciplines.find(
    (discipline) => discipline.discipline_id === state.selectedDiscipline
  ) ?? state.data.disciplines[0];

  const disciplineButtons = state.data.disciplines.map((discipline) => `
    <button
      class="discipline-button${discipline.discipline_id === active.discipline_id ? ' active' : ''}"
      type="button"
      data-discipline="${escapeHtml(discipline.discipline_id)}"
    >
      ${escapeHtml(discipline.discipline_id)}
    </button>
  `).join('');

  return `
    <div class="explorer-panel">
      <div class="explorer-intro">
        <h3>See the mission through a flight-control lens.</h3>
        <p>
          Pick a discipline. MissionLab highlights which validated public events matter
          most to that role and what kinds of questions the discipline would care about.
          Relevance does not imply private NASA decision authority.
        </p>
      </div>

      <div class="discipline-tabs">${disciplineButtons}</div>

      <div class="control-layout">
        <article class="console-card">
          <span class="console-code">${escapeHtml(active.discipline_id)}</span>
          <h3>${escapeHtml(active.display_name)}</h3>
          <p class="console-basis">${escapeHtml(active.public_role_basis)}</p>

          <div class="console-columns">
            <div>
              <h4>MissionLab focus</h4>
              <ul>
                ${(active.missionlab_focus ?? []).map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
              </ul>
            </div>
            <div>
              <h4>Questions this lens asks</h4>
              <ul>
                ${(active.primary_questions ?? []).map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
              </ul>
            </div>
          </div>
        </article>

        <div>
          <div class="suggestion-heading">HIGH / PRIMARY RELEVANCE EVENTS</div>
          <div class="console-events">${disciplineEventRows(active.discipline_id)}</div>
        </div>
      </div>

      <figure class="visual-card" style="margin-top:1rem">
        <img
          src="docs/assets/mission_control/phase7a_discipline_priority_matrix.svg"
          alt="MissionLab discipline priority matrix across the validated mission timeline"
          loading="lazy"
        >
        <figcaption>
          Seven analytical discipline lenses across the validated 24-event shared timeline.
          DISCIPLINE RELEVANCE ≠ DECISION AUTHORITY.
        </figcaption>
      </figure>
    </div>
  `;
}

function renderDecisionExplorer() {
  const threads = state.data.decisionThreads;
  if (!state.selectedThread || !threads.some((thread) => thread.thread_id === state.selectedThread)) {
    state.selectedThread = threads[0]?.thread_id ?? null;
  }

  const active = threads.find((thread) => thread.thread_id === state.selectedThread);
  if (!active) {
    return `<div class="explorer-panel"><p>No validated decision threads are available.</p></div>`;
  }

  const stageOrder = state.data.decisions.decision_stage_model ?? [
    'detection','evidence','constraint','options','decision','action','outcome'
  ];

  const stages = stageOrder.map((stageName) => {
    const stage = active.stages?.[stageName] ?? {};
    return `
      <article class="decision-stage">
        <span class="stage-name">${escapeHtml(humanize(stageName))}</span>
        <span class="stage-status">${escapeHtml(humanize(stage.status ?? 'unknown'))}</span>
        <p>${escapeHtml(stage.summary ?? 'No public summary available.')}</p>
      </article>
    `;
  }).join('');

  return `
    <div class="explorer-panel">
      <div class="explorer-intro">
        <h3>Investigate how public evidence becomes an operational story.</h3>
        <p>
          These are MissionLab evidence syntheses, not private NASA console transcripts.
          The seven-stage view makes missing options, synthesis, and public boundaries visible.
        </p>
      </div>

      <select id="decision-select" class="decision-select" aria-label="Choose a MissionLab decision thread">
        ${threads.map((thread) => `
          <option value="${escapeHtml(thread.thread_id)}"${thread.thread_id === active.thread_id ? ' selected' : ''}>
            ${escapeHtml(thread.title)}
          </option>
        `).join('')}
      </select>

      <div class="decision-layout" style="grid-template-columns:1fr">
        <div>
          <div class="suggestion-heading">${escapeHtml(humanize(active.classification))}</div>
          <h3 style="margin:.45rem 0 1rem">${escapeHtml(active.title)}</h3>
          <div class="decision-thread">${stages}</div>
          <div class="guardrail">
            <strong>EVIDENCE GUARDRAILS</strong><br>
            ${(active.guardrails ?? []).map((item) => escapeHtml(item)).join(' · ')}
          </div>
        </div>
      </div>

      <figure class="visual-card" style="margin-top:1rem">
        <img
          src="docs/assets/mission_control/phase7b_decision_thread_matrix.svg"
          alt="MissionLab decision thread matrix"
          loading="lazy"
        >
        <figcaption>
          Validated MissionLab decision-thread coverage. Public action and sequence are
          not treated as a complete internal NASA option set or private decision history.
        </figcaption>
      </figure>
    </div>
  `;
}

function renderGallery(view) {
  const assets = GALLERY_ASSETS[view] ?? [];
  const title = view === 'science'
    ? 'Turn the mission science into something you can see.'
    : 'Open the spacecraft systems behind the mission.';

  const intro = view === 'science'
    ? 'Explore lunar observations, space weather, entry science, and the Mission Control relevance picture. Each figure was already produced by the validated engineering phases.'
    : 'These diagrams expose how navigation, propulsion, communications, and crew piloting fit together without pretending MissionLab has private spacecraft telemetry.';

  return `
    <div class="explorer-panel">
      <div class="explorer-intro">
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(intro)}</p>
      </div>

      <div class="gallery-grid">
        ${assets.map((asset) => `
          <article class="gallery-card">
            <div class="gallery-visual">
              <img src="${escapeHtml(asset.src)}" alt="${escapeHtml(asset.title)}" loading="lazy">
            </div>
            <div>
              <span class="gallery-topic">${escapeHtml(asset.topic)}</span>
              <h4>${escapeHtml(asset.title)}</h4>
              <p>${escapeHtml(asset.description)}</p>
            </div>
          </article>
        `).join('')}
      </div>
    </div>
  `;
}

const LUNAR_PLAYER_STEPS = Object.freeze([
  {
    title: 'Earthset',
    time: '22:41 UTC · NASA-reported image product',
    label: 'VISIBLE EARTH · CONTACT TRANSITION',
    statusTitle: 'Earth reaches the lunar limb',
    copy: 'NASA’s public Earthset image is timestamped 22:41 UTC. The communications blackout is a separate operational event reported three minutes later.',
    x: 43,
    y: 20,
    eventId: 'A2_EARTHSET',
  },
  {
    title: 'DSN blackout begins',
    time: '22:44 UTC · NASA-reported operational event',
    label: 'EXPECTED RF BLACKOUT',
    statusTitle: 'The Moon blocks the DSN radio path',
    copy: 'NASA reported Orion entering the planned communications blackout at 22:44 UTC. This is an expected geometry-driven constraint, not a spacecraft communications failure.',
    x: 64,
    y: 23,
    eventId: 'A2_EARTHSET',
  },
  {
    title: 'Closest approach',
    time: '23:00:46 UTC · MissionLab-derived geometry',
    label: 'FARSIDE · EARTH OCCULTED',
    statusTitle: 'Orion reaches pericynthion',
    copy: 'MissionLab refines closest approach to about 6,545 km above the Moon’s mean-radius surface while Earth remains blocked from direct view.',
    x: 76,
    y: 50,
    eventId: 'A2_PERICYNTHION',
  },
  {
    title: 'Earthrise',
    time: '23:22 UTC · NASA public image product',
    label: 'EARTH RETURNS TO VIEW',
    statusTitle: 'Earth re-emerges beyond the lunar limb',
    copy: 'MissionLab preserves the 23:22 UTC NASA image timestamp separately from the 23:24 UTC Earthrise time in the live communications update.',
    x: 65,
    y: 78,
    eventId: 'A2_EARTHRISE',
  },
  {
    title: 'DSN reacquisition',
    time: 'Live report: moments after Earthrise · planned 23:25 UTC',
    label: 'RADIO CONTACT RECOVERS',
    statusTitle: 'Deep Space Network reacquires Orion',
    copy: 'The live NASA update says DSN reacquired Orion moments after Earthrise. MissionLab does not invent an exact observed reacquisition UTC.',
    x: 42,
    y: 80,
    eventId: 'A2_EARTHRISE',
  },
]);

function updateLunarPlayer(index, { syncMission = false } = {}) {
  const step = LUNAR_PLAYER_STEPS[Math.max(0, Math.min(LUNAR_PLAYER_STEPS.length - 1, Number(index)))];
  if (!step) return;

  const orion = els.explorerContent.querySelector('#lunar-player-orion');
  const title = els.explorerContent.querySelector('#lunar-player-title');
  const time = els.explorerContent.querySelector('#lunar-player-time');
  const label = els.explorerContent.querySelector('#lunar-player-status-label');
  const statusTitle = els.explorerContent.querySelector('#lunar-player-status-title');
  const copy = els.explorerContent.querySelector('#lunar-player-status-copy');

  if (orion) {
    orion.style.left = `${step.x}%`;
    orion.style.top = `${step.y}%`;
  }
  if (title) title.textContent = step.title;
  if (time) time.textContent = step.time;
  if (label) label.textContent = step.label;
  if (statusTitle) statusTitle.textContent = step.statusTitle;
  if (copy) copy.textContent = step.copy;

  if (syncMission && step.eventId) {
    selectEventById(step.eventId, { animate: true, updateUrl: true });
  }
}

function bindExplorerContent() {
  els.explorerContent.querySelectorAll('img[data-fallback-src]').forEach((image) => {
    image.addEventListener('error', () => {
      if (image.dataset.fallbackUsed === 'true') return;
      image.dataset.fallbackUsed = 'true';
      image.src = image.dataset.fallbackSrc;
    }, { once: true });
  });

  els.explorerContent.querySelectorAll('[data-event-jump]').forEach((button) => {
    button.addEventListener('click', () => {
      selectEventById(button.dataset.eventJump, { animate: true, updateUrl: true });
      document.querySelector('#mission').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  els.explorerContent.querySelectorAll('[data-discipline]').forEach((button) => {
    button.addEventListener('click', () => {
      state.selectedDiscipline = button.dataset.discipline;
      renderExplorer();
    });
  });

  const lunarScrubber = els.explorerContent.querySelector('#lunar-encounter-scrubber');
  if (lunarScrubber) {
    lunarScrubber.addEventListener('input', () => {
      updateLunarPlayer(Number(lunarScrubber.value), { syncMission: true });
    });
    updateLunarPlayer(Number(lunarScrubber.value), { syncMission: false });
  }

  const select = els.explorerContent.querySelector('#decision-select');
  if (select) {
    select.addEventListener('change', () => {
      state.selectedThread = select.value;
      renderExplorer();
    });
  }
}

function renderExplorer() {
  let html = '';
  if (state.explorerView === 'lunar') html = renderLunarExplorer();
  else if (state.explorerView === 'entry') html = renderEntryExplorer();
  else if (state.explorerView === 'control') html = renderControlExplorer();
  else if (state.explorerView === 'decisions') html = renderDecisionExplorer();
  else if (state.explorerView === 'systems') html = renderGallery('systems');
  else if (state.explorerView === 'science') html = renderGallery('science');

  els.explorerContent.innerHTML = html;
  bindExplorerContent();
}

function renderSuggestions() {
  els.suggestions.innerHTML = ANALYST_SUGGESTIONS.map((question) => `
    <button class="question-suggestion" type="button" data-question="${escapeHtml(question)}">
      ${escapeHtml(question)}
    </button>
  `).join('');

  els.suggestions.querySelectorAll('[data-question]').forEach((button) => {
    button.addEventListener('click', () => askQuestion(button.dataset.question));
  });
}

function messageHtml(role, content) {
  if (role === 'user') {
    return `
      <article class="message user-message">
        <div class="message-avatar">ME</div>
        <div class="message-body">
          <span class="message-role">MISSION QUERY</span>
          <p>${escapeHtml(content)}</p>
        </div>
      </article>
    `;
  }
  return content;
}

function citationHtml(citation) {
  const label = escapeHtml(citation.label ?? 'MissionLab evidence record');
  if (citation.url && /^https:\/\/(www\.)?(nasa\.gov|science\.nasa\.gov|ntrs\.nasa\.gov|pds\.nasa\.gov|planetarynames\.wr\.usgs\.gov)\//i.test(citation.url)) {
    return `<a class="answer-citation" href="${escapeHtml(citation.url)}" target="_blank" rel="noreferrer">${label} ↗</a>`;
  }
  return `<span class="answer-citation">${label}</span>`;
}

function answerHtml(answer) {
  const unknown = String(answer.status).includes('UNKNOWN');
  const facts = (answer.facts ?? []).length
    ? `
      <div class="answer-section">
        <strong>Key mission facts</strong>
        <ul>${answer.facts.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
      </div>
    `
    : '';

  const evidence = (answer.evidence ?? []).length
    ? `
      <div class="answer-section">
        <strong>Evidence</strong>
        <ul>${answer.evidence.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
      </div>
    `
    : '';

  const citations = (answer.citations ?? []).length
    ? `
      <div class="answer-section">
        <strong>Sources</strong>
        ${answer.citations.map(citationHtml).join('')}
      </div>
    `
    : '';

  const related = (answer.related ?? []).length
    ? `
      <div class="answer-section">
        <strong>Related questions</strong>
        <div class="question-suggestions">
          ${answer.related.map((question) => `
            <button class="question-suggestion related-question" type="button" data-related-question="${escapeHtml(question)}">
              ${escapeHtml(question)}
            </button>
          `).join('')}
        </div>
      </div>
    `
    : '';

  const interpretation = answer.interpretation
    ? `<div class="answer-interpretation"><strong>I interpreted this as:</strong> ${escapeHtml(answer.interpretation)}</div>`
    : '';

  const contextActions = answer.context?.eventId || answer.context?.threadId
    ? `
      <div class="answer-context-actions">
        ${answer.context?.eventId ? `
          <button class="answer-context-button" type="button" data-answer-event="${escapeHtml(answer.context.eventId)}">
            Open this moment on the mission map ↗
          </button>
        ` : ''}
        ${answer.context?.threadId ? `
          <button class="answer-context-button" type="button" data-answer-thread="${escapeHtml(answer.context.threadId)}">
            Open this decision thread ↗
          </button>
        ` : ''}
      </div>
    `
    : '';

  return `
    <article class="message assistant-message">
      <div class="message-avatar">A2</div>
      <div class="message-body">
        <span class="message-role">MISSION BRIEFING</span>
        <span class="message-route">${escapeHtml(answer.route)}</span>
        ${interpretation}
        <p><strong>${escapeHtml(answer.headline)}</strong></p>
        <p>${escapeHtml(answer.answer)}</p>
        ${answer.why ? `<p><strong>Why it matters.</strong> ${escapeHtml(answer.why)}</p>` : ''}
        ${facts}
        <span class="answer-status${unknown ? ' unknown' : ''}">${escapeHtml(humanize(answer.status))}</span>
        <span class="answer-confidence">${escapeHtml(answer.confidence ?? 'HIGH')} CONFIDENCE</span>
        ${evidence}
        ${citations}
        ${contextActions}
        ${related}
      </div>
    </article>
  `;
}

function appendChat(html) {
  els.chatLog.insertAdjacentHTML('beforeend', html);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function bindRelatedQuestions() {
  els.chatLog.querySelectorAll('[data-related-question]').forEach((button) => {
    if (button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => askQuestion(button.dataset.relatedQuestion));
  });

  els.chatLog.querySelectorAll('[data-answer-event]').forEach((button) => {
    if (button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => {
      selectEventById(button.dataset.answerEvent, { animate: true, updateUrl: true });
      document.querySelector('#mission').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  els.chatLog.querySelectorAll('[data-answer-thread]').forEach((button) => {
    if (button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => {
      state.selectedThread = button.dataset.answerThread;
      setExplorerTab('decisions');
      document.querySelector('#explore').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

function setAskBusy(busy) {
  state.askBusy = Boolean(busy);
  els.analystQuestion.disabled = state.askBusy;
  const submit = els.analystForm.querySelector('button[type="submit"]');
  if (submit) {
    submit.disabled = state.askBusy;
    submit.querySelector('span:first-child').textContent = state.askBusy ? 'WORKING' : 'BRIEF';
  }
}

function askQuestion(question) {
  const normalized = String(question ?? '').trim();
  if (!normalized || state.askBusy) return;

  setAskBusy(true);
  try {
    appendChat(messageHtml('user', normalized));
    els.analystQuestion.value = '';

    const answer = state.analyst.answer(normalized);
    appendChat(answerHtml(answer));
    bindRelatedQuestions();
  } finally {
    setAskBusy(false);
    els.analystQuestion.focus();
    els.chatLog.scrollTop = els.chatLog.scrollHeight;
  }
}

function setEngineeringMode(enabled) {
  state.engineeringMode = Boolean(enabled);
  els.body.classList.toggle('engineering-mode', state.engineeringMode);
  els.experienceMode.setAttribute('aria-pressed', state.engineeringMode ? 'true' : 'false');
  els.appStatus.textContent = state.engineeringMode
    ? 'Engineering view enabled.'
    : 'Explain It view enabled.';
}

function bindControls() {
  els.scrubber.addEventListener('input', () => {
    selectEvent(Number(els.scrubber.value), { animate: true, updateUrl: true });
  });

  els.eventDetails.addEventListener('click', () => {
    const view = eventToView(selectedEvent());
    setExplorerTab(view);
    document.querySelector('#explore').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  els.askEvent.addEventListener('click', () => {
    const event = selectedEvent();
    if (!event) return;
    document.querySelector('#briefing').scrollIntoView({ behavior: 'smooth', block: 'start' });
    window.setTimeout(() => {
      askQuestion(`What should I know about ${event.name}?`);
    }, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 350);
  });

  els.startTour.addEventListener('click', () => setChapter(0, { scroll: true }));
  els.chapterPrev.addEventListener('click', () => setChapter(state.chapterIndex - 1));
  els.chapterNext.addEventListener('click', () => {
    if (state.chapterIndex < TOUR_CHAPTERS.length - 1) {
      setChapter(state.chapterIndex + 1);
    }
  });

  els.explorerTabs.forEach((tab) => {
    tab.addEventListener('click', () => setExplorerTab(tab.dataset.view));
  });

  els.experienceMode.addEventListener('click', () => {
    setEngineeringMode(!state.engineeringMode);
  });

  els.analystForm.addEventListener('submit', (event) => {
    event.preventDefault();
    askQuestion(els.analystQuestion.value);
  });

  els.analystQuestion.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      els.analystForm.requestSubmit();
    }
  });
}

function applyInitialState() {
  const params = currentUrlState();
  const eventIndex = params.eventId
    ? state.data.events.findIndex((event) => event.event_id === params.eventId)
    : 0;

  selectEvent(eventIndex >= 0 ? eventIndex : 0, {
    animate: false,
    updateUrl: false,
  });

  setExplorerTab(params.view ?? eventToView(selectedEvent()), { updateUrl: false });

  const chapterIndex = TOUR_CHAPTERS.findIndex(
    (chapter) => chapter.eventId === selectedEvent().event_id
  );
  state.chapterIndex = chapterIndex >= 0 ? chapterIndex : 0;
  setChapter(state.chapterIndex);
}

async function init() {
  if (window.location.protocol === 'file:') {
    throw new Error(
      'MissionLab V2 must be served over HTTP. Run: python -m http.server 8000'
    );
  }

  state.data = await loadMissionData();
  state.analyst = new MissionAnalyst(state.data);

    const px = state.data.publicExperience;
  els.factDistance.textContent =
    `${fmt(px.mission_extrema.max_earth_center_distance_km)} km`;
  els.factLunarAltitude.textContent =
    `${fmt(px.lunar_encounter.closest_approach.mean_radius_altitude_km)} km`;

  renderScrubberMarkers();
  renderTourTabs();
  renderSuggestions();

  state.map = new MissionMap(
    els.missionMap,
    state.data.events,
    (eventId) => selectEventById(eventId)
  );

  bindControls();
  applyInitialState();

  els.appStatus.textContent =
    `A2 MissionLab Public Experience V2.7 loaded with ${state.data.events.length} validated events, ${state.data.records.length} searchable records, ${state.data.decisionThreads.length} decision threads, and the stable Mission Briefing evidence console.`;
}

init().catch((error) => {
  console.error(error);
  els.appStatus.textContent = error.message;

  const target = document.querySelector('.mission-stage');
  if (target) {
    target.insertAdjacentHTML(
      'afterbegin',
      `<div class="guardrail" role="alert"><strong>MissionLab could not load.</strong><br>${escapeHtml(error.message)}</div>`
    );
  }
});
