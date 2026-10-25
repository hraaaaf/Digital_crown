"""CB-03 G4-B: actual OS kills, real HTTP failure and real Chromium→FastAPI→PG.

CI-only. Exactly one virgin loopback PostgreSQL database; all persons are
invented. No Neon, no on-prem or installed application. Live server flags
enabled only in disposable child processes. No mocked /api/bot/guided routes.

Evidence boundaries: hosted Linux Chromium (NOT Windows/NVDA or clinician),
PostgreSQL only (NOT integrated SQLCipher), and two SIGKILL windows: before
COMMIT while transaction is open, and after COMMIT before HTTP ACK.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import requests
from sqlalchemy import text
from playwright.sync_api import sync_playwright

HEAD = os.getenv("CB03_G4B_SOURCE_HEAD", "")
# G5 adds the ACTUAL CrownBotChat in front of the already-proven G4B
# synthetic PG/real SIGKILL tests. Never silently switch the old G4B lab.
G5_CHAT = os.getenv("CB03_G5_REAL_CHAT_PG") == "1"
url = os.getenv("DATABASE_URL", "")
u = urlsplit(url)
if not (
    os.getenv("GITHUB_ACTIONS") == "true"
    and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
    and os.getenv("ENVIRONMENT") == "rehearsal"
    and u.scheme == "postgresql" and u.hostname == "127.0.0.1"
    and u.port == 5432 and u.username == "cb03_g4b"
    and u.path == "/cb03_g4b_disposable" and not u.query and not u.fragment
    and len(HEAD) == 40 and all(c in "0123456789abcdef" for c in HEAD)
    and subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip() == HEAD
):
    raise RuntimeError("REFUSED: G4B only on fresh loopback PG exact SHA")

base = "http://127.0.0.1:8899"
repo = Path(__file__).resolve().parents[2]
from backend import database, models
from backend.security import get_password_hash
from backend.core.schema_runtime import assert_database_at_current_head

assert database.engine.dialect.name == "postgresql"
assert_database_at_current_head(database.engine)
with database.SessionLocal() as s:
    assert s.query(models.User).count() == 0, "REFUSED: preexisting users"
    assert s.query(models.Patient).count() == 0, "REFUSED: preexisting patients"
    assert s.query(models.BotPendingAction).count() == 0, "REFUSED: preexisting actions"

password = secrets.token_urlsafe(28)
email = "g4b-lab-owner@synthetic.invalid"
with database.SessionLocal() as s:
    owner = models.User(email=email, hashed_password=get_password_hash(password),
        role=models.UserRole.DENTISTE, nom_complet="G4-B Synthetic Dentist",
        is_active=True, is_licensed=True,
        approval_status=models.ApprovalStatus.APPROVED.value)
    s.add(owner);s.flush()
    patient = models.Patient(numero_dossier="G4B-001", nom="BENALI", prenom="SALMA",
        sexe="F", date_naissance=datetime(1990,1,1), employer_id=owner.id)
    s.add(patient);s.flush()
    # This appointment is used only for the pre-commit kill.
    old_appt=models.Appointment(
        employer_id=owner.id, patient_id=patient.id, praticien_id=owner.id,
        datetime_start=datetime.now()+timedelta(days=34),
        duration_minutes=30, motif="G4B synthetic SIGKILL",
        status=models.AppointmentStatus.PREVU)
    s.add(old_appt);s.commit()
    owner_id=int(owner.id);patient_id=int(patient.id);old_appt_id=int(old_appt.id)

# Lab-only BEFORE UPDATE trigger pauses inside G2 after the business status
# change but BEFORE its one COMMIT. Parent observes backend pg_sleep and sends
# real SIGKILL. Trigger has no path to a real/nonempty database.
with database.engine.begin() as conn:
    conn.execute(text("""
      CREATE TABLE cb03_g4b_pause_action (
        id varchar(36) PRIMARY KEY
      )
    """))
    conn.execute(text("""
      CREATE FUNCTION cb03_g4b_pause_before_commit()
      RETURNS TRIGGER AS $$
      BEGIN
        IF NEW.status='executed' AND OLD.status='executing'
           AND EXISTS(SELECT 1 FROM cb03_g4b_pause_action WHERE id=NEW.id) THEN
          PERFORM pg_sleep(35);
        END IF;
        RETURN NEW;
      END;
      $$ LANGUAGE plpgsql
    """))
    conn.execute(text("""
      CREATE TRIGGER cb03_g4b_pause_action_trigger
      BEFORE UPDATE OF status ON bot_pending_actions
      FOR EACH ROW EXECUTE FUNCTION cb03_g4b_pause_before_commit()
    """))

proof=[]
def assert_one_audit(action_id, expected):
    with database.SessionLocal() as s:
        return s.query(models.AuditLog).filter_by(
            action="CB03_ACTION_CONFIRMED",resource_id=action_id).count() == expected

def wait_port(proc, timeout=25):
    limit=time.monotonic()+timeout
    while time.monotonic()<limit:
        if proc.poll() is not None:
            raise AssertionError(f"Backend died prematurely (exit {proc.returncode})")
        try:
            with socket.create_connection(("127.0.0.1",8899),timeout=.6):
                return
        except OSError:
            time.sleep(.2)
    raise AssertionError("Real FastAPI TCP port was not available")

def start_backend(*, withhold_ack=False, marker=None):
    env=os.environ.copy()
    env.update({
        "CB03_G4B_SERVER":"1",
        "CB03_G4B_WITHHOLD_ACK":"1" if withhold_ack else "0",
        "CB03_G4B_ACK_MARKER":str(marker or ""),
        # Explicit opt-in only in this ephemeral backend subprocess.
        "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED":"true",
        "CROWN_BOT_GUIDED_NLU_ENABLED":"true",
        "CROWN_BOT_CB03_PREPARATION_ENABLED":"true",
        "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED":"true",
        "CROWN_BOT_CB03_CONFIRMATION_ENABLED":"true",
        "TELEMETRY_ENABLED":"false","CLOUD_AI_ENABLED":"false",
        "ALLOWED_ORIGINS":"http://127.0.0.1:5173",
    })
    proc=subprocess.Popen([
        sys.executable,"-m","uvicorn","scripts.ci.cb03_g4b_server:app",
        "--host","127.0.0.1","--port","8899","--lifespan","off",
        "--log-level","warning",
    ],cwd=repo,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    wait_port(proc)
    return proc

def kill_server(proc):
    if proc.poll() is None:
        os.kill(proc.pid,signal.SIGKILL)
    proc.wait(timeout=10)
    assert proc.returncode == -signal.SIGKILL, (
        "REFUSED: not a real OS SIGKILL",proc.returncode)

def stop_server(proc):
    if proc and proc.poll() is None:
        proc.terminate()
        try: proc.wait(timeout=8)
        except subprocess.TimeoutExpired: kill_server(proc)

def login():
    r=requests.post(base+"/api/auth/login",
        data={"username":email,"password":password},timeout=20)
    assert r.status_code==200, f"REAL_HTTP_LOGIN_{r.status_code}"
    assert r.json().get("access_token")
    return r.json()["access_token"]

def api_post(token,endpoint,payload,timeout=40):
    return requests.post(base+endpoint,json=payload,
        headers={"Authorization":"Bearer "+token},timeout=timeout)

def api_get(token,endpoint,timeout=25):
    return requests.get(base+endpoint,
        headers={"Authorization":"Bearer "+token},timeout=timeout)

def wait_for(check, timeout, label):
    limit=time.monotonic()+timeout
    while time.monotonic()<limit:
        if check(): return
        time.sleep(.15)
    raise AssertionError("TIMEOUT: "+label)

backend=None
vite=None
try:
    # ---- Case A: actual OS kill while transaction is open before commit ----
    backend=start_backend()
    token=login()
    prepared=api_post(token,"/api/bot/guided/prepare-status",{
        "selected_appointment_id":old_appt_id,
        "utterance":"Prépare le statut du RDV en salle d'attente",
    })
    assert prepared.status_code==200, f"STATUS_PREPARE_{prepared.status_code}_{prepared.text[:450]}"
    action_id=prepared.json()["preparation_id"]
    with database.SessionLocal() as s:
        start_rev=int(s.get(models.Appointment,old_appt_id).clinical_revision)
    with database.engine.begin() as conn:
        conn.execute(text("INSERT INTO cb03_g4b_pause_action(id) VALUES (:id)"),{"id":action_id})

    def post_to_killed_server():
        try:
            response=api_post(token,"/api/bot/guided/confirm",{
                "preparation_id":action_id,"confirm":True},timeout=45)
            return {"received":response.status_code}
        except requests.RequestException:
            return {"received":None,"transportFailed":True}

    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(post_to_killed_server)
        def sleeping():
            with database.engine.connect() as conn:
                return bool(conn.execute(text("""
                    SELECT 1 FROM pg_stat_activity
                    WHERE datname=current_database()
                      AND wait_event='PgSleep'
                      AND query ILIKE '%bot_pending_actions%'
                    LIMIT 1
                """)).scalar())
        wait_for(sleeping,25,"before-COMMIT pg_sleep reached")
        kill_server(backend);backend=None
        lost=future.result(timeout=12)
    assert lost.get("transportFailed") is True, f"Expected physical TCP loss: {lost}"
    # PG will rollback the open transaction as the OS kills its backend client.
    def recovered_prepared():
        with database.SessionLocal() as s:
            return s.get(models.BotPendingAction,action_id).status=="prepared"
    wait_for(recovered_prepared,12,"postgres rollback after OS kill")
    with database.SessionLocal() as s:
        a=s.get(models.Appointment,old_appt_id)
        assert a.status==models.AppointmentStatus.PREVU
        assert int(a.clinical_revision)==start_rev
        assert s.get(models.BotPendingAction,action_id).status=="prepared"
    assert assert_one_audit(action_id,0)
    proof.append({"scenario":"OS_SIGKILL_OPEN_G2_TRANSACTION",
        "actualSigkill":True,"sawPostgresPgSleep":True,
        "networkConnectionCut":True,"action":"prepared",
        "clinicalRevisionDelta":0,"confirmedAudit":0,
        "noAutomaticReplay":True})
    print("CB03_G4B_REAL_PRECOMMIT_SIGKILL_PASS",json.dumps(proof[-1]))

    # Remove fault trigger before the browser case; only lab synthetic DDL.
    with database.engine.begin() as conn:
        conn.execute(text("DROP TRIGGER cb03_g4b_pause_action_trigger ON bot_pending_actions"))
        conn.execute(text("DROP FUNCTION cb03_g4b_pause_before_commit()"))
        conn.execute(text("DROP TABLE cb03_g4b_pause_action"))

    # ---- Case B: real browser → real HTTP → canonical G1/G2 → real PG ----
    with tempfile.TemporaryDirectory(prefix="cb03-g4b-ci-rehearsal-") as tmp:
        artifact=Path("artifacts/cb03-g4b");artifact.mkdir(parents=True,exist_ok=True)
        marker=Path(tmp)/"committed-ack-withheld.marker"
        backend=start_backend(withhold_ack=True,marker=marker)
        token=login()
        # Vite frontend only on CI loopback; no production/service-worker use.
        env=os.environ.copy()
        env.update({
            "VITE_CB03_G4B_LIVE_PG_LAB":"true",
            "VITE_CB03_G5_CHAT_LAB":"true" if G5_CHAT else "false",
            "VITE_CB03_G5_LAB_PRACTITIONER_ID":str(owner_id),
            "VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED":"true" if G5_CHAT else "false",
            "VITE_CROWN_BOT_GUIDED_NLU_ENABLED":"true" if G5_CHAT else "false",
            "VITE_CROWN_BOT_CB03_CHAT_ENABLED":"true" if G5_CHAT else "false",
            "VITE_CROWN_BOT_CB03_G3_ENABLED":"true",
            "VITE_CB03_G4_NATIVE_A11Y_LAB":"true", # disable DEV PWA only
            "VITE_API_URL":base,
        })
        vite=subprocess.Popen([
            "node","node_modules/vite/bin/vite.js","--host","127.0.0.1",
            "--port","5173","--strictPort",
        ],cwd=repo/"frontend",env=env,
            stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        lab_path="/cb03-g5-chat-lab.html" if G5_CHAT else "/cb03-g4b-live-pg-lab.html"
        def vite_ready():
            if vite.poll() is not None:
                raise AssertionError("Vite exited before integrated browser")
            try:
                return requests.get(
                    "http://127.0.0.1:5173"+lab_path,
                    timeout=1.5).status_code == 200
            except requests.RequestException:
                return False
        wait_for(vite_ready,35,"G4B UI static server")

        today=datetime.now(ZoneInfo("Africa/Casablanca"))+timedelta(days=22)
        while today.weekday()!=0:
            today+=timedelta(days=1)
        day=today.date().isoformat()
        phrase=f"Prépare un RDV le {day} à 10h pour Mme Benali contrôle"
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            context=browser.new_context(viewport={"width":1280,"height":900},
                locale="fr-FR")
            # Cookie issued by the REAL app login endpoint. No hardcoded token
            # or bypass of get_current_user.
            context.add_cookies([{
                "name":"access_token","value":token,
                "url":base,"httpOnly":True,"secure":False,"sameSite":"Lax",
            }])
            page=context.new_page()
            posts=[]
            reads=[]
            def collect_request(request):
                if "/api/bot/guided/" not in request.url: return
                endpoint=request.url.split("/api/")[-1]
                if request.method=="POST": posts.append(endpoint)
                if request.method=="GET": reads.append(endpoint)
            page.on("request",collect_request)
            page.goto("http://127.0.0.1:5173"+lab_path,
                wait_until="domcontentloaded",timeout=45000)
            if G5_CHAT:
                page.get_by_role("button",name="Ouvrir CrownBot").click()
                panel=page.get_by_role("region",
                    name="Conversation Crown Bot — actions guidées CB-03")
                panel.wait_for(timeout=25000)
                box=page.get_by_role("textbox",name="Votre message à Crown Bot")
                box.fill(phrase)
                page.get_by_role("button",name="Envoyer").click()
            else:
                panel=page.get_by_role("region",name="CB-03 G3 — actions guidées")
                panel.wait_for(timeout=25000)
                box=page.get_by_role("textbox",name="Votre demande en français")
                box.fill(phrase)
                page.get_by_role("textbox",name="Praticien ID").fill(str(owner_id))
                page.get_by_role("button",name=re.compile("Vérifier et préparer")).click()
            page.get_by_text("SALMA BENALI · Dossier G4B-001").wait_for(timeout=30000)
            confirm=page.get_by_role("button",name="Confirmer explicitement cette action")
            assert not confirm.is_enabled(),"CONFIRM_BEFORE_CHECKBOX"
            page.screenshot(path=str(artifact/"real-pg-prepared.png"),full_page=True)
            page.get_by_role("checkbox",name=re.compile("J’ai vérifié le patient")).check()
            assert confirm.is_enabled()
            confirm.click()
            wait_for(marker.exists,25,"ack withheld only AFTER real PG commit")
            with database.SessionLocal() as s:
                executed=s.query(models.BotPendingAction).filter(
                    models.BotPendingAction.action_type=="CREATE_APPOINTMENT",
                    models.BotPendingAction.employer_id==owner_id,
                    models.BotPendingAction.status=="executed").all()
                assert len(executed)==1,f"G2_EXECUTIONS_{len(executed)}"
                browser_action_id=executed[0].id
                receipt=executed[0].params_json.get("_cb03_receipt")
                assert receipt and receipt["status"]=="CREATED"
                booked=s.get(models.Appointment,receipt["appointment_id"])
                assert booked.patient_id==patient_id and booked.employer_id==owner_id
            assert assert_one_audit(browser_action_id,1)

            # Physical network loss after commit and before response start.
            kill_server(backend);backend=None
            page.get_by_text(re.compile("Résultat à réconcilier")).wait_for(timeout=20000)
            assert posts.count("bot/guided/confirm")==1,posts
            page.screenshot(path=str(artifact/"real-pg-lost-ack-uncertain.png"),
                full_page=True)
            backend=start_backend()
            # The G3 form and genuine G5 chat have DIFFERENT accessible
            # button names. Check the actual rendered G5 button, never hide
            # a failed reconciliation by falling back to server-side GET.
            page.get_by_role("button",name=(
                "Vérifier l’état (lecture seule)" if G5_CHAT
                else re.compile("Vérifier l’état par identifiant"))).click()
            page.get_by_text(re.compile(
                "Reçu retrouvé en lecture seule" if G5_CHAT
                else "Action exécutée et vérifiée")).wait_for(timeout=25000)
            assert posts.count("bot/guided/confirm")==1,posts
            with database.SessionLocal() as s:
                assert s.query(models.BotPendingAction).filter(
                    models.BotPendingAction.id==browser_action_id,
                    models.BotPendingAction.status=="executed").count()==1
                assert s.query(models.Appointment).filter(
                    models.Appointment.id==receipt["appointment_id"]).count()==1
            assert assert_one_audit(browser_action_id,1)
            assert reads==["bot/guided/actions/"+browser_action_id],reads
            page.screenshot(path=str(artifact/"real-pg-after-readonly-get.png"),
                full_page=True)
            proof.append({
                "scenario":"CHROMIUM_FASTAPI_REAL_PG_SIGKILL_POSTCOMMIT_PRE_ACK",
                "actualSigkill":True,"realHttp":True,"realBackend":True,
                "realDatabase":"full-Alembic-ephemeral-PostgreSQL",
                "responseAckDelivered":False,
                "receiptRecoveredViaReadOnlyGET":True,
                "confirmPosts":posts.count("bot/guided/confirm"),
                "preparedPosts":posts.count("bot/guided/prepare-appointment"),
                "readOnlyGetRequests":len(reads),
                "confirmedAudit":1,"oneAppointment":True,
                "renderedFinalReceipt":True,
                "realReactCrownBotChat":G5_CHAT,
                "syntheticAccountsOnly":True})
            assert proof[-1]["preparedPosts"]==1,posts
            print("CB03_G4B_REAL_CHROMIUM_PG_LOST_ACK_PASS",json.dumps(proof[-1]))
            context.close();browser.close()
        if vite and vite.poll() is None:
            vite.terminate();vite.wait(timeout=8);vite=None
finally:
    stop_server(backend)
    if vite is not None and vite.poll() is None:
        vite.terminate()
        try:vite.wait(timeout=8)
        except subprocess.TimeoutExpired:vite.kill();vite.wait()

report={
    "schema":"CB03_G5_REAL_CHAT_FAILURE_INTEGRATED_HTTP_PG_V1" if G5_CHAT
      else "CB03_G4B_REAL_FAILURE_INTEGRATED_HTTP_PG_V1",
    "realCrownBotChat":G5_CHAT,
    "head":HEAD,"source":"exact-head-isolated-CI",
    "environment":"DOCKER_LOCALHOST_PG_ALembic_REAL_UVICORN_LINUX_CHROMIUM",
    "realOsSigkill":True,"realTcpLoss":True,"noMockedClinicalHttp":True,
    "allPatientsSynthetic":True,"productionFlagsActivated":False,
    "tests":proof,
    "limitations":[
        "Not Windows native NVDA; independent G4 Windows synthetic proof remains separate",
        "Not full SQLCipher backend; PostgreSQL disposable full-Alembic only",
        "No real cabinet workstation, data, human clinical acceptance or production",
        "Pre-commit sleep uses an ephemeral test-only PG trigger, not native DB fault injection",
        "Network loss induced by killing uvicorn process immediately before response headers",
    ],
}
out=Path("artifacts/cb03-g4b/real-failure-integrated-report.json")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print("CB03_G5_REAL_CROWNBOTCHAT_PG_SIGKILL_PASS" if G5_CHAT
      else "CB03_G4B_REAL_FAILURE_AND_INTEGRATED_PASS",json.dumps(report))
