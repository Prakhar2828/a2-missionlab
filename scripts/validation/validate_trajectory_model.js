'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const model=require('../../js/trajectory-model.js');
const canonical=JSON.parse(fs.readFileSync(path.join(__dirname,'../../data/reference/artemis_ii_maneuver_plan_execution.json'),'utf8'));
const missionHtml=fs.readFileSync(path.join(__dirname,'../../mission.html'),'utf8');
const canonicalById=Object.fromEntries(canonical.maneuvers.map(x=>[x.maneuver_id,x]));

const close=(a,b,tol)=>Math.abs(a-b)<=tol;
const zero=model.compute({coastHours:21,dvFtS:0,direction:'tangential'});
const t5=model.compute({coastHours:5,dvFtS:4.2,direction:'tangential'});
const t21=model.compute({coastHours:21,dvFtS:4.2,direction:'tangential'});
const t72=model.compute({coastHours:72,dvFtS:4.2,direction:'tangential'});
const radial=model.compute({coastHours:21,dvFtS:4.2,direction:'radial'});
const normal=model.compute({coastHours:21,dvFtS:4.2,direction:'normal'});
const reverse=model.compute({coastHours:21,dvFtS:4.2,direction:'retrograde'});

assert(zero.finite,'zero-burn output must be finite');
assert(zero.separationKm<1e-5,'zero burn must preserve the reference state');
assert(t5.separationKm<t21.separationKm && t21.separationKm<t72.separationKm,'earlier correction opportunities must produce more downstream separation for this reference case');
assert(Math.abs(normal.sepN)>Math.abs(normal.sepR)*10,'normal burn should primarily create cross-track separation');
assert(Math.abs(t21.periapsisShiftKm)>Math.abs(normal.periapsisShiftKm)*20,'tangential burn should affect modeled periapsis far more than a pure normal burn');
assert(Math.sign(t21.periapsisShiftKm)===-Math.sign(reverse.periapsisShiftKm),'prograde and retrograde burns must move modeled periapsis in opposite directions');
assert(Math.abs(radial.separationKm-t21.separationKm)>20,'radial and tangential burns must not collapse to the same response');
assert(Math.abs(t21.separationKm-t21.linearKm)>20,'two-body response should not silently reduce to delta-v-times-time');
const nominalFine=model.propagate(t21.nominalStart,21*3600,{maxStepSeconds:30,sampleCount:180});
const correctedFine=model.propagate(t21.correctedStart,21*3600,{maxStepSeconds:30,sampleCount:180});
const fineSeparation=Math.hypot(...correctedFine.state.position.map((v,i)=>v-nominalFine.state.position[i]));
assert(Math.abs(t21.separationKm-fineSeparation)<.01,'default integration step failed convergence check against 30-second RK4 reference');

const byId=Object.fromEntries(model.MANEUVERS.map(x=>[x.id,x]));
assert(byId.otc1.status==='CANCELLED' && byId.otc1.executedDvFtS===null && byId.otc1.reportedDvFtS===null,'OTC1 must remain cancelled, not executed');
assert(close(byId.otc1.plannedDvFtS,0.7,1e-12) && close(byId.otc1.plannedDurationSeconds,8,1e-12),'OTC1 planned quantities changed or were conflated with execution');
assert(byId.otc2.status==='CANCELLED' && byId.otc2.executedDvFtS===null,'OTC2 must remain cancelled, not executed');
assert(byId.otc3.status==='EXECUTED' && byId.otc3.reportedDvFtS===null,'OTC3 executed magnitude must remain unknown in this source set');
assert(close(byId.rtc1.reportedDvFtS,1.6,1e-12),'RTC1 reported magnitude changed');
assert(close(byId.rtc2.reportedDvFtS,5.3,1e-12),'RTC2 reported magnitude changed');
assert(close(byId.rtc3.reportedDvFtS,4.2,1e-12),'RTC3 reported magnitude changed');
assert(close(byId.rtc2.coastHours,21,1e-12) && close(byId.rtc3.coastHours,5,1e-12),'return-to-entry timing anchors changed');
const coastControl=(missionHtml.match(/<input\b[^>]*\bid=[\"']trajectory-coast[\"'][^>]*>/i)||[])[0]||'';
assert(coastControl && /\bstep=[\"']any[\"']/i.test(coastControl),'trajectory coast control must accept exact mission-derived preset intervals such as RTC1 71.8333 h');
for(const item of model.MANEUVERS){
  const source=canonicalById[item.id];
  assert(source,`canonical maneuver missing: ${item.id}`);
  assert(item.status===source.status,`${item.id} status diverged from canonical maneuver record`);
  if(source.executed){
    assert(item.time===source.execution.timestamp_utc,`${item.id} UTC anchor diverged from canonical maneuver record`);
    assert(close(item.durationSeconds,source.execution.duration_seconds,1e-12),`${item.id} duration diverged from canonical maneuver record`);
    const srcDv=source.execution.reported_delta_v_ft_s;
    assert(srcDv===null?item.reportedDvFtS===null:close(item.reportedDvFtS,srcDv,1e-12),`${item.id} reported delta-v diverged from canonical maneuver record`);
  }else{
    assert(item.durationSeconds===null&&item.executedDvFtS===null,`${item.id} cancellation gained executed quantities`);
    const planned=source.plan||{};
    const srcPlanDv=planned.planned_delta_v_ft_s??null;
    const srcPlanDuration=planned.planned_duration_seconds??null;
    assert(srcPlanDv===null?item.plannedDvFtS===null:close(item.plannedDvFtS,srcPlanDv,1e-12),`${item.id} planned delta-v diverged from canonical maneuver record`);
    assert(srcPlanDuration===null?item.plannedDurationSeconds===null:close(item.plannedDurationSeconds,srcPlanDuration,1e-12),`${item.id} planned duration diverged from canonical maneuver record`);
  }
}

for(const hours of [1,5,12,21,48,72,96]){
  for(const dv of [0,.5,1.6,4.2,5.3,8]){
    for(const direction of Object.keys(model.DIRECTIONS)){
      const result=model.compute({coastHours:hours,dvFtS:dv,direction});
      assert(result.finite,`non-finite output at ${hours}h ${dv}ft/s ${direction}`);
    }
  }
}

console.log('A2 MissionLab trajectory-correction pure-model regression');
console.log('PASS: zero burn preserves reference state');
console.log('PASS: earlier opportunities amplify downstream separation in the reference case');
console.log('PASS: radial / tangential / normal directions produce distinct responses');
console.log('PASS: prograde / retrograde modeled periapsis response changes sign');
console.log('PASS: two-body result is not the old linear delta-v-times-time proxy');
console.log('PASS: default RK4 propagation converges within 10 m of the 30-second reference case');
console.log('PASS: OTC plan/execution boundaries and RTC public magnitudes remain evidence-bounded');
console.log('PASS: browser maneuver facts match the canonical Phase 2I.1 maneuver record');
console.log('PASS: coast-time control accepts exact mission-derived preset intervals');
console.log('PASS: full model sweep finite');
console.log(JSON.stringify({
  rtc3:model.serializable(t5),
  rtc2:model.serializable(model.compute({coastHours:21,dvFtS:5.3,direction:'tangential'})),
  rtc1:model.serializable(model.compute({coastHours:71.8333,dvFtS:1.6,direction:'tangential'})),
  normal:model.serializable(normal)
},null,2));
