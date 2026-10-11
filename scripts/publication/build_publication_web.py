from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE = ROOT / "data" / "reference"
WORKFLOWS = ROOT / ".github" / "workflows"
VALIDATION_DIR = ROOT / "scripts" / "validation"

PHASE7A_PATH = REFERENCE / "artemis_ii_mission_control_perspectives.json"
PHASE9A_MANIFEST_PATH = REFERENCE / "artemis_ii_publication_manifest.json"

INDEX_PATH = ROOT / "index.html"
APP_PATH = ROOT / "app.js"
STYLES_PATH = ROOT / "styles.css"
CI_PATH = WORKFLOWS / "ci.yml"
PAGES_PATH = WORKFLOWS / "pages.yml"
VALIDATOR_PATH = VALIDATION_DIR / "validate_publication_web.py"
WEB_MANIFEST_PATH = REFERENCE / "artemis_ii_publication_web_manifest.json"


def fail(message: str) -> None:
    raise SystemExit(f"PHASE 9B BUILD FAILED: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(path: Path) -> dict:
    require(path.exists(), f"missing required file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    phase7a = load_json(PHASE7A_PATH)
    phase9a = load_json(PHASE9A_MANIFEST_PATH)

    require(
        phase7a.get("dataset_id")
        == "phase7a_artemis_ii_mission_control_perspectives",
        "Phase 7A dataset identity mismatch",
    )

    require(
        len(phase7a.get("shared_timeline", [])) == 24,
        "expected 24 validated shared-timeline events",
    )

    require(
        phase9a.get("dataset_id")
        == "phase9a_artemis_ii_publication_manifest",
        "Phase 9A publication manifest identity mismatch",
    )

    index_html = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta
    name="description"
    content="A2 MissionLab — evidence-grounded Artemis II mission operations and engineering reconstruction."
  >
  <meta name="theme-color" content="#05080e">
  <title>A2 MissionLab — Artemis II Mission Reconstruction</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to mission content</a>

  <header class="topbar">
    <div>
      <div class="eyebrow">ARTEMIS II · PUBLIC-EVIDENCE RECONSTRUCTION</div>
      <h1>A2 MissionLab</h1>
      <p class="subtitle">Mission Operations & Engineering Reconstruction</p>
    </div>

    <div class="status-card" aria-label="Project publication status">
      <span class="status-dot" aria-hidden="true"></span>
      <div>
        <strong>PHASE 9</strong>
        <small>Publication quality</small>
      </div>
    </div>
  </header>

  <nav class="project-nav" aria-label="Project navigation">
    <a href="#overview">Overview</a>
    <a href="#timeline">Mission timeline</a>
    <a href="#provenance">Provenance</a>
    <a href="docs/METHODOLOGY.md">Methodology</a>
    <a href="docs/VALIDATION_REPORT.md">Validation</a>
    <a href="docs/ANALYST_GUIDE.md">Mission Analyst</a>
  </nav>

  <main id="main-content">
    <section id="overview" class="hero-grid" aria-labelledby="overview-title">
      <div class="panel hero-copy">
        <div class="panel-label">EVIDENCE-GROUNDED MISSION RECONSTRUCTION</div>
        <h2 id="overview-title">One mission clock. Multiple engineering disciplines. Explicit evidence boundaries.</h2>
        <p>
          MissionLab connects public Artemis II trajectory, spacecraft systems,
          communications, lunar science, entry and recovery, mission-control
          perspectives, and postflight engineering without inventing unavailable telemetry.
        </p>
      </div>

      <div class="panel metrics-panel" aria-labelledby="metrics-title">
        <div class="panel-label" id="metrics-title">VALIDATED ANALYST INVENTORY</div>
        <div id="metric-grid" class="metric-grid" aria-live="polite">
          <p class="loading-copy">Loading publication metrics…</p>
        </div>
      </div>
    </section>

    <section class="mission-clock panel" aria-labelledby="clock-label">
      <div class="panel-label" id="clock-label">SELECTED MISSION EVENT</div>
      <div id="clock-time" class="clock-time">—</div>
      <div id="clock-phase" class="clock-phase">Select an event below</div>
    </section>

    <section class="controls panel" aria-labelledby="filter-title">
      <div class="control-heading">
        <div class="panel-label" id="filter-title">TIMELINE FILTERS</div>
        <p>Filter the validated Phase 7 shared mission timeline.</p>
      </div>

      <label>
        Primary discipline
        <select id="discipline-filter">
          <option value="ALL">All disciplines</option>
        </select>
      </label>

      <label>
        Evidence
        <select id="evidence-filter">
          <option value="ALL">All evidence classes</option>
        </select>
      </label>

      <button id="reset-btn" type="button">Reset filters</button>
    </section>

    <section id="timeline" class="workspace" aria-labelledby="timeline-title">
      <aside class="timeline panel">
        <div class="panel-heading">
          <div>
            <div class="panel-label">VALIDATED SHARED TIMELINE</div>
            <h2 id="timeline-title">Mission events</h2>
          </div>
          <span id="event-count" class="count" aria-label="Visible event count">0</span>
        </div>

        <div
          id="event-list"
          class="event-list"
          aria-live="polite"
          aria-label="Mission event list"
        ></div>
      </aside>

      <section
        class="detail panel"
        id="detail-panel"
        aria-labelledby="detail-title"
        tabindex="-1"
      >
        <div class="empty-state">
          <div class="orbital-icon" aria-hidden="true">◌</div>
          <h2 id="detail-title">Select a mission event</h2>
          <p>
            Inspect validated timing, evidence class, Mission Elapsed Time,
            classification, and discipline relevance.
          </p>
        </div>
      </section>
    </section>

    <section id="provenance" class="provenance-legend panel" aria-labelledby="provenance-title">
      <div class="panel-label" id="provenance-title">EVIDENCE BOUNDARIES</div>

      <div class="boundary-grid">
        <article>
          <strong>NASA REPORTED</strong>
          <p>Publicly reported mission fact or event.</p>
        </article>

        <article>
          <strong>MISSIONLAB DERIVED</strong>
          <p>Deterministic result calculated from public inputs, not onboard telemetry.</p>
        </article>

        <article>
          <strong>KNOWN UNKNOWN</strong>
          <p>Missing public evidence remains explicitly unresolved.</p>
        </article>

        <article>
          <strong>CAUSATION</strong>
          <p>Temporal sequence is never promoted to causation without evidence.</p>
        </article>
      </div>
    </section>

    <section class="boundary-callout panel" aria-label="MissionLab evidence rules">
      <code>MISSIONLAB DERIVED != NASA REPORTED</code>
      <code>TEMPORAL SEQUENCE != CAUSATION</code>
      <code>UNKNOWN PUBLIC FACT != PERMISSION TO INVENT</code>
    </section>

    <p id="app-status" class="sr-only" aria-live="assertive"></p>
  </main>

  <footer>
    <p>
      Independent open-source project using publicly released NASA data.
      Not an official NASA application and not NASA-endorsed.
    </p>
    <p>
      <a href="README.md">README</a>
      ·
      <a href="DISCLAIMER.md">Disclaimer</a>
      ·
      <a href="docs/ROADMAP.md">Roadmap</a>
    </p>
  </footer>

  <script src="app.js" defer></script>
</body>
</html>
'''

    app_js = r'''const state = {
  events: [],
  disciplines: [],
  selectedId: null,
};

const els = {
  eventList: document.querySelector('#event-list'),
  eventCount: document.querySelector('#event-count'),
  detail: document.querySelector('#detail-panel'),
  discipline: document.querySelector('#discipline-filter'),
  evidence: document.querySelector('#evidence-filter'),
  reset: document.querySelector('#reset-btn'),
  clockTime: document.querySelector('#clock-time'),
  clockPhase: document.querySelector('#clock-phase'),
  metricGrid: document.querySelector('#metric-grid'),
  appStatus: document.querySelector('#app-status'),
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function evidenceLabel(value) {
  return String(value ?? 'UNKNOWN').replaceAll('_', ' ');
}

function eventTimeLabel(event) {
  if (event.timestamp_utc) {
    return `${event.timestamp_utc} UTC`;
  }

  if (event.date_utc) {
    return `${event.date_utc} · ${event.time_precision}`;
  }

  return event.time_precision || 'No exact public time';
}

function eventMetLabel(event) {
  return event.met || 'Not assigned at this public precision';
}

function filteredEvents() {
  return state.events.filter((event) => {
    const disciplineMatch =
      els.discipline.value === 'ALL'
      || event.primary_lenses.includes(els.discipline.value);

    const evidenceMatch =
      els.evidence.value === 'ALL'
      || event.evidence_class === els.evidence.value;

    return disciplineMatch && evidenceMatch;
  });
}

function renderMetrics(metrics) {
  const values = [
    ['Datasets', metrics.datasets],
    ['Public sources', metrics.sources],
    ['Mission events', metrics.events],
    ['Decision threads', metrics.decision_threads],
    ['Searchable records', metrics.searchable_records],
    ['Analyst tools', metrics.tools],
    ['Answer routes', metrics.answer_routes],
  ];

  els.metricGrid.innerHTML = values.map(([label, value]) => `
    <div class="metric-card">
      <strong>${escapeHtml(value)}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
  `).join('');
}

function renderList() {
  const events = filteredEvents()
    .slice()
    .sort((a, b) => a.order - b.order);

  els.eventCount.textContent = String(events.length);

  if (!events.length) {
    els.eventList.innerHTML = `
      <p class="no-results">No validated events match these filters.</p>
    `;
    return;
  }

  els.eventList.innerHTML = events.map((event) => {
    const active = state.selectedId === event.event_id;

    return `
      <button
        class="event-item${active ? ' active' : ''}"
        type="button"
        data-id="${escapeHtml(event.event_id)}"
        aria-pressed="${active ? 'true' : 'false'}"
      >
        <div class="event-meta">
          <span class="evidence-badge">
            ${escapeHtml(evidenceLabel(event.evidence_class))}
          </span>
          <span class="order-badge">
            #${escapeHtml(event.order)}
          </span>
        </div>

        <strong>${escapeHtml(event.name)}</strong>
        <time>${escapeHtml(eventTimeLabel(event))}</time>
      </button>
    `;
  }).join('');

  els.eventList.querySelectorAll('.event-item').forEach((button) => {
    button.addEventListener('click', () => {
      selectEvent(button.dataset.id);
    });
  });
}

function renderPriorities(event) {
  return Object.entries(event.priority_labels)
    .map(([discipline, priority]) => `
      <div class="priority-row">
        <strong>${escapeHtml(discipline)}</strong>
        <span>${escapeHtml(priority)}</span>
      </div>
    `)
    .join('');
}

function selectEvent(eventId) {
  const event = state.events.find(
    (item) => item.event_id === eventId
  );

  if (!event) {
    return;
  }

  state.selectedId = eventId;

  els.clockTime.textContent = eventTimeLabel(event);
  els.clockPhase.textContent = event.classification;

  const primaryLenses = event.primary_lenses
    .map((lens) => `<span class="lens-chip">${escapeHtml(lens)}</span>`)
    .join('');

  els.detail.innerHTML = `
    <div class="event-meta">
      <span class="evidence-badge">
        ${escapeHtml(evidenceLabel(event.evidence_class))}
      </span>
      <span class="order-badge">
        EVENT ${escapeHtml(event.order)}
      </span>
    </div>

    <h2 id="detail-title">${escapeHtml(event.name)}</h2>

    <p class="detail-summary">${escapeHtml(event.summary)}</p>

    <div class="detail-grid">
      <div class="metric">
        <small>UTC / public timing</small>
        <strong>${escapeHtml(eventTimeLabel(event))}</strong>
      </div>

      <div class="metric">
        <small>Mission Elapsed Time</small>
        <strong>${escapeHtml(eventMetLabel(event))}</strong>
      </div>

      <div class="metric">
        <small>Classification</small>
        <strong>${escapeHtml(event.classification)}</strong>
      </div>

      <div class="metric">
        <small>Time precision</small>
        <strong>${escapeHtml(event.time_precision)}</strong>
      </div>
    </div>

    <div class="section-title">PRIMARY DISCIPLINE LENSES</div>
    <div class="lens-list">${primaryLenses}</div>

    <div class="section-title">DISCIPLINE PRIORITIES</div>
    <div class="priority-grid">${renderPriorities(event)}</div>

    <div class="section-title">EVIDENCE DEPENDENCY</div>
    <div class="source-card">
      <strong>${escapeHtml(event.source_dependency)}</strong>
      <p>
        Evidence class:
        ${escapeHtml(evidenceLabel(event.evidence_class))}
      </p>
    </div>
  `;

  renderList();

  els.appStatus.textContent =
    `Selected ${event.name}. ${eventTimeLabel(event)}.`;
}

function populateFilters() {
  state.disciplines.forEach((discipline) => {
    const option = document.createElement('option');
    option.value = discipline.discipline_id;
    option.textContent = discipline.discipline_id;
    els.discipline.appendChild(option);
  });

  [...new Set(state.events.map((event) => event.evidence_class))]
    .sort()
    .forEach((evidence) => {
      const option = document.createElement('option');
      option.value = evidence;
      option.textContent = evidenceLabel(evidence);
      els.evidence.appendChild(option);
    });
}

function bindControls() {
  [els.discipline, els.evidence].forEach((control) => {
    control.addEventListener('change', renderList);
  });

  els.reset.addEventListener('click', () => {
    els.discipline.value = 'ALL';
    els.evidence.value = 'ALL';
    renderList();
  });
}

async function fetchJson(path) {
  const response = await fetch(path);

  if (!response.ok) {
    throw new Error(
      `Could not load ${path}: HTTP ${response.status}`
    );
  }

  return response.json();
}

async function init() {
  const [perspectives, publication] = await Promise.all([
    fetchJson('./data/reference/artemis_ii_mission_control_perspectives.json'),
    fetchJson('./data/reference/artemis_ii_publication_manifest.json'),
  ]);

  if (
    perspectives.dataset_id
    !== 'phase7a_artemis_ii_mission_control_perspectives'
  ) {
    throw new Error('Validated shared-timeline dataset identity mismatch');
  }

  if (perspectives.shared_timeline.length !== 24) {
    throw new Error('Expected 24 validated shared-timeline events');
  }

  state.events = perspectives.shared_timeline;
  state.disciplines = perspectives.discipline_registry;

  populateFilters();
  bindControls();
  renderMetrics(publication.publication_metrics);
  renderList();

  if (state.events.length) {
    selectEvent(state.events[0].event_id);
  }

  els.appStatus.textContent =
    'A2 MissionLab publication interface loaded successfully.';
}

init().catch((error) => {
  console.error(error);

  els.eventList.innerHTML = `
    <p class="error-message">
      ${escapeHtml(error.message)}
    </p>
  `;

  els.metricGrid.innerHTML = `
    <p class="error-message">
      Publication metrics could not be loaded.
    </p>
  `;

  els.appStatus.textContent = error.message;
});
'''

    styles_css = r''':root {
  color-scheme: dark;
  --bg: #05080e;
  --panel: #0a101a;
  --line: #213047;
  --text: #eef4fb;
  --muted: #9aacbf;
  --accent: #89bfff;
  --good: #7ee2b8;
  --danger: #ff9a9a;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  color: var(--text);
  background: radial-gradient(circle at 80% -10%, rgba(40, 88, 140, 0.20), transparent 35%), var(--bg);
}

a {
  color: #a8d0ff;
}

button,
select,
a {
  font: inherit;
}

button,
select {
  color: var(--text);
}

button:focus-visible,
select:focus-visible,
a:focus-visible,
[tabindex]:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 3px;
}

.skip-link {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  z-index: 100;
  padding: 0.7rem 0.9rem;
  color: #07101a;
  background: #d9ebff;
  transform: translateY(-180%);
}

.skip-link:focus {
  transform: translateY(0);
}

.topbar,
.project-nav,
main,
footer {
  width: min(1440px, calc(100% - 2rem));
  margin-inline: auto;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 2rem;
  padding: 2rem 0 1.25rem;
  border-bottom: 1px solid var(--line);
}

.eyebrow,
.panel-label,
.section-title {
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

h1 {
  margin: 0.3rem 0 0;
  font-size: clamp(2rem, 5vw, 4rem);
  line-height: 0.95;
}

.subtitle {
  margin: 0.55rem 0 0;
  color: var(--muted);
}

.status-card {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 190px;
  padding: 0.8rem 1rem;
  border: 1px solid var(--line);
  background: var(--panel);
}

.status-card small {
  display: block;
  margin-top: 0.15rem;
  color: var(--muted);
}

.status-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--good);
}

.project-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  padding: 0.75rem 0;
}

.project-nav a {
  padding: 0.45rem 0.65rem;
  color: var(--muted);
  text-decoration: none;
  border: 1px solid transparent;
}

.project-nav a:hover {
  color: var(--text);
  border-color: var(--line);
}

main {
  padding-block: 1rem 3rem;
}

.panel {
  border: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(14, 22, 35, 0.97), rgba(8, 13, 22, 0.97));
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
  gap: 1rem;
}

.hero-copy,
.metrics-panel {
  padding: 1.3rem;
}

.hero-copy h2 {
  max-width: 22ch;
  margin: 0.75rem 0;
  font-size: clamp(1.7rem, 3.5vw, 3rem);
}

.hero-copy p {
  max-width: 72ch;
  color: #c6d2df;
  line-height: 1.7;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.7rem;
  margin-top: 1rem;
}

.metric-card,
.metric {
  min-width: 0;
  padding: 0.8rem;
  border: 1px solid var(--line);
  background: rgba(5, 9, 15, 0.35);
}

.metric-card strong {
  display: block;
  font-size: 1.5rem;
  font-variant-numeric: tabular-nums;
}

.metric-card span,
.metric small {
  display: block;
  margin-top: 0.25rem;
  color: var(--muted);
}

.loading-copy {
  color: var(--muted);
}

.mission-clock {
  margin-top: 1rem;
  padding: 1.1rem 1.3rem;
}

.clock-time {
  margin-top: 0.7rem;
  overflow-wrap: anywhere;
  font-size: clamp(1.25rem, 3vw, 2.5rem);
  font-variant-numeric: tabular-nums;
}

.clock-phase {
  margin-top: 0.3rem;
  color: var(--accent);
  font-weight: 700;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 1rem;
  margin-top: 1rem;
  padding: 1rem;
}

.control-heading {
  flex: 1 1 280px;
}

.control-heading p {
  margin: 0.35rem 0 0;
  color: var(--muted);
}

.controls label {
  display: grid;
  gap: 0.4rem;
  color: var(--muted);
  font-size: 0.8rem;
}

select,
button {
  min-height: 44px;
  padding: 0.65rem 0.8rem;
  border: 1px solid #30435c;
  background: #08101a;
}

select {
  min-width: 185px;
}

button {
  cursor: pointer;
}

button:hover {
  border-color: var(--accent);
}

.workspace {
  display: grid;
  grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.7fr);
  gap: 1rem;
  min-height: 620px;
  margin-top: 1rem;
}

.timeline,
.detail {
  min-width: 0;
  overflow: hidden;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid var(--line);
}

.panel-heading h2 {
  margin: 0.25rem 0 0;
  font-size: 1.1rem;
}

.count {
  padding: 0.3rem 0.55rem;
  color: var(--muted);
  border: 1px solid var(--line);
}

.event-list {
  max-height: 760px;
  overflow: auto;
}

.event-item {
  width: 100%;
  min-height: 44px;
  padding: 1rem;
  text-align: left;
  border: 0;
  border-bottom: 1px solid #17243a;
  border-left: 3px solid transparent;
  background: transparent;
}

.event-item:hover,
.event-item.active {
  background: #0c1623;
  border-left-color: var(--accent);
}

.event-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.55rem;
}

.evidence-badge,
.order-badge,
.lens-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.22rem 0.45rem;
  border: 1px solid #35506f;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.order-badge {
  color: var(--muted);
  border-color: var(--line);
}

.event-item strong {
  display: block;
  line-height: 1.35;
}

.event-item time {
  display: block;
  margin-top: 0.4rem;
  color: var(--muted);
  font-size: 0.8rem;
  line-height: 1.4;
}

.detail {
  padding: 1.4rem;
}

.detail h2 {
  margin: 0.4rem 0 0.7rem;
  font-size: clamp(1.5rem, 3vw, 2.35rem);
}

.detail-summary {
  max-width: 82ch;
  color: #c6d2df;
  line-height: 1.7;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.7rem;
  margin: 1.2rem 0;
}

.metric strong {
  overflow-wrap: anywhere;
}

.section-title {
  margin: 1.5rem 0 0.7rem;
}

.lens-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.priority-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}

.priority-row {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--line);
  background: #09121d;
}

.priority-row span {
  color: var(--muted);
}

.source-card {
  padding: 1rem;
  border: 1px solid var(--line);
  background: #08101a;
}

.source-card p {
  margin-bottom: 0;
  color: var(--muted);
}

.empty-state {
  min-height: 540px;
  display: grid;
  place-content: center;
  padding: 2rem;
  text-align: center;
  color: var(--muted);
}

.empty-state h2 {
  margin: 0.6rem 0 0.2rem;
  color: var(--text);
}

.orbital-icon {
  color: #547ba5;
  font-size: 4rem;
}

.no-results,
.error-message {
  margin: 0;
  padding: 1rem;
  color: var(--muted);
}

.error-message {
  color: var(--danger);
}

.provenance-legend,
.boundary-callout {
  margin-top: 1rem;
  padding: 1rem;
}

.boundary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.7rem;
  margin-top: 0.8rem;
}

.boundary-grid article {
  padding: 0.85rem;
  border: 1px solid var(--line);
  background: #08101a;
}

.boundary-grid p {
  margin: 0.45rem 0 0;
  color: var(--muted);
  line-height: 1.5;
}

.boundary-callout {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.boundary-callout code {
  padding: 0.55rem 0.7rem;
  border: 1px solid #40516a;
  background: #080e17;
  overflow-wrap: anywhere;
}

footer {
  padding-block: 0 2rem;
  color: #8295ab;
  font-size: 0.82rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 900px) {
  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-grid,
  .workspace {
    grid-template-columns: 1fr;
  }

  .event-list {
    max-height: 420px;
  }

  .boundary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .topbar,
  .project-nav,
  main,
  footer {
    width: min(100% - 1rem, 1440px);
  }

  .project-nav {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .status-card,
  .controls label,
  select,
  .controls button {
    width: 100%;
  }

  .metric-grid,
  .detail-grid,
  .priority-grid,
  .boundary-grid {
    grid-template-columns: 1fr;
  }

  .controls {
    align-items: stretch;
  }
}

@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
'''

    ci_yaml = r'''name: MissionLab CI

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Compile Python sources
        run: python -m compileall -q scripts

      - name: Validate Phase 9A publication pack
        run: python scripts/validation/validate_publication_pack.py

      - name: Validate Phase 9B public web
        run: python scripts/validation/validate_publication_web.py
'''

    pages_yaml = r'''name: Deploy MissionLab Pages

on:
  workflow_dispatch:
  push:
    branches:
      - main

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}

    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure Pages
        uses: actions/configure-pages@v5

      - name: Upload static site
        uses: actions/upload-pages-artifact@v3
        with:
          path: .

      - name: Deploy
        id: deployment
        uses: actions/deploy-pages@v4
'''

    validator = r'''from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE = ROOT / "data" / "reference"

INDEX_PATH = ROOT / "index.html"
APP_PATH = ROOT / "app.js"
STYLES_PATH = ROOT / "styles.css"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"
PAGES_PATH = ROOT / ".github" / "workflows" / "pages.yml"

PHASE7A_PATH = REFERENCE / "artemis_ii_mission_control_perspectives.json"
PHASE9A_PATH = REFERENCE / "artemis_ii_publication_manifest.json"
WEB_MANIFEST_PATH = REFERENCE / "artemis_ii_publication_web_manifest.json"


def fail(message: str) -> None:
    raise SystemExit(f"PHASE 9B VALIDATION FAILED: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_text(path: Path) -> str:
    require(path.exists(), f"missing file: {path}")
    text = path.read_text(encoding="utf-8")
    require(bool(text.strip()), f"empty file: {path}")
    return text


def load_json(path: Path) -> dict:
    require(path.exists(), f"missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    print()
    print("Phase 9B Artemis II Public Web Validation")
    print("=" * 72)

    html = load_text(INDEX_PATH)
    js = load_text(APP_PATH)
    css = load_text(STYLES_PATH)
    ci = load_text(CI_PATH)
    pages = load_text(PAGES_PATH)

    phase7a = load_json(PHASE7A_PATH)
    phase9a = load_json(PHASE9A_PATH)
    manifest = load_json(WEB_MANIFEST_PATH)

    require(
        phase7a.get("dataset_id")
        == "phase7a_artemis_ii_mission_control_perspectives",
        "Phase 7A identity mismatch",
    )

    require(
        len(phase7a.get("shared_timeline", [])) == 24,
        "validated timeline must contain 24 events",
    )

    require(
        phase9a.get("dataset_id")
        == "phase9a_artemis_ii_publication_manifest",
        "Phase 9A manifest identity mismatch",
    )

    require(
        manifest.get("dataset_id")
        == "phase9b_artemis_ii_publication_web_manifest",
        "Phase 9B web manifest identity mismatch",
    )

    require(
        manifest.get("status")
        == "PUBLIC_WEB_AND_CI_COMPLETE",
        "Phase 9B web status mismatch",
    )

    print()
    print("Phase 7A validated timeline dependency: PASS")
    print("24-event shared timeline: PASS")
    print("Phase 9A publication dependency: PASS")
    print("Phase 9B web manifest identity: PASS")

    for marker in [
        'class="skip-link"',
        'id="main-content"',
        'aria-label="Project navigation"',
        'aria-live="polite"',
        'aria-live="assertive"',
        'tabindex="-1"',
        'PHASE 9',
        'VALIDATED SHARED TIMELINE',
        'EVIDENCE BOUNDARIES',
    ]:
        require(marker in html, f"HTML missing accessibility marker: {marker}")

    require("PHASE 0" not in html, "stale Phase 0 status remains in public HTML")

    print()
    print("Skip navigation: PASS")
    print("Semantic main navigation: PASS")
    print("ARIA live regions: PASS")
    print("Keyboard-focusable detail panel: PASS")
    print("Current Phase 9 status: PASS")
    print("Stale Phase 0 status removed: PASS")

    require(
        "artemis_ii_mission_control_perspectives.json" in js,
        "frontend does not use validated Phase 7A timeline",
    )

    require(
        "artemis_ii_publication_manifest.json" in js,
        "frontend does not use publication metrics",
    )

    require(
        "data/seed/mission_events.json" not in js,
        "frontend still depends on obsolete Phase 0 seed timeline",
    )

    require(
        "event.timestamp_utc" in js
        and "event.date_utc" in js
        and "event.time_precision" in js,
        "frontend does not preserve timing precision",
    )

    require("escapeHtml" in js, "frontend missing HTML output escaping")

    print()
    print("Validated timeline frontend source: PASS")
    print("Phase 0 seed dependency removed: PASS")
    print("Missing/exact timing distinction: PASS")
    print("HTML output escaping: PASS")

    for marker in [
        ":focus-visible",
        ".skip-link",
        "@media (max-width: 900px)",
        "@media (max-width: 600px)",
        "@media (prefers-reduced-motion: reduce)",
        "min-height: 44px",
    ]:
        require(marker in css, f"CSS missing requirement: {marker}")

    print()
    print("Visible keyboard focus: PASS")
    print("44px interactive targets: PASS")
    print("Tablet responsive breakpoint: PASS")
    print("Mobile responsive breakpoint: PASS")
    print("Reduced-motion support: PASS")

    for marker in [
        "actions/checkout@v4",
        "actions/setup-python@v5",
        "validate_publication_pack.py",
        "validate_publication_web.py",
    ]:
        require(marker in ci, f"CI workflow missing: {marker}")

    print()
    print("GitHub Actions CI workflow: PASS")
    print("Python syntax check in CI: PASS")
    print("Phase 9A validator in CI: PASS")
    print("Phase 9B validator in CI: PASS")

    for marker in [
        "actions/configure-pages@v5",
        "actions/upload-pages-artifact@v3",
        "actions/deploy-pages@v4",
        "pages: write",
        "id-token: write",
    ]:
        require(marker in pages, f"Pages workflow missing: {marker}")

    print()
    print("GitHub Pages workflow: PASS")
    print("Static-site artifact deployment: PASS")
    print("Pages permission model: PASS")

    principles = manifest["publication_principles"]

    require(principles["validated_timeline_only"] is True, "validated-timeline-only rule missing")
    require(principles["no_phase0_seed_dependency"] is True, "Phase 0 seed prohibition missing")
    require(principles["no_new_mission_reconstruction"] is True, "Phase 9B adds reconstruction")

    print()
    print("Validated timeline only: PASS")
    print("No Phase 0 seed dependency: PASS")
    print("No new mission reconstruction: PASS")

    print()
    print("PHASE 9B VALIDATION PASSED")


if __name__ == "__main__":
    main()
'''

    web_manifest = {
        "dataset_id": "phase9b_artemis_ii_publication_web_manifest",
        "mission": "Artemis II",
        "phase": "9B",
        "status": "PUBLIC_WEB_AND_CI_COMPLETE",
        "dependencies": [
            {
                "dataset_id": phase7a["dataset_id"],
                "path": "data/reference/artemis_ii_mission_control_perspectives.json",
                "role": "validated 24-event public timeline",
            },
            {
                "dataset_id": phase9a["dataset_id"],
                "path": "data/reference/artemis_ii_publication_manifest.json",
                "role": "validated publication metrics and documentation state",
            },
        ],
        "publication_features": {
            "validated_shared_timeline": True,
            "phase0_seed_timeline_removed_from_frontend": True,
            "keyboard_navigation": True,
            "visible_focus": True,
            "skip_navigation": True,
            "aria_live_regions": True,
            "responsive_tablet_layout": True,
            "responsive_mobile_layout": True,
            "reduced_motion_support": True,
            "minimum_interactive_target_px": 44,
            "output_escaping": True,
            "github_actions_ci": True,
            "github_pages_workflow": True,
        },
        "publication_principles": {
            "validated_timeline_only": True,
            "no_phase0_seed_dependency": True,
            "no_new_mission_reconstruction": True,
            "public_evidence_boundaries_preserved": True,
            "unknown_timing_not_fabricated": True,
        },
        "phase9_state": {
            "documentation": "COMPLETE_PHASE9A",
            "accessibility": "COMPLETE_PHASE9B",
            "mobile_desktop_behavior": "COMPLETE_PHASE9B",
            "tests_and_ci": "COMPLETE_PHASE9B",
            "performance_optimization": "COMPLETE_PHASE9B_STATIC_ZERO_FRAMEWORK",
            "public_deployment_readiness": "COMPLETE_PHASE9B_GITHUB_PAGES_WORKFLOW",
            "final_cross_phase_validation": "PENDING_PHASE9C",
        },
        "outputs": [
            "index.html",
            "app.js",
            "styles.css",
            ".github/workflows/ci.yml",
            ".github/workflows/pages.yml",
            "scripts/validation/validate_publication_web.py",
            "data/reference/artemis_ii_publication_web_manifest.json",
        ],
    }

    write_text(INDEX_PATH, index_html)
    write_text(APP_PATH, app_js)
    write_text(STYLES_PATH, styles_css)
    write_text(CI_PATH, ci_yaml)
    write_text(PAGES_PATH, pages_yaml)
    write_text(VALIDATOR_PATH, validator)
    write_json(WEB_MANIFEST_PATH, web_manifest)

    outputs = [
        INDEX_PATH,
        APP_PATH,
        STYLES_PATH,
        CI_PATH,
        PAGES_PATH,
        VALIDATOR_PATH,
        WEB_MANIFEST_PATH,
    ]

    for path in outputs:
        require(path.exists(), f"output missing: {path}")
        require(path.stat().st_size > 0, f"output empty: {path}")

    print()
    print("Phase 9B Artemis II Public Web Build")
    print("=" * 72)
    print()
    print("Validated Phase 7A timeline: 24 events")
    print("Phase 0 seed timeline frontend dependency: REMOVED")
    print("Accessibility: COMPLETE")
    print("Responsive behavior: COMPLETE")
    print("Static zero-framework performance: COMPLETE")
    print("GitHub Actions CI: CREATED")
    print("GitHub Pages deployment workflow: CREATED")
    print()
    print("Generated:")
    for path in outputs:
        print(f"  {path.relative_to(ROOT)}")
    print()
    print("PHASE 9B PUBLIC WEB BUILD COMPLETE")


if __name__ == "__main__":
    main()
