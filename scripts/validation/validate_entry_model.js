'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const model=require('../../js/entry-model.js');
const reference=JSON.parse(fs.readFileSync(path.join(__dirname,'../../data/reference/artemis_ii_entry_phase_i.json'),'utf8'));
const missionHtml=fs.readFileSync(path.join(__dirname,'../../mission.html'),'utf8');

const close=(a,b,tol=1e-6)=>Math.abs(a-b)<=tol;
const byId=Object.fromEntries(reference.analysis_landmarks.map(x=>[x.id,x]));
const eventById=Object.fromEntries(model.events.map(x=>[x.id,x]));

assert(close(model.durationSeconds,817.975,1e-9),'high-rate source duration changed');
assert(model.sourceStartUtc===reference.high_rate_source.source_start_utc,'source-start UTC diverged from Phase I reference');
assert(model.sourceStopUtc===reference.high_rate_source.source_stop_utc,'source-stop UTC diverged from Phase I reference');
assert(reference.high_rate_source.records===819,'Phase I reference lost the 819-state source count');
assert(reference.high_rate_source.frame_label==='M50','source frame label changed');
assert(reference.high_rate_source.eighth_numeric_field_physical_meaning==='UNRESOLVED','unresolved PROP_MAN eighth field gained a fabricated meaning');

const start=model.stateAt(0);
assert(close(start.altitudeKm,byId.high_rate_start.altitude_km),'start altitude diverged from reference');
assert(close(start.speedKmS,byId.high_rate_start.earth_relative_speed_km_s),'start Earth-relative speed diverged from reference');
assert(close(start.mach,byId.high_rate_start.mach),'start Mach diverged from reference');
assert(close(start.heatFluxWcm2,byId.high_rate_start.sutton_graves_heat_flux_w_cm2),'start formal heating diagnostic diverged from reference');

const heatPeak=model.stateAt(byId.sutton_graves_peak.analysis_elapsed_seconds);
assert(close(heatPeak.altitudeKm,byId.sutton_graves_peak.altitude_km),'heat-peak altitude changed');
assert(close(heatPeak.speedKmS,byId.sutton_graves_peak.earth_relative_speed_km_s),'heat-peak speed changed');
assert(close(heatPeak.mach,byId.sutton_graves_peak.mach),'heat-peak Mach changed');
assert(close(heatPeak.heatFluxWcm2,byId.sutton_graves_peak.sutton_graves_heat_flux_w_cm2),'Sutton-Graves peak changed');

const qEarly=model.stateAt(byId.early_dynamic_pressure_peak.analysis_elapsed_seconds);
const qLate=model.stateAt(byId.global_dynamic_pressure_peak.analysis_elapsed_seconds);
assert(close(qEarly.dynamicPressureKpa,12.798779),'early modeled dynamic-pressure peak changed');
assert(close(qLate.dynamicPressureKpa,12.808389),'global modeled dynamic-pressure peak changed');
assert(close(qEarly.heatFluxWcm2,104.975953),'early load-peak modeled heating changed');
assert(close(qLate.heatFluxWcm2,7.596440),'late load-peak modeled heating changed');
assert(Math.abs(qLate.dynamicPressureKpa-qEarly.dynamicPressureKpa)/qLate.dynamicPressureKpa*100<0.08,'protected near-equality of dominant dynamic-pressure peaks was lost');
assert(qEarly.heatFluxWcm2/qLate.heatFluxWcm2>13,'heating contrast between near-equal pressure peaks was weakened');
assert(byId.sutton_graves_peak.analysis_elapsed_seconds<byId.global_dynamic_pressure_peak.analysis_elapsed_seconds,'heating must peak before the global dynamic-pressure peak');

const heatingReference=JSON.parse(fs.readFileSync(path.join(__dirname,'../../data/reference/artemis_ii_convective_heating_model.json'),'utf8'));
const sgK=heatingReference.correlation.earth_constant, noseRadius=heatingReference.geometry.reference_nose_radius_m;
const reconstructedDynamicPressure=(heatWcm2,speedKmS)=>{const v=speedKmS*1000;const rho=Math.pow((heatWcm2*1e4)/(sgK*Math.pow(v,3)),2)*noseRadius;return 0.5*rho*v*v/1000;};
for(const [id,key] of [['sutton_graves_peak','dynamic_pressure_kpa_reconstructed_from_same_phase2_model_inputs'],['loft_rebound_start','dynamic_pressure_kpa_reconstructed_from_same_phase2_model_inputs'],['loft_rebound_top','dynamic_pressure_kpa_reconstructed_from_same_phase2_model_inputs'],['final_mach_5','dynamic_pressure_kpa_reconstructed_from_same_phase2_model_inputs']]){
  const point=byId[id];
  const reconstructed=reconstructedDynamicPressure(point.sutton_graves_heat_flux_w_cm2,point.earth_relative_speed_km_s);
  assert(close(reconstructed,point[key],1e-6),`${id} UI dynamic-pressure support point is not algebraically consistent with the existing Sutton-Graves model inputs`);
}
assert(reference.continuous_ui_support.dynamic_pressure_support_checkpoint_derivation.interpretation.includes('not independent evidence'),'dynamic-pressure UI support values lost their derivation boundary');

const loftStart=model.stateAt(reference.continuous_ui_support.artemis_ii_loft_rebound.start_seconds);
const loftTop=model.stateAt(reference.continuous_ui_support.artemis_ii_loft_rebound.end_seconds);
assert(close(loftTop.altitudeKm-loftStart.altitudeKm,reference.continuous_ui_support.artemis_ii_loft_rebound.altitude_recovery_km,1e-6),'loft/rebound altitude recovery changed');
assert(close(loftStart.speedKmS-loftTop.speedKmS,reference.continuous_ui_support.artemis_ii_loft_rebound.speed_loss_km_s,2e-6),'loft/rebound speed loss changed');
assert(loftStart.inLoft&&loftTop.inLoft,'loft interval classification missing');
assert(!model.stateAt(111).inLoft&&!model.stateAt(240).inLoft,'loft classification leaked outside protected interval');

assert(close(eventById.reacq.t,389.134,1e-9)&&eventById.reacq.kind==='public','reacquisition public-minute anchor changed');
assert(close(eventById.drogues.t,569.134,1e-9)&&eventById.drogues.kind==='public','drogue public-minute anchor changed');
assert(close(eventById.mains.t,629.134,1e-9)&&eventById.mains.kind==='public','main public-minute anchor changed');
assert(close(eventById['splash-minute'].t,809.134,1e-9)&&eventById['splash-minute'].kind==='public','splashdown public-minute anchor changed');
assert(eventById.reacq.evidence.includes('MINUTE')&&eventById.drogues.evidence.includes('MINUTE'),'public event precision labels weakened');

const afterMach5=model.stateAt(500);
assert(afterMach5.heatFluxWcm2===null&&afterMach5.dynamicPressureKpa===null,'public UI must not extrapolate Phase 2 hypersonic heat/q model beyond its protected window');
assert(model.stateAt(200).comm.detail.includes('not synthesized'),'blackout runtime gained fabricated exact start/end timing');
assert(model.stateAt(390).comm.label.includes('PUBLIC MINUTE'),'reacquisition lost minute-resolution evidence label');

for(let t=0;t<=model.durationSeconds;t+=0.5){
  const state=model.stateAt(t);
  assert([state.t,state.progress,state.altitudeKm,state.speedKmS,state.mach,state.kineticEnergyRemovedFraction].every(Number.isFinite),`non-finite state at ${t}s`);
  assert(state.altitudeKm>=-1e-9&&state.altitudeKm<=125,'altitude left protected display domain');
  assert(state.speedKmS>=0&&state.speedKmS<11,'speed left protected display domain');
  assert(state.progress>=0&&state.progress<=1,'progress left [0,1]');
}

const boundarySet=new Set(reference.critical_non_equivalences);
for(const required of [
  'NASA_REPORTED_PUBLIC_MINUTE != EXACT_SECOND_LEVEL_TELEMETRY',
  'EDUCATIONAL_INTERPOLATION != MEASURED_TRAJECTORY_STATE',
  'MODELED_SUTTON_GRAVES_HEATING != MEASURED_TPS_TELEMETRY',
  'KINEMATIC_DECELERATION_G0_EQUIVALENT != CREW_SENSED_G_LOAD',
  'EXPECTED_ENTRY_BLACKOUT != COMMUNICATIONS_ANOMALY',
  'ARTEMIS_II_LOFT_REBOUND != ARTEMIS_I_SKIP_ENTRY',
  'DERIVED_SURFACE_CROSSING != OFFICIAL_NASA_ACTUAL_SPLASHDOWN_COORDINATE',
  'DERIVED_TERMINAL_STATE != OFFICIAL_LANDING_TARGETING_ACCURACY',
  'CREW_RECOVERY != SPACECRAFT_RECOVERY != POSTFLIGHT_ENGINEERING_CLOSURE'
]) assert(boundarySet.has(required),`missing Phase I evidence boundary: ${required}`);

for(const phrase of [
  'not a telemetry replay',
  'not a skip entry',
  'Not measured TPS telemetry',
  'exact start/end seconds unknown',
  'not publicly quantifiable',
  'crew recovery from spacecraft recovery',
  'curated Phase 2 checkpoints'
]) assert(missionHtml.toLowerCase().includes(phrase.toLowerCase()),`public Entry experience missing evidence text: ${phrase}`);

assert(reference.splashdown_boundary.offset_is_exact_timing_error===false,'public-minute offset was promoted to exact timing error');
assert(reference.splashdown_boundary.official_target_to_actual_miss_distance==='NOT_PUBLICLY_QUANTIFIABLE','landing miss distance was fabricated');
assert(reference.parachute_architecture.architecture_is_exact_as_flown_individual_canopy_log===false,'parachute architecture was promoted to an exact as-flown canopy log');
assert(reference.continuous_ui_support.heating.measured_tps_telemetry===false,'modeled heating was promoted to measured TPS telemetry');

console.log('A2 MissionLab Phase I entry pure-model/evidence regression');
console.log('PASS: source identity, duration, frame, and unresolved-field boundary');
console.log('PASS: continuous altitude / speed / Mach checkpoints');
console.log('PASS: modeled heating and dynamic-pressure peak relationship');
console.log('PASS: Artemis II loft / rebound geometry and terminology boundary');
console.log('PASS: public-minute event anchors remain minute-resolution evidence');
console.log('PASS: no heat/q extrapolation beyond protected Phase 2 hypersonic model window');
console.log('PASS: blackout timing remains evidence-bounded');
console.log('PASS: full continuous UI model sweep finite');
console.log('PASS: splashdown / recovery non-equivalence boundaries');
console.log(JSON.stringify({
  source:{start:model.sourceStartUtc,stop:model.sourceStopUtc,states:reference.high_rate_source.records},
  heatPeak:{t:heatPeak.t,altitudeKm:heatPeak.altitudeKm,mach:heatPeak.mach,heatFluxWcm2:heatPeak.heatFluxWcm2},
  dynamicPressure:{early:{qKpa:qEarly.dynamicPressureKpa,heat:qEarly.heatFluxWcm2},late:{qKpa:qLate.dynamicPressureKpa,heat:qLate.heatFluxWcm2}},
  loft:{startAltitudeKm:loftStart.altitudeKm,topAltitudeKm:loftTop.altitudeKm,speedLossKmS:loftStart.speedKmS-loftTop.speedKmS},
  publicMinutes:{reacq:eventById.reacq.time,drogues:eventById.drogues.time,mains:eventById.mains.time,splash:eventById['splash-minute'].time}
},null,2));
