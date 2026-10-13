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

  // GNC proximity-operations teaching model. Real context; simplified dynamics.
  if ($('#gnc-lab')) {
  const gncCanvas=$('#gnc-canvas');
  const gnc={x:82,y:-58,yaw:12,pitch:-7,vx:0,vy:0,vyaw:0,vpitch:0,lastFire:0,started:false,mode:'auto',disturbed:false};
  const sensors=['IMU','Star tracker','Optical / docking camera context','Onboard navigation state','RCS effectors','DSN tracking · external'];
  const sensorBox=$('#sensor-chips');if(sensorBox)sensorBox.innerHTML=sensors.map((x,i)=>`<span class="sensor-chip ${i===5?'external':''}">${x}</span>`).join('');
  const gncBlocks={sense:'Sensors observe motion and references. NASA reported onboard navigation sensors during proximity operations; DSN is external ground support, not an onboard sensor.',estimate:'Navigation fuses measurements into an estimated state: where Orion is, how it is moving, and how it is pointed. MissionLab does not claim access to Orion’s private navigation-filter state.',guide:'Guidance defines the desired condition — here, a target corridor around the ICPS reference. The target box is educational, not a recovered flown gate.',control:'Control turns state error into a correction request. AUTO MODE demonstrates that closed-loop idea; the proprietary Orion control law, gains, and allocation logic are not public.',fire:'Effectors create force and torque. NASA reported reaction-control-thruster use during proximity operations, but individual thruster firing history is not public.',verify:'The vehicle moves, sensors observe the result, and the loop repeats. A disturbance matters because every correction must be verified against the new state.'};
  function setGncBlock(k){$$('[data-gnc-block]').forEach(b=>b.classList.toggle('active',b.dataset.gncBlock===k));const e=$('#gnc-block-explainer');if(e)e.textContent=gncBlocks[k];}
  $$('[data-gnc-block]').forEach(b=>b.addEventListener('click',()=>setGncBlock(b.dataset.gncBlock)));setGncBlock('sense');
  function resetGnc(){Object.assign(gnc,{x:82,y:-58,yaw:12,pitch:-7,vx:0,vy:0,vyaw:0,vpitch:0,lastFire:0,disturbed:false});const st=$('#gnc-autopilot-status');if(st)st.textContent=gnc.started?(gnc.mode==='auto'?'ACQUIRING TARGET':'MANUAL CONTROL'):'READY';}
  function setGncMode(mode){
    gnc.mode=mode;
    $$('[data-gnc-mode]').forEach(b=>b.classList.toggle('active',b.dataset.gncMode===mode));
    const controls=$('#gnc-controls');if(controls)controls.classList.toggle('auto-locked',mode==='auto');
    const read=$('#gnc-mode-readout');if(read)read.textContent=mode==='auto'?'AUTO GUIDANCE DEMO':'CREW MANUAL';
    const title=$('#gnc-mode-title'),help=$('#gnc-mode-help'),startBtn=$('#gnc-start');
    if(title)title.textContent=mode==='auto'?'AUTO MODE · watch the closed loop work':'MANUAL MODE · you fly the capture';
    if(help)help.textContent=mode==='auto'?'The demo continuously senses error, estimates the state, guides toward the target, commands a correction, fires conceptual RCS, and verifies the result.':'Use THC to translate and RHC to rotate. Capture the corridor while keeping motion small. Introduce a disturbance at any time to see why closed-loop correction matters.';
    if(startBtn&&!gnc.started)startBtn.textContent=mode==='auto'?'Start auto demonstration':'Start manual approach';
    const st=$('#gnc-autopilot-status');if(st&&gnc.started)st.textContent=mode==='auto'?'ACQUIRING TARGET':'MANUAL CONTROL';
    setGncBlock(mode==='auto'?'sense':'control');
  }
  $$('[data-gnc-mode]').forEach(b=>b.addEventListener('click',()=>setGncMode(b.dataset.gncMode)));
  function gncCommand(cmd){if(!gnc.started||gnc.mode!=='manual')return;const impulse=.34,rot=.075;if(cmd==='up')gnc.vy-=impulse;if(cmd==='down')gnc.vy+=impulse;if(cmd==='left')gnc.vx-=impulse;if(cmd==='right')gnc.vx+=impulse;if(cmd==='pitchUp')gnc.vpitch-=rot;if(cmd==='pitchDown')gnc.vpitch+=rot;if(cmd==='yawLeft')gnc.vyaw-=rot;if(cmd==='yawRight')gnc.vyaw+=rot;if(cmd==='attCenter'){gnc.vyaw=0;gnc.vpitch=0;}if(cmd==='transCenter'){gnc.vx=0;gnc.vy=0;}gnc.lastFire=1;setGncBlock('fire');setTimeout(()=>setGncBlock('verify'),180);}
  $$('.pad button').forEach(b=>b.addEventListener('click',()=>gncCommand(b.dataset.cmd)));
  $('#gnc-start')?.addEventListener('click',()=>{gnc.started=true;$('#gnc-tutorial').hidden=true;$('#gnc-controls').hidden=false;setGncMode(gnc.mode);});
  $('#gnc-reset')?.addEventListener('click',()=>{resetGnc();setGncBlock('sense');});
  $('#gnc-disturbance')?.addEventListener('click',()=>{if(!gnc.started){gnc.started=true;$('#gnc-tutorial').hidden=true;$('#gnc-controls').hidden=false;}const sx=Math.random()<.5?-1:1,sy=Math.random()<.5?-1:1;gnc.vx+=sx*(.38+Math.random()*.22);gnc.vy+=sy*(.28+Math.random()*.18);gnc.vyaw+=sx*(.10+Math.random()*.05);gnc.vpitch+=sy*(.08+Math.random()*.04);gnc.x=clamp(gnc.x+sx*(12+Math.random()*10),-150,150);gnc.y=clamp(gnc.y+sy*(8+Math.random()*9),-105,105);gnc.lastFire=1;gnc.disturbed=true;const st=$('#gnc-autopilot-status');if(st)st.textContent=gnc.mode==='auto'?'DISTURBANCE · RECOVERING':'DISTURBANCE · YOUR MOVE';setGncBlock('sense');});
  setGncMode('auto');
  if(gncCanvas){let last=performance.now();const loop=t=>{const dt=Math.min(.04,(t-last)/1000);last=t;
      if(gnc.started&&gnc.mode==='auto'){
        const targetVx=clamp(-gnc.x*.0031,-.24,.24),targetVy=clamp(-gnc.y*.0031,-.24,.24),targetYaw=clamp(-gnc.yaw*.006,-.075,.075),targetPitch=clamp(-gnc.pitch*.006,-.075,.075);
        const blend=Math.min(1,dt*1.55);gnc.vx+=(targetVx-gnc.vx)*blend;gnc.vy+=(targetVy-gnc.vy)*blend;gnc.vyaw+=(targetYaw-gnc.vyaw)*blend;gnc.vpitch+=(targetPitch-gnc.vpitch)*blend;
        if(Math.hypot(gnc.x,gnc.y)>18||Math.hypot(gnc.yaw,gnc.pitch)>3){gnc.lastFire=Math.max(gnc.lastFire,.38);const cycle=Math.floor(t/650)%6;setGncBlock(['sense','estimate','guide','control','fire','verify'][cycle]);}
      }
      gnc.x+=gnc.vx*60*dt;gnc.y+=gnc.vy*60*dt;gnc.yaw+=gnc.vyaw*60*dt;gnc.pitch+=gnc.vpitch*60*dt;gnc.vx*=Math.pow(.955,dt*60);gnc.vy*=Math.pow(.955,dt*60);gnc.vyaw*=Math.pow(.94,dt*60);gnc.vpitch*=Math.pow(.94,dt*60);gnc.x=clamp(gnc.x,-150,150);gnc.y=clamp(gnc.y,-105,105);gnc.yaw=clamp(gnc.yaw,-35,35);gnc.pitch=clamp(gnc.pitch,-25,25);gnc.lastFire=Math.max(0,gnc.lastFire-dt*2.4);
      const {ctx,w,h,layout}=fitCanvas(gncCanvas);ctx.clearRect(0,0,w,h);ctx.fillStyle='#010408';ctx.fillRect(0,0,w,h);drawStars(ctx,w,h,layout.compact?105:160,41,.8);
      const scene=sceneRect(w,h,{top:layout.phone?18:26,bottom:layout.phone?18:72},layout.phone?14:20),scale=clamp(Math.min(scene.width/340,scene.height/250),.68,1.35),tx=scene.cx,ty=scene.y+scene.height*.47,cw=clamp(124*scale,92,160),ch=clamp(92*scale,68,118);
      ctx.save();ctx.translate(tx,ty);ctx.strokeStyle='rgba(127,197,255,.3)';ctx.setLineDash([7,7]);ctx.strokeRect(-cw/2,-ch/2,cw,ch);ctx.setLineDash([]);const iw=cw*.39,ih=ch*.33;ctx.strokeStyle='rgba(255,255,255,.88)';ctx.lineWidth=2;ctx.strokeRect(-iw/2,-ih/2,iw,ih);ctx.beginPath();ctx.moveTo(-iw*.8,0);ctx.lineTo(iw*.8,0);ctx.moveTo(0,-ih);ctx.lineTo(0,ih);ctx.stroke();ctx.restore();
      drawCanvasLabel(ctx,'ICPS TARGET',tx,ty+ch/2+17,Math.max(90,cw*1.15),{size:layout.phone?10:11,minSize:10,align:'center',color:'rgba(255,255,255,.66)',maxLines:1});
      const sx=tx+gnc.x*scale,sy=ty+gnc.y*scale,craft=clamp(scale,.76,1.25);ctx.save();ctx.translate(sx,sy);ctx.rotate(gnc.yaw*Math.PI/180);ctx.scale(craft,craft);ctx.strokeStyle='#f6fbff';ctx.lineWidth=1.6/craft;ctx.beginPath();ctx.moveTo(-22,12);ctx.lineTo(0,-24);ctx.lineTo(22,12);ctx.lineTo(8,8);ctx.lineTo(0,19);ctx.lineTo(-8,8);ctx.closePath();ctx.stroke();ctx.strokeStyle='rgba(240,196,118,.75)';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(Math.sin(gnc.pitch*Math.PI/180)*42,-42);ctx.stroke();if(gnc.lastFire>0){ctx.fillStyle=`rgba(111,231,225,${.25+.65*gnc.lastFire})`;for(const [x,y] of [[-18,10],[18,10],[-8,-7],[8,-7]]){ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+(x<0?-16:16)*gnc.lastFire,y+8);ctx.lineTo(x,y+3);ctx.fill();}}ctx.restore();ctx.strokeStyle='rgba(125,224,173,.42)';ctx.setLineDash([4,6]);ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(tx,ty);ctx.stroke();ctx.setLineDash([]);
      const offset=Math.hypot(gnc.x,gnc.y),ang=Math.hypot(gnc.yaw,gnc.pitch),success=offset<24&&ang<4&&Math.hypot(gnc.vx,gnc.vy)<.35;$('#gnc-offset-readout').textContent=`${(offset*.5).toFixed(0)} m · conceptual`;$('#gnc-error-readout').textContent=`${ang.toFixed(1)}°`;const ok=$('#gnc-success');if(ok){ok.textContent=success?'TARGET CORRIDOR CAPTURED':'CORRIDOR NOT YET CAPTURED';ok.classList.toggle('ok',success);}const st=$('#gnc-autopilot-status');if(st&&gnc.started&&success){st.textContent=gnc.mode==='auto'?'CAPTURE COMPLETE · STABLE':'CAPTURED · HOLD IT';gnc.disturbed=false;}else if(st&&gnc.started&&gnc.mode==='auto'&&!gnc.disturbed){st.textContent='ACQUIRING TARGET';}
      requestAnimationFrame(loop);};requestAnimationFrame(loop);}


  }


})();
