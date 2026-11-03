"""CAS controls against stale clinical JSON sessions — synthetic SQLite."""
import copy

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend.services.cephalo_clinical_cas import cas_replace_clinical_json
from backend.services import cephalo_r13_option_decision as r13
from backend.services import cephalo_r14_final_decision as r14
from backend.services import cephalo_r11_r13_staging as staging
from backend.tests.test_cephalo_r13_option_decision import _prepared
from backend.tests.test_cephalo_r14_final_decision import _selected_study


def test_r13_stale_session_cannot_erase_committed_selection(monkeypatch):
    engine, _body, actor, request = _prepared(monkeypatch)
    with Session(engine) as stale:
        old_analysis = stale.get(models.CephaloAnalysis, 101)
        original_sha = old_analysis.angles_data["_cephalo_clinical_staging_v1"]["content_sha256"]
        with Session(engine) as winner:
            response = r13.decide_r13_option(
                patient_id=1, analysis=winner.get(models.CephaloAnalysis, 101),
                actor=actor, request=request, db=winner,
            )
        with pytest.raises(HTTPException) as err:
            # Old loaded study contains pre-decision staging; DB CAS must
            # reject it even if the in-memory scientific validator succeeds.
            r13.decide_r13_option(
                patient_id=1, analysis=old_analysis,
                actor=actor, request=request, db=stale,
            )
        assert err.value.status_code == 409
        assert original_sha != response["staging_sha256"]
    with Session(engine) as db:
        actual = db.get(models.CephaloAnalysis, 101)
        assert actual.angles_data["_cephalo_clinical_staging_v1"]["content_sha256"] == response["staging_sha256"]
        assert db.query(models.AuditLog).filter(
            models.AuditLog.action == r13.DECISION_ACTION
        ).count() == 1


def test_r14_second_stale_session_cannot_replace_final_decision(monkeypatch):
    engine, actor, request = _selected_study(monkeypatch)
    with Session(engine) as stale:
        old_analysis = stale.get(models.CephaloAnalysis, 101)
        assert "_cephalo_r14_final_decision_v1" not in old_analysis.angles_data
        with Session(engine) as winner:
            first = r14.decide_r14_final(
                patient_id=1, analysis=winner.get(models.CephaloAnalysis, 101),
                actor=actor, request=request, db=winner,
            )
        with pytest.raises(HTTPException) as err:
            r14.decide_r14_final(
                patient_id=1, analysis=old_analysis,
                actor=actor, request=request.model_copy(
                    update={"action": "REJECT_FINAL_R14"},
                ), db=stale,
            )
        assert err.value.status_code == 409
    with Session(engine) as db:
        recorded = db.get(models.CephaloAnalysis, 101).angles_data["_cephalo_r14_final_decision_v1"]
        assert recorded["content_sha256"] == first["r14_sha256"]
        assert recorded["decision"] == "VALIDATE_FINAL_R14"
        assert db.query(models.AuditLog).filter(
            models.AuditLog.action == r14.R14_AUDIT_ACTION
        ).count() == 1


def test_cas_rejects_revision_change_loaded_in_another_session(monkeypatch):
    engine, _body, _actor, request = _prepared(monkeypatch)
    with Session(engine) as stale:
        obj = stale.get(models.CephaloAnalysis, 101)
        baseline = copy.deepcopy(obj.angles_data)
        with Session(engine) as concurrent:
            current = concurrent.get(models.CephaloAnalysis, 101)
            angles = copy.deepcopy(current.angles_data)
            angles["_evidence_graph_v1"]["revision"] = 3
            current.angles_data = angles
            concurrent.commit()
        with pytest.raises(HTTPException) as err:
            cas_replace_clinical_json(
                db=stale, analysis=obj, patient_id=1,
                expected_revision=2,
                expected_stage_sha=request.expected_staging_sha256,
                replacement={**baseline, "test_only_flag": True},
            )
        assert err.value.status_code == 409
    with Session(engine) as db:
        actual = db.get(models.CephaloAnalysis, 101).angles_data
        assert actual["_evidence_graph_v1"]["revision"] == 3
        assert "test_only_flag" not in actual


def test_cas_rejects_changed_stage_digest_without_study_revision_bump(monkeypatch):
    engine, _body, _actor, request = _prepared(monkeypatch)
    with Session(engine) as stale:
        obj = stale.get(models.CephaloAnalysis, 101)
        baseline = copy.deepcopy(obj.angles_data)
        with Session(engine) as concurrent:
            current = concurrent.get(models.CephaloAnalysis, 101)
            angles = copy.deepcopy(current.angles_data)
            angles["_cephalo_clinical_staging_v1"]["content_sha256"] = "f" * 64
            current.angles_data = angles
            concurrent.commit()
        with pytest.raises(HTTPException) as err:
            cas_replace_clinical_json(
                db=stale, analysis=obj, patient_id=1,
                expected_revision=2,
                expected_stage_sha=request.expected_staging_sha256,
                replacement={**baseline, "test_only_flag": True},
            )
        assert err.value.status_code == 409
    with Session(engine) as db:
        assert db.get(models.CephaloAnalysis, 101).angles_data["_cephalo_clinical_staging_v1"]["content_sha256"] == "f" * 64


def test_stale_staging_cannot_erase_selected_option(monkeypatch):
    engine, body, actor, request = _prepared(monkeypatch)
    with Session(engine) as stale:
        analysis = stale.get(models.CephaloAnalysis, 101)
        with Session(engine) as winner:
            selected = r13.decide_r13_option(
                patient_id=1, analysis=winner.get(models.CephaloAnalysis, 101),
                actor=actor, request=request, db=winner,
            )
        with pytest.raises(HTTPException) as err:
            staging.stage_clinical_evidence(
                patient_id=1, analysis=analysis, actor=actor,
                body=body, db=stale,
            )
        assert err.value.status_code == 409
    with Session(engine) as db:
        current = db.get(models.CephaloAnalysis, 101).angles_data
        assert current[staging.STAGING_KEY]["content_sha256"] == selected["staging_sha256"]
        assert current[staging.STAGING_KEY]["r13"]["options"][0]["status"] == "CLINICIAN_SELECTED"
        assert db.query(models.AuditLog).filter(
            models.AuditLog.action == staging.STAGING_AUDIT_ACTION
        ).count() == 1
