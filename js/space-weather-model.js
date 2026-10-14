(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.A2SpaceWeatherModel=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCALES=[
    {scale:'S1',description:'MINOR',minimumPfu:10,rank:1},
    {scale:'S2',description:'MODERATE',minimumPfu:100,rank:2},
    {scale:'S3',description:'STRONG',minimumPfu:1000,rank:3},
    {scale:'S4',description:'SEVERE',minimumPfu:10000,rank:4},
    {scale:'S5',description:'EXTREME',minimumPfu:100000,rank:5}
  ];

  const LOCATIONS={
    leo:{label:'LEO',context:'Near Earth · geomagnetic shielding can reduce parts of the external charged-particle environment, while trapped-particle regions remain relevant.'},
    deep:{label:'DEEP SPACE',context:'Beyond persistent low-Earth-orbit geomagnetic protection · crewed missions require dedicated radiation monitoring and response capability.'},
    lunar:{label:'LUNAR VICINITY',context:'Cislunar/deep-space context · location changes mission geometry and protection context, but does not by itself convert proton flux into crew dose.'}
  };

  const MISSION_CONTEXT={
    bzMin:{value:-14.46,unit:'nT',utc:'2026-04-02T07:09:00Z',met:'00:08:33:48'},
    speedMax:{value:789.7,unit:'km/s',utc:'2026-04-03T15:52:00Z',met:'01:17:16:48'},
    pressureMax:{value:11.75,unit:'nPa',utc:'2026-04-10T07:16:00Z',met:'08:08:40:48'},
    symhMin:{value:-104,unit:'nT',utc:'2026-04-02T08:41:00Z',met:'00:10:05:48'}
  };

  function clamp(value,min,max){return Math.min(max,Math.max(min,value));}
  function pfuFromLog10(log10Pfu){return Math.pow(10,clamp(Number(log10Pfu),-1,5));}
  function classifyPfu(pfu){
    const value=Math.max(0,Number(pfu)||0);
    let result={scale:'BELOW S1',description:'BELOW NOAA RADIATION-STORM THRESHOLD',minimumPfu:0,rank:0};
    for(const item of SCALES){if(value>=item.minimumPfu)result=item;}
    return {...result};
  }
  function formatPfu(value){
    if(value>=100000)return `${Math.round(value).toLocaleString('en-US')} pfu`;
    if(value>=1000)return `${Math.round(value).toLocaleString('en-US')} pfu`;
    if(value>=10)return `${value.toFixed(value<100?1:0)} pfu`;
    return `${value.toFixed(value<1?2:1)} pfu`;
  }
  function evaluate(input={}){
    const log10Pfu=clamp(Number(input.log10Pfu??0),-1,5);
    const pfu=pfuFromLog10(log10Pfu);
    const scale=classifyPfu(pfu);
    const location=LOCATIONS[input.location]||LOCATIONS.deep;
    const environment=scale.rank===0?'Below NOAA S1 reference threshold':`${scale.scale} · ${scale.description}`;
    const crew=scale.rank===0
      ?'No NOAA solar-radiation-storm threshold crossed in this scenario.'
      :scale.rank<=2
        ?'Energetic-particle conditions warrant stronger radiation awareness and correlation with actual onboard/ground measurements.'
        :'A strong energetic-particle environment would make crew-radiation assessment an integrated mission-risk problem.';
    const electronics=scale.rank===0
      ?'Energetic-proton environment remains below the NOAA S1 reference threshold.'
      :scale.rank<=2
        ?'Single-event-effect vigilance becomes more relevant as energetic-particle flux rises.'
        :'High energetic-particle flux can materially increase concern for single-event effects and radiation-sensitive electronics.';
    const operations=scale.rank===0
      ?'MONITOR MEASUREMENTS + TREND'
      :scale.rank<=2
        ?'CORRELATE EVENT GROWTH + ONBOARD DATA'
        :'PRESERVE DECISION TIME + EVALUATE PROTECTIVE OPTIONS';
    return {
      log10Pfu,pfu,scale,location,environment,crew,electronics,operations,
      doseKnown:false,crewDose:null,
      doseText:'UNKNOWN FROM THIS CONTROL · proton flux is not absorbed dose or crew effective dose',
      shieldingText:'NO ORION SHIELDING DEPTH ASSUMED',
      noaaBoundary:'NOAA S-scale reference ≠ Artemis II flight rule',
      finite:Number.isFinite(pfu)&&Number.isFinite(log10Pfu)
    };
  }

  return {SCALES,LOCATIONS,MISSION_CONTEXT,pfuFromLog10,classifyPfu,formatPfu,evaluate};
});
