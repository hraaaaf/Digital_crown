"""LOT05.6 — real HTTP/JWT/workstation contract on a fresh Alembic PostgreSQL DB.

CI-only synthetic principal and exact official fictitious SQLite, NEVER clinic data.
Does not attest SQLCipher, real imports, cabinet deployment, or medical correctness.
"""
from __future__ import annotations

import os
from sqlalchemy import func, select, text
from fastapi import FastAPI
from fastapi.testclient import TestClient

assert os.environ.get("ENVIRONMENT") == "rehearsal", "REHEARSAL_ONLY"
assert os.environ.get("DATABASE_URL", "").startswith("postgresql://"), "POSTGRES_ONLY"

from backend import database, models
from backend.core.schema_runtime import assert_database_at_current_head, CURRENT_ALEMBIC_HEAD

# The real routers/__init__.py eagerly boots unrelated AI/vision engines.
# Create a package namespace that loads the EXACT three runtime router modules
# below; do not import or mock any auth, JWT, Workstation or migration dependency.
import sys
import types
from pathlib import Path
import backend
real_routers = types.ModuleType("backend.routers")
real_routers.__path__ = [str(Path(__file__).resolve().parents[1] / "routers")]
sys.modules["backend.routers"] = real_routers
backend.routers = real_routers
from backend.routers import auth, workstation_mode, legacy_migration_v15
from backend.security import get_password_hash

assert_database_at_current_head(database.engine)
app = FastAPI()
app.include_router(auth.router, prefix="/api/auth")
app.include_router(workstation_mode.router, prefix="/api/workstation")
app.include_router(legacy_migration_v15.router, prefix="/api/migration")

owner_email = "lot05-6-owner@example.invalid"
team_email = "lot05-6-staff@example.invalid"
passwd = "SYNTHETIC_TEST_ONLY_PASSWORD_8359"
with database.SessionLocal() as db:
    assert db.execute(select(func.count()).select_from(models.Patient)).scalar_one() == 0
    assert db.execute(select(func.count()).select_from(models.Appointment)).scalar_one() == 0
    owner = models.User(
        email=owner_email, hashed_password=get_password_hash(passwd),
        role=models.UserRole.DENTISTE, nom_complet="Synthetic Owner",
        is_active=True, is_licensed=False,
    )
    db.add(owner)
    db.flush()
    staff = models.User(
        email=team_email, hashed_password=get_password_hash(passwd),
        role=models.UserRole.DENTISTE, nom_complet="Synthetic Employee",
        is_active=True, is_licensed=False, employer_id=owner.id,
        approval_status="approved", permissions={"settings": True},
    )
    db.add(staff)
    db.commit()

with TestClient(app, raise_server_exceptions=True) as client:
    def expect(response, code, label):
        assert response.status_code == code, (label, response.status_code, response.text[:700])
        return response

    expect(client.get("/api/migration/preflight"), 401, "anonymous preflight")
    expect(client.get("/api/migration/synthetic-fixture"), 401, "anonymous fixture")
    expect(client.post("/api/migration/synthetic-file-dryrun",
                       content=b"not-sqlite",
                       headers={"Content-Type": "application/vnd.sqlite3"}),
           401, "anonymous upload")

    login=expect(client.post("/api/auth/login",
                             data={"username":owner_email,"password":passwd}),
                 200, "real owner login")
    owner_token=login.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    owner_headers={"Authorization":f"Bearer {owner_token}"}

    # A real prior-registered workstation forces valid workplace identity.
    state=expect(client.get("/api/workstation/state",headers=owner_headers),
                 200, "register actual workstation")
    assert state.json()["workstationId"] is not None

    with TestClient(app, raise_server_exceptions=True) as no_station:
        expect(no_station.get("/api/migration/preflight",headers=owner_headers),
               423,"registered cabinet workstation cookie required")
        expect(no_station.get("/api/migration/synthetic-fixture",headers=owner_headers),
               423,"fixture cannot bypass workstation")

    expect(client.get("/api/migration/preflight",
                      headers={"Authorization":"Bearer bogus.invalid.token"}),
           401,"invalid JWT")

    staff_login=expect(client.post("/api/auth/login",
                                   data={"username":team_email,"password":passwd}),
                       200,"real staff login")
    staff_token=staff_login.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    expect(client.get("/api/migration/preflight",
                      headers={"Authorization":f"Bearer {staff_token}"}),
           403, "employee settings override cannot bypass owner")
    expect(client.get("/api/migration/synthetic-fixture",
                      headers={"Authorization":f"Bearer {staff_token}"}),
           403, "employee cannot fetch fixture")

    # Workstation switched to Station must block non-exempt routes, even for owner.
    expect(client.post("/api/workstation/owner-pin",headers=owner_headers,
                       json={"accountPassword":passwd,"newPin":"2468"}),
           200, "configure owner PIN")
    changed=expect(client.post("/api/workstation/mode",headers=owner_headers,
                               json={"mode":"station","ownerPin":"2468"}),
                   200,"Station activated on synthetic CI workstation")
    assert changed.json()["stationLocked"] is True
    expect(client.get("/api/migration/preflight",headers=owner_headers),
           423,"Station refuses preflight")
    expect(client.post("/api/migration/synthetic-file-dryrun",
                       content=b"untrusted",
                       headers={**owner_headers,"Content-Type":"application/vnd.sqlite3"}),
           423,"Station refuses file POST")
    expect(client.post("/api/workstation/station/escape",headers=owner_headers,
                       json={"ownerPin":"2468"}),
           200,"owner session-bound Station escape")

    preflight=expect(client.get("/api/migration/preflight",headers=owner_headers),
                     200,"owner preflight against Alembic PG")
    assert preflight.json()["schema_revision_matches"] is True
    assert preflight.json()["physical_subset_checked"] is True, preflight.json()
    assert preflight.json()["import_permitted"] is False

    fixture=expect(client.get("/api/migration/synthetic-fixture",
                              headers=owner_headers),200,"official fixture download")
    payload=fixture.content
    assert payload.startswith(b"SQLite format 3\\x00".replace(b"\\x00", b"\x00"))
    assert len(payload) <= 512*1024
    expect(client.post("/api/migration/synthetic-file-dryrun",
                       content=payload,
                       headers={**owner_headers,"Content-Type":"text/plain"}),
           415,"reject MIME")
    altered=bytearray(payload)
    altered[-1]^=1
    expect(client.post("/api/migration/synthetic-file-dryrun",
                       content=bytes(altered),
                       headers={**owner_headers,"Content-Type":"application/vnd.sqlite3"}),
           422,"reject tampered source bytes")
    expect(client.post("/api/migration/synthetic-file-dryrun",
                       content=payload+b"x"*(512*1024),
                       headers={**owner_headers,"Content-Type":"application/vnd.sqlite3"}),
           413,"reject oversized stream")
    result=expect(client.post("/api/migration/synthetic-file-dryrun",
                              content=payload,
                              headers={**owner_headers,"Content-Type":"application/vnd.sqlite3"}),
                  200,"real HTTP official dryrun").json()
    assert (result["source_patients"], result["source_appointments"],
            result["verified_patient_links"],result["orphan_appointments"],
            result["cross_tenant_links"],result["after_rollback_patients"],
            result["after_rollback_appointments"])==(100,200,200,0,0,0,0), result
    assert all(result[x] is False for x in
               ("cabinet_rows_read","cabinet_rows_written","source_persisted","import_permitted"))

with database.SessionLocal() as db:
    assert db.execute(select(func.count()).select_from(models.Patient)).scalar_one()==0
    assert db.execute(select(func.count()).select_from(models.Appointment)).scalar_one()==0
    assert db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()==CURRENT_ALEMBIC_HEAD
print("LOT05_6_HTTP_PG_PASS alembic_head="+CURRENT_ALEMBIC_HEAD+
      " real_jwt=1 owner_only=1 workstation_cookie=1 station_lock=1 station_escape=1"+
      " synthetic_file=100x200 link_parity=200 tamper_422=1 mime_415=1 oversize_413=1"+
      " clinic_patient_rows=0 clinic_appointment_rows=0 import_permit=0")
