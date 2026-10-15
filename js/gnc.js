(() => {
'use strict';
if(!window.A2)throw new Error('A2 MissionLab core runtime must load before experience runtimes.');
const {$,$$,clamp,fitCanvas,sceneRect,drawStars,drawCanvasLabel}=window.A2;
if(!$('#gnc-lab'))return;

const QA_MODE=new URLSearchParams(location.search).get('gnc-qa')==='1';
const PHYSICS_STEP=1/120;
const MAX_FRAME_CATCHUP=2;
const AUTO={
  translationGain:.0035,translationLimit:.26,translationBlend:1.75,translationDamping:.957,
  attitudeGain:.007,attitudeLimit:.085,attitudeBlend:1.75,attitudeDamping:.943
};
const PHASES=[
  ['initial','INITIAL ERROR','sense'],['sense','SENSE','sense'],['estimate','ESTIMATE','estimate'],
  ['guide','GUIDE','guide'],['control','CONTROL','control'],['fire','FIRE','fire'],
  ['verify','VERIFY','verify'],['convergence','CONVERGENCE','verify']
];
const THRESHOLDS=[0,0,1.8,3.6,5.4,7.2,9.0];

function initialState(){return{x:82,y:-58,yaw:12,pitch:-7,vx:0,vy:0,vyaw:0,vpitch:0,lastFire:0};}
const gnc=Object.assign(initialState(),{
  started:false,mode:'auto',disturbed:false,autoElapsed:0,captureLatched:false,
  captureSeconds:null,phaseIndex:0,phaseHistory:['INITIAL ERROR']
});
const canvas=$('#gnc-canvas');

const sensors=['IMU','Star tracker','Optical / docking camera context','Onboard navigation state','RCS effectors','DSN tracking · external'];
const sensorBox=$('#sensor-chips');
if(sensorBox)sensorBox.innerHTML=sensors.map((s,i)=>`<span class="sensor-chip ${i===5?'external':''}">${s}</span>`).join('');

const explanations={
  sense:'Sensors observe motion and references. NASA reported onboard navigation sensors during proximity operations; DSN is external ground support, not an onboard sensor.',
  estimate:'Navigation fuses measurements into an estimated state. MissionLab does not claim access to Orion’s private navigation-filter state.',
  guide:'Guidance compares the desired condition with the estimated state so the remaining error is explicit. The target box is educational, not a recovered flown gate.',
  control:'Control turns that state error into a correction command. The proprietary Orion control law, gains, and allocation logic are not public.',
  fire:'Effectors create force and torque, producing the spacecraft response. Individual Artemis II thruster firing history is not public.',
  verify:'Sensors observe the changed state, close the feedback loop, and begin the next correction cycle.'
};
function setBlock(key){
  $$('[data-gnc-block]').forEach(b=>{const active=b.dataset.gncBlock===key;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
  const box=$('#gnc-block-explainer');if(box)box.textContent=explanations[key];
}
$$('[data-gnc-block]').forEach(b=>b.addEventListener('click',()=>setBlock(b.dataset.gncBlock)));

const offset=s=>Math.hypot(s.x,s.y);
const angle=s=>Math.hypot(s.yaw,s.pitch);
const speed=s=>Math.hypot(s.vx,s.vy);
const isCaptured=s=>offset(s)<24&&angle(s)<4&&speed(s)<.35;

function applyAuto(s,dt){
  const tvx=clamp(-s.x*AUTO.translationGain,-AUTO.translationLimit,AUTO.translationLimit);
  const tvy=clamp(-s.y*AUTO.translationGain,-AUTO.translationLimit,AUTO.translationLimit);
  const tyr=clamp(-s.yaw*AUTO.attitudeGain,-AUTO.attitudeLimit,AUTO.attitudeLimit);
  const tpr=clamp(-s.pitch*AUTO.attitudeGain,-AUTO.attitudeLimit,AUTO.attitudeLimit);
  const tb=Math.min(1,dt*AUTO.translationBlend),ab=Math.min(1,dt*AUTO.attitudeBlend);
  s.vx+=(tvx-s.vx)*tb;s.vy+=(tvy-s.vy)*tb;s.vyaw+=(tyr-s.vyaw)*ab;s.vpitch+=(tpr-s.vpitch)*ab;
  if(offset(s)>18||angle(s)>3)s.lastFire=Math.max(s.lastFire,.38);
}
function step(s,dt,auto){
  if(auto)applyAuto(s,dt);
  s.x+=s.vx*60*dt;s.y+=s.vy*60*dt;s.yaw+=s.vyaw*60*dt;s.pitch+=s.vpitch*60*dt;
  s.vx*=Math.pow(AUTO.translationDamping,dt*60);s.vy*=Math.pow(AUTO.translationDamping,dt*60);
  s.vyaw*=Math.pow(AUTO.attitudeDamping,dt*60);s.vpitch*=Math.pow(AUTO.attitudeDamping,dt*60);
  s.x=clamp(s.x,-150,150);s.y=clamp(s.y,-105,105);s.yaw=clamp(s.yaw,-35,35);s.pitch=clamp(s.pitch,-25,25);
  s.lastFire=Math.max(0,s.lastFire-dt*2.4);
}
function integrateElapsed(s,elapsed,auto){
  let remaining=Math.min(MAX_FRAME_CATCHUP,Math.max(0,Number(elapsed)||0));
  const integrated=remaining;let guard=0;
  while(remaining>1e-9&&guard<300){const dt=Math.min(PHYSICS_STEP,remaining);step(s,dt,auto);remaining-=dt;guard++;}
  return integrated;
}

function setPhase(index,record=true){
  const safe=clamp(Math.round(Number(index)||0),0,PHASES.length-1);
  gnc.phaseIndex=safe;const phase=PHASES[safe];
  $$('#gnc-progress [data-gnc-phase]').forEach((item,i)=>{
    item.classList.toggle('active',i===safe);item.classList.toggle('complete',i<safe);
    if(i===safe)item.setAttribute('aria-current','step');else item.removeAttribute('aria-current');
  });
  setBlock(phase[2]);
  if(record&&gnc.phaseHistory[gnc.phaseHistory.length-1]!==phase[1])gnc.phaseHistory.push(phase[1]);
}
function advanceProgress(){
  let desired=1;
  for(let i=2;i<THRESHOLDS.length;i++)if(gnc.autoElapsed>=THRESHOLDS[i])desired=i;
  while(gnc.phaseIndex<desired)setPhase(gnc.phaseIndex+1);
}
function currentStatus(){
  if(!gnc.started)return'INITIAL ERROR · READY';
  if(gnc.captureLatched)return gnc.mode==='auto'?'CAPTURE COMPLETE · STABLE':'CAPTURED · HOLD IT';
  if(gnc.mode==='manual')return gnc.disturbed?'DISTURBANCE · YOUR MOVE':'MANUAL CONTROL';
  return `${PHASES[gnc.phaseIndex][1]} · ${gnc.disturbed?'RECOVERING':'ACQUIRING'}`;
}
function updateReadouts(){
  const o=offset(gnc),a=angle(gnc),success=isCaptured(gnc);
  const ob=$('#gnc-offset-readout'),ab=$('#gnc-error-readout'),ok=$('#gnc-success'),st=$('#gnc-autopilot-status');
  if(ob)ob.textContent=`${(o*.5).toFixed(0)} m · conceptual`;
  if(ab)ab.textContent=`${a.toFixed(1)}°`;
  if(ok){ok.textContent=success?'TARGET CORRIDOR CAPTURED':'CORRIDOR NOT YET CAPTURED';ok.classList.toggle('ok',success);}
  if(success&&gnc.started&&!gnc.captureLatched){
    gnc.captureLatched=true;gnc.captureSeconds=gnc.mode==='auto'?gnc.autoElapsed:null;gnc.disturbed=false;setPhase(7);
  }
  if(st)st.textContent=currentStatus();
}

function render(){
  if(!canvas)return;
  const {ctx,w,h,layout}=fitCanvas(canvas);ctx.clearRect(0,0,w,h);ctx.fillStyle='#010408';ctx.fillRect(0,0,w,h);
  drawStars(ctx,w,h,layout.compact?105:160,41,.8);
  const scene=sceneRect(w,h,{top:layout.phone?18:26,bottom:layout.phone?18:72},layout.phone?14:20);
  const scale=clamp(Math.min(scene.width/340,scene.height/250),.68,1.35),tx=scene.cx,ty=scene.y+scene.height*.47;
  const cw=clamp(124*scale,92,160),ch=clamp(92*scale,68,118),iw=cw*.39,ih=ch*.33;
  ctx.save();ctx.translate(tx,ty);ctx.strokeStyle='rgba(127,197,255,.3)';ctx.setLineDash([7,7]);ctx.strokeRect(-cw/2,-ch/2,cw,ch);
  ctx.setLineDash([]);ctx.strokeStyle='rgba(255,255,255,.88)';ctx.lineWidth=2;ctx.strokeRect(-iw/2,-ih/2,iw,ih);
  ctx.beginPath();ctx.moveTo(-iw*.8,0);ctx.lineTo(iw*.8,0);ctx.moveTo(0,-ih);ctx.lineTo(0,ih);ctx.stroke();ctx.restore();
  drawCanvasLabel(ctx,'ICPS TARGET',tx,ty+ch/2+17,Math.max(90,cw*1.15),{size:layout.phone?10:11,minSize:10,align:'center',color:'rgba(255,255,255,.66)',maxLines:1});
  const sx=tx+gnc.x*scale,sy=ty+gnc.y*scale,craft=clamp(scale,.76,1.25);
  ctx.save();ctx.translate(sx,sy);ctx.rotate(gnc.yaw*Math.PI/180);ctx.scale(craft,craft);ctx.strokeStyle='#f6fbff';ctx.lineWidth=1.6/craft;
  ctx.beginPath();ctx.moveTo(-22,12);ctx.lineTo(0,-24);ctx.lineTo(22,12);ctx.lineTo(8,8);ctx.lineTo(0,19);ctx.lineTo(-8,8);ctx.closePath();ctx.stroke();
  ctx.strokeStyle='rgba(240,196,118,.75)';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(Math.sin(gnc.pitch*Math.PI/180)*42,-42);ctx.stroke();
  if(gnc.lastFire>0){
    ctx.fillStyle=`rgba(111,231,225,${.25+.65*gnc.lastFire})`;
    for(const [x,y] of [[-18,10],[18,10],[-8,-7],[8,-7]]){ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+(x<0?-16:16)*gnc.lastFire,y+8);ctx.lineTo(x,y+3);ctx.fill();}
  }
  ctx.restore();ctx.strokeStyle='rgba(125,224,173,.42)';ctx.setLineDash([4,6]);ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(tx,ty);ctx.stroke();ctx.setLineDash([]);
}
function advanceSimulation(elapsed){
  if(gnc.started){
    const integrated=integrateElapsed(gnc,elapsed,gnc.mode==='auto');
    if(gnc.mode==='auto'){gnc.autoElapsed+=integrated;advanceProgress();}
  }
  updateReadouts();render();
}

function reset(){
  const mode=gnc.mode;
  Object.assign(gnc,initialState(),{started:false,mode,disturbed:false,autoElapsed:0,captureLatched:false,captureSeconds:null,phaseIndex:0,phaseHistory:['INITIAL ERROR']});
  setPhase(0,false);
  const tutorial=$('#gnc-tutorial'),controls=$('#gnc-controls'),start=$('#gnc-start');
  if(tutorial)tutorial.hidden=false;if(controls)controls.hidden=true;
  if(start)start.textContent=mode==='auto'?'Start auto demonstration':'Start manual approach';
  updateReadouts();
}
function start(){
  if(gnc.started)return;
  gnc.started=true;gnc.disturbed=false;gnc.autoElapsed=0;gnc.captureLatched=false;gnc.captureSeconds=null;
  const tutorial=$('#gnc-tutorial'),controls=$('#gnc-controls');if(tutorial)tutorial.hidden=true;if(controls)controls.hidden=false;
  if(gnc.mode==='auto'){gnc.phaseHistory=['INITIAL ERROR'];setPhase(1);}else setPhase(4);
  updateReadouts();
}
function setMode(mode){
  if(!['auto','manual'].includes(mode))return;
  const changed=gnc.mode!==mode;gnc.mode=mode;
  $$('[data-gnc-mode]').forEach(b=>{const active=b.dataset.gncMode===mode;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
  const controls=$('#gnc-controls'),read=$('#gnc-mode-readout'),title=$('#gnc-mode-title'),help=$('#gnc-mode-help'),startButton=$('#gnc-start');
  if(controls)controls.classList.toggle('auto-locked',mode==='auto');
  if(read)read.textContent=mode==='auto'?'AUTO GUIDANCE DEMO':'CREW MANUAL';
  if(title)title.textContent=mode==='auto'?'AUTO MODE · watch the closed loop work':'MANUAL MODE · you fly the capture';
  if(help)help.textContent=mode==='auto'
    ?'Watch Sense → Estimate → Guide → Control → Fire → Verify converge on the corridor. Rendering frame rate does not change simulated timing.'
    :'Use THC to translate and RHC to rotate. Capture the corridor while keeping motion small.';
  if(startButton&&!gnc.started)startButton.textContent=mode==='auto'?'Start auto demonstration':'Start manual approach';
  if(gnc.started&&changed){
    gnc.captureLatched=false;gnc.captureSeconds=null;gnc.disturbed=false;
    if(mode==='auto'){gnc.autoElapsed=0;gnc.phaseHistory=['INITIAL ERROR'];setPhase(1);}else setPhase(4);
  }
  if(!gnc.started)setPhase(0,false);
  updateReadouts();
}
function command(cmd){
  if(!gnc.started||gnc.mode!=='manual')return;
  const impulse=.34,rot=.075;
  if(cmd==='up')gnc.vy-=impulse;if(cmd==='down')gnc.vy+=impulse;if(cmd==='left')gnc.vx-=impulse;if(cmd==='right')gnc.vx+=impulse;
  if(cmd==='pitchUp')gnc.vpitch-=rot;if(cmd==='pitchDown')gnc.vpitch+=rot;if(cmd==='yawLeft')gnc.vyaw-=rot;if(cmd==='yawRight')gnc.vyaw+=rot;
  if(cmd==='attCenter'){gnc.vyaw=0;gnc.vpitch=0;}if(cmd==='transCenter'){gnc.vx=0;gnc.vy=0;}
  gnc.captureLatched=false;gnc.lastFire=1;setPhase(5);updateReadouts();
  setTimeout(()=>{if(gnc.started&&gnc.mode==='manual'&&!gnc.captureLatched){setPhase(6);updateReadouts();}},180);
}
function deterministicDisturbance(s){
  s.x=clamp(s.x+18,-150,150);s.y=clamp(s.y-13,-105,105);s.yaw=clamp(s.yaw+4.5,-35,35);s.pitch=clamp(s.pitch-3.5,-25,25);
  s.vx+=.48;s.vy-=.36;s.vyaw+=.12;s.vpitch-=.10;s.lastFire=1;
}
function randomDisturbance(s){
  const sx=Math.random()<.5?-1:1,sy=Math.random()<.5?-1:1;
  s.vx+=sx*(.38+Math.random()*.22);s.vy+=sy*(.28+Math.random()*.18);
  s.vyaw+=sx*(.10+Math.random()*.05);s.vpitch+=sy*(.08+Math.random()*.04);
  s.x=clamp(s.x+sx*(12+Math.random()*10),-150,150);s.y=clamp(s.y+sy*(8+Math.random()*9),-105,105);s.lastFire=1;
}
function disturb(deterministic=false){
  if(!gnc.started)start();
  deterministic?deterministicDisturbance(gnc):randomDisturbance(gnc);
  gnc.disturbed=true;gnc.captureLatched=false;gnc.captureSeconds=null;
  if(gnc.mode==='auto'){gnc.autoElapsed=0;gnc.phaseHistory=['INITIAL ERROR'];setPhase(1);}else setPhase(1);
  updateReadouts();
}

function simulateAutoCadence(frameSeconds){
  const cadence=clamp(Number(frameSeconds)||(1/60),1/240,1),state=initialState();let elapsed=0;
  while(elapsed<30&&!isCaptured(state)){const chunk=Math.min(cadence,30-elapsed);integrateElapsed(state,chunk,true);elapsed+=chunk;}
  return{pass:isCaptured(state),captureSeconds:+elapsed.toFixed(4),offset:+offset(state).toFixed(4),attitudeError:+angle(state).toFixed(4),speed:+speed(state).toFixed(4)};
}
function simulateDisturbanceRecovery(frameSeconds){
  const cadence=clamp(Number(frameSeconds)||(1/60),1/240,1),state=initialState();let initial=0;
  while(initial<30&&!isCaptured(state)){integrateElapsed(state,cadence,true);initial+=cadence;}
  if(!isCaptured(state))return{pass:false,reason:'initial-capture-failed'};
  deterministicDisturbance(state);let recovery=0;
  while(recovery<20&&!isCaptured(state)){integrateElapsed(state,cadence,true);recovery+=cadence;}
  return{pass:isCaptured(state),initialCaptureSeconds:+initial.toFixed(4),recoverySeconds:+recovery.toFixed(4),offset:+offset(state).toFixed(4),attitudeError:+angle(state).toFixed(4)};
}
function snapshot(){
  return{...gnc,phase:PHASES[gnc.phaseIndex][1],phaseHistory:[...gnc.phaseHistory],offset:offset(gnc),attitudeError:angle(gnc),speed:speed(gnc)};
}

window.A2GNC=Object.freeze({
  snapshot,reset,start,setMode,command,testAutoCadence:simulateAutoCadence,testDisturbanceRecovery:simulateDisturbanceRecovery,
  injectTestDisturbance:()=>{if(!QA_MODE)throw new Error('QA mode required.');disturb(true);},
  advanceTestTime:seconds=>{if(!QA_MODE)throw new Error('QA mode required.');advanceSimulation(seconds);return snapshot();}
});

$$('[data-gnc-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.gncMode)));
$$('.pad button').forEach(b=>b.addEventListener('click',()=>command(b.dataset.cmd)));
$('#gnc-start')?.addEventListener('click',start);
$('#gnc-reset')?.addEventListener('click',reset);
$('#gnc-disturbance')?.addEventListener('click',()=>disturb(false));

setBlock('sense');setMode('auto');reset();

if(canvas){
  let frameId=0;
  let last=0;
  let canvasInView=true;

  const stopLoop=()=>{
    if(frameId){cancelAnimationFrame(frameId);frameId=0;}
    last=0;
    canvas.dataset.a2Animation='paused';
  };

  const frame=timestamp=>{
    frameId=0;
    if(document.hidden||!canvasInView){stopLoop();return;}
    const elapsed=last?Math.max(0,(timestamp-last)/1000):0;
    last=timestamp;
    if(!QA_MODE)advanceSimulation(elapsed);else{updateReadouts();render();}
    frameId=requestAnimationFrame(frame);
    canvas.dataset.a2Animation='running';
  };

  const syncLoop=()=>{
    if(document.hidden||!canvasInView){stopLoop();return;}
    last=0;
    if(!frameId)frameId=requestAnimationFrame(frame);
    canvas.dataset.a2Animation='running';
  };

  if('IntersectionObserver' in window){
    new IntersectionObserver(entries=>{
      canvasInView=entries[0]?.isIntersecting!==false;
      if(canvasInView){render();syncLoop();}else stopLoop();
    },{rootMargin:'180px'}).observe(canvas);
  }

  document.addEventListener('visibilitychange',syncLoop);
  window.addEventListener('resize',()=>{if(document.hidden||!canvasInView)return;render();},{passive:true});
  syncLoop();
}
})();
