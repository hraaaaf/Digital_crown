"""Synthetic only: actual G6 MainLayout + real G5 chat themed in browser.

No real HTTP clinical routes: intercepted fixture expressly tests VISUAL COLOURS only.
It must never be reported as SQLCipher, native Windows zoom or clinical E2E.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import time
from playwright.sync_api import sync_playwright

assert os.getenv("GITHUB_ACTIONS") == "true"
assert os.getenv("CB2_THEME_MATRIX_EXPERIMENT") == "1"
assert os.getenv("CLOUD_AI_ENABLED") == "false"
assert os.getenv("TELEMETRY_ENABLED") == "false"
ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "artifacts" / "cb2-theme-matrix"
ARTIFACT.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:5173/cb03-g6-mainlayout-lab.html"
STATES = ["default", "emerald", "rose", "ocean", "graphite",
          "prestige", "dark", "high-contrast"]
env=os.environ.copy()
env.update({
    "VITE_CB03_G6_MAINLAYOUT_LAB": "true",
    "VITE_CROWN_BOT_CB03_CHAT_ENABLED": "true",
    "VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED": "true",
    "VITE_CROWN_BOT_GUIDED_NLU_ENABLED": "true",
    "VITE_CROWN_BOT_CB03_G3_ENABLED": "true",
    "VITE_CB03_G5_LAB_PRACTITIONER_ID": "9",
    "VITE_CB03_G4_NATIVE_A11Y_LAB": "true",
    "VITE_CB2_THEME_MATRIX_EXPERIMENT": "true",
    "VITE_API_URL": "http://127.0.0.1:8899",
})
vite=subprocess.Popen(["node","node_modules/vite/bin/vite.js",
                       "--host","127.0.0.1","--port","5173","--strictPort"],
                      cwd=ROOT/"frontend",env=env,stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
try:
    import requests
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        assert vite.poll() is None,"Vite failed"
        try:
            if requests.get(URL,timeout=1).status_code==200:break
        except requests.RequestException:
            pass
        time.sleep(.2)
    else:
        raise AssertionError("Vite unavailable")

    fake_preparation={
      "status":"prepared","executable":False,
      "preparation_id":"f3bbd173-bf01-4ce6-99c1-5ca1e8010001",
      "expires_at":"2026-11-01T12:30:00",
      "summary":{
        "patient":{"id":21,"prenom":"Salma","nom":"Benali","numero_dossier":"S-21"},
        "praticien_id":9,"resource_id":None,"datetime_start":"2026-11-07T10:00:00",
        "duration_minutes":30,"motif":"CONTROLE"
      },
    }
    evidence=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1280,"height":900},locale="fr-FR")
        clinical_posts=[]
        def route_generic(route):
            route.fulfill(status=404,content_type="application/json",body="{}",
                          headers={"access-control-allow-origin":"*"})
        def route_sessions(route):
            route.fulfill(status=200,content_type="application/json",body="[]",
                          headers={"access-control-allow-origin":"*"})
        def route_guided(route):
            req=route.request
            clinical_posts.append(req.method+" "+req.url.split("/api/")[-1])
            if req.method=="OPTIONS":
                route.fulfill(status=204, headers={
                    "access-control-allow-origin":"*",
                    "access-control-allow-methods":"POST,GET,OPTIONS",
                    "access-control-allow-headers":"content-type,authorization"
                })
                return
            if req.method=="POST" and req.url.endswith("/prepare-appointment"):
                route.fulfill(status=200,content_type="application/json",
                    body=json.dumps(fake_preparation),
                    headers={"access-control-allow-origin":"*"})
                return
            raise AssertionError("REFUSED: test must not confirm or write clinical results")
        page.route("**/api/**",route_generic)
        page.route("**/api/bot/sessions",route_sessions)
        page.route("**/api/bot/guided/**",route_guided)
        page.goto(URL,wait_until="domcontentloaded",timeout=45000)
        page.get_by_role("button",name="Ouvrir CrownBot").first.click()
        panel=page.get_by_role("region",name="Conversation Crown Bot — actions guidées CB-03")
        panel.wait_for(timeout=25000)
        box=page.get_by_role("textbox",name="Votre message à Crown Bot")
        box.fill("Prépare un RDV demain 10h pour Mme Benali contrôle")
        page.get_by_role("button",name="Envoyer").click()
        receipt=page.locator('[aria-label="Récapitulatif vérifié par le serveur"]')
        receipt.wait_for(timeout=20000)
        assert clinical_posts.count("POST bot/guided/prepare-appointment")==1
        assert not any("confirm" in x for x in clinical_posts)
        consent=page.get_by_role("checkbox",name=re.compile("J’ai vérifié le patient"))
        assert not consent.is_checked()
        btn=page.get_by_role("button",name="Confirmer explicitement cette action")
        assert not btn.is_enabled()
        for theme in STATES:
            page.evaluate("(t)=>{document.documentElement.setAttribute('data-theme',t)}",theme)
            page.wait_for_timeout(180)
            style=page.evaluate("""() => {
                const root=document.documentElement;
                const panel=document.querySelector('section[aria-label="Conversation Crown Bot — actions guidées CB-03"]');
                const card=document.querySelector('[aria-label="Récapitulatif vérifié par le serveur"]');
                const button=[...document.querySelectorAll('button')].find(x=>x.textContent?.includes('Confirmer explicitement cette action'));
                if (!panel || !card || !button) throw Error('Missing semantic UI');
                const styles=x=>{const z=getComputedStyle(x);return {background:z.backgroundColor,color:z.color,border:z.borderTopColor}};
                const computed=getComputedStyle(root);
                const probe=document.createElement('div');probe.style.backgroundColor='var(--bg-medical-pearl)';
                root.append(probe);const rootBg=getComputedStyle(probe).backgroundColor;probe.remove();
                return {panel:styles(panel),card:styles(card),button:styles(button),
                        rootBg,themeColor:computed.getPropertyValue('--text-main').trim(),
                        primary:computed.getPropertyValue('--primary').trim(),
                        onPrimary:computed.getPropertyValue('--text-on-primary').trim()};
            }""")
            # Actual computed styles, not just a color token name in JSX.
            assert style["panel"]["background"] == style["rootBg"],(theme,style)
            assert style["panel"]["background"] != "rgba(0, 0, 0, 0)",(theme,style)
            page.screenshot(path=str(ARTIFACT/("g5-"+theme+"-1280.png")),full_page=True)
            assert not btn.is_enabled()
            evidence.append({"theme":theme,"styles":style})
        browser.close()
    output={
        "schema":"CB2_G5_THEME_VISUAL_MATRIX_SYNTHETIC_V1",
        "sourceSha":subprocess.check_output(["git","rev-parse","HEAD"],
                                             cwd=ROOT,text=True).strip(),
        "realMainLayout":True,"realCrownBotChat":True,"realClinicalBackend":False,
        "nativeWindowsZoom":False,"NVDA":False,"themes":evidence,
        "syntheticOnly":True,"clinicalConfirmPosts":0,
        "captures":len(STATES),
        "limitations":["CI Linux Chromium, not Windows native zoom/assistive tech",
                       "Visual mock server only; separate G7 provides real SQLCipher integration",
                       "A human must approve new exact-SHA screenshots"] 
    }
    (ARTIFACT/"report.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",
                                         encoding="utf-8")
    print("CB2_G5_THEME_MATRIX_PASS",json.dumps({
          "themes":[x["theme"] for x in evidence],
          "captures":len(STATES),"realClinicalBackend":False
    }))
finally:
    if vite.poll() is None:
        vite.terminate()
        try: vite.wait(timeout=8)
        except subprocess.TimeoutExpired: vite.kill();vite.wait(timeout=8)
