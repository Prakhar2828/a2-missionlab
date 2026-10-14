'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const model=require('../../js/space-weather-model.js');
const evidence=JSON.parse(fs.readFileSync(path.join(__dirname,'../../data/reference/artemis_ii_space_weather_phase_h.json'),'utf8'));
const oldNairas=JSON.parse(fs.readFileSync(path.join(__dirname,'../../data/reference/artemis_ii_nairas_interface.json'),'utf8'));
const missionHtml=fs.readFileSync(path.join(__dirname,'../../mission.html'),'utf8');

const close=(a,b,tol=1e-9)=>Math.abs(a-b)<=tol;
const cases=[
  {log:0,scale:'BELOW S1',rank:0,pfu:1},
  {log:1,scale:'S1',rank:1,pfu:10},
  {log:2,scale:'S2',rank:2,pfu:100},
  {log:3,scale:'S3',rank:3,pfu:1000},
  {log:4,scale:'S4',rank:4,pfu:10000},
  {log:5,scale:'S5',rank:5,pfu:100000}
];
for(const c of cases){
  const r=model.evaluate({log10Pfu:c.log,location:'deep'});
  assert(r.finite,`non-finite result for ${c.scale}`);
  assert(close(r.pfu,c.pfu,1e-8),`${c.scale} pfu mismatch`);
  assert(r.scale.scale===c.scale&&r.scale.rank===c.rank,`${c.scale} classification mismatch`);
  assert(r.doseKnown===false&&r.crewDose===null,`${c.scale} must not become crew dose`);
}
assert(model.classifyPfu(9.999).scale==='BELOW S1','S1 lower boundary regressed');
assert(model.classifyPfu(10).scale==='S1','S1 threshold regressed');
assert(model.classifyPfu(100).scale==='S2','S2 threshold regressed');
assert(model.classifyPfu(1000).scale==='S3','S3 threshold regressed');
assert(model.classifyPfu(10000).scale==='S4','S4 threshold regressed');
assert(model.classifyPfu(100000).scale==='S5','S5 threshold regressed');

const deep=model.evaluate({log10Pfu:3,location:'deep'});
const leo=model.evaluate({log10Pfu:3,location:'leo'});
const lunar=model.evaluate({log10Pfu:3,location:'lunar'});
assert(deep.pfu===leo.pfu&&leo.pfu===lunar.pfu,'location must not alter measured proton flux');
assert(deep.scale.scale===leo.scale.scale&&leo.scale.scale===lunar.scale.scale,'location must not alter NOAA scale');
assert(deep.location.context!==leo.location.context&&deep.location.context!==lunar.location.context,'location context must remain educationally distinct');

const thresholds=evidence.sep_reference_scale.thresholds;
assert.deepStrictEqual(thresholds.map(x=>x.minimum_pfu),[10,100,1000,10000,100000],'evidence S-scale thresholds changed');
assert.deepStrictEqual(thresholds.map(x=>x.scale),['S1','S2','S3','S4','S5'],'evidence S-scale labels changed');
assert(evidence.evidence_boundaries.sep_pfu_equal_absorbed_dose===false,'pfu/dose evidence boundary changed');
assert(evidence.evidence_boundaries.public_noaa_scale_equal_nasa_flight_rule===false,'NOAA/NASA flight-rule boundary changed');
assert(evidence.evidence_boundaries.crew_dosimetry_claimed===false,'crew dosimetry must remain unclaimed');
assert(evidence.artemis_ii_monitoring.hera_active_sensors_inside_orion===6,'HERA public count changed');

assert(oldNairas.nairas_model.version_family==='3.0','historical Phase 5B NAIRAS version changed');
assert(oldNairas.nairas_run_status.run_submitted_by_missionlab===false,'historical Phase 5B unexpectedly claims a run');
assert(evidence.nairas_version_resolution.current_public_documentation.version_family==='4','current NAIRAS documentation version mismatch');
assert(evidence.nairas_version_resolution.current_public_documentation.production_release_noted==='4.15','NAIRAS production release note mismatch');
assert(evidence.nairas_version_resolution.historical_repository_interface.version_family==='3.0','historical/current NAIRAS distinction regressed');
assert(evidence.nairas_version_resolution.historical_repository_interface.run_submitted_by_missionlab===false,'Phase H unexpectedly claims a NAIRAS run');

assert(model.MISSION_CONTEXT.speedMax.value===789.7&&model.MISSION_CONTEXT.speedMax.unit==='km/s','OMNI speed context mismatch');
assert(model.MISSION_CONTEXT.bzMin.value===-14.46&&model.MISSION_CONTEXT.bzMin.unit==='nT','OMNI Bz context mismatch');
assert(model.MISSION_CONTEXT.pressureMax.value===11.75&&model.MISSION_CONTEXT.pressureMax.unit==='nPa','OMNI pressure context mismatch');
assert(model.MISSION_CONTEXT.symhMin.value===-104&&model.MISSION_CONTEXT.symhMin.unit==='nT','OMNI SYM/H context mismatch');
assert(!/id=["']solar-activity["']/i.test(missionHtml),'old generic solar activity 0-100 control still exists');
assert(!/id=["']shielding-assumption["']/i.test(missionHtml),'old generic shielding 0-100 control still exists');
assert(/id=["']sep-flux-log["']/i.test(missionHtml),'physical proton-flux control missing');
assert(/NOAA S-scale reference ≠ Artemis II flight rule|not as an Artemis II flight rule/i.test(missionHtml),'NOAA flight-rule boundary missing');

for(let log=-1;log<=5;log+=.125){
  for(const location of Object.keys(model.LOCATIONS)){
    const r=model.evaluate({log10Pfu:log,location});
    assert(r.finite&&Number.isFinite(r.pfu),`non-finite sweep at ${log} ${location}`);
    assert(r.doseKnown===false&&r.crewDose===null,`dose boundary regressed at ${log} ${location}`);
  }
}

console.log('A2 MissionLab Phase H space-weather pure-model regression');
console.log('PASS: physically meaningful >=10 MeV proton-flux axis');
console.log('PASS: NOAA S1-S5 thresholds and boundary behavior');
console.log('PASS: location changes context but not measured flux/classification');
console.log('PASS: pfu never becomes crew dose');
console.log('PASS: Phase 5A OMNI mission-window anchors preserved');
console.log('PASS: Artemis II HERA monitoring context preserved');
console.log('PASS: historical NAIRAS 3.0 interface separated from current Version 4 documentation');
console.log('PASS: no MissionLab NAIRAS run or crew dosimetry fabricated');
console.log(JSON.stringify({thresholds,nairas:evidence.nairas_version_resolution,baseline:model.evaluate({log10Pfu:0,location:'deep'}),s3:model.evaluate({log10Pfu:3,location:'lunar'})},null,2));
