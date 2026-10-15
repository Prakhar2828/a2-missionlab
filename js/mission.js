(() => {
  'use strict';

  if (!window.A2) {
    throw new Error('A2 MissionLab core runtime must load before experience runtimes.');
  }

  const staticMissionQa = /(?:^|[?&])(?:trajectory-qa|space-weather-qa|entry-qa)=1(?:&|$)/.test(window.location.search);

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

  // Mission explorer.
  if ($('#mission-explorer')) {
  const missionCanvas=$('#mission-canvas');
  const missionMoments=[
    {p:0,date:'APR 01 · FLIGHT DAY 1',title:'Launch from Kennedy Space Center',phase:'Launch',met:'00:00:00:00',comm:'Near-Earth network',copy:'The shared mission clock begins at 22:35:12 UTC. MissionLab uses this epoch to align public trajectory products, events, science observations, and engineering analyses.',aL:'Distance context',a:'Earth departure',bL:'Evidence',b:'NASA reported',caption:'Orion begins the first crewed Artemis lunar flyby mission.'},
    {p:.13,date:'APR 02 · OUTBOUND',title:'Earth gets smaller. Navigation changes with distance.',phase:'Outbound coast',met:'00:18:32:00',comm:'Network transition',copy:'After Earth-orbit checkout and translunar departure, Orion coasts outward. Near Earth, GPS can contribute. Deeper in space, onboard sensors and ground tracking become more important.',aL:'Navigation idea',a:'Near-Earth → deep-space',bL:'MissionLab',b:'Public architecture reconstruction',caption:'A long coast magnifies the effect of even small velocity errors.'},
    {p:.28,date:'APR 04 · FLIGHT DAY 4',title:'The crew manually pilots Orion.',phase:'Manual piloting',met:'02:18:00:00',comm:'Deep-space link',copy:'Artemis II included manual-control demonstrations. Rotation Hand Controller inputs command attitude motion; Translation Hand Controller inputs command translational motion. MissionLab reconstructs the public architecture without inventing private control laws.',aL:'Control modes',a:'3-DOF / 6-DOF context',bL:'Human interface',b:'RHC + THC',caption:'The GNC lab below lets you experiment with the difference between rotation and translation.'},
    {p:.45,date:'APR 06 · LUNAR APPROACH',title:'Orion enters the Moon’s sphere of influence.',phase:'Lunar approach',met:'04:06:02:56',comm:'DSN support',copy:'MissionLab derives lunar SOI entry at 04:38:07 UTC. The spacecraft is now in the part of the flight where Moon-relative geometry becomes the natural way to reason about the path.',aL:'Inside selected SOI',a:'~36.76 hours',bL:'Evidence',b:'MissionLab derived',caption:'The Moon now dominates the local geometry used in the reconstruction.'},
    {p:.54,date:'APR 06 · 22:41 UTC',title:'Earthset. Then the Moon blocks the radio path.',phase:'Earthset / occultation',met:'05:00:05:48',comm:'Loss of signal approaching',copy:'The crew photographs Earth sinking behind the lunar limb. Minutes later, lunar terrain blocks line of sight to Earth. That planned loss of signal is a geometry constraint, not evidence of a spacecraft failure.',aL:'Derived occultation',a:'~36.57 minutes',bL:'NASA ops window',b:'~41 minutes',caption:'Earthset and communications occultation are two views of the same changing geometry.'},
    {p:.585,date:'APR 06 · 23:00:46 UTC',title:'Closest approach to the Moon.',phase:'Pericynthion',met:'05:00:25:34',comm:'Behind the Moon',copy:'MissionLab refines closest approach to a Moon-center distance of 8,281.938 km, corresponding to a mean-radius altitude of 6,544.538 km and Moon-relative speed of about 1.381073 km/s.',aL:'Mean-radius altitude',a:'6,544.538 km',bL:'Moon-relative speed',b:'1.381073 km/s',caption:'This closest-approach time is derived from public trajectory data, not private telemetry.'},
    {p:.63,date:'APR 06 · 23:22 UTC',title:'Earthrise. Contact returns.',phase:'Earthrise / reacquisition',met:'05:00:46:48',comm:'Reacquiring',copy:'Earth reappears from behind the lunar limb. NASA’s public operational reference planned acquisition near 23:25 UTC; the geometry model and the operational window are related but not identical.',aL:'Why different?',a:'Earth center ≠ DSN antenna',bL:'Evidence rule',b:'Geometry ≠ link margin',caption:'Topocentric DSN geometry improves on a simple Earth-center line-of-sight test.'},
    {p:.69,date:'APR 07 · 00:34 UTC',title:'A solar eclipse lasts almost 54 minutes.',phase:'Lunar eclipse',met:'05:01:59:15',comm:'Deep-space link',copy:'From Orion’s moving vantage point, the Moon completely covers the Sun for an unusually long interval. MissionLab derives the eclipse window from public spacecraft and body geometry.',aL:'Derived duration',a:'~54.43 minutes',bL:'Science context',b:'Crew photography',caption:'The lunar flyby became a rare human-observation platform as well as a spacecraft test.'},
    {p:.78,date:'APR 08–10 · RETURN',title:'Small correction burns protect the path home.',phase:'Return corrections',met:'06:01:27:48',comm:'Deep-space link',copy:'RTC1, RTC2, and RTC3 make small velocity changes. Over many hours of coast, those changes protect the future entry geometry. The trajectory lab below propagates an educational two-body correction response without pretending to reproduce NASA’s targeting solution.',aL:'Largest listed RTC',a:'RTC2 · ~5.3 ft/s',bL:'Operations',b:'Target future geometry',caption:'Targeting is about where a tiny velocity change places the spacecraft later.'},
    {p:.91,date:'APR 10 · 23:53 UTC',title:'Entry interface. The atmosphere becomes the engine.',phase:'Atmospheric entry',met:'09:01:17:48',comm:'Entry link / blackout',copy:'Orion reaches the public Entry Interface minute. Drag begins converting lunar-return kinetic energy into heating, atmospheric motion, and deceleration. Plasma can temporarily disrupt communications.',aL:'Physics',a:'Drag + heating',bL:'Model',b:'Atmosphere + Sutton–Graves',caption:'Entry is where trajectory, atmosphere, thermal protection, communications, and recovery converge.'},
    {p:1,date:'APR 11 · 00:07 UTC',title:'Splashdown. Then recovery begins.',phase:'Splashdown',met:'09:01:31:48',comm:'Recovered',copy:'Drogues, main parachutes, splashdown, crew extraction, and spacecraft recovery close the flight. MissionLab keeps those public events connected to the entry and environmental data rather than treating splashdown as the end of the engineering story.',aL:'Mission outcome',a:'Crew safely home',bL:'Next phase',b:'Recovery + postflight',caption:'Nearly ten days of flight end in the Pacific; engineering analysis continues.'}
  ];
  let missionP=0;
  let missionMoment=null;
  const missionReducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
  let refreshMissionCanvas=()=>{};
  const missionMarkerIndexes=[0,3,4,5,8,10];

  function missionNearest(p){
    return missionMoments.reduce(
      (best,m)=>
        Math.abs(m.p-p)<
        Math.abs(best.p-p)
          ?m
          :best,
      missionMoments[0]
    );
  }

  function missionIndex(){
    return missionMoments.indexOf(
      missionNearest(
        missionP
      )
    );
  }

  function updateMission(
    p,
    snap=false
  ){
    missionP=clamp(
      p,
      0,
      1
    );

    const m=
      missionNearest(
        missionP
      );

    const momentChanged=
      missionMoment!==m;

    missionMoment=m;

    if(snap){
      missionP=m.p;
    }

    const ids={
      date:'mission-date',
      title:'mission-title',
      copy:'mission-copy',
      met:'mission-met',
      phase:'mission-phase',
      comm:'mission-comm',
      caption:'mission-stage-caption',
      aL:'mission-readout-a-label',
      a:'mission-readout-a',
      bL:'mission-readout-b-label',
      b:'mission-readout-b'
    };

    Object.entries(
      ids
    ).forEach(
      ([key,id])=>{
        const element=
          $('#'+id);

        if(element){
          element.textContent=
            m[key];
        }
      }
    );

    const scrubber=
      $('#mission-scrubber');

    if(scrubber){
      scrubber.value=
        String(
          Math.round(
            missionP*1000
          )
        );

      scrubber.setAttribute(
        'aria-valuetext',
        `${m.date}: ${m.phase}`
      );
    }

    $$('#mission-markers button')
      .forEach(
        button=>{
          const active=
            Math.abs(
              Number(
                button.dataset.p
              )-
              missionP
            )<.055;

          button.classList.toggle(
            'active',
            active
          );

          if(active){
            button.setAttribute(
              'aria-current',
              'step'
            );
          }else{
            button.removeAttribute(
              'aria-current'
            );
          }
        }
      );

    const previous=
      $('#mission-prev');

    const next=
      $('#mission-next');

    if(previous){
      previous.disabled=
        missionP<=
        missionMoments[0].p+
        1e-6;
    }

    if(next){
      next.disabled=
        missionP>=
        missionMoments[
          missionMoments.length-1
        ].p-
        1e-6;
    }

    if(momentChanged){
      const story=
        $('#mission-story-copy');

      if(story){
        requestAnimationFrame(
          ()=>{
            story.scrollTop=0;
          }
        );
      }
    }

    refreshMissionCanvas();
  }

  function goMissionPrevious(){
    const previous=
      [...missionMoments]
        .reverse()
        .find(
          moment=>
            moment.p<
            missionP-.02
        )
      ||
      missionMoments[0];

    updateMission(
      previous.p,
      true
    );
  }

  function goMissionNext(){
    const next=
      missionMoments
        .find(
          moment=>
            moment.p>
            missionP+.02
        )
      ||
      missionMoments[
        missionMoments.length-1
      ];

    updateMission(
      next.p,
      true
    );
  }

  function setMissionIndex(
    index
  ){
    const safeIndex=
      clamp(
        Math.round(
          Number(index)||0
        ),
        0,
        missionMoments.length-1
      );

    updateMission(
      missionMoments[
        safeIndex
      ].p,
      true
    );
  }

  function initMission(){
    const markers=
      $('#mission-markers');

    if(markers){
      markers.innerHTML=
        missionMarkerIndexes
          .map(
            index=>{
              const moment=
                missionMoments[
                  index
                ];

              return (
                `<button type="button" `
                +`data-p="${moment.p}" `
                +`aria-label="Jump to ${moment.phase}">`
                +`${moment.phase}</button>`
              );
            }
          )
          .join('');

      $$(
        'button',
        markers
      ).forEach(
        button=>
          button.addEventListener(
            'click',
            ()=>{
              updateMission(
                Number(
                  button.dataset.p
                ),
                true
              );
            }
          )
      );
    }

    const scrubber=
      $('#mission-scrubber');

    if(scrubber){
      scrubber.addEventListener(
        'input',
        event=>
          updateMission(
            Number(
              event.target.value
            )/1000
          )
      );
    }

    $('#mission-prev')
      ?.addEventListener(
        'click',
        goMissionPrevious
      );

    $('#mission-next')
      ?.addEventListener(
        'click',
        goMissionNext
      );

    updateMission(
      0,
      true
    );
  }

  window.A2MissionExplorer=
    Object.freeze({
      count:()=>
        missionMoments.length,

      index:()=>
        missionIndex(),

      position:()=>
        missionP,

      set:
        setMissionIndex,

      next:
        goMissionNext,

      prev:
        goMissionPrevious
    });

  initMission();
  if(missionCanvas){
    let missionFrame=0;
    let missionInView=true;

    const loop=t=>{const {ctx,w,h,layout}=fitCanvas(missionCanvas);ctx.clearRect(0,0,w,h);drawStars(ctx,w,h,layout.compact?105:150,13,.72);
      const portrait=layout.profile==='phone-portrait',landPhone=layout.profile==='phone-landscape';
      const scene=sceneRect(w,h,{top:portrait?16:landPhone?14:18,bottom:portrait?16:landPhone?14:22},portrait?10:14);
      const earth=portrait?{...scenePoint(scene,.19,.69),r:scene.min*.105}:landPhone?{...scenePoint(scene,.16,.61),r:scene.min*.09}:{...scenePoint(scene,.16,.56),r:scene.min*.092};
      const moon=portrait?{...scenePoint(scene,.76,.46),r:scene.min*.13}:landPhone?{...scenePoint(scene,.81,.50),r:scene.min*.11}:{...scenePoint(scene,.82,.47),r:scene.min*.115};
      drawEarth(ctx,earth.x,earth.y,earth.r);drawMoon(ctx,moon.x,moon.y,moon.r);
      const out0={x:earth.x+earth.r*.72,y:earth.y-earth.r*.2},out1=portrait?scenePoint(scene,.43,.05):scenePoint(scene,.47,.05),out2={x:moon.x-moon.r*.7,y:moon.y};
      const ret0={x:moon.x-moon.r*.56,y:moon.y+moon.r*.1},ret1=portrait?scenePoint(scene,.56,.96):scenePoint(scene,.58,.94),ret2={x:earth.x+earth.r*.66,y:earth.y+earth.r*.25};
      ctx.save();ctx.strokeStyle='rgba(127,197,255,.30)';ctx.lineWidth=1.35;ctx.setLineDash([4,7]);ctx.beginPath();ctx.moveTo(out0.x,out0.y);ctx.quadraticCurveTo(out1.x,out1.y,out2.x,out2.y);ctx.quadraticCurveTo(ret1.x,ret1.y,ret2.x,ret2.y);ctx.stroke();ctx.restore();
      let pos;if(missionP<=.6)pos=bezier(out0,out1,out2,missionP/.6);else pos=bezier(ret0,ret1,ret2,(missionP-.6)/.4);
      ctx.save();ctx.shadowColor='#d9f2ff';ctx.shadowBlur=12;ctx.fillStyle='#f7fbff';ctx.beginPath();ctx.arc(pos.x,pos.y,layout.phone?3.8:4.2,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;ctx.strokeStyle='rgba(255,255,255,.55)';ctx.beginPath();ctx.arc(pos.x,pos.y,9+Math.sin(t*.004)*2,0,Math.PI*2);ctx.stroke();ctx.restore();
      drawCanvasLabel(ctx,'EARTH',earth.x,earth.y+earth.r+18,portrait?70:95,{size:portrait?10:12,minSize:10,align:'center',color:'rgba(255,255,255,.7)',maxLines:1});
      drawCanvasLabel(ctx,'MOON',moon.x,moon.y+moon.r+18,portrait?70:95,{size:portrait?10:12,minSize:10,align:'center',color:'rgba(255,255,255,.7)',maxLines:1});
      if(!portrait){drawCanvasLabel(ctx,'OUTBOUND',scene.x+scene.width*.36,scene.y+scene.height*.13,120,{size:11,minSize:10,color:'rgba(127,197,255,.78)',maxLines:1});drawCanvasLabel(ctx,'RETURN',scene.x+scene.width*.50,scene.y+scene.height*.91,110,{size:11,minSize:10,color:'rgba(112,198,156,.8)',maxLines:1});}
      const iw=portrait?Math.min(150,scene.width*.45):Math.min(220,scene.width*.31),ih=portrait?104:Math.min(150,scene.height*.34),ix=portrait?scene.right-iw:scene.right-iw,iy=portrait?scene.y+8:scene.y+4;
      ctx.save();ctx.fillStyle='rgba(3,8,13,.88)';ctx.strokeStyle='rgba(255,255,255,.16)';ctx.fillRect(ix,iy,iw,ih);ctx.strokeRect(ix,iy,iw,ih);const imx=ix+iw*.54,imy=iy+ih*.53,imr=Math.min(iw,ih)*.21;drawMoon(ctx,imx,imy,imr);ctx.strokeStyle='rgba(127,197,255,.58)';ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(ix+iw*.12,iy+ih*.72);ctx.bezierCurveTo(ix+iw*.29,iy+ih*.18,ix+iw*.68,iy+ih*.14,ix+iw*.88,iy+ih*.67);ctx.stroke();ctx.fillStyle='rgba(255,255,255,.9)';const lp=clamp((missionP-.47)/.20,0,1),lpos=bezier({x:ix+iw*.12,y:iy+ih*.72},{x:ix+iw*.42,y:iy+ih*.05},{x:ix+iw*.88,y:iy+ih*.67},lp);ctx.beginPath();ctx.arc(lpos.x,lpos.y,3,0,Math.PI*2);ctx.fill();ctx.strokeStyle='rgba(255,104,93,.56)';ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(ix+iw*.07,imy);ctx.lineTo(imx-imr*.25,imy);ctx.stroke();ctx.setLineDash([]);drawCanvasLabel(ctx,'LUNAR FLYBY INSET',ix+8,iy+15,iw-16,{size:portrait?9.5:11,minSize:9,color:'rgba(255,255,255,.72)',maxLines:1});if(portrait&&w<350){
        ctx.fillStyle='rgba(3,8,13,.94)';
        ctx.fillRect(ix+1,iy+ih-35,iw-2,34);
        drawCanvasLabel(ctx,'FAR SIDE /',ix+8,iy+ih-20,iw-16,{size:10,minSize:10,color:'rgba(255,255,255,.78)',maxLines:1});
        drawCanvasLabel(ctx,'LOS BLOCKED',ix+8,iy+ih-8,iw-16,{size:10,minSize:10,color:'rgba(255,255,255,.78)',maxLines:1});
      }else{
        drawCanvasLabel(ctx,'FAR SIDE / LOS BLOCKED',ix+8,portrait?iy+ih-25:iy+ih-9,iw-16,{size:portrait?9:10.5,minSize:9,color:'rgba(255,255,255,.68)',maxLines:portrait?2:1});
      }ctx.restore();
      if(missionP>.515&&missionP<.635){ctx.save();ctx.strokeStyle='rgba(255,104,93,.72)';ctx.setLineDash([3,5]);ctx.beginPath();ctx.moveTo(pos.x,pos.y);ctx.lineTo(earth.x,earth.y);ctx.stroke();ctx.setLineDash([]);drawCanvasLabel(ctx,'LUNAR OCCULTATION REGION',portrait?scene.x+8:scene.x+scene.width*.45,portrait?scene.bottom-18:scene.y+scene.height*.61,portrait?scene.width*.64:scene.width*.5,{size:portrait?10:11,minSize:10,color:'rgba(255,104,93,.92)',maxLines:portrait?2:1});ctx.restore();}
      missionFrame=0;
      const shouldAnimate=!staticMissionQa&&!missionReducedMotion.matches&&!document.hidden&&missionInView;
      missionCanvas.dataset.a2Animation=shouldAnimate?'running':'paused';
      if(shouldAnimate)missionFrame=requestAnimationFrame(loop);
    };

    refreshMissionCanvas=()=>{
      if(missionFrame){cancelAnimationFrame(missionFrame);missionFrame=0;}
      const shouldAnimate=!staticMissionQa&&!missionReducedMotion.matches&&!document.hidden&&missionInView;
      missionCanvas.dataset.a2Animation=shouldAnimate?'running':'paused';
      if(shouldAnimate)missionFrame=requestAnimationFrame(loop);else loop(0);
    };

    if('IntersectionObserver' in window){
      new IntersectionObserver(entries=>{
        missionInView=entries[0]?.isIntersecting!==false;
        refreshMissionCanvas();
      },{rootMargin:'180px'}).observe(missionCanvas);
    }

    missionReducedMotion.addEventListener?.('change',refreshMissionCanvas);
    document.addEventListener('visibilitychange',refreshMissionCanvas);
    window.addEventListener('a2:celestialchange',refreshMissionCanvas);
    refreshMissionCanvas();
  }

  }


})();
