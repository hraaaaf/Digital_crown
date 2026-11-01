"""LOT06-C05B-03J selective integration checks: synthetic, no clinical write.

The imported services are deliberately NOT mounted as FastAPI routes.
A failing test here must never be interpreted as a cabinet migration result.
"""
from pathlib import Path

import pytest

from backend.services.imaging_acquisition_preflight_v15 import (
    PreflightRejected,
    resolve_acquisition_preflight,
)
from backend.services import imaging_acquisition_transfer_lab_v15 as lab
from backend.services.imaging_lab_authorized_media_gate_v15 import (
    verify_lab_approved_capture_and_media,
)
from backend.tests.test_clinical_asset_storage import _make_patient, _make_user


def test_no_patient_or_appointment_never_inferred(db):
    result = resolve_acquisition_preflight(db, employer_id=1)
    assert result.status == "AWAITING_HUMAN_LINK"
    assert result.patient_id is None
    assert result.appointment_id is None


def test_exact_synthetic_patient_always_requires_staff_confirmation(db):
    owner = _make_user(db, suffix="c05b03j")
    patient = _make_patient(db, owner.id, suffix="C05B03J")
    result = resolve_acquisition_preflight(db, employer_id=owner.id, patient_id=patient.id)
    assert result.status == "STAFF_CONFIRMATION_REQUIRED"
    assert result.patient_id == patient.id
    assert result.reason == "NO_SERVER_VERIFIED_CAPTURE_CONTEXT"
    with pytest.raises(PreflightRejected, match="PATIENT_NOT_FOUND"):
        resolve_acquisition_preflight(
            db, employer_id=owner.id + 100000, patient_id=patient.id
        )
    with pytest.raises(PreflightRejected, match="APPOINTMENT_NOT_FOUND"):
        resolve_acquisition_preflight(
            db, employer_id=owner.id, patient_id=patient.id,
            appointment_id=999999999
        )


def test_lab_transfer_denied_even_with_opt_in_when_not_test(db, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    with pytest.raises(lab.TransferLabRejected, match="ISOLATED_TRANSFER_DISABLED"):
        lab.guard(db)


def test_authorized_media_gate_denied_outside_lab(db, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    with pytest.raises(lab.TransferLabRejected, match="ISOLATED_TRANSFER_DISABLED"):
        verify_lab_approved_capture_and_media(
            db, tenant=1, device="synthetic", token="invalid",
            capture="synthetic", patient=1, staff_id=1,
            workstation_id="synthetic", appointment=None,
            reason="LAB_WALK_IN", asset_id=1,
            digest="0" * 64, byte_size=1
        )


def test_service_imports_have_no_product_route_wiring():
    backend_main = Path(__file__).resolve().parents[1] / "main.py"
    source = backend_main.read_text(encoding="utf-8")
    assert "imaging_acquisition_preflight_v15" not in source
    assert "imaging_acquisition_transfer_lab_v15" not in source
    assert "imaging_lab_authorized_media_gate_v15" not in source
