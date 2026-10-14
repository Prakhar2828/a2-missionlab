(function(root,factory){
  'use strict';
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  if(root) root.A2EntryModel=Object.freeze(api);
})(typeof window!=='undefined'?window:null,function(){
  'use strict';

  const DURATION = 817.975;
  const HEAT_PEAK = 109.641953;
  const Q_PEAK = 12.808389;
  const SOURCE_START_MS = Date.parse('2026-04-10T23:53:30.866Z');

  const altitude = [
    [0,121.919907],[20,101.215372],[22,100],[27.918054,94.025448],[45.249112,80.330899],[46,80],
    [85,61.878469],[95,60.807901],[96,60.748759],[112.294128,60.350128],[193,62.767375],[239.647374,64.211808],
    [311,60],[374,50],[431,40.042026],[481,30],[526,20],[576,10],
    [619,5],[669,2],[693,1],[817.957676,0]
  ];
  const speed = [
    [0,10.632214],[20,10.650226],[85,9.984103],[95,9.6205],[112.294128,8.993741],
    [147,8],[198,7],[239.647374,6.479165],[285,6],[311,5.675],[350,5],[374,4.4],
    [388,4],[419,3],[431,2.587485],[450,2],[464.815771,1.535716],[481,1.079],
    [485,1],[512,.5],[526,.345],[566,.2],[576,.175],[601,.1],[619,.067],
    [669,.056],[679,.05],[693,.017],[817.957676,.00913]
  ];
  const mach = [
    [0,24.384670],[1.040993,25],[7.193687,30],[12.203316,35],[20,38.589162],
    [27.918054,37.793429],[45.249112,38.262468],[68.338295,35],[85,32.285653],[95,30.911621],
    [102.217443,30],[112.294128,28.826346],[156.678064,25],
    [239.647374,21.291566],[273.329676,20],[356.554606,15],[410.937535,10],
    [431,8.102942],[464.815771,5],[488.579165,3],[525.703754,1.2],[535.583533,1],
    [552.996307,.8],[817.957676,.03]
  ];
  const heat = [
    [0,1.027304],[20,5.951922],[27.918054,10.740910],[45.249112,34.071681],
    [85,109.641953],[95,104.975953],[112.294128,88.222385],[239.647374,25.574568],
    [431,7.596440],[464.815771,2.595809202]
  ];
  const q = [
    [0,.000821652],[27.918054,.091985],[45.249112,.990522],[85,12.036568],
    [95,12.798779],[112.294128,11.835359],[239.647374,3.692545],
    [431,12.808389],[464.815771,12.052781]
  ];

  const events = [
    {id:'source-start',t:0,label:'High-rate source begins',time:'23:53:30.866',evidence:'MISSIONLAB DERIVED',kind:'analysis'},
    {id:'continuum',t:27.918054,label:'Primary heating domain',time:'analysis +27.9 s',evidence:'MODELED',kind:'analysis'},
    {id:'heat-peak',t:85,label:'Modeled heat-flux peak',time:'analysis +85 s',evidence:'MODELED',kind:'analysis'},
    {id:'loft-start',t:112.294128,label:'Loft / rebound begins',time:'analysis +112.3 s',evidence:'MISSIONLAB DERIVED',kind:'analysis'},
    {id:'loft-top',t:239.647374,label:'Loft / rebound top',time:'analysis +239.6 s',evidence:'MISSIONLAB DERIVED',kind:'analysis'},
    {id:'reacq',t:389.134,label:'Communications reacquisition',time:'00:00 UTC',evidence:'NASA REPORTED MINUTE',kind:'public'},
    {id:'q-peak',t:431,label:'Global modeled dynamic-pressure peak',time:'analysis +431 s',evidence:'MODELED',kind:'analysis'},
    {id:'mach5',t:464.815771,label:'Final Mach 5 crossing',time:'analysis +464.8 s',evidence:'MODELED',kind:'analysis'},
    {id:'drogues',t:569.134,label:'Drogue parachutes',time:'00:03 UTC',evidence:'NASA REPORTED MINUTE',kind:'public'},
    {id:'mains',t:629.134,label:'Main parachutes',time:'00:04 UTC',evidence:'NASA REPORTED MINUTE',kind:'public'},
    {id:'splash-minute',t:809.134,label:'Splashdown public minute',time:'00:07 UTC',evidence:'NASA REPORTED MINUTE',kind:'public'},
    {id:'surface',t:817.957676,label:'Derived surface crossing',time:'00:07:08.824',evidence:'MISSIONLAB DERIVED',kind:'analysis'}
  ];

  const recovery = [
    {time:'00:12 UTC',delta:'+5 min',title:'Recovery teams approach',copy:'NASA and U.S. military recovery personnel begin approaching Orion in inflatable boats.',evidence:'NASA REPORTED'},
    {time:'01:34 UTC',delta:'+87 min',title:'Crew extracted',copy:'All four crewmembers are safely out of Orion and on the recovery raft.',evidence:'NASA REPORTED'},
    {time:'01:58 UTC',delta:'+111 min',title:'Crew aboard recovery ship',copy:'The crew is safely aboard USS John P. Murtha for post-mission medical evaluations.',evidence:'NASA REPORTED'},
    {time:'08:27 UTC',delta:'+500 min',title:'Orion secured in well deck',copy:'Spacecraft recovery reaches a different closure point than crew recovery. Postflight engineering work still continues.',evidence:'NASA REPORTED'}
  ];

  function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
  function interpolate(series,t){
    const x=clamp(t,series[0][0],series[series.length-1][0]);
    for(let i=1;i<series.length;i++){
      if(x<=series[i][0]){
        const [t0,v0]=series[i-1],[t1,v1]=series[i];
        const f=(x-t0)/(t1-t0||1);
        return v0+(v1-v0)*f;
      }
    }
    return series[series.length-1][1];
  }
  function formatUtc(t){
    const d=new Date(SOURCE_START_MS+clamp(t,0,DURATION)*1000);
    return d.toISOString().slice(11,23).replace('Z','')+' UTC';
  }
  function phaseAt(t){
    if(t<27.918054)return {id:'rarefied',title:'Rarefied upper entry',copy:'The vehicle is already fast, but body-scale continuum assumptions are not yet fully satisfied.'};
    if(t<85)return {id:'heating-rise',title:'Continuum hypersonic entry',copy:'Density rises rapidly while velocity remains enormous. The modeled convective-heating pulse builds.'};
    if(t<112.294128)return {id:'peak-heating',title:'Peak heating / first load peak',copy:'Modeled heating peaks before the first dominant dynamic-pressure maximum.'};
    if(t<239.647374)return {id:'loft',title:'Artemis II loft / rebound',copy:'The reconstructed trajectory briefly climbs about 3.86 km while still losing about 2.51 km/s of speed.'};
    if(t<389.134)return {id:'descent',title:'Renewed descent',copy:'After the rebound top, Orion descends again while speed and modeled external heat flux continue to fall.'};
    if(t<464.815771)return {id:'reacq',title:'Reacquired / lower hypersonic descent',copy:'The public 00:00 UTC reacquisition minute arrives before the final modeled Mach 5 crossing.'};
    if(t<535.583533)return {id:'supersonic',title:'Supersonic to transonic',copy:'The Sutton–Graves public interpretation domain has ended; the trajectory continues toward parachute conditions.'};
    if(t<569.134)return {id:'subsonic',title:'Subsonic descent',copy:'Atmospheric entry has removed almost all lunar-return speed before drogue deployment.'};
    if(t<629.134)return {id:'drogue',title:'Drogue parachute descent',copy:'NASA reported two drogues at 23,400 ft to stabilize and slow Orion.'};
    if(t<809.134)return {id:'main',title:'Main parachute descent',copy:'NASA reported all three mains deploying at 5,400 ft after the drogues were cut away.'};
    return {id:'splash',title:'Splashdown minute / derived surface crossing',copy:'NASA reported splashdown in the 00:07 UTC minute; MissionLab’s derived surface crossing occurs within that same public minute.'};
  }
  function commAt(t){
    if(t<=0)return {label:'BLACKOUT EXPECTED SHORTLY',tone:'watch',detail:'NASA reported a planned blackout shortly after Entry Interface; exact start second is not public.'};
    if(t<389.134)return {label:'PLANNED BLACKOUT CONTEXT',tone:'blackout',detail:'Exact blackout start/end seconds are intentionally not synthesized.'};
    return {label:'COMM REACQUIRED · PUBLIC MINUTE',tone:'ok',detail:'NASA reported communications reestablished at 00:00 UTC.'};
  }
  function heatAt(t){return t<=464.815771?interpolate(heat,t):null;}
  function qAt(t){return t<=464.815771?interpolate(q,t):null;}
  function stateAt(t){
    const x=clamp(Number(t)||0,0,DURATION);
    const v=interpolate(speed,x), h=interpolate(altitude,x), m=interpolate(mach,x), hf=heatAt(x), qp=qAt(x);
    return {
      t:x, progress:x/DURATION, utc:formatUtc(x), altitudeKm:h, speedKmS:v, mach:m,
      heatFluxWcm2:hf, dynamicPressureKpa:qp, phase:phaseAt(x), comm:commAt(x),
      heatNormalized:hf===null?0:clamp(hf/HEAT_PEAK,0,1), qNormalized:qp===null?0:clamp(qp/Q_PEAK,0,1),
      kineticEnergyRemovedFraction:clamp(1-(v/10.632214)**2,0,1),
      heatDomain:x<27.918054?'FORMAL · RAREFIED':x<=464.815771?'PRIMARY MODEL DOMAIN':'MODEL DOMAIN ENDED',
      inLoft:x>=112.294128&&x<=239.647374
    };
  }

  return {
    durationSeconds:DURATION, sourceStartUtc:'2026-04-10T23:53:30.866000Z', sourceStopUtc:'2026-04-11T00:07:08.841000Z',
    events:Object.freeze(events.map(Object.freeze)), recovery:Object.freeze(recovery.map(Object.freeze)),
    stateAt, altitudeAt:t=>interpolate(altitude,t), speedAt:t=>interpolate(speed,t), machAt:t=>interpolate(mach,t),
    heatAt, qAt, formatUtc,
    constants:Object.freeze({heatPeakWcm2:HEAT_PEAK,qPeakKpa:Q_PEAK,loftStart:112.294128,loftEnd:239.647374,mach5:464.815771,publicReacqOffset:389.134,drogueOffset:569.134,mainOffset:629.134,splashMinuteOffset:809.134,derivedSurfaceCrossing:817.957676})
  };
});
