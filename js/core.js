(() => {
  'use strict';
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
  const lerp = (a,b,t) => a+(b-a)*t;
  const invLerp = (a,b,v) => (v-a)/(b-a);
  const ease = t => t<.5 ? 2*t*t : 1-Math.pow(-2*t+2,2)/2;
  const canvasRuntime = new WeakMap();
  const canvasRuntimeStates = new Set();

  function viewportProfile(w,h){
    const aspect=w/Math.max(1,h), landscape=aspect>1.22;
    if(w<=560 || (landscape && w<=950 && h<=500)) return landscape?'phone-landscape':'phone-portrait';
    if(w<=900) return landscape?'tablet-landscape':'tablet-portrait';
    if(w<=1180) return 'compact-desktop';
    return 'desktop';
  }
  function responsiveDpr(w,h){
    const raw=clamp(window.devicePixelRatio||1,1,3);
    const pixelBudget=w<=900?4_200_000:5_500_000;
    const budgeted=Math.sqrt(pixelBudget/Math.max(1,w*h));
    return clamp(Math.min(raw,budgeted),1,raw);
  }
  function ensureCanvasRuntime(canvas){
    let state=canvasRuntime.get(canvas);if(state)return state;
    state={canvas,w:1,h:1,dirty:true,observer:null};
    state.measure=()=>{const r=canvas.getBoundingClientRect();state.w=Math.max(1,r.width);state.h=Math.max(1,r.height);state.dirty=false;};
    state.measure();
    if('ResizeObserver' in window){
      state.observer=new ResizeObserver(entries=>{const box=entries[0]?.contentRect;if(box){state.w=Math.max(1,box.width);state.h=Math.max(1,box.height);state.dirty=false;}else state.dirty=true;});
      state.observer.observe(canvas);
    }
    canvasRuntime.set(canvas,state);canvasRuntimeStates.add(state);return state;
  }
  function invalidateCanvasLayouts(){canvasRuntimeStates.forEach(s=>s.dirty=true);}
  window.addEventListener('orientationchange',invalidateCanvasLayouts,{passive:true});
  window.visualViewport?.addEventListener('resize',invalidateCanvasLayouts,{passive:true});
  function syncViewportVars(){
    const vv=window.visualViewport;
    document.documentElement.style.setProperty('--a2-vvh',`${Math.round(vv?.height||innerHeight)}px`);
    document.documentElement.style.setProperty('--a2-vvw',`${Math.round(vv?.width||innerWidth)}px`);
  }
  function resyncResponsiveViewport(){
    syncViewportVars();
    invalidateCanvasLayouts();
  }
  function queueResponsiveViewportResync(){
    resyncResponsiveViewport();
    requestAnimationFrame(resyncResponsiveViewport);
    setTimeout(resyncResponsiveViewport,120);
    setTimeout(resyncResponsiveViewport,360);
  }
  syncViewportVars();
  window.addEventListener('resize',queueResponsiveViewportResync,{passive:true});
  window.addEventListener('orientationchange',queueResponsiveViewportResync,{passive:true});
  window.addEventListener('pageshow',queueResponsiveViewportResync,{passive:true});
  window.visualViewport?.addEventListener('resize',queueResponsiveViewportResync,{passive:true});
  screen.orientation?.addEventListener?.('change',queueResponsiveViewportResync);

  function fitCanvas(canvas){
    const state=ensureCanvasRuntime(canvas);if(state.dirty)state.measure();
    const w=state.w,h=state.h,d=responsiveDpr(w,h),bw=Math.max(1,Math.round(w*d)),bh=Math.max(1,Math.round(h*d));
    if(canvas.width!==bw||canvas.height!==bh){canvas.width=bw;canvas.height=bh;}
    const ctx=canvas.getContext('2d');ctx.setTransform(d,0,0,d,0,0);
    const profile=viewportProfile(w,h),aspect=w/Math.max(1,h);
    if(canvas.dataset.a2Profile!==profile)canvas.dataset.a2Profile=profile;
    const cssSize=`${Math.round(w)}x${Math.round(h)}`;if(canvas.dataset.a2CssSize!==cssSize)canvas.dataset.a2CssSize=cssSize;
    return {ctx,w,h,dpr:d,layout:{profile,aspect,portrait:aspect<.92,landscape:aspect>1.22,phone:profile.startsWith('phone'),tablet:profile.startsWith('tablet'),compact:profile!=='desktop'}};
  }
  function sceneRect(w,h,insets={},pad=0){
    const top=(insets.top||0)+pad,right=(insets.right||0)+pad,bottom=(insets.bottom||0)+pad,left=(insets.left||0)+pad;
    const x=left,y=top,width=Math.max(1,w-left-right),height=Math.max(1,h-top-bottom);
    return {x,y,width,height,right:x+width,bottom:y+height,cx:x+width/2,cy:y+height/2,min:Math.min(width,height)};
  }
  function scenePoint(scene,nx,ny){return{x:scene.x+scene.width*nx,y:scene.y+scene.height*ny};}

  function roundRect(ctx,x,y,w,h,r){r=Math.min(r,w/2,h/2);ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
  function drawStars(ctx,w,h,count,seed=1,alpha=.7){
    let s=seed>>>0; const rand=()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296};
    ctx.save();
    for(let i=0;i<count;i++){const x=rand()*w,y=rand()*h,r=rand()*1.25+.2,a=(rand()*.65+.18)*alpha;ctx.fillStyle=`rgba(255,255,255,${a})`;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();}
    ctx.restore();
  }
  const celestialImages={};
  let celestialLoaded=0;
  let celestialFailed=0;

  document.documentElement.dataset.a2Celestial='loading';

  function updateCelestialAssetState(){
    const total=2;
    const finished=celestialLoaded+celestialFailed;

    if(celestialLoaded===total){
      document.documentElement.dataset.a2Celestial='ready';
    }else if(finished===total){
      document.documentElement.dataset.a2Celestial=
        celestialLoaded>0?'partial':'fallback';
    }else{
      document.documentElement.dataset.a2Celestial='loading';
    }

    invalidateCanvasLayouts();

    requestAnimationFrame(()=>{
      window.dispatchEvent(
        new Event('resize')
      );
    });
  }

  function loadCelestialImage(name,src){
    const img=new Image();

    img.decoding='async';

    img.addEventListener(
      'load',
      ()=>{
        celestialLoaded++;
        updateCelestialAssetState();
      },
      {once:true}
    );

    img.addEventListener(
      'error',
      ()=>{
        celestialFailed++;
        updateCelestialAssetState();
      },
      {once:true}
    );

    img.src=src;

    celestialImages[name]=img;

    return img;
  }

  loadCelestialImage(
    'earth',
    'assets/public/celestial/earth_pia18033.jpg'
  );

  loadCelestialImage(
    'moon',
    'assets/public/celestial/moon_lro_mosaic.jpg'
  );

  function celestialImageReady(img){
    return Boolean(
      img &&
      img.complete &&
      img.naturalWidth>0 &&
      img.naturalHeight>0
    );
  }

  function drawCelestialImageDisk(
    ctx,
    img,
    x,
    y,
    r,
    sourceInset,
    body
  ){
    if(!celestialImageReady(img)){
      return false;
    }

    const naturalSize=
      Math.min(
        img.naturalWidth,
        img.naturalHeight
      );

    const baseX=
      (
        img.naturalWidth-
        naturalSize
      )/2;

    const baseY=
      (
        img.naturalHeight-
        naturalSize
      )/2;

    const inset=
      naturalSize*
      sourceInset;

    const sourceSize=
      naturalSize-
      inset*2;

    ctx.save();

    ctx.beginPath();
    ctx.arc(
      x,
      y,
      r,
      0,
      Math.PI*2
    );
    ctx.clip();

    ctx.drawImage(
      img,
      baseX+inset,
      baseY+inset,
      sourceSize,
      sourceSize,
      x-r,
      y-r,
      r*2,
      r*2
    );

    if(body==='earth'){

      const limb=
        ctx.createRadialGradient(
          x-r*.28,
          y-r*.3,
          r*.08,
          x+r*.06,
          y+r*.05,
          r*1.04
        );

      limb.addColorStop(
        0,
        'rgba(255,255,255,.05)'
      );

      limb.addColorStop(
        .54,
        'rgba(0,0,0,0)'
      );

      limb.addColorStop(
        .84,
        'rgba(0,8,18,.2)'
      );

      limb.addColorStop(
        1,
        'rgba(0,4,10,.67)'
      );

      ctx.fillStyle=limb;

      ctx.fillRect(
        x-r,
        y-r,
        r*2,
        r*2
      );

    }else{

      const lunarShade=
        ctx.createRadialGradient(
          x-r*.32,
          y-r*.34,
          r*.04,
          x+r*.12,
          y+r*.09,
          r*1.08
        );

      lunarShade.addColorStop(
        0,
        'rgba(255,255,255,.08)'
      );

      lunarShade.addColorStop(
        .48,
        'rgba(0,0,0,0)'
      );

      lunarShade.addColorStop(
        .82,
        'rgba(2,4,6,.16)'
      );

      lunarShade.addColorStop(
        1,
        'rgba(0,0,0,.58)'
      );

      ctx.fillStyle=lunarShade;

      ctx.fillRect(
        x-r,
        y-r,
        r*2,
        r*2
      );
    }

    ctx.restore();

    return true;
  }

  function drawEarthProcedural(ctx,x,y,r){
    ctx.save();
    const g=ctx.createRadialGradient(x-r*.35,y-r*.35,r*.08,x,y,r);g.addColorStop(0,'#7fc8ff');g.addColorStop(.42,'#2a78ac');g.addColorStop(.72,'#15415f');g.addColorStop(1,'#06111b');ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=.42;ctx.strokeStyle='#d8f0ff';ctx.lineWidth=Math.max(1,r*.025);for(let i=0;i<4;i++){ctx.beginPath();ctx.arc(x-r*.15+i*r*.1,y-r*.1+i*r*.09,r*(.34-i*.035),.15,1.75);ctx.stroke();}
    ctx.globalAlpha=1;ctx.strokeStyle='rgba(170,220,255,.32)';ctx.lineWidth=1;ctx.beginPath();ctx.arc(x,y,r+5,0,Math.PI*2);ctx.stroke();ctx.restore();
  }

  function drawMoonProcedural(ctx,x,y,r){
    ctx.save();const g=ctx.createRadialGradient(x-r*.35,y-r*.35,r*.05,x,y,r);g.addColorStop(0,'#d5d2cc');g.addColorStop(.5,'#8d8d8b');g.addColorStop(1,'#373a3c');ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();let s=22;const rand=()=>{s=(s*1103515245+12345)&0x7fffffff;return s/0x7fffffff};for(let i=0;i<22;i++){const a=rand()*Math.PI*2,rr=Math.sqrt(rand())*r*.8,cr=rand()*r*.11+r*.02,cx=x+Math.cos(a)*rr,cy=y+Math.sin(a)*rr;ctx.fillStyle='rgba(20,22,24,.22)';ctx.beginPath();ctx.arc(cx,cy,cr,0,Math.PI*2);ctx.fill();ctx.strokeStyle='rgba(255,255,255,.11)';ctx.beginPath();ctx.arc(cx-cr*.12,cy-cr*.15,cr*.8,0,Math.PI*2);ctx.stroke();}ctx.restore();
  }

  function drawEarth(ctx,x,y,r){
    if(
      !celestialImageReady(
        celestialImages.earth
      )
    ){
      drawEarthProcedural(
        ctx,
        x,
        y,
        r
      );
      return;
    }

    ctx.save();

    const glow=
      ctx.createRadialGradient(
        x,
        y,
        r*.82,
        x,
        y,
        r*1.2
      );

    glow.addColorStop(
      0,
      'rgba(69,160,222,0)'
    );

    glow.addColorStop(
      .72,
      'rgba(71,172,235,.09)'
    );

    glow.addColorStop(
      1,
      'rgba(71,172,235,0)'
    );

    ctx.fillStyle=glow;

    ctx.beginPath();
    ctx.arc(
      x,
      y,
      r*1.2,
      0,
      Math.PI*2
    );
    ctx.fill();

    drawCelestialImageDisk(
      ctx,
      celestialImages.earth,
      x,
      y,
      r,
      .048,
      'earth'
    );

    ctx.strokeStyle=
      'rgba(126,203,250,.35)';

    ctx.lineWidth=
      Math.max(
        1,
        r*.018
      );

    ctx.beginPath();
    ctx.arc(
      x,
      y,
      r+1,
      0,
      Math.PI*2
    );
    ctx.stroke();

    ctx.restore();
  }

  function drawMoon(ctx,x,y,r){
    if(
      !celestialImageReady(
        celestialImages.moon
      )
    ){
      drawMoonProcedural(
        ctx,
        x,
        y,
        r
      );
      return;
    }

    ctx.save();

    const glow=
      ctx.createRadialGradient(
        x,
        y,
        r*.9,
        x,
        y,
        r*1.16
      );

    glow.addColorStop(
      0,
      'rgba(214,220,224,0)'
    );

    glow.addColorStop(
      .65,
      'rgba(214,220,224,.055)'
    );

    glow.addColorStop(
      1,
      'rgba(214,220,224,0)'
    );

    ctx.fillStyle=glow;

    ctx.beginPath();
    ctx.arc(
      x,
      y,
      r*1.16,
      0,
      Math.PI*2
    );
    ctx.fill();

    drawCelestialImageDisk(
      ctx,
      celestialImages.moon,
      x,
      y,
      r,
      .012,
      'moon'
    );

    ctx.strokeStyle=
      'rgba(220,225,228,.18)';

    ctx.lineWidth=
      Math.max(
        .8,
        r*.012
      );

    ctx.beginPath();
    ctx.arc(
      x,
      y,
      r,
      0,
      Math.PI*2
    );
    ctx.stroke();

    ctx.restore();
  }

  function bezier(p0,p1,p2,t){const u=1-t;return{x:u*u*p0.x+2*u*t*p1.x+t*t*p2.x,y:u*u*p0.y+2*u*t*p1.y+t*t*p2.y};}
  function drawCanvasLabel(ctx,text,x,y,maxWidth,opts={}){
    const size=opts.size??12,minSize=opts.minSize??10,weight=opts.weight??700,align=opts.align??'left',color=opts.color??'rgba(255,255,255,.68)',lineHeight=opts.lineHeight??1.18,maxLines=opts.maxLines??2;
    const canvasW=ctx.canvas.width/(ctx.getTransform().a||1),canvasH=ctx.canvas.height/(ctx.getTransform().d||1),margin=opts.margin??8;
    ctx.save();ctx.fillStyle=color;ctx.textAlign=align;ctx.textBaseline=opts.baseline??'alphabetic';
    let px=size,lines=[String(text)],limit=Math.max(24,maxWidth);
    const wrap=()=>{
      ctx.font=`${weight} ${px}px system-ui`;
      const words=String(text).split(/\s+/),out=[];let line='';
      for(const word of words){const test=line?`${line} ${word}`:word;if(ctx.measureText(test).width<=limit||!line)line=test;else{out.push(line);line=word;}}
      if(line)out.push(line);return out;
    };
    while(px>minSize){lines=wrap();if(lines.length<=maxLines&&lines.every(v=>ctx.measureText(v).width<=limit))break;px-=.5;}
    lines=wrap();if(lines.length>maxLines){lines=lines.slice(0,maxLines);let last=lines[maxLines-1];while(last.length>1&&ctx.measureText(last+'…').width>limit)last=last.slice(0,-1);lines[maxLines-1]=last+'…';}
    ctx.font=`${weight} ${px}px system-ui`;
    const widest=Math.min(limit,Math.max(...lines.map(v=>ctx.measureText(v).width),0));
    let drawX=x;if(align==='left')drawX=clamp(x,margin,canvasW-margin-widest);else if(align==='right')drawX=clamp(x,margin+widest,canvasW-margin);else drawX=clamp(x,margin+widest/2,canvasW-margin-widest/2);
    const lh=px*lineHeight,total=(lines.length-1)*lh;let drawY=clamp(y,margin+px,canvasH-margin-total);
    lines.forEach((line,i)=>ctx.fillText(line,drawX,drawY+i*lh));ctx.restore();
  }

  // Shared chrome.
  const header=$('.x-header');
  if(header){window.addEventListener('scroll',()=>header.classList.toggle('scrolled',scrollY>18),{passive:true});}
  const setupDisclosureNav=(menu,nav)=>{
    if(!menu||!nav)return;
    const setOpen=(open,{returnFocus=false}={})=>{
      nav.classList.toggle('open',open);
      menu.setAttribute('aria-expanded',String(open));
      if(returnFocus){try{menu.focus({preventScroll:true});}catch{menu.focus();}}
    };
    menu.addEventListener('click',()=>setOpen(!nav.classList.contains('open')));
    $$('a',nav).forEach(a=>a.addEventListener('click',()=>setOpen(false)));
    document.addEventListener('keydown',event=>{
      if(event.key==='Escape'&&nav.classList.contains('open')){
        event.preventDefault();
        setOpen(false,{returnFocus:true});
      }
    });
  };
  setupDisclosureNav($('.x-menu'),$('.x-nav'));
  setupDisclosureNav($('.menu-btn'),$('.nav-links'));

  // Remote NASA imagery fails safely into repository-local technical imagery.
  $$('.nasa-photo').forEach(img=>{
    img.addEventListener('error',()=>{
      const fb=img.dataset.fallback;
      if(fb && !img.dataset.didFallback){img.dataset.didFallback='1';img.classList.add('is-fallback');img.src=fb;img.alt += ' — NASA image unavailable; MissionLab local figure substituted';}
    });
  });

  // Hero star shimmer.
  const heroCanvas=$('#hero-stars');
  if(heroCanvas){
    const stars=Array.from({length:80},(_,i)=>({x:(i*47.31)%997/997,y:(i*83.17)%991/991,r:.35+(i%7)*.09,p:i*.63}));
    const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
    let heroFrame=0;
    const paint=t=>{const {ctx,w,h}=fitCanvas(heroCanvas);ctx.clearRect(0,0,w,h);stars.forEach(s=>{const a=.12+.34*(.5+.5*Math.sin(t*.001+s.p));ctx.fillStyle=`rgba(255,255,255,${a})`;ctx.beginPath();ctx.arc(s.x*w,s.y*h,s.r,0,Math.PI*2);ctx.fill();});};
    const animate=t=>{heroFrame=0;paint(t);if(!reducedMotion.matches&&!document.hidden)heroFrame=requestAnimationFrame(animate);};
    const syncHeroMotion=()=>{if(heroFrame){cancelAnimationFrame(heroFrame);heroFrame=0;}if(reducedMotion.matches||document.hidden)paint(0);else heroFrame=requestAnimationFrame(animate);};
    reducedMotion.addEventListener?.('change',syncHeroMotion);
    document.addEventListener('visibilitychange',syncHeroMotion);
    addEventListener('resize',()=>{if(reducedMotion.matches)paint(0);},{passive:true});
    syncHeroMotion();
  }


  window.A2 = Object.freeze({
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
  });

})();
