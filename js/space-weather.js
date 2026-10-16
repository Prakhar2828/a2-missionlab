(() => {
  'use strict';
  const root=document.querySelector('#space-weather');
  if(!root)return;
  if(!window.A2||!window.A2SpaceWeatherModel)throw new Error('Space Weather requires A2 core and model runtimes.');

  const {$,$$,clamp,lerp,fitCanvas,sceneRect,scenePoint,drawStars,drawEarth,drawCanvasLabel}=window.A2;
  const model=window.A2SpaceWeatherModel;
  const slider=$('#sep-flux-log');
  const canvas=$('#weather-canvas');
  const reducedMotion=window.matchMedia?.('(prefers-reduced-motion: reduce)');
  const staticQa=/(?:^|[?&])space-weather-qa=1(?:&|$)/.test(window.location.search);
  let state={log10Pfu:Number(slider?.value||0),location:'deep'};
  let current=model.evaluate(state),frame=0,lastStamp=0,wavePhase=.46,inView=true;

  function setText(selector,value){const el=$(selector);if(el)el.textContent=value;}
  function levelName(rank){return rank===0?'low':rank<=2?'elevated':'high';}
  function animationAllowed(){return !staticQa&&!reducedMotion?.matches&&!document.hidden&&inView;}

  function renderReadouts(result){
    root.dataset.pfu=String(result.pfu);
    root.dataset.scale=result.scale.scale;
    root.dataset.scaleRank=String(result.scale.rank);
    root.dataset.location=Object.entries(model.LOCATIONS).find(([,v])=>v===result.location)?.[0]||state.location;
    root.dataset.doseKnown=String(result.doseKnown);
    root.dataset.finite=String(result.finite);
    setText('#sep-flux-value',model.formatPfu(result.pfu));
    setText('#weather-scale',result.environment);
    setText('#crew-rad-readout',result.crew);
    setText('#electronics-readout',result.electronics);
    setText('#weather-posture',result.operations);
    setText('#weather-dose',result.doseText);
    setText('#weather-location-context',result.location.context);
    setText('#weather-action',result.operations);
    setText('#weather-action-copy',result.scale.rank===0
      ?'A quiet reference state is not zero radiation. Flight teams still care about background GCR, instrument health, trends, and forecast uncertainty.'
      :'This public reference scale identifies the external energetic-proton environment. Orion-specific decisions require real spacecraft measurements, crew dosimetry, geometry, shielding, system status, and NASA operational criteria.');
    for(const id of ['#crew-rad-card','#electronics-card','#weather-posture-card']){const el=$(id);if(el)el.dataset.level=levelName(result.scale.rank);}
    $$('#location-select button').forEach(button=>{const active=button.dataset.location===state.location;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
    $$('#weather-presets button').forEach(button=>{const active=Math.abs(Number(button.dataset.logPfu)-state.log10Pfu)<1e-9;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
  }

  function drawOrion(ctx,x,y,scale=1){
    ctx.save();ctx.translate(x,y);ctx.rotate(-.18);ctx.scale(scale,scale);
    ctx.shadowColor='rgba(214,236,248,.45)';ctx.shadowBlur=8;
    ctx.fillStyle='#dce4e8';ctx.strokeStyle='#42525d';ctx.lineWidth=1.2;
    ctx.beginPath();ctx.moveTo(-10,8);ctx.quadraticCurveTo(-13,-2,0,-13);ctx.quadraticCurveTo(13,-2,10,8);ctx.quadraticCurveTo(0,13,-10,8);ctx.closePath();ctx.fill();ctx.stroke();
    ctx.shadowBlur=0;ctx.fillStyle='#8798a4';ctx.fillRect(-17,8,34,3);
    ctx.fillStyle='#546b79';ctx.fillRect(-21,6,8,7);ctx.fillRect(13,6,8,7);
    ctx.restore();
  }

  function drawWaveFront(ctx,sun,target,progress,rank,scene){
    const startX=sun.x+sun.r*.76;
    const dx=target.x-startX,dy=target.y-sun.y;
    const x=startX+dx*progress,y=sun.y+dy*progress;
    const angle=Math.atan2(dy,dx);
    const amplitude=clamp(scene.height*(.12+.11*progress),32,92);
    const thickness=2.4+rank*.55;
    const alpha=.12+.055*rank;
    ctx.save();ctx.translate(x,y);ctx.rotate(angle);
    const glow=ctx.createLinearGradient(-12,0,12,0);glow.addColorStop(0,'rgba(255,116,62,0)');glow.addColorStop(.5,`rgba(255,190,92,${Math.min(.78,alpha+.24)})`);glow.addColorStop(1,'rgba(255,116,62,0)');
    ctx.strokeStyle=glow;ctx.lineWidth=thickness;ctx.shadowColor='rgba(255,146,75,.46)';ctx.shadowBlur=10+rank*3;
    ctx.beginPath();ctx.ellipse(0,0,3.2+rank*.7,amplitude,0,-Math.PI*.46,Math.PI*.46);ctx.stroke();
    ctx.shadowBlur=0;ctx.strokeStyle=`rgba(255,216,148,${alpha})`;ctx.lineWidth=1;
    ctx.beginPath();ctx.ellipse(-7,0,2.4,amplitude*.86,0,-Math.PI*.46,Math.PI*.46);ctx.stroke();
    ctx.restore();
  }

  function draw(result,phase=wavePhase){
    if(!canvas)return;
    const {ctx,w,h,layout}=fitCanvas(canvas);
    const scene=sceneRect(w,h,{top:layout.phone?18:24,bottom:layout.phone?24:30},layout.phone?10:18);
    ctx.clearRect(0,0,w,h);
    const bg=ctx.createLinearGradient(0,0,w,h);bg.addColorStop(0,'#02070c');bg.addColorStop(.54,'#07101a');bg.addColorStop(1,'#10100c');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
    drawStars(ctx,w,h,layout.compact?55:90,47,.5);

    const sunPoint=scenePoint(scene,layout.phone?.16:.13,.5),sr=clamp(scene.min*.12,28,48),sun={x:sunPoint.x,y:sunPoint.y,r:sr};
    const glow=ctx.createRadialGradient(sun.x,sun.y,4,sun.x,sun.y,sr*1.58);glow.addColorStop(0,'rgba(255,248,207,.98)');glow.addColorStop(.35,'rgba(255,202,80,.9)');glow.addColorStop(.7,'rgba(211,81,26,.58)');glow.addColorStop(1,'rgba(211,81,26,0)');ctx.fillStyle=glow;ctx.beginPath();ctx.arc(sun.x,sun.y,sr*1.58,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#ffd466';ctx.beginPath();ctx.arc(sun.x,sun.y,sr*.73,0,Math.PI*2);ctx.fill();

    const earth=scenePoint(scene,layout.phone?.63:.64,.65),er=clamp(scene.min*.07,20,31);drawEarth(ctx,earth.x,earth.y,er);
    ctx.strokeStyle='rgba(106,205,219,.14)';ctx.lineWidth=1;for(let i=0;i<4;i++){ctx.beginPath();ctx.ellipse(earth.x,earth.y,er*(1.5+i*.5),er*(1.05+i*.33),-.12,0,Math.PI*2);ctx.stroke();}

    let craft;if(state.location==='leo')craft={x:earth.x+er*1.8,y:earth.y-er*.92};else if(state.location==='lunar')craft=scenePoint(scene,.9,.54);else craft=scenePoint(scene,.83,.3);
    const target={x:craft.x,y:craft.y};

    ctx.save();ctx.strokeStyle='rgba(238,183,92,.16)';ctx.lineWidth=1;ctx.setLineDash([5,8]);ctx.beginPath();ctx.moveTo(sun.x+sr*.78,sun.y);ctx.lineTo(target.x,target.y);ctx.stroke();ctx.setLineDash([]);ctx.restore();

    const rank=result.scale.rank;
    for(let j=0;j<3;j++){
      const p=(phase-j*.31+1)%1;
      drawWaveFront(ctx,sun,target,p,rank,scene);
    }

    const count=16+Math.round(rank*9+Math.max(0,result.log10Pfu)*3);
    for(let i=0;i<count;i++){
      const p=(phase+i/count)%1;
      const x=lerp(sun.x+sr*.76,target.x,p),centerY=lerp(sun.y,target.y,p);
      const spread=scene.height*(.025+.055*p+.013*rank);
      const y=centerY+Math.sin(i*2.31+p*8.7)*spread*(.35+.65*Math.sin(Math.PI*p));
      const alpha=Math.min(.82,.22+.075*rank+.12*Math.sin(Math.PI*p));
      ctx.fillStyle=`rgba(255,${186-Math.min(72,rank*14)},${92-Math.min(38,rank*7)},${alpha})`;
      ctx.beginPath();ctx.arc(x,y,rank>=3?2.15:1.45,0,Math.PI*2);ctx.fill();
    }

    drawOrion(ctx,craft.x,craft.y,layout.phone?.86:1);
    drawCanvasLabel(ctx,'SUN',sun.x,sun.y+sr+22,80,{align:'center',size:10.5,minSize:10,color:'rgba(255,255,255,.62)',maxLines:1});
    drawCanvasLabel(ctx,'PROPAGATING SOLAR DISTURBANCE',scene.x+scene.width*.31,scene.y+20,scene.width*.43,{align:'center',size:layout.phone?9.2:10.5,minSize:8.5,color:'rgba(240,198,118,.74)',maxLines:1});
    drawCanvasLabel(ctx,'EARTH',earth.x,earth.y+er+18,70,{align:'center',size:10,minSize:9,color:'rgba(255,255,255,.56)',maxLines:1});
    drawCanvasLabel(ctx,`${result.location.label} · ORION CONTEXT`,layout.phone?scene.right-2:craft.x-58,craft.y-22,layout.phone?scene.width*.7:138,{align:layout.phone?'right':'left',size:10.5,minSize:9.3,color:'rgba(255,255,255,.75)',maxLines:2});
    drawCanvasLabel(ctx,`${model.formatPfu(result.pfu)} · ${result.scale.scale}`,scene.x+8,scene.y+16,scene.width*.68,{size:layout.phone?11:12,minSize:10,color:'#f0c676',maxLines:1});
    drawCanvasLabel(ctx,'QUALITATIVE PROPAGATION · NOT TRAVEL-TIME OR DOSE PREDICTION',scene.x+8,scene.bottom-2,scene.width*.94,{size:layout.phone?8.7:9.8,minSize:8.4,color:'rgba(255,255,255,.54)',maxLines:1});
    root.dataset.visualDirection='sun-to-orion';
    root.dataset.animation=animationAllowed()?'running':'paused';
  }

  function schedule(){
    if(frame){cancelAnimationFrame(frame);frame=0;}
    lastStamp=0;
    if(animationAllowed())frame=requestAnimationFrame(loop);else draw(current,staticQa?.46:wavePhase);
  }

  function loop(stamp){
    if(!animationAllowed()){frame=0;draw(current,staticQa?.46:wavePhase);return;}
    if(!lastStamp)lastStamp=stamp;
    const dt=Math.min(64,stamp-lastStamp);lastStamp=stamp;
    const speed=.00006+.000012*current.scale.rank;
    wavePhase=(wavePhase+dt*speed)%1;
    draw(current,wavePhase);
    frame=requestAnimationFrame(loop);
  }

  function update(){current=model.evaluate(state);renderReadouts(current);if(!animationAllowed())draw(current,staticQa?.46:wavePhase);}
  slider?.addEventListener('input',event=>{state.log10Pfu=Number(event.target.value);update();});
  $$('#location-select button').forEach(button=>button.addEventListener('click',()=>{state.location=button.dataset.location;update();}));
  $$('#weather-presets button').forEach(button=>button.addEventListener('click',()=>{state.log10Pfu=Number(button.dataset.logPfu);if(slider)slider.value=String(state.log10Pfu);update();}));
  let resizeQueued=false;window.addEventListener('resize',()=>{if(resizeQueued)return;resizeQueued=true;requestAnimationFrame(()=>{resizeQueued=false;draw(current,staticQa?.46:wavePhase);});},{passive:true});
  window.addEventListener('a2:celestialchange',()=>draw(current,staticQa?.46:wavePhase));
  reducedMotion?.addEventListener?.('change',schedule);
  document.addEventListener('visibilitychange',schedule);
  if('IntersectionObserver' in window&&canvas){new IntersectionObserver(entries=>{inView=entries[0]?.isIntersecting!==false;schedule();},{rootMargin:'180px'}).observe(canvas);}
  update();schedule();
})();
