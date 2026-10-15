(() => {
  'use strict';

  if (!window.A2) {
    throw new Error(
      'A2 MissionLab core runtime must load before experience runtimes.'
    );
  }

  const {
    $,
    $$,
    clamp,
    fitCanvas,
    sceneRect,
    scenePoint,
    drawEarth,
    drawMoon,
    drawCanvasLabel
  } = window.A2;

  if (!$('#mission-control')) {
    return;
  }


  const roles = {

    FLIGHT: {
      name: 'Flight Director',
      nav: 'Integrator',

      title:
        'What does the integrated mission need?',

      copy:
        'FLIGHT is the integrator. The flight director looks across disciplines, protects crew and mission objectives, and decides whether the team needs an action, a trade, or disciplined monitoring.',

      q: [
        'Is the crew safe?',
        'Is this expected?',
        'Which disciplines are affected?',
        'What decision, if any, is required?'
      ]
    },


    FDO: {
      name: 'Flight Dynamics Officer',
      nav: 'Trajectory',

      title:
        'What does the trajectory say?',

      copy:
        "FDO frames Orion's trajectory, future geometry, maneuver targeting, entry conditions, and the handoff between mission phases.",

      q: [
        'Where is Orion relative to the plan?',
        'Does future geometry remain acceptable?',
        'Is a correction opportunity needed?',
        'What is the next trajectory constraint?'
      ]
    },


    FAO: {
      name: 'Flight Activities Officer',
      nav: 'Timeline',

      title:
        'What happens to the flight plan?',

      copy:
        'FAO protects the timeline, procedures, crew activities, and real-time replanning needed to meet mission objectives.',

      q: [
        'What activity is next?',
        'What must move in the timeline?',
        'What crew work competes for time?',
        'What objective can be deferred?'
      ]
    },


    EECOM: {
      name:
        'Emergency, Environmental & Consumables Officer',

      nav:
        'Crew systems',

      title:
        'What does this mean for the crew environment?',

      copy:
        'EECOM watches environmental control and life support, thermal conditions, consumables, and integrated emergency response.',

      q: [
        'Is required function still available?',
        'Is habitability affected?',
        'What redundancy remains?',
        'Is this closed in flight or postflight?'
      ]
    },


    COMM: {
      name:
        'Communications lens',

      nav:
        'Links',

      title:
        'Is loss of signal expected or anomalous?',

      copy:
        'COMM is MissionLab shorthand for the communications problem: geometry-driven occultation, entry plasma blackout, network transitions, reacquisition, and unexpected link issues. It is not asserted to be an exact Artemis II console acronym.',

      q: [
        'Is line of sight physically blocked?',
        'Which network is relevant?',
        'When is reacquisition expected?',
        'Is this a link anomaly or normal geometry?'
      ]
    },


    SCIENCE: {
      name:
        'Science Officer',

      nav:
        'Lunar science',

      title:
        'What observation opportunity exists right now?',

      copy:
        'The Artemis SCIENCE console integrates lunar science and geology objectives into mission execution, connecting crew observations with supporting science analysis.',

      q: [
        'What target is visible?',
        'What lighting makes it useful?',
        'What did the crew actually observe?',
        'What needs postflight analysis?'
      ]
    },


    ENGINEERING: {
      name:
        'Engineering support lens',

      nav:
        'Evidence',

      title:
        'What technical explanation is actually supported?',

      copy:
        'Engineering support is a MissionLab synthesis lens rather than a claimed Artemis II front-room console name. It tests hypotheses against evidence and keeps action taken separate from root cause confirmed.',

      q: [
        'What evidence constrains the explanation?',
        'What is still unknown?',
        'Which model or test is relevant?',
        'What must be closed after flight?'
      ]
    }

  };


  const mcScenarios = [

    {
      id: 'occultation',

      tag:
        'EXPECTED GEOMETRY',

      title:
        'Lunar loss of signal',

      summary:
        'Orion is moving behind the Moon. Lunar terrain is about to block the radio path to Earth.',

      clock:
        'MET 05:00:08:10',

      kind:
        'orbit',

      evidenceLabel:
        'NASA REPORTED + MISSIONLAB DERIVED',

      evidenceCopy:
        'Expected loss-of-signal geometry is public mission context. This rendering is a schematic reconstruction, not private NASA telemetry or a flight-control display.',

      canvasLabel:
        'Schematic lunar occultation view showing Orion, Earth, Moon, and the blocked line of sight.',

      visualizationLabels: [
        'EARTH',
        'MOON',
        'ORION',
        'LOS BLOCKED BY LUNAR TERRAIN'
      ],

      trace: [

        {
          stage: 'DETECT',
          text:
            'Recognize the approaching loss of the Earth radio path.'
        },

        {
          stage: 'EVIDENCE',
          text:
            'Use public mission geometry to distinguish planned occultation from an unexpected link problem.'
        },

        {
          stage: 'CONSTRAINTS',
          text:
            'Lunar terrain physically blocks line of sight while Orion is behind the Moon.'
        },

        {
          stage: 'OPTIONS',
          text:
            'Continue the planned timeline or react only if evidence departs from the expected window.'
        },

        {
          stage: 'DECISION',
          text:
            'Treat the predicted interruption as an expected geometry constraint unless contrary evidence appears.'
        },

        {
          stage: 'ACTION',
          text:
            'Maintain disciplined monitoring through the expected loss-of-signal interval.'
        },

        {
          stage: 'OUTCOME',
          text:
            'Confirm the expected return of communications after Orion clears the occultation.'
        }

      ]
    },


    {
      id:
        'rtc2',

      tag:
        'TARGETING DECISION',

      title:
        'Return trajectory correction',

      summary:
        'A small velocity correction is being evaluated against the future entry corridor and remaining maneuver opportunities.',

      clock:
        'MET 08:04:17:48',

      kind:
        'burn',

      evidenceLabel:
        'NASA REPORTED + MISSIONLAB DERIVED',

      evidenceCopy:
        'Public maneuver context supports trajectory-correction analysis. The candidate paths shown here are schematic and are not unpublished targeting solutions or private navigation products.',

      canvasLabel:
        'Schematic return trajectory correction view showing Earth, candidate future paths, and a velocity-change marker.',

      visualizationLabels: [
        'EARTH',
        'CANDIDATE PATHS',
        'DELTA-V'
      ],

      trace: [

        {
          stage: 'DETECT',
          text:
            'Identify that the predicted future trajectory warrants a correction trade.'
        },

        {
          stage: 'EVIDENCE',
          text:
            'Use the public mission state and maneuver context to frame the future-path problem.'
        },

        {
          stage: 'CONSTRAINTS',
          text:
            'Entry targeting, remaining maneuver opportunities, and available performance bound the trade.'
        },

        {
          stage: 'OPTIONS',
          text:
            'Compare a small correction with the consequences of preserving the current path.'
        },

        {
          stage: 'DECISION',
          text:
            'Represent the public maneuver as a targeting decision without reconstructing a private option tree.'
        },

        {
          stage: 'ACTION',
          text:
            'Illustrate execution of the selected correction within the public mission context.'
        },

        {
          stage: 'OUTCOME',
          text:
            'Reassess the future trajectory after the modeled correction.'
        }

      ]
    },


    {
      id:
        'waste',

      tag:
        'SYSTEM TROUBLESHOOTING',

      title:
        'Orion toilet fault response',

      summary:
        'The crew reported a blinking fault indication. Mission Control assessed the available information and worked with the crew until normal operation was restored.',

      clock:
        'MET 03:11:40:00',

      kind:
        'system',

      evidenceLabel:
        'NASA REPORTED + UNKNOWN / NOT PUBLIC',

      evidenceCopy:
        'The reported indication, troubleshooting activity, and restored operation are public. The public troubleshooting sequence does not by itself establish a root cause.',

      canvasLabel:
        'Simplified crew-system status view with TEMP, WASTE, CABIN, and POWER bars; WASTE is highlighted as the alert condition.',

      visualizationLabels: [
        'TEMP',
        'WASTE',
        'CABIN',
        'POWER'
      ],

      trace: [

        {
          stage: 'DETECT',
          text:
            'Crew reports a blinking fault indication.'
        },

        {
          stage: 'EVIDENCE',
          text:
            'Use the available public indications and reported troubleshooting activity without inventing hidden telemetry.'
        },

        {
          stage: 'CONSTRAINTS',
          text:
            'Protect required function, crew time, and mission activities while the cause remains uncertain.'
        },

        {
          stage: 'OPTIONS',
          text:
            'Gather indications, preserve function, adjust activity, and continue troubleshooting as needed.'
        },

        {
          stage: 'DECISION',
          text:
            'Continue the reported troubleshooting response without promoting an unconfirmed root cause.'
        },

        {
          stage: 'ACTION',
          text:
            'Mission Control works with the crew through the publicly reported recovery sequence.'
        },

        {
          stage: 'OUTCOME',
          text:
            'Normal operation is restored; a specific root cause is not established by the public sequence.'
        }

      ]
    },


    {
      id:
        'entry',

      tag:
        'EXPECTED ENTRY CONSTRAINT',

      title:
        'Plasma communications blackout',

      summary:
        'Ionized flow around Orion can interrupt radio communications during hypersonic entry. Expected silence is not the same as a communications failure.',

      clock:
        'MET 09:01:22:00',

      kind:
        'entry',

      evidenceLabel:
        'NASA REPORTED + MODELED VISUALIZATION',

      evidenceCopy:
        'Entry communications blackout is established physical and mission context. The animated flow field is illustrative only; it is not CFD, private telemetry, or a reconstruction of an unpublished NASA display.',

      canvasLabel:
        'Illustrative hypersonic entry communications view with a stylized plasma-flow field and expected reacquisition messaging.',

      visualizationLabels: [
        'PLASMA FLOW',
        'EXPECTED REACQUISITION WINDOW AHEAD'
      ],

      trace: [

        {
          stage: 'DETECT',
          text:
            'Orion approaches the expected entry communications constraint.'
        },

        {
          stage: 'EVIDENCE',
          text:
            'Hypersonic ionization can interrupt radio links during entry.'
        },

        {
          stage: 'CONSTRAINTS',
          text:
            'Expected silence alone does not establish a communications failure.'
        },

        {
          stage: 'OPTIONS',
          text:
            'Track the predicted blackout window and the conditions expected for reacquisition.'
        },

        {
          stage: 'DECISION',
          text:
            'Classify silence inside the expected window as a planned constraint unless other evidence contradicts it.'
        },

        {
          stage: 'ACTION',
          text:
            'Maintain the expected-blackout interpretation while monitoring the broader entry picture.'
        },

        {
          stage: 'OUTCOME',
          text:
            'Expect communications to return as the relevant flow and geometry conditions change.'
        }

      ]
    }

  ];


  const roleIds =
    Object.keys(roles);

  const scenarioIds =
    mcScenarios.map(
      scenario => scenario.id
    );


  let mcScenario =
    mcScenarios[0];

  let mcRole =
    'FLIGHT';


  const strip =
    $('#mc-strip');

  const evBox =
    $('#mc-events');

  const mcCanvas =
    $('#mc-canvas');

  const srStatus =
    $('#mc-sr-status');


  let rafId =
    0;

  let canvasInView =
    true;


  const reducedMotionQuery =
    window.matchMedia &&
    window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    );


  const reducedMotion = () =>
    Boolean(
      reducedMotionQuery &&
      reducedMotionQuery.matches
    );


  function roleDisplayKey(key) {

    return (
      key === 'ENGINEERING'
        ? 'ENG SUPPORT'
        : key
    );
  }


  function scenarioById(id) {

    return mcScenarios.find(
      scenario =>
        scenario.id === id
    );
  }


  function currentSnapshot() {

    const scenario =
      mcScenario;

    const role =
      roles[mcRole];


    return {

      role:
        mcRole,

      roleDisplay:
        roleDisplayKey(
          mcRole
        ),

      roleName:
        role.name,

      roleTitle:
        role.title,

      roleCopy:
        role.copy,

      questions: [
        ...role.q
      ],

      scenarioId:
        scenario.id,

      eventTitle:
        scenario.title,

      eventClass:
        scenario.tag,

      eventSummary:
        scenario.summary,

      clock:
        scenario.clock,

      evidenceLabel:
        scenario.evidenceLabel,

      evidenceCopy:
        scenario.evidenceCopy,

      canvasLabel:
        scenario.canvasLabel,

      visualizationLabels: [
        ...scenario.visualizationLabels
      ],

      decisionTrace:
        scenario.trace.map(
          step => ({
            stage:
              step.stage,

            text:
              step.text
          })
        )
    };
  }


  function setPressedState(
    root,
    attribute,
    activeValue
  ) {

    $$(
      'button',
      root
    ).forEach(
      button => {

        const active =
          button.dataset[
            attribute
          ] ===
          activeValue;


        button.classList.toggle(
          'active',
          active
        );


        button.setAttribute(
          'aria-pressed',
          active
            ? 'true'
            : 'false'
        );
      }
    );
  }


  function renderDecisionTrace(
    scenario
  ) {

    $('#mc-decision-trace').innerHTML =
      scenario.trace.map(
        (
          step,
          index
        ) => `
          <article
            role="listitem"
            data-stage="${step.stage}"
          >
            <small>
              ${String(index + 1).padStart(2, '0')}
              /
              ${step.stage}
            </small>

            <b>
              ${step.stage}
            </b>

            <p>
              ${step.text}
            </p>
          </article>
        `
      ).join('');
  }


  function scheduleCanvas() {

    if (
      !mcCanvas ||
      rafId
    ) {
      return;
    }

    if (
      !canvasInView ||
      document.hidden
    ) {
      return;
    }

    rafId =
      window.requestAnimationFrame(
        drawCanvasFrame
      );
  }


  function renderMc(
    announce = false
  ) {

    const scenario =
      mcScenario;

    const role =
      roles[mcRole];


    $('#mc-clock').textContent =
      scenario.clock;

    $('#mc-event-class').textContent =
      scenario.tag;

    $('#mc-event-title').textContent =
      scenario.title;

    $('#mc-event-summary').textContent =
      scenario.summary;

    $('#mc-evidence-label').textContent =
      scenario.evidenceLabel;

    $('#mc-evidence-copy').textContent =
      scenario.evidenceCopy;


    $('#mc-role-label').textContent =
      (
        roleDisplayKey(
          mcRole
        ) +
        ' / ' +
        role.name
      );


    $('#mc-role-title').textContent =
      role.title;

    $('#mc-role-copy').textContent =
      role.copy;


    $('#mc-questions').innerHTML =
      role.q.map(
        question =>
          `<div>${question}</div>`
      ).join('');


    renderDecisionTrace(
      scenario
    );


    setPressedState(
      strip,
      'role',
      mcRole
    );


    setPressedState(
      evBox,
      'id',
      scenario.id
    );


    document.body.dataset.mcScenario =
      scenario.id;

    document.body.dataset.mcRole =
      mcRole;


    if (mcCanvas) {

      mcCanvas.setAttribute(
        'aria-label',
        scenario.canvasLabel
      );


      mcCanvas.dataset.kind =
        scenario.kind;


      mcCanvas.dataset.visualizationLabels =
        scenario.visualizationLabels.join('|');
    }


    if (
      announce &&
      srStatus
    ) {

      srStatus.textContent =
        (
          'Mission event: ' +
          scenario.title +
          '. Discipline lens: ' +
          roleDisplayKey(
            mcRole
          ) +
          ', ' +
          role.name +
          '.'
        );
    }


    scheduleCanvas();
  }


  function selectRole(
    key,
    announce = true
  ) {

    if (!roles[key]) {

      throw new Error(
        'Unknown Mission Control role: ' +
        key
      );
    }


    mcRole =
      key;


    renderMc(
      announce
    );
  }


  function selectScenario(
    id,
    announce = true
  ) {

    const next =
      scenarioById(
        id
      );


    if (!next) {

      throw new Error(
        'Unknown Mission Control scenario: ' +
        id
      );
    }


    mcScenario =
      next;


    renderMc(
      announce
    );
  }


  if (strip) {

    strip.innerHTML =
      Object.entries(
        roles
      ).map(
        ([key, role]) => `
          <button
            type="button"
            data-role="${key}"
            aria-pressed="${
              key === mcRole
                ? 'true'
                : 'false'
            }"
            aria-controls="mc-role-context"
            aria-label="${
              roleDisplayKey(key)
            }: ${role.name}"
            title="${role.name}"
          >
            <b>
              ${roleDisplayKey(key)}
            </b>

            <small>
              ${role.nav}
            </small>
          </button>
        `
      ).join('');


    $$(
      'button',
      strip
    ).forEach(
      button => {

        button.addEventListener(
          'click',
          () => {

            selectRole(
              button.dataset.role
            );
          }
        );
      }
    );
  }


  if (evBox) {

    evBox.innerHTML =
      mcScenarios.map(
        scenario => `
          <button
            type="button"
            data-id="${scenario.id}"
            aria-pressed="${
              scenario.id === mcScenario.id
                ? 'true'
                : 'false'
            }"
            aria-controls="mc-event-context mc-decision-trace"
          >
            <small>
              ${scenario.tag}
            </small>

            <b>
              ${scenario.title}
            </b>
          </button>
        `
      ).join('');


    $$(
      'button',
      evBox
    ).forEach(
      button => {

        button.addEventListener(
          'click',
          () => {

            selectScenario(
              button.dataset.id
            );
          }
        );
      }
    );
  }


  window.A2MissionControl =
    Object.freeze({

      version:
        'phase-d-r3.2',

      roleIds:
        () => [
          ...roleIds
        ],

      scenarioIds:
        () => [
          ...scenarioIds
        ],

      getState:
        () =>
          currentSnapshot(),

      selectRole:
        key =>
          selectRole(
            key,
            false
          ),

      selectScenario:
        id =>
          selectScenario(
            id,
            false
          )

    });


  function drawCanvasFrame(t) {

    rafId =
      0;


    if (!mcCanvas) {
      return;
    }


    const {
      ctx,
      w,
      h,
      layout
    } = fitCanvas(
      mcCanvas
    );


    const scene =
      sceneRect(
        w,
        h,
        {},
        layout.phone
          ? 14
          : 20
      );


    const u =
      scene.min;


    ctx.clearRect(
      0,
      0,
      w,
      h
    );


    ctx.fillStyle =
      '#02070a';


    ctx.fillRect(
      0,
      0,
      w,
      h
    );


    ctx.strokeStyle =
      'rgba(96,144,176,.08)';


    ctx.lineWidth =
      1;


    for (
      let x = scene.x;
      x < scene.right;
      x += 40
    ) {

      ctx.beginPath();

      ctx.moveTo(
        x,
        scene.y
      );

      ctx.lineTo(
        x,
        scene.bottom
      );

      ctx.stroke();
    }


    for (
      let y = scene.y;
      y < scene.bottom;
      y += 40
    ) {

      ctx.beginPath();

      ctx.moveTo(
        scene.x,
        y
      );

      ctx.lineTo(
        scene.right,
        y
      );

      ctx.stroke();
    }


    const motionTime =
      reducedMotion()
        ? 0
        : t;


    if (
      mcScenario.kind ===
      'orbit'
    ) {

      const earth =
        scenePoint(
          scene,
          0.18,
          0.56
        );


      const moon =
        scenePoint(
          scene,
          layout.phone
            ? 0.72
            : 0.67,
          0.52
        );


      const earthRadius =
        clamp(
          u * 0.085,
          27,
          42
        );


      const moonRadius =
        clamp(
          u * 0.145,
          48,
          72
        );


      drawEarth(
        ctx,
        earth.x,
        earth.y,
        earthRadius
      );


      drawMoon(
        ctx,
        moon.x,
        moon.y,
        moonRadius
      );


      const orionX =
        (
          scene.x +
          scene.width *
          0.59 +
          Math.sin(
            motionTime *
            0.0005
          ) *
          clamp(
            scene.width *
            0.035,
            10,
            25
          )
        );


      const orionY =
        (
          scene.y +
          scene.height *
          0.34
        );


      ctx.strokeStyle =
        'rgba(255,100,90,.65)';


      ctx.setLineDash(
        [
          5,
          5
        ]
      );


      ctx.beginPath();


      ctx.moveTo(
        orionX,
        orionY
      );


      ctx.lineTo(
        earth.x,
        earth.y
      );


      ctx.stroke();


      ctx.setLineDash(
        []
      );


      ctx.fillStyle =
        '#fff';


      ctx.beginPath();


      ctx.arc(
        orionX,
        orionY,
        4,
        0,
        Math.PI * 2
      );


      ctx.fill();


      drawCanvasLabel(
        ctx,
        'LOS BLOCKED BY LUNAR TERRAIN',
        layout.phone
          ? scene.x + 8
          : (
              scene.x +
              scene.width *
              0.42
            ),
        layout.phone
          ? scene.y + 26
          : (
              scene.y +
              scene.height *
              0.78
            ),
        layout.phone
          ? (
              scene.width *
              0.72
            )
          : (
              scene.width *
              0.52
            ),
        {
          size:
            layout.phone
              ? 10.5
              : 12,

          minSize:
            10,

          color:
            '#ff7f76',

          maxLines:
            2
        }
      );
    }


    else if (
      mcScenario.kind ===
      'burn'
    ) {

      const earth =
        scenePoint(
          scene,
          0.16,
          0.58
        );


      const earthRadius =
        clamp(
          u * 0.08,
          26,
          38
        );


      drawEarth(
        ctx,
        earth.x,
        earth.y,
        earthRadius
      );


      const p0 =
        scenePoint(
          scene,
          0.23,
          0.60
        );


      const p1 =
        scenePoint(
          scene,
          0.52,
          0.16
        );


      const p2 =
        scenePoint(
          scene,
          0.86,
          0.52
        );


      const p3 =
        scenePoint(
          scene,
          0.55,
          0.12
        );


      const p4 =
        scenePoint(
          scene,
          0.88,
          0.47
        );


      ctx.strokeStyle =
        'rgba(127,197,255,.4)';


      ctx.lineWidth =
        2;


      ctx.beginPath();


      ctx.moveTo(
        p0.x,
        p0.y
      );


      ctx.quadraticCurveTo(
        p1.x,
        p1.y,
        p2.x,
        p2.y
      );


      ctx.stroke();


      ctx.strokeStyle =
        'rgba(125,224,173,.78)';


      ctx.beginPath();


      ctx.moveTo(
        p0.x,
        p0.y
      );


      ctx.quadraticCurveTo(
        p3.x,
        p3.y,
        p4.x,
        p4.y
      );


      ctx.stroke();


      const burnPoint =
        scenePoint(
          scene,
          0.54,
          0.21
        );


      ctx.fillStyle =
        '#f5f9fc';


      ctx.beginPath();


      ctx.arc(
        burnPoint.x,
        burnPoint.y,
        4,
        0,
        Math.PI * 2
      );


      ctx.fill();


      ctx.strokeStyle =
        '#f0c476';


      ctx.beginPath();


      ctx.moveTo(
        burnPoint.x,
        burnPoint.y
      );


      ctx.lineTo(
        burnPoint.x +
        scene.width *
        0.055,
        burnPoint.y -
        scene.height *
        0.055
      );


      ctx.stroke();


      drawCanvasLabel(
        ctx,
        '\u0394V',
        burnPoint.x +
        scene.width *
        0.06,
        burnPoint.y -
        scene.height *
        0.06,
        50,
        {
          size:
            12,

          minSize:
            10,

          color:
            '#f0c476',

          maxLines:
            1
        }
      );
    }


    else if (
      mcScenario.kind ===
      'system'
    ) {

      const values = [
        0.24,
        0.36,
        0.58,
        0.72
      ];


      const labels = [
        'TEMP',
        'WASTE',
        'CABIN',
        'POWER'
      ];


      values.forEach(
        (
          value,
          index
        ) => {

          const barWidth =
            scene.width *
            0.12;


          const x =
            (
              scene.x +
              scene.width *
              (
                0.12 +
                index *
                0.21
              )
            );


          const base =
            (
              scene.y +
              scene.height *
              0.82
            );


          const barHeight =
            (
              scene.height *
              value *
              0.7
            );


          ctx.fillStyle =
            index === 1
              ? 'rgba(255,103,95,.68)'
              : 'rgba(111,231,225,.42)';


          ctx.fillRect(
            x,
            base - barHeight,
            barWidth,
            barHeight
          );


          if (
            index === 1
          ) {

            ctx.strokeStyle =
              'rgba(255,142,134,.85)';


            ctx.lineWidth =
              1.5;


            ctx.strokeRect(
              x - 2,
              base - barHeight - 2,
              barWidth + 4,
              barHeight + 4
            );
          }


          drawCanvasLabel(
            ctx,
            labels[index],
            x +
            barWidth /
            2,
            base + 18,
            barWidth + 12,
            {
              size:
                layout.phone
                  ? 9.5
                  : 11,

              minSize:
                9,

              align:
                'center',

              color:
                index === 1
                  ? '#ff8b83'
                  : 'rgba(255,255,255,.66)',

              maxLines:
                1
            }
          );
        }
      );
    }


    else {

      const gradient =
        ctx.createLinearGradient(
          scene.x,
          0,
          scene.right,
          0
        );


      gradient.addColorStop(
        0,
        '#1b2230'
      );


      gradient.addColorStop(
        0.5,
        '#a23c1e'
      );


      gradient.addColorStop(
        1,
        '#240703'
      );


      ctx.fillStyle =
        gradient;


      ctx.fillRect(
        scene.x,
        scene.y,
        scene.width,
        scene.height
      );


      ctx.strokeStyle =
        'rgba(255,220,190,.35)';


      for (
        let i = 0;
        i < 14;
        i += 1
      ) {

        ctx.beginPath();


        ctx.moveTo(
          scene.x,
          (
            scene.y +
            (
              i /
              14
            ) *
            scene.height +
            Math.sin(
              motionTime *
              0.002 +
              i
            ) *
            8
          )
        );


        ctx.bezierCurveTo(
          scene.x +
          scene.width *
          0.25,

          scene.y +
          scene.height *
          0.2 +
          i *
          9,

          scene.x +
          scene.width *
          0.55,

          scene.bottom -
          i *
          7,

          scene.right,

          scene.y +
          scene.height *
          0.32 +
          i *
          7
        );


        ctx.stroke();
      }


      drawCanvasLabel(
        ctx,
        'EXPECTED REACQUISITION WINDOW AHEAD',
        scene.right - 8,
        scene.y + 30,
        scene.width *
        0.72,
        {
          size:
            layout.phone
              ? 10.5
              : 13,

          minSize:
            10,

          align:
            'right',

          color:
            'rgba(255,255,255,.92)',

          maxLines:
            2
        }
      );
    }


    if (
      !reducedMotion() &&
      canvasInView &&
      !document.hidden
    ) {

      scheduleCanvas();
    }
  }


  if (
    mcCanvas &&
    'IntersectionObserver' in window
  ) {

    const observer =
      new IntersectionObserver(
        entries => {

          const entry =
            entries[0];


          canvasInView =
            Boolean(
              entry &&
              entry.isIntersecting
            );


          if (canvasInView) {
            scheduleCanvas();
          }
        },
        {
          rootMargin:
            '180px'
        }
      );


    observer.observe(
      mcCanvas
    );
  }


  document.addEventListener(
    'visibilitychange',
    () => {

      if (!document.hidden) {
        scheduleCanvas();
      }
    }
  );


  window.addEventListener(
    'a2:celestialchange',
    scheduleCanvas
  );


  window.addEventListener(
    'resize',
    scheduleCanvas,
    {
      passive:
        true
    }
  );


  if (
    reducedMotionQuery &&
    typeof reducedMotionQuery.addEventListener ===
      'function'
  ) {

    reducedMotionQuery.addEventListener(
      'change',
      scheduleCanvas
    );
  }


  renderMc(
    false
  );

})();
