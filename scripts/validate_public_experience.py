from __future__ import annotations
import argparse,re,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
REQUIRED_FILES=['index.html','styles.css','app.js','library.html','library.js','technical-report.html','favicon.svg','favicon.ico','assets/public/IMAGE_SOURCES.md','assets/public/AUTHORITATIVE_SOURCE_AUDIT.md','assets/public/FIGURE_AUDIT.md','assets/public/fallback-mission.svg','assets/public/figures/navigation-state-products.svg','assets/public/figures/esm-propulsion-architecture.svg','assets/public/figures/trajectory-correction-plan-execution.svg','assets/public/figures/entry-recovery-sequence.svg','assets/public/figures/gnc-proximity-loop.svg','PUBLIC_EXPERIENCE_FINAL_README.md']
REPO_DEPS=['data/reference/artemis_ii_gnc_architecture.json','data/reference/artemis_ii_manual_piloting_control_modes.json','data/reference/artemis_ii_entry_events.json','data/reference/artemis_ii_maneuver_plan_execution.json','data/reference/artemis_ii_phase2_closure_manifest.json','scripts/ingestion/parse_oem.py','scripts/processing/add_lunar_geometry.py','scripts/analysis/refine_lunar_closest_approach.py','docs/assets/entry/phase2e_sutton_graves_heat_flux.svg','docs/assets/lunar_science/phase6b_lunar_observation_reconstruction.svg']
FORBIDDEN=[r'technical\s+paper',r'engineering\s+paper',r'\bmanuscript\b',r'flight-qualified simulation',r'mission telemetry replay',r'navigation filter reconstruction']
REQUIRED_IDS=['mission-canvas','mission-scrubber','crew-photo','crew-scrubber','crew-geometry-canvas','crew-image-prev','crew-image-next','crew-image-count','gnc-canvas','gnc-start','gnc-mode-auto','gnc-mode-manual','gnc-disturbance','gnc-autopilot-status','mc-canvas','entry-canvas','entry-scrubber','maneuver-canvas','dv-magnitude','maneuver-hud-shift','weather-canvas','shielding-assumption','weather-action','psi-canvas','psi-cant','psi-angle','psi-hardware-risk']
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
 pages=[ROOT/'index.html',ROOT/'library.html',ROOT/'technical-report.html']; parsed={}
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
 text='\n'.join((ROOT/n).read_text(encoding='utf8') for n in ['index.html','styles.css','app.js','library.html','library.js','technical-report.html'] if (ROOT/n).exists())
 for pat in FORBIDDEN:
  if re.search(pat,text,re.I):fail.append('forbidden public claim/term: '+pat)
 ip=parsed.get((ROOT/'index.html').resolve())
 if ip:
  miss=[x for x in REQUIRED_IDS if x not in ip.ids]
  if miss:fail.append('missing interaction surfaces: '+', '.join(miss))
  notes += [f'interactive canvas surfaces: {len(ip.canvases)}',f'optional engineering drawers: {ip.details}']
 for phrase in ['NASA REPORTED','MISSIONLAB DERIVED','MODELED','INFERRED','UNKNOWN / NOT PUBLIC','ARTEMIS II DID NOT LAND ON THE MOON','Artemis IV','Sutton','8,281.938','6,544.538','36.76','RTC1','RTC2','RTC3']:
  if phrase.lower() not in text.lower():fail.append('missing required concept: '+phrase)
 for phrase in ['AUTO MODE','MANUAL MODE','Introduce disturbance','MissionLab shorthand','WHY CANT MATTERS','WHY SPREAD MATTERS','WHAT WOULD OPERATORS CARE ABOUT?']:
  if phrase.lower() not in text.lower():fail.append('missing final-polish UX concept: '+phrase)
 app=(ROOT/'app.js').read_text(encoding='utf8')
 crew_count=len(re.findall(r'\"id\":\"(?:art|jsc)[^\"]+\"',app))
 notes.append(f'Through Orion windows moments: {crew_count}')
 if crew_count!=25:fail.append(f'expected 25 Through Orion windows moments, found {crew_count}')
 if 'phase2e_sutton_graves_heat_flux.svg' not in text:fail.append('correct Sutton-Graves asset not referenced')
 if 'phase2e_convective_heating.svg' in text:fail.append('obsolete Sutton-Graves filename referenced')
 l=(ROOT/'library.js').read_text(encoding='utf8'); tids=set(re.findall(r"\bid:'([^']+)'",l));notes.append(f'Mission Library deep dives: {len(tids)}')
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
