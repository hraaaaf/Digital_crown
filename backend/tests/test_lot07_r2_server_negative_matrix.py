"""LOT07 R2 — targeted HTTP denial matrix, disposable pytest SQLite only.

This suite certifies existing patient-media API boundaries, NOT full MultiView
W/X slot authorization or exclusive document/signature workflows.
No patient production data, uploads, browser sessions or cabinet mutation.
"""
from datetime import datetime

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.security import get_password_hash, token_blacklist


def _user(db, email, *, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("R2SyntheticPass123!"),
        role="DENTISTE",
        nom_complet="Synthetic R2",
        is_active=True,
        is_licensed=True,
        employer_id=employer_id,
        permissions=permissions if permissions is not None else {},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _patient(db, employer_id, name):
    patient = models.Patient(
        numero_dossier=f"R2-NEG-{name}",
        nom="Synthetic",
        prenom="R2",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _login(client, email, password):
    response = client.post(
        "/api/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    # Auth accepts a cookie before a Bearer header. Remove auth cookies so
    # every following assertion exercises the named JWT, not a stale cookie.
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    return token, {"Authorization": f"Bearer {token}"}


def _attempt_media_write(client, patient_id, headers):
    # Auth/RBAC/tenant decisions must precede content validation and ingestion.
    return client.post(
        f"/api/patients/{patient_id}/assets/import",
        headers=headers,
        data={"asset_type": "PHOTO"},
        files={"file": ("synthetic.txt", b"R2-invalid-image", "text/plain")},
    )


def test_r2_cross_tenant_media_read_and_direct_write_are_denied(
    client, db, dentiste
):
    alien_owner = _user(db, "r2-other-owner@example.test")
    alien_patient = _patient(db, alien_owner.id, "FOREIGN")
    _token, headers = _login(client, dentiste.email, "TestPass123!")
    before = db.query(ClinicalAsset).count()

    read = client.get(f"/api/patients/{alien_patient.id}/assets", headers=headers)
    write = _attempt_media_write(client, alien_patient.id, headers)
    assert read.status_code in (403, 404)
    assert write.status_code in (403, 404)
    assert db.query(ClinicalAsset).count() == before


def test_r2_existing_jwt_loses_media_read_and_write_after_permission_revocation(
    client, db, dentiste
):
    patient = _patient(db, dentiste.id, "REVOKED-PERMISSION")
    staff = _user(
        db,
        "r2-staff@example.test",
        employer_id=dentiste.id,
        permissions={"patients": True, "prescriptions": False, "accounting": False},
    )
    _token, headers = _login(client, staff.email, "R2SyntheticPass123!")
    url = f"/api/patients/{patient.id}/assets"
    assert client.get(url, headers=headers).status_code == 200

    # No fresh login: this MUST invalidate the effective authorization of
    # the still cryptographically valid JWT on the next API request.
    staff.permissions = {
        "patients": False,
        "prescriptions": False,
        "accounting": False,
    }
    db.commit()
    db.expire_all()
    before = db.query(ClinicalAsset).count()

    assert client.get(url, headers=headers).status_code == 403
    assert _attempt_media_write(client, patient.id, headers).status_code == 403
    assert db.query(ClinicalAsset).count() == before


def test_r2_unrelated_permission_does_not_grant_media_write(
    client, db, dentiste
):
    patient = _patient(db, dentiste.id, "WRONG-PERMISSION")
    staff = _user(
        db,
        "r2-prescriptions-only@example.test",
        employer_id=dentiste.id,
        permissions={"patients": False, "prescriptions": True},
    )
    _token, headers = _login(client, staff.email, "R2SyntheticPass123!")
    before = db.query(ClinicalAsset).count()

    assert client.get(
        f"/api/patients/{patient.id}/assets", headers=headers
    ).status_code == 403
    assert _attempt_media_write(client, patient.id, headers).status_code == 403
    assert db.query(ClinicalAsset).count() == before


def test_r2_revoked_access_token_cannot_read_or_write_patient_media(
    client, db, dentiste
):
    patient = _patient(db, dentiste.id, "REVOKED-JTI")
    token, headers = _login(client, dentiste.email, "TestPass123!")
    url = f"/api/patients/{patient.id}/assets"
    assert client.get(url, headers=headers).status_code == 200

    token_blacklist.revoke(token, db)
    before = db.query(ClinicalAsset).count()
    assert client.get(url, headers=headers).status_code == 401
    assert _attempt_media_write(client, patient.id, headers).status_code == 401
    assert db.query(ClinicalAsset).count() == before


def test_r2_deactivated_account_cannot_read_or_write_with_existing_jwt(
    client, db, dentiste
):
    patient = _patient(db, dentiste.id, "DISABLED-ACTOR")
    staff = _user(
        db,
        "r2-disabled@example.test",
        employer_id=dentiste.id,
        permissions={"patients": True},
    )
    _token, headers = _login(client, staff.email, "R2SyntheticPass123!")
    url = f"/api/patients/{patient.id}/assets"
    assert client.get(url, headers=headers).status_code == 200

    staff.is_active = False
    db.commit()
    db.expire_all()
    before = db.query(ClinicalAsset).count()
    assert client.get(url, headers=headers).status_code == 401
    assert _attempt_media_write(client, patient.id, headers).status_code == 401
    assert db.query(ClinicalAsset).count() == before
