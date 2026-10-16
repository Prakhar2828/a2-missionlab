(() => {
  'use strict';
  if(!window.A2||!window.A2EntryModel)throw new Error('Entry runtime requires A2 core and A2EntryModel.');
  const { $, $$, clamp, fitCanvas, roundRect, drawCanvasLabel }=window.A2;
  const model=window.A2EntryModel;
  const root=$('#entry-lab[data-entry-phase-i]');
  if(!root)return;

  const canvas=$('#entry-flight-canvas');
  const scrubber=$('#entry-scrubber');
  const eventRail=$('#entry-event-rail');
  const play=$('#entry-play');
  const reset=$('#entry-reset');
  const stage=$('.entry-flight-stage');
  const stageTopline=$('.entry-stage-topline');
  let stagePlay=null,stageReset=null;
  const entryPlaybackProfile='r8-cinematic-paced';
  let t=0,playing=false,lastFrame=0;
  const qa=/(?:^|[?&])entry-qa=1(?:&|$)/.test(location.search);

  function fmt(value,digits=1){return Number.isFinite(value)?value.toFixed(digits):'—';}
  function metric(id,value,detail){const el=$(id);if(el)el.textContent=value;const d=$(id+'-detail');if(d)d.textContent=detail||'';}
  function nearestEvent(seconds){return model.events.reduce((best,e)=>Math.abs(e.t-seconds)<Math.abs(best.t-seconds)?e:best,model.events[0]);}
  function installStageControls(){
    if(!stageTopline||$('#entry-stage-play'))return;
    const dock=document.createElement('div');
    dock.className='entry-stage-live-controls';
    dock.innerHTML='<span>WATCH THE RECONSTRUCTION</span><div><button type="button" id="entry-stage-play" aria-pressed="false">Play profile</button><button type="button" id="entry-stage-reset">Reset</button></div>';
    const evidence=stageTopline.querySelector('.entry-stage-evidence');
    stageTopline.insertBefore(dock,evidence||null);
    stagePlay=$('#entry-stage-play');
    stageReset=$('#entry-stage-reset');
  }

  function renderEventRail(){
    eventRail.innerHTML=model.events.map(e=>`<button type="button" data-t="${e.t}" data-kind="${e.kind}"><span>${e.time}</span><b>${e.label}</b><small>${e.evidence}</small></button>`).join('');
    $$('button',eventRail).forEach(b=>b.addEventListener('click',()=>setTime(Number(b.dataset.t),false)));
  }

  function renderRecovery(){
    const target=$('#entry-recovery-rail');
    if(!target)return;
    target.innerHTML=model.recovery.map((e,i)=>`<article><div class="entry-recovery-clock"><span>${e.time}</span><b>${e.delta}</b></div><div><small>${i===0?'RECOVERY STARTS':'RECOVERY CONTINUES'}</small><h4>${e.title}</h4><p>${e.copy}</p><em>${e.evidence}</em></div></article>`).join('');
  }

  function setTime(next,fromAnimation=false){
    t=clamp(next,0,model.durationSeconds);
    const s=model.stateAt(t), nearest=nearestEvent(t);
    scrubber.value=String(t);
    scrubber.setAttribute('aria-valuetext',`${s.utc} · ${s.phase.title} · ${nearest.label}`);
    $('#entry-analysis-time').textContent=s.utc;
    $('#entry-analysis-offset').textContent=`analysis +${fmt(t,1)} s`;
    $('#entry-phase').textContent=s.phase.title;
    $('#entry-visual-caption').textContent=s.phase.copy;
    $('#entry-evidence').textContent=nearest.evidence;
    $('#entry-current-event').textContent=nearest.label;
    $('#entry-comm').textContent=s.comm.label;
    $('#entry-comm').dataset.tone=s.comm.tone;
    $('#entry-comm-detail').textContent=s.comm.detail;
    $('#entry-heat-domain').textContent=s.heatDomain;
    $('#entry-energy-removed').textContent=`${Math.round(s.kineticEnergyRemovedFraction*100)}%`;

    metric('#g-alt',`${fmt(s.altitudeKm,s.altitudeKm<10?2:1)} km`,'WGS 84 reconstruction');
    metric('#g-speed',`${fmt(s.speedKmS,s.speedKmS<1?3:2)} km/s`,'Earth-relative reconstruction');
    metric('#g-mach',`${fmt(s.mach,s.mach<2?2:1)}`,'modeled free-stream Mach');
    metric('#g-q',s.dynamicPressureKpa===null?'—':`${fmt(s.dynamicPressureKpa,s.dynamicPressureKpa<1?3:2)} kPa`,s.dynamicPressureKpa===null?'not surfaced beyond Phase 2 hypersonic model window':'modeled from NRLMSIS density + reconstructed speed');
    metric('#g-heat',s.heatFluxWcm2===null?'—':`${fmt(s.heatFluxWcm2,s.heatFluxWcm2<10?2:1)} W/cm²`,s.heatFluxWcm2===null?'Sutton–Graves interpretation ends at final Mach 5 crossing':'MODELED external convective heat flux');

    $('#entry-heat-fill').style.width=`${s.heatNormalized*100}%`;
    $('#entry-q-fill').style.width=`${s.qNormalized*100}%`;
    $('#entry-energy-fill').style.width=`${s.kineticEnergyRemovedFraction*100}%`;
    root.dataset.phase=s.phase.id;
    root.dataset.loft=String(s.inLoft);
    root.dataset.finite=String([s.altitudeKm,s.speedKmS,s.mach].every(Number.isFinite));
    $$('button',eventRail).forEach(b=>{const near=Math.abs(Number(b.dataset.t)-t)<18;const current=Number(b.dataset.t)===nearest.t;b.classList.toggle('active',near);if(current)b.setAttribute('aria-current','true');else b.removeAttribute('aria-current');});
    if(!fromAnimation)draw();
  }

  function pathPoint(plot,seconds,alt){
    const x=plot.x+plot.w*(seconds/model.durationSeconds);
    const y=plot.y+plot.h*(1-clamp(alt/125,0,1));
    return{x,y};
  }

  function drawParachutes(ctx,p,kind,scale=1){
    const count=kind==='main'?3:2, spread=kind==='main'?24:18, radius=kind==='main'?18:11;
    ctx.save();ctx.strokeStyle='rgba(244,247,248,.9)';ctx.fillStyle='rgba(222,230,234,.2)';ctx.lineWidth=1.2;
    for(let i=0;i<count;i++){
      const dx=(i-(count-1)/2)*spread*scale, cy=p.y-34*scale;
      ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.x+dx,cy+radius*.15);ctx.stroke();
      ctx.beginPath();ctx.arc(p.x+dx,cy,radius*scale,Math.PI,0);ctx.lineTo(p.x+dx-radius*scale,cy);ctx.closePath();ctx.fill();ctx.stroke();
    }ctx.restore();
  }

  function draw(){
    if(!canvas)return;
    const {ctx,w,h}=fitCanvas(canvas);ctx.clearRect(0,0,w,h);
    const pad={l:52,r:20,t:30,b:46};const plot={x:pad.l,y:pad.t,w:Math.max(1,w-pad.l-pad.r),h:Math.max(1,h-pad.t-pad.b)};
    const bg=ctx.createLinearGradient(0,0,0,h);bg.addColorStop(0,'#02060b');bg.addColorStop(.45,'#101116');bg.addColorStop(1,'#173848');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);

    const bands=[[100,'UPPER ATMOSPHERE'],[80,'DEEPER CONTINUUM'],[60,'LOFT / REBOUND REGION'],[40,'LOWER HYPERSONIC'],[20,'PARACHUTE APPROACH'],[0,'OCEAN']];
    ctx.save();ctx.strokeStyle='rgba(255,255,255,.1)';ctx.fillStyle='rgba(255,255,255,.42)';ctx.font='600 10px system-ui';
    bands.forEach(([a,label])=>{const y=pathPoint(plot,0,a).y;ctx.beginPath();ctx.moveTo(plot.x,y);ctx.lineTo(plot.x+plot.w,y);ctx.stroke();ctx.fillText(`${a} km`,8,y+3);if(w>760)ctx.fillText(label,plot.x+7,y-6);});ctx.restore();

    const ls=pathPoint(plot,model.constants.loftStart,60.350128), le=pathPoint(plot,model.constants.loftEnd,64.211808);
    ctx.save();ctx.fillStyle='rgba(112,181,220,.08)';ctx.fillRect(ls.x,plot.y,Math.max(1,le.x-ls.x),plot.h);ctx.strokeStyle='rgba(112,181,220,.35)';ctx.setLineDash([5,5]);ctx.strokeRect(ls.x,plot.y,Math.max(1,le.x-ls.x),plot.h);ctx.setLineDash([]);drawCanvasLabel(ctx,'ARTEMIS II LOFT / REBOUND',ls.x+8,plot.y+18,Math.max(100,le.x-ls.x-16),{size:10,minSize:8,color:'rgba(164,210,236,.82)',maxLines:2});ctx.restore();

    ctx.save();ctx.strokeStyle='rgba(245,201,170,.4)';ctx.lineWidth=2;ctx.beginPath();
    for(let x=0;x<=model.durationSeconds;x+=4){const p=pathPoint(plot,x,model.altitudeAt(x));if(x===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);}ctx.stroke();
    ctx.strokeStyle='rgba(255,133,92,.95)';ctx.lineWidth=3;ctx.beginPath();
    for(let x=0;x<=t;x+=3){const p=pathPoint(plot,x,model.altitudeAt(x));if(x===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);}ctx.stroke();ctx.restore();

    model.events.forEach(e=>{const p=pathPoint(plot,e.t,model.altitudeAt(e.t));ctx.save();ctx.strokeStyle=e.kind==='public'?'rgba(118,203,162,.32)':'rgba(255,255,255,.14)';ctx.setLineDash(e.kind==='public'?[3,5]:[2,6]);ctx.beginPath();ctx.moveTo(p.x,plot.y);ctx.lineTo(p.x,plot.y+plot.h);ctx.stroke();ctx.restore();});

    const s=model.stateAt(t), p=pathPoint(plot,t,s.altitudeKm), glow=10+28*s.heatNormalized;
    ctx.save();const g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,glow);g.addColorStop(0,`rgba(255,143,91,${.75*s.heatNormalized+.15})`);g.addColorStop(1,'rgba(255,120,70,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(p.x,p.y,glow,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#f2f5f6';ctx.strokeStyle='#ff8c63';ctx.lineWidth=2;ctx.beginPath();ctx.arc(p.x,p.y,5.5,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.restore();

    if(t>=model.constants.drogueOffset&&t<model.constants.mainOffset)drawParachutes(ctx,p,'drogue',.8);
    if(t>=model.constants.mainOffset&&t<model.constants.splashMinuteOffset)drawParachutes(ctx,p,'main',1);

    const oceanY=pathPoint(plot,0,0).y;ctx.fillStyle='rgba(62,130,160,.28)';ctx.fillRect(plot.x,oceanY-2,plot.w,plot.y+plot.h-oceanY+2);
    const labelW=Math.min(210,Math.max(105,plot.w*.26));
    const labelX=p.x+labelW+18<=plot.x+plot.w?p.x+12:Math.max(plot.x+8,p.x-labelW-12);
    drawCanvasLabel(ctx,s.phase.title,labelX,Math.max(plot.y+20,p.y-12),labelW,{size:11,minSize:8,color:'rgba(255,255,255,.86)',maxLines:2});
    root.dataset.canvasPass=String(Number.isFinite(p.x)&&Number.isFinite(p.y)&&w>0&&h>0);
  }

  scrubber.min='0';scrubber.max=String(model.durationSeconds);scrubber.step='.1';
  scrubber.addEventListener('input',()=>{playing=false;updatePlay();setTime(Number(scrubber.value),false);});
  function updatePlay(){
    play.textContent=playing?'Pause':'Play';play.setAttribute('aria-pressed',String(playing));
    if(stagePlay){stagePlay.textContent=playing?'Pause profile':'Play profile';stagePlay.setAttribute('aria-pressed',String(playing));}
  }
  function startEntryPlayback(){
    const launch=()=>{if(playing)requestAnimationFrame(tick);};
    if(stage){
      const r=stage.getBoundingClientRect();
      const offscreen=r.top<0||r.bottom>innerHeight;
      if(offscreen){
        stage.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
        setTimeout(launch,300);
        return;
      }
    }
    launch();
  }
  function toggleEntryPlayback(){playing=!playing;lastFrame=0;root.dataset.playbackProfile=entryPlaybackProfile;updatePlay();if(playing)startEntryPlayback();}
  function resetEntryPlayback(){playing=false;lastFrame=0;updatePlay();setTime(0,false);}
  play.addEventListener('click',toggleEntryPlayback);
  reset.addEventListener('click',resetEntryPlayback);
  function tick(now){if(!playing)return;if(!lastFrame)lastFrame=now;const dt=Math.min(80,now-lastFrame);lastFrame=now;const factor=t<240?.018:t<569?.028:t<629?.014:t<810?.018:.010;setTime(t+dt*factor,true);draw();if(t>=model.durationSeconds){playing=false;updatePlay();return;}requestAnimationFrame(tick);}
  addEventListener('resize',draw,{passive:true});

  installStageControls();
  if(stagePlay)stagePlay.addEventListener('click',toggleEntryPlayback);
  if(stageReset)stageReset.addEventListener('click',resetEntryPlayback);
  root.dataset.playbackProfile=entryPlaybackProfile;
  renderEventRail();renderRecovery();setTime(0,false);updatePlay();draw();
  if(qa){
    const probe=[0,20,85,112.294128,239.647374,431,464.815771,569.134,629.134,817.957676].map(model.stateAt);
    root.dataset.qaFinite=String(probe.every(s=>[s.altitudeKm,s.speedKmS,s.mach,s.progress].every(Number.isFinite)));
    root.dataset.qaLoft=String(model.stateAt(150).altitudeKm<model.stateAt(239.647374).altitudeKm);
    root.dataset.qaHeating=String(Math.abs(model.stateAt(85).heatFluxWcm2-109.641953)<1e-6&&model.stateAt(431).heatFluxWcm2<10);
    root.dataset.qaPressure=String(Math.abs(model.stateAt(95).dynamicPressureKpa-12.798779)<1e-6&&Math.abs(model.stateAt(431).dynamicPressureKpa-12.808389)<1e-6);
    root.dataset.qaEvidence=String(root.textContent.includes('Not measured TPS telemetry')&&root.textContent.includes('not a skip entry')&&root.textContent.includes('exact start/end seconds unknown'));
  }
})();
