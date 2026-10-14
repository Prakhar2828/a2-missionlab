(function(root,factory){
  'use strict';
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  if(root) root.A2TrajectoryModel=Object.freeze(api);
})(typeof window!=='undefined'?window:null,function(){
  'use strict';

  const MU_EARTH=398600.4418;
  const EARTH_RADIUS_KM=6378.1363;
  const ENTRY_ALTITUDE_KM=121.92;
  const ENTRY_RADIUS_KM=EARTH_RADIUS_KM+ENTRY_ALTITUDE_KM;
  const REFERENCE_APOGEE_RADIUS_KM=413144.445;
  const FT_S_TO_KM_S=0.0003048;
  const DEFAULTS=Object.freeze({coastHours:21,dvFtS:5.3,direction:'tangential'});
  const DIRECTIONS=Object.freeze({
    tangential:Object.freeze({label:'+T · along track',r:0,t:1,n:0}),
    retrograde:Object.freeze({label:'−T · reverse along track',r:0,t:-1,n:0}),
    radial:Object.freeze({label:'+R · outward radial',r:1,t:0,n:0}),
    inward:Object.freeze({label:'−R · inward radial',r:-1,t:0,n:0}),
    normal:Object.freeze({label:'+N · out of plane',r:0,t:0,n:1})
  });

  const MANEUVERS=Object.freeze([
    Object.freeze({id:'otc1',label:'OTC1',leg:'Outbound',status:'CANCELLED',time:'2026-04-03T22:49:00Z',timeLabel:'Apr 03 · planned 22:49 UTC',plannedDurationSeconds:8,plannedDvFtS:0.7,durationSeconds:null,reportedDvFtS:null,executedDvFtS:null,coastHours:null,evidence:'NASA REPORTED',note:'NASA cancelled OTC1 because Orion was already on the correct flight path. The 0.7 ft/s value and approximately eight-second duration were planned quantities, not executed performance data.'}),
    Object.freeze({id:'otc2',label:'OTC2',leg:'Outbound',status:'CANCELLED',time:null,timeLabel:'Apr 04 · date-level only',plannedDurationSeconds:null,plannedDvFtS:null,durationSeconds:null,reportedDvFtS:null,executedDvFtS:null,coastHours:null,evidence:'NASA REPORTED',note:'NASA cancelled OTC2 because Orion remained on track. Public MissionLab evidence does not retain an exact burn time or executed delta-v because no burn occurred.'}),
    Object.freeze({id:'otc3',label:'OTC3',leg:'Outbound',status:'EXECUTED',time:'2026-04-06T03:03:00Z',timeLabel:'Apr 06 · 03:03 UTC',durationSeconds:17.5,reportedDvFtS:null,executedDvFtS:null,coastHours:null,evidence:'NASA REPORTED',note:'NASA reported OTC3 execution and 17.5-second duration. The MissionLab source set does not establish a public flown delta-v magnitude, so any magnitude used here is modeled.'}),
    Object.freeze({id:'rtc1',label:'RTC1',leg:'Return',status:'EXECUTED',time:'2026-04-08T00:03:00Z',timeLabel:'Apr 08 · 00:03 UTC',durationSeconds:15,reportedDvFtS:1.6,executedDvFtS:1.6,coastHours:71.8333,evidence:'NASA REPORTED',note:'NASA reported RTC1 at 00:03 UTC on April 8: 15 seconds and 1.6 ft/s of velocity change.'}),
    Object.freeze({id:'rtc2',label:'RTC2',leg:'Return',status:'EXECUTED',time:'2026-04-10T02:53:00Z',timeLabel:'Apr 10 · 02:53 UTC',durationSeconds:9,reportedDvFtS:5.3,executedDvFtS:5.3,coastHours:21,evidence:'NASA REPORTED',note:'NASA reported RTC2 at 02:53 UTC on April 10: 9 seconds and 5.3 ft/s of velocity change. MissionLab does not infer a flown vector from the public magnitude.'}),
    Object.freeze({id:'rtc3',label:'RTC3',leg:'Return',status:'EXECUTED',time:'2026-04-10T18:53:00Z',timeLabel:'Apr 10 · 18:53 UTC',durationSeconds:8,reportedDvFtS:4.2,executedDvFtS:4.2,coastHours:5,evidence:'NASA REPORTED',note:'NASA reported RTC3 at 18:53 UTC on April 10: 8 seconds and 4.2 ft/s of velocity change, five hours before the public Entry Interface minute.'})
  ]);

  const refA=(ENTRY_RADIUS_KM+REFERENCE_APOGEE_RADIUS_KM)/2;
  const refE=(REFERENCE_APOGEE_RADIUS_KM-ENTRY_RADIUS_KM)/(REFERENCE_APOGEE_RADIUS_KM+ENTRY_RADIUS_KM);
  const refN=Math.sqrt(MU_EARTH/(refA*refA*refA));
  const refPeriod=2*Math.PI/refN;

  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const mag=v=>Math.hypot(v[0],v[1],v[2]);
  const add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]];
  const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
  const scale=(v,s)=>[v[0]*s,v[1]*s,v[2]*s];
  const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const unit=v=>{const m=mag(v);return m>0?scale(v,1/m):[0,0,0];};

  function solveE(M,e){
    let E=M;
    for(let i=0;i<24;i++){
      const f=E-e*Math.sin(E)-M;
      const fp=1-e*Math.cos(E);
      const step=f/fp;
      E-=step;
      if(Math.abs(step)<1e-13) break;
    }
    return E;
  }

  function referenceState(secondsBeforeEntry){
    const t=-Math.abs(secondsBeforeEntry);
    if(Math.abs(t)>refPeriod/2){
      throw new Error('Reference coast exceeds the inbound half-period of the educational orbit.');
    }
    const M=refN*t;
    const E=solveE(M,refE);
    const beta=Math.sqrt(1-refE*refE);
    const denom=1-refE*Math.cos(E);
    const position=[
      refA*(Math.cos(E)-refE),
      refA*beta*Math.sin(E),
      0
    ];
    const velocity=[
      -refA*Math.sin(E)*refN/denom,
      refA*beta*Math.cos(E)*refN/denom,
      0
    ];
    return {position,velocity,t};
  }

  function rtnBasis(state){
    const rHat=unit(state.position);
    const h= cross(state.position,state.velocity);
    const nHat=unit(h);
    const tHat=unit(cross(nHat,rHat));
    return {rHat,tHat,nHat};
  }

  function derivative(state){
    const r=state.position;
    const radius=mag(r);
    const factor=-MU_EARTH/(radius*radius*radius);
    return {
      position:[state.velocity[0],state.velocity[1],state.velocity[2]],
      velocity:[factor*r[0],factor*r[1],factor*r[2]]
    };
  }

  function stateAdd(base,k,s){
    return {
      position:[base.position[0]+k.position[0]*s,base.position[1]+k.position[1]*s,base.position[2]+k.position[2]*s],
      velocity:[base.velocity[0]+k.velocity[0]*s,base.velocity[1]+k.velocity[1]*s,base.velocity[2]+k.velocity[2]*s]
    };
  }

  function rk4Step(state,dt){
    const k1=derivative(state);
    const k2=derivative(stateAdd(state,k1,dt/2));
    const k3=derivative(stateAdd(state,k2,dt/2));
    const k4=derivative(stateAdd(state,k3,dt));
    return {
      position:[0,1,2].map(i=>state.position[i]+dt*(k1.position[i]+2*k2.position[i]+2*k3.position[i]+k4.position[i])/6),
      velocity:[0,1,2].map(i=>state.velocity[i]+dt*(k1.velocity[i]+2*k2.velocity[i]+2*k3.velocity[i]+k4.velocity[i])/6)
    };
  }

  function propagate(state,totalSeconds,options={}){
    const maxStep=Math.max(20,options.maxStepSeconds||120);
    const count=Math.max(1,Math.ceil(Math.abs(totalSeconds)/maxStep));
    const dt=totalSeconds/count;
    const sampleTarget=Math.max(24,options.sampleCount||180);
    const sampleEvery=Math.max(1,Math.floor(count/sampleTarget));
    let current={position:[...state.position],velocity:[...state.velocity]};
    const path=[{t:0,position:[...current.position]}];
    for(let i=1;i<=count;i++){
      current=rk4Step(current,dt);
      if(i%sampleEvery===0||i===count) path.push({t:i*dt,position:[...current.position]});
    }
    return {state:current,path};
  }

  function osculating(state){
    const r=state.position,v=state.velocity;
    const radius=mag(r),speed=mag(v);
    const h=cross(r,v),hMag=mag(h);
    const eVec=sub(scale(cross(v,h),1/MU_EARTH),scale(r,1/radius));
    const e=mag(eVec);
    const energy=speed*speed/2-MU_EARTH/radius;
    const a=-MU_EARTH/(2*energy);
    if(!(a>0&&e<1)) return {a,e,periapsisRadius:null,timeToPeriapsis:null,inclinationDeg:null};
    const cosE=clamp((1-radius/a)/Math.max(e,1e-12),-1,1);
    const sinE=dot(r,v)/(Math.max(e,1e-12)*Math.sqrt(MU_EARTH*a));
    const E=Math.atan2(sinE,cosE);
    const M=E-e*Math.sin(E);
    const n=Math.sqrt(MU_EARTH/(a*a*a));
    const timeToPeriapsis=M<=0?-M/n:(2*Math.PI-M)/n;
    const inclinationDeg=Math.acos(clamp(h[2]/hMag,-1,1))*180/Math.PI;
    return {a,e,periapsisRadius:a*(1-e),timeToPeriapsis,inclinationDeg};
  }

  function compute(patch={}){
    const input={...DEFAULTS,...patch};
    input.coastHours=clamp(Number(input.coastHours),1,96);
    input.dvFtS=clamp(Number(input.dvFtS),0,8);
    if(!DIRECTIONS[input.direction]) input.direction=DEFAULTS.direction;
    const coastSeconds=input.coastHours*3600;
    const nominalStart=referenceState(coastSeconds);
    const basis=rtnBasis(nominalStart);
    const d=DIRECTIONS[input.direction];
    const dvKmS=input.dvFtS*FT_S_TO_KM_S;
    const dv=add(add(scale(basis.rHat,d.r*dvKmS),scale(basis.tHat,d.t*dvKmS)),scale(basis.nHat,d.n*dvKmS));
    const correctedStart={position:[...nominalStart.position],velocity:add(nominalStart.velocity,dv)};
    const nominal=propagate(nominalStart,coastSeconds);
    const corrected=propagate(correctedStart,coastSeconds);
    const dr=sub(corrected.state.position,nominal.state.position);
    const endBasis=rtnBasis(nominal.state);
    const sepR=dot(dr,endBasis.rHat),sepT=dot(dr,endBasis.tHat),sepN=dot(dr,endBasis.nHat);
    const separationKm=mag(dr);
    const linearKm=input.dvFtS*0.3048*coastSeconds/1000;
    const correctedOsc=osculating(correctedStart);
    const nominalOsc=osculating(nominalStart);
    const periapsisShiftKm=correctedOsc.periapsisRadius===null?null:correctedOsc.periapsisRadius-ENTRY_RADIUS_KM;
    const arrivalShiftSeconds=correctedOsc.timeToPeriapsis===null?null:correctedOsc.timeToPeriapsis-coastSeconds;
    const planeChangeDeg=correctedOsc.inclinationDeg===null?null:correctedOsc.inclinationDeg;
    const startRadiusKm=mag(nominalStart.position);
    const endRadiusKm=mag(corrected.state.position);
    const finite=[separationKm,sepR,sepT,sepN,linearKm,startRadiusKm,endRadiusKm,periapsisShiftKm??0,arrivalShiftSeconds??0,planeChangeDeg??0].every(Number.isFinite);
    return {
      input,
      nominalStart,
      correctedStart,
      nominal,
      corrected,
      basis,
      endBasis,
      dv,
      separationKm,
      sepR,
      sepT,
      sepN,
      linearKm,
      periapsisShiftKm,
      arrivalShiftSeconds,
      planeChangeDeg,
      startRadiusKm,
      endRadiusKm,
      nominalOsc,
      correctedOsc,
      finite
    };
  }

  function serializable(m){
    return {
      coastHours:m.input.coastHours,
      dvFtS:m.input.dvFtS,
      direction:m.input.direction,
      startRadiusKm:m.startRadiusKm,
      separationKm:m.separationKm,
      sepR:m.sepR,
      sepT:m.sepT,
      sepN:m.sepN,
      linearKm:m.linearKm,
      periapsisShiftKm:m.periapsisShiftKm,
      arrivalShiftSeconds:m.arrivalShiftSeconds,
      planeChangeDeg:m.planeChangeDeg,
      finite:m.finite
    };
  }

  return {
    MU_EARTH,
    EARTH_RADIUS_KM,
    ENTRY_ALTITUDE_KM,
    ENTRY_RADIUS_KM,
    REFERENCE_APOGEE_RADIUS_KM,
    DEFAULTS,
    DIRECTIONS,
    MANEUVERS,
    referenceOrbit:Object.freeze({a:refA,e:refE,periodSeconds:refPeriod}),
    referenceState,
    rtnBasis,
    propagate,
    osculating,
    compute,
    serializable
  };
});
