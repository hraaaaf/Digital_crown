"""DEC-R2-01: real HTTP negative/positive tests; only synthetic rows/files."""
from datetime import datetime
from hashlib import sha256

from backend import models
from backend.routers import documents
from backend.security import get_password_hash


def _user(db, role, owner_id, label, grant=False):
    actor = models.User(
        email=f"r2-bilan-{label}@example.test",
        hashed_password=get_password_hash("SyntheticBilan2026!"),
        role=role,
        nom_complet="Synthetic BILAN access actor",
        is_active=True, is_licensed=True,
        employer_id=owner_id,
        permissions={"patients": True, "bilan_read": grant},
    )
    db.add(actor)
    db.commit()
    db.refresh(actor)
    return actor


def _patient(db, owner, label):
    row = models.Patient(
        numero_dossier=f"R2-BILAN-{label}", nom="Synthetic",
        prenom="BILAN", sexe="M", date_naissance=datetime(2000, 1, 1),
        employer_id=owner,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _doc(db, patient, typ=models.DocumentType.BILAN, path="static/archives/synthetic/bilan.pdf"):
    content = b"%PDF-1.4\nsynthetic-bilan-test-only\n%%EOF"
    row = models.DocumentArchive(
        patient_id=patient.id, document_type=typ,
        filename="bilan.pdf", original_filename="bilan.pdf",
        document_group_id=f"bilan-{patient.id}-{typ.value.lower()}",
        file_path=path,
        file_hash=sha256(content).hexdigest(), file_size=len(content),
        title="Synthetic historical BILAN", status=models.DocumentStatus.ACTIF,
        is_latest_version=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _token(client, actor, password="SyntheticBilan2026!"):
    response = client.post("/api/auth/login", data={
        "username": actor.email, "password": password,
    })
    assert response.status_code == 200, response.text
    jwt = response.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    return {"Authorization": f"Bearer {jwt}"}


def _pdf(monkeypatch, tmp_path):
    monkeypatch.setattr(documents, "MEDIA_DIR", tmp_path)
    root = tmp_path / "archives" / "synthetic"
    root.mkdir(parents=True)
    data = b"%PDF-1.4\nsynthetic-bilan-test-only\n%%EOF"
    (root / "bilan.pdf").write_bytes(data)
    return data


def test_dec01_owner_can_read_bilan_without_legacy_static_url(client, db, dentiste, monkeypatch, tmp_path):
    data = _pdf(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "OWNER")
    doc = _doc(db, patient)
    headers = _token(client, dentiste, password="TestPass123!")
    result = client.get(f"/api/documents/bilan/{doc.id}/view", headers=headers)
    assert result.status_code == 200, result.text
    assert result.content == data
    assert result.headers["content-disposition"] == "inline"
    assert result.headers["cache-control"] == "no-store"
    listing = client.get(f"/api/patients/{patient.id}/documents", headers=headers)
    assert listing.status_code == 200, listing.text
    shown = next(item for item in listing.json() if item["id"] == str(doc.id))
    assert shown["type"] == "BILAN"
    assert shown["url"] == f"/api/documents/bilan/{doc.id}/view"
    assert "static/archives" not in shown["url"]


def test_dec01_explicit_admin_same_cabinet_and_revoke_same_jwt(client, db, dentiste, monkeypatch, tmp_path):
    _pdf(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "ADMIN")
    doc = _doc(db, patient)
    admin = _user(db, "ADMIN", dentiste.id, "admin-approved", grant=True)
    headers = _token(client, admin)
    assert client.get(f"/api/documents/bilan/{doc.id}/view", headers=headers).status_code == 200
    assert any(d["id"] == str(doc.id) for d in client.get(
        f"/api/patients/{patient.id}/documents", headers=headers).json())
    admin.permissions = {"patients": True, "bilan_read": False}
    db.commit()
    db.expire_all()
    assert client.get(f"/api/documents/bilan/{doc.id}/view", headers=headers).status_code == 403
    listing = client.get(f"/api/patients/{patient.id}/documents", headers=headers)
    assert listing.status_code == 200
    assert all(d["id"] != str(doc.id) for d in listing.json())


def test_dec01_staff_other_cabinet_and_implicit_admin_denied(client, db, dentiste, monkeypatch, tmp_path):
    _pdf(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "DENIED")
    doc = _doc(db, patient)
    other_owner = _user(db, "DENTISTE", None, "other-owner")
    actors = [
        _user(db, "SECRETAIRE", dentiste.id, "secretary", grant=True),
        _user(db, "DENTISTE", dentiste.id, "employed-dentist", grant=True),
        _user(db, "ADMIN", dentiste.id, "admin-no-explicit", grant=False),
        _user(db, "ADMIN", other_owner.id, "foreign-admin", grant=True),
        other_owner,
    ]
    for actor in actors:
        headers = _token(client, actor)
        assert client.get(f"/api/documents/bilan/{doc.id}/view", headers=headers).status_code in (403, 404)
        listed = client.get(f"/api/patients/{patient.id}/documents", headers=headers)
        if listed.status_code == 200:
            assert all(d["id"] != str(doc.id) for d in listed.json())


def test_dec01_reader_cannot_download_sign_trash_restore_or_delete_bilan(client, db, dentiste, monkeypatch, tmp_path):
    _pdf(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "READ-NOT-WRITE")
    doc = _doc(db, patient)
    admin = _user(db, "ADMIN", dentiste.id, "admin-no-writes", grant=True)
    for actor, password in [(dentiste, "TestPass123!"), (admin, "SyntheticBilan2026!")]:
        headers = _token(client, actor, password=password)
        attempted = [
            client.get(f"/api/documents/{doc.id}/download", headers=headers),
            client.post(f"/api/documents/{doc.id}/sign", headers=headers),
            client.post(f"/api/documents/{doc.id}/trash", headers=headers),
            client.post(f"/api/documents/{doc.id}/restore", headers=headers),
            client.delete(f"/api/documents/{doc.id}", params={"confirm": "true"}, headers=headers),
        ]
        assert [r.status_code for r in attempted] == [403] * 5
    db.refresh(doc)
    assert doc.status == models.DocumentStatus.ACTIF
    assert db.query(models.DocumentArchive).count() == 1


def test_dec01_typed_bilan_static_bypass_and_unclassified_paths_denied(client, db, dentiste, monkeypatch, tmp_path):
    _pdf(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "STATIC")
    doc = _doc(db, patient, path="static/documents/private-bilan.pdf")
    headers = _token(client, dentiste, password="TestPass123!")
    assert client.get("/api/static/documents/private-bilan.pdf", headers=headers).status_code == 403
    assert client.get(f"/api/documents/bilan/{doc.id}/view", headers=headers).status_code == 404
    unclassified = _doc(db, patient, typ=models.DocumentType.AUTRE,
                        path="static/archives/synthetic/unknown.pdf")
    assert client.get(f"/api/documents/bilan/{unclassified.id}/view", headers=headers).status_code == 404
    doc.status = models.DocumentStatus.SUPPRIME
    db.commit()
    assert client.get(f"/api/documents/bilan/{doc.id}/view", headers=headers).status_code == 404
