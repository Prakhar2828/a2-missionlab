(() => {
  'use strict';
  const root=document.querySelector('#space-weather');
  if(!root)return;
  if(!window.A2||!window.A2SpaceWeatherModel)throw new Error('Space Weather requires A2 core and model runtimes.');

  const {$,$$,clamp,fitCanvas,sceneRect,scenePoint,drawStars,drawEarth,drawCanvasLabel}=window.A2;
  const model=window.A2SpaceWeatherModel;
  const slider=$('#sep-flux-log');
  const canvas=$('#weather-canvas');
  let state={log10Pfu:Number(slider?.value||0),location:'deep'};

  function setText(selector,value){const el=$(selector);if(el)el.textContent=value;}
  function levelName(rank){return rank===0?'low':rank<=2?'elevated':'high';}

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
    draw(result);
  }

  function draw(result){
    if(!canvas)return;
    const {ctx,w,h,layout}=fitCanvas(canvas);
    const scene=sceneRect(w,h,{top:layout.phone?18:24,bottom:layout.phone?24:30},layout.phone?10:18);
    ctx.clearRect(0,0,w,h);
    const bg=ctx.createLinearGradient(0,0,w,h);bg.addColorStop(0,'#02070c');bg.addColorStop(.56,'#07101a');bg.addColorStop(1,'#10100c');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
    drawStars(ctx,w,h,layout.compact?55:90,47,.5);
    const sun=scenePoint(scene,layout.phone?.18:.14,.48),sr=clamp(scene.min*.12,28,48);
    const glow=ctx.createRadialGradient(sun.x,sun.y,4,sun.x,sun.y,sr*1.45);glow.addColorStop(0,'rgba(255,248,207,.98)');glow.addColorStop(.35,'rgba(255,202,80,.88)');glow.addColorStop(.68,'rgba(211,81,26,.6)');glow.addColorStop(1,'rgba(211,81,26,0)');ctx.fillStyle=glow;ctx.beginPath();ctx.arc(sun.x,sun.y,sr*1.45,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#ffd466';ctx.beginPath();ctx.arc(sun.x,sun.y,sr*.72,0,Math.PI*2);ctx.fill();
    const earth=scenePoint(scene,layout.phone?.56:.57,.64),er=clamp(scene.min*.07,20,31);drawEarth(ctx,earth.x,earth.y,er);
    ctx.strokeStyle='rgba(106,205,219,.14)';ctx.lineWidth=1;for(let i=0;i<4;i++){ctx.beginPath();ctx.ellipse(earth.x,earth.y,er*(1.5+i*.5),er*(1.05+i*.33),-.12,0,Math.PI*2);ctx.stroke();}
    let craft;if(state.location==='leo')craft={x:earth.x+er*1.75,y:earth.y-er*.9};else if(state.location==='lunar')craft=scenePoint(scene,.9,.55);else craft=scenePoint(scene,.82,.31);
    const count=8+Math.round(result.scale.rank*7+Math.max(0,result.log10Pfu)*3);
    const span=Math.max(1,craft.x-(sun.x+sr));
    for(let i=0;i<count;i++){
      const phase=(i+.5)/count,x=sun.x+sr+phase*span,y=scene.y+scene.height*(.28+.43*((i*37)%101)/100)+Math.sin(i*1.71)*7;
      const alpha=.18+.09*result.scale.rank;ctx.fillStyle=`rgba(255,${180-Math.min(85,result.scale.rank*18)},${96-Math.min(46,result.scale.rank*8)},${Math.min(.82,alpha)})`;ctx.beginPath();ctx.arc(x,y,result.scale.rank>=3?2.2:1.5,0,Math.PI*2);ctx.fill();
    }
    ctx.save();ctx.translate(craft.x,craft.y);ctx.rotate(-.22);ctx.strokeStyle='#e6eef2';ctx.fillStyle='#cfd8dd';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(-10,7);ctx.lineTo(0,-9);ctx.lineTo(11,7);ctx.closePath();ctx.fill();ctx.stroke();ctx.fillStyle='#8aa4b1';ctx.fillRect(-17,5,34,3);ctx.restore();
    drawCanvasLabel(ctx,'SUN',sun.x,sun.y+sr+22,80,{align:'center',size:10.5,minSize:10,color:'rgba(255,255,255,.62)',maxLines:1});
    drawCanvasLabel(ctx,`${result.location.label} · ORION CONTEXT`,layout.phone?scene.right-2:craft.x-58,craft.y-20,layout.phone?scene.width*.7:130,{align:layout.phone?'right':'left',size:10.5,minSize:9.5,color:'rgba(255,255,255,.72)',maxLines:2});
    drawCanvasLabel(ctx,`${model.formatPfu(result.pfu)} · ${result.scale.scale}`,scene.x+8,scene.y+16,scene.width*.72,{size:layout.phone?11:12,minSize:10,color:'#f0c676',maxLines:1});
    drawCanvasLabel(ctx,'VISUALIZATION = QUALITATIVE · NOT DOSE TRANSPORT',scene.x+8,scene.bottom-2,scene.width*.92,{size:layout.phone?9.2:10,minSize:8.8,color:'rgba(255,255,255,.54)',maxLines:1});
  }

  function update(){renderReadouts(model.evaluate(state));}
  slider?.addEventListener('input',event=>{state.log10Pfu=Number(event.target.value);update();});
  $$('#location-select button').forEach(button=>button.addEventListener('click',()=>{state.location=button.dataset.location;update();}));
  $$('#weather-presets button').forEach(button=>button.addEventListener('click',()=>{state.log10Pfu=Number(button.dataset.logPfu);if(slider)slider.value=String(state.log10Pfu);update();}));
  let resizeQueued=false;window.addEventListener('resize',()=>{if(resizeQueued)return;resizeQueued=true;requestAnimationFrame(()=>{resizeQueued=false;draw(model.evaluate(state));});},{passive:true});
  window.addEventListener('a2:celestialchange',()=>draw(model.evaluate(state)));
  update();
})();
