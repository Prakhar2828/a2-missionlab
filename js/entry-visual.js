(() => {
  'use strict';

  if (!window.A2 || !window.A2EntryModel) {
    throw new Error('Entry visual companion requires A2 core and A2EntryModel.');
  }

  const { $, $$, clamp, lerp, fitCanvas, sceneRect, drawStars, drawCanvasLabel } = window.A2;
  const model = window.A2EntryModel;
  const root = $('#entry-visual-companion');
  if (!root) return;

  const canvas = $('#entry-visual-canvas');
  const scrubber = $('#entry-visual-scrubber');
  const play = $('#entry-visual-play');
  const reset = $('#entry-visual-reset');
  const phaseButtons = $('#entry-visual-phase-buttons');
  const qa = /(?:^|[?&])(?:entry-qa|phase-r-qa)=1(?:&|$)/.test(location.search);

  const anchors = Object.freeze([
    { id: 'space', label: 'Space edge', t: 0, note: 'Orion approaches the sensible atmosphere from near-space conditions.' },
    { id: 'entry', label: 'Atmospheric entry', t: 85, note: 'Modeled external heating is near its reconstructed peak.' },
    { id: 'descent', label: 'Descent', t: 300, note: 'Orion is descending again after the reconstructed loft / rebound.' },
    { id: 'parachutes', label: 'Parachutes / recovery', t: model.constants.mainOffset, note: 'The visual enters the public-minute parachute sequence before splashdown.' },
    { id: 'splashdown', label: 'Ocean splashdown', t: model.constants.derivedSurfaceCrossing, note: 'The visual closes at the MissionLab-derived surface crossing inside NASA’s public splashdown minute.' },
  ]);

  let visualT = 0;
  let playing = false;
  let lastFrame = 0;
  let animationFrame = 0;

  function phaseFor(t) {
    if (t < 60) return anchors[0];
    if (t < 180) return anchors[1];
    if (t < model.constants.drogueOffset) return anchors[2];
    if (t < model.constants.splashMinuteOffset) return anchors[3];
    return anchors[4];
  }

  function setText(selector, value) {
    const el = $(selector);
    if (el) el.textContent = value;
  }

  function updatePlayLabel() {
    if (!play) return;
    play.textContent = playing ? 'Pause visual sequence' : 'Play visual sequence';
    play.setAttribute('aria-pressed', String(playing));
  }

  function pointForState(scene, seconds, altitudeKm) {
    const progress = clamp(seconds / model.durationSeconds, 0, 1);
    const altitude = clamp(altitudeKm / 125, 0, 1);
    const x = scene.x + scene.width * (.81 - .50 * progress);
    const top = scene.y + scene.height * .17;
    const ocean = scene.y + scene.height * .83;
    const y = lerp(ocean, top, altitude) + Math.sin(progress * Math.PI) * scene.height * .018;
    return { x, y };
  }

  function drawAtmosphere(ctx, scene, progress) {
    const horizon = scene.y + scene.height * .84;
    const radius = Math.max(scene.width * 1.05, scene.height * .94);
    const cx = scene.x + scene.width * .48;
    const cy = horizon + radius * .73;

    for (let i = 5; i >= 1; i -= 1) {
      ctx.strokeStyle = `rgba(78,170,224,${.018 + i * .018})`;
      ctx.lineWidth = i * 5;
      ctx.beginPath();
      ctx.arc(cx, cy, radius - i * 2, Math.PI, Math.PI * 2);
      ctx.stroke();
    }

    const earth = ctx.createLinearGradient(0, horizon, 0, scene.bottom);
    earth.addColorStop(0, progress > .70 ? '#155875' : '#0a2a40');
    earth.addColorStop(1, '#04111b');
    ctx.fillStyle = earth;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, Math.PI, Math.PI * 2);
    ctx.fill();
    return horizon;
  }

  function drawOcean(ctx, scene, progress, now) {
    const oceanY = scene.y + scene.height * .82;
    if (progress < .66) return oceanY;

    const ocean = ctx.createLinearGradient(0, oceanY, 0, scene.bottom);
    ocean.addColorStop(0, 'rgba(47,126,162,.84)');
    ocean.addColorStop(1, 'rgba(15,59,82,.96)');
    ctx.fillStyle = ocean;
    ctx.fillRect(scene.x, oceanY, scene.width, scene.bottom - oceanY);

    ctx.save();
    ctx.strokeStyle = 'rgba(215,241,252,.28)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 7; i += 1) {
      const y = oceanY + i * 10;
      ctx.beginPath();
      ctx.moveTo(scene.x, y);
      ctx.quadraticCurveTo(scene.cx, y - 2 + Math.sin(now * .0015 + i) * 2, scene.right, y);
      ctx.stroke();
    }
    ctx.restore();
    return oceanY;
  }

  function drawTrajectory(ctx, scene) {
    ctx.save();
    ctx.strokeStyle = 'rgba(188,210,223,.22)';
    ctx.lineWidth = 1.25;
    ctx.setLineDash([4, 7]);
    ctx.beginPath();
    for (let seconds = 0; seconds <= model.durationSeconds; seconds += 10) {
      const p = pointForState(scene, seconds, model.altitudeAt(seconds));
      if (seconds === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  }

  function drawHeatTrail(ctx, point, state, scene, now) {
    if (visualT < 18 || visualT > 535) return;
    const intensity = clamp(
      Math.max(state.heatNormalized, state.mach > 5 ? .18 + (state.mach / 40) * .45 : 0),
      0,
      1,
    );
    const trail = clamp(scene.width * .22, 76, 190);

    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 13; i += 1) {
      const alpha = .025 + intensity * .035;
      ctx.strokeStyle = `rgba(255,${92 + i * 8},${32 + i * 3},${alpha})`;
      ctx.lineWidth = 1 + i * .14;
      ctx.beginPath();
      ctx.moveTo(point.x + 9, point.y - 5 + i * .75);
      ctx.bezierCurveTo(
        point.x + trail * .32,
        point.y - 12 + Math.sin(now * .004 + i) * 6,
        point.x + trail * .7,
        point.y + (i - 6) * 2.4,
        point.x + trail,
        point.y + (i - 6) * 3.2,
      );
      ctx.stroke();
    }

    const glow = ctx.createRadialGradient(point.x, point.y, 2, point.x, point.y, 18 + intensity * 26);
    glow.addColorStop(0, `rgba(255,164,92,${.18 + .42 * intensity})`);
    glow.addColorStop(1, 'rgba(255,92,42,0)');
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(point.x, point.y, 18 + intensity * 26, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawParachutes(ctx, point, kind, scale = 1) {
    const count = kind === 'main' ? 3 : 2;
    const spread = kind === 'main' ? 30 : 22;
    const radius = kind === 'main' ? 23 : 14;

    ctx.save();
    ctx.strokeStyle = 'rgba(244,247,248,.92)';
    ctx.fillStyle = 'rgba(232,238,241,.22)';
    ctx.lineWidth = 1.25;
    for (let i = 0; i < count; i += 1) {
      const dx = (i - (count - 1) / 2) * spread * scale;
      const cy = point.y - 44 * scale;
      ctx.beginPath();
      ctx.moveTo(point.x, point.y - 7 * scale);
      ctx.lineTo(point.x + dx, cy + radius * .12);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(point.x + dx, cy, radius * scale, Math.PI, 0);
      ctx.lineTo(point.x + dx - radius * scale, cy);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawCapsule(ctx, point, progress, scene) {
    const scale = clamp(scene.width / 820, .72, 1.08) * (1 + clamp((progress - .65) / .35, 0, 1) * .40);
    ctx.save();
    ctx.translate(point.x, point.y);
    ctx.rotate(lerp(-.52, .08, progress));
    ctx.scale(scale, scale);
    ctx.fillStyle = '#dce3e6';
    ctx.strokeStyle = '#344047';
    ctx.lineWidth = 1.3 / scale;
    ctx.beginPath();
    ctx.moveTo(-15, 10);
    ctx.quadraticCurveTo(-20, -4, 0, -19);
    ctx.quadraticCurveTo(20, -4, 15, 10);
    ctx.quadraticCurveTo(0, 18, -15, 10);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.strokeStyle = '#ff946d';
    ctx.lineWidth = 1.2 / scale;
    ctx.beginPath();
    ctx.moveTo(-12, 10);
    ctx.quadraticCurveTo(0, 15, 12, 10);
    ctx.stroke();
    ctx.restore();
  }

  function drawSplash(ctx, point, oceanY) {
    if (visualT < model.constants.splashMinuteOffset) return;
    ctx.save();
    ctx.strokeStyle = 'rgba(216,243,255,.82)';
    ctx.lineWidth = 1.4;
    for (let i = 0; i < 3; i += 1) {
      ctx.beginPath();
      ctx.ellipse(point.x, oceanY + 2, 16 + i * 12, 4 + i * 3, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.fillStyle = 'rgba(223,246,255,.58)';
    for (const dx of [-15, -6, 6, 15]) {
      ctx.beginPath();
      ctx.arc(point.x + dx, oceanY - 5 - Math.abs(dx) * .18, 2.1, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function drawPhaseStrip(ctx, scene, activePhase) {
    const items = anchors.map(anchor => ({ ...anchor, active: anchor.id === activePhase.id }));
    const gap = 5;
    const cellWidth = (scene.width - gap * (items.length - 1)) / items.length;
    const y = scene.y + 8;

    items.forEach((item, index) => {
      const x = scene.x + index * (cellWidth + gap);
      ctx.fillStyle = item.active ? 'rgba(255,139,95,.16)' : 'rgba(4,11,17,.72)';
      ctx.strokeStyle = item.active ? 'rgba(255,148,111,.70)' : 'rgba(255,255,255,.12)';
      ctx.fillRect(x, y, cellWidth, 27);
      ctx.strokeRect(x, y, cellWidth, 27);
      if (scene.width > 460 || item.id === 'splashdown') {
        drawCanvasLabel(ctx, item.label.toUpperCase(), x + cellWidth / 2, y + 18, cellWidth - 8, {
          align: 'center', size: 9.3, minSize: 7.8, color: item.active ? '#ffd2c0' : 'rgba(255,255,255,.55)', maxLines: 1,
        });
      }
    });
  }

  function draw(now = 0) {
    if (!canvas) return;
    const { ctx, w, h, layout } = fitCanvas(canvas);
    ctx.clearRect(0, 0, w, h);
    const scene = sceneRect(w, h, { top: layout.phone ? 12 : 16, bottom: layout.phone ? 12 : 18 }, layout.phone ? 8 : 12);
    const state = model.stateAt(visualT);
    const progress = state.progress;
    const phase = phaseFor(visualT);

    const bg = ctx.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, progress < .62 ? '#010308' : '#071625');
    bg.addColorStop(.55, progress < .38 ? '#050811' : '#16364e');
    bg.addColorStop(1, progress < .60 ? '#0b1b2a' : '#5a91ad');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    if (progress < .72) drawStars(ctx, w, h, layout.compact ? 70 : 110, 71, clamp(1 - progress * .9, .18, 1));
    drawAtmosphere(ctx, scene, progress);
    const oceanY = drawOcean(ctx, scene, progress, qa ? 0 : now);
    drawTrajectory(ctx, scene);

    const point = pointForState(scene, visualT, state.altitudeKm);
    drawHeatTrail(ctx, point, state, scene, qa ? 0 : now);
    if (visualT >= model.constants.drogueOffset && visualT < model.constants.mainOffset) {
      drawParachutes(ctx, point, 'drogue', layout.phone ? .72 : .9);
    }
    if (visualT >= model.constants.mainOffset && visualT < model.constants.splashMinuteOffset) {
      drawParachutes(ctx, point, 'main', layout.phone ? .70 : .88);
    }
    drawCapsule(ctx, point, progress, scene);
    drawSplash(ctx, point, oceanY);
    drawPhaseStrip(ctx, scene, phase);

    drawCanvasLabel(ctx, phase.label.toUpperCase(), scene.x + 8, scene.y + 55, Math.min(scene.width * .58, 330), {
      size: 11, minSize: 9, color: 'rgba(255,255,255,.88)', maxLines: 1,
    });
    drawCanvasLabel(ctx, 'VISUAL COMPANION · CURRENT ENGINEERING SIMULATION REMAINS SEPARATE', scene.x + 8, scene.bottom - 5, scene.width * .94, {
      size: 9.1, minSize: 7.9, color: 'rgba(255,255,255,.50)', maxLines: 1,
    });

    root.dataset.canvasPass = String(Number.isFinite(point.x) && Number.isFinite(point.y) && w > 0 && h > 0);
    root.dataset.visualSequence = 'space-entry-descent-parachutes-splashdown';
  }

  function setTime(next, fromAnimation = false) {
    visualT = clamp(Number(next) || 0, 0, model.durationSeconds);
    const state = model.stateAt(visualT);
    const phase = phaseFor(visualT);

    if (scrubber) {
      scrubber.value = String(visualT);
      scrubber.setAttribute('aria-valuetext', `${phase.label} · ${state.utc}`);
    }
    setText('#entry-visual-phase', phase.label);
    setText('#entry-visual-time', state.utc);
    setText('#entry-visual-note', phase.note);

    root.dataset.visualTime = String(visualT);
    root.dataset.visualPhase = phase.id;
    root.dataset.modelDriven = 'true';
    root.dataset.currentSimulationPreserved = 'true';

    $$('#entry-visual-phase-buttons button').forEach(button => {
      const active = button.dataset.phase === phase.id;
      button.classList.toggle('active', active);
      if (active) button.setAttribute('aria-current', 'step');
      else button.removeAttribute('aria-current');
    });

    if (!fromAnimation) draw(0);
  }

  function renderPhaseButtons() {
    if (!phaseButtons) return;
    phaseButtons.innerHTML = anchors.map(anchor => (
      `<button type="button" data-phase="${anchor.id}" data-t="${anchor.t}"><span>${anchor.label}</span></button>`
    )).join('');
    $$('button', phaseButtons).forEach(button => {
      button.addEventListener('click', () => {
        playing = false;
        updatePlayLabel();
        setTime(Number(button.dataset.t), false);
      });
    });
  }

  function tick(now) {
    if (!playing) return;
    if (!lastFrame) lastFrame = now;
    const delta = Math.min(80, now - lastFrame);
    lastFrame = now;
    setTime(visualT + delta * .18, true);
    draw(now);
    if (visualT >= model.durationSeconds) {
      playing = false;
      updatePlayLabel();
      return;
    }
    animationFrame = requestAnimationFrame(tick);
  }

  if (scrubber) {
    scrubber.min = '0';
    scrubber.max = String(model.durationSeconds);
    scrubber.step = '.1';
    scrubber.addEventListener('input', () => {
      playing = false;
      updatePlayLabel();
      setTime(Number(scrubber.value), false);
    });
  }

  play?.addEventListener('click', () => {
    playing = !playing;
    lastFrame = 0;
    updatePlayLabel();
    if (playing) {
      if (animationFrame) cancelAnimationFrame(animationFrame);
      animationFrame = requestAnimationFrame(tick);
    }
  });

  reset?.addEventListener('click', () => {
    playing = false;
    lastFrame = 0;
    updatePlayLabel();
    setTime(0, false);
  });

  addEventListener('resize', () => draw(0), { passive: true });

  renderPhaseButtons();
  updatePlayLabel();
  setTime(0, false);
  draw(0);

  if (qa) {
    root.dataset.qaAnchors = String(anchors.length === 5 && anchors[0].t === 0 && anchors[4].t === model.constants.derivedSurfaceCrossing);
    root.dataset.qaIndependent = String(
      $('#entry-scrubber') !== scrubber &&
      $('#entry-play') !== play &&
      $('#entry-flight-canvas') !== canvas
    );
  }
})();
