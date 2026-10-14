(function(root,factory){
  'use strict';
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  if(root) root.A2PsiModel=Object.freeze(api);
})(typeof window!=='undefined'?window:null,function(){
  'use strict';
  const rad=d=>d*Math.PI/180;
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const DEFAULTS=Object.freeze({altitude:18,throttle:55,cant:6,spread:14,engines:2,regolith:'reference',hardwareDistance:35});
  const surfaceClasses=Object.freeze({
    resistant:Object.freeze({label:'More resistant',multiplier:.65}),
    reference:Object.freeze({label:'Reference',multiplier:1}),
    erodible:Object.freeze({label:'More erodible',multiplier:1.45})
  });
  function coneFootprint(input){
    const h=input.altitude,theta=rad(input.cant),alpha=rad(input.spread);
    const axis={x:Math.sin(theta),y:0,z:-Math.cos(theta)};
    const b={x:Math.cos(theta),y:0,z:Math.sin(theta)};
    const c={x:0,y:1,z:0};
    const points=[],count=240;
    for(let i=0;i<count;i++){
      const phi=2*Math.PI*i/count,cp=Math.cos(phi),sp=Math.sin(phi);
      const dx=Math.cos(alpha)*axis.x+Math.sin(alpha)*(cp*b.x+sp*c.x);
      const dy=Math.cos(alpha)*axis.y+Math.sin(alpha)*(cp*b.y+sp*c.y);
      const dz=Math.cos(alpha)*axis.z+Math.sin(alpha)*(cp*b.z+sp*c.z);
      if(dz>=-.00001) continue;
      const t=h/(-dz);points.push({x:t*dx,y:t*dy});
    }
    let twiceArea=0,cxNum=0,cyNum=0;
    for(let i=0;i<points.length;i++){
      const p=points[i],q=points[(i+1)%points.length],cross=p.x*q.y-q.x*p.y;
      twiceArea+=cross;cxNum+=(p.x+q.x)*cross;cyNum+=(p.y+q.y)*cross;
    }
    const area=Math.abs(twiceArea/2),denom=3*twiceArea;
    const centroid={x:Math.abs(denom)>1e-9?cxNum/denom:0,y:Math.abs(denom)>1e-9?cyNum/denom:0};
    const xs=points.map(p=>p.x),ys=points.map(p=>p.y),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
    return {points,area,centroid,minX,maxX,minY,maxY,width:maxX-minX,crossWidth:maxY-minY,equivalentRadius:Math.sqrt(area/Math.PI),axisIntersection:h*Math.tan(theta),slant:h/Math.cos(theta)};
  }
  const referenceArea=coneFootprint(DEFAULTS).area;
  const referenceLoading=DEFAULTS.engines*(DEFAULTS.throttle/100)/referenceArea;
  function compute(patch={}){
    const input={...DEFAULTS,...patch};
    const footprint=coneFootprint(input),loadingRaw=input.engines*(input.throttle/100)/footprint.area,loadingRatio=loadingRaw/referenceLoading;
    const surface=surfaceClasses[input.regolith]||surfaceClasses.reference,erosionRatio=loadingRatio*surface.multiplier,clearance=input.hardwareDistance-footprint.maxX;
    const screeningBand=footprint.equivalentRadius*clamp(.45+.42*Math.sqrt(Math.max(0,erosionRatio)),.65,1.6);
    let hardwareLevel='clear',hardwareTitle='Outside ideal plume footprint';
    if(clearance<=0){hardwareLevel='direct';hardwareTitle='Inside ideal plume footprint';}
    else if(clearance<screeningBand){hardwareLevel='near';hardwareTitle='Near modeled disturbance region';}
    let erosionLabel='Lower';if(erosionRatio>=.75)erosionLabel='Reference';if(erosionRatio>=1.35)erosionLabel='Elevated';if(erosionRatio>=2.4)erosionLabel='High relative';
    let visibility='Lower obscuration tendency';if(erosionRatio>=.75)visibility='Moderate obscuration tendency';if(erosionRatio>=1.45)visibility='Elevated obscuration tendency';if(erosionRatio>=2.6)visibility='High relative obscuration tendency';
    return {input,footprint,loadingRatio,erosionRatio,erosionLabel,visibility,clearance,screeningBand,hardwareLevel,hardwareTitle,surface};
  }
  function serializable(m){return {area:m.footprint.area,centroidX:m.footprint.centroid.x,minX:m.footprint.minX,maxX:m.footprint.maxX,crossWidth:m.footprint.crossWidth,equivalentRadius:m.footprint.equivalentRadius,axisIntersection:m.footprint.axisIntersection,loadingRatio:m.loadingRatio,erosionRatio:m.erosionRatio,erosionLabel:m.erosionLabel,visibility:m.visibility,clearance:m.clearance,hardwareLevel:m.hardwareLevel,hardwareTitle:m.hardwareTitle};}
  return {DEFAULTS,surfaceClasses,coneFootprint,compute,serializable};
});
