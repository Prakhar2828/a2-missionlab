from __future__ import annotations
import argparse, html, json, os, re, shutil, subprocess, tempfile, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,format,*args): pass

def browser_paths():
    found={}; candidates={"edge":[],"chrome":[]}
    if os.name=="nt":
        env=os.environ
        options=[
            ("PROGRAMFILES(X86)","Microsoft/Edge/Application/msedge.exe","edge"),("PROGRAMFILES","Microsoft/Edge/Application/msedge.exe","edge"),("LOCALAPPDATA","Microsoft/Edge/Application/msedge.exe","edge"),
            ("PROGRAMFILES","Google/Chrome/Application/chrome.exe","chrome"),("PROGRAMFILES(X86)","Google/Chrome/Application/chrome.exe","chrome"),("LOCALAPPDATA","Google/Chrome/Application/chrome.exe","chrome")]
        for key,relative,name in options:
            base=env.get(key)
            if base:candidates[name].append(Path(base)/relative)
    else:
        for executable,name in [("microsoft-edge","edge"),("microsoft-edge-stable","edge"),("google-chrome","chrome"),("google-chrome-stable","chrome"),("chromium","chrome"),("chromium-browser","chrome")]:
            path=shutil.which(executable)
            if path:candidates[name].append(Path(path))
    for name,paths in candidates.items():
        for path in paths:
            if path.is_file():found[name]=path.resolve();break
    return found

def run_browser(name,executable,url):
    profile=Path(tempfile.mkdtemp(prefix=f"a2-space-weather-{name}-"))
    try:
        command=[str(executable),"--headless=new","--disable-gpu","--disable-dev-shm-usage","--no-first-run","--no-default-browser-check","--disable-background-networking","--disable-background-timer-throttling","--disable-backgrounding-occluded-windows","--disable-renderer-backgrounding","--run-all-compositor-stages-before-draw","--disable-component-update","--disable-sync","--metrics-recording-only","--mute-audio","--window-size=1200,1100","--virtual-time-budget=12000","--user-data-dir="+str(profile),"--dump-dom",url]
        if os.name!="nt":command.insert(1,"--no-sandbox")
        try:
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=30)
        except subprocess.TimeoutExpired:
            print();print(f"[{name.upper()}]");print("FAIL: browser regression timed out before DOM capture completed.")
            return False
        dom=result.stdout or ""
        def attr(key):
            m=re.search(rf'{re.escape(key)}="([^"]+)"',dom,re.I);return m.group(1) if m else "MISSING"
        keys=["data-status","data-baseline-pass","data-threshold-pass","data-location-pass","data-dose-pass","data-evidence-pass","data-canvas-pass","data-overflow-pass","data-finite-pass"]
        values={k:attr(k) for k in keys}
        print();print(f"[{name.upper()}]")
        for k,v in values.items():print(k.replace('data-','').replace('-',' ')+':',v)
        passed=values["data-status"]=="PASS" and all(values[k]=="true" for k in keys[1:])
        if not passed:
            m=re.search(r'<pre id="results">(.*?)</pre>',dom,re.I|re.S)
            if m:
                details=html.unescape(m.group(1)).strip()
                try:print(json.dumps(json.loads(details),indent=2))
                except Exception:print(details[:16000])
            if result.stderr:print("Browser stderr:\n"+result.stderr[-4000:])
            return False
        print("PASS:",name,"space weather measurement / evidence regression")
        return True
    finally:
        shutil.rmtree(profile,ignore_errors=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--required",action="store_true");args=parser.parse_args();found=browser_paths()
    if not found:
        print("FAIL: no compatible browser found." if args.required else "SKIP: no compatible browser found.");return 1 if args.required else 0
    if args.required and os.name=="nt":
        missing=[name for name in ("edge","chrome") if name not in found]
        if missing:print("FAIL: required Windows browser(s) missing:",", ".join(missing));return 1
    old=Path.cwd();os.chdir(ROOT);server=ThreadingHTTPServer(("127.0.0.1",0),Quiet);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f"http://127.0.0.1:{server.server_address[1]}/scripts/validation/space_weather_regression.html"
    outcomes={}
    try:
        for name in sorted(found):outcomes[name]=run_browser(name,found[name],url)
    finally:
        server.shutdown();server.server_close();os.chdir(old)
    failures=[name for name,passed in outcomes.items() if not passed]
    if failures:print();print("FAIL: Space weather regression failed in:",", ".join(failures));return 1
    print();print("="*78);print("PHASE H SPACE WEATHER EDUCATIONAL MODEL REGRESSION PASSED");print("Browsers:",", ".join(name.upper() for name in sorted(outcomes)));print("Verified: physical baseline, NOAA S1-S5 thresholds, location invariance, dose boundary, NAIRAS version evidence, finite output, canvas render, mobile overflow");print("="*78);return 0
if __name__=="__main__":raise SystemExit(main())
