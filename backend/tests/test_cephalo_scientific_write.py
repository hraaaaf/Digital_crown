"""Typed scientific-write guards and stale-session SQLite regressions."""
import copy

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend import models
from backend.repositories.cephalo_repository import CephaloRepository
from backend.services.cephalo_scientific_write import (
    guard_scientific_payload, save_scientific_transition,
)
from backend.services.cephalo_clinical_cas import STAGING_KEY, R14_KEY
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def _graph(revision=2, case_id="case:synthetic", x=1):
    return {
        "schema_version": "CEPHALO_EVIDENCE_V1",
        "case_id": case_id,
        "revision": revision,
        "sources": [{"marker": x}],
    }


def _data():
    return {
        EVIDENCE_GRAPH_KEY: _graph(),
        STAGING_KEY: {"content_sha256": "a" * 64},
        R14_KEY: {"content_sha256": "b" * 64},
        "metrics": {"SNA": 81},
    }


def _engine():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    models.CephaloAnalysis.__table__.create(engine)
    with Session(engine) as db:
        db.add(models.CephaloAnalysis(
            id=101, patient_id=1, image_original_path="synthetic://case",
            landmarks_data=[], angles_data=_data(),
        ))
        db.commit()
    return engine


@pytest.mark.parametrize("incoming", [
    {},
    {EVIDENCE_GRAPH_KEY: _graph(revision=2, x=9)},
    {EVIDENCE_GRAPH_KEY: _graph(revision=4, x=9)},
    {EVIDENCE_GRAPH_KEY: _graph(revision=1, x=9)},
    {EVIDENCE_GRAPH_KEY: _graph(revision=3, case_id="other", x=9)},
])
def test_scientific_guard_rejects_deleted_unversioned_or_wrong_case_graph(incoming):
    with pytest.raises(HTTPException) as e:
        guard_scientific_payload(previous=_data(), updated=incoming)
    assert e.value.status_code == 409


def test_new_scientific_revision_preserves_historical_r11_r14_receipts():
    replacement = guard_scientific_payload(
        previous=_data(),
        updated={EVIDENCE_GRAPH_KEY: _graph(revision=3, x=9), "metrics": {"SNA": 82}},
    )
    assert replacement[EVIDENCE_GRAPH_KEY]["revision"] == 3
    assert replacement[STAGING_KEY]["content_sha256"] == "a" * 64
    assert replacement[R14_KEY]["content_sha256"] == "b" * 64


def test_scientific_writer_does_not_accept_new_client_receipts():
    prior = {EVIDENCE_GRAPH_KEY: _graph()}
    result = guard_scientific_payload(
        previous=prior,
        updated={
            EVIDENCE_GRAPH_KEY: _graph(revision=3, x=9),
            R14_KEY: {"content_sha256": "c" * 64},
        },
    )
    assert R14_KEY not in result


def test_scientific_sql_write_updates_graph_and_metadata_together():
    engine = _engine()
    with Session(engine) as db:
        obj = db.get(models.CephaloAnalysis, 101)
        save_scientific_transition(
            db=db, analysis=obj,
            updated_angles={EVIDENCE_GRAPH_KEY: _graph(revision=3, x=9)},
            other_values={"landmarks_data": [{"id": "S", "x": 1, "y": 2}],
                          "mm_per_pixel": .25},
        )
        db.commit()
        db.refresh(obj)
        assert obj.angles_data[EVIDENCE_GRAPH_KEY]["revision"] == 3
        assert obj.angles_data[STAGING_KEY]["content_sha256"] == "a" * 64
        assert obj.angles_data[R14_KEY]["content_sha256"] == "b" * 64
        assert obj.landmarks_data[0]["id"] == "S"
        assert obj.mm_per_pixel == .25


def test_repository_refinement_never_drops_scientific_receipts():
    engine = _engine()
    with Session(engine) as db:
        repo = CephaloRepository(db)
        obj = repo.update(101, [], {
            EVIDENCE_GRAPH_KEY: _graph(revision=3, x=9),
            "metrics": {"SNA": 82},
        })
        assert obj.angles_data[STAGING_KEY]["content_sha256"] == "a" * 64
        assert obj.angles_data[R14_KEY]["content_sha256"] == "b" * 64
        assert obj.angles_data[EVIDENCE_GRAPH_KEY]["revision"] == 3


def test_repository_refinement_cannot_erase_scientific_graph():
    engine = _engine()
    with Session(engine) as db:
        repo = CephaloRepository(db)
        with pytest.raises(HTTPException) as e:
            repo.update(101, [], {"metrics": {}})
        assert e.value.status_code == 409
    with Session(engine) as db:
        obj = db.get(models.CephaloAnalysis, 101)
        assert obj.angles_data[EVIDENCE_GRAPH_KEY]["revision"] == 2


def test_two_loaded_scientific_sessions_cannot_both_commit():
    engine = _engine()
    with Session(engine) as stale:
        old = stale.get(models.CephaloAnalysis, 101)
        snapshot = copy.deepcopy(old.angles_data)
        with Session(engine) as winner:
            obj = winner.get(models.CephaloAnalysis, 101)
            save_scientific_transition(
                db=winner, analysis=obj,
                updated_angles={EVIDENCE_GRAPH_KEY: _graph(revision=3, x=7)},
            )
            winner.commit()
        with pytest.raises(HTTPException) as e:
            save_scientific_transition(
                db=stale, analysis=old,
                updated_angles={EVIDENCE_GRAPH_KEY: _graph(revision=3, x=8)},
            )
        assert e.value.status_code == 409
    with Session(engine) as db:
        obj = db.get(models.CephaloAnalysis, 101)
        assert obj.angles_data[EVIDENCE_GRAPH_KEY]["sources"][0]["marker"] == 7
        assert obj.angles_data[R14_KEY]["content_sha256"] == snapshot[R14_KEY]["content_sha256"]


def test_scientific_writer_rejects_concurrent_clinical_decision():
    engine = _engine()
    with Session(engine) as stale:
        old = stale.get(models.CephaloAnalysis, 101)
        with Session(engine) as winner:
            obj = winner.get(models.CephaloAnalysis, 101)
            payload = copy.deepcopy(obj.angles_data)
            payload[STAGING_KEY]["content_sha256"] = "c" * 64
            obj.angles_data = payload
            winner.commit()
        with pytest.raises(HTTPException) as e:
            save_scientific_transition(
                db=stale, analysis=old,
                updated_angles={EVIDENCE_GRAPH_KEY: _graph(revision=3, x=9)},
            )
        assert e.value.status_code == 409
    with Session(engine) as db:
        assert db.get(models.CephaloAnalysis, 101).angles_data[STAGING_KEY]["content_sha256"] == "c" * 64
