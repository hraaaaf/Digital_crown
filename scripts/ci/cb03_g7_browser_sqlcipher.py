"""Disposable browser smoke: real CrownBotChat -> loopback FastAPI -> SQLCipher."""
import os,subprocess,sys,time,secrets,re
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import requests
from playwright.sync_api import sync_playwright
from backend import database,models
from backend.security import get_password_hash
from sqlalchemy import inspect
assert os.getenv("GITHUB_ACTIONS")=="true" and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME")=="1"
assert os.getenv("CB03_G7_SOURCE_HEAD")==subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
assert database.engine.dialect.name=="sqlite" and "pysqlcipher" in database.engine.url.drivername
assert not inspect(database.engine).get_table_names()
from backend.models_document_provenance_p3 import install_document_provenance_p3
install_document_provenance_p3()
models.Base.metadata.create_all(database.engine)
from backend.core.appointment_revision_ddl import install_appointment_revision_guard,install_appointment_overlap_index
with database.engine.begin() as c:
    install_appointment_revision_guard(c);install_appointment_overlap_index(c)
password=secrets.token_urlsafe(25)
with database.SessionLocal() as s:
    u=models.User(email="browser-g7@synthetic.invalid",hashed_password=get_password_hash(password),role=models.UserRole.DENTISTE,nom_complet="Synthetic Dentist",is_active=True,is_licensed=True,approval_status=models.ApprovalStatus.APPROVED.value)
    s.add(u);s.flush()
    p=models.Patient(numero_dossier="G7-001",nom="BENALI",prenom="SALMA",sexe="F",date_naissance=datetime(1990,1,1),employer_id=u.id)
    s.add(p);s.commit();uid=u.id;pid=p.id
base="http://127.0.0.1:8899"
env=os.environ.copy()
env.update({k:"true" for k in ("CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED","CROWN_BOT_GUIDED_NLU_ENABLED","CROWN_BOT_CB03_PREPARATION_ENABLED","CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED","CROWN_BOT_CB03_CONFIRMATION_ENABLED")})
env.update(CLOUD_AI_ENABLED="false",TELEMETRY_ENABLED="false",ALLOWED_ORIGINS="http://127.0.0.1:5173")
backend=None;vite=None
def ready(url,proc):
    for _ in range(150):
        if proc.poll() is not None:raise RuntimeError("server exited")
        try:
            if requests.get(url,timeout=1).status_code in (200,404):return
        except requests.RequestException:pass
        time.sleep(.2)
    raise RuntimeError("server timeout")
try:
    backend=subprocess.Popen([sys.executable,"-m","uvicorn","backend.main:app","--host","127.0.0.1","--port","8899","--lifespan","off"],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    ready(base+"/openapi.json",backend)
    r=requests.post(base+"/api/auth/login",data={"username":"browser-g7@synthetic.invalid","password":password},timeout=20)
    assert r.status_code==200,r.text[:250]
    front=env.copy()
    front.update(VITE_CB03_G5_CHAT_LAB="true",VITE_CB03_G5_REAL_CHAT_PG="true",VITE_CB03_G5_LAB_PRACTITIONER_ID=str(uid),VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED="true",VITE_CROWN_BOT_GUIDED_NLU_ENABLED="true",VITE_CROWN_BOT_CB03_CHAT_ENABLED="true",VITE_CROWN_BOT_CB03_G3_ENABLED="true",VITE_CB03_G4_NATIVE_A11Y_LAB="true",VITE_API_URL=base)
    vite=subprocess.Popen(["node","node_modules/vite/bin/vite.js","--host","127.0.0.1","--port","5173","--strictPort"],cwd="frontend",env=front,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    ready("http://127.0.0.1:5173/cb03-g5-chat-lab.html",vite)
    day=datetime.now(ZoneInfo("Africa/Casablanca"))+timedelta(days=22)
    while day.weekday()!=0:day+=timedelta(days=1)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        ctx=browser.new_context(viewport={"width":1280,"height":900},locale="fr-FR")
        ctx.add_cookies([{"name":"access_token","value":r.json()["access_token"],"url":base,"httpOnly":True,"secure":False,"sameSite":"Lax"}])
        page=ctx.new_page();posts=[]
        page.on("request",lambda q:posts.append(q.url) if q.method=="POST" and "/api/bot/guided/" in q.url else None)
        page.goto("http://127.0.0.1:5173/cb03-g5-chat-lab.html")
        page.get_by_role("button",name="Ouvrir CrownBot").click()
        page.get_by_role("textbox",name="Votre message à Crown Bot").fill(f"Prépare un RDV le {day.date().isoformat()} à 10h pour Mme Benali contrôle")
        page.get_by_role("button",name="Envoyer").click()
        page.get_by_text("SALMA BENALI · Dossier G7-001").wait_for(timeout=30000)
        confirm=page.get_by_role("button",name="Confirmer explicitement cette action")
        assert not confirm.is_enabled()
        page.get_by_role("checkbox",name=re.compile("J’ai vérifié le patient")).check()
        confirm.click()
        page.get_by_text(re.compile("Action confirmée|Rendez-vous créé|RDV créé")).wait_for(timeout=25000)
        assert sum("/prepare-appointment" in q for q in posts)==1
        assert sum("/confirm" in q for q in posts)==1
        with database.SessionLocal() as s:
            actions=s.query(models.BotPendingAction).filter_by(employer_id=uid,status="executed").all()
            assert len(actions)==1
            receipt=actions[0].params_json["_cb03_receipt"]
            assert receipt["status"]=="CREATED"
            assert s.get(models.Appointment,receipt["appointment_id"]).patient_id==pid
        Path("artifacts/cb03-g7").mkdir(parents=True,exist_ok=True)
        page.screenshot(path="artifacts/cb03-g7/browser-sqlcipher.png",full_page=True)
        browser.close()
    print("CB03_G7_REAL_BROWSER_SQLCIPHER_PASS")
finally:
    for proc in (vite,backend):
        if proc and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=8)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
