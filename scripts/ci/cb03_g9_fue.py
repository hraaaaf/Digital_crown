"""CB-03 G9 FUE: first real App login + workstation + CrownBot G2 SQLCipher.

Single new targeted CI certification. Never execute against cabinet/production
data. G7/G8 certifications must remain frozen and are not called by this file.
"""
from __future__ import annotations
import json
import os
import re
import secrets
import subprocess
import sys
import time
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from playwright.sync_api import sync_playwright
from sqlalchemy import inspect

head=os.getenv("CB03_G9_SOURCE_HEAD","")
runner=Path(os.getenv("RUNNER_TEMP","/nonexistent")).resolve()
dbfile=runner/"cb03-g9-fue-synthetic.db"
media=runner/"cb03-g9-fue-rehearsal-media"
url="sqlite:///"+str(dbfile)
assert (os.getenv("GITHUB_ACTIONS")=="true"
    and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME")=="1"
    and os.getenv("CB03_G9_FUE")=="1"
    and os.getenv("ENVIRONMENT")=="rehearsal"
    and os.getenv("DATABASE_URL")==url
    and len(bytes.fromhex(os.getenv("SQLCIPHER_KEY_HEX","")))==32
    and len(head)==40
    and subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()==head
    and dbfile.parent==runner and not dbfile.exists()
    and media.parent==runner and not media.exists()),"REFUSED: non-virgin G9 CI environment"
media.mkdir(mode=0o700)
from backend.core.runtime_safety import database_target_fingerprint
os.environ["DIGITALCROWN_ISOLATION_DB_FINGERPRINT"]=database_target_fingerprint(url)
os.environ["MEDIA_ROOT"]=str(media)
from backend import database,models
from backend.security import get_password_hash
from backend.models_document_provenance_p3 import install_document_provenance_p3
from backend.core.appointment_revision_ddl import install_appointment_revision_guard,install_appointment_overlap_index

assert database.engine.dialect.name=="sqlite"
assert "pysqlcipher" in database.engine.url.drivername
assert not inspect(database.engine).get_table_names(),"REFUSED: existing clinical schema"
install_document_provenance_p3()
models.Base.metadata.create_all(bind=database.engine)
with database.engine.begin() as c:
    install_appointment_revision_guard(c)
    install_appointment_overlap_index(c)

password=secrets.token_urlsafe(28)
email="g9-fue-owner@synthetic.invalid"
with database.SessionLocal() as s:
    dentist=models.User(email=email,hashed_password=get_password_hash(password),
        role=models.UserRole.DENTISTE,nom_complet="G9 Synthetic Dentist",
        is_active=True,is_licensed=True,
        approval_status=models.ApprovalStatus.APPROVED.value)
    s.add(dentist);s.flush()
    owner=dentist.id
    s.add(models.CabinetConfig(owner_id=owner,nom_cabinet="Cabinet FUE G9 - SYNTHETIC",
        nom_praticien="Dr G9 Synthetic",is_initialized=True,
        hide_header=False,hide_footer=False))
    patient=models.Patient(numero_dossier="G9-001",nom="BENALI",prenom="SALMA",
        sexe="F",date_naissance=datetime(1990,1,1),employer_id=owner)
    s.add(patient);s.commit();patient_id=patient.id

root=Path(__file__).resolve().parents[2]
base="http://127.0.0.1:8899"
site="http://127.0.0.1:5173"
out=Path("artifacts/cb03-g9")
out.mkdir(parents=True,exist_ok=True)
results=[]
backend=None
vite=None
backend_log=(out/"fastapi.log").open("w+")
vite_log=(out/"vite.log").open("w+")

def ready(addr,proc,log):
    limit=time.monotonic()+35
    while time.monotonic()<limit:
        if proc.poll() is not None:
            log.flush();log.seek(0)
            raise RuntimeError("Server stopped: "+log.read()[-6000:])
        try:
            if requests.get(addr,timeout=1).status_code in (200,404):return
        except requests.RequestException:pass
        time.sleep(.25)
    raise RuntimeError("Server readiness timeout: "+addr)

try:
    environment=os.environ.copy()
    environment.update({
        "CLOUD_AI_ENABLED":"false",
        "TELEMETRY_ENABLED":"false",
        "ALLOWED_ORIGINS":"http://127.0.0.1:5173",
        "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED":"true",
        "CROWN_BOT_GUIDED_NLU_ENABLED":"true",
        "CROWN_BOT_CB03_PREPARATION_ENABLED":"true",
        "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED":"true",
        "CROWN_BOT_CB03_CONFIRMATION_ENABLED":"true",
    })
    backend=subprocess.Popen([sys.executable,"-m","uvicorn","backend.main:app",
        "--host","127.0.0.1","--port","8899","--lifespan","off",
        "--log-level","warning"],cwd=root,env=environment,stdout=backend_log,stderr=subprocess.STDOUT)
    ready(base+"/openapi.json",backend,backend_log)

    # Real server enrollment creates an independent workstation identity.
    # The browser receives ONLY the workstation cookie and must login via UI.
    api=requests.Session()
    response=api.post(base+"/api/auth/login",
        data={"username":email,"password":password},timeout=20)
    assert response.status_code==200,("BOOTSTRAP_LOGIN",response.status_code,response.text[:280])
    enrollment=api.post(base+"/api/workstation/enroll",
        json={"accountPassword":password},
        headers={"Authorization":"Bearer "+response.json()["access_token"]},timeout=20)
    assert enrollment.status_code==200,("WORKSTATION_ENROLL",enrollment.status_code,enrollment.text[:300])
    assert enrollment.json()["enrollmentRequired"] is False
    workstation=api.cookies.get("dc_workstation")
    assert workstation,"Missing real opaque workstation cookie"
    api.close()
    print("CB03_G9_REAL_WORKSTATION_ENROLLMENT_PASS",flush=True)

    frontend_env=environment.copy()
    frontend_env.update({
        "VITE_API_URL":base,
        "VITE_CB03_G4_NATIVE_A11Y_LAB":"true",
        "VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED":"true",
        "VITE_CROWN_BOT_GUIDED_NLU_ENABLED":"true",
        "VITE_CROWN_BOT_CB03_CHAT_ENABLED":"true",
        "VITE_CROWN_BOT_CB03_G3_ENABLED":"true",
    })
    vite=subprocess.Popen(["node","node_modules/vite/bin/vite.js","--host","127.0.0.1",
        "--port","5173","--strictPort"],cwd=root/"frontend",env=frontend_env,
        stdout=vite_log,stderr=subprocess.STDOUT)
    ready(site+"/",vite,vite_log)

    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        for n,(label,width,height) in enumerate([
            ("desktop-1280",1280,900),("mobile-390",390,844)
        ]):
            case={"viewport":label,"checks":[],"status":"FAIL"}
            context=browser.new_context(viewport={"width":width,"height":height},
                locale="fr-FR",reduced_motion="reduce")
            context.add_cookies([{"name":"dc_workstation","value":workstation,
                "url":base,"httpOnly":True,"secure":False,"sameSite":"Strict"}])
            page=context.new_page()
            posts=[];reads=[]
            page.on("request",lambda request:(
                posts.append(request.url) if request.method=="POST"
                else reads.append(request.url)
            ) if "/api/bot/guided/" in request.url else None)
            def snap(name):
                path=out/(label+"-"+name+".png")
                page.screenshot(path=str(path),full_page=True,animations="disabled")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 3"),("HORIZONTAL_OVERFLOW",label,name)
            try:
                # Real App/ProtectedRoute must reject anonymous /dashboard.
                page.goto(site+"/dashboard",wait_until="domcontentloaded")
                page.wait_for_url("**/login",timeout=35000)
                case["checks"].append("Anonymous ProtectedRoute redirects to LoginPage")
                snap("01-login")
                page.locator("input[type=email]").fill(email)
                page.locator("input[type=password]").fill(password)
                page.get_by_role("button",name="Se connecter").click()
                page.wait_for_url("**/dashboard",timeout=40000)
                page.locator("[data-cb01-workspace-shell]").wait_for(timeout=35000)
                assert page.locator("[data-cb03-g8-workspace]").count()==0
                assert page.evaluate("Boolean(localStorage.getItem('token'))")
                case["checks"].append("Real LoginPage, workstation gate and App Dashboard")
                snap("02-real-dashboard")

                page.get_by_role("button",name="Ouvrir CrownBot").click()
                page.get_by_role("region",name="Conversation Crown Bot — actions guidées CB-03").wait_for(timeout=25000)
                future=datetime.now(ZoneInfo("Africa/Casablanca"))+timedelta(days=22+7*n)
                while future.weekday()!=0:future+=timedelta(days=1)
                phrase=f"Prépare un RDV le {future.date().isoformat()} à 10h pour Mme Benali contrôle"
                page.get_by_role("textbox",name="Votre message à Crown Bot").fill(phrase)
                page.get_by_role("button",name="Envoyer").click()
                page.get_by_text("SALMA BENALI · Dossier G9-001").wait_for(timeout=30000)
                confirm=page.get_by_role("button",name="Confirmer explicitement cette action")
                assert not confirm.is_enabled(),"Early clinical confirmation enabled"
                page.get_by_role("checkbox",name=re.compile("J’ai vérifié le patient")).check()
                assert confirm.is_enabled()
                snap("03-prepared")
                confirm.click()
                page.get_by_text(re.compile("Action exécutée et vérifiée")).wait_for(timeout=30000)
                case["checks"].append("Real CrownBotChat G1/G2 SQLCipher explicit confirmation")
                assert sum("/prepare-appointment" in u for u in posts)==1
                assert sum("/confirm" in u for u in posts)==1
                with database.SessionLocal() as s:
                    actions=s.query(models.BotPendingAction).filter_by(
                        employer_id=owner,action_type="CREATE_APPOINTMENT",status="executed").all()
                    assert len(actions)==n+1
                    for action in actions:
                        receipt=action.params_json.get("_cb03_receipt")
                        assert receipt and receipt["status"]=="CREATED"
                        assert s.get(models.Appointment,receipt["appointment_id"]).patient_id==patient_id
                        assert s.query(models.AuditLog).filter_by(
                            action="CB03_ACTION_CONFIRMED",resource_id=action.id).count()==1
                case["checks"].append("Exactly one new durable appointment and audit")
                snap("04-confirmed")
                page.reload(wait_until="domcontentloaded")
                page.locator("[data-cb01-workspace-shell]").wait_for(timeout=35000)
                assert page.url.endswith("/dashboard"),page.url
                case["checks"].append("Real App protected Dashboard survives refresh")
                snap("05-refresh")
                case["status"]="PASS"
                print("CB03_G9_FUE_REAL_APP_SQLCIPHER_PASS",label,flush=True)
            except Exception as exc:
                case["error"]=str(exc)[:900]
                try: page.screenshot(path=str(out/(label+"-failure.png")),full_page=True)
                except Exception:pass
                raise
            finally:
                results.append(case)
                context.close()
        browser.close()
    summary={"head":head,"scope":"full real App/ProtectedRoute + LoginPage + workstation gate + MainLayout + CrownBotChat + actual FastAPI + disposable SQLCipher; Linux browser NOT installed Windows","status":"PASS","cases":results}
    (out/"report.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("CB03_G9_TARGETED_FIRST_USER_EXPERIENCE_PASS",flush=True)
finally:
    (out/"report.json").write_text(json.dumps({"head":head,"status":"PASS" if len(results)==2 and all(x["status"]=="PASS" for x in results) else "FAIL","cases":results},indent=2)+"\n")
    for proc in (vite,backend):
        if proc and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait(timeout=8)
    vite_log.close();backend_log.close()
