(() => {
  'use strict';

  if (!window.A2) {
    throw new Error('A2 MissionLab core runtime must load before experience runtimes.');
  }

  const staticMissionQa = /(?:^|[?&])(?:trajectory-qa|space-weather-qa)=1(?:&|$)/.test(window.location.search);

  const {
    $,
    $$,
    clamp,
    lerp,
    invLerp,
    ease,
    viewportProfile,
    responsiveDpr,
    ensureCanvasRuntime,
    invalidateCanvasLayouts,
    syncViewportVars,
    resyncResponsiveViewport,
    queueResponsiveViewportResync,
    fitCanvas,
    sceneRect,
    scenePoint,
    roundRect,
    drawStars,
    drawEarth,
    drawMoon,
    bezier,
    drawCanvasLabel
  } = window.A2;

  // Mission explorer.
  if ($('#mission-explorer')) {
  const missionCanvas=$('#mission-canvas');
  const missionMoments=[
    {p:0,date:'APR 01 · FLIGHT DAY 1',title:'Launch from Kennedy Space Center',phase:'Launch',met:'00:00:00:00',comm:'Near-Earth network',copy:'The shared mission clock begins at 22:35:12 UTC. MissionLab uses this epoch to align public trajectory products, events, science observations, and engineering analyses.',aL:'Distance context',a:'Earth departure',bL:'Evidence',b:'NASA reported',caption:'Orion begins the first crewed Artemis lunar flyby mission.'},
    {p:.13,date:'APR 02 · OUTBOUND',title:'Earth gets smaller. Navigation changes with distance.',phase:'Outbound coast',met:'00:18:32:00',comm:'Network transition',copy:'After Earth-orbit checkout and translunar departure, Orion coasts outward. Near Earth, GPS can contribute. Deeper in space, onboard sensors and ground tracking become more important.',aL:'Navigation idea',a:'Near-Earth → deep-space',bL:'MissionLab',b:'Public architecture reconstruction',caption:'A long coast magnifies the effect of even small velocity errors.'},
    {p:.28,date:'APR 04 · FLIGHT DAY 4',title:'The crew manually pilots Orion.',phase:'Manual piloting',met:'02:18:00:00',comm:'Deep-space link',copy:'Artemis II included manual-control demonstrations. Rotation Hand Controller inputs command attitude motion; Translation Hand Controller inputs command translational motion. MissionLab reconstructs the public architecture without inventing private control laws.',aL:'Control modes',a:'3-DOF / 6-DOF context',bL:'Human interface',b:'RHC + THC',caption:'The GNC lab below lets you experiment with the difference between rotation and translation.'},
    {p:.45,date:'APR 06 · LUNAR APPROACH',title:'Orion enters the Moon’s sphere of influence.',phase:'Lunar approach',met:'04:06:02:56',comm:'DSN support',copy:'MissionLab derives lunar SOI entry at 04:38:07 UTC. The spacecraft is now in the part of the flight where Moon-relative geometry becomes the natural way to reason about the path.',aL:'Inside selected SOI',a:'~36.76 hours',bL:'Evidence',b:'MissionLab derived',caption:'The Moon now dominates the local geometry used in the reconstruction.'},
    {p:.54,date:'APR 06 · 22:41 UTC',title:'Earthset. Then the Moon blocks the radio path.',phase:'Earthset / occultation',met:'05:00:05:48',comm:'Loss of signal approaching',copy:'The crew photographs Earth sinking behind the lunar limb. Minutes later, lunar terrain blocks line of sight to Earth. That planned loss of signal is a geometry constraint, not evidence of a spacecraft failure.',aL:'Derived occultation',a:'~36.57 minutes',bL:'NASA ops window',b:'~41 minutes',caption:'Earthset and communications occultation are two views of the same changing geometry.'},
    {p:.585,date:'APR 06 · 23:00:46 UTC',title:'Closest approach to the Moon.',phase:'Pericynthion',met:'05:00:25:34',comm:'Behind the Moon',copy:'MissionLab refines closest approach to a Moon-center distance of 8,281.938 km, corresponding to a mean-radius altitude of 6,544.538 km and Moon-relative speed of about 1.381073 km/s.',aL:'Mean-radius altitude',a:'6,544.538 km',bL:'Moon-relative speed',b:'1.381073 km/s',caption:'This closest-approach time is derived from public trajectory data, not private telemetry.'},
    {p:.63,date:'APR 06 · 23:22 UTC',title:'Earthrise. Contact returns.',phase:'Earthrise / reacquisition',met:'05:00:46:48',comm:'Reacquiring',copy:'Earth reappears from behind the lunar limb. NASA’s public operational reference planned acquisition near 23:25 UTC; the geometry model and the operational window are related but not identical.',aL:'Why different?',a:'Earth center ≠ DSN antenna',bL:'Evidence rule',b:'Geometry ≠ link margin',caption:'Topocentric DSN geometry improves on a simple Earth-center line-of-sight test.'},
    {p:.69,date:'APR 07 · 00:34 UTC',title:'A solar eclipse lasts almost 54 minutes.',phase:'Lunar eclipse',met:'05:01:59:15',comm:'Deep-space link',copy:'From Orion’s moving vantage point, the Moon completely covers the Sun for an unusually long interval. MissionLab derives the eclipse window from public spacecraft and body geometry.',aL:'Derived duration',a:'~54.43 minutes',bL:'Science context',b:'Crew photography',caption:'The lunar flyby became a rare human-observation platform as well as a spacecraft test.'},
    {p:.78,date:'APR 08–10 · RETURN',title:'Small correction burns protect the path home.',phase:'Return corrections',met:'06:01:27:48',comm:'Deep-space link',copy:'RTC1, RTC2, and RTC3 make small velocity changes. Over many hours of coast, those changes protect the future entry geometry. The trajectory lab below propagates an educational two-body correction response without pretending to reproduce NASA’s targeting solution.',aL:'Largest listed RTC',a:'RTC2 · ~5.3 ft/s',bL:'Operations',b:'Target future geometry',caption:'Targeting is about where a tiny velocity change places the spacecraft later.'},
    {p:.91,date:'APR 10 · 23:53 UTC',title:'Entry interface. The atmosphere becomes the engine.',phase:'Atmospheric entry',met:'09:01:17:48',comm:'Entry link / blackout',copy:'Orion reaches the public Entry Interface minute. Drag begins converting lunar-return kinetic energy into heating, atmospheric motion, and deceleration. Plasma can temporarily disrupt communications.',aL:'Physics',a:'Drag + heating',bL:'Model',b:'Atmosphere + Sutton–Graves',caption:'Entry is where trajectory, atmosphere, thermal protection, communications, and recovery converge.'},
    {p:1,date:'APR 11 · 00:07 UTC',title:'Splashdown. Then recovery begins.',phase:'Splashdown',met:'09:01:31:48',comm:'Recovered',copy:'Drogues, main parachutes, splashdown, crew extraction, and spacecraft recovery close the flight. MissionLab keeps those public events connected to the entry and environmental data rather than treating splashdown as the end of the engineering story.',aL:'Mission outcome',a:'Crew safely home',bL:'Next phase',b:'Recovery + postflight',caption:'Nearly ten days of flight end in the Pacific; engineering analysis continues.'}
  ];
  let missionP=0;
  let missionMoment=null;
  const missionMarkerIndexes=[0,3,4,5,8,10];

  function missionNearest(p){
    return missionMoments.reduce(
      (best,m)=>
        Math.abs(m.p-p)<
        Math.abs(best.p-p)
          ?m
          :best,
      missionMoments[0]
    );
  }

  function missionIndex(){
    return missionMoments.indexOf(
      missionNearest(
        missionP
      )
    );
  }

  function updateMission(
    p,
    snap=false
  ){
    missionP=clamp(
      p,
      0,
      1
    );

    const m=
      missionNearest(
        missionP
      );

    const momentChanged=
      missionMoment!==m;

    missionMoment=m;

    if(snap){
      missionP=m.p;
    }

    const ids={
      date:'mission-date',
      title:'mission-title',
      copy:'mission-copy',
      met:'mission-met',
      phase:'mission-phase',
      comm:'mission-comm',
      caption:'mission-stage-caption',
      aL:'mission-readout-a-label',
      a:'mission-readout-a',
      bL:'mission-readout-b-label',
      b:'mission-readout-b'
    };

    Object.entries(
      ids
    ).forEach(
      ([key,id])=>{
        const element=
          $('#'+id);

        if(element){
          element.textContent=
            m[key];
        }
      }
    );

    const scrubber=
      $('#mission-scrubber');

    if(scrubber){
      scrubber.value=
        String(
          Math.round(
            missionP*1000
          )
        );

      scrubber.setAttribute(
        'aria-valuetext',
        `${m.date}: ${m.phase}`
      );
    }

    $$('#mission-markers button')
      .forEach(
        button=>{
          const active=
            Math.abs(
              Number(
                button.dataset.p
              )-
              missionP
            )<.055;

          button.classList.toggle(
            'active',
            active
          );

          if(active){
            button.setAttribute(
              'aria-current',
              'step'
            );
          }else{
            button.removeAttribute(
              'aria-current'
            );
          }
        }
      );

    const previous=
      $('#mission-prev');

    const next=
      $('#mission-next');

    if(previous){
      previous.disabled=
        missionP<=
        missionMoments[0].p+
        1e-6;
    }

    if(next){
      next.disabled=
        missionP>=
        missionMoments[
          missionMoments.length-1
        ].p-
        1e-6;
    }

    if(momentChanged){
      const story=
        $('#mission-story-copy');

      if(story){
        requestAnimationFrame(
          ()=>{
            story.scrollTop=0;
          }
        );
      }
    }
  }

  function goMissionPrevious(){
    const previous=
      [...missionMoments]
        .reverse()
        .find(
          moment=>
            moment.p<
            missionP-.02
        )
      ||
      missionMoments[0];

    updateMission(
      previous.p,
      true
    );
  }

  function goMissionNext(){
    const next=
      missionMoments
        .find(
          moment=>
            moment.p>
            missionP+.02
        )
      ||
      missionMoments[
        missionMoments.length-1
      ];

    updateMission(
      next.p,
      true
    );
  }

  function setMissionIndex(
    index
  ){
    const safeIndex=
      clamp(
        Math.round(
          Number(index)||0
        ),
        0,
        missionMoments.length-1
      );

    updateMission(
      missionMoments[
        safeIndex
      ].p,
      true
    );
  }

  function initMission(){
    const markers=
      $('#mission-markers');

    if(markers){
      markers.innerHTML=
        missionMarkerIndexes
          .map(
            index=>{
              const moment=
                missionMoments[
                  index
                ];

              return (
                `<button type="button" `
                +`data-p="${moment.p}" `
                +`aria-label="Jump to ${moment.phase}">`
                +`${moment.phase}</button>`
              );
            }
          )
          .join('');

      $$(
        'button',
        markers
      ).forEach(
        button=>
          button.addEventListener(
            'click',
            ()=>{
              updateMission(
                Number(
                  button.dataset.p
                ),
                true
              );
            }
          )
      );
    }

    const scrubber=
      $('#mission-scrubber');

    if(scrubber){
      scrubber.addEventListener(
        'input',
        event=>
          updateMission(
            Number(
              event.target.value
            )/1000
          )
      );
    }

    $('#mission-prev')
      ?.addEventListener(
        'click',
        goMissionPrevious
      );

    $('#mission-next')
      ?.addEventListener(
        'click',
        goMissionNext
      );

    updateMission(
      0,
      true
    );
  }

  window.A2MissionExplorer=
    Object.freeze({
      count:()=>
        missionMoments.length,

      index:()=>
        missionIndex(),

      position:()=>
        missionP,

      set:
        setMissionIndex,

      next:
        goMissionNext,

      prev:
        goMissionPrevious
    });

  initMission();
  if(missionCanvas){
    const loop=t=>{const {ctx,w,h,layout}=fitCanvas(missionCanvas);ctx.clearRect(0,0,w,h);drawStars(ctx,w,h,layout.compact?105:150,13,.72);
      const portrait=layout.profile==='phone-portrait',landPhone=layout.profile==='phone-landscape';
      const scene=sceneRect(w,h,{top:portrait?16:landPhone?14:18,bottom:portrait?16:landPhone?14:22},portrait?10:14);
      const earth=portrait?{...scenePoint(scene,.19,.69),r:scene.min*.105}:landPhone?{...scenePoint(scene,.16,.61),r:scene.min*.09}:{...scenePoint(scene,.16,.56),r:scene.min*.092};
      const moon=portrait?{...scenePoint(scene,.76,.46),r:scene.min*.13}:landPhone?{...scenePoint(scene,.81,.50),r:scene.min*.11}:{...scenePoint(scene,.82,.47),r:scene.min*.115};
      drawEarth(ctx,earth.x,earth.y,earth.r);drawMoon(ctx,moon.x,moon.y,moon.r);
      const out0={x:earth.x+earth.r*.72,y:earth.y-earth.r*.2},out1=portrait?scenePoint(scene,.43,.05):scenePoint(scene,.47,.05),out2={x:moon.x-moon.r*.7,y:moon.y};
      const ret0={x:moon.x-moon.r*.56,y:moon.y+moon.r*.1},ret1=portrait?scenePoint(scene,.56,.96):scenePoint(scene,.58,.94),ret2={x:earth.x+earth.r*.66,y:earth.y+earth.r*.25};
      ctx.save();ctx.strokeStyle='rgba(127,197,255,.30)';ctx.lineWidth=1.35;ctx.setLineDash([4,7]);ctx.beginPath();ctx.moveTo(out0.x,out0.y);ctx.quadraticCurveTo(out1.x,out1.y,out2.x,out2.y);ctx.quadraticCurveTo(ret1.x,ret1.y,ret2.x,ret2.y);ctx.stroke();ctx.restore();
      let pos;if(missionP<=.6)pos=bezier(out0,out1,out2,missionP/.6);else pos=bezier(ret0,ret1,ret2,(missionP-.6)/.4);
      ctx.save();ctx.shadowColor='#d9f2ff';ctx.shadowBlur=12;ctx.fillStyle='#f7fbff';ctx.beginPath();ctx.arc(pos.x,pos.y,layout.phone?3.8:4.2,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;ctx.strokeStyle='rgba(255,255,255,.55)';ctx.beginPath();ctx.arc(pos.x,pos.y,9+Math.sin(t*.004)*2,0,Math.PI*2);ctx.stroke();ctx.restore();
      drawCanvasLabel(ctx,'EARTH',earth.x,earth.y+earth.r+18,portrait?70:95,{size:portrait?10:12,minSize:10,align:'center',color:'rgba(255,255,255,.7)',maxLines:1});
      drawCanvasLabel(ctx,'MOON',moon.x,moon.y+moon.r+18,portrait?70:95,{size:portrait?10:12,minSize:10,align:'center',color:'rgba(255,255,255,.7)',maxLines:1});
      if(!portrait){drawCanvasLabel(ctx,'OUTBOUND',scene.x+scene.width*.36,scene.y+scene.height*.13,120,{size:11,minSize:10,color:'rgba(127,197,255,.78)',maxLines:1});drawCanvasLabel(ctx,'RETURN',scene.x+scene.width*.50,scene.y+scene.height*.91,110,{size:11,minSize:10,color:'rgba(112,198,156,.8)',maxLines:1});}
      const iw=portrait?Math.min(150,scene.width*.45):Math.min(220,scene.width*.31),ih=portrait?104:Math.min(150,scene.height*.34),ix=portrait?scene.right-iw:scene.right-iw,iy=portrait?scene.y+8:scene.y+4;
      ctx.save();ctx.fillStyle='rgba(3,8,13,.88)';ctx.strokeStyle='rgba(255,255,255,.16)';ctx.fillRect(ix,iy,iw,ih);ctx.strokeRect(ix,iy,iw,ih);const imx=ix+iw*.54,imy=iy+ih*.53,imr=Math.min(iw,ih)*.21;drawMoon(ctx,imx,imy,imr);ctx.strokeStyle='rgba(127,197,255,.58)';ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(ix+iw*.12,iy+ih*.72);ctx.bezierCurveTo(ix+iw*.29,iy+ih*.18,ix+iw*.68,iy+ih*.14,ix+iw*.88,iy+ih*.67);ctx.stroke();ctx.fillStyle='rgba(255,255,255,.9)';const lp=clamp((missionP-.47)/.20,0,1),lpos=bezier({x:ix+iw*.12,y:iy+ih*.72},{x:ix+iw*.42,y:iy+ih*.05},{x:ix+iw*.88,y:iy+ih*.67},lp);ctx.beginPath();ctx.arc(lpos.x,lpos.y,3,0,Math.PI*2);ctx.fill();ctx.strokeStyle='rgba(255,104,93,.56)';ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(ix+iw*.07,imy);ctx.lineTo(imx-imr*.25,imy);ctx.stroke();ctx.setLineDash([]);drawCanvasLabel(ctx,'LUNAR FLYBY INSET',ix+8,iy+15,iw-16,{size:portrait?9.5:11,minSize:9,color:'rgba(255,255,255,.72)',maxLines:1});if(portrait&&w<350){
        ctx.fillStyle='rgba(3,8,13,.94)';
        ctx.fillRect(ix+1,iy+ih-35,iw-2,34);
        drawCanvasLabel(ctx,'FAR SIDE /',ix+8,iy+ih-20,iw-16,{size:10,minSize:10,color:'rgba(255,255,255,.78)',maxLines:1});
        drawCanvasLabel(ctx,'LOS BLOCKED',ix+8,iy+ih-8,iw-16,{size:10,minSize:10,color:'rgba(255,255,255,.78)',maxLines:1});
      }else{
        drawCanvasLabel(ctx,'FAR SIDE / LOS BLOCKED',ix+8,portrait?iy+ih-25:iy+ih-9,iw-16,{size:portrait?9:10.5,minSize:9,color:'rgba(255,255,255,.68)',maxLines:portrait?2:1});
      }ctx.restore();
      if(missionP>.515&&missionP<.635){ctx.save();ctx.strokeStyle='rgba(255,104,93,.72)';ctx.setLineDash([3,5]);ctx.beginPath();ctx.moveTo(pos.x,pos.y);ctx.lineTo(earth.x,earth.y);ctx.stroke();ctx.setLineDash([]);drawCanvasLabel(ctx,'LUNAR OCCULTATION REGION',portrait?scene.x+8:scene.x+scene.width*.45,portrait?scene.bottom-18:scene.y+scene.height*.61,portrait?scene.width*.64:scene.width*.5,{size:portrait?10:11,minSize:10,color:'rgba(255,104,93,.92)',maxLines:portrait?2:1});ctx.restore();}
      if(!staticMissionQa)requestAnimationFrame(loop);};requestAnimationFrame(loop);
  }

  }


  // Entry / descent / recovery: NASA-reported anchors with educational interpolation.
  if ($('#entry-lab')) {
  const entryCanvas=$('#entry-canvas');let entryP=0;
  const entryStates=[
    {p:0,time:'23:53 UTC',phase:'Entry interface',cap:'400,000 ft. Mach 35. The atmosphere is about to become the braking system.',alt:'121.9 km',mach:'35',q:'building',heat:'rising',comm:'available',evidence:'NASA REPORTED MILESTONE',lesson:'The atmosphere starts doing the braking.',copy:'NASA reported Orion reaching the atmosphere at 400,000 feet at roughly Mach 35. Aerodynamic drag removes most of the lunar-return kinetic energy; this scene interpolates between public milestones.'},
    {p:.16,time:'~23:54 UTC',phase:'Hypersonic entry',cap:'Speed is still enormous while density rises by orders of magnitude.',alt:'~90 km',mach:'>25',q:'rising fast',heat:'high',comm:'available → degrading',evidence:'EDUCATIONAL INTERPOLATION',lesson:'Heating is extremely sensitive to velocity.',copy:'In Sutton–Graves, convective stagnation heat flux scales approximately with V³ and the square root of density. The visualization is qualitative; use the engineering drawer for the actual MissionLab model curve.'},
    {p:.32,time:'~23:55–23:57 UTC',phase:'Peak-heating / blackout neighborhood',cap:'A luminous plasma envelope forms while Orion rapidly sheds energy.',alt:'~70–55 km',mach:'hypersonic',q:'high',heat:'MODEL PEAK REGION',comm:'planned blackout',evidence:'MODEL + NASA BLACKOUT CONTEXT',lesson:'Expected radio silence is not a communications failure.',copy:'Ionized gas around the capsule can interfere with RF propagation. NASA expected an approximately six-minute blackout after entry interface; MissionLab does not infer plasma density from the communications event.'},
    {p:.53,time:'00:00 UTC',phase:'Communications reacquisition',cap:'The plasma environment relaxes enough for contact to return.',alt:'lower atmosphere',mach:'falling rapidly',q:'falling',heat:'falling',comm:'reacquired',evidence:'NASA REPORTED MINUTE',lesson:'Reacquisition marks an operational transition.',copy:'NASA reported communications reestablished at 8:00 p.m. EDT. That public event is used as a milestone, not as a direct measurement of plasma properties.'},
    {p:.72,time:'00:03 UTC',phase:'Drogue parachutes',cap:'At 23,400 ft, two drogues stabilize and slow Orion.',alt:'7.13 km',mach:'subsonic',q:'low',heat:'low',comm:'available',evidence:'NASA REPORTED · 23,400 FT · 479 FT/S',lesson:'Drogues make the capsule stable before the big canopies arrive.',copy:'NASA reported drogue deployment at 23,400 feet, with velocity dropping to 479 ft/s. A parachute deployed at hypersonic entry speed would see destructive loads, so terminal descent must wait until the atmosphere has already removed almost all of the energy.'},
    {p:.83,time:'00:04 UTC',phase:'Main parachutes',cap:'At 5,400 ft, the drogues cut away and three mains deploy.',alt:'1.65 km',mach:'low',q:'very low',heat:'ambient',comm:'available',evidence:'NASA REPORTED · 5,400 FT · <200 FT/S',lesson:'The mains carry the final descent.',copy:'The drogue stage stabilizes and slows first; the three main canopies then provide the much larger drag area needed to reduce speed for ocean impact.'},
    {p:1,time:'00:07 UTC',phase:'Splashdown',cap:'Orion reaches the Pacific off San Diego.',alt:'0 km',mach:'0',q:'0',heat:'ambient',comm:'recovery',evidence:'NASA REPORTED',lesson:'Splashdown ends the flight path, not the engineering.',copy:'NASA reported parachute-assisted splashdown at 8:07 p.m. EDT on April 10, which is 00:07 UTC on April 11. Recovery, safing, extraction, inspection, and postflight analysis continue after touchdown.'}
  ];
  function nearestState(p){return entryStates.reduce((b,s)=>Math.abs(s.p-p)<Math.abs(b.p-p)?s:b,entryStates[0]);}
  function renderEntry(p,snap=false){entryP=clamp(p,0,1);const st=nearestState(entryP);if(snap)entryP=st.p;const map={time:'entry-time',phase:'entry-phase',cap:'entry-visual-caption',alt:'g-alt',mach:'g-mach',q:'g-q',heat:'g-heat',comm:'g-comm',evidence:'entry-evidence',lesson:'entry-lesson-title',copy:'entry-lesson-copy'};Object.entries(map).forEach(([k,id])=>{const el=$('#'+id);if(el)el.textContent=st[k]});const range=$('#entry-scrubber');if(range)range.value=Math.round(entryP*1000);$$('#entry-milestones button').forEach(b=>b.classList.toggle('active',Math.abs(Number(b.dataset.p)-entryP)<.065));const sig=$('#entry-signal');if(sig){const blackout=entryP>.22&&entryP<.5;sig.classList.toggle('blackout',blackout);$('span',sig).textContent=blackout?'EXPECTED BLACKOUT':entryP<.53?'COMM AVAILABLE':'COMM REACQUIRED';}}
  const eMiles=$('#entry-milestones');if(eMiles){eMiles.innerHTML=entryStates.map(x=>`<button type="button" data-p="${x.p}">${x.phase}</button>`).join('');$$('button',eMiles).forEach(b=>b.addEventListener('click',()=>renderEntry(Number(b.dataset.p),true)));}$('#entry-scrubber')?.addEventListener('input',e=>renderEntry(Number(e.target.value)/1000));
  const entryTopics={speed:'<strong>Why velocity matters so much.</strong> Lunar-return entry begins around Mach 35. In the Sutton–Graves approximation, convective heat flux scales roughly with velocity cubed, so modest changes in speed strongly change the heating term. That model output is not heat-shield telemetry.',pressure:'<strong>Dynamic pressure is aerodynamic loading pressure.</strong> q = ½ρV². Density climbs dramatically while velocity is falling; their competition produces a peak instead of a steady increase all the way to the ocean.',blackout:'<strong>Why radio can disappear.</strong> Hypersonic heating ionizes gas around the capsule. The resulting plasma can interfere with RF propagation. NASA treated this as a planned entry blackout, which is operationally different from an unexpected communications anomaly.',parachutes:'<strong>Why Orion cannot deploy parachutes immediately.</strong> At entry interface the kinetic energy and aerodynamic loads are far beyond what terminal-descent canopies are designed to absorb. The heat shield and atmosphere must do the high-energy braking first.',staging:'<strong>Why drogues and mains are separate.</strong> Drogues deploy first to stabilize and slow the capsule at 23,400 ft. At 5,400 ft they are cut away and three much larger main canopies deploy for the final descent.'};
  function setEntryTopic(k){$$('[data-entry-topic]').forEach(b=>b.classList.toggle('active',b.dataset.entryTopic===k));const e=$('#entry-topic-panel');if(e)e.innerHTML=entryTopics[k];}$$('[data-entry-topic]').forEach(b=>b.addEventListener('click',()=>setEntryTopic(b.dataset.entryTopic)));setEntryTopic('speed');renderEntry(0,true);
  if(entryCanvas){const loop=t=>{const {ctx,w,h,layout}=fitCanvas(entryCanvas);ctx.clearRect(0,0,w,h);const p=entryP,overlayed=!layout.phone,scene=sceneRect(w,h,{top:overlayed?128:0,bottom:overlayed?92:0},layout.phone?8:10);const bg=ctx.createLinearGradient(0,0,0,h);bg.addColorStop(0,p<.55?'#010308':'#071625');bg.addColorStop(.58,p<.38?'#050811':'#183a55');bg.addColorStop(1,p<.6?'#0b1b2a':'#5a91ad');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);if(p<.62)drawStars(ctx,w,h,layout.compact?85:120,71,1-p);
      const limbY=scene.y+scene.height*(.93-.26*clamp(p/.7,0,1)),er=Math.max(scene.width*1.12,scene.height*.92),ex=scene.cx,ey=limbY+er*.72;for(let k=5;k>=1;k--){ctx.strokeStyle=`rgba(85,173,226,${.025*k})`;ctx.lineWidth=k*5;ctx.beginPath();ctx.arc(ex,ey,er-k*2,Math.PI,Math.PI*2);ctx.stroke();}ctx.fillStyle=p>.7?'#15516e':'#071d2e';ctx.beginPath();ctx.arc(ex,ey,er,Math.PI,Math.PI*2);ctx.fill();
      if(p>.84){const ocean=scene.y+scene.height*.82;ctx.fillStyle='rgba(37,111,143,.78)';ctx.fillRect(scene.x,ocean,scene.width,scene.bottom-ocean);ctx.strokeStyle='rgba(216,243,255,.26)';for(let i=0;i<7;i++){ctx.beginPath();ctx.moveTo(scene.x,ocean+i*10+Math.sin(t*.002+i)*2);ctx.quadraticCurveTo(scene.cx,ocean-2+i*10,scene.right,ocean+i*10);ctx.stroke();}}
      const cx=lerp(scene.x+scene.width*(layout.phone?.77:.74),scene.cx,p),cy=lerp(scene.y+scene.height*.17,scene.y+scene.height*.73,p),baseScale=clamp(scene.min/440,.72,1.15),heat=Math.sin(clamp(p/.56,0,1)*Math.PI);ctx.save();ctx.translate(cx,cy);ctx.rotate(lerp(-.45,.08,p));const sc=baseScale*(1+clamp((p-.58)/.42,0,1)*.7);ctx.scale(sc,sc);
      if(p>.08&&p<.58){const trail=clamp(scene.width*.28/baseScale,85,220);for(let i=0;i<16;i++){ctx.strokeStyle=`rgba(255,${85+i*5},${30+i*2},${.04+heat*.04})`;ctx.lineWidth=1+i*.18;ctx.beginPath();ctx.moveTo(12,-8+i);ctx.bezierCurveTo(trail*.35,Math.sin(t*.004+i)*12,trail*.68,(i-8)*3.6,trail,(i-8)*4.6);ctx.stroke();}}
      if(p>=.68&&p<.83){for(const dx of [-20,20]){ctx.strokeStyle='rgba(245,245,242,.88)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(dx*.2,-8);ctx.lineTo(dx,-48);ctx.stroke();ctx.beginPath();ctx.arc(dx,-52,14,Math.PI,0);ctx.stroke();}}
      if(p>=.83&&p<.98){for(const dx of [-34,0,34]){ctx.strokeStyle='rgba(247,247,244,.9)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(dx*.16,-8);ctx.lineTo(dx,-72);ctx.stroke();ctx.fillStyle='rgba(229,234,236,.92)';ctx.beginPath();ctx.arc(dx,-72,30,Math.PI,0);ctx.lineTo(dx-30,-72);ctx.closePath();ctx.fill();}}
      ctx.fillStyle='#dce3e6';ctx.strokeStyle='#29343b';ctx.lineWidth=1.3/sc;ctx.beginPath();ctx.moveTo(-15,10);ctx.quadraticCurveTo(-20,-4,0,-19);ctx.quadraticCurveTo(20,-4,15,10);ctx.quadraticCurveTo(0,18,-15,10);ctx.closePath();ctx.fill();ctx.stroke();ctx.restore();if(!staticMissionQa)requestAnimationFrame(loop);};requestAnimationFrame(loop);}


  }



})();
