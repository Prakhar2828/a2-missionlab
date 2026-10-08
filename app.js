const state = { events: [], selectedId: null };

const els = {
  eventList: document.querySelector('#event-list'),
  eventCount: document.querySelector('#event-count'),
  detail: document.querySelector('#detail-panel'),
  domain: document.querySelector('#domain-filter'),
  provenance: document.querySelector('#provenance-filter'),
  criticality: document.querySelector('#criticality-filter'),
  reset: document.querySelector('#reset-btn'),
  clockTime: document.querySelector('#clock-time'),
  clockPhase: document.querySelector('#clock-phase'),
};

function badgeClass(provenance) {
  return ({
    FLIGHT_DATA: 'flight',
    NASA_REPORTED: 'nasa',
    DERIVED: 'derived',
    MODEL: 'model',
    SYNTHETIC: 'synthetic',
  })[provenance] || 'nasa';
}

function prettyUtc(value) {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC', year: 'numeric', month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }).format(new Date(value)) + ' UTC';
}

function filteredEvents() {
  return state.events.filter(event => {
    const domain = els.domain.value === 'ALL' || event.domain === els.domain.value;
    const provenance = els.provenance.value === 'ALL' || event.provenance_class === els.provenance.value;
    const criticality = els.criticality.value === 'ALL' || event.mission_criticality === els.criticality.value;
    return domain && provenance && criticality;
  });
}

function renderList() {
  const events = filteredEvents().sort((a,b) => new Date(a.timestamp_utc) - new Date(b.timestamp_utc));
  els.eventCount.textContent = events.length;
  els.eventList.innerHTML = events.map(event => `
    <button class="event-item ${state.selectedId === event.id ? 'active' : ''}" data-id="${event.id}">
      <div class="event-meta">
        <span class="badge ${badgeClass(event.provenance_class)}">${event.provenance_class.replace('_',' ')}</span>
        <span class="criticality ${event.mission_criticality}">${event.mission_criticality}</span>
      </div>
      <strong>${event.title}</strong>
      <time>${prettyUtc(event.timestamp_utc)}</time>
    </button>
  `).join('') || '<div style="padding:1rem;color:#91a4ba">No events match the current filters.</div>';

  els.eventList.querySelectorAll('.event-item').forEach(button => {
    button.addEventListener('click', () => selectEvent(button.dataset.id));
  });
}

function decisionHtml(thread) {
  if (!thread) return '<p class="detail-summary">No decision thread is attached to this event yet.</p>';
  const order = [
    ['DETECTION', thread.detection], ['EVIDENCE', thread.evidence], ['CONSTRAINT', thread.constraint],
    ['OPTIONS', thread.options?.join(' · ')], ['DECISION', thread.decision], ['ACTION', thread.action], ['OUTCOME', thread.outcome]
  ];
  return order.filter(([,value]) => value).map(([label,value]) => `
    <div class="thread-step"><strong>${label}</strong><p>${value}</p></div>
  `).join('');
}

function selectEvent(id) {
  const event = state.events.find(item => item.id === id);
  if (!event) return;
  state.selectedId = id;
  els.clockTime.textContent = prettyUtc(event.timestamp_utc);
  els.clockPhase.textContent = event.mission_phase;
  els.detail.innerHTML = `
    <div class="event-meta">
      <span class="badge ${badgeClass(event.provenance_class)}">${event.provenance_class.replace('_',' ')}</span>
      <span class="criticality ${event.mission_criticality}">${event.mission_criticality}</span>
    </div>
    <h2>${event.title}</h2>
    <p class="detail-summary">${event.summary}</p>
    <div class="detail-grid">
      <div class="metric"><small>UTC</small><strong>${prettyUtc(event.timestamp_utc)}</strong></div>
      <div class="metric"><small>Mission phase</small><strong>${event.mission_phase}</strong></div>
      <div class="metric"><small>Domain</small><strong>${event.domain}</strong></div>
    </div>
    <div class="section-title">AFFECTED DISCIPLINES</div>
    <div class="disciplines">${event.affected_disciplines.map(x => `<span class="discipline">${x}</span>`).join('')}</div>
    <div class="section-title">DECISION THREAD</div>
    <div class="decision-thread">${decisionHtml(event.decision_thread)}</div>
    <div class="section-title">SOURCE & PROVENANCE</div>
    <div class="source-card">
      <strong>${event.source_title}</strong>
      <p>${event.source_agency} · ${event.provenance_class}</p>
      <a href="${event.source_url}" target="_blank" rel="noreferrer">Open primary public source ↗</a>
    </div>
    <div class="section-title">LIMITATIONS</div>
    <div class="limitations">${event.limitations || 'No limitation note recorded.'}</div>
  `;
  renderList();
}

async function init() {
  const response = await fetch('./data/seed/mission_events.json');
  if (!response.ok) throw new Error(`Could not load mission events: ${response.status}`);
  state.events = await response.json();

  [...new Set(state.events.map(event => event.domain))].sort().forEach(domain => {
    const option = document.createElement('option');
    option.value = domain;
    option.textContent = domain;
    els.domain.appendChild(option);
  });

  [els.domain, els.provenance, els.criticality].forEach(control => control.addEventListener('change', renderList));
  els.reset.addEventListener('click', () => {
    els.domain.value = 'ALL'; els.provenance.value = 'ALL'; els.criticality.value = 'ALL'; renderList();
  });
  renderList();
  if (state.events.length) selectEvent(state.events[0].id);
}

init().catch(error => {
  console.error(error);
  els.eventList.innerHTML = `<div style="padding:1rem;color:#ff9a9a">${error.message}. Run this project from a local web server instead of opening index.html directly.</div>`;
});
