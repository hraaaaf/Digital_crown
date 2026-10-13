"""04.8-C real app E2E security regression — authentic tokens and clinical audit.

Uses the EXISTING pytest shared application fixture, real FastAPI dependencies,
JWTs, signed workstation cookie, owner PIN, patient companion session claim,
and an archived synthetic care sheet. This is not physical printing or a
permit to dispatch. All tests use isolated SQLite and a fake patient record.
"""
import hashlib

import pytest
from sqlalchemy import inspect, text

from backend.tests.test_station_care_sheet_v15 import (
    _identified_session,
    _care_sheet,
    _set_mode,
)
from backend.services.station_print_held_claims_lab import claims, claim_events


@pytest.fixture(autouse=True)
def _require_real_staging_ledger_tables(db):
    """Make the absence of print claims observable, never vacuously true.

    The application's full ORM fixture normally excludes these separately
    staged Alembic tables. Add them in the isolated test SQLite before every
    HTTP request, assert their existence, then drop only these test tables.
    No production schema is changed, and a print claim cannot hide behind
    "table absent" in the E2E assertion.
    """
    claims.create(bind=db.get_bind(), checkfirst=True)
    claim_events.create(bind=db.get_bind(), checkfirst=True)
    try:
        yield
    finally:
        db.rollback()
        claim_events.drop(bind=db.get_bind(), checkfirst=True)
        claims.drop(bind=db.get_bind(), checkfirst=True)

URL = "/api/admin/station-print-config/clinical-check"
EXPECTED = {
    "status": "printing_unavailable",
    "printingAvailable": False,
    "claimCreated": False,
    "archiveVerified": False,
}


def _payload(session_id, document, pin="2468", sha=None):
    return {
        "sessionId": session_id,
        "documentId": document.id,
        "archiveSha256": sha or document.file_hash,
        "ownerPin": pin,
    }


def _headers(client, headers):
    return {
        **headers,
        "origin": str(client.base_url).rstrip("/"),
        "sec-fetch-site": "same-origin",
    }


def _assert_no_print_claims(db):
    names = set(inspect(db.get_bind()).get_table_names())
    # FAIL if the test did not install the actual staging tables: silence
    # caused by missing DDL is NOT a print deduplication proof.
    assert claims.name in names and claim_events.name in names, names
    assert db.execute(text(f"SELECT COUNT(*) FROM {claims.name}")).scalar_one() == 0
    assert db.execute(text(f"SELECT COUNT(*) FROM {claim_events.name}")).scalar_one() == 0


def test_real_jwt_station_cannot_clinical_check_or_print(client, db, dentiste):
    owner_headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST048-E2E-1",
    )
    document = _care_sheet(db, patient)
    result = client.post(
        URL, json=_payload(session_id, document),
        headers=_headers(client, owner_headers),
    )
    # WorkstationModeGate returns 423 for an authenticated Station locked
    # outside the Cabinet. Do NOT downgrade it to a generic 403.
    assert result.status_code == 423, result.text
    assert result.json()["detail"] == "WORKSTATION_STATION_LOCKED"
    # A real identified Station still MUST NOT fetch PDF bytes to its
    # shared kiosk, even with a genuine login and document selector.
    locked_pdf = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=owner_headers,
    )
    assert locked_pdf.status_code == 423, locked_pdf.text
    assert "application/pdf" not in locked_pdf.headers.get("content-type", "")
    _assert_no_print_claims(db)


def test_real_owner_cabinet_jwt_audited_archive_still_denies_print(client, db, dentiste):
    headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST048-E2E-2",
    )
    document = _care_sheet(db, patient)
    _set_mode(client, headers, "cabinet")
    # Before withdrawal approval, the body and policy MUST remain identical
    # to after approval. Do not reveal whether a patient has an archive.
    denied = client.post(URL, json=_payload(session_id, document), headers=_headers(client, headers))
    assert denied.status_code == 200, denied.text
    assert denied.json() == EXPECTED
    assert denied.headers["cache-control"] == "no-store"
    withdrawal = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert withdrawal.status_code == 200, withdrawal.text
    approved = client.post(URL, json=_payload(session_id, document), headers=_headers(client, headers))
    assert approved.status_code == 200, approved.text
    assert approved.json() == EXPECTED
    assert approved.headers["cache-control"] == "no-store"
    assert "application/pdf" not in approved.headers.get("content-type", "")
    assert all(x not in approved.text for x in (
        patient.nom, patient.prenom, document.file_path, document.file_hash,
        "pdfBytes", "deliveryKey", "printerId",
    ))
    _assert_no_print_claims(db)


def test_real_owner_wrong_pin_origin_and_sha_fail_closed(client, db, dentiste):
    headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST048-E2E-3",
    )
    document = _care_sheet(db, patient)
    _set_mode(client, headers, "cabinet")
    payload = _payload(session_id, document)
    bad_pin = client.post(
        URL, json={**payload, "ownerPin": "9999"}, headers=_headers(client, headers),
    )
    assert bad_pin.status_code == 403
    csrf = client.post(
        URL, json=payload, headers={
            **headers, "origin": "https://foreign.invalid", "sec-fetch-site": "cross-site",
        },
    )
    assert csrf.status_code == 403
    unknown_key = client.post(
        URL, json={**payload, "trustedPrinter": True}, headers=_headers(client, headers),
    )
    assert unknown_key.status_code == 422
    digest_denied = client.post(
        URL,
        json={**payload, "archiveSha256": "a" * 64},
        headers=_headers(client, headers),
    )
    assert digest_denied.status_code == 200
    assert digest_denied.json() == EXPECTED
    _assert_no_print_claims(db)
