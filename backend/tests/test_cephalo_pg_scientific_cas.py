"""Real PostgreSQL two-connection CAS conflicts, synthetic records only.

Executed only with a disposable CI PostgreSQL service (CEPH_PG_URL).
No production database, patient or clinical-rule activation.
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend import models
from backend.services.cephalo_clinical_cas import (
    STAGING_KEY, R14_KEY, cas_replace_clinical_json,
)
from backend.services.cephalo_scientific_write import save_scientific_transition
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


@pytest.fixture(scope="module")
def pg_engine():
    import os
    url = os.getenv("CEPH_PG_URL")
    if not url:
        pytest.skip("Disposable PostgreSQL CI database not provided")
    engine = create_engine(url, isolation_level="READ COMMITTED", future=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS patients (id integer primary key)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS users (id integer primary key)"))
        models.CephaloAnalysis.__table__.create(conn, checkfirst=True)
        models.AuditLog.__table__.create(conn, checkfirst=True)
        conn.execute(text("INSERT INTO patients(id) VALUES(1) ON CONFLICT DO NOTHING"))
        conn.execute(text("INSERT INTO users(id) VALUES(1) ON CONFLICT DO NOTHING"))
    yield engine
    engine.dispose()


def _reset(engine):
    with Session(engine) as db:
        db.query(models.AuditLog).delete()
        db.query(models.CephaloAnalysis).delete()
        db.add(models.CephaloAnalysis(
            id=101, patient_id=1, image_original_path="synthetic://pg-cas",
            landmarks_data=[],
            angles_data={
                EVIDENCE_GRAPH_KEY: {
                    "schema_version": "CEPHALO_EVIDENCE_V1",
                    "case_id": "synthetic:pg", "revision": 2,
                    "sources": [{"marker": "old"}],
                },
                STAGING_KEY: {"content_sha256": "a" * 64},
                R14_KEY: {"content_sha256": "b" * 64},
            },
        ))
        db.commit()


def _parallel(engine, change):
    gate = Barrier(2)
    def worker(marker):
        with Session(engine) as db:
            analysis = db.get(models.CephaloAnalysis, 101)
            gate.wait(timeout=25)
            try:
                change(db, analysis, marker)
                db.commit()
                return ("success", marker)
            except HTTPException as exc:
                db.rollback()
                return ("conflict", exc.status_code)
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(worker, ("first", "second")))
    assert sorted(item[0] for item in results) == ["conflict", "success"]
    assert [x for x in results if x[0] == "conflict"] == [("conflict", 409)]
    return next(x[1] for x in results if x[0] == "success")


def test_pg_two_connections_one_scientific_revision_wins(pg_engine):
    _reset(pg_engine)
    def change(db, analysis, marker):
        new_graph = {
            **analysis.angles_data[EVIDENCE_GRAPH_KEY],
            "revision": 3, "sources": [{"marker": marker}],
        }
        save_scientific_transition(
            db=db, analysis=analysis,
            updated_angles={EVIDENCE_GRAPH_KEY: new_graph},
        )
    winner = _parallel(pg_engine, change)
    with Session(pg_engine) as db:
        saved = db.get(models.CephaloAnalysis, 101).angles_data
        assert saved[EVIDENCE_GRAPH_KEY]["revision"] == 3
        assert saved[EVIDENCE_GRAPH_KEY]["sources"][0]["marker"] == winner
        assert saved[STAGING_KEY]["content_sha256"] == "a" * 64
        assert saved[R14_KEY]["content_sha256"] == "b" * 64


def test_pg_two_connections_one_clinical_stage_cas_wins(pg_engine):
    _reset(pg_engine)
    def change(db, analysis, marker):
        replacement = {
            **analysis.angles_data,
            STAGING_KEY: {"content_sha256": ("c" if marker == "first" else "d") * 64},
        }
        cas_replace_clinical_json(
            db=db, analysis=analysis, patient_id=1, expected_revision=2,
            expected_stage_sha="a" * 64, replacement=replacement,
        )
    winner = _parallel(pg_engine, change)
    with Session(pg_engine) as db:
        saved = db.get(models.CephaloAnalysis, 101).angles_data
        assert saved[STAGING_KEY]["content_sha256"] == (
            "c" if winner == "first" else "d"
        ) * 64
        assert saved[EVIDENCE_GRAPH_KEY]["revision"] == 2
        assert saved[R14_KEY]["content_sha256"] == "b" * 64


def _seed_stage_for_r11_reviews(pg_engine, monkeypatch):
    """Transfer only synthetic fixture JSON and its audited staging into PG CI."""
    from backend.tests.test_cephalo_r11_target_reviews import _case
    from backend.services import cephalo_r11_r13_staging as stage
    engine, body, actor, stage_sha = _case(monkeypatch)
    with Session(engine) as source:
        row = source.get(models.CephaloAnalysis, 101)
        clinical_json = row.angles_data
        staging_log = source.query(models.AuditLog).filter(
            models.AuditLog.action == stage.STAGING_AUDIT_ACTION,
        ).one()
        log_details = staging_log.details
    _reset(pg_engine)
    with Session(pg_engine) as db:
        target = db.get(models.CephaloAnalysis, 101)
        target.angles_data = clinical_json
        db.add(models.AuditLog(
            action=stage.STAGING_AUDIT_ACTION,
            resource_type="CephaloAnalysis", resource_id="101",
            user_id=actor.id, employer_id=actor.get_employer_id(),
            details=log_details, severity="INFO",
        ))
        db.commit()
    return actor, stage_sha, body


@pytest.mark.parametrize("same_target", [True, False], ids=["same-target","different-targets"])
def test_pg_concurrent_r11_target_reviews_are_serialized(pg_engine, monkeypatch, same_target):
    """Real PG16: identical target => one audit/409, separate targets => two audits."""
    from backend.services import cephalo_r11_target_reviews as reviews
    actor, stage_sha, _body = _seed_stage_for_r11_reviews(pg_engine, monkeypatch)
    gate = Barrier(2)
    def worker(target_type):
        with Session(pg_engine) as db:
            analysis = db.get(models.CephaloAnalysis, 101)
            group, key = (
                ("findings", "finding_id") if target_type == "finding"
                else ("diagnoses", "diagnosis_id")
            )
            target_id = analysis.angles_data[EVIDENCE_GRAPH_KEY][group][0][key]
            request = reviews.R11TargetReviewRequest(
                expected_revision=2, expected_staging_sha256=stage_sha,
                target_type=target_type, target_id=target_id,
                action="CONFIRM_R11_TARGET_REVIEW",
            )
            gate.wait(timeout=25)
            try:
                answer = reviews.record_r11_target_review(
                    patient_id=1, analysis=analysis, actor=actor,
                    request=request, db=db,
                )
                return ("success", answer["audit_id"])
            except HTTPException as error:
                db.rollback()
                return ("conflict", error.status_code)
    targets = ("finding", "finding" if same_target else "diagnosis")
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(worker, targets))
    with Session(pg_engine) as db:
        count = db.query(models.AuditLog).filter(
            models.AuditLog.action == reviews.R11_TARGET_ACTION,
        ).count()
        assert db.get(models.CephaloAnalysis, 101).angles_data[STAGING_KEY]["content_sha256"] == stage_sha
    if same_target:
        assert sorted(x[0] for x in outcomes) == ["conflict", "success"]
        assert [x for x in outcomes if x[0] == "conflict"] == [("conflict", 409)]
        assert count == 1
    else:
        assert [x[0] for x in outcomes] == ["success", "success"]
        assert count == 2
