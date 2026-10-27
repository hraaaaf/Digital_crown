"""CB-03 G8: real MainLayout Chromium → G1/G2 FastAPI → SQLCipher SIGKILL.

CI-only. Real G2 SQL transaction paused by test-only SQLite UDF trigger,
then SIGKILL (rollback). Second action uses genuine MainLayout CrownBotChat,
a real SQLCipher commit and SIGKILL before HTTP ACK; UI reconciles via GET.
No production path, existing database, mock clinical HTTP, or real patient.
"""
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from playwright.sync_api import sync_playwright
from sqlalchemy import inspect,text

head=os.environ.get("CB03_G8_SOURCE_HEAD","")
temp=Path(os.environ.get("RUNNER_TEMP","/nonexistent")).resolve()
dbfile=temp/"cb03-g8-synthetic.db"
media=temp/"cb03-g8-rehearsal-media"
dburl="sqlite:///"+str(dbfile)
assert (os.environ.get("GITHUB_ACTIONS")=="true"
    and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME")=="1"
    and os.environ.get("CB03_G8_LAB")=="1"
    and os.environ.get("ENVIRONMENT")=="rehearsal"
    and len(head)==40
    and subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()==head
    and os.environ.get("DATABASE_URL")==dburl
    and len(bytes.fromhex(os.environ.get("SQLCIPHER_KEY_HEX","")))==32
    and not dbfile.exists() and not media.exists())
media.mkdir(mode=0o700)
from backend.core.runtime_safety import database_target_fingerprint
os.environ["DIGITALCROWN_ISOLATION_DB_FINGERPRINT"]=database_target_fingerprint(dburl)
os.environ["MEDIA_ROOT"]=str(media)
from backend import database,models
from backend.security import get_password_hash
from backend.core.appointment_revision_ddl import install_appointment_revision_guard,install_appointment_overlap_index
from backend.models_document_provenance_p3 import install_document_provenance_p3

assert database.engine.dialect.name=="sqlite"
assert "pysqlcipher" in database.engine.url.drivername
assert not inspect(database.engine).get_table_names(),"REFUSED_EXISTING_TABLES"
install_document_provenance_p3()
models.Base.metadata.create_all(bind=database.engine)
with database.engine.begin() as conn:
    install_appointment_revision_guard(conn)
    install_appointment_overlap_index(conn)
    conn.execute(text("CREATE TABLE cb03_g8_pause_action (id VARCHAR(36) PRIMARY KEY)"))
    conn.execute(text("""
      CREATE TRIGGER cb03_g8_pause_before_commit
      BEFORE UPDATE OF status ON bot_pending_actions
      FOR EACH ROW
      WHEN NEW.status='executed' AND OLD.status='executing'
       AND EXISTS (SELECT 1 FROM cb03_g8_pause_action WHERE id=NEW.id)
      BEGIN SELECT cb03_g8_precommit_pause(); END
    """))
password=secrets.token_urlsafe(28)
email="cb03-g8-ci@synthetic.invalid"
with database.SessionLocal() as s:
    owner=models.User(email=email,hashed_password=get_password_hash(password),
        role=models.UserRole.DENTISTE,nom_complet="G8 Synthetic Dentist",
        is_active=True,is_licensed=True,approval_status=models.ApprovalStatus.APPROVED.value)
    s.add(owner);s.flush()
    patient=models.Patient(numero_dossier="G8-001",nom="BENALI",prenom="SALMA",
        sexe="F",date_naissance=datetime(1990,1,1),employer_id=owner.id)
    s.add(patient);s.flush()
    old=models.Appointment(employer_id=owner.id,patient_id=patient.id,
        praticien_id=owner.id,datetime_start=datetime.now()+timedelta(days=34),
        duration_minutes=30,motif="G8 precommit synthetic",
        status=models.AppointmentStatus.PREVU)
    s.add(old);s.commit()
    uid=owner.id;pid=patient.id;old_id=old.id

base="http://127.0.0.1:8899"
root=Path(__file__).resolve().parents[2]
marker=temp/"cb03-g8-precommit.marker"
ack=temp/"cb03-g8-postcommit.marker"
artifact=Path("artifacts/cb03-g8")
artifact.mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
env.update({
    "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED":"true",
    "CROWN_BOT_GUIDED_NLU_ENABLED":"true",
    "CROWN_BOT_CB03_PREPARATION_ENABLED":"true",
    "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED":"true",
    "CROWN_BOT_CB03_CONFIRMATION_ENABLED":"true",
    "CLOUD_AI_ENABLED":"false",
    "TELEMETRY_ENABLED":"false",
    "ALLOWED_ORIGINS":"http://127.0.0.1:5173",
    "CB03_G8_SERVER":"1",
})
backend=None;vite=None;report=[]
def until(check,timeout,label):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if check():return
        time.sleep(.12)
    raise AssertionError("TIMEOUT_"+label)
def ready(url,proc):
    def good():
        if proc.poll() is not None:
            raise AssertionError("EARLY_SERVER_EXIT "+(proc.stdout.read()[-6000:] if proc.stdout else ""))
        try:return requests.get(url,timeout=1).status_code in (200,404)
        except requests.RequestException:return False
    until(good,32,"FASTAPI_OR_VITE")
def start(*,pre=False,post=False):
    e=env.copy()
    e.update(CB03_G8_HOLD_PRECOMMIT="1" if pre else "0",
        CB03_G8_WITHHOLD_ACK="1" if post else "0")
    proc=subprocess.Popen([sys.executable,"-m","uvicorn",
        "scripts.ci.cb03_g8_sqlcipher_server:app","--host","127.0.0.1",
        "--port","8899","--lifespan","off","--log-level","warning"],
        cwd=root,env=e,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    ready(base+"/openapi.json",proc)
    return proc
def stop(proc,kill=False):
    if proc and proc.poll() is None:
        if kill:os.kill(proc.pid,signal.SIGKILL)
        else:proc.terminate()
        proc.wait(timeout=12)
        if kill:assert proc.returncode==-signal.SIGKILL,proc.returncode
def login():
    response=requests.post(base+"/api/auth/login",data={"username":email,"password":password},timeout=20)
    assert response.status_code==200,("LOGIN",response.status_code,response.text[:350])
    return response.json()["access_token"]
def post(token,endpoint,payload,timeout=40):
    return requests.post(base+endpoint,json=payload,
        headers={"Authorization":"Bearer "+token},timeout=timeout)
def audits(id):
    with database.SessionLocal() as s:
        return s.query(models.AuditLog).filter_by(
            action="CB03_ACTION_CONFIRMED",resource_id=id,employer_id=uid).count()

try:
    # A: true FastAPI G2 status mutation, OS SIGKILL while SQLCipher is still
    # inside the uncommitted transaction (test trigger runs at final UPDATE).
    backend=start(pre=True)
    token=login()
    req=post(token,"/api/bot/guided/prepare-status",{
        "selected_appointment_id":old_id,
        "utterance":"Prépare le statut du RDV en salle d'attente"})
    assert req.status_code==200,("G1_STATUS",req.status_code,req.text[:450])
    action_id=req.json()["preparation_id"]
    with database.SessionLocal() as s:
        start_revision=int(s.get(models.Appointment,old_id).clinical_revision)
    with database.engine.begin() as conn:
        conn.execute(text("INSERT INTO cb03_g8_pause_action (id) VALUES (:id)"),{"id":action_id})

    def confirm_and_lose_connection():
        try:
            response=post(token,"/api/bot/guided/confirm",{
                "preparation_id":action_id,"confirm":True},timeout=45)
            return {"status":response.status_code}
        except requests.RequestException:
            return {"transport_failed":True}
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(confirm_and_lose_connection)
        until(marker.exists,25,"ACTUAL_G2_PRECOMMIT_PAUSE")
        stop(backend,kill=True);backend=None
        result=future.result(timeout=12)
    assert result.get("transport_failed") is True,result
    with database.SessionLocal() as s:
        a=s.get(models.Appointment,old_id)
        assert a.status==models.AppointmentStatus.PREVU,a.status
        assert int(a.clinical_revision)==start_revision
        assert s.get(models.BotPendingAction,action_id).status=="prepared"
    assert audits(action_id)==0
    # Proof from real API: GET only, no blind replay.
    backend=start()
    token=login()
    follow=requests.get(base+"/api/bot/guided/actions/"+action_id,
        headers={"Authorization":"Bearer "+token},timeout=20)
    assert follow.status_code==200,follow.text[:350]
    assert follow.json()["status"]=="prepared"
    assert follow.json()["safe_to_retry_automatically"] is False
    stop(backend);backend=None
    report.append({"scenario":"G2_SQLCIPHER_PRECOMMIT_OS_SIGKILL",
        "actual_sigkill":True,"real_fastapi_route":True,
        "uncommitted_marker":True,"transport_failed":True,
        "appointment_revision_delta":0,"audit":0,"action":"prepared",
        "read_only_get":True})
    print("CB03_G8_REAL_G2_SQLCIPHER_PRECOMMIT_SIGKILL_PASS",flush=True)

    # B: ACTUAL MainLayout contains the real CrownBotChat. POST G2 commits,
    # ASGI withholds 200 headers, OS SIGKILL, UI GET reconciles without retry.
    backend=start(post=True)
    token=login()
    front=env.copy()
    front.update({
        "VITE_CB03_G8_MAINLAYOUT_LAB":"true",
        "VITE_CB03_G8_SYNTHETIC_OWNER_ID":str(uid),
        "VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED":"true",
        "VITE_CROWN_BOT_GUIDED_NLU_ENABLED":"true",
        "VITE_CROWN_BOT_CB03_CHAT_ENABLED":"true",
        "VITE_CROWN_BOT_CB03_G3_ENABLED":"true",
        "VITE_CB03_G4_NATIVE_A11Y_LAB":"true",
        "VITE_API_URL":base,
    })
    vite=subprocess.Popen(["node","node_modules/vite/bin/vite.js","--host",
        "127.0.0.1","--port","5173","--strictPort"],
        cwd=root/"frontend",env=front,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    url="http://127.0.0.1:5173/cb03-g8-mainlayout-lab.html"
    ready(url,vite)
    day=datetime.now(ZoneInfo("Africa/Casablanca"))+timedelta(days=22)
    while day.weekday()!=0:day+=timedelta(days=1)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        ctx=browser.new_context(viewport={"width":1280,"height":900},locale="fr-FR")
        ctx.add_cookies([{"name":"access_token","value":token,
            "url":base,"httpOnly":True,"secure":False,"sameSite":"Lax"}])
        page=ctx.new_page()
        posts=[];reads=[]
        page.on("request",lambda q:(
            posts.append(q.url) if q.method=="POST" else reads.append(q.url)
        ) if "/api/bot/guided/" in q.url else None)
        try:
            page.goto(url,wait_until="domcontentloaded",timeout=45000)
            page.locator("[data-cb01-workspace-shell]").wait_for(timeout=30000)
            page.locator("[data-cb03-g8-workspace]").wait_for()
            assert page.get_by_role("button",name="Ouvrir CrownBot").count()==1
            page.get_by_role("button",name="Ouvrir CrownBot").click()
            page.get_by_role("region",name="Conversation Crown Bot — actions guidées CB-03").wait_for(timeout=25000)
            page.get_by_role("textbox",name="Votre message à Crown Bot").fill(
                f"Prépare un RDV le {day.date().isoformat()} à 10h pour Mme Benali contrôle")
            page.get_by_role("button",name="Envoyer").click()
            page.get_by_text("SALMA BENALI · Dossier G8-001").wait_for(timeout=30000)
            confirm=page.get_by_role("button",name="Confirmer explicitement cette action")
            assert not confirm.is_enabled()
            page.get_by_role("checkbox",name=re.compile("J’ai vérifié le patient")).check()
            assert confirm.is_enabled()
            page.screenshot(path=str(artifact/"mainlayout-prepared.png"),full_page=True)
            confirm.click()
            until(ack.exists,25,"G2_SQLCIPHER_DURABLE_COMMIT_BEFORE_ACK")
            with database.SessionLocal() as s:
                actions=s.query(models.BotPendingAction).filter_by(
                    employer_id=uid,action_type="CREATE_APPOINTMENT",status="executed").all()
                assert len(actions)==1,("EXECUTED_ACTIONS",len(actions))
                committed_id=actions[0].id
                receipt=actions[0].params_json.get("_cb03_receipt")
                assert receipt and receipt["status"]=="CREATED",receipt
                booked=s.get(models.Appointment,receipt["appointment_id"])
                assert booked and booked.patient_id==pid and booked.employer_id==uid
            assert audits(committed_id)==1
            stop(backend,kill=True);backend=None
            page.get_by_text(re.compile("Résultat à réconcilier")).wait_for(timeout=25000)
            page.screenshot(path=str(artifact/"mainlayout-ack-lost.png"),full_page=True)
            backend=start()
            page.get_by_role("button",name="Vérifier l’état (lecture seule)").click()
            page.get_by_text(re.compile("Reçu retrouvé en lecture seule")).wait_for(timeout=25000)
            assert sum("/confirm" in u for u in posts)==1,posts
            assert sum("/prepare-appointment" in u for u in posts)==1,posts
            assert sum("/guided/actions/" in u for u in reads)==1,reads
            with database.SessionLocal() as s:
                assert s.query(models.BotPendingAction).filter_by(
                    id=committed_id,status="executed").count()==1
                assert s.query(models.Appointment).filter_by(
                    id=receipt["appointment_id"]).count()==1
            assert audits(committed_id)==1
            page.screenshot(path=str(artifact/"mainlayout-reconciled.png"),full_page=True)
            report.append({"scenario":"MAINLAYOUT_CROWNBOT_FASTAPI_SQLCIPHER_POSTCOMMIT_SIGKILL",
                "real_mainlayout":True,"real_crownbotchat":True,
                "real_fastapi":True,"sqlcipher":True,"actual_sigkill":True,
                "committed_before_ack":True,"ack_delivered":False,
                "recovered_by_ui_read_only_get":True,"confirm_posts":1,
                "read_only_get":1,"audit":1,"one_appointment":True})
            print("CB03_G8_MAINLAYOUT_SQLCIPHER_G2_LOST_ACK_PASS",flush=True)
        except Exception:
            page.screenshot(path=str(artifact/"mainlayout-failure.png"),full_page=True)
            raise
        finally:
            ctx.close();browser.close()
    (artifact/"report.json").write_text(json.dumps({
        "head":head,"rehearsal":True,"data":"synthetic_only",
        "mainlayout":"real component in CI-only router shell (not full ProtectedRoute)",
        "tests":report,
        "excluded":["production","real patient","Windows native","full App ProtectedRoute"],
    },indent=2)+"\n",encoding="utf-8")
    print("CB03_G8_TARGETED_SQLCIPHER_MAINLAYOUT_SIGKILL_PASS",flush=True)
finally:
    if vite is not None:stop(vite)
    if backend is not None:stop(backend)
