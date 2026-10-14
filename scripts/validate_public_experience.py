from __future__ import annotations
import argparse,re,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
PUBLIC_JS=['js/core.js','js/mission.js','js/windows.js','js/gnc.js','js/mission-control.js','js/psi-model.js','js/psi.js','js/trajectory-model.js','js/trajectory.js']
PHASE10_PAGES=['mission.html','windows.html','gnc.html','mission-control.html','psi.html']
REQUIRED_FILES=['index.html','styles.css','landing.css','windows.css','gnc.css','mission-control.css','psi.css','trajectory.css','app.js',*PUBLIC_JS,*PHASE10_PAGES,'library.html','library.js','technical-report.html','favicon.svg','favicon.ico','assets/public/IMAGE_SOURCES.md','assets/public/AUTHORITATIVE_SOURCE_AUDIT.md','assets/public/FIGURE_AUDIT.md','assets/public/fallback-mission.svg','assets/public/figures/navigation-state-products.svg','assets/public/figures/esm-propulsion-architecture.svg','assets/public/figures/trajectory-correction-plan-execution.svg','assets/public/figures/entry-recovery-sequence.svg','assets/public/figures/gnc-proximity-loop.svg','PUBLIC_EXPERIENCE_FINAL_README.md','scripts/validation/windows_scroll_regression.html','scripts/validation/validate_windows_scroll_regression.py','assets/public/celestial/earth_pia18033.jpg','assets/public/celestial/moon_lro_mosaic.jpg','assets/public/celestial/manifest.json','scripts/validation/validate_celestial_assets.py','scripts/validation/responsive_browser_qa.html','scripts/validation/validate_responsive_browser_qa.py','docs/RESPONSIVE_BROWSER_QA.md']
REQUIRED_FILES += ['scripts/validation/validate_text_integrity.py','docs/PHASE10_QUALITY_STANDARD.md']
REQUIRED_FILES += ['.gitattributes','scripts/validation/mission_scroll_regression.html','scripts/validation/validate_mission_scroll_regression.py','docs/MISSION_EXPLORER_QA.md']
REQUIRED_FILES += ['scripts/validation/gnc_auto_regression.html','scripts/validation/validate_gnc_auto_regression.py','docs/GNC_INTERACTION_QA.md']
REQUIRED_FILES += ['scripts/validation/psi_regression.html','scripts/validation/validate_psi_regression.py','scripts/validation/validate_psi_model.js','docs/PSI_INTERACTION_QA.md']
REQUIRED_FILES += ['scripts/validation/trajectory_regression.html','scripts/validation/validate_trajectory_regression.py','scripts/validation/validate_trajectory_model.js','docs/TRAJECTORY_CORRECTION_QA.md']
REPO_DEPS=['data/reference/artemis_ii_gnc_architecture.json','data/reference/artemis_ii_manual_piloting_control_modes.json','data/reference/artemis_ii_entry_events.json','data/reference/artemis_ii_maneuver_plan_execution.json','data/reference/artemis_ii_phase2_closure_manifest.json','scripts/ingestion/parse_oem.py','scripts/processing/add_lunar_geometry.py','scripts/analysis/refine_lunar_closest_approach.py','docs/assets/entry/phase2e_sutton_graves_heat_flux.svg','docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg']
FORBIDDEN=[r'engineering\s+paper',r'\bmanuscript\b',r'flight-qualified simulation',r'mission telemetry replay',r'navigation filter reconstruction']
HOME_REQUIRED_IDS=['hero-stars','experiences','experience-grid','built']
class P(HTMLParser):
 def __init__(self): super().__init__(); self.ids=set();self.refs=[];self.canvases=[];self.details=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs); i=a.get('id');
  if i:self.ids.add(i)
  if tag=='canvas' and i:self.canvases.append(i)
  if tag=='details':self.details+=1
  for x in ('src','href','data-fallback'):
   if x in a:self.refs.append((x,a[x]))
def ext(v):return v.startswith(('http://','https://','mailto:','tel:','data:','javascript:'))
def target(page,v):
 if not v or ext(v):return None,None
 if v.startswith('#'):return page.resolve(),v[1:]
 u=urlparse(v); return (page.parent/u.path).resolve(),u.fragment or None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--overlay-only',action='store_true');args=ap.parse_args();fail=[];notes=[]
 for r in REQUIRED_FILES:
  if not (ROOT/r).is_file():fail.append('missing release file: '+r)
 if not args.overlay_only:
  for r in REPO_DEPS:
   if not (ROOT/r).exists():fail.append('missing repository dependency: '+r)
 pages=[ROOT/'index.html',*(ROOT/n for n in PHASE10_PAGES),ROOT/'library.html',ROOT/'technical-report.html']; parsed={}
 for pg in pages:
  if pg.exists(): q=P();q.feed(pg.read_text(encoding='utf8'));parsed[pg.resolve()]=q
 for pg,q in parsed.items():
  for attr,ref in q.refs:
   t,frag=target(pg,ref)
   if t is None:continue
   rel=''
   try: rel=str(t.relative_to(ROOT)).replace('\\','/')
   except: pass
   if not t.exists():
    if args.overlay_only and (rel.startswith('docs/') or rel.startswith('data/')):continue
    fail.append(f'{pg.name}: broken local {attr} -> {ref}');continue
   if frag and t in parsed and frag not in parsed[t].ids and t.name!='library.html':fail.append(f'{pg.name}: missing anchor {ref}')
 text='\n'.join((ROOT/n).read_text(encoding='utf8') for n in ['index.html',*PHASE10_PAGES,'styles.css','app.js',*PUBLIC_JS,'library.html','library.js','technical-report.html'] if (ROOT/n).exists())
 technical_paper_claim_text=re.sub(r'\bPublic\s+NASA\s+technical\s+papers\b','',text,flags=re.I)
 if re.search(r'technical\s+paper',technical_paper_claim_text,re.I):fail.append('forbidden public claim/term outside NASA source context: technical paper')
 for pat in FORBIDDEN:
  if re.search(pat,text,re.I):fail.append('forbidden public claim/term: '+pat)
 ip=parsed.get((ROOT/'index.html').resolve())
 if ip:
  miss=[x for x in HOME_REQUIRED_IDS if x not in ip.ids]
  if miss:fail.append('missing homepage surfaces: '+', '.join(miss))
  notes += [f'homepage canvas surfaces: {len(ip.canvases)}',f'homepage optional engineering drawers: {ip.details}']
 dedicated_page_ids={
  'mission.html':['mission-canvas','mission-scrubber','entry-canvas','entry-scrubber','trajectory-lab','trajectory-canvas','trajectory-dv','trajectory-coast','trajectory-presets','trajectory-reset','weather-canvas'],
  'windows.html':['crew-photo','crew-scrubber','crew-geometry-canvas','crew-image-prev','crew-image-next','crew-image-count','crew-zoom','crew-lightbox','crew-lightbox-image','crew-lightbox-prev','crew-lightbox-next','crew-lightbox-close'],
  'gnc.html':['gnc-canvas','gnc-start','gnc-mode-auto','gnc-mode-manual','gnc-disturbance','gnc-autopilot-status'],
  'mission-control.html':['mc-canvas'],
  'psi.html':['psi-lab-section','psi-canvas','psi-alt','psi-throttle','psi-cant','psi-spread','engine-count','regolith-select','psi-hardware','psi-reset'],
 }
 for name,required_ids in dedicated_page_ids.items():
  page_path=(ROOT/name).resolve(); page_parser=parsed.get(page_path)
  if not page_parser:
   fail.append('missing parsed dedicated page: '+name);continue
  missing=[x for x in required_ids if x not in page_parser.ids]
  if missing:fail.append(name+': missing dedicated interaction surfaces: '+', '.join(missing))
  else:notes.append(name+' interaction contract: '+str(len(required_ids))+' required IDs')
 dedicated_forbidden_ids={
  'mission.html':['crew-view','gnc-lab','mission-control','psi-lab-section'],
  'windows.html':['mission-explorer','gnc-lab','mission-control','entry-lab','maneuver-lab','trajectory-lab','space-weather','psi-lab-section'],
  'gnc.html':['mission-explorer','crew-view','mission-control','entry-lab','maneuver-lab','trajectory-lab','space-weather','psi-lab-section'],
  'mission-control.html':['mission-explorer','crew-view','gnc-lab','entry-lab','maneuver-lab','trajectory-lab','space-weather','psi-lab-section'],
  'psi.html':['mission-explorer','crew-view','gnc-lab','mission-control','entry-lab','maneuver-lab','trajectory-lab','space-weather'],
 }
 for name,forbidden_ids in dedicated_forbidden_ids.items():
  page_parser=parsed.get((ROOT/name).resolve())
  if not page_parser:continue
  leaked=[x for x in forbidden_ids if x in page_parser.ids]
  if leaked:fail.append(name+': contains interaction surfaces owned by another route: '+', '.join(leaked))
 home_forbidden=['mission-explorer','crew-view','gnc-lab','mission-control','entry-lab','maneuver-lab','trajectory-lab','space-weather','psi-lab-section']
 if ip:
  leaked=[x for x in home_forbidden if x in ip.ids]
  if leaked:fail.append('index.html still contains dedicated experience sections: '+', '.join(leaked))
 for phrase in ['NASA REPORTED','MISSIONLAB DERIVED','MODELED','INFERRED','UNKNOWN / NOT PUBLIC','ARTEMIS II DID NOT LAND ON THE MOON','Artemis IV','Sutton','8,281.938','6,544.538','36.76','RTC1','RTC2','RTC3']:
  if phrase.lower() not in text.lower():fail.append('missing required concept: '+phrase)
 mission_text=(ROOT/'mission.html').read_text(encoding='utf8')
 mission_js=(ROOT/'js/trajectory-model.js').read_text(encoding='utf8') if (ROOT/'js/trajectory-model.js').exists() else ''
 for phrase in ['SMALL ΔV NOW','two-body','local RTN','public record ≠ targeting solution','NASA REPORTED','MISSIONLAB DERIVED','UNKNOWN / NOT PUBLIC']:
  if phrase.lower() not in mission_text.lower():fail.append('mission trajectory lab missing evidence/model concept: '+phrase)
 for phrase in ['MU_EARTH','rtnBasis','rk4Step','periapsisShiftKm','arrivalShiftSeconds']:
  if phrase not in mission_js:fail.append('trajectory model missing implementation contract: '+phrase)
 for phrase in ['AUTO MODE','MANUAL MODE','Introduce disturbance','MissionLab shorthand','WHAT WOULD OPERATORS CARE ABOUT?']:
  if phrase.lower() not in text.lower():fail.append('missing final-polish UX concept: '+phrase)
 windows_js=(ROOT/'js/windows.js').read_text(encoding='utf8')
 crew_count=len(re.findall(r'\"id\":\"(?:art|jsc)[^\"]+\"',windows_js))
 notes.append(f'Through Orion windows moments: {crew_count}')
 if crew_count!=25:fail.append(f'expected 25 Through Orion windows moments, found {crew_count}')
 if 'phase2e_sutton_graves_heat_flux.svg' not in text:fail.append('correct Sutton-Graves asset not referenced')
 if 'phase2e_convective_heating.svg' in text:fail.append('obsolete Sutton-Graves filename referenced')
 l=(ROOT/'library.js').read_text(encoding='utf8'); tids=set(re.findall(r"\bid:'([^']+)'",l));notes.append(f'Mission Library deep dives: {len(tids)}')
 if 'psi' not in tids:fail.append('Mission Library missing PSI campaign-context deep dive')
 if 'artemis ii did not land on the moon' not in l.lower():fail.append('Mission Library PSI Artemis II boundary missing')
 if len(tids)<28:fail.append('Mission Library has fewer than 28 topics')
 figs=set(re.findall(r"\bfigure:'([^']+\.svg)'",l));notes.append(f'Mission Library figure references: {len(figs)}')
 for f in figs:
  if not (ROOT/f).exists() and not (args.overlay_only and f.startswith('docs/')):fail.append('missing Library figure: '+f)
 r=(ROOT/'technical-report.html').read_text(encoding='utf8'); h2=len(re.findall(r'<h2\b',r,re.I));notes.append(f'Technical Report major sections: {h2}')
 if h2<20:fail.append('Technical Report has fewer than 20 major sections')
 print('A2 MissionLab final public experience validation');print('='*58)
 for n in notes: print('PASS:',n)
 if fail:
  for x in fail:print('FAIL:',x)
  print(f'\nRESULT: FAIL ({len(fail)} issue(s))');return 1
 print('PASS: final release structure and terminology')
 print('PASS: interaction/evidence guardrails')
 print('PASS: local links/assets' + (' (overlay scope)' if args.overlay_only else ' + repository dependencies'))
 print('\nRESULT: PASS');return 0
if __name__=='__main__':sys.exit(main())
