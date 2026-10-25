"""CB2 G7: real CrownBotChat -> real FastAPI -> full-schema SQLCipher.
Isolated GitHub Actions validation ONLY, synthetic users and encrypted tempfile.
This cannot certify a Windows installer, physical cabinet, or human visual review.
"""
from __future__ import annotations
import json
import os
import re
import secrets
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "f56d8fd55092bbc958d12254d7f484bda7625994"
url = os.environ.get("DATABASE_URL", "")
assert os.environ.get("GITHUB_ACTIONS") == "true"
assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
assert os.environ.get("ENVIRONMENT") == "rehearsal"
assert os.environ.get("CLOUD_AI_ENABLED") == "false"
assert os.environ.get("TELEMETRY_ENABLED") == "false"
assert os.environ.get("CROWN_BOT_CB03_CONFIRMATION_ENABLED") == "false"
assert url.startswith("sqlite:////") and "?" not in url and "#" not in url
dbfile = Path(url[len("sqlite:///"):]).resolve()
assert dbfile.is_relative_to(Path(os.environ["RUNNER_TEMP"]).resolve())
assert dbfile.name == "cb2-g7-synthetic.db"
assert dbfile.is_file()
assert subprocess.run(["git", "merge-base", "--is-ancestor", BASE_SHA, "HEAD"], cwd=REPO).returncode == 0
assert len(bytes.fromhex(os.environ["SQLCIPHER_KEY_HEX"])) == 32
assert os.environ["SQLCIPHER_KEY_HEX"] != os.environ["SECRET_KEY"]

from backend import database, models
from backend.security import get_password_hash
from backend.core.schema_runtime import assert_database_at_current_head
assert database.engine.dialect.name == "sqlite"
assert_database_at_current_head(database.engine)
assert Path(database.engine.url.database).resolve() == dbfile

with database.SessionLocal() as s:
    assert s.query(models.User).count() == 0, "non-empty user set"
    assert s.query(models.Patient).count() == 0, "non-empty patient set"
    assert s.query(models.BotPendingAction).count() == 0, "non-empty bot action set"

# Verify the exact full application database is encrypted, not just a minimal fixture.
assert dbfile.read_bytes()[:16] != b"SQLite format 3\x00"
try:
    with sqlite3.connect(str(dbfile)) as plain:
        plain.execute("SELECT name FROM sqlite_master").fetchall()
except sqlite3.DatabaseError:
    pass
else:
    raise AssertionError("SQLCipher database readable by plaintext SQLite")
from sqlcipher3 import dbapi2 as cipher
with cipher.connect(str(dbfile)) as wrong:
    wrong.execute("PRAGMA key = 'incorrect-test-key'")
    try:
        wrong.execute("SELECT COUNT(*) FROM users").fetchone()
    except cipher.DatabaseError:
        pass
    else:
        raise AssertionError("SQLCipher wrong key did not fail")

password = secrets.token_urlsafe(26)
with database.SessionLocal() as s:
    owner = models.User(email="cb2-g7-owner@synthetic.invalid",
        hashed_password=get_password_hash(password),
        role=models.UserRole.DENTISTE, nom_complet="G7 Synthetic Dentist",
        is_active=True, is_licensed=True,
        approval_status=models.ApprovalStatus.APPROVED.value)
    foreign = models.User(email="cb2-g7-foreign@synthetic.invalid",
        hashed_password=get_password_hash(password),
        role=models.UserRole.DENTISTE, nom_complet="G7 Foreign Synthetic",
        is_active=True, is_licensed=True,
        approval_status=models.ApprovalStatus.APPROVED.value)
    s.add_all([owner, foreign]); s.flush()
    patient = models.Patient(numero_dossier="G4B-001", nom="BENALI",
        prenom="SALMA", sexe="F", date_naissance=datetime(1990,1,1),
        employer_id=owner.id)
    s.add(patient); s.flush()
    old_appt = models.Appointment(employer_id=owner.id, patient_id=patient.id,
        praticien_id=owner.id, datetime_start=datetime.now()+timedelta(days=32),
        duration_minutes=30, motif="G7 synthetic crash rollback",
        status=models.AppointmentStatus.PREVU)
    s.add(old_appt); s.commit()
    owner_id, foreign_id, patient_id, old_id = owner.id, foreign.id, patient.id, old_appt.id

# Actual OS-killed separate SQLCipher connection with a transaction not committed.
# This checks durability in the full app schema; it is NOT an interrupted G2 HTTP transaction.
with tempfile.TemporaryDirectory(prefix="cb2-g7-proc-", dir=os.environ["RUNNER_TEMP"]) as tmpdir:
    marker = Path(tmpdir) / "uncommitted.marker"
    code = """
import os, time
from pathlib import Path
from sqlcipher3 import dbapi2 as cipher
c=cipher.connect(os.environ['CB2_DB_FILE'], timeout=10)
c.execute("PRAGMA key = '" + os.environ['SQLCIPHER_KEY_HEX'] + "'")
c.execute('BEGIN IMMEDIATE')
c.execute('UPDATE appointments SET status=? WHERE id=?',
    ('EN_SALLE_ATTENTE', int(os.environ['CB2_OLD_ID'])))
Path(os.environ['CB2_CRASH_MARKER']).write_text('TRANSACTION_OPEN')
time.sleep(60)
"""
    env = os.environ.copy()
    env.update(CB2_DB_FILE=str(dbfile), CB2_OLD_ID=str(old_id),
               CB2_CRASH_MARKER=str(marker))
    worker = subprocess.Popen([sys.executable, "-c", code], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic()+20
    while not marker.exists() and time.monotonic()<deadline:
        assert worker.poll() is None, "precommit worker exited"
        time.sleep(.1)
    assert marker.exists(), "precommit worker never opened transaction"
    os.kill(worker.pid, signal.SIGKILL)
    worker.wait(timeout=10)
    assert worker.returncode == -signal.SIGKILL
    database.engine.dispose()
    with database.SessionLocal() as s:
        old = s.get(models.Appointment, old_id)
        assert old.status == models.AppointmentStatus.PREVU
        assert old.clinical_revision == 0

base = "http://127.0.0.1:8899"
server = None
vite = None
artifact = REPO / "artifacts/cb2-g7-sqlcipher"
artifact.mkdir(parents=True, exist_ok=True)

def wait_for(check, seconds, label):
    limit = time.monotonic()+seconds
    while time.monotonic()<limit:
        if check(): return
        time.sleep(.2)
    raise AssertionError("TIMEOUT " + label)

def start_server(server_module, *, withhold=False):
    env = os.environ.copy()
    env.update({
        "CB2_G7_WITHHOLD_ACK": "1" if withhold else "0",
        "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED": "true",
        "CROWN_BOT_GUIDED_NLU_ENABLED": "true",
        "CROWN_BOT_CB03_PREPARATION_ENABLED": "true",
        "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED": "true",
        "CROWN_BOT_CB03_CONFIRMATION_ENABLED": "true",
        "CLOUD_AI_ENABLED": "false", "TELEMETRY_ENABLED": "false",
        "ALLOWED_ORIGINS": "http://127.0.0.1:5173",
        "PYTHONPATH": str(server_module.parent) + os.pathsep + str(REPO),
    })
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn",
        server_module.stem + ":app", "--host", "127.0.0.1", "--port", "8899",
        "--lifespan", "off", "--log-level", "warning"], cwd=REPO, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    def ready():
        assert proc.poll() is None, f"FastAPI process exited early: {proc.returncode}"
        try:
            with socket.create_connection(("127.0.0.1",8899), timeout=.5): return True
        except OSError: return False
    wait_for(ready, 35, "FastAPI start")
    return proc

def kill_server(proc):
    assert proc and proc.poll() is None, "server not running"
    os.kill(proc.pid,signal.SIGKILL)
    proc.wait(timeout=10)
    assert proc.returncode == -signal.SIGKILL

def login(email):
    res=requests.post(base+"/api/auth/login",
        data={"username":email, "password":password}, timeout=20)
    assert res.status_code == 200, f"auth failed {res.status_code}"
    return res.json()["access_token"]

try:
    with tempfile.TemporaryDirectory(prefix="cb2-g7-asgi-", dir=os.environ["RUNNER_TEMP"]) as t:
        shim = Path(t)/"cb2_g7_real_server.py"
        shim.write_text('''
import asyncio, os
from pathlib import Path
from backend.main import app as actual_app
class AfterCommitWithhold:
    def __init__(self, app): self.app=app
    async def __call__(self, scope, receive, send):
        if (scope["type"]=="http" and scope.get("method")=="POST"
            and scope.get("path")=="/api/bot/guided/confirm"
            and os.environ.get("CB2_G7_WITHHOLD_ACK")=="1"):
            async def intercept(message):
                if message["type"]=="http.response.start" and message["status"]==200:
                    Path(os.environ["CB2_G7_ACK_MARKER"]).write_text("COMMITTED")
                    await asyncio.Event().wait()
                await send(message)
            return await self.app(scope,receive,intercept)
        return await self.app(scope,receive,send)
app=AfterCommitWithhold(actual_app)
''', encoding="utf-8")
        ack = Path(t)/"committed.marker"
        os.environ["CB2_G7_ACK_MARKER"] = str(ack)
        server=start_server(shim,withhold=True)
        token = login("cb2-g7-owner@synthetic.invalid")
        foreign_token = login("cb2-g7-foreign@synthetic.invalid")
        vite_env=os.environ.copy()
        vite_env.update({
            "VITE_CB03_G5_CHAT_LAB": "true",
            "VITE_CB03_G5_REAL_CHAT_PG": "true",
            "VITE_CB03_G5_LAB_PRACTITIONER_ID": str(owner_id),
            "VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED": "true",
            "VITE_CROWN_BOT_GUIDED_NLU_ENABLED": "true",
            "VITE_CROWN_BOT_CB03_CHAT_ENABLED": "true",
            "VITE_CROWN_BOT_CB03_G3_ENABLED": "true",
            "VITE_CB03_G4_NATIVE_A11Y_LAB": "true",
            "VITE_API_URL": base,
        })
        vite=subprocess.Popen(["node","node_modules/vite/bin/vite.js",
            "--host","127.0.0.1","--port","5173","--strictPort"],
            cwd=REPO/"frontend", env=vite_env,
            stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        lab_url="http://127.0.0.1:5173/cb03-g5-chat-lab.html"
        def vite_ready():
            assert vite.poll() is None, "Vite process exited"
            try: return requests.get(lab_url,timeout=1).status_code==200
            except requests.RequestException: return False
        wait_for(vite_ready,45,"G5 real chat laboratory")
        day = datetime.now(ZoneInfo("Africa/Casablanca"))+timedelta(days=22)
        while day.weekday()!=0: day+=timedelta(days=1)
        phrase=f"Prépare un RDV le {day.date().isoformat()} à 10h pour Mme Benali contrôle"
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            context=browser.new_context(viewport={"width":1280,"height":900},locale="fr-FR")
            context.add_cookies([{"name":"access_token","value":token,
                "url":base,"httpOnly":True,"secure":False,"sameSite":"Lax"}])
            page=context.new_page()
            posts=[]; gets=[]
            def record(req):
                if "/api/bot/guided/" not in req.url: return
                endpoint=req.url.split("/api/")[-1]
                if req.method=="POST": posts.append(endpoint)
                if req.method=="GET": gets.append(endpoint)
            page.on("request",record)
            page.goto(lab_url,wait_until="domcontentloaded",timeout=45000)
            page.get_by_role("button",name="Ouvrir CrownBot").click()
            page.get_by_role("region",name="Conversation Crown Bot — actions guidées CB-03").wait_for()
            box=page.get_by_role("textbox",name="Votre message à Crown Bot")
            box.fill(phrase)
            page.get_by_role("button",name="Envoyer").click()
            page.get_by_text("SALMA BENALI · Dossier G4B-001").wait_for(timeout=30000)
            confirm=page.get_by_role("button",name="Confirmer explicitement cette action")
            assert not confirm.is_enabled(), "confirmation active without explicit check"
            page.screenshot(path=str(artifact/"before-confirm.png"),full_page=True)
            page.get_by_role("checkbox",name=re.compile("J’ai vérifié le patient")).check()
            assert confirm.is_enabled()
            confirm.click()
            wait_for(ack.exists,30,"durable COMMIT before withheld HTTP ACK")
            with database.SessionLocal() as s:
                executed=s.query(models.BotPendingAction).filter(
                    models.BotPendingAction.action_type=="CREATE_APPOINTMENT",
                    models.BotPendingAction.employer_id==owner_id,
                    models.BotPendingAction.status=="executed").all()
                assert len(executed)==1, f"action count {len(executed)}"
                action_id=executed[0].id
                receipt=executed[0].params_json["_cb03_receipt"]
                assert receipt["status"]=="CREATED"
                created_id=receipt["appointment_id"]
                appt=s.get(models.Appointment,created_id)
                assert appt and appt.patient_id==patient_id and appt.employer_id==owner_id
                assert s.query(models.AuditLog).filter_by(
                    action="CB03_ACTION_CONFIRMED",resource_id=action_id).count()==1
            deny=requests.get(base+"/api/bot/guided/actions/"+action_id,
                headers={"Authorization":"Bearer "+foreign_token},timeout=15)
            assert deny.status_code==404, f"cross-tenant read {deny.status_code}"
            kill_server(server);server=None
            page.get_by_text(re.compile("Résultat à réconcilier")).wait_for(timeout=20000)
            assert posts.count("bot/guided/confirm")==1, posts
            page.screenshot(path=str(artifact/"ack-lost.png"),full_page=True)
            server=start_server(shim)
            page.get_by_role("button",name="Vérifier l’état (lecture seule)").click()
            page.get_by_text(re.compile("Reçu retrouvé en lecture seule")).wait_for(timeout=25000)
            assert posts.count("bot/guided/confirm")==1, posts
            assert gets==["bot/guided/actions/"+action_id], gets
            with database.SessionLocal() as s:
                assert s.query(models.Appointment).filter_by(id=created_id).count()==1
                assert s.query(models.AuditLog).filter_by(
                    action="CB03_ACTION_CONFIRMED",resource_id=action_id).count()==1
            page.screenshot(path=str(artifact/"receipt-recovered.png"),full_page=True)
            browser.close()
        evidence={
            "schema":"CB2_G7_REAL_SQLCIPHER_FULL_APP_E2E_V1",
            "sourceSha":BASE_SHA,
            "fullAppSchema":True,"database":"ephemeral-encrypted-SQLCipher",
            "realCrownBotChat":True,"realFastApi":True,
            "realChromium":True,"actualOsSigkillPrecommitConnection":True,
            "precommitScope":"direct full-schema SQLCipher transaction, not FastAPI G2",
            "actualOsSigkillAfterCommitBeforeHttpAck":True,
            "confirmPosts":posts.count("bot/guided/confirm"),
            "readOnlyRecoveryGets":len(gets),
            "crossTenantReadDenied":True,
            "singleAppointmentAndAudit":True,
            "plainAndWrongKeyRejected":True,
            "limitations":["Isolated CI browser shell, not full MainLayout",
                "Not native Windows / no human visual approval",
                "No real patient or cabinet workstation",
                "Not G2 HTTP precommit kill; separate direct SQLCipher rollback only"]
        }
        (artifact/"evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
        print("CB2_G7_REAL_SQLCIPHER_E2E_PASS",json.dumps(evidence))
finally:
    if server and server.poll() is None:
        server.terminate()
        try: server.wait(timeout=8)
        except subprocess.TimeoutExpired: kill_server(server)
    if vite and vite.poll() is None:
        vite.terminate()
        try: vite.wait(timeout=8)
        except subprocess.TimeoutExpired: vite.kill();vite.wait(timeout=8)
