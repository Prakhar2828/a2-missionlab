const state = {
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
