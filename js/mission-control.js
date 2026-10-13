(() => {
  'use strict';

  if (!window.A2) {
    throw new Error('A2 MissionLab core runtime must load before experience runtimes.');
  }

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

  // Mission Control simulator.
  if ($('#mission-control')) {
  const roles={
    FLIGHT:{name:'Flight Director',nav:'Flight Director',title:'What does the integrated mission need?',copy:'FLIGHT is the integrator. The flight director looks across disciplines, protects crew and mission objectives, and decides whether the team needs an action, a trade, or disciplined monitoring.',q:['Is the crew safe?','Is this expected?','Which disciplines are affected?','What decision, if any, is required?']},
    FDO:{name:'Flight Dynamics Officer',nav:'Trajectory',title:'What does the trajectory say?',copy:'FDO monitors Orion’s trajectory, future geometry, maneuver targeting, entry conditions, and the handoff between mission phases.',q:['Where is Orion relative to the plan?','Does future geometry remain acceptable?','Is a correction opportunity needed?','What is the next trajectory constraint?']},
    FAO:{name:'Flight Activities Officer',nav:'Timeline',title:'What happens to the flight plan?',copy:'FAO protects the timeline, procedures, crew activities, and real-time replanning needed to meet mission objectives.',q:['What activity is next?','What must move in the timeline?','What crew work competes for time?','What objective can be deferred?']},
    EECOM:{name:'Emergency, Environmental & Consumables Officer',nav:'Crew systems',title:'What does this mean for the crew environment?',copy:'EECOM watches environmental control and life support, thermal conditions, consumables, and integrated emergency response.',q:['Is required function still available?','Is habitability affected?','What redundancy remains?','Is this closed in flight or postflight?']},
    COMM:{name:'Communications lens',nav:'Links',title:'Is loss of signal expected or anomalous?',copy:'COMM is MissionLab shorthand for the communications problem: geometry-driven occultation, entry plasma blackout, network transitions, reacquisition, and unexpected link issues. It is not asserted to be an exact Artemis II console acronym.',q:['Is line of sight physically blocked?','Which network is in use?','When is reacquisition expected?','Is this a link anomaly or normal geometry?']},
    SCIENCE:{name:'Science Officer',nav:'Lunar science',title:'What observation opportunity exists right now?',copy:'The Artemis SCIENCE console integrates lunar science and geology objectives into mission execution, connecting crew observations with the supporting Science Evaluation Room.',q:['What target is visible?','What lighting makes it useful?','What did the crew actually observe?','What needs postflight analysis?']},
    ENGINEERING:{name:'Engineering support lens',nav:'Evidence',title:'What technical explanation is actually supported?',copy:'Engineering support is a MissionLab synthesis lens rather than a claimed Artemis front-room console name. It tests hypotheses against evidence and keeps “action taken” separate from “root cause confirmed.”',q:['What evidence constrains the explanation?','What is still unknown?','Which model or test is relevant?','What must be closed after flight?']}
  };
  const mcScenarios=[
    {id:'occultation',tag:'EXPECTED GEOMETRY',title:'Lunar loss of signal',summary:'Orion is moving behind the Moon. Lunar terrain is about to block the radio path to Earth.',clock:'MET 05:00:08:10',trace:['detect LOS closure','confirm geometry','expect blackout','hold timeline','reacquire'],kind:'orbit'},
    {id:'rtc2',tag:'TARGETING DECISION',title:'Return trajectory correction',summary:'A small velocity correction is being evaluated against the future entry corridor and remaining maneuver opportunities.',clock:'MET 08:04:17:48',trace:['update state','predict future path','compare constraints','target burn','execute','reassess'],kind:'burn'},
    {id:'waste',tag:'SYSTEM TROUBLESHOOTING',title:'Orion toilet fault response',summary:'The crew reported a blinking fault light. Mission Control assessed the data and worked with the crew until normal operation was restored; the public troubleshooting sequence does not by itself establish a root cause.',clock:'MET 03:11:40:00',trace:['detect indication','gather evidence','protect function','adjust activity','monitor','defer root cause'],kind:'system'},
    {id:'entry',tag:'EXPECTED ENTRY CONSTRAINT',title:'Plasma communications blackout',summary:'Ionized flow around Orion can interrupt radio communications during hypersonic entry. Expected silence is not the same as a communications failure.',clock:'MET 09:01:22:00',trace:['predict blackout','enter window','monitor trajectory','wait for geometry/flow change','reacquire'],kind:'entry'}
  ];
  let mcScenario=mcScenarios[0],mcRole='FLIGHT';
  function renderMc(){const s=mcScenario,r=roles[mcRole];$('#mc-clock').textContent=s.clock;$('#mc-event-class').textContent=s.tag;$('#mc-event-title').textContent=s.title;$('#mc-event-summary').textContent=s.summary;$('#mc-role-label').textContent=`${mcRole==='ENGINEERING'?'ENG SUPPORT':mcRole} · ${r.name}`;$('#mc-role-title').textContent=r.title;$('#mc-role-copy').textContent=r.copy;$('#mc-questions').innerHTML=r.q.map(x=>`<div>${x}</div>`).join('');$('#mc-decision-trace').innerHTML=s.trace.map((x,i)=>`<i><b>${String(i+1).padStart(2,'0')}</b>${x}</i>`).join('');$$('#mc-strip button').forEach(b=>b.classList.toggle('active',b.dataset.role===mcRole));$$('#mc-events button').forEach(b=>b.classList.toggle('active',b.dataset.id===s.id));}
  const strip=$('#mc-strip');if(strip){strip.innerHTML=Object.entries(roles).map(([k,r])=>`<button type="button" data-role="${k}" title="${r.name}"><b>${k==='ENGINEERING'?'ENG SUPPORT':k}</b><small>${r.nav}</small></button>`).join('');$$('button',strip).forEach(b=>b.addEventListener('click',()=>{mcRole=b.dataset.role;renderMc();}));}
  const evBox=$('#mc-events');if(evBox){evBox.innerHTML=mcScenarios.map(s=>`<button type="button" data-id="${s.id}"><small>${s.tag}</small><b>${s.title}</b></button>`).join('');$$('button',evBox).forEach(b=>b.addEventListener('click',()=>{mcScenario=mcScenarios.find(s=>s.id===b.dataset.id);renderMc();}));}renderMc();
  const mcCanvas=$('#mc-canvas');if(mcCanvas){const loop=t=>{const {ctx,w,h,layout}=fitCanvas(mcCanvas),scene=sceneRect(w,h,{},layout.phone?14:20),u=scene.min;ctx.clearRect(0,0,w,h);ctx.fillStyle='#02070a';ctx.fillRect(0,0,w,h);ctx.strokeStyle='rgba(96,144,176,.08)';ctx.lineWidth=1;for(let x=scene.x;x<scene.right;x+=40){ctx.beginPath();ctx.moveTo(x,scene.y);ctx.lineTo(x,scene.bottom);ctx.stroke()}for(let y=scene.y;y<scene.bottom;y+=40){ctx.beginPath();ctx.moveTo(scene.x,y);ctx.lineTo(scene.right,y);ctx.stroke()}
      if(mcScenario.kind==='orbit'){const e=scenePoint(scene,.18,.56),m=scenePoint(scene,layout.phone?.72:.67,.52),er=clamp(u*.085,27,42),mr=clamp(u*.145,48,72);drawEarth(ctx,e.x,e.y,er);drawMoon(ctx,m.x,m.y,mr);const ox=scene.x+scene.width*.59+Math.sin(t*.0005)*clamp(scene.width*.035,10,25),oy=scene.y+scene.height*.34;ctx.strokeStyle='rgba(255,100,90,.65)';ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(ox,oy);ctx.lineTo(e.x,e.y);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(ox,oy,4,0,Math.PI*2);ctx.fill();drawCanvasLabel(ctx,'LOS BLOCKED BY LUNAR TERRAIN',layout.phone?scene.x+8:scene.x+scene.width*.42,layout.phone?scene.y+26:scene.y+scene.height*.78,layout.phone?scene.width*.72:scene.width*.52,{size:layout.phone?10.5:12,minSize:10,color:'#ff7f76',maxLines:2});}
      else if(mcScenario.kind==='burn'){const e=scenePoint(scene,.16,.58),er=clamp(u*.08,26,38);drawEarth(ctx,e.x,e.y,er);const p0=scenePoint(scene,.23,.60),p1=scenePoint(scene,.52,.16),p2=scenePoint(scene,.86,.52),p3=scenePoint(scene,.55,.12),p4=scenePoint(scene,.88,.47);ctx.strokeStyle='rgba(127,197,255,.4)';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(p0.x,p0.y);ctx.quadraticCurveTo(p1.x,p1.y,p2.x,p2.y);ctx.stroke();ctx.strokeStyle='rgba(125,224,173,.78)';ctx.beginPath();ctx.moveTo(p0.x,p0.y);ctx.quadraticCurveTo(p3.x,p3.y,p4.x,p4.y);ctx.stroke();const burnPt=scenePoint(scene,.54,.21);ctx.fillStyle='#f5f9fc';ctx.beginPath();ctx.arc(burnPt.x,burnPt.y,4,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#f0c476';ctx.beginPath();ctx.moveTo(burnPt.x,burnPt.y);ctx.lineTo(burnPt.x+scene.width*.055,burnPt.y-scene.height*.055);ctx.stroke();drawCanvasLabel(ctx,'ΔV',burnPt.x+scene.width*.06,burnPt.y-scene.height*.06,50,{size:12,minSize:10,color:'#f0c476',maxLines:1});}
      else if(mcScenario.kind==='system'){const cols=[.24,.36,.58,.72],labels=['TEMP','WASTE','CABIN','POWER'];cols.forEach((v,i)=>{const bw=scene.width*.12,x=scene.x+scene.width*(.12+i*.21),base=scene.y+scene.height*.82,bh=scene.height*v*.7;ctx.fillStyle=i===1?'rgba(255,103,95,.65)':'rgba(111,231,225,.4)';ctx.fillRect(x,base-bh,bw,bh);drawCanvasLabel(ctx,labels[i],x+bw/2,base+18,bw+12,{size:layout.phone?9.5:11,minSize:9,align:'center',color:'rgba(255,255,255,.62)',maxLines:1});});}
      else{const grad=ctx.createLinearGradient(scene.x,0,scene.right,0);grad.addColorStop(0,'#1b2230');grad.addColorStop(.5,'#a23c1e');grad.addColorStop(1,'#240703');ctx.fillStyle=grad;ctx.fillRect(scene.x,scene.y,scene.width,scene.height);ctx.strokeStyle='rgba(255,220,190,.35)';for(let i=0;i<14;i++){ctx.beginPath();ctx.moveTo(scene.x,scene.y+(i/14)*scene.height+Math.sin(t*.002+i)*8);ctx.bezierCurveTo(scene.x+scene.width*.25,scene.y+scene.height*.2+i*9,scene.x+scene.width*.55,scene.bottom-i*7,scene.right,scene.y+scene.height*.32+i*7);ctx.stroke()}drawCanvasLabel(ctx,'EXPECTED REACQUISITION WINDOW AHEAD',scene.right-8,scene.y+30,scene.width*.72,{size:layout.phone?10.5:13,minSize:10,align:'right',color:'rgba(255,255,255,.92)',maxLines:2});}
      requestAnimationFrame(loop);};requestAnimationFrame(loop);}


  }


})();
