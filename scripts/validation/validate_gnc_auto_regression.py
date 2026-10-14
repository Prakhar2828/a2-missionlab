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
            ("PROGRAMFILES(X86)","Microsoft/Edge/Application/msedge.exe","edge"),
            ("PROGRAMFILES","Microsoft/Edge/Application/msedge.exe","edge"),
            ("LOCALAPPDATA","Microsoft/Edge/Application/msedge.exe","edge"),
            ("PROGRAMFILES","Google/Chrome/Application/chrome.exe","chrome"),
            ("PROGRAMFILES(X86)","Google/Chrome/Application/chrome.exe","chrome"),
            ("LOCALAPPDATA","Google/Chrome/Application/chrome.exe","chrome"),
        ]
        for key,relative,name in options:
            base=env.get(key)
            if base:candidates[name].append(Path(base)/relative)
    else:
        for executable,name in [
            ("microsoft-edge","edge"),("microsoft-edge-stable","edge"),("google-chrome","chrome"),
            ("google-chrome-stable","chrome"),("chromium","chrome"),("chromium-browser","chrome")
        ]:
            path=shutil.which(executable)
            if path:candidates[name].append(Path(path))
    for name,paths in candidates.items():
        for path in paths:
            if path.is_file():found[name]=path.resolve();break
    return found

def run_browser(name,executable,url):
    with tempfile.TemporaryDirectory(prefix=f"a2-gnc-r4-{name}-") as profile:
        command=[
            str(executable),"--headless=new","--disable-gpu","--disable-dev-shm-usage","--no-first-run","--no-default-browser-check",
            "--disable-background-networking","--disable-background-timer-throttling","--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding","--run-all-compositor-stages-before-draw","--disable-component-update","--disable-sync",
            "--metrics-recording-only","--mute-audio","--window-size=1200,1000","--virtual-time-budget=12000",
            "--user-data-dir="+profile,"--dump-dom",url
        ]
        if os.name!="nt":command.insert(1,"--no-sandbox")
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=30)
        dom=result.stdout or ""
        def attr(name):
            match=re.search(rf'{re.escape(name)}="([^"]+)"',dom,re.I)
            return match.group(1) if match else "MISSING"
        values={
            "status":attr("data-status"),"capture":attr("data-browser-capture-seconds"),"min":attr("data-cadence-min"),
            "max":attr("data-cadence-max"),"spread":attr("data-cadence-spread"),"recovery":attr("data-max-recovery-seconds"),
            "phases":attr("data-phase-count"),"manual":attr("data-manual-command-pass"),"manual_dist":attr("data-manual-disturbance-pass"),
            "auto_dist":attr("data-auto-disturbance-pass"),"canvas":attr("data-canvas-pass")
        }
        print();print(f"[{name.upper()}]");print("Status:",values["status"])
        print("Browser-driven AUTO capture:",values["capture"],"simulation seconds")
        print("Cadence capture range:",values["min"],"to",values["max"],"seconds")
        print("Cadence spread:",values["spread"],"seconds")
        print("Max deterministic disturbance recovery:",values["recovery"],"seconds")
        print("Progress history entries:",values["phases"])
        print("Manual THC/RHC response:",values["manual"])
        print("Manual disturbance:",values["manual_dist"])
        print("Auto disturbance:",values["auto_dist"])
        print("Canvas render path:",values["canvas"])
        passed=values["status"]=="PASS" and all(values[key]=="true" for key in ("manual","manual_dist","auto_dist","canvas"))
        if not passed:
            match=re.search(r'<pre id="results">(.*?)</pre>',dom,re.I|re.S)
            if match:
                details=html.unescape(match.group(1)).strip()
                try:print(json.dumps(json.loads(details),indent=2))
                except Exception:print(details[:20000])
            if result.stderr:print("Browser stderr:\n"+result.stderr[-4000:])
            return False
        print("PASS:",name,"GNC deterministic browser regression")
        return True

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--required",action="store_true");args=parser.parse_args()
    found=browser_paths()
    if not found:
        print("FAIL: no compatible browser found." if args.required else "SKIP: no compatible browser found.")
        return 1 if args.required else 0
    if args.required and os.name=="nt":
        missing=[name for name in ("edge","chrome") if name not in found]
        if missing:print("FAIL: required Windows browser(s) missing:",", ".join(missing));return 1
    old=Path.cwd();os.chdir(ROOT);server=ThreadingHTTPServer(("127.0.0.1",0),Quiet)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f"http://127.0.0.1:{server.server_address[1]}/scripts/validation/gnc_auto_regression.html"
    outcomes={}
    try:
        for name in sorted(found):outcomes[name]=run_browser(name,found[name],url)
    finally:
        server.shutdown();server.server_close();os.chdir(old)
    failures=[name for name,passed in outcomes.items() if not passed]
    if failures:print();print("FAIL: GNC regression failed in:",", ".join(failures));return 1
    print();print("="*78);print("GNC DETERMINISTIC AUTO / MANUAL REGRESSION PASSED")
    print("Browsers:",", ".join(name.upper() for name in sorted(outcomes)))
    print("AUTO target: 15-20 simulation seconds")
    print("Cadences: 60, 30, 15, 5, 2, and 1 FPS equivalent")
    print("Cadence spread target: <= 0.5 seconds")
    print("Disturbance recovery target: <= 12 seconds");print("="*78)
    return 0
if __name__=="__main__":raise SystemExit(main())
