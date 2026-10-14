(() => {
  'use strict';

  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const rad=d=>d*Math.PI/180;
  const fmt=(v,d=1)=>Number(v).toFixed(d);
  const query=new URLSearchParams(location.search);
  const qa=query.get('psi-qa')==='1';
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');

  const PSI=window.A2PsiModel;
  if(!PSI) throw new Error('PSI model runtime must load before PSI experience runtime.');
  const DEFAULTS=PSI.DEFAULTS;
  const state={...DEFAULTS};

  const canvas=$('#psi-canvas');
  if(!canvas) return;
  const ctx=canvas.getContext('2d');
  const controls={
    altitude:$('#psi-alt'),throttle:$('#psi-throttle'),cant:$('#psi-cant'),spread:$('#psi-spread'),hardwareDistance:$('#psi-hardware')
  };
  const outputs={
    altitude:$('#psi-alt-value'),throttle:$('#psi-throttle-value'),cant:$('#psi-cant-value'),spread:$('#psi-spread-value'),hardware:$('#psi-hardware-value'),
    area:$('#psi-footprint-area'),offset:$('#psi-offset'),loading:$('#psi-loading'),erosion:$('#psi-erosion'),hardwareRisk:$('#psi-hardware-risk'),hardwareDetail:$('#psi-hardware-detail'),visibility:$('#psi-visibility'),ops:$('#psi-ops-detail')
  };

  let canvasW=1,canvasH=1,dpr=1,visible=true,raf=0,startTime=performance.now();
  const particles=Array.from({length:80},(_,i)=>({seed:(i*.61803398875)%1,phase:(i*.4137)%1,side:i%2?-1:1}));

  function model(input=state){return PSI.compute(input);}
  function syncUI(){
    const m=model();
    outputs.altitude.textContent=`${state.altitude} m`;
    outputs.throttle.textContent=`${state.throttle}%`;
    outputs.cant.textContent=`${state.cant}°`;
    outputs.spread.textContent=`${state.spread}°`;
    outputs.hardware.textContent=`${state.hardwareDistance} m`;
    outputs.area.textContent=`${Math.round(m.footprint.area)} m²`;
    outputs.offset.textContent=`${fmt(m.footprint.centroid.x,1)} m`;
    outputs.loading.textContent=`${fmt(m.loadingRatio,2)}×`;
    outputs.erosion.textContent=m.erosionLabel;
    outputs.hardwareRisk.textContent=m.hardwareTitle;
    outputs.hardwareDetail.textContent=m.clearance<=0
      ?`Hardware sits ${fmt(Math.abs(m.clearance),1)} m inside the idealized downrange footprint edge. This is a geometry flag, not a damage prediction.`
      :`Hardware clearance is ${fmt(m.clearance,1)} m beyond the modeled footprint edge.${m.hardwareLevel==='near'?' The remaining concern is a conceptual screening flag, not a predicted ejecta reach.':''}`;
    outputs.visibility.textContent=m.visibility;
    outputs.ops.textContent=`Relative erosion tendency is ${fmt(m.erosionRatio,2)}× the reference case. NASA reports that PSI can create ejecta, contamination and visibility/sensor hazards; MissionLab does not convert this proxy into a certified keep-out distance.`;
    $$('#engine-count button').forEach(b=>b.classList.toggle('active',Number(b.dataset.engines)===state.engines));
    $$('#regolith-select button').forEach(b=>b.classList.toggle('active',b.dataset.regolith===state.regolith));
    draw(performance.now());
    return m;
  }

  function resize(){
    const r=canvas.getBoundingClientRect();
    canvasW=Math.max(1,r.width);canvasH=Math.max(1,r.height);
    const raw=window.devicePixelRatio||1;
    const budget=Math.sqrt(3500000/Math.max(1,canvasW*canvasH));
    dpr=clamp(Math.min(raw,budget),1,2.5);
    const w=Math.round(canvasW*dpr),h=Math.round(canvasH*dpr);
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
    ctx.setTransform(dpr,0,0,dpr,0,0);
    draw(performance.now());
  }

  function line(x1,y1,x2,y2,stroke,width=1,dash=[]){ctx.save();ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.setLineDash(dash);ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();ctx.restore();}
  function label(text,x,y,align='left',color='rgba(255,255,255,.72)',size=11){ctx.save();ctx.font=`700 ${size}px system-ui`;ctx.textAlign=align;ctx.textBaseline='middle';ctx.fillStyle=color;ctx.fillText(text,x,y);ctx.restore();}

  function draw(time){
    if(!ctx||canvasW<2||canvasH<2) return;
    const m=model();
    ctx.clearRect(0,0,canvasW,canvasH);
    const bg=ctx.createLinearGradient(0,0,0,canvasH);bg.addColorStop(0,'#020303');bg.addColorStop(.68,'#050403');bg.addColorStop(1,'#17120d');ctx.fillStyle=bg;ctx.fillRect(0,0,canvasW,canvasH);

    const phone=canvasW<620;
    const pad=phone?26:42,top=phone?78:72,groundY=canvasH-(phone?92:100);
    const fp=m.footprint;
    const leftWorld=Math.min(fp.minX,-fp.equivalentRadius*1.4,-8);
    const rightWorld=Math.max(state.hardwareDistance+8,fp.maxX+fp.equivalentRadius*1.5,18);
    const span=Math.max(20,rightWorld-leftWorld);
    const mapX=x=>pad+(x-leftWorld)/(span)*(canvasW-pad*2);
    const maxHeight=Math.max(42,state.altitude*1.18);
    const mapY=z=>groundY-(z/maxHeight)*(groundY-top);
    const apexX=mapX(0),apexY=mapY(state.altitude),surfaceY=groundY;

    ctx.fillStyle='#4f4538';ctx.fillRect(0,surfaceY,canvasW,canvasH-surfaceY);
    ctx.fillStyle='rgba(214,181,135,.13)';
    for(let x=0;x<canvasW;x+=8){const y=surfaceY+2+((x*17)%11);ctx.fillRect(x,y,1.2,1.2);}
    line(pad,surfaceY,canvasW-pad,surfaceY,'rgba(222,201,172,.34)',1);

    const theta=rad(state.cant),alpha=rad(state.spread);
    const leftAngle=theta-alpha,rightAngle=theta+alpha;
    const xL=state.altitude*Math.tan(leftAngle),xR=state.altitude*Math.tan(rightAngle),axisX=state.altitude*Math.tan(theta);
    const plumeGrad=ctx.createLinearGradient(apexX,apexY,mapX(axisX),surfaceY);plumeGrad.addColorStop(0,'rgba(146,202,229,.18)');plumeGrad.addColorStop(1,'rgba(222,173,104,.09)');
    ctx.fillStyle=plumeGrad;ctx.beginPath();ctx.moveTo(apexX,apexY);ctx.lineTo(mapX(xL),surfaceY);ctx.lineTo(mapX(xR),surfaceY);ctx.closePath();ctx.fill();
    line(apexX,apexY,mapX(xL),surfaceY,'rgba(221,173,104,.72)',1.4,[6,5]);
    line(apexX,apexY,mapX(xR),surfaceY,'rgba(221,173,104,.72)',1.4,[6,5]);
    line(apexX,apexY,mapX(axisX),surfaceY,'rgba(131,196,233,.82)',1.4,[4,4]);

    const fpStart=mapX(fp.minX),fpEnd=mapX(fp.maxX);
    ctx.fillStyle='rgba(218,133,97,.22)';ctx.fillRect(fpStart,surfaceY-5,Math.max(2,fpEnd-fpStart),10);
    line(fpStart,surfaceY-10,fpEnd,surfaceY-10,'rgba(218,133,97,.85)',2);
    label('IDEALIZED FOOTPRINT',clamp((fpStart+fpEnd)/2,80,canvasW-80),surfaceY+24,'center','rgba(231,167,132,.9)',phone?9:10);

    const vehicleScale=phone?.8:1;
    ctx.save();ctx.translate(apexX,apexY-20*vehicleScale);ctx.scale(vehicleScale,vehicleScale);
    ctx.fillStyle='#d8d4ca';ctx.fillRect(-34,-18,68,28);ctx.fillStyle='#777e80';ctx.fillRect(-20,10,40,9);ctx.strokeStyle='#9aa1a1';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(-25,8);ctx.lineTo(-43,29);ctx.moveTo(25,8);ctx.lineTo(43,29);ctx.stroke();
    const spacing=state.engines===1?0:state.engines===2?14:10;for(let i=0;i<state.engines;i++){const ex=(i-(state.engines-1)/2)*spacing;ctx.fillStyle='#4c5558';ctx.fillRect(ex-3,19,6,7);}
    ctx.restore();

    const hwX=mapX(state.hardwareDistance),hwW=phone?24:30,hwH=phone?42:50;
    ctx.strokeStyle=m.hardwareLevel==='direct'?'#e27861':m.hardwareLevel==='near'?'#e1ad66':'#77b7d8';ctx.lineWidth=1.5;ctx.strokeRect(hwX-hwW/2,surfaceY-hwH,hwW,hwH);line(hwX-hwW*.72,surfaceY-hwH,hwX+hwW*.72,surfaceY-hwH,'rgba(255,255,255,.35)',1);label('NEARBY HARDWARE',clamp(hwX,75,canvasW-75),surfaceY-hwH-15,'center','rgba(205,216,222,.78)',phone?8:10);

    const erosion=clamp(m.erosionRatio,.2,4);const moving=!reduced.matches&&!qa;
    particles.forEach((p,i)=>{
      const phase=moving?((time-startTime)*.00012*(.7+erosion*.25)+p.phase)%1:p.phase;
      const origin=fp.centroid.x+(p.seed-.5)*fp.width*.72;
      const direction=p.side*(.4+erosion*.16)*(3+fp.equivalentRadius*.5);
      const x=origin+direction*phase;
      const z=Math.sin(Math.PI*phase)*(1.4+erosion*2.2)*(0.5+p.seed*.8);
      const px=mapX(x),py=mapY(z);
      if(px>pad&&px<canvasW-pad&&py<surfaceY){ctx.fillStyle=`rgba(206,190,164,${.18+.48*(1-phase)})`;ctx.fillRect(px,py,1.2+(i%3)*.35,1.2+(i%2)*.35);}
    });
    label('CONCEPTUAL PARTICLE PATHS',clamp(mapX(fp.centroid.x),105,canvasW-105),mapY(Math.min(8,state.altitude*.42)),'center','rgba(190,177,157,.62)',phone?8:10);

    line(mapX(0),surfaceY+48,mapX(state.hardwareDistance),surfaceY+48,'rgba(255,255,255,.25)',1,[3,4]);
    label(`${state.hardwareDistance} m HARDWARE DISTANCE`,(mapX(0)+mapX(state.hardwareDistance))/2,surfaceY+63,'center','rgba(190,184,175,.62)',phone?8:10);
    label(`CANT ${state.cant}°`,pad,top-22,'left','rgba(131,196,233,.86)',phone?9:11);
    label(`SPREAD ±${state.spread}°`,pad,top-5,'left','rgba(221,173,104,.86)',phone?9:11);
    label(`ALTITUDE ${state.altitude} m`,canvasW-pad,top-22,'right','rgba(255,255,255,.68)',phone?9:11);
    label(`FOOTPRINT ${Math.round(fp.area)} m²`,canvasW-pad,top-5,'right','rgba(218,133,97,.86)',phone?9:11);
  }

  function animate(t){raf=0;if(!visible||document.hidden||reduced.matches||qa)return;draw(t);raf=requestAnimationFrame(animate);}
  function ensureAnimation(){if(visible&&!document.hidden&&!reduced.matches&&!qa&&!raf)raf=requestAnimationFrame(animate);}
  function stopAnimation(){if(raf){cancelAnimationFrame(raf);raf=0;}}

  Object.entries(controls).forEach(([key,input])=>input?.addEventListener('input',e=>{state[key]=Number(e.target.value);syncUI();}));
  $$('#engine-count button').forEach(b=>b.addEventListener('click',()=>{state.engines=Number(b.dataset.engines);syncUI();}));
  $$('#regolith-select button').forEach(b=>b.addEventListener('click',()=>{state.regolith=b.dataset.regolith;syncUI();}));
  $('#psi-reset')?.addEventListener('click',()=>{Object.assign(state,DEFAULTS);Object.entries(controls).forEach(([key,input])=>{input.value=state[key];});syncUI();});

  const header=$('.x-header'),menu=$('.x-menu'),nav=$('.x-nav');
  if(header) addEventListener('scroll',()=>header.classList.toggle('scrolled',scrollY>18),{passive:true});
  if(menu&&nav){menu.addEventListener('click',()=>{const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));});$$('a',nav).forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');menu.setAttribute('aria-expanded','false');}));}

  const ro='ResizeObserver'in window?new ResizeObserver(resize):null;ro?.observe(canvas);addEventListener('resize',resize,{passive:true});
  if('IntersectionObserver'in window){new IntersectionObserver(entries=>{visible=entries[0]?.isIntersecting!==false;if(visible){draw(performance.now());ensureAnimation();}else stopAnimation();},{threshold:.02}).observe(canvas);}
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAnimation();else{draw(performance.now());ensureAnimation();}});
  reduced.addEventListener?.('change',()=>{if(reduced.matches)stopAnimation();else ensureAnimation();draw(performance.now());});

  if(qa){
    window.__A2_PSI_TEST__=Object.freeze({
      defaults:{...DEFAULTS},
      set(patch){Object.assign(state,patch);Object.entries(controls).forEach(([key,input])=>{if(key in patch)input.value=state[key];});return snapshot();},
      reset(){Object.assign(state,DEFAULTS);Object.entries(controls).forEach(([key,input])=>{input.value=state[key];});return snapshot();},
      snapshot(){return snapshot();},
      compute(input){return serializable(model({...state,...input}));}
    });
  }
  const serializable=PSI.serializable;
  function snapshot(){const m=syncUI();return {...state,...serializable(m),canvasWidth:canvas.width,canvasHeight:canvas.height,bodyScrollWidth:document.body.scrollWidth,viewportWidth:innerWidth};}

  resize();syncUI();ensureAnimation();
})();
