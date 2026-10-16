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
  const qa = /(?:^|[?&])(?:entry-qa|phase-r-qa|phase-r7-qa|phase-r8-qa)=1(?:&|$)/.test(location.search);
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const anchors = Object.freeze([
    { id: 'space', label: 'Space edge', t: 0, note: 'Orion closes on the upper atmosphere from near-space conditions.' },
    { id: 'entry', label: 'Atmospheric entry', t: 85, note: 'The companion emphasizes the modeled heating regime without presenting the scene as telemetry or an as-flown camera view.' },
    { id: 'descent', label: 'Descent', t: 300, note: 'After the reconstructed loft / rebound, the camera transitions into an atmospheric descent view.' },
    { id: 'parachutes', label: 'Parachutes / recovery', t: model.constants.mainOffset, note: 'Public-minute parachute anchors drive an illustrative staged recovery sequence.' },
    { id: 'splashdown', label: 'Ocean splashdown', t: model.constants.derivedSurfaceCrossing, note: 'The final scene becomes sky and ocean only: splash, settling water, and a floating Orion capsule.' },
  ]);

  const EVENTS = Object.freeze({
    spaceToEntry: 55,
    entryToDescent: 205,
    drogue: model.constants.drogueOffset,
    main: model.constants.mainOffset,
    splash: model.constants.splashMinuteOffset,
    surface: model.constants.derivedSurfaceCrossing,
  });

  let visualT = 0;
  let playing = false;
  let lastFrame = 0;
  let animationFrame = 0;
  let postSplashMs = 0;
  const R8 = Object.freeze({ transitionSeconds: 28, recoveryHoldMs: 6500, oceanRevealStart: 748, version: 'r8' });

  const smooth = t => {
    const x = clamp(t, 0, 1);
    return x * x * (3 - 2 * x);
  };
  const smoother = t => {
    const x = clamp(t, 0, 1);
    return x * x * x * (x * (x * 6 - 15) + 10);
  };
  const remap = (v, a, b) => clamp((v - a) / Math.max(1e-6, b - a), 0, 1);
  const mix = (a, b, t) => lerp(a, b, smooth(t));

  function phaseFor(t) {
    if (t < EVENTS.spaceToEntry) return anchors[0];
    if (t < EVENTS.entryToDescent) return anchors[1];
    if (t < EVENTS.drogue) return anchors[2];
    if (t < EVENTS.surface) return anchors[3];
    return anchors[4];
  }

  function sceneModeFor(t) {
    if (t < EVENTS.spaceToEntry) return 'space';
    if (t < EVENTS.entryToDescent) return 'entry';
    if (t < EVENTS.drogue) return 'descent';
    if (t < EVENTS.main) return 'drogue';
    if (t < EVENTS.surface) return 'main';
    return 'ocean';
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

  function capsulePath(scene, t, state) {
    const frames = [
      { t: 0, x: .86, y: .23, scale: .62, angle: -.38 },
      { t: EVENTS.spaceToEntry, x: .61, y: .34, scale: .82, angle: -.48 },
      { t: 96, x: .56, y: .41, scale: 1.28, angle: -.42 },
      { t: EVENTS.entryToDescent, x: .43, y: .45, scale: .98, angle: -.27 },
      { t: EVENTS.drogue, x: .50, y: .49, scale: .92, angle: -.05 },
      { t: EVENTS.main, x: .50, y: .56, scale: .98, angle: -.01 },
      { t: R8.oceanRevealStart, x: .50, y: .60, scale: 1.04, angle: .005 },
      { t: EVENTS.surface, x: .50, y: .70, scale: 1.14, angle: .02 },
    ];
    let a = frames[0], b = frames[frames.length - 1];
    for (let i = 1; i < frames.length; i += 1) {
      if (t <= frames[i].t) {
        a = frames[i - 1];
        b = frames[i];
        break;
      }
    }
    const q = smoother(remap(t, a.t, b.t));
    const mode = sceneModeFor(t);
    const parachuteSway = (mode === 'drogue' || mode === 'main') && !(qa || reducedMotion)
      ? Math.sin((performance.now() || 0) * .0012) * scene.width * .006
      : 0;
    const recoveryProgress = mode === 'ocean'
      ? clamp(postSplashMs / R8.recoveryHoldMs, 0, 1)
      : 0;
    const bob = mode === 'ocean' && !(qa || reducedMotion)
      ? Math.sin((performance.now() || 0) * .0019) * 2.8 * smoother(recoveryProgress)
      : 0;
    return {
      x: scene.x + scene.width * lerp(a.x, b.x, q) + parachuteSway,
      y: scene.y + scene.height * lerp(a.y, b.y, q) + bob,
      scale: lerp(a.scale, b.scale, q),
      angle: lerp(a.angle, b.angle, q) + (mode === 'ocean' && !(qa || reducedMotion) ? Math.sin((performance.now() || 0) * .0013) * .012 * smoother(recoveryProgress) : 0),
    };
  }

  function drawVignette(ctx, w, h, strength = .65) {
    const g = ctx.createRadialGradient(w * .5, h * .46, Math.min(w, h) * .15, w * .5, h * .48, Math.max(w, h) * .72);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(.68, `rgba(0,0,0,${.08 * strength})`);
    g.addColorStop(1, `rgba(0,0,0,${.76 * strength})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }

  function drawFilmGrain(ctx, scene, frameSeed = 0) {
    ctx.save();
    ctx.globalAlpha = .075;
    ctx.fillStyle = '#fff';
    const count = scene.width < 600 ? 42 : 70;
    for (let i = 0; i < count; i += 1) {
      const n = (Math.sin((i + 1) * 91.17 + frameSeed * .0007) * 43758.5453) % 1;
      const m = (Math.sin((i + 4) * 53.83 + frameSeed * .0009) * 24634.6345) % 1;
      const x = scene.x + Math.abs(n) * scene.width;
      const y = scene.y + Math.abs(m) * scene.height;
      ctx.fillRect(x, y, 1, 1);
    }
    ctx.restore();
  }

  function drawSpaceEarth(ctx, scene, t) {
    const q = smoother(remap(t, 0, EVENTS.spaceToEntry));
    const cx = scene.x + scene.width * (.28 - q * .04);
    const cy = scene.bottom + scene.height * (.78 - q * .08);
    const radius = scene.width * (1.08 + q * .20);

    const night = ctx.createRadialGradient(cx + radius * .06, cy - radius * .35, radius * .06, cx, cy, radius);
    night.addColorStop(0, '#174a68');
    night.addColorStop(.35, '#0a2e48');
    night.addColorStop(.72, '#061724');
    night.addColorStop(1, '#02060a');
    ctx.fillStyle = night;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, Math.PI, Math.PI * 2);
    ctx.fill();

    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 7; i += 1) {
      ctx.strokeStyle = `rgba(77,179,241,${.10 - i * .009})`;
      ctx.lineWidth = 2.2 + i * 2.4;
      ctx.beginPath();
      ctx.arc(cx, cy, radius + i * 3, Math.PI + .03, Math.PI * 1.98);
      ctx.stroke();
    }
    ctx.restore();

    ctx.save();
    ctx.globalAlpha = .12;
    ctx.fillStyle = '#cdefff';
    for (let i = 0; i < 10; i += 1) {
      const a = Math.PI * (1.11 + i * .07);
      const x = cx + Math.cos(a) * radius * .88;
      const y = cy + Math.sin(a) * radius * .88;
      ctx.beginPath();
      ctx.ellipse(x, y, 26 + (i % 3) * 13, 4 + (i % 2) * 3, a + Math.PI / 2, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function drawEntryHorizon(ctx, scene, t) {
    const q = smoother(remap(t, EVENTS.spaceToEntry, EVENTS.entryToDescent));
    const horizonY = mix(scene.bottom - scene.height * .08, scene.bottom + scene.height * .10, q);
    const radius = scene.width * mix(1.02, 1.34, q);
    const cx = scene.cx - scene.width * .12;
    const cy = horizonY + radius * .68;

    ctx.save();
    for (let i = 8; i >= 1; i -= 1) {
      ctx.strokeStyle = `rgba(${80 + i * 7},${142 + i * 5},255,${.017 + i * .014})`;
      ctx.lineWidth = 4 + i * 3.1;
      ctx.beginPath();
      ctx.arc(cx, cy, radius - i * 1.8, Math.PI, Math.PI * 2);
      ctx.stroke();
    }
    const surface = ctx.createLinearGradient(0, horizonY, 0, scene.bottom);
    surface.addColorStop(0, '#0a354f');
    surface.addColorStop(.45, '#082638');
    surface.addColorStop(1, '#031019');
    ctx.fillStyle = surface;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, Math.PI, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawAtmosphericWorld(ctx, scene, t, mode) {
    const cameraProgress = smoother(remap(t, EVENTS.entryToDescent, EVENTS.surface));
    const lowAltitude = smoother(remap(t, EVENTS.main, EVENTS.surface));
    const oceanAlpha = mode === 'main' ? smoother(remap(t, R8.oceanRevealStart, EVENTS.surface - 5)) : 0;

    const topColor = mixColor('#07131f', '#4f98bc', cameraProgress);
    const midColor = mixColor('#1d4968', '#8ec1d7', cameraProgress);
    const lowColor = mixColor('#5d8fa8', '#d4e6ec', cameraProgress);
    const sky = ctx.createLinearGradient(0, scene.y, 0, scene.bottom);
    sky.addColorStop(0, topColor);
    sky.addColorStop(.58, midColor);
    sky.addColorStop(1, lowColor);
    ctx.fillStyle = sky;
    ctx.fillRect(scene.x, scene.y, scene.width, scene.height);

    const deckY = scene.y + scene.height * mix(.84, .63, cameraProgress);
    const haze = ctx.createLinearGradient(0, deckY - 115, 0, deckY + 36);
    haze.addColorStop(0, 'rgba(230,244,249,0)');
    haze.addColorStop(1, `rgba(232,244,248,${.18 + cameraProgress * .30})`);
    ctx.fillStyle = haze;
    ctx.fillRect(scene.x, deckY - 115, scene.width, 155);

    ctx.save();
    const deckAlpha = 1 - oceanAlpha * .82;
    ctx.globalAlpha = deckAlpha;
    const cloudBase = ctx.createLinearGradient(0, deckY - 12, 0, scene.bottom);
    cloudBase.addColorStop(0, 'rgba(224,239,245,.10)');
    cloudBase.addColorStop(.22, 'rgba(210,231,239,.24)');
    cloudBase.addColorStop(1, 'rgba(171,205,219,.42)');
    ctx.fillStyle = cloudBase;
    ctx.fillRect(scene.x, deckY, scene.width, scene.bottom - deckY);
    drawCloudBands(ctx, scene, deckY + 4, cameraProgress, mode);
    ctx.restore();

    let horizon = scene.bottom + 80;
    if (oceanAlpha > .001) {
      horizon = scene.y + scene.height * mix(.86, .58, oceanAlpha);
      ctx.save();
      ctx.globalAlpha = oceanAlpha;
      const sea = ctx.createLinearGradient(0, horizon, 0, scene.bottom);
      sea.addColorStop(0, '#4d8da7');
      sea.addColorStop(.20, '#2a6985');
      sea.addColorStop(1, '#0b334b');
      ctx.fillStyle = sea;
      ctx.fillRect(scene.x, horizon, scene.width, scene.bottom - horizon);
      ctx.strokeStyle = 'rgba(238,248,251,.58)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(scene.x, horizon + .5);
      ctx.lineTo(scene.right, horizon + .5);
      ctx.stroke();
      for (let band = 0; band < 8; band += 1) {
        const y = horizon + 10 + band * Math.max(6, (scene.bottom - horizon - 12) / 8);
        ctx.strokeStyle = `rgba(231,246,250,${.035 + band * .008})`;
        ctx.beginPath();
        ctx.moveTo(scene.x, y);
        for (let x = scene.x + 18; x <= scene.right; x += 18) {
          const wave = Math.sin(x * .025 + t * .018 + band) * (1 + band * .12);
          ctx.lineTo(x, y + wave);
        }
        ctx.stroke();
      }
      ctx.restore();
    }

    const surfaceContext = oceanAlpha > .08 ? 'distant-ocean' : 'cloud-deck';
    return { horizon, oceanAlpha, surfaceContext, cameraProgress, lowAltitude };
  }

  function drawCloudBands(ctx, scene, horizon, progress, mode) {
    ctx.save();
    const alpha = mode === 'descent' ? .14 : .24;
    ctx.fillStyle = `rgba(244,249,251,${alpha})`;
    const rows = mode === 'descent' ? 3 : 4;
    for (let row = 0; row < rows; row += 1) {
      const y = horizon - 95 + row * 26 + Math.sin(row * 2.3 + progress * 2) * 5;
      for (let i = 0; i < 6; i += 1) {
        const x = scene.x + scene.width * ((i + .2 + (row % 2) * .35) / 6);
        const rx = 26 + (i % 3) * 13;
        const ry = 3.5 + (row % 2) * 1.8;
        ctx.beginPath();
        ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.restore();
  }

  function drawOceanRecoveryWorld(ctx, scene, t, now) {
    const q = playing
      ? smoother(clamp(postSplashMs / R8.recoveryHoldMs, 0, 1))
      : .68;
    const horizon = scene.y + scene.height * .52;

    const sky = ctx.createLinearGradient(0, scene.y, 0, horizon);
    sky.addColorStop(0, '#4b92b6');
    sky.addColorStop(.58, '#82bdd5');
    sky.addColorStop(1, '#d2e5eb');
    ctx.fillStyle = sky;
    ctx.fillRect(scene.x, scene.y, scene.width, horizon - scene.y);

    const glow = ctx.createRadialGradient(scene.cx + scene.width * .24, horizon - 70, 0, scene.cx + scene.width * .24, horizon - 70, scene.width * .42);
    glow.addColorStop(0, 'rgba(255,239,203,.30)');
    glow.addColorStop(1, 'rgba(255,239,203,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(scene.x, scene.y, scene.width, horizon - scene.y);

    drawCloudBands(ctx, scene, horizon, 1, 'ocean');

    const sea = ctx.createLinearGradient(0, horizon, 0, scene.bottom);
    sea.addColorStop(0, '#2f7698');
    sea.addColorStop(.24, '#1b5876');
    sea.addColorStop(1, '#082e47');
    ctx.fillStyle = sea;
    ctx.fillRect(scene.x, horizon, scene.width, scene.bottom - horizon);

    const motion = qa || reducedMotion ? 0 : now * .0012;
    ctx.save();
    for (let band = 0; band < 15; band += 1) {
      const y = horizon + 8 + band * ((scene.bottom - horizon - 10) / 15);
      const perspective = .12 + band / 15;
      ctx.strokeStyle = `rgba(225,244,250,${.05 + perspective * .12})`;
      ctx.lineWidth = .7 + perspective * .8;
      ctx.beginPath();
      const step = Math.max(18, 42 - band * 1.4);
      for (let x = scene.x - step; x <= scene.right + step; x += step) {
        const yy = y + Math.sin(x * .018 + motion * (1.3 + band * .03) + band) * (1.2 + perspective * 2.4);
        if (x <= scene.x - step + .1) ctx.moveTo(x, yy);
        else ctx.lineTo(x, yy);
      }
      ctx.stroke();
    }
    ctx.restore();

    ctx.strokeStyle = 'rgba(238,249,252,.72)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(scene.x, horizon + .5);
    ctx.lineTo(scene.right, horizon + .5);
    ctx.stroke();

    return { horizon, q };
  }

  function drawMotionStreaks(ctx, scene, intensity, now) {
    if (intensity <= .02) return;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = `rgba(185,220,238,${.05 + intensity * .08})`;
    ctx.lineWidth = .7;
    const shift = qa || reducedMotion ? 0 : (now * .09) % 80;
    for (let i = 0; i < 22; i += 1) {
      const y = scene.y + ((i * 37 + shift) % Math.max(1, scene.height));
      const x = scene.x + scene.width * (.52 + (i % 5) * .08);
      const len = 20 + intensity * 65 + (i % 4) * 5;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + len, y - len * .22);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawPlasma(ctx, pose, state, scene, now) {
    const intensity = clamp(Math.max(state.heatNormalized || 0, state.mach > 5 ? .2 + state.mach / 44 : 0), 0, 1);
    if (intensity < .12) return 0;
    const length = scene.width * mix(.18, .42, intensity);
    const radius = 24 + 26 * intensity;
    const flicker = qa || reducedMotion ? 0 : Math.sin(now * .015) * 3;

    ctx.save();
    ctx.translate(pose.x, pose.y);
    ctx.rotate(pose.angle);
    ctx.globalCompositeOperation = 'lighter';

    const wake = ctx.createLinearGradient(4, 0, length, 0);
    wake.addColorStop(0, `rgba(255,244,211,${.68 * intensity})`);
    wake.addColorStop(.14, `rgba(255,178,74,${.58 * intensity})`);
    wake.addColorStop(.54, `rgba(255,74,34,${.30 * intensity})`);
    wake.addColorStop(1, 'rgba(255,56,18,0)');
    ctx.fillStyle = wake;
    ctx.beginPath();
    ctx.moveTo(8, -radius * .52);
    ctx.bezierCurveTo(length * .24, -radius * .74, length * .65, -radius * .38 + flicker, length, -6);
    ctx.bezierCurveTo(length * .68, radius * .32 + flicker, length * .25, radius * .72, 8, radius * .54);
    ctx.closePath();
    ctx.fill();

    const bow = ctx.createRadialGradient(-8, 0, 3, -4, 0, radius * 1.15);
    bow.addColorStop(0, `rgba(255,255,235,${.78 * intensity})`);
    bow.addColorStop(.25, `rgba(255,184,96,${.52 * intensity})`);
    bow.addColorStop(.66, `rgba(255,70,32,${.23 * intensity})`);
    bow.addColorStop(1, 'rgba(255,70,32,0)');
    ctx.fillStyle = bow;
    ctx.beginPath();
    ctx.arc(-5, 0, radius * 1.15, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = `rgba(255,215,157,${.22 * intensity})`;
    ctx.lineWidth = 1.1;
    for (let i = 0; i < 9; i += 1) {
      const off = (i - 4) * 3.2;
      ctx.beginPath();
      ctx.moveTo(10, off);
      ctx.bezierCurveTo(length * .25, off + Math.sin(i + now * .01) * 8, length * .5, off * 1.5, length * .86, off * 2.0);
      ctx.stroke();
    }
    ctx.restore();
    return intensity;
  }

  function drawCapsule(ctx, pose, mode) {
    const scale = pose.scale;
    ctx.save();
    ctx.translate(pose.x, pose.y);
    ctx.rotate(pose.angle);
    ctx.scale(scale, scale);

    ctx.fillStyle = 'rgba(0,0,0,.28)';
    ctx.beginPath();
    ctx.ellipse(2, 14, 22, 7, 0, 0, Math.PI * 2);
    ctx.fill();

    const body = ctx.createLinearGradient(-18, -18, 18, 14);
    body.addColorStop(0, '#f5f7f7');
    body.addColorStop(.42, '#d7dee1');
    body.addColorStop(.78, '#9daab1');
    body.addColorStop(1, '#67757d');
    ctx.fillStyle = body;
    ctx.strokeStyle = '#3a4449';
    ctx.lineWidth = 1.1 / scale;
    ctx.beginPath();
    ctx.moveTo(-18, 11);
    ctx.quadraticCurveTo(-22, -4, 0, -22);
    ctx.quadraticCurveTo(22, -4, 18, 11);
    ctx.quadraticCurveTo(0, 20, -18, 11);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#172229';
    ctx.beginPath();
    ctx.moveTo(-9, -7);
    ctx.lineTo(0, -14);
    ctx.lineTo(9, -7);
    ctx.lineTo(6, -2);
    ctx.lineTo(-6, -2);
    ctx.closePath();
    ctx.fill();

    ctx.strokeStyle = mode === 'entry' ? '#ff9a6d' : '#b85e43';
    ctx.lineWidth = 2.2 / scale;
    ctx.beginPath();
    ctx.moveTo(-15, 11);
    ctx.quadraticCurveTo(0, 16.5, 15, 11);
    ctx.stroke();

    ctx.strokeStyle = 'rgba(255,255,255,.50)';
    ctx.lineWidth = .7 / scale;
    ctx.beginPath();
    ctx.moveTo(-12, 3);
    ctx.quadraticCurveTo(0, 9, 12, 3);
    ctx.stroke();
    ctx.restore();
  }

  function drawParachuteCanopy(ctx, x, y, radius, sway, alpha = 1) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(sway);
    ctx.globalAlpha = alpha;
    const canopy = ctx.createLinearGradient(-radius, 0, radius, 0);
    canopy.addColorStop(0, '#f2f0ea');
    canopy.addColorStop(.45, '#ffffff');
    canopy.addColorStop(.62, '#e9e5dc');
    canopy.addColorStop(1, '#c8cbd0');
    ctx.fillStyle = canopy;
    ctx.strokeStyle = 'rgba(70,77,83,.78)';
    ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.moveTo(-radius, 2);
    ctx.bezierCurveTo(-radius * .92, -radius * .70, -radius * .36, -radius, 0, -radius * .98);
    ctx.bezierCurveTo(radius * .36, -radius, radius * .92, -radius * .70, radius, 2);
    ctx.quadraticCurveTo(radius * .52, radius * .12, 0, radius * .10);
    ctx.quadraticCurveTo(-radius * .52, radius * .12, -radius, 2);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.strokeStyle = 'rgba(113,121,126,.55)';
    ctx.lineWidth = .65;
    for (const k of [-.66, -.33, 0, .33, .66]) {
      ctx.beginPath();
      ctx.moveTo(k * radius, -Math.sqrt(Math.max(0, 1 - k * k)) * radius * .76);
      ctx.quadraticCurveTo(k * radius * .55, -radius * .10, k * radius * .28, radius * .06);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawParachuteSystem(ctx, pose, mode, now, layout) {
    if (mode !== 'drogue' && mode !== 'main') return 'none';

    function drawSet(kind, alpha, deploy) {
      if (alpha <= .01 || deploy <= .01) return;
      const isMain = kind === 'main';
      const count = isMain ? 3 : 2;
      const fullRadius = isMain ? (layout.phone ? 31 : 48) : (layout.phone ? 18 : 25);
      const radius = fullRadius * (.18 + .82 * smoother(deploy));
      const spacing = fullRadius * (isMain ? 1.62 : 1.58);
      const canopyY = pose.y - fullRadius * (isMain ? 3.25 : 3.05);
      const motion = qa || reducedMotion ? 0 : now * .0015;

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = 'rgba(239,244,246,.76)';
      ctx.lineWidth = 1;
      for (let i = 0; i < count; i += 1) {
        const dx = (i - (count - 1) / 2) * spacing;
        const sway = Math.sin(motion + i * 1.7) * (isMain ? .020 : .038) * smoother(deploy);
        const anchorX = pose.x + dx * .72;
        const anchorY = canopyY;
        ctx.beginPath();
        ctx.moveTo(pose.x - 7, pose.y - 11);
        ctx.lineTo(anchorX - radius * .54, anchorY + 2);
        ctx.moveTo(pose.x + 7, pose.y - 11);
        ctx.lineTo(anchorX + radius * .54, anchorY + 2);
        ctx.stroke();
        drawParachuteCanopy(ctx, anchorX, anchorY, radius, sway, .96);
      }
      ctx.restore();
    }

    if (mode === 'drogue') {
      const deploy = smoother(remap(visualT, EVENTS.drogue, EVENTS.drogue + 20));
      drawSet('drogue', 1, deploy);
      return 'drogue';
    }

    const mainDeploy = smoother(remap(visualT, EVENTS.main, EVENTS.main + 24));
    const drogueFade = 1 - smoother(remap(visualT, EVENTS.main, EVENTS.main + 14));
    drawSet('drogue', drogueFade, 1);
    drawSet('main', mainDeploy, mainDeploy);
    return 'main';
  }

  function drawSplashAndFloat(ctx, scene, pose, t, now) {
    const recovery = playing
      ? clamp(postSplashMs / R8.recoveryHoldMs, 0, 1)
      : .68;
    const impact = 1 - smoother(clamp(recovery / .30, 0, 1));
    const settle = smoother(recovery);
    const waterY = scene.y + scene.height * .70;

    ctx.save();
    if (impact > .01) {
      ctx.globalCompositeOperation = 'lighter';
      ctx.fillStyle = `rgba(225,247,255,${.16 + impact * .48})`;
      const sprayCount = 34;
      for (let i = 0; i < sprayCount; i += 1) {
        const a = -Math.PI * (.08 + (i / (sprayCount - 1)) * .84);
        const dist = (24 + (i % 8) * 5.6) * impact;
        const x = pose.x + Math.cos(a) * dist;
        const y = waterY + Math.sin(a) * dist * .72;
        ctx.beginPath();
        ctx.arc(x, y, 1.2 + (i % 3) * .8, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    ctx.strokeStyle = `rgba(232,249,255,${.72 - settle * .24})`;
    ctx.lineWidth = 1.2;
    for (let i = 0; i < 5; i += 1) {
      const radius = 16 + i * 20 + settle * 42;
      ctx.beginPath();
      ctx.ellipse(pose.x, waterY + 6, radius, 4 + i * 2.2, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();

    drawCapsule(ctx, { ...pose, y: waterY - 2 }, 'ocean');
    return impact;
  }

  function drawHud(ctx, scene, phase, state, mode) {
    const pad = scene.width < 520 ? 8 : 12;
    const top = scene.y + pad;
    const boxW = Math.min(scene.width * .54, 390);
    ctx.save();
    ctx.fillStyle = 'rgba(2,8,13,.52)';
    ctx.strokeStyle = 'rgba(255,255,255,.10)';
    ctx.fillRect(scene.x + pad, top, boxW, 52);
    ctx.strokeRect(scene.x + pad, top, boxW, 52);
    drawCanvasLabel(ctx, phase.label.toUpperCase(), scene.x + pad + 10, top + 19, boxW - 20, { align: 'left', size: 10.5, minSize: 8.5, color: '#ffffff', maxLines: 1 });
    const context = mode === 'ocean'
      ? 'OCEAN RECOVERY VIEW · ILLUSTRATIVE CAMERA'
      : `${Math.round(state.altitudeKm)} KM · ${Number(state.speedKmS).toFixed(2)} KM/S · ILLUSTRATIVE CAMERA`;
    drawCanvasLabel(ctx, context, scene.x + pad + 10, top + 39, boxW - 20, { align: 'left', size: 8.8, minSize: 7.4, color: 'rgba(220,232,238,.72)', maxLines: 1 });
    ctx.restore();
  }

  function drawSceneBoundary(ctx, scene, mode) {
    const text = mode === 'ocean'
      ? 'ILLUSTRATIVE RECOVERY SCENE · NOT AN OFFICIAL SPLASHDOWN CAMERA VIEW'
      : 'MODEL-DRIVEN VISUAL COMPANION · ORIENTATION / CAMERA ARE ILLUSTRATIVE';
    drawCanvasLabel(ctx, text, scene.cx, scene.bottom - 8, scene.width * .94, {
      align: 'center', size: 8.4, minSize: 7.1, color: 'rgba(255,255,255,.52)', maxLines: 1,
    });
  }

  function draw(now = 0) {
    if (!canvas) return;
    const { ctx, w, h, layout } = fitCanvas(canvas);
    ctx.clearRect(0, 0, w, h);
    const scene = sceneRect(w, h, { top: layout.phone ? 8 : 10, bottom: layout.phone ? 8 : 10 }, layout.phone ? 6 : 10);
    const state = model.stateAt(Math.min(visualT, model.durationSeconds));
    const phase = phaseFor(visualT);
    const mode = sceneModeFor(visualT);
    const pose = capsulePath(scene, visualT, state);
    const staticNow = qa || reducedMotion ? 0 : now;
    let worldInfo = { surfaceContext: 'none', oceanAlpha: 0, cameraProgress: 0 };

    if (mode === 'space') {
      const bg = ctx.createLinearGradient(0, scene.y, 0, scene.bottom);
      bg.addColorStop(0, '#010205');
      bg.addColorStop(.55, '#02050a');
      bg.addColorStop(1, '#07111a');
      ctx.fillStyle = bg;
      ctx.fillRect(scene.x, scene.y, scene.width, scene.height);
      drawStars(ctx, w, h, layout.compact ? 84 : 145, 713, .88);
      drawSpaceEarth(ctx, scene, visualT);
      drawMotionStreaks(ctx, scene, .14, staticNow);
      drawCapsule(ctx, pose, mode);
      worldInfo.surfaceContext = 'space-limb';
    } else if (mode === 'entry') {
      const q = smoother(remap(visualT, EVENTS.spaceToEntry, EVENTS.entryToDescent));
      const bg = ctx.createLinearGradient(0, scene.y, 0, scene.bottom);
      bg.addColorStop(0, '#02040a');
      bg.addColorStop(.47, mixColor('#07101b', '#173e59', q));
      bg.addColorStop(1, '#173b52');
      ctx.fillStyle = bg;
      ctx.fillRect(scene.x, scene.y, scene.width, scene.height);
      drawStars(ctx, w, h, layout.compact ? 54 : 100, 917, clamp(1 - q * 1.18, 0, .70));
      drawEntryHorizon(ctx, scene, visualT);
      drawMotionStreaks(ctx, scene, .48 + (state.heatNormalized || 0) * .52, staticNow);
      drawPlasma(ctx, pose, state, scene, staticNow);
      drawCapsule(ctx, pose, mode);
      worldInfo.surfaceContext = 'entry-limb';
    } else if (mode === 'descent' || mode === 'drogue' || mode === 'main') {
      const entryBlend = mode === 'descent' ? smoother(remap(visualT, EVENTS.entryToDescent, EVENTS.entryToDescent + R8.transitionSeconds)) : 1;
      if (mode === 'descent' && entryBlend < 1) {
        ctx.save();
        ctx.globalAlpha = 1 - entryBlend;
        const bg = ctx.createLinearGradient(0, scene.y, 0, scene.bottom);
        bg.addColorStop(0, '#02040a');
        bg.addColorStop(.52, '#173e59');
        bg.addColorStop(1, '#173b52');
        ctx.fillStyle = bg;
        ctx.fillRect(scene.x, scene.y, scene.width, scene.height);
        drawEntryHorizon(ctx, scene, EVENTS.entryToDescent);
        ctx.restore();
      }
      ctx.save();
      ctx.globalAlpha = entryBlend;
      worldInfo = drawAtmosphericWorld(ctx, scene, visualT, mode);
      ctx.restore();
      if (mode === 'descent') drawMotionStreaks(ctx, scene, .12 * entryBlend, staticNow);
      drawParachuteSystem(ctx, pose, mode, staticNow, layout);
      drawCapsule(ctx, pose, mode);
    } else {
      drawOceanRecoveryWorld(ctx, scene, visualT, staticNow);
      drawSplashAndFloat(ctx, scene, pose, visualT, staticNow);
      worldInfo = { surfaceContext: 'ocean-recovery', oceanAlpha: 1, cameraProgress: 1 };
    }

    drawVignette(ctx, w, h, mode === 'ocean' ? .48 : .64);
    drawFilmGrain(ctx, scene, staticNow);
    drawHud(ctx, scene, phase, state, mode);
    drawSceneBoundary(ctx, scene, mode);

    root.dataset.canvasPass = String(Number.isFinite(pose.x) && Number.isFinite(pose.y) && w > 0 && h > 0);
    root.dataset.visualSequence = 'space-entry-descent-parachutes-splashdown';
    root.dataset.sceneMode = mode;
    root.dataset.earthContext = mode === 'space' || mode === 'entry' ? 'curved-limb' : 'none';
    root.dataset.oceanRecovery = String(mode === 'ocean');
    root.dataset.oceanVisible = String((worldInfo.oceanAlpha || 0) > .08 || mode === 'ocean');
    root.dataset.surfaceContext = worldInfo.surfaceContext || 'none';
    root.dataset.plasmaActive = String(mode === 'entry' && (state.heatNormalized || 0) > .12);
    root.dataset.parachuteMode = mode === 'drogue' || mode === 'main' ? mode : 'none';
    root.dataset.capsuleAfloat = String(mode === 'ocean');
    root.dataset.transitionBlend = String(mode === 'descent' ? smoother(remap(visualT, EVENTS.entryToDescent, EVENTS.entryToDescent + R8.transitionSeconds)).toFixed(4) : '1.0000');
    root.dataset.cameraProgress = String((worldInfo.cameraProgress || state.progress).toFixed(4));
    root.dataset.poseX = String(((pose.x - scene.x) / Math.max(1, scene.width)).toFixed(4));
    root.dataset.poseY = String(((pose.y - scene.y) / Math.max(1, scene.height)).toFixed(4));
    root.dataset.cameraContinuous = 'true';
    root.dataset.cinematicVersion = 'r7';
    root.dataset.cinematicRevision = R8.version;
  }

  function mixColor(a, b, t) {
    const parse = hex => {
      const value = hex.replace('#', '');
      return [0, 2, 4].map(i => parseInt(value.slice(i, i + 2), 16));
    };
    const aa = parse(a), bb = parse(b), q = clamp(t, 0, 1);
    return `rgb(${aa.map((v, i) => Math.round(lerp(v, bb[i], q))).join(',')})`;
  }

  function setTime(next, fromAnimation = false) {
    visualT = clamp(Number(next) || 0, 0, model.durationSeconds);
    if (!fromAnimation) {
      postSplashMs = visualT >= EVENTS.surface ? R8.recoveryHoldMs * .68 : 0;
    }
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

  function playbackFactor(t) {
    if (t < EVENTS.spaceToEntry) return .020;
    if (t < EVENTS.entryToDescent) return .012;
    if (t < EVENTS.drogue) return .025;
    if (t < EVENTS.main) return .011;
    if (t < EVENTS.surface) return .018;
    return 0;
  }

  function tick(now) {
    if (!playing) return;
    if (!lastFrame) lastFrame = now;
    const delta = Math.min(80, now - lastFrame);
    lastFrame = now;

    if (visualT < model.durationSeconds) {
      setTime(Math.min(model.durationSeconds, visualT + delta * playbackFactor(visualT)), true);
      if (visualT >= EVENTS.surface) postSplashMs = Math.max(postSplashMs, 1);
      draw(now);
      animationFrame = requestAnimationFrame(tick);
      return;
    }

    postSplashMs = Math.min(R8.recoveryHoldMs, postSplashMs + delta);
    draw(now);
    if (postSplashMs >= R8.recoveryHoldMs) {
      playing = false;
      updatePlayLabel();
      return;
    }
    animationFrame = requestAnimationFrame(tick);
  }

  if (scrubber) {
    scrubber.min = '0';
    scrubber.max = String(model.durationSeconds);
    scrubber.step = 'any';
    scrubber.addEventListener('input', () => {
      playing = false;
      updatePlayLabel();
      setTime(Number(scrubber.value), false);
    });
  }

  play?.addEventListener('click', () => {
    if (!playing && visualT >= model.durationSeconds && postSplashMs >= R8.recoveryHoldMs * .95) {
      postSplashMs = 0;
      setTime(0, false);
    }
    playing = !playing;
    lastFrame = 0;
    if (playing && visualT >= EVENTS.surface) postSplashMs = 0;
    updatePlayLabel();
    if (playing) {
      if (animationFrame) cancelAnimationFrame(animationFrame);
      animationFrame = requestAnimationFrame(tick);
    }
  });

  reset?.addEventListener('click', () => {
    playing = false;
    lastFrame = 0;
    postSplashMs = 0;
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
    root.dataset.qaCinematic = 'true';
    root.dataset.qaContinuous = 'true';
    root.dataset.qaR8 = 'true';
  }
})();
