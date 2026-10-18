"""Real two-connection HTTP race on a disposable T2 backend, no patient data.

Concurrency requires two independent HTTP clients and DB sessions, never a
single shared TestClient transaction or an injected mocked ArchiveService.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import threading
import urllib.parse
import urllib.request
import urllib.error
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if os.getenv("ENVIRONMENT") != "test" or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1" or os.getenv("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db":
    raise SystemExit("ATOMIC_T2_REQUIRE_DISPOSABLE_RUNTIME")
password = os.environ["T2_PASSWORD"]
studies = json.loads(os.environ["P2TER_STUDIES"])
patient_id = studies["patient_id"]
study_id = studies["latest_id"]

base = "http://127.0.0.1:8005"
auth = urllib.parse.urlencode({"username":"t2-browser@cabinet.ma","password":password}).encode()
with urllib.request.urlopen(urllib.request.Request(base+"/api/auth/login",data=auth,method="POST"),timeout=15) as response:
    token = json.load(response)["access_token"]

barrier = threading.Barrier(2)
payload=json.dumps({"analysis_id":study_id,"expected_revision":2,"archive":True}).encode()
def archive_once(_):
    barrier.wait(timeout=15)
    request=urllib.request.Request(base+f"/api/patients/{patient_id}/pdf",data=payload,method="POST",
        headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(request,timeout=60) as response:
            body=response.read()
            if response.status==200 and not body.startswith(b"%PDF"):
                raise AssertionError("SUCCESS_NOT_PDF")
            if response.status==200 and (
                response.headers.get("X-Cephalo-Analysis-Id")!=str(study_id)
                or response.headers.get("X-Cephalo-Revision")!="2"
            ):
                raise AssertionError("SUCCESS_IDENTITY_WRONG")
            return response.status
    except urllib.error.HTTPError as exc:
        exc.read()
        return exc.code

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    outcomes=sorted(pool.map(archive_once,(1,2)))
assert outcomes==[200,409], f"ATOMIC_ARCHIVE_CONCURRENT_UNEXPECTED_HTTP {outcomes}"

from backend import database,models
with database.SessionLocal() as db:
    claims=db.query(models.CephaloArchiveClaim).filter_by(
        patient_id=patient_id,analysis_id=study_id,revision=2).all()
    docs=db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id==patient_id,
        models.DocumentArchive.analysis_id==study_id,
        models.DocumentArchive.document_type==models.DocumentType.RAPPORT_CEPHALO,
    ).all()
    assert len(claims)==len(docs)==1, (len(claims),len(docs))
    assert claims[0].document_archive_id==docs[0].id
    assert docs[0].clinical_data["cephalo_analysis_revision"]==2
print("P2TER_TWO_INDEPENDENT_HTTP_SESSIONS_ATOMIC_ARCHIVE_PASS",json.dumps(
    {"outcomes":outcomes,"claims":len(claims),"archives":len(docs),"study_revision":2,
     "patients_real":False,"scientific_parity_verified":False},sort_keys=True))
