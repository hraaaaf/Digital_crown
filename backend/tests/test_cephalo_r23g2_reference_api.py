"""R23-G2 Stage 2: real JWT/SQLite study-bound source-only reference API.

Synthetic 38-point cases are NOT calibrated anatomical truth. No patient records.
This module checks only security, revision binding and no fabricated values.
"""
from copy import deepcopy
from fastapi.routing import APIRoute

from backend import models
from backend.routers import ia
from backend.routers.cephalo_analysis_read import get_r23g2_reference_profiles
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.tests.conftest import make_user
from backend.tests.p2ter_bridge_synthetic_support import PATH, _case, _jwt, _read

REFERENCE_SUFFIX = "/r23g2-reference-profiles"
EXPECTED = {"mcnamara": 13, "com": 10, "ricketts_atlas2009": 33, "ricketts_gregoret13": 13}


def _reference(client, study_id, headers, revision=1):
    return client.get(PATH + str(study_id) + REFERENCE_SUFFIX,
                      params={"expected_revision": revision}, headers=headers)


def _assert_source_only(reply, analysis_id, revision):
    assert reply.status_code == 200, reply.text[:800]
    assert reply.headers.get("cache-control") == "no-store"
    body = reply.json()
    assert body["analysis_id"] == analysis_id
    assert body["revision"] == revision
    assert body["authority"] == "EVIDENCE_GRAPH_V1"
    assert body["active_chain"] == "VERIFIED"
    assert body["clinical_release"] is False
    assert body["reference_display_only"] is True
    assert set(body["profiles"]) == set(EXPECTED)
    for name, count in EXPECTED.items():
        profile = body["profiles"][name]
        assert profile["classification_authority"] is False
        assert len(profile["rows"]) == count
        for row in profile["rows"]:
            assert row["classification_authority"] is False
            if row["availability_status"] != "AVAILABLE":
                assert row["value"] is None
                assert not row.get("focus_evidence")
            if row.get("focus_evidence"):
                evidence = row["focus_evidence"]
                assert row["availability_status"] == "AVAILABLE"
                assert evidence["authority"] == "ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1"
                assert evidence["canonical_measurement_id"] == row["canonical_measurement_id"]
                assert evidence["measurement_ref"] in row["measurement_refs"]
                assert evidence["value_authority_method_id"] == row["value_authority_method_id"]
    com = body["profiles"]["com"]["rows"]
    assert any(row["contract_state"].startswith("PENDING_EQUIVALENCE") and row["value"] is None
               for row in com)
    return body


def test_reference_route_unique_without_altering_standard_clinical_get():
    routes = [r for r in ia.router.routes if isinstance(r, APIRoute)
              and r.path == "/analyses/{analysis_id}" + REFERENCE_SUFFIX]
    assert len(routes) == 1
    assert routes[0].methods == {"GET"}
    assert routes[0].endpoint is get_r23g2_reference_profiles


def test_authenticated_reference_is_study_bound_and_standard_get_stays_two_profiles(
    client, db, dentiste
):
    patient, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    baseline = deepcopy(db.get(models.CephaloAnalysis, study.id).angles_data)
    _, scientific = _read(client, study.id, headers)
    assert set(scientific["protocol_profiles"]) == {"steiner", "tweed_merrifield"}
    body = _assert_source_only(_reference(client, study.id, headers), study.id, 1)
    assert "r23g2_reference_profiles" not in scientific
    assert body["analysis_id"] == study.id
    db.expire_all()
    assert db.get(models.CephaloAnalysis, study.id).angles_data == baseline
    assert patient.id == study.patient_id


def test_reference_revision_rejects_stale_request_before_and_after_real_landmark_put(
    client, db, dentiste
):
    _, study, points = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    assert _reference(client, study.id, headers, revision=2).status_code == 409
    assert _reference(client, study.id, headers, revision=0).status_code == 422
    assert _reference(client, study.id, headers, revision=-1).status_code == 422
    changed = deepcopy(points)
    next(p for p in changed if p["id"] == "A")["x"] += 2.0
    edit = client.put(PATH + str(study.id), json={"landmarks": changed}, headers=headers)
    assert edit.status_code == 200, edit.text[:500]
    db.expire_all()
    assert db.get(models.CephaloAnalysis, study.id).angles_data[EVIDENCE_GRAPH_KEY]["revision"] == 2
    assert _reference(client, study.id, headers, revision=1).status_code == 409
    _assert_source_only(_reference(client, study.id, headers, revision=2), study.id, 2)
    _, standard_science = _read(client, study.id, headers)
    assert set(standard_science["protocol_profiles"]) == {"steiner", "tweed_merrifield"}


def test_reference_denies_no_jwt_and_cross_tenant_without_data_mutation(
    client, db, dentiste
):
    _, study, _ = _case(db, dentiste)
    original = deepcopy(db.get(models.CephaloAnalysis, study.id).angles_data)
    outsider = make_user(db, email="r23g2-outsider@cabinet.invalid")
    client.cookies.clear()
    assert _reference(client, study.id, {}, revision=1).status_code == 401
    assert _reference(client, study.id, _jwt(client, outsider), revision=1).status_code == 403
    db.expire_all()
    assert db.get(models.CephaloAnalysis, study.id).angles_data == original
    _assert_source_only(_reference(client, study.id, _jwt(client, dentiste)), study.id, 1)


def test_reference_refuses_corrupt_active_chain_and_other_patient_evidence(
    client, db, dentiste
):
    _, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    record = db.get(models.CephaloAnalysis, study.id)
    original = deepcopy(record.angles_data)
    corrupt = deepcopy(original)
    corrupt[EVIDENCE_GRAPH_KEY]["current_landmark_refs"] = []
    record.angles_data = corrupt
    db.commit()
    db.expire_all()
    blocked = _reference(client, study.id, headers)
    assert blocked.status_code == 409
    assert "NEVER-REAL" not in blocked.text

    record = db.get(models.CephaloAnalysis, study.id)
    cross_patient = deepcopy(original)
    cross_patient[EVIDENCE_GRAPH_KEY]["landmarks"][0]["patient_id"] = study.patient_id + 1000
    record.angles_data = cross_patient
    db.commit()
    db.expire_all()
    blocked = _reference(client, study.id, headers)
    assert blocked.status_code == 409
    assert "NEVER-REAL" not in blocked.text


def test_distinct_studies_with_identical_synthetic_landmark_names_never_share_selection(
    client, db, dentiste
):
    _, study_a, _ = _case(db, dentiste)
    _, study_b, _ = _case(db, dentiste)
    assert study_a.id != study_b.id
    assert study_a.patient_id != study_b.patient_id
    headers = _jwt(client, dentiste)
    a = _assert_source_only(_reference(client, study_a.id, headers), study_a.id, 1)
    b = _assert_source_only(_reference(client, study_b.id, headers), study_b.id, 1)
    assert a["analysis_id"] != b["analysis_id"]
    _, normal_a = _read(client, study_a.id, headers)
    _, normal_b = _read(client, study_b.id, headers)
    assert set(normal_a["protocol_profiles"]) == set(normal_b["protocol_profiles"]) == {
        "steiner", "tweed_merrifield"
    }
