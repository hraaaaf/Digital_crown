"""Céphalo V1 LOT 1/4 — ten synthetic FUE PREFLIGHT gates.

These are automated preflight checks, NOT the 10 user-acceptance sessions
performed by a dentist at the clinic. No patient-specific clinical approval,
source/rule activation, signed plan or final PDF release is asserted here.
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend import models
from backend.services import cephalo_diagnostic_rule_registry as diagnostic
from backend.services import cephalo_therapeutic_rule_registry as therapeutic
from backend.services import cephalo_norm_registry as norms
from backend.services import cephalo_r11_r13_staging as staging
from backend.services import cephalo_r11_target_reviews as r11
from backend.services import cephalo_r11_r12_attestation as attestation
from backend.services import cephalo_r13_option_decision as r13
from backend.services import cephalo_r14_final_decision as r14
from backend.services import cephalo_r15_clinical_studio as studio
from backend.services import cephalo_pdf_projection as pdf
from backend.tests.test_cephalo_r11_r13_staging import fixture, approve_test_rules
from backend.tests.test_cephalo_r13_option_decision import _source_locked_test_validators
from backend.tests.test_cephalo_r14_final_decision import _selected_study


def _stage_with_test_rules(monkeypatch):
    _source_locked_test_validators(monkeypatch)
    engine, body, actor = fixture()
    with Session(engine) as db:
        stage = staging.stage_clinical_evidence(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, body=body, db=db,
        )
    return engine, body, actor, stage["content_sha256"]


def test_fue_01_production_rule_registries_are_empty_and_norms_inert():
    assert len(diagnostic.registry.finding_rules) == 0
    assert len(diagnostic.registry.diagnostic_rules) == 0
    assert len(therapeutic.registry.sources) == 0
    assert len(therapeutic.registry.criterion_rules) == 0
    assert len(therapeutic.registry.option_rules) == 0
    assert all(not ref.active_for_patient_classification for ref in norms.registry.references.values())


def test_fue_02_absent_study_cannot_offer_r15_authority():
    result = studio.build_r15_clinical_studio_snapshot(
        patient_id=1, analysis_id=None, angles_data=None,
    )
    assert result["clinical_validation_available"] is False
    assert "cephalo_analysis_missing" in result["blocking_gates"]
    assert all(not stage["clinician_action"]["available"] for stage in result["stages"])


def test_fue_03_legacy_forged_diagnosis_does_not_complete_pdf():
    result = pdf.build_cephalo_pdf_projection(
        patient_id=1, analysis_id=101,
        angles_data={
            "ai_diagnostic": {"diagnosis": "FAKE_CERTIFICATION_SENTINEL"},
            "clinical_data": {"plan_traitement": "FAKE_PLAN_SENTINEL"},
            "clinical_validation_available": True,
        },
    )
    assert result["document_state"] == "INCOMPLETE"
    assert "typed_evidence_graph_missing" in result["blocking_gates"]
    assert "FAKE_CERTIFICATION_SENTINEL" not in str(result)
    assert "FAKE_PLAN_SENTINEL" not in str(result)


def test_fue_04_wrong_patient_cannot_stage_clinical_graph():
    engine, body, actor = fixture()
    with Session(engine) as db:
        with pytest.raises(HTTPException) as exc:
            staging.stage_clinical_evidence(
                patient_id=99, analysis=db.get(models.CephaloAnalysis, 101),
                actor=actor, body=body, db=db,
            )
        assert exc.value.status_code == 404
        assert db.query(models.AuditLog).count() == 0


def test_fue_05_production_without_approved_diagnostic_rules_rejects_staging(monkeypatch):
    engine, body, actor = fixture()
    monkeypatch.setattr(
        staging, "project_runtime_chain_read_path",
        lambda payload, patient_id: {"scientific_read_path": {"active_chain": "VERIFIED"}},
    )
    with Session(engine) as db:
        with pytest.raises(HTTPException) as exc:
            staging.stage_clinical_evidence(
                patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
                actor=actor, body=body, db=db,
            )
        assert exc.value.status_code == 409
        assert db.query(models.AuditLog).count() == 0


def test_fue_06_browser_cannot_forge_r11_practitioner_confirmation():
    allowed = r11.R11TargetReviewRequest(
        expected_revision=2, expected_staging_sha256="a" * 64,
        target_type="finding", target_id="synthetic:target",
        action="CONFIRM_R11_TARGET_REVIEW",
    )
    for forbidden, value in (
        ("clinician_id", "clinician:other"),
        ("signature", "fake-signature"),
        ("clinical_validation_available", True),
    ):
        with pytest.raises(ValidationError):
            r11.R11TargetReviewRequest.model_validate({
                **allowed.model_dump(), forbidden: value,
            })


def test_fue_07_missing_diagnosis_review_blocks_global_r11_r12(monkeypatch):
    engine, _body, actor, stage_sha = _stage_with_test_rules(monkeypatch)
    with Session(engine) as db:
        study = db.get(models.CephaloAnalysis, 101)
        finding = study.angles_data["_evidence_graph_v1"]["findings"][0]["finding_id"]
        r11.record_r11_target_review(
            patient_id=1, analysis=study, actor=actor, db=db,
            request=r11.R11TargetReviewRequest(
                expected_revision=2, expected_staging_sha256=stage_sha,
                target_type="finding", target_id=finding,
                action="CONFIRM_R11_TARGET_REVIEW",
            ),
        )
        with pytest.raises(HTTPException) as exc:
            attestation.attest_r11r12(
                patient_id=1, analysis=study, actor=actor, db=db,
                request=attestation.R11R12AttestationRequest(
                    expected_revision=2, expected_staging_sha256=stage_sha,
                    action="ATTEST_R11_R12",
                ),
            )
        assert exc.value.status_code == 409
        assert db.query(models.AuditLog).count() == 2


def test_fue_08_replayed_r11_review_writes_no_duplicate_audit(monkeypatch):
    engine, _body, actor, stage_sha = _stage_with_test_rules(monkeypatch)
    with Session(engine) as db:
        study = db.get(models.CephaloAnalysis, 101)
        finding = study.angles_data["_evidence_graph_v1"]["findings"][0]["finding_id"]
        req = r11.R11TargetReviewRequest(
            expected_revision=2, expected_staging_sha256=stage_sha,
            target_type="finding", target_id=finding,
            action="CONFIRM_R11_TARGET_REVIEW",
        )
        r11.record_r11_target_review(
            patient_id=1, analysis=study, actor=actor, request=req, db=db,
        )
        with pytest.raises(HTTPException) as exc:
            r11.record_r11_target_review(
                patient_id=1, analysis=study, actor=actor, request=req, db=db,
            )
        assert exc.value.status_code == 409
        assert db.query(models.AuditLog).filter(
            models.AuditLog.action == r11.R11_TARGET_ACTION,
        ).count() == 1


def test_fue_09_r13_option_cannot_be_selected_without_r11_r12_attestation(monkeypatch):
    engine, body, actor, stage_sha = _stage_with_test_rules(monkeypatch)
    with Session(engine) as db:
        with pytest.raises(HTTPException) as exc:
            r13.decide_r13_option(
                patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
                actor=actor, db=db,
                request=r13.R13DecisionRequest(
                    expected_revision=2, expected_staging_sha256=stage_sha,
                    action="SELECT_OPTION", option_id=body.options[0].option_id,
                ),
            )
        assert exc.value.status_code == 409
        assert db.query(models.AuditLog).count() == 1


def test_fue_10_r14_unapproved_science_remains_blocked_and_pdf_incomplete(monkeypatch):
    # Upstream positive rules are TEST-ONLY; R14 is checked with production registries.
    engine, actor, request = _selected_study(monkeypatch, trusted_r14=False)
    with Session(engine) as db:
        study = db.get(models.CephaloAnalysis, 101)
        with pytest.raises(HTTPException) as exc:
            r14.decide_r14_final(
                patient_id=1, analysis=study, actor=actor, request=request, db=db,
            )
        assert exc.value.status_code == 409
        assert r14.R14_KEY not in study.angles_data
        projection = pdf.build_cephalo_pdf_projection(
            patient_id=1, analysis_id=study.id, angles_data=study.angles_data,
        )
        assert projection["document_state"] == "INCOMPLETE"
        assert projection["clinical_validation_available"] is False

# External pixel coefficients are *untrusted inputs*, not calibration evidence.
# The values below reproduce a published/mirror conflict, NOT physical ground truth.
# All landmarks and ruler points are synthetic; these are technical preflight checks,
# not the ten practitioner-led FUE sessions at the clinic.
@pytest.mark.parametrize("untrusted_mm_per_pixel", [0.139, 1.139])
def test_preflight_external_machine_ratio_alone_never_unlocks_linear_mm(untrusted_mm_per_pixel):
    from datetime import datetime, timezone

    from backend.services.cephalo_runtime_evidence import build_cephalo_runtime_evidence_payload
    from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
    from backend.tests.test_cephalo_runtime_evidence import _graph, _result, _srpose_raw

    payload = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="synthetic-promax-check.jpg",
        result=_result(untrusted_mm_per_pixel),
        landmarks=_srpose_raw(),
        inference_mode="SOTA_ONNX_38",
        case_id="cephalo:synthetic-promax-scale-gate",
        recorded_at=datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc),
    )
    assert not any(source["kind"] == "calibration" for source in payload["sources"])
    linear = [row for row in payload["measurements"] if row["requires_calibration"]]
    assert linear, "The test must exercise actual calibrated measurement records"
    assert all(row["value"] is None for row in linear)
    assert all(row["availability_status"] != "AVAILABLE" for row in linear)
    validate_case_evidence_graph(
        _graph(payload), patient_id=7, case_id="cephalo:synthetic-promax-scale-gate"
    )


@pytest.mark.parametrize("untrusted_mm_per_pixel", [0.139, 1.139])
def test_preflight_external_ratio_cannot_override_inconsistent_two_point_ruler(untrusted_mm_per_pixel):
    from datetime import datetime, timezone

    from backend.services.cephalo_runtime_evidence import (
        CephaloRuntimeEvidenceError,
        build_cephalo_runtime_evidence_payload,
    )
    from backend.tests.test_cephalo_runtime_evidence import _result, _srpose_raw

    # The independent synthetic ruler is 10 mm / 50 px = 0.2 mm/px.
    # Neither disputed external coefficient is consistent with that ruler.
    with pytest.raises(
        CephaloRuntimeEvidenceError,
        match="Calibration geometry does not match runtime ratio",
    ):
        build_cephalo_runtime_evidence_payload(
            patient_id=7,
            image_record_id="synthetic-promax-check.jpg",
            result=_result(untrusted_mm_per_pixel),
            landmarks=_srpose_raw(),
            inference_mode="SOTA_ONNX_38",
            case_id="cephalo:synthetic-promax-scale-gate",
            is_calibrated=True,
            calibration_data={
                "method": "MANUAL_TWO_POINT",
                "p1": {"x": 0, "y": 0},
                "p2": {"x": 0, "y": 50},
                "distance_mm": 10,
            },
            recorded_at=datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc),
        )
