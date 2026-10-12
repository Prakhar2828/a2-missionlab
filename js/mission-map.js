const SVG_NS = 'http://www.w3.org/2000/svg';

const EVENT_PROGRESS = Object.freeze({
  A2_LAUNCH: 0.00,
  A2_UWMS_FD1_FAULT: 0.035,
  A2_UWMS_FD1_RESTORED: 0.055,
  A2_PROXIMITY_OPERATIONS: 0.09,
  A2_UWMS_FD4_VENT_ISSUE: 0.19,
  A2_OTC3: 0.27,
  A2_LUNAR_SOI_ENTRY: 0.34,
  A2_EARTHSET: 0.405,
  A2_PERICYNTHION: 0.445,
  A2_EARTHRISE: 0.475,
  A2_TOTAL_SOLAR_ECLIPSE: 0.515,
  A2_LUNAR_SOI_EXIT: 0.56,
  A2_RTC1: 0.64,
  A2_RETURN_LINK_LOSS: 0.73,
  A2_RTC2: 0.77,
  A2_RTC3: 0.875,
  A2_DSN_NSN_HANDOVER: 0.925,
  A2_CM_SM_SEPARATION: 0.948,
  A2_ENTRY_INTERFACE: 0.962,
  A2_ENTRY_BLACKOUT: 0.972,
  A2_ENTRY_REACQUISITION: 0.979,
  A2_DROGUE_DEPLOYMENT: 0.987,
  A2_MAIN_DEPLOYMENT: 0.993,
  A2_SPLASHDOWN: 1.00,
});

const MAJOR_EVENTS = new Set([
  'A2_LAUNCH',
  'A2_OTC3',
  'A2_EARTHSET',
  'A2_PERICYNTHION',
  'A2_EARTHRISE',
  'A2_RTC1',
  'A2_ENTRY_INTERFACE',
  'A2_ENTRY_BLACKOUT',
  'A2_SPLASHDOWN',
]);


const STATIC_LABELS = Object.freeze({});

function svgEl(name, attrs = {}, text = null) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
  if (text !== null) element.textContent = text;
  return element;
}

function addStop(parent, offset, color, opacity = 1) {
  parent.appendChild(svgEl('stop', {
    offset,
    'stop-color': color,
    'stop-opacity': opacity,
  }));
}

export class MissionMap {
  constructor(svg, events, onSelect) {
    this.svg = svg;
    this.events = events;
    this.onSelect = onSelect;
    this.selectedId = null;
    this.reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.markerById = new Map();
    this.draw();
  }

  draw() {
    this.svg.innerHTML = '';

    const defs = svgEl('defs');

    const earthGradient = svgEl('radialGradient', {
      id: 'earthGradient',
      cx: '34%',
      cy: '28%',
      r: '72%',
    });
    addStop(earthGradient, '0%', '#dff8ff');
    addStop(earthGradient, '10%', '#5fc4ee');
    addStop(earthGradient, '45%', '#2677b8');
    addStop(earthGradient, '75%', '#0d3e70');
    addStop(earthGradient, '100%', '#06182b');

    const moonGradient = svgEl('radialGradient', {
      id: 'moonGradient',
      cx: '34%',
      cy: '30%',
      r: '72%',
    });
    addStop(moonGradient, '0%', '#e2e5e7');
    addStop(moonGradient, '42%', '#a7adb1');
    addStop(moonGradient, '72%', '#687178');
    addStop(moonGradient, '100%', '#2d3339');

    const pathGradient = svgEl('linearGradient', {
      id: 'pathGradient',
      x1: '0%',
      x2: '100%',
    });
    addStop(pathGradient, '0%', '#4f9fe4', .45);
    addStop(pathGradient, '48%', '#73e2ff', .95);
    addStop(pathGradient, '100%', '#7db7ef', .55);

    const glow = svgEl('filter', {
      id: 'glow',
      x: '-50%',
      y: '-50%',
      width: '200%',
      height: '200%',
    });
    glow.appendChild(svgEl('feGaussianBlur', {
      stdDeviation: '7',
      result: 'coloredBlur',
    }));
    const merge = svgEl('feMerge');
    merge.appendChild(svgEl('feMergeNode', { in: 'coloredBlur' }));
    merge.appendChild(svgEl('feMergeNode', { in: 'SourceGraphic' }));
    glow.appendChild(merge);

    defs.append(earthGradient, moonGradient, pathGradient, glow);
    this.svg.appendChild(defs);

    const stars = svgEl('g', { opacity: '.72' });
    const coords = [
      [54,74,1.2],[120,120,.9],[188,54,1.1],[260,102,.8],[332,46,1.1],
      [420,95,.8],[506,58,1.2],[592,120,.8],[682,52,1.1],[752,96,.7],
      [842,54,1.2],[912,126,.9],[70,235,.8],[214,228,1],[348,180,.7],
      [514,220,.85],[650,184,1],[896,246,.8],[38,418,1.1],[162,486,.8],
      [302,432,1],[452,510,.7],[590,448,1.1],[734,512,.8],[892,432,1],
      [246,560,.75],[516,572,.85],[824,560,.7]
    ];
    coords.forEach(([cx, cy, r]) => {
      stars.appendChild(svgEl('circle', {
        cx,
        cy,
        r,
        fill: '#dcecff',
      }));
    });
    this.svg.appendChild(stars);

    this.path = svgEl('path', {
      id: 'mission-trajectory',
      d: 'M 128 358 C 232 165, 494 105, 742 228 C 853 283, 852 397, 758 422 C 672 445, 642 330, 735 260 C 650 466, 405 544, 130 386',
      fill: 'none',
      stroke: 'url(#pathGradient)',
      'stroke-width': '2.4',
      'stroke-linecap': 'round',
      'stroke-dasharray': '4 8',
      opacity: '.95',
    });

    const pathGlow = this.path.cloneNode(true);
    pathGlow.setAttribute('stroke-width', '10');
    pathGlow.setAttribute('opacity', '.08');
    pathGlow.removeAttribute('stroke-dasharray');

    this.svg.append(pathGlow, this.path);

    const earthHalo = svgEl('circle', {
      cx: 128,
      cy: 372,
      r: 92,
      fill: 'none',
      stroke: '#4d9ee4',
      'stroke-width': '1',
      opacity: '.12',
    });
    const earth = svgEl('circle', {
      cx: 128,
      cy: 372,
      r: 63,
      fill: 'url(#earthGradient)',
      filter: 'url(#glow)',
    });
    const earthShade = svgEl('path', {
      d: 'M 128 309 A 63 63 0 0 1 128 435 A 46 63 0 0 0 128 309',
      fill: 'rgba(0,0,0,.32)',
    });
    const earthLabel = svgEl('text', {
      x: 128,
      y: 464,
      fill: '#8ea8bf',
      'font-size': '13',
      'font-family': 'Inter, system-ui, sans-serif',
      'text-anchor': 'middle',
      'letter-spacing': '2',
    }, 'EARTH');

    const moonHalo = svgEl('circle', {
      cx: 760,
      cy: 320,
      r: 100,
      fill: 'none',
      stroke: '#d2dae1',
      'stroke-width': '1',
      opacity: '.08',
    });
    const moon = svgEl('circle', {
      cx: 760,
      cy: 320,
      r: 67,
      fill: 'url(#moonGradient)',
      filter: 'url(#glow)',
    });
    const crater1 = svgEl('circle', {
      cx: 735,
      cy: 295,
      r: 13,
      fill: 'rgba(41,47,52,.20)',
    });
    const crater2 = svgEl('circle', {
      cx: 786,
      cy: 345,
      r: 18,
      fill: 'rgba(41,47,52,.18)',
    });
    const crater3 = svgEl('circle', {
      cx: 782,
      cy: 286,
      r: 8,
      fill: 'rgba(41,47,52,.18)',
    });
    const moonLabel = svgEl('text', {
      x: 760,
      y: 414,
      fill: '#9eaab4',
      'font-size': '13',
      'font-family': 'Inter, system-ui, sans-serif',
      'text-anchor': 'middle',
      'letter-spacing': '2',
    }, 'MOON');

    this.occultation = svgEl('g', { opacity: '0' });
    const occultLine = svgEl('line', {
      x1: 176,
      y1: 364,
      x2: 692,
      y2: 326,
      stroke: '#68e4ff',
      'stroke-width': '1.3',
      'stroke-dasharray': '5 6',
      opacity: '.42',
    });
    this.occultation.append(occultLine);

    this.svg.append(
      earthHalo,
      earth,
      earthShade,
      earthLabel,
      moonHalo,
      moon,
      crater1,
      crater2,
      crater3,
      moonLabel,
      this.occultation
    );

    const eventLayer = svgEl('g', { class: 'map-event-layer' });
    const length = this.path.getTotalLength();

    this.events.forEach((event, index) => {
      const progress =
        EVENT_PROGRESS[event.event_id] ??
        (index / Math.max(1, this.events.length - 1));
      const point = this.path.getPointAtLength(progress * length);
      const major = MAJOR_EVENTS.has(event.event_id);

      const group = svgEl('g', {
        class: `map-event ${major ? 'major' : ''}`,
        tabindex: '0',
        role: 'button',
        'aria-label': `${event.name}. ${event.timestamp_utc ?? event.time_precision ?? ''}`,
        'data-event-id': event.event_id,
      });
      group.style.cursor = 'pointer';

      const ring = svgEl('circle', {
        cx: point.x,
        cy: point.y,
        r: major ? 7 : 5,
        fill: '#030812',
        stroke: major ? '#68e4ff' : '#6a8197',
        'stroke-width': major ? '2' : '1.5',
        opacity: major ? '1' : '.72',
      });

      if (major) {
        const glowRing = svgEl('circle', {
          cx: point.x,
          cy: point.y,
          r: 12,
          fill: 'none',
          stroke: '#68e4ff',
          'stroke-width': '1',
          opacity: '.13',
        });
        group.appendChild(glowRing);
      }

      group.appendChild(ring);

      const staticLabel = STATIC_LABELS[event.event_id];
      if (staticLabel) {
        const label = svgEl('text', {
          x: point.x + staticLabel.dx,
          y: point.y + staticLabel.dy,
          fill: '#89a4bd',
          'font-size': '9',
          'font-family': 'Inter, system-ui, sans-serif',
          'font-weight': '800',
          'text-anchor': staticLabel.anchor,
          'letter-spacing': '1.2',
          class: 'map-phase-label',
          opacity: '.82',
        }, staticLabel.text);
        group.appendChild(label);
      }

      group.addEventListener('click', () => this.onSelect(event.event_id));
      group.addEventListener('keydown', (eventKey) => {
        if (eventKey.key === 'Enter' || eventKey.key === ' ') {
          eventKey.preventDefault();
          this.onSelect(event.event_id);
        }
      });

      eventLayer.appendChild(group);
      this.markerById.set(event.event_id, {
        group,
        ring,
        point,
        progress,
      });
    });

    this.svg.appendChild(eventLayer);

    this.craftGroup = svgEl('g', {
      class: 'orion-craft',
      filter: 'url(#glow)',
    });
    const craftPulse = svgEl('circle', {
      cx: 0,
      cy: 0,
      r: 17,
      fill: 'none',
      stroke: '#68e4ff',
      'stroke-width': '1.5',
      opacity: '.22',
      class: 'orion-craft-pulse',
    });
    const craftBody = svgEl('path', {
      d: 'M -11 -6 L 5 -6 L 12 0 L 5 6 L -11 6 L -16 0 Z',
      fill: '#d9efff',
      stroke: '#68e4ff',
      'stroke-width': '1',
    });
    const craftWindow = svgEl('circle', {
      cx: -2,
      cy: 0,
      r: 2.3,
      fill: '#174a70',
    });
    const craftTail = svgEl('path', {
      d: 'M -16 -4 L -23 -9 L -23 9 L -16 4 Z',
      fill: '#7c95aa',
      opacity: '.9',
    });
    this.craftGroup.append(craftPulse, craftTail, craftBody, craftWindow);
    this.svg.appendChild(this.craftGroup);

        this.select(this.events[0]?.event_id, false);
  }

  select(eventId, animate = true) {
    const marker = this.markerById.get(eventId);
    const event = this.events.find((item) => item.event_id === eventId);
    if (!marker || !event) return;

    if (this.selectedId && this.markerById.has(this.selectedId)) {
      const previous = this.markerById.get(this.selectedId);
      previous.ring.setAttribute('fill', '#030812');
      previous.ring.setAttribute(
        'stroke-width',
        MAJOR_EVENTS.has(this.selectedId) ? '2' : '1.5'
      );
    }

    this.selectedId = eventId;
    marker.ring.setAttribute('fill', '#68e4ff');
    marker.ring.setAttribute('stroke-width', '3');

    const target = marker.point;
    const current = this.currentPoint ?? target;

    if (animate && !this.reduceMotion) {
      this.animateCraft(current, target, 420);
    } else {
      this.setCraftPosition(target);
    }

    const lunarOcclusionIds = new Set([
      'A2_EARTHSET',
      'A2_PERICYNTHION',
      'A2_EARTHRISE',
    ]);
    this.occultation.setAttribute(
      'opacity',
      lunarOcclusionIds.has(eventId) ? '1' : '0'
    );
  }

  animateCraft(from, to, duration) {
    const start = performance.now();

    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);

      const point = {
        x: from.x + (to.x - from.x) * eased,
        y: from.y + (to.y - from.y) * eased,
      };

      this.setCraftPosition(point);

      if (t < 1) {
        requestAnimationFrame(tick);
      }
    };

    requestAnimationFrame(tick);
  }

  setCraftPosition(point) {
    this.currentPoint = {
      x: point.x,
      y: point.y,
    };
    this.craftGroup.setAttribute(
      'transform',
      `translate(${point.x} ${point.y}) scale(.85)`
    );
  }

}

export function isMajorEvent(eventId) {
  return MAJOR_EVENTS.has(eventId);
}
