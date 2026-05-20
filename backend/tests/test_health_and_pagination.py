"""
Tests: health endpoint + pagination X-Total-Count on patient list.
"""
from datetime import datetime
from backend import models
from backend.security import get_password_hash


def _make_user(db, email: str, role: str = "DENTISTE"):
    import uuid
    u = models.User(
        email=email or f"u-{uuid.uuid4().hex[:8]}@test.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role=role,
        nom_complet="Dr. Test",
        is_active=True,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


def _make_patient(db, employer_id: int, n: int = 0):
    p = models.Patient(
        nom=f"Martin{n}",
        prenom="Jean",
        date_naissance=datetime(1985, 1, 1),
        sexe="M",
        employer_id=employer_id,
        numero_dossier=f"P-{n:06d}",
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


def _login(client, email: str) -> dict:
    r = client.post("/api/auth/login", data={"username": email, "password": "TestPass123!"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# --- Health ---

def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"


# --- Pagination ---

def test_patient_list_returns_x_total_count(client, db):
    doc = _make_user(db, "pag1@test.ma")
    headers = _login(client, "pag1@test.ma")
    for i in range(3):
        _make_patient(db, employer_id=doc.id, n=i)

    resp = client.get("/api/patients/", headers=headers)
    assert resp.status_code == 200
    assert "x-total-count" in resp.headers
    assert int(resp.headers["x-total-count"]) >= 3


def test_patient_list_limit_respected(client, db):
    doc = _make_user(db, "pag2@test.ma")
    headers = _login(client, "pag2@test.ma")
    for i in range(5):
        _make_patient(db, employer_id=doc.id, n=100 + i)

    resp = client.get("/api/patients/?limit=2", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    assert int(resp.headers["x-total-count"]) >= 5


def test_patient_list_skip(client, db):
    doc = _make_user(db, "pag3@test.ma")
    headers = _login(client, "pag3@test.ma")
    for i in range(4):
        _make_patient(db, employer_id=doc.id, n=200 + i)

    all_ids = [p["id"] for p in client.get("/api/patients/", headers=headers).json()]
    skipped = [p["id"] for p in client.get("/api/patients/?skip=2&limit=100", headers=headers).json()]
    assert skipped == all_ids[2:]


# --- Multi-tenant isolation ---

def test_patient_list_tenant_isolation(client, db):
    doc_a = _make_user(db, "docA@test.ma")
    doc_b = _make_user(db, "docB@test.ma")
    _make_patient(db, employer_id=doc_b.id, n=999)
    _make_patient(db, employer_id=doc_a.id, n=998)

    headers = _login(client, "docA@test.ma")
    resp = client.get("/api/patients/", headers=headers)
    assert resp.status_code == 200
    for p in resp.json():
        assert p["employer_id"] == doc_a.id
