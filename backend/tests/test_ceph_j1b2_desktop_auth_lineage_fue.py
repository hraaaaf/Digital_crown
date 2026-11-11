"""J1.B2 FUE-I: real desktop HTTP JWT / tenant / audited ceph revision.

All fixtures are disposable. No patient identifiers, images, ML downloads,
production database, installable executable or clinical authority.
"""
from __future__ import annotations

from backend import models
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.tests.conftest import make_user
from backend.tests.p2ter_bridge_synthetic_support import _case, _jwt

PATH = "/api/ia/analyses/"


def _reloaded_graph(db, analysis_id: int) -> dict:
    db.expire_all()
    stored = db.get(models.CephaloAnalysis, analysis_id)
    assert stored is not None
    return stored.angles_data[EVIDENCE_GRAPH_KEY]


def test_real_jwt_cross_tenant_denial_and_clinician_bound_revision(client, db, dentiste):
    patient, study, original = _case(db, dentiste)
    owner = _jwt(client, dentiste)
    study_url = PATH + str(study.id)
    updated = [dict(p) for p in original]
    point = next(p for p in updated if p["id"] == "A")
    before_x = point["x"]
    point["x"] = before_x + 3.0
    payload = {
        "landmarks": updated,
        # Client narrative must never become the landmark's validator.
        "ai_diagnostic": {"validated_by": "attacker-forged", "clinician_id": "999999"},
    }

    unauth = client.put(study_url, json=payload)
    assert unauth.status_code == 401, unauth.text[:500]
    assert _reloaded_graph(db, study.id)["revision"] == 1

    intruder = make_user(db)
    foreign = _jwt(client, intruder)
    denied = client.put(study_url, json=payload, headers=foreign)
    assert denied.status_code == 403, denied.text[:500]
    denied_read = client.get(study_url, headers=foreign)
    assert denied_read.status_code == 403, denied_read.text[:500]
    assert _reloaded_graph(db, study.id)["revision"] == 1

    accepted = client.put(study_url, json=payload, headers=owner)
    assert accepted.status_code == 200, accepted.text[:900]
    revision2 = _reloaded_graph(db, study.id)
    assert revision2["revision"] == 2
    assert revision2["revision_reason"] == "LANDMARK_EDIT"
    active = set(revision2["current_landmark_refs"])
    corrected = [
        item for item in revision2["landmarks"]
        if item["landmark_id"] == "A" and item["evidence_id"] in active
    ]
    assert len(corrected) == 1
    point_evidence = corrected[0]
    assert point_evidence["origin"] == "MANUAL_CORRECTED"
    assert point_evidence["evidence_status"] == "CLINICIAN_VALIDATED"
    assert point_evidence["validated_by"] == str(dentiste.id)
    assert point_evidence["validated_by"] != payload["ai_diagnostic"]["validated_by"]
    assert point_evidence["original_auto_x"] == before_x
    assert point_evidence["x"] == before_x + 3.0
    original_auto = [
        item for item in revision2["landmarks"]
        if item["landmark_id"] == "A" and item["origin"] == "SRPOSE38_AUTO"
    ]
    assert len(original_auto) == 1 and original_auto[0]["x"] == before_x
    assert original_auto[0]["evidence_id"] not in active

    reread = client.get(study_url, headers=owner)
    assert reread.status_code == 200, reread.text[:900]
    assert reread.json()["angles_data"][EVIDENCE_GRAPH_KEY]["revision"] == 2

    # Replaying identical coordinates must be a no-op: no second clinical
    # attestation, no duplicate active landmark, no revision inflation.
    repeat = client.put(study_url, json=payload, headers=owner)
    assert repeat.status_code == 200, repeat.text[:900]
    revision_again = _reloaded_graph(db, study.id)
    assert revision_again["revision"] == 2
    assert revision_again["current_landmark_refs"] == revision2["current_landmark_refs"]
    assert revision_again["history"] == revision2["history"]

    # Neither a tenant denial nor a no-op may turn the unreviewed point set
    # into an automatically validated source of canonical anatomical data.
    auto_current = [
        item for item in revision_again["landmarks"]
        if item["landmark_id"] == "Co"
        and item["evidence_id"] in set(revision_again["current_landmark_refs"])
    ]
    assert auto_current
    assert all(item["origin"] == "SRPOSE38_AUTO" for item in auto_current)
    assert all(item["validated_by"] is None for item in auto_current)
    assert patient.employer_id == dentiste.id
