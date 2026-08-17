"""P0-F — RVG lifecycle must stay authenticated, recoverable and tenant-isolated."""
import base64
from datetime import datetime

from backend import models
from backend.tests.conftest import make_user


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Z4J0AAAAASUVORK5CYII="
)


def _patient(db, owner, suffix):
    patient = models.Patient(
        numero_dossier=f"RVG-{suffix}",
        nom=f"RVG{suffix}",
        prenom="P0",
        date_naissance=datetime(1990, 1, 1),
        sexe="F",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _headers(client, user, password="TestPass123!"):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    # Auth is cookie-first. Clear login cookies so each request below proves
    # the explicit Bearer identity rather than whichever user logged in last.
    client.cookies.clear()
    return {"Authorization": f"Bearer {token}"}


def test_rvg_full_lifecycle_is_authenticated_recoverable_and_tenant_isolated(
    client, db, dentiste, auth_headers
):
    client.cookies.clear()
    patient_a = _patient(db, dentiste, "A")
    other = make_user(db, email="rvg-other@cabinet.ma")
    patient_b = _patient(db, other, "B")
    other_headers = _headers(client, other)

    upload = client.post(
        f"/api/documents/patients/{patient_a.id}/rvg",
        headers=auth_headers,
        files={"file": ("rvg-p0.png", PNG_1X1, "image/png")},
        data={
            "radio_type": "periapical",
            "tooth_number": "11",
            "sector": "antérieur maxillaire",
            "note": "preuve P0-F",
        },
    )
    assert upload.status_code == 200, upload.text
    document_id = upload.json()["id"]

    listed = client.get(
        f"/api/documents/patients/{patient_a.id}/rvg",
        headers=auth_headers,
    )
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()] == [document_id]

    # Download is Bearer-only: query-string credentials must never work.
    missing_bearer = client.get(f"/api/documents/{document_id}/download?token=forbidden")
    assert missing_bearer.status_code == 401, missing_bearer.text
    downloaded = client.get(
        f"/api/documents/{document_id}/download",
        headers=auth_headers,
    )
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content == PNG_1X1

    # Another cabinet cannot discover the patient or touch this document.
    cross_list = client.get(
        f"/api/documents/patients/{patient_a.id}/rvg",
        headers=other_headers,
    )
    assert cross_list.status_code in (403, 404), cross_list.text
    cross_download = client.get(
        f"/api/documents/{document_id}/download",
        headers=other_headers,
    )
    assert cross_download.status_code in (403, 404), cross_download.text
    cross_trash = client.post(
        f"/api/documents/{document_id}/trash",
        headers=other_headers,
    )
    assert cross_trash.status_code in (403, 404), cross_trash.text

    # Own-cabinet delete is recoverable: trash removes it from the active RVG list.
    trashed = client.post(
        f"/api/documents/{document_id}/trash",
        headers=auth_headers,
    )
    assert trashed.status_code == 200, trashed.text
    after_trash = client.get(
        f"/api/documents/patients/{patient_a.id}/rvg",
        headers=auth_headers,
    )
    assert after_trash.status_code == 200, after_trash.text
    assert all(item["id"] != document_id for item in after_trash.json())

    # Cross-tenant restore must also fail without changing the trashed state.
    cross_restore = client.post(
        f"/api/documents/{document_id}/restore",
        headers=other_headers,
    )
    assert cross_restore.status_code in (403, 404), cross_restore.text

    restored = client.post(
        f"/api/documents/{document_id}/restore",
        headers=auth_headers,
    )
    assert restored.status_code == 200, restored.text
    after_restore = client.get(
        f"/api/documents/patients/{patient_a.id}/rvg",
        headers=auth_headers,
    )
    assert after_restore.status_code == 200, after_restore.text
    assert [item["id"] for item in after_restore.json()] == [document_id]

    # Sanity check: the second tenant's own patient remains independent.
    own_other_list = client.get(
        f"/api/documents/patients/{patient_b.id}/rvg",
        headers=other_headers,
    )
    assert own_other_list.status_code == 200, own_other_list.text
    assert own_other_list.json() == []
