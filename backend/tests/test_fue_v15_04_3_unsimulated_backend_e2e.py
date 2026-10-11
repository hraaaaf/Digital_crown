"""Real HTTP insurance finalization -> staff approval -> patient station PDF retrieval.

Synthetic clinic/patient/template and isolated source store. No renderer/archiver/
station-finalization monkeypatch: the PDF bytes are rendered and archived by the
real production services. A TEST-ONLY registry SHA override is required because
the synthetic licensed template cannot equal the cabinet real-world template.
This test does not certify real insurer templates or physical user experience.
"""
import hashlib
from datetime import datetime

import fitz

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.routers.patient_companion_common import create_patient_device_token
from backend.schemas.insurance_submission import InsuranceOrganization
from backend.services.insurance_validation import validate_insurance_draft_by_practitioner
from backend.services.insurance_pdf_overlay import InsuranceOverlayProfile, InsuranceOverlayPlacement
from backend.services.insurance_template_registry import CNSS_610_1_04
from backend.tests.test_insurance_validation import _prepared_fixture, _complete_admin
from backend.tests.test_station_care_sheet_v15 import _set_mode, _station


def test_fue043_true_http_finalize_staff_approve_patient_retrieve_without_renderer_stub(
    client, auth_headers, db, dentiste, tmp_path, monkeypatch,
):
    draft, _locked_ngap = _prepared_fixture(
        client, auth_headers, db, dentiste, tmp_path,
        organization=InsuranceOrganization.CNSS,
    )
    draft = draft.model_copy(update={"administrative": _complete_admin(draft)})
    validated = validate_insurance_draft_by_practitioner(
        db, draft=draft, practitioner_id=dentiste.id,
        source_store_root=tmp_path,
        validated_at=datetime(2026, 9, 14, 20, 30),
    )
    digest = validated.template.template_hash
    assert digest is not None

    test_overlay = InsuranceOverlayProfile(
        organization="CNSS", template_version=CNSS_610_1_04.version,
        template_hash=digest, profile_version="fue043-synthetic-validated-v1",
        placements=(InsuranceOverlayPlacement(
            field_key="computed.total_amount_mad", page_index=0, x=72, y=96,
        ),),
    )

    # Only test configuration: redirect immutable source store to tmp_path and
    # identify the synthetic template hash. Never stub the render/finalize route.
    monkeypatch.setattr(
        "backend.routers.insurance_submissions.get_insurance_source_store_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "backend.routers.insurance_submissions._template_config_for",
        lambda organization: (CNSS_610_1_04, digest, test_overlay),
    )
    _headers = _station(client, dentiste)
    _set_mode(client, _headers, "cabinet")

    response = client.post(
        "/api/documents/insurance-submissions/finalize",
        headers=_headers, json=validated.model_dump(mode="json"),
    )
    assert response.status_code == 200, response.text
    archive_id = response.json()["document_id"]
    archived = db.get(models.DocumentArchive, archive_id)
    assert archived is not None
    assert archived.patient_id == validated.patient_id
    assert archived.file_hash == response.json()["file_hash"]
    assert archived.clinical_data["render_evidence"]["renderer"] == "PDF_OVERLAY_V1"
    assert archived.clinical_data["render_evidence"]["rendered_pdf_sha256"] == archived.file_hash

    approval = client.post(
        f"/api/workstation/documents/care-sheet/{archive_id}/authorize-withdrawal",
        headers=_headers,
    )
    assert approval.status_code == 200, approval.text
    assert approval.json()["created"] is True
    _set_mode(client, _headers, "station")

    issued = client.post("/api/workstation/patient-session", headers=_headers)
    assert issued.status_code == 201, issued.text
    session_id = issued.json()["sessionId"]
    raw_token = issued.json()["handoffUrl"].split("stationSession=", 1)[1]

    identity = PatientCompanionIdentity(
        provider="local_bridge", subject="device:fue043-full-real-flow",
        last_seen_at=datetime.utcnow(),
    )
    db.add(identity)
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id, employer_id=dentiste.id,
        patient_id=validated.patient_id, relationship_type="SELF",
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    patient_headers = {
        "Authorization": f"Bearer {create_patient_device_token(identity, access)}",
    }
    claim = client.post(
        "/api/workstation/patient-session/claim",
        headers=patient_headers,
        json={"token": raw_token, "accessId": access.public_id},
    )
    assert claim.status_code == 200, claim.text

    download = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{archive_id}",
        headers=_headers,
    )
    assert download.status_code == 200, download.text
    assert download.headers["content-type"].startswith("application/pdf")
    assert download.headers["cache-control"] == "no-store"
    assert hashlib.sha256(download.content).hexdigest() == archived.file_hash
    actual_pdf = fitz.open(stream=download.content, filetype="pdf")
    try:
        assert actual_pdf.page_count == 2
    finally:
        actual_pdf.close()

    actions = {
        log.action for log in db.query(models.AuditLog).filter(
            models.AuditLog.resource_type == "DocumentArchive",
            models.AuditLog.resource_id == str(archive_id),
            models.AuditLog.employer_id == dentiste.id,
        )
    }
    assert {
        "STATION_CARE_SHEET_TRUSTED_FINALIZATION_V1",
        "STATION_CARE_SHEET_WITHDRAWAL_AUTHORIZED",
        "STATION_CARE_SHEET_WITHDRAWN",
    }.issubset(actions)
