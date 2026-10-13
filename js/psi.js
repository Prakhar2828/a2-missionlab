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

  // PSI campaign-context educational model. Artemis II did not land.
  if ($('#psi-lab-section')) {
  const psiCanvas=$('#psi-canvas');let psiAlt=18,psiThrottle=55,psiAngle=12,psiCant=4,psiEngines=2,psiRegolith='baseline';const particles=Array.from({length:240},(_,i)=>({seed:i*.61803398875%1}));
  const regMult=()=>psiRegolith==='loose'?1.35:psiRegolith==='cohesive'?.7:1;
  function renderPsi(){const $id=id=>$('#'+id);$id('psi-alt-value').textContent=`${psiAlt} m`;$id('psi-throttle-value').textContent=`${psiThrottle}%`;$id('psi-angle-value').textContent=`${psiAngle}°`;$id('psi-cant-value').textContent=`${psiCant}°`;const score=psiThrottle*psiEngines*regMult()/(psiAlt*1.5)*(1+psiAngle/45),risk=score>10?'Broad / energetic conceptual ejecta zone':score>4.5?'Moderate conceptual ejecta footprint':'Lower conceptual ejecta footprint';$id('psi-risk').textContent=risk;$id('psi-hardware-risk').textContent=score>10?'Nearby hardware · higher conceptual exposure':score>4.5?'Nearby hardware · watch exposure':'Nearby hardware · lower conceptual exposure';$$('#engine-count button').forEach(b=>b.classList.toggle('active',Number(b.dataset.engines)===psiEngines));$$('#regolith-select button').forEach(b=>b.classList.toggle('active',b.dataset.regolith===psiRegolith));}
  $('#psi-alt')?.addEventListener('input',e=>{psiAlt=Number(e.target.value);renderPsi();});$('#psi-throttle')?.addEventListener('input',e=>{psiThrottle=Number(e.target.value);renderPsi();});$('#psi-angle')?.addEventListener('input',e=>{psiAngle=Number(e.target.value);renderPsi();});$('#psi-cant')?.addEventListener('input',e=>{psiCant=Number(e.target.value);renderPsi();});$$('#engine-count button').forEach(b=>b.addEventListener('click',()=>{psiEngines=Number(b.dataset.engines);renderPsi();}));$$('#regolith-select button').forEach(b=>b.addEventListener('click',()=>{psiRegolith=b.dataset.regolith;renderPsi();}));renderPsi();
  if(psiCanvas){const loop=t=>{const {ctx,w,h,layout}=fitCanvas(psiCanvas),scene=sceneRect(w,h,{},layout.phone?10:16);ctx.clearRect(0,0,w,h);ctx.fillStyle='#020406';ctx.fillRect(0,0,w,h);drawStars(ctx,w,h,layout.compact?45:65,57,.55);const ground=scene.y+scene.height*.78;ctx.fillStyle='#77756f';ctx.beginPath();ctx.moveTo(scene.x,ground);for(let x=scene.x;x<=scene.right;x+=15)ctx.lineTo(x,ground+Math.sin(x*.07)*4+Math.sin(x*.018)*7);ctx.lineTo(scene.right,scene.bottom);ctx.lineTo(scene.x,scene.bottom);ctx.closePath();ctx.fill();const ly=lerp(scene.y+scene.height*.24,scene.y+scene.height*.58,(40-psiAlt)/36),lx=scene.x+scene.width*.48,lander=clamp(scene.min/360,.72,1.18);ctx.save();ctx.translate(lx,ly);ctx.scale(lander,lander);ctx.fillStyle='#cfd5d8';ctx.fillRect(-42,-20,84,28);ctx.fillStyle='#8fa1aa';ctx.fillRect(-23,8,46,8);ctx.strokeStyle='#9ba7ad';ctx.lineWidth=3/lander;ctx.beginPath();ctx.moveTo(-28,7);ctx.lineTo(-47,31);ctx.moveTo(28,7);ctx.lineTo(47,31);ctx.stroke();ctx.restore();const spread=(24+psiThrottle*.55+psiAngle*2.6)*regMult()*lander,engineSpacing=16*lander,cant=psiCant*Math.PI/180;for(let e=0;e<psiEngines;e++){const ex=lx+(e-(psiEngines-1)/2)*engineSpacing,side=e<(psiEngines/2)?-1:1,dir=side*cant,center=ex+Math.sin(dir)*(ground-ly);ctx.fillStyle='rgba(170,214,234,.22)';ctx.beginPath();ctx.moveTo(ex-6*lander,ly+18*lander);ctx.lineTo(center-spread*.48,ground);ctx.lineTo(center+spread*.48,ground);ctx.lineTo(ex+6*lander,ly+18*lander);ctx.closePath();ctx.fill();ctx.strokeStyle='rgba(197,229,245,.55)';ctx.setLineDash([3,5]);ctx.beginPath();ctx.moveTo(ex,ly+18*lander);ctx.lineTo(center,ground);ctx.stroke();ctx.setLineDash([]);}
      const activity=psiThrottle/100*(25/psiAlt)*psiEngines*regMult()*(1+psiAngle/35),drift=Math.sin(cant)*(ground-ly);particles.forEach((pp,i)=>{const ph=((t*.00016*(.7+activity)+pp.seed)%1),side=i%2?1:-1,px=lx+drift*.55+side*(ph*(45+activity*scene.width*.42)),py=ground-4-Math.sin(ph*Math.PI)*(14+activity*scene.height*.22);if(px>scene.x&&px<scene.right){ctx.fillStyle=`rgba(202,194,174,${.18+.55*(1-ph)})`;ctx.fillRect(px,py,1.3+(i%3)*.5,1.3+(i%2)*.4);}});const hz=Math.min(scene.width*.44,spread*(1.05+activity*.58)),hc=clamp(lx+drift*.55,scene.x+hz,scene.right-hz);ctx.strokeStyle='rgba(255,112,82,.65)';ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(hc-hz,ground+8);ctx.lineTo(hc+hz,ground+8);ctx.stroke();ctx.setLineDash([]);drawCanvasLabel(ctx,'CONCEPTUAL HAZARD / EJECTA ZONE',hc,ground+25,Math.min(scene.width*.78,hz*2),{size:layout.phone?9.8:11,minSize:9.5,align:'center',color:'rgba(255,130,96,.9)',maxLines:2});const hardwareW=clamp(scene.width*.10,34,48),hardwareX=scene.right-hardwareW-10;ctx.strokeStyle='rgba(127,197,255,.55)';ctx.strokeRect(hardwareX,ground-35,hardwareW,30);drawCanvasLabel(ctx,'NEARBY HARDWARE',scene.right-4,ground-43,scene.width*.45,{size:layout.phone?9.8:11,minSize:9.5,align:'right',color:'rgba(127,197,255,.78)',maxLines:2});drawCanvasLabel(ctx,`CANT ${psiCant}° · SPREAD ${psiAngle}°`,scene.x+4,scene.y+18,scene.width*.7,{size:layout.phone?9.8:11,minSize:9.5,color:'rgba(255,255,255,.58)',maxLines:1});requestAnimationFrame(loop);};requestAnimationFrame(loop);}

  }


})();
