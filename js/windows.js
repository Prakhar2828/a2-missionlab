(() => {
  'use strict';

  if (!window.A2) {
    throw new Error('A2 MissionLab core runtime must load before experience runtimes.');
  }

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

  // Crew observation journey — photography plus geometry, with provenance labels.
  if ($('#crew-view')) {
  const crewViews=[{"id":"art002e023506","badge":"OUTBOUND · EARTH VIEW","title":"Earth begins to fall away.","desc":"Artemis II crew photography from the journey to the Moon shows Earth isolated against black space after translunar injection. This is mission-phase imagery, not a claimed frame at a reconstructed state-vector timestamp.","notice":"The planet is still visually dominant, but the mission has already shifted from near-Earth operations into deep-space navigation and communications.","why":"The changing apparent size of Earth makes the scale of translunar flight intuitive and sets up why small navigation errors can matter hours later.","time":"Apr 2 · outbound coast","geometry":"Earth receding","evidence":"NASA crew imagery","provenance":"MISSION-PHASE CREW PHOTOGRAPHY","earth":0.96,"moon":0.03,"source":"https://www.nasa.gov/gallery/journey-to-the-moon/"},{"id":"art002e023710","badge":"OUTBOUND · DEEP SPACE","title":"Home becomes a thin illuminated edge.","desc":"NASA identifies this April 3 Artemis II image as a sliver of Earth brightly illuminated against deep space during the outbound journey.","notice":"The crew is no longer looking at Earth as a nearby horizon. It is becoming a compact body with a changing phase and line-of-sight geometry.","why":"This is the visual transition from Earth departure to true cislunar flight.","time":"Apr 3 · outbound coast","geometry":"Earth phase changing","evidence":"NASA exact mission image","provenance":"EXACT MISSION IMAGE · NASA IDENTIFIED","earth":0.82,"moon":0.06,"source":"https://www.nasa.gov/gallery/journey-to-the-moon/"},{"id":"art002e014225","badge":"APPROACH · CRESCENT EARTH","title":"Earth becomes a delicate crescent.","desc":"NASA describes Earth in this Artemis II image as a small waning crescent suspended in darkness during the lunar-flyby phase.","notice":"Earth is now a distant reference rather than the scene around the spacecraft.","why":"Human perception makes the Earth–Moon distance emotionally obvious in a way a single distance number cannot.","time":"Apr 6 · lunar-flyby day","geometry":"Distant crescent Earth","evidence":"NASA crew imagery","provenance":"EXACT MISSION IMAGE · NASA GALLERY","earth":0.58,"moon":0.18,"source":"https://www.nasa.gov/gallery/lunar-flyby/"},{"id":"art002e009582","badge":"APPROACH · BROAD LUNAR VIEW","title":"The Moon stops being a dot and becomes terrain.","desc":"NASA’s lunar-flyby gallery includes this broad illuminated view as the crew closes on the Moon and begins the observation period.","notice":"Large-scale albedo differences, maria, crater rays, and the day–night boundary become visible together.","why":"The crew’s science task changes from “find the Moon” to “identify, compare, and describe specific geologic targets.”","time":"Apr 6 · before closest approach","geometry":"Moon angular size increasing","evidence":"NASA exact mission image","provenance":"EXACT MISSION IMAGE · FLYBY PERIOD","earth":0.28,"moon":0.68,"source":"https://www.nasa.gov/gallery/lunar-flyby/"},{"id":"art002e009294","badge":"SCIENCE PREP · EXACT IMAGE","title":"The observation window had to be prepared before the Moon arrived.","desc":"NASA identifies this image as Victor Glover, Reid Wiseman, and Jeremy Hansen configuring camera equipment shortly before lunar-flyby observations.","notice":"Cameras, lenses, window geometry, target lists, and crew positions had to come together during a limited observation period.","why":"Science return depends on operations design: the vehicle must be in the right geometry and the crew must be ready to use it.","time":"Apr 6 · before observations","geometry":"Observation setup inside Orion","evidence":"NASA exact mission image","provenance":"EXACT MISSION IMAGE · NASA IDENTIFIED","earth":0.34,"moon":0.54,"source":"https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/"},{"id":"art002e009293","badge":"CREW SCIENCE · EXACT IMAGE","title":"The crew turns a fleeting view into science data.","desc":"NASA imagery shows Artemis II crew members actively gathering lunar images and observations during the seven-hour flyby science period.","notice":"The astronauts could call out color, brightness, texture, layering, and unexpected features while simultaneously capturing imagery for later analysis.","why":"NASA’s science team used those real-time observations to refine follow-up guidance, demonstrating how human perception can influence an observation plan while it is underway.","time":"Apr 6 · lunar science period","geometry":"Crew observation workflow","evidence":"NASA exact mission image","provenance":"EXACT MISSION IMAGE · CREW OBSERVATION","earth":0.22,"moon":0.76,"source":"https://www.nasa.gov/blogs/missions/2026/04/06/artemis-ii-flight-day-6-lunar-flyby-updates/"},{"id":"art002e012278","badge":"WINDOW VIEW · LUNAR APPROACH","title":"The Moon rises into Orion’s window.","desc":"NASA identifies this image as the Moon peeking above Orion’s window sill during the lunar-flyby observation period.","notice":"The spacecraft window itself becomes part of the composition, emphasizing that this is a crewed observation from inside a moving vehicle.","why":"The apparent motion of the lunar limb is the visible expression of rapidly changing Moon-relative geometry.","time":"Apr 6 · lunar approach","geometry":"Lunar limb through Orion window","evidence":"NASA exact mission image","provenance":"EXACT MISSION IMAGE · WINDOW VIEW","earth":0.18,"moon":0.84,"source":"https://www.nasa.gov/gallery/lunar-flyby/"},{"id":"art002e012273","badge":"SCIENCE TARGET · ORIENTALE","title":"Orientale’s rings become a live geology target.","desc":"NASA identifies this view as the southwest portion of Orientale Basin, highlighting one of its prominent annular rings. Orientale was one of the crew’s prioritized lunar targets.","notice":"Ring structure preserves evidence of the enormous impact that formed the basin roughly 3.8 billion years ago.","why":"The science team selected targets using expected lighting and viewing geometry so the crew could compare landforms from a unique moving vantage point.","time":"Apr 6 · science observation window","geometry":"Near/far-side boundary region","evidence":"NASA identified science target","provenance":"EXACT MISSION IMAGE · TARGET IDENTIFIED BY NASA","earth":0.12,"moon":0.92,"source":"https://www.nasa.gov/gallery/lunar-flyby/page/2/"},{"id":"art002e012702","badge":"SCIENCE TARGET · POYNTING / KEELER","title":"Two craters reveal different impact histories in one frame.","desc":"NASA identifies Poynting and Keeler craters side by side in this Artemis II lunar-flyby image.","notice":"Adjacent craters can preserve different textures, ejecta patterns, degradation states, and superposed features.","why":"Side-by-side morphology lets trained observers compare relative age and geologic processes quickly while the view is changing.","time":"Apr 6 · lunar science period","geometry":"Far-side crater field","evidence":"NASA identified features","provenance":"EXACT MISSION IMAGE · FEATURES IDENTIFIED BY NASA","earth":0.08,"moon":0.96,"source":"https://www.nasa.gov/gallery/lunar-flyby/page/2/"},{"id":"art002e010208","badge":"TERMINATOR · REAL-TIME OBSERVATION","title":"The day–night boundary turns subtle relief into dramatic structure.","desc":"NASA notes that the crew described the lunar terminator during the flyby. Low-angle sunlight exaggerates topography and makes ridges, crater walls, and textures easier to read.","notice":"During the flyby, the crew also reported color nuances; the ground science team used incoming observations to update follow-up guidance.","why":"Human eyes can notice subtle color and texture differences that become scientifically useful when tied to location, lighting, and later image analysis.","time":"Apr 6 · live science observations","geometry":"Low-Sun terminator lighting","evidence":"NASA image + reported crew observations","provenance":"EXACT MISSION IMAGE · LIVE OBSERVATION CONTEXT","earth":0.05,"moon":0.98,"source":"https://www.nasa.gov/blogs/missions/2026/04/06/artemis-ii-flight-day-6-lunar-flyby-updates/"},{"id":"art002e009283","badge":"FAR SIDE · SOUTH POLE–AITKEN EDGE","title":"The far side becomes a heavily cratered archive.","desc":"NASA identifies this image as heavily cratered terrain along the eastern edge of the South Pole–Aitken basin, with the terminator visible in the scene.","notice":"The far side preserves a different visual character from the familiar nearside maria seen from Earth.","why":"Artemis II gave trained human observers a moving, close-range look at regions that cannot be viewed directly from Earth.","time":"Apr 6 · far-side observation","geometry":"South Pole–Aitken basin edge","evidence":"NASA identified region","provenance":"EXACT MISSION IMAGE · REGION IDENTIFIED BY NASA","earth":0.02,"moon":1,"source":"https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/"},{"id":"art002e009282","badge":"FAR SIDE · VAVILOV / HERTZSPRUNG","title":"Long shadows turn Vavilov into a relief map.","desc":"NASA identifies Vavilov Crater on the rim of the older Hertzsprung basin in this far-side image, captured with a handheld camera at 400 mm.","notice":"Low Sun angles emphasize wall relief, ejecta, and the transition between smoother basin material and rugged terrain.","why":"Lighting geometry can expose structure that is much harder to interpret under a high Sun.","time":"Apr 6 · far-side observation","geometry":"Low-Sun far-side terrain","evidence":"NASA identified feature","provenance":"EXACT MISSION IMAGE · FEATURE IDENTIFIED BY NASA","earth":0.02,"moon":1,"source":"https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/"},{"id":"art002e012093","badge":"SCIENCE TARGET · HERTZSPRUNG","title":"Hertzsprung’s concentric rings come into view.","desc":"NASA identifies Hertzsprung Basin and its distinctive concentric mountain rings in this Artemis II flyby image.","notice":"A giant basin can only be understood at scale by relating local crater detail to the broad ring structure surrounding it.","why":"The crew’s moving perspective offered multiple viewing angles across a target the science team had prioritized before the flyby.","time":"Apr 6 · far-side science","geometry":"Hertzsprung basin rings","evidence":"NASA identified feature","provenance":"EXACT MISSION IMAGE · TARGET IDENTIFIED BY NASA","earth":0.02,"moon":1,"source":"https://www.nasa.gov/gallery/lunar-flyby/"},{"id":"art002e012279","badge":"EARTHSET APPROACH · ~9 MIN BEFORE","title":"Earth approaches the lunar horizon.","desc":"NASA identifies this view as being captured from Orion approximately nine minutes before Earthset.","notice":"The apparent closing distance between Earth and the lunar limb is a visual countdown to occultation.","why":"The same geometry that produces Earthset also drives a planned loss of direct radio line of sight shortly afterward.","time":"Apr 6 · ~9 min before Earthset","geometry":"Earth nearing lunar limb","evidence":"NASA near-event image","provenance":"NEAR-EVENT IMAGE · NASA TIME CONTEXT","earth":0.2,"moon":0.99,"source":"https://www.nasa.gov/gallery/lunar-flyby/"},{"id":"art002e009288","badge":"EARTHSET · 22:41 UTC","title":"Earth disappears behind the Moon.","desc":"NASA timestamps this Earthset image at 6:41 p.m. EDT on April 6, three minutes before Orion went behind the Moon and lost contact with Earth for about 40 minutes.","notice":"A crescent Earth sinks behind lunar terrain. The photograph is direct visual evidence; it is not itself a radio link-budget measurement.","why":"The moment makes occultation intuitive: the Moon physically moves between Orion and Earth.","time":"2026-04-06 · 22:41 UTC","geometry":"Earthset → occultation","evidence":"NASA exact event image","provenance":"EXACT EVENT IMAGE · NASA TIMESTAMP","earth":0.18,"moon":1,"source":"https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/"},{"id":"jsc2026e020490","badge":"GROUND LOOP · SCIENCE CONSOLE","title":"The view through the window has a team in Houston behind it.","desc":"NASA photographed Artemis II science officers Angela Garcia, Kelsey Young, and Trevor Graff in the White Flight Control Room about ten minutes before Earthset, monitoring mission data in real time.","notice":"Crew observations flowed into a ground team that could analyze, prioritize, ask follow-up questions, and integrate science with the flight-control structure.","why":"Exploration is distributed: astronauts observe while specialists on Earth turn those observations into decisions and durable science products.","time":"Apr 6 · ~10 min before Earthset","geometry":"Mission Control · Houston","evidence":"NASA exact ground image","provenance":"GROUND CONTEXT · EXACT NASA IMAGE","earth":0.18,"moon":0.98,"source":"https://images.nasa.gov/details/jsc2026e020490"},{"id":"art002e009289","badge":"FAR SIDE · PLANNED LOSS OF SIGNAL","title":"Behind the Moon, silence is expected.","desc":"During the planned far-side passage, lunar terrain blocked direct Earth line of sight. This image is flyby terrain context rather than a private communications measurement.","notice":"Mission Control expects the silence. Orion continues through the planned flyby while the ground waits for geometry to reopen.","why":"Operational discipline includes knowing when no signal is normal so an expected constraint is not mistaken for an anomaly.","time":"Apr 6 · planned ~40 min LOS","geometry":"Moon between Orion and Earth","evidence":"NASA mission image + reported LOS","provenance":"SAME-PHASE IMAGE · NASA REPORTED EVENT","earth":0.01,"moon":1,"source":"https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/"},{"id":"art002e009299","badge":"DEEPEST FLYBY · SAME PHASE","title":"Closest approach happens inside a moving landscape.","desc":"MissionLab derives pericynthion near 23:00:46 UTC. This NASA crew image is from the same lunar-flyby phase, not claimed as the exact frame at that derived instant.","notice":"MissionLab derives a Moon-center distance of 8,281.938 km and mean-radius altitude of 6,544.538 km from public trajectory data.","why":"Closest approach is a geometric result. Nearby photography can show the environment without inventing an image timestamp to the derived second.","time":"Derived · 23:00:46 UTC","geometry":"Pericynthion region","evidence":"MissionLab time + NASA same-phase image","provenance":"MISSIONLAB DERIVED EVENT · SAME-PHASE IMAGE","earth":0.01,"moon":1,"source":"https://www.nasa.gov/gallery/lunar-flyby/"},{"id":"art002e009301","badge":"TOTAL SOLAR ECLIPSE · MISSION IMAGE","title":"The Moon covers the Sun from deep space.","desc":"Artemis II crew photography captured the Moon fully eclipsing the Sun. MissionLab separately derives an approximately 54-minute eclipse interval from spacecraft and body geometry.","notice":"The photograph is direct mission evidence. The precise interval in MissionLab is a separate derived geometry product.","why":"The moving Orion–Moon–Sun alignment produced a totality duration and perspective impossible to experience from Earth.","time":"Apr 7 · eclipse interval","geometry":"Sun–Moon–Orion alignment","evidence":"NASA image + MissionLab geometry","provenance":"MISSION IMAGE + DERIVED INTERVAL","earth":0.08,"moon":0.95,"source":"https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/"},{"id":"art002e009298","badge":"ECLIPSE SCIENCE · IMPACT-FLASH CONTEXT","title":"Darkness turns the lunar night side into an observation field.","desc":"This NASA image is an eclipse close-up from the Artemis II flyby. During the eclipse observation period, crew members reported extremely faint meteoroid impact flashes on the dark Moon.","notice":"This photograph provides eclipse context; MissionLab does not claim that a specific flash is visible in this frame unless NASA metadata says so.","why":"The observation shows why a darkened lunar surface can reveal transient events that disappear against normal daylight.","time":"Apr 7 · eclipse observation period","geometry":"Dark Moon / deep-space viewing","evidence":"NASA eclipse image + reported observation","provenance":"MISSION IMAGE · IMPACT-FLASH CONTEXT","earth":0.06,"moon":0.92,"source":"https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/"},{"id":"art002e009573","badge":"ECLIPSE · MULTI-BODY VIEW","title":"An eclipse becomes a deep-space composition.","desc":"NASA’s flyby gallery includes this backlit lunar eclipse view from Orion, part of the mission’s rare deep-space solar-eclipse sequence.","notice":"The dark lunar disk, scattered stars, and surrounding deep-space targets become visible under lighting conditions unlike a normal sunlit Moon view.","why":"The scene connects lunar observation, solar science, and celestial navigation geometry in one human-scale view.","time":"Apr 7 · eclipse period","geometry":"Backlit Moon from Orion","evidence":"NASA exact mission image","provenance":"EXACT MISSION IMAGE · ECLIPSE PERIOD","earth":0.08,"moon":0.9,"source":"https://www.nasa.gov/gallery/lunar-flyby/"},{"id":"art002e021278","badge":"EARTHRISE · 23:22 UTC","title":"Earth returns over the lunar horizon.","desc":"NASA timestamps this Earthrise at 7:22 p.m. EDT on April 6 as Earth reappears from behind the Moon.","notice":"Visual Earthrise signals reopening line-of-sight geometry, while actual communications reacquisition still depends on ground-station geometry, pointing, link margin, and network state.","why":"MissionLab can compare geometric emergence with NASA’s operational communications timeline without treating them as identical.","time":"2026-04-06 · 23:22 UTC","geometry":"Earthrise / emerging LOS","evidence":"NASA exact event image","provenance":"EXACT EVENT IMAGE · NASA TIMESTAMP","earth":0.2,"moon":1,"source":"https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/"},{"id":"art002e016299","badge":"EARTHRISE · EXTERNAL CAMERA","title":"The same geometry looks different from outside Orion.","desc":"NASA identifies this Earthrise as captured from a camera mounted on one of Orion’s solar array wings.","notice":"The vehicle-mounted perspective separates crew handheld photography from spacecraft exterior-imaging systems.","why":"Different cameras can document the same mission geometry for different engineering, outreach, and situational-awareness purposes.","time":"Apr 6 · Earthrise period","geometry":"Solar-array camera view","evidence":"NASA spacecraft camera image","provenance":"EXACT MISSION IMAGE · EXTERNAL CAMERA","earth":0.2,"moon":0.96,"source":"https://www.nasa.gov/gallery/lunar-flyby/page/3/"},{"id":"art002e016354","badge":"RETURN · LUNAR CRESCENT","title":"The Moon starts shrinking behind Orion.","desc":"NASA identifies this April 8 image as a thin lunar crescent captured by the Artemis II crew while traveling back toward Earth.","notice":"The flyby is over, but the Moon remains a changing reference in the rearward geometry of the return coast.","why":"Mission phase has shifted from lunar observation to protecting the future Earth-entry corridor.","time":"Apr 8 · return coast","geometry":"Moon receding","evidence":"NASA exact mission image","provenance":"EXACT MISSION IMAGE · RETURN COAST","earth":0.52,"moon":0.24,"source":"https://www.nasa.gov/gallery/lunar-flyby/"},{"id":"art002e012588","badge":"RETURN · MILKY WAY","title":"The journey home opens a window on the galaxy.","desc":"NASA highlights this Flight Day 7 image as a striking Artemis II crew photograph of the Milky Way during the return journey.","notice":"Away from bright nearby terrain, the window can frame an entirely different scale of observation: the star field of our own galaxy.","why":"The mission’s human perspective extends beyond engineering milestones; deep-space flight changes what the crew can see and document.","time":"Apr 7 · return to Earth","geometry":"Deep-space star field","evidence":"NASA exact mission image","provenance":"EXACT MISSION IMAGE · RETURN PHASE","earth":0.46,"moon":0.16,"source":"https://www.nasa.gov/general/artemis-ii-mission-milestones-an-image-and-video-recap/"}].map(v=>({...v,src:`https://images-assets.nasa.gov/image/${v.id}/${v.id}~large.jpg`,mobileSrc:`https://images-assets.nasa.gov/image/${v.id}/${v.id}~medium.jpg`,origSrc:`https://images-assets.nasa.gov/image/${v.id}/${v.id}~orig.jpg`,thumbSrc:`https://images-assets.nasa.gov/image/${v.id}/${v.id}~small.jpg`}));
  let crewIndex=0;
  let crewResizeFrame=0;
  let crewImageRequest=0;
  const crewImagePreloads=new Map();

  function crewUsesMobileImage(){
    return matchMedia('(max-width:760px), (max-width:950px) and (max-height:500px) and (orientation:landscape)').matches;
  }

  function crewImageSources(v){
    const preferred=crewUsesMobileImage()?v.mobileSrc:v.src;

    return [...new Set([
      preferred,
      v.src,
      v.origSrc
    ].filter(Boolean))];
  }

  function preloadCrewUrl(url){
    if(!url || crewImagePreloads.has(url))return;

    const probe=new Image();
    probe.decoding='async';
    probe.src=url;

    crewImagePreloads.set(url,probe);
  }

  function preloadCrewNeighbors(index){
    [-1,1].forEach(delta=>{
      const i=(index+delta+crewViews.length)%crewViews.length;
      const url=crewImageSources(crewViews[i])[0];

      preloadCrewUrl(url);
    });
  }

  function setCrewImage(img,v){
    const request=++crewImageRequest;
    const sources=crewImageSources(v);

    img.setAttribute('aria-busy','true');
    img.classList.add('crew-photo-loading');

    const finalize=()=>{
      if(request!==crewImageRequest)return;

      img.alt=v.title;
      img.style.objectPosition=crewObjectPosition(v);

      img.classList.remove(
        'is-fallback',
        'crew-photo-loading'
      );

      img.removeAttribute('aria-busy');

      preloadCrewNeighbors(crewIndex);
    };

    const trySource=n=>{
      if(request!==crewImageRequest)return;

      if(n>=sources.length){
        img.src='assets/public/fallback-mission.svg';
        img.alt=v.title+' — NASA image unavailable';
        img.classList.add('is-fallback');
        img.classList.remove('crew-photo-loading');
        img.removeAttribute('aria-busy');
        return;
      }

      const probe=new Image();
      probe.decoding='async';

      probe.onload=()=>{
        if(request!==crewImageRequest)return;

        img.src=probe.src;

        if(typeof img.decode==='function'){
          img.decode()
            .then(finalize)
            .catch(finalize);
        }else{
          finalize();
        }
      };

      probe.onerror=()=>{
        trySource(n+1);
      };

      probe.src=sources[n];
    };

    trySource(0);
  }
  function queueCrewGeometryResize(){
    cancelAnimationFrame(crewResizeFrame);
    crewResizeFrame=requestAnimationFrame(()=>drawCrewGeometry(crewViews[crewIndex]));
  }
  window.addEventListener('resize',queueCrewGeometryResize,{passive:true});
  window.addEventListener('orientationchange',queueCrewGeometryResize,{passive:true});
  window.visualViewport?.addEventListener('resize',queueCrewGeometryResize,{passive:true});
  function crewObjectPosition(v){
    const badge=(v.badge||'').toUpperCase();
    if(/GROUND LOOP|SCIENCE PREP|CREW SCIENCE/.test(badge))return '50% 42%';
    if(/EARTHSET|EARTHRISE|WINDOW VIEW/.test(badge))return '50% 50%';
    if(/MILKY WAY|ECLIPSE/.test(badge))return '50% 46%';
    return '50% 50%';
  }
  function drawCrewGeometry(v){
    const c=$('#crew-geometry-canvas');if(!c)return;const {ctx,w,h,layout}=fitCanvas(c);ctx.clearRect(0,0,w,h);ctx.fillStyle='rgba(2,5,9,.76)';ctx.fillRect(0,0,w,h);
    const scene=sceneRect(w,h,{},layout.phone?8:10);ctx.strokeStyle='rgba(255,255,255,.14)';ctx.beginPath();ctx.moveTo(scene.x,scene.cy);ctx.lineTo(scene.right,scene.cy);ctx.stroke();
    const er=clamp(scene.min*(.08+v.earth*.095),6,20),mr=clamp(scene.min*(.075+v.moon*.10),6,21),ex=scene.x+er+6,mx=scene.right-mr-6;
    ctx.fillStyle='#7fc8ff';ctx.beginPath();ctx.arc(ex,scene.cy,er,0,Math.PI*2);ctx.fill();ctx.fillStyle='#a8a6a0';ctx.beginPath();ctx.arc(mx,scene.cy,mr,0,Math.PI*2);ctx.fill();const x=lerp(ex,mx,v.moon/(v.moon+v.earth+.001));ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(x,scene.cy,3.2,0,Math.PI*2);ctx.fill();
    drawCanvasLabel(ctx,'EARTH',scene.x,scene.bottom-2,64,{size:10.5,minSize:9.5,color:'rgba(255,255,255,.65)',maxLines:1});drawCanvasLabel(ctx,'MOON',scene.right,scene.bottom-2,64,{size:10.5,minSize:9.5,align:'right',color:'rgba(255,255,255,.65)',maxLines:1});
  }
  function renderCrew(i){
    crewIndex=((Math.round(i)%crewViews.length)+crewViews.length)%crewViews.length;
    const v=crewViews[crewIndex],img=$('#crew-photo'),source=$('#crew-source');
    if(source)source.href=v.source||'https://www.nasa.gov/gallery/lunar-flyby/';
    if(img){img.loading='eager';img.decoding='async';img.dataset.fallback='assets/public/fallback-mission.svg';setCrewImage(img,v);}
    const fields={badge:v.badge,index:`MISSION VIEW ${String(crewIndex+1).padStart(2,'0')} / ${String(crewViews.length).padStart(2,'0')}`,title:v.title,description:v.desc,notice:v.notice,why:v.why,time:v.time,geometry:v.geometry,evidence:v.evidence,provenance:v.provenance};
    Object.entries(fields).forEach(([k,val])=>{const el=$('#crew-'+k);if(el)el.textContent=val;});
    const count=$('#crew-image-count');if(count)count.textContent=`${String(crewIndex+1).padStart(2,'0')} / ${String(crewViews.length).padStart(2,'0')}`;
    const scrub=$('#crew-scrubber');if(scrub){scrub.max=crewViews.length-1;scrub.value=crewIndex;}
    const thumbs=$$('#crew-filmstrip button');thumbs.forEach((b,j)=>b.classList.toggle('active',j===crewIndex));
    const active=thumbs[crewIndex],strip=$('#crew-filmstrip');if(active&&strip){const left=Math.max(0,active.offsetLeft-(strip.clientWidth-active.clientWidth)/2);strip.scrollTo({left,behavior:'smooth'});}
    drawCrewGeometry(v);
    syncCrewLightbox(v);
  }
  const film=$('#crew-filmstrip');if(film){film.innerHTML=crewViews.map((v,i)=>`<button type="button" data-i="${i}" aria-label="${v.badge}"><img src="${v.thumbSrc}" data-fallback="assets/public/fallback-mission.svg" loading="lazy" decoding="async" alt=""><span>${String(i+1).padStart(2,'0')}</span><small>${v.badge.split(' · ')[0]}</small></button>`).join('');$$('img',film).forEach(img=>img.addEventListener('error',()=>{if(!img.dataset.didFallback){img.dataset.didFallback='1';img.src=img.dataset.fallback;}}));$$('button',film).forEach(b=>b.addEventListener('click',()=>renderCrew(Number(b.dataset.i))));}
  const crewPrev=()=>renderCrew(crewIndex-1),crewNext=()=>renderCrew(crewIndex+1);

  const crewLightbox=$('#crew-lightbox');
  const crewLightboxStage=$('#crew-lightbox-stage');
  const crewLightboxImage=$('#crew-lightbox-image');
  const crewLightboxScale=$('#crew-lightbox-scale');

  const crewLightboxState={
    scale:1,
    x:0,
    y:0,
    pointers:new Map(),
    panStartX:0,
    panStartY:0,
    pointerStartX:0,
    pointerStartY:0,
    pinchStartDistance:0,
    pinchStartScale:1,
    lastTapAt:0,
    lastTapX:0,
    lastTapY:0
  };

  let crewLightboxReturnFocus=null;

  function crewFullImageSource(v){
    return (
      v.origSrc ||
      v.src ||
      v.mobileSrc ||
      $('#crew-photo')?.currentSrc ||
      $('#crew-photo')?.src ||
      'assets/public/fallback-mission.svg'
    );
  }

  function crewLightboxBounds(){
    if(!crewLightboxStage)return {x:0,y:0};

    return {
      x:Math.max(
        0,
        crewLightboxStage.clientWidth*
          (crewLightboxState.scale-1)/2
      ),
      y:Math.max(
        0,
        crewLightboxStage.clientHeight*
          (crewLightboxState.scale-1)/2
      )
    };
  }

  function applyCrewLightboxTransform(){
    if(!crewLightboxImage || !crewLightboxStage)return;

    const bounds=crewLightboxBounds();

    crewLightboxState.x=clamp(
      crewLightboxState.x,
      -bounds.x,
      bounds.x
    );

    crewLightboxState.y=clamp(
      crewLightboxState.y,
      -bounds.y,
      bounds.y
    );

    crewLightboxImage.style.transform=
      `translate3d(${crewLightboxState.x}px,${crewLightboxState.y}px,0) scale(${crewLightboxState.scale})`;

    crewLightboxStage.classList.toggle(
      'is-zoomed',
      crewLightboxState.scale>1.01
    );

    if(crewLightboxScale){
      crewLightboxScale.value=
        `${Math.round(crewLightboxState.scale*100)}%`;

      crewLightboxScale.textContent=
        `${Math.round(crewLightboxState.scale*100)}%`;
    }
  }

  function setCrewLightboxScale(nextScale){
    crewLightboxState.scale=clamp(
      nextScale,
      1,
      5
    );

    if(crewLightboxState.scale<=1.001){
      crewLightboxState.scale=1;
      crewLightboxState.x=0;
      crewLightboxState.y=0;
    }

    applyCrewLightboxTransform();
  }

  function resetCrewLightboxTransform(){
    crewLightboxState.scale=1;
    crewLightboxState.x=0;
    crewLightboxState.y=0;
    crewLightboxState.pointers.clear();

    crewLightboxStage?.classList.remove(
      'is-dragging'
    );

    applyCrewLightboxTransform();
  }

  function preloadCrewFullNeighbors(index){
    [-1,1].forEach(delta=>{
      const i=(
        index+
        delta+
        crewViews.length
      )%crewViews.length;

      preloadCrewUrl(
        crewFullImageSource(
          crewViews[i]
        )
      );
    });
  }

  function syncCrewLightbox(v){
    if(!crewLightbox || !crewLightbox.open)return;

    const source=crewFullImageSource(v);

    if(crewLightboxImage){

      if(
        crewLightboxImage.dataset.source
        !==source
      ){
        crewLightboxImage.dataset.source=
          source;

        crewLightboxImage.dataset.didFallback=
          '';

        crewLightboxImage.src=source;
      }

      crewLightboxImage.alt=v.title;
    }

    const title=$('#crew-lightbox-title');
    const count=$('#crew-lightbox-count');
    const provenance=$(
      '#crew-lightbox-provenance'
    );

    if(title){
      title.textContent=v.title;
    }

    if(count){
      count.textContent=
        `IMAGE ${String(crewIndex+1).padStart(2,'0')} / ${String(crewViews.length).padStart(2,'0')}`;
    }

    if(provenance){
      provenance.textContent=
        v.provenance ||
        v.evidence ||
        'NASA MISSION IMAGERY';
    }

    resetCrewLightboxTransform();
    preloadCrewFullNeighbors(crewIndex);
  }

  function cleanupCrewLightbox(){
    document.body.classList.remove(
      'crew-lightbox-open'
    );

    resetCrewLightboxTransform();

    const returnFocus=
      crewLightboxReturnFocus;

    crewLightboxReturnFocus=null;

    if(
      returnFocus &&
      typeof returnFocus.focus==='function'
    ){
      try{
        returnFocus.focus({
          preventScroll:true
        });
      }catch{
        returnFocus.focus();
      }
    }
  }

  function openCrewLightbox(sourceElement){
    if(!crewLightbox)return;

    crewLightboxReturnFocus=
      sourceElement ||
      document.activeElement;

    document.body.classList.add(
      'crew-lightbox-open'
    );

    if(
      typeof crewLightbox.showModal
      ==='function'
    ){
      if(!crewLightbox.open){
        crewLightbox.showModal();
      }
    }else{
      crewLightbox.setAttribute(
        'open',
        ''
      );
    }

    syncCrewLightbox(
      crewViews[crewIndex]
    );

    setTimeout(()=>{
      try{
        crewLightboxStage?.focus({
          preventScroll:true
        });
      }catch{
        crewLightboxStage?.focus();
      }
    },0);
  }

  function closeCrewLightbox(){
    if(!crewLightbox)return;

    if(
      typeof crewLightbox.close
      ==='function' &&
      crewLightbox.open
    ){
      crewLightbox.close();
      return;
    }

    crewLightbox.removeAttribute(
      'open'
    );

    cleanupCrewLightbox();
  }

  function crewPointerDistance(){
    const values=[
      ...crewLightboxState.pointers.values()
    ];

    if(values.length<2)return 0;

    return Math.hypot(
      values[0].x-values[1].x,
      values[0].y-values[1].y
    );
  }

  function rebaseCrewPointer(){
    const first=[
      ...crewLightboxState.pointers.values()
    ][0];

    if(!first)return;

    first.startX=first.x;
    first.startY=first.y;

    crewLightboxState.panStartX=
      crewLightboxState.x;

    crewLightboxState.panStartY=
      crewLightboxState.y;

    crewLightboxState.pointerStartX=
      first.x;

    crewLightboxState.pointerStartY=
      first.y;
  }

  $('#crew-zoom')?.addEventListener(
    'click',
    e=>{
      e.preventDefault();
      openCrewLightbox(
        e.currentTarget
      );
    }
  );

  $('#crew-photo')?.addEventListener(
    'click',
    e=>{
      e.preventDefault();
      openCrewLightbox(
        e.currentTarget
      );
    }
  );

  $('#crew-photo')?.addEventListener(
    'keydown',
    e=>{
      if(
        e.key!=='Enter' &&
        e.key!==' '
      )return;

      e.preventDefault();

      openCrewLightbox(
        e.currentTarget
      );
    }
  );

  $('#crew-lightbox-close')?.addEventListener(
    'click',
    closeCrewLightbox
  );

  $('#crew-lightbox-prev')?.addEventListener(
    'click',
    e=>{
      e.preventDefault();
      crewPrev();
    }
  );

  $('#crew-lightbox-next')?.addEventListener(
    'click',
    e=>{
      e.preventDefault();
      crewNext();
    }
  );

  $('#crew-lightbox-minus')?.addEventListener(
    'click',
    ()=>setCrewLightboxScale(
      crewLightboxState.scale-.5
    )
  );

  $('#crew-lightbox-plus')?.addEventListener(
    'click',
    ()=>setCrewLightboxScale(
      crewLightboxState.scale+.5
    )
  );

  $('#crew-lightbox-reset')?.addEventListener(
    'click',
    resetCrewLightboxTransform
  );

  crewLightboxImage?.addEventListener(
    'error',
    ()=>{
      if(
        crewLightboxImage.dataset.didFallback
      )return;

      crewLightboxImage.dataset.didFallback=
        '1';

      crewLightboxImage.src=
        'assets/public/fallback-mission.svg';
    }
  );

  crewLightbox?.addEventListener(
    'close',
    cleanupCrewLightbox
  );

  crewLightbox?.addEventListener(
    'cancel',
    e=>{
      e.preventDefault();
      closeCrewLightbox();
    }
  );

  crewLightboxStage?.addEventListener(
    'wheel',
    e=>{
      e.preventDefault();

      setCrewLightboxScale(
        crewLightboxState.scale+
        (
          e.deltaY<0
            ?.35
            :-.35
        )
      );
    },
    {
      passive:false
    }
  );

  crewLightboxStage?.addEventListener(
    'dblclick',
    e=>{
      e.preventDefault();

      setCrewLightboxScale(
        crewLightboxState.scale>1.1
          ?1
          :2.5
      );
    }
  );

  crewLightboxStage?.addEventListener(
    'pointerdown',
    e=>{
      if(
        e.target.closest(
          'button'
        )
      )return;

      e.preventDefault();

      try{
        crewLightboxStage.setPointerCapture(
          e.pointerId
        );
      }catch{}

      crewLightboxState.pointers.set(
        e.pointerId,
        {
          x:e.clientX,
          y:e.clientY,
          startX:e.clientX,
          startY:e.clientY
        }
      );

      if(
        crewLightboxState.pointers.size
        ===1
      ){
        crewLightboxState.panStartX=
          crewLightboxState.x;

        crewLightboxState.panStartY=
          crewLightboxState.y;

        crewLightboxState.pointerStartX=
          e.clientX;

        crewLightboxState.pointerStartY=
          e.clientY;

        if(
          crewLightboxState.scale>1.01
        ){
          crewLightboxStage.classList.add(
            'is-dragging'
          );
        }
      }

      if(
        crewLightboxState.pointers.size
        ===2
      ){
        crewLightboxState.pinchStartDistance=
          Math.max(
            1,
            crewPointerDistance()
          );

        crewLightboxState.pinchStartScale=
          crewLightboxState.scale;
      }
    }
  );

  crewLightboxStage?.addEventListener(
    'pointermove',
    e=>{
      const pointer=
        crewLightboxState.pointers.get(
          e.pointerId
        );

      if(!pointer)return;

      pointer.x=e.clientX;
      pointer.y=e.clientY;

      if(
        crewLightboxState.pointers.size
        >=2
      ){
        e.preventDefault();

        const distance=
          crewPointerDistance();

        if(
          crewLightboxState.pinchStartDistance
          >0
        ){
          crewLightboxState.scale=
            clamp(
              crewLightboxState.pinchStartScale*
              (
                distance/
                crewLightboxState.pinchStartDistance
              ),
              1,
              5
            );

          if(
            crewLightboxState.scale<=1.001
          ){
            crewLightboxState.scale=1;
            crewLightboxState.x=0;
            crewLightboxState.y=0;
          }

          applyCrewLightboxTransform();
        }

        return;
      }

      if(
        crewLightboxState.scale>1.01
      ){
        e.preventDefault();

        crewLightboxState.x=
          crewLightboxState.panStartX+
          (
            e.clientX-
            crewLightboxState.pointerStartX
          );

        crewLightboxState.y=
          crewLightboxState.panStartY+
          (
            e.clientY-
            crewLightboxState.pointerStartY
          );

        applyCrewLightboxTransform();
      }
    },
    {
      passive:false
    }
  );

  function finishCrewPointer(e){
    const pointer=
      crewLightboxState.pointers.get(
        e.pointerId
      );

    if(!pointer)return;

    const pointerCount=
      crewLightboxState.pointers.size;

    const dx=
      e.clientX-
      pointer.startX;

    const dy=
      e.clientY-
      pointer.startY;

    const distance=
      Math.hypot(
        dx,
        dy
      );

    if(
      pointerCount===1 &&
      crewLightboxState.scale<=1.01
    ){
      if(
        Math.abs(dx)>=58 &&
        Math.abs(dx)>
          Math.abs(dy)*1.15
      ){
        if(dx<0){
          crewNext();
        }else{
          crewPrev();
        }
      }else if(distance<16){

        const now=
          performance.now();

        const tapDistance=
          Math.hypot(
            e.clientX-
              crewLightboxState.lastTapX,
            e.clientY-
              crewLightboxState.lastTapY
          );

        if(
          now-
            crewLightboxState.lastTapAt
            <320 &&
          tapDistance<34
        ){
          crewLightboxState.lastTapAt=0;

          setCrewLightboxScale(
            crewLightboxState.scale>1.1
              ?1
              :2.5
          );
        }else{
          crewLightboxState.lastTapAt=
            now;

          crewLightboxState.lastTapX=
            e.clientX;

          crewLightboxState.lastTapY=
            e.clientY;
        }
      }
    }

    crewLightboxState.pointers.delete(
      e.pointerId
    );

    if(
      crewLightboxState.pointers.size
      ===1
    ){
      rebaseCrewPointer();
    }

    if(
      crewLightboxState.pointers.size
      ===0
    ){
      crewLightboxStage?.classList.remove(
        'is-dragging'
      );
    }
  }

  crewLightboxStage?.addEventListener(
    'pointerup',
    finishCrewPointer
  );

  crewLightboxStage?.addEventListener(
    'pointercancel',
    finishCrewPointer
  );

  crewLightboxStage?.addEventListener(
    'keydown',
    e=>{
      if(e.key==='ArrowLeft'){
        crewPrev();
        e.preventDefault();
      }

      if(e.key==='ArrowRight'){
        crewNext();
        e.preventDefault();
      }

      if(
        e.key==='+' ||
        e.key==='='
      ){
        setCrewLightboxScale(
          crewLightboxState.scale+.5
        );

        e.preventDefault();
      }

      if(e.key==='-'){
        setCrewLightboxScale(
          crewLightboxState.scale-.5
        );

        e.preventDefault();
      }

      if(
        e.key==='0' ||
        e.key==='Home'
      ){
        resetCrewLightboxTransform();
        e.preventDefault();
      }
    }
  );

  window.addEventListener(
    'resize',
    ()=>{
      if(
        crewLightbox?.open
      ){
        applyCrewLightboxTransform();
      }
    },
    {
      passive:true
    }
  );

  $('#crew-prev')?.addEventListener('click',crewPrev);
  $('#crew-next')?.addEventListener('click',crewNext);

  function bindCrewImageArrow(selector,action){
    const el=$(selector);
    if(!el)return;

    let directTouchAt=0;

    if('PointerEvent' in window){
      el.addEventListener('pointerup',e=>{
        if(
          e.pointerType!=='touch' &&
          e.pointerType!=='pen'
        )return;

        directTouchAt=performance.now();

        e.preventDefault();
        e.stopPropagation();

        action();
      });
    }else{
      el.addEventListener(
        'touchend',
        e=>{
          directTouchAt=performance.now();

          e.preventDefault();
          e.stopPropagation();

          action();
        },
        {passive:false}
      );
    }

    el.addEventListener('click',e=>{
      e.preventDefault();
      e.stopPropagation();

      if(performance.now()-directTouchAt<700)return;

      action();
    });
  }

  bindCrewImageArrow(
    '#crew-image-prev',
    crewPrev
  );

  bindCrewImageArrow(
    '#crew-image-next',
    crewNext
  );

  $('#crew-scrubber')?.addEventListener(
    'input',
    e=>renderCrew(Number(e.target.value))
  );
  document.addEventListener('keydown',e=>{if($('#crew-lightbox')?.open)return;const section=$('#crew-view');if(!section)return;const r=section.getBoundingClientRect();const visible=r.top<innerHeight*.72&&r.bottom>innerHeight*.28;if(!visible||/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName||''))return;if(e.key==='ArrowLeft'){crewPrev();e.preventDefault();}if(e.key==='ArrowRight'){crewNext();e.preventDefault();}});
  window.A2Windows=Object.freeze({
    next:crewNext,
    prev:crewPrev,
    render:renderCrew,
    index:()=>crewIndex,
    openLightbox:()=>openCrewLightbox($('#crew-zoom')),
    closeLightbox:closeCrewLightbox
  });

  window.addEventListener('resize',()=>drawCrewGeometry(crewViews[crewIndex]));renderCrew(0);

  }


})();
