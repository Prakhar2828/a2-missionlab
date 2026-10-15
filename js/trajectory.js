(() => {
  'use strict';

  const root=document.querySelector('#trajectory-lab');
  if(!root) return;
  if(!window.A2TrajectoryModel) throw new Error('Trajectory model runtime must load before trajectory experience.');
  if(!window.A2) throw new Error('A2 MissionLab core runtime must load before trajectory experience.');

  const model=window.A2TrajectoryModel;
  const {$,$$,clamp,fitCanvas,drawEarth,drawCanvasLabel}=window.A2;
  const byId=Object.fromEntries(model.MANEUVERS.map(item=>[item.id,item]));
  const returnPresets=['rtc1','rtc2','rtc3'].map(id=>byId[id]);
  let selected=byId.rtc2;
  let dv=selected.reportedDvFtS;
  let coast=selected.coastHours;
  let direction='tangential';
  let result=model.compute({dvFtS:dv,coastHours:coast,direction});
  let frame=0;

  const canvas=$('#trajectory-canvas');
  const dvInput=$('#trajectory-dv');
  const coastInput=$('#trajectory-coast');

  function fmtSigned(value,digits=0,unit=''){
    if(value===null||!Number.isFinite(value)) return 'n/a';
    const threshold=Math.pow(10,-digits)/2;
    const v=Math.abs(value)<threshold?0:value;
    const sign=v>0?'+':v<0?'−':'';
    return `${sign}${Math.abs(v).toFixed(digits)}${unit}`;
  }

  function fmtDistance(km){
    const a=Math.abs(km);
    if(a<1) return `${Math.round(a*1000)} m`;
    if(a<10) return `${a.toFixed(1)} km`;
    return `${Math.round(a)} km`;
  }

  function fmtDuration(seconds){
    if(seconds===null) return 'not executed';
    return `${Number.isInteger(seconds)?seconds:seconds.toFixed(1)} s`;
  }

  function publicDvText(item){
    if(item.status==='CANCELLED'){
      if(item.plannedDvFtS!==null) return `planned ${item.plannedDvFtS.toFixed(1)} ft/s · no burn`;
      return 'no executed Δv';
    }
    if(item.reportedDvFtS===null) return 'not public in source set';
    return `${item.reportedDvFtS.toFixed(1)} ft/s`;
  }

  function buildRecord(){
    const host=$('#trajectory-record-grid');
    host.innerHTML=model.MANEUVERS.map(item=>{
      const detail=item.status==='CANCELLED'
        ?(item.plannedDvFtS!==null?`planned ${item.plannedDvFtS.toFixed(1)} ft/s · ~${item.plannedDurationSeconds.toFixed(0)} s planned`:'no executed burn')
        :(item.reportedDvFtS===null?`${fmtDuration(item.durationSeconds)} · |Δv| not public`:`${item.reportedDvFtS.toFixed(1)} ft/s · ${fmtDuration(item.durationSeconds)}`);
      return `<article class="trajectory-record-card" data-status="${item.status}"><span>${item.leg.toUpperCase()}</span><b>${item.label} · ${item.status}</b><small>${detail}</small></article>`;
    }).join('');
  }

  function buildPresets(){
    const host=$('#trajectory-presets');
    host.innerHTML=returnPresets.map(item=>`<button type="button" data-preset="${item.id}"><b>${item.label}</b><small>${item.coastHours.toFixed(item.coastHours%1?1:0)} h to EI</small></button>`).join('');
    $$('button',host).forEach(button=>button.addEventListener('click',()=>selectPreset(button.dataset.preset)));
  }

  function selectPreset(id){
    selected=byId[id];
    dv=selected.reportedDvFtS||0;
    coast=selected.coastHours;
    dvInput.value=String(dv);
    coastInput.value=String(coast);
    update();
  }

  function isMissionAnchored(){
    return selected.reportedDvFtS!==null && Math.abs(dv-selected.reportedDvFtS)<.001 && Math.abs(coast-selected.coastHours)<.01;
  }

  function updateRecordReadout(){
    $('#trajectory-record-name').textContent=`${selected.label} · ${selected.status}`;
    $('#trajectory-record-time').textContent=selected.timeLabel;
    $('#trajectory-record-duration').textContent=fmtDuration(selected.durationSeconds);
    $('#trajectory-record-dv').textContent=publicDvText(selected);
    $$('#trajectory-presets button').forEach(button=>{const active=button.dataset.preset===selected.id;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
  }

  function updateControls(){
    $('#trajectory-dv-value').textContent=`${dv.toFixed(1)} ft/s`;
    const coastDigits=Math.abs(coast-Math.round(coast))<1e-9?0:1;
    $('#trajectory-coast-value').textContent=`${coast.toFixed(coastDigits)} h`;
    $$('#trajectory-directions button').forEach(button=>{const active=button.dataset.direction===direction;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});

    const magMatches=selected.reportedDvFtS!==null&&Math.abs(dv-selected.reportedDvFtS)<.001;
    const timeMatches=Math.abs(coast-selected.coastHours)<.01;
    $('#trajectory-dv-note').textContent=magMatches
      ?`Matches the NASA-reported ${selected.label} scalar magnitude. Direction remains modeled.`
      :`Modeled what-if magnitude. NASA reported ${selected.label} at ${selected.reportedDvFtS.toFixed(1)} ft/s.`;
    $('#trajectory-coast-note').textContent=timeMatches
      ?`${selected.label} occurred ${selected.coastHours.toFixed(selected.coastHours%1?1:0)} hours before the public Entry Interface minute.`
      :`Modeled what-if timing. ${selected.label} occurred ${selected.coastHours.toFixed(selected.coastHours%1?1:0)} hours before the public Entry Interface minute.`;

    const anchored=isMissionAnchored();
    $('#trajectory-case-label').textContent=anchored?'MISSION-ANCHORED MODEL':'MODELED WHAT-IF';
    $('#trajectory-case-note').textContent=anchored
      ?`Magnitude and timing match public ${selected.label} reporting. Direction and all propagated consequences remain MissionLab modeled.`
      :`At least one input differs from the public ${selected.label} record. This is an educational sensitivity case, not a reconstruction of the flown targeting solution.`;
  }

  function updateOutputs(){
    $('#trajectory-separation').textContent=fmtDistance(result.separationKm);
    $('#trajectory-periapsis').textContent=result.periapsisShiftKm===null?'n/a':fmtSigned(result.periapsisShiftKm,result.periapsisShiftKm<10?1:0,' km');
    $('#trajectory-arrival').textContent=result.arrivalShiftSeconds===null?'n/a':fmtSigned(result.arrivalShiftSeconds,Math.abs(result.arrivalShiftSeconds)<10?1:0,' s');
    $('#trajectory-rtn').textContent=`R ${fmtSigned(result.sepR,0)} · T ${fmtSigned(result.sepT,0)} · N ${fmtSigned(result.sepN,0)} km`;
    $('#trajectory-linear-compare').textContent=`Linear drift: ${fmtDistance(result.linearKm)} · two-body: ${fmtDistance(result.separationKm)}`;
    root.dataset.selected=selected.id;
    root.dataset.direction=direction;
    root.dataset.anchored=String(isMissionAnchored());
    root.dataset.finite=String(result.finite);
    root.dataset.separationKm=String(result.separationKm);
    root.dataset.sepR=String(result.sepR);
    root.dataset.sepT=String(result.sepT);
    root.dataset.sepN=String(result.sepN);
    root.dataset.periapsisShiftKm=String(result.periapsisShiftKm ?? '');
    root.dataset.arrivalShiftSeconds=String(result.arrivalShiftSeconds ?? '');
    root.dataset.linearKm=String(result.linearKm);
  }

  function update(){
    result=model.compute({dvFtS:dv,coastHours:coast,direction});
    updateRecordReadout();
    updateControls();
    updateOutputs();
    scheduleDraw();
  }

  function projectFactory(rect,paths){
    const points=[];
    paths.forEach(path=>path.forEach(sample=>points.push(sample.position)));
    points.push([-model.EARTH_RADIUS_KM,-model.EARTH_RADIUS_KM,0],[model.EARTH_RADIUS_KM,model.EARTH_RADIUS_KM,0]);
    let minX=Math.min(...points.map(p=>p[0])),maxX=Math.max(...points.map(p=>p[0]));
    let minY=Math.min(...points.map(p=>p[1])),maxY=Math.max(...points.map(p=>p[1]));
    const spanX=Math.max(1,maxX-minX),spanY=Math.max(1,maxY-minY);
    const padX=spanX*.06,padY=spanY*.10;
    minX-=padX;maxX+=padX;minY-=padY;maxY+=padY;
    const scale=Math.min(rect.w/(maxX-minX),rect.h/(maxY-minY));
    const cx=(minX+maxX)/2,cy=(minY+maxY)/2;
    return p=>({x:rect.x+rect.w/2+(p[0]-cx)*scale,y:rect.y+rect.h/2-(p[1]-cy)*scale,scale});
  }

  function drawPath(ctx,path,project,stroke,width,dash=[]){
    if(!path.length) return;
    ctx.save();ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.setLineDash(dash);ctx.beginPath();
    path.forEach((sample,index)=>{const p=project(sample.position);if(index)ctx.lineTo(p.x,p.y);else ctx.moveTo(p.x,p.y);});
    ctx.stroke();ctx.restore();
  }

  function drawArrow(ctx,x1,y1,x2,y2,color){
    const angle=Math.atan2(y2-y1,x2-x1),head=8;
    ctx.save();ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=2.2;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();ctx.beginPath();ctx.moveTo(x2,y2);ctx.lineTo(x2-head*Math.cos(angle-Math.PI/6),y2-head*Math.sin(angle-Math.PI/6));ctx.lineTo(x2-head*Math.cos(angle+Math.PI/6),y2-head*Math.sin(angle+Math.PI/6));ctx.closePath();ctx.fill();ctx.restore();
  }

  function drawArrivalInset(ctx,rect,layout){
    const pad=layout.phone?12:16;
    ctx.save();ctx.fillStyle='rgba(3,10,16,.90)';ctx.strokeStyle='rgba(255,255,255,.11)';ctx.lineWidth=1;ctx.fillRect(rect.x,rect.y,rect.w,rect.h);ctx.strokeRect(rect.x+.5,rect.y+.5,rect.w-1,rect.h-1);
    ctx.fillStyle='rgba(138,166,184,.78)';ctx.font=`${layout.phone?9:10}px ui-monospace,Consolas,monospace`;ctx.fillText('MAGNIFIED EI-EPOCH SEPARATION · RT PLANE',rect.x+pad,rect.y+pad+2);
    const plot={x:rect.x+pad,y:rect.y+pad+18,w:rect.w-pad*2,h:rect.h-pad*2-28};
    const maxVal=Math.max(1,Math.abs(result.sepR),Math.abs(result.sepT))*1.25;
    const sx=plot.w/(2*maxVal),sy=plot.h/(2*maxVal),cx=plot.x+plot.w/2,cy=plot.y+plot.h/2;
    ctx.strokeStyle='rgba(126,151,169,.24)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(plot.x,cy);ctx.lineTo(plot.x+plot.w,cy);ctx.moveTo(cx,plot.y);ctx.lineTo(cx,plot.y+plot.h);ctx.stroke();
    ctx.fillStyle='rgba(126,151,169,.7)';ctx.font=`${layout.phone?9:10}px ui-monospace,Consolas,monospace`;ctx.fillText('T',plot.x+plot.w-9,cy-5);ctx.fillText('R',cx+5,plot.y+10);
    ctx.fillStyle='#75b9e7';ctx.beginPath();ctx.arc(cx,cy,4,0,Math.PI*2);ctx.fill();
    const x=cx+result.sepT*sx,y=cy-result.sepR*sy;
    ctx.strokeStyle='rgba(240,196,118,.65)';ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(x,y);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle='#83d3ad';ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='rgba(223,235,242,.85)';ctx.font=`${layout.phone?9:10}px ui-monospace,Consolas,monospace`;ctx.fillText(`N ${fmtSigned(result.sepN,1,' km')}`,plot.x,plot.y+plot.h+15);
    ctx.fillText(`|Δr| ${fmtDistance(result.separationKm)}`,plot.x+plot.w-110,plot.y+plot.h+15);
    ctx.restore();
  }

  function draw(){
    frame=0;
    if(!canvas||!result) return;
    const {ctx,w,h,layout}=fitCanvas(canvas);
    ctx.clearRect(0,0,w,h);
    const bg=ctx.createLinearGradient(0,0,w,h);bg.addColorStop(0,'#02070c');bg.addColorStop(.55,'#07131d');bg.addColorStop(1,'#02070b');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);

    const margin=layout.phone?12:20;
    const insetH=layout.phone?Math.min(150,h*.34):Math.min(190,h*.32);
    const mainRect={x:margin,y:42,w:w-margin*2,h:h-insetH-72};
    const insetRect={x:layout.phone?margin:w-Math.min(360,w*.42)-margin,y:h-insetH-margin,w:layout.phone?w-margin*2:Math.min(360,w*.42),h:insetH};
    const project=projectFactory(mainRect,[result.nominal.path,result.corrected.path]);

    const earth=project([0,0,0]);
    const earthRadius=Math.max(3,model.EARTH_RADIUS_KM*earth.scale);
    drawEarth(ctx,earth.x,earth.y,earthRadius);
    ctx.strokeStyle='rgba(110,185,225,.24)';ctx.lineWidth=1;ctx.beginPath();ctx.arc(earth.x,earth.y,model.ENTRY_RADIUS_KM*earth.scale,0,Math.PI*2);ctx.stroke();

    drawPath(ctx,result.nominal.path,project,'rgba(117,185,231,.72)',2);
    drawPath(ctx,result.corrected.path,project,'rgba(131,211,173,.92)',2.2);

    const burn=project(result.nominalStart.position);
    ctx.fillStyle='#f4f7f9';ctx.beginPath();ctx.arc(burn.x,burn.y,4.2,0,Math.PI*2);ctx.fill();
    const dir=model.DIRECTIONS[direction];
    if(Math.abs(dir.n)>0){
      ctx.strokeStyle='#f0c476';ctx.lineWidth=2;ctx.beginPath();ctx.arc(burn.x,burn.y,10,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#f0c476';ctx.beginPath();ctx.arc(burn.x,burn.y,2.3,0,Math.PI*2);ctx.fill();
    }else{
      const dvxy=[result.dv[0],result.dv[1]],m=Math.hypot(...dvxy)||1,ux=dvxy[0]/m,uy=dvxy[1]/m;
      drawArrow(ctx,burn.x,burn.y,burn.x+ux*42,burn.y-uy*42,'#f0c476');
    }

    const endNom=project(result.nominal.state.position),endCor=project(result.corrected.state.position);
    ctx.fillStyle='#75b9e7';ctx.beginPath();ctx.arc(endNom.x,endNom.y,3.5,0,Math.PI*2);ctx.fill();ctx.fillStyle='#83d3ad';ctx.beginPath();ctx.arc(endCor.x,endCor.y,3.5,0,Math.PI*2);ctx.fill();

    drawCanvasLabel(ctx,`${selected.label} MODEL START`,burn.x+10,burn.y-12,Math.max(90,mainRect.x+mainRect.w-burn.x-14),{size:layout.phone?9:10,minSize:9,color:'rgba(240,196,118,.88)',maxLines:1});
    drawCanvasLabel(ctx,'EARTH',earth.x+earthRadius+6,earth.y+4,80,{size:layout.phone?9:10,minSize:9,color:'rgba(210,230,242,.72)',maxLines:1});
    if(!layout.phone) drawCanvasLabel(ctx,'REFERENCE + CORRECTED TWO-BODY RETURN',mainRect.x+8,mainRect.y+12,mainRect.w*.62,{size:10,minSize:9,color:'rgba(151,176,191,.68)',maxLines:1});

    drawArrivalInset(ctx,insetRect,layout);
  }

  function scheduleDraw(){
    if(frame) cancelAnimationFrame(frame);
    frame=requestAnimationFrame(draw);
  }

  buildRecord();
  buildPresets();
  $$('#trajectory-directions button').forEach(button=>button.addEventListener('click',()=>{direction=button.dataset.direction;update();}));
  dvInput.addEventListener('input',event=>{dv=Number(event.target.value);update();});
  coastInput.addEventListener('input',event=>{coast=Number(event.target.value);update();});
  $('#trajectory-reset').addEventListener('click',()=>selectPreset(selected.id));
  window.addEventListener('resize',scheduleDraw,{passive:true});
  window.addEventListener('orientationchange',scheduleDraw,{passive:true});
  window.addEventListener('a2:celestialchange',scheduleDraw);
  if('ResizeObserver' in window) new ResizeObserver(scheduleDraw).observe(canvas.parentElement);
  update();
})();
