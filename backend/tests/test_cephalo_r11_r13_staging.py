"""R11-R13 staged proof: only source-locked drafts, no R14 approval."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend import models
from backend.services import cephalo_r11_r13_staging as staging
from backend.services import cephalo_r15_clinical_studio as studio
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, EVIDENCE_SCHEMA_VERSION
from backend.services.cephalo_r13_therapeutic_safety import validate_r13_therapeutic_options
from backend.tests.test_cephalo_r13_therapeutic_safety import (
    _r12, _criteria, _option, _diagnostic_registry, _therapeutic_registry,
)


def fixture():
    r12 = _r12()
    criteria = _criteria(r12)
    body = staging.R11R13StagingRequest(
        expected_revision=2, action="STAGE_R11_R13",
        problems=list(r12.problems), objectives=list(r12.objectives),
        criteria=criteria, options=[_option(r12, criteria)],
    )
    graph = r12.diagnostic_graph
    fields = ("sources", "landmarks", "constructions", "measurements",
              "normative_evaluations", "findings", "diagnoses", "validations")
    payload = dict(schema_version=EVIDENCE_SCHEMA_VERSION, case_id="synthetic:A", revision=2)
    payload.update({key: [obj.model_dump(mode="json") for obj in getattr(graph,key)] for key in fields})
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    models.CephaloAnalysis.__table__.create(engine)
    models.AuditLog.__table__.create(engine)
    with Session(engine) as db:
        db.add(models.CephaloAnalysis(
            id=101, patient_id=1, image_original_path="synthetic",
            landmarks_data={}, angles_data={EVIDENCE_GRAPH_KEY: payload}
        ))
        db.commit()
    actor = SimpleNamespace(
        id=1, role=models.UserRole.DENTISTE, is_active=True, employer_id=None,
        approval_status="approved", get_employer_id=lambda: 1,
    )
    return engine, body, actor


def approve_test_rules(monkeypatch):
    monkeypatch.setattr(
        staging, "project_runtime_chain_read_path",
        lambda data, patient_id: {"scientific_read_path": {"active_chain": "VERIFIED"}},
    )
    monkeypatch.setattr(
        staging, "validate_r13_therapeutic_options",
        lambda snapshot: validate_r13_therapeutic_options(
            snapshot, diagnostic_rule_registry=_diagnostic_registry(),
            therapeutic_rule_registry=_therapeutic_registry(),
        ),
    )


def test_r11_r13_request_forbids_signature_and_untyped_revision():
    _engine, body, _actor = fixture()
    with pytest.raises(ValidationError):
        staging.R11R13StagingRequest.model_validate({
            **body.model_dump(mode="json"), "signature": "NOT_ALLOWED"
        })
    with pytest.raises(ValidationError):
        staging.R11R13StagingRequest.model_validate({
            **body.model_dump(mode="json"), "expected_revision": True
        })


def test_production_registries_empty_cannot_be_promoted(monkeypatch):
    engine, body, actor = fixture()
    monkeypatch.setattr(
        staging, "project_runtime_chain_read_path",
        lambda data, patient_id: {"scientific_read_path": {"active_chain": "VERIFIED"}},
    )
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        with pytest.raises(HTTPException) as error:
            staging.stage_clinical_evidence(
                patient_id=1, analysis=analysis, actor=actor, body=body, db=db
            )
        assert error.value.status_code == 409
        assert db.query(models.AuditLog).count() == 0


def test_valid_synthetic_rules_roundtrip_and_R14_stays_blocked(monkeypatch):
    approve_test_rules(monkeypatch)
    engine, body, actor = fixture()
    with Session(engine) as db:
        result = staging.stage_clinical_evidence(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, body=body, db=db,
        )
        assert result["state"] == "SOURCE_VALIDATED_NON_FINAL"
        assert result["clinical_validation_available"] is False
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        assert staging.read_staged_clinical_evidence(
            patient_id=1, analysis=analysis
        )["state"] == "CURRENT_NON_FINAL"
        assert db.query(models.AuditLog).count() == 1
        assert analysis.angles_data[staging.STAGING_KEY]["r13"]["option_validations"] == []
        snapshot = studio.build_r15_clinical_studio_snapshot(
            patient_id=1, analysis_id=101, angles_data=analysis.angles_data,
        )
        assert snapshot["clinical_validation_available"] is False


def test_revision_change_and_content_change_invalidate(monkeypatch):
    approve_test_rules(monkeypatch)
    engine, body, actor = fixture()
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        staging.stage_clinical_evidence(
            patient_id=1, analysis=analysis, actor=actor, body=body, db=db,
        )
        original = dict(analysis.angles_data)
        analysis.angles_data = {
            **original, EVIDENCE_GRAPH_KEY: {
                **original[EVIDENCE_GRAPH_KEY], "revision": 3
            }
        }
        db.commit()
        assert staging.read_staged_clinical_evidence(
            patient_id=1, analysis=analysis
        )["state"] == "STALE"
        changed = dict(original[staging.STAGING_KEY])
        changed["actor_user_id"] = 5
        analysis.angles_data = {**original, staging.STAGING_KEY: changed}
        db.commit()
        assert staging.read_staged_clinical_evidence(
            patient_id=1, analysis=analysis
        )["state"] == "STALE"


def test_other_patient_or_non_dentist_rejected():
    engine, body, actor = fixture()
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        with pytest.raises(HTTPException) as error:
            staging.stage_clinical_evidence(
                patient_id=2, analysis=analysis, actor=actor, body=body, db=db,
            )
        assert error.value.status_code == 404
        actor.role = models.UserRole.SECRETAIRE
        with pytest.raises(HTTPException) as error:
            staging.stage_clinical_evidence(
                patient_id=1, analysis=analysis, actor=actor, body=body, db=db,
            )
        assert error.value.status_code == 403
