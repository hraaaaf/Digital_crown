from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from backend import models
from backend.security import get_password_hash
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_GRAPH_KEY,
    build_cephalo_runtime_evidence_payload,
)
from backend.services.ortho_workbench_export import (
    OrthoWorkbenchExportError,
    OrthoWorkbenchExportRequest,
    build_ortho_workbench_export,
)
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


NOW = datetime(2026, 10, 3, 10, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 10, 3, 10, 15, tzinfo=timezone.utc)
EXPORT_AT = datetime(2026, 10, 3, 10, 30, tzinfo=timezone.utc)
CASE_ID = "cephalo:lot07g-export-fixture"


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _patient(db, employer_id: int):
    patient = models.Patient(
        numero_dossier="LOT07G-EXPORT",
        nom="Synthetic",
        prenom="Export",
        date_naissance=datetime(2000, 1, 1),
        sexe="F",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _analysis(db, patient_id: int, *, with_graph: bool = True):
    raw = _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    angles = result.model_dump()
    if with_graph:
        angles[EVIDENCE_GRAPH_KEY] = build_cephalo_runtime_evidence_payload(
            patient_id=patient_id,
            image_record_id="radio-lot07g.jpg",
            result=result,
            landmarks=raw,
            inference_mode="SOTA_ONNX_38",
            case_id=CASE_ID,
            recorded_at=NOW,
        )
    analysis = models.CephaloAnalysis(
        patient_id=patient_id,
        image_original_path="radio-lot07g.jpg",
        landmarks_data=raw,
        angles_data=angles,
        is_calibrated=False,
        mm_per_pixel=None,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def _request(**overrides):
    payload = {
        "timepoint": "T0",
        "layer_visibility": {
            "landmarks": True,
            "plans": True,
            "hard_tissue": False,
            "teeth": True,
            "soft_tissue": True,
            "measurements": True,
            "t1": False,
            "t2": False,
        },
        "layer_opacity": {
            "landmarks": 1.0,
            "plans": 1.0,
            "hard_tissue": 0.85,
            "teeth": 1.0,
            "soft_tissue": 0.9,
            "measurements": 1.0,
            "t1": 0.5,
            "t2": 0.5,
        },
        "traced_structures": [],
        "session_edit_audit": [],
    }
    payload.update(overrides)
    return OrthoWorkbenchExportRequest.model_validate(payload)


def test_lot07g_contract_freezes_authority_and_no_formula_invariants():
    root = Path(__file__).resolve().parents[2]
    contract = json.loads(
        (root / "docs/audits/schemas/ortho_workbench_export_contract_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["export_schema_version"] == "ORTHO_WORKBENCH_EXPORT_V1"
    assert contract["authority"]["scientific"] == "LOT06_CANONICAL_ENGINE"
    assert contract["authority"]["scientific_read"] == "EVIDENCE_GRAPH_V1"
    assert "NO_CEPHALOMETRIC_FORMULA_IN_EXPORT" in contract["invariants"]
    assert "NO_FRONTEND_SCIENTIFIC_RECALCULATION" in contract["invariants"]
    assert "MISSING_SCIENTIFIC_PREREQUISITE_FAILS_CLOSED" in contract["invariants"]


def test_lot07g_export_projects_canonical_evidence_without_recomputing_science(db, dentiste):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id)

    exported = build_ortho_workbench_export(
        db,
        analysis=analysis,
        employer_id=dentiste.id,
        request=_request(),
        exported_at=EXPORT_AT,
    )

    assert exported["schema_version"] == "ORTHO_WORKBENCH_EXPORT_V1"
    assert exported["authority"]["scientific"] == "LOT06_CANONICAL_ENGINE"
    assert exported["authority"]["scientific_read"] == "EVIDENCE_GRAPH_V1"
    assert exported["case"]["patient_id"] == patient.id
    assert exported["case"]["analysis_id"] == analysis.id
    assert exported["case"]["case_id"] == CASE_ID
    assert exported["case"]["timepoint_id"] == "T0"
    assert exported["case"]["source_evidence_id"] == f"source:{CASE_ID}:ceph"
    assert exported["case"]["source_record_id"] == "radio-lot07g.jpg"
    assert exported["case"]["source_provenance"]["kind"] == "lateral_ceph"
    assert len(exported["landmarks"]["items"]) == 38
    construction_landmark_refs = {
        ref
        for item in exported["lot06_scientific_refs"]["construction_refs"]
        for ref in item["landmark_refs"]
    }
    exported_landmark_refs = {
        item["evidence_id"] for item in exported["landmarks"]["items"]
    } | {
        item["evidence_id"] for item in exported["landmarks"]["canonical_dependency_items"]
    }
    assert construction_landmark_refs <= exported_landmark_refs
    assert exported["landmarks"]["current_refs"]
    assert exported["lot06_scientific_refs"]["construction_refs"]
    assert exported["lot06_scientific_refs"]["measurement_refs"]
    assert exported["lot06_scientific_refs"]["canonical_measurements"]
    assert exported["calibration"]["current"] is None
    assert exported["traced_structures"]["items"] == []
    assert exported["media"]["schema_version"] == "ORTHO_MEDIA_RECORD_V1"
    assert all(slot["state"] == "EMPTY" for slot in exported["media"]["photo_slots"])

    serialized = json.dumps(exported, default=str)
    for forbidden in ("formula", "threshold", "norm_mean", "diagnosis_rule"):
        assert f'"{forbidden}"' not in serialized


def test_lot07g_export_includes_backend_persisted_manual_correction_history(db, dentiste):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id)
    previous = analysis.angles_data[EVIDENCE_GRAPH_KEY]
    edited = [dict(item) for item in analysis.landmarks_data]
    target = next(item for item in edited if item["id"] == "A")
    target["x"] += 2.0
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(edited))
    revised = rebuild_evidence_after_landmark_edit(
        previous_payload=previous,
        patient_id=patient.id,
        image_record_id="radio-lot07g.jpg",
        result=result,
        runtime_landmarks=edited,
        clinician_id=str(dentiste.id),
        validated_at=LATER,
    )
    analysis.landmarks_data = edited
    analysis.angles_data = {**result.model_dump(), EVIDENCE_GRAPH_KEY: revised}
    db.commit()
    db.refresh(analysis)

    exported = build_ortho_workbench_export(
        db,
        analysis=analysis,
        employer_id=dentiste.id,
        request=_request(
            session_edit_audit=[
                {
                    "sequence": 1,
                    "action": "EDIT",
                    "transactionId": "landmark-edit-1",
                    "changedLandmarkIds": ["A"],
                }
            ]
        ),
        exported_at=EXPORT_AT,
    )

    corrections = exported["correction_history"]["manual_corrections"]
    assert any(item["landmark_id"] == "A" and item["validated_by"] == str(dentiste.id) for item in corrections)
    assert exported["correction_history"]["persisted_revision_count"] == 2
    assert exported["correction_history"]["session_operations"]["authority"] == (
        "SESSION_OPERATIONAL_UNDO_REDO_ONLY"
    )


def test_lot07g_export_fails_closed_without_typed_evidence_graph(db, dentiste):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id, with_graph=False)
    with pytest.raises(OrthoWorkbenchExportError, match="evidence graph"):
        build_ortho_workbench_export(
            db,
            analysis=analysis,
            employer_id=dentiste.id,
            request=_request(),
            exported_at=EXPORT_AT,
        )


def test_lot07g_export_fails_closed_for_unavailable_visible_layer():
    visibility = _request().layer_visibility.copy()
    visibility["hard_tissue"] = True
    with pytest.raises(ValueError, match="unavailable LOT07 layer"):
        _request(layer_visibility=visibility)


def test_lot07g_export_rejects_client_measurement_authority():
    now = NOW.isoformat()
    with pytest.raises(ValueError):
        _request(
            traced_structures=[
                {
                    "structure_id": "forged-canonical",
                    "structure_class": "CANONICAL_CONSTRUCTION",
                    "authority_state": "MEASUREMENT_AUTHORITATIVE",
                    "coordinate_space": "IMAGE_PIXEL",
                    "version": "1",
                    "source_record_id": "client:forged",
                    "created_at": now,
                    "updated_at": now,
                    "provenance": {"source": "client"},
                    "edit_history": [],
                }
            ]
        )


def test_lot07g_route_is_mounted_once(client):
    from backend.main import app

    matches = [
        route
        for route in app.routes
        if getattr(route, "path", None) == "/api/ia/analyses/{analysis_id}/ortho-workbench-export"
        and "POST" in (getattr(route, "methods", set()) or set())
    ]
    assert len(matches) == 1


def test_lot07g_route_preserves_patient_access_and_returns_fail_closed_409(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id, with_graph=False)
    response = client.post(
        f"/api/ia/analyses/{analysis.id}/ortho-workbench-export",
        headers=auth_headers,
        json=_request().model_dump(mode="json"),
    )
    assert response.status_code == 409
    assert "Export orthodontique bloqué" in response.json()["detail"]


def test_lot07g_export_rejects_longitudinal_structure_outside_lot07(db, dentiste):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id)
    request = _request(
        traced_structures=[
            {
                "structure_id": "t1-ghost",
                "structure_class": "LONGITUDINAL_GHOST",
                "authority_state": "DERIVED_VISUALIZATION",
                "coordinate_space": "REGISTERED_LONGITUDINAL",
                "version": "1",
                "source_record_id": "session:t1",
                "created_at": NOW.isoformat(),
                "updated_at": NOW.isoformat(),
                "provenance": {"source": "client-presentation"},
                "edit_history": [],
            }
        ]
    )
    with pytest.raises(OrthoWorkbenchExportError, match="outside LOT07"):
        build_ortho_workbench_export(
            db,
            analysis=analysis,
            employer_id=dentiste.id,
            request=request,
            exported_at=EXPORT_AT,
        )


def test_lot07g_export_rejects_calibrated_display_coordinates_without_calibration(db, dentiste):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id)
    request = _request(
        traced_structures=[
            {
                "structure_id": "soft-tissue-mm",
                "structure_class": "SOFT_TISSUE_PROFILE",
                "authority_state": "DISPLAY_TEMPLATE_ONLY",
                "coordinate_space": "CALIBRATED_MM",
                "version": "1",
                "source_record_id": "session:soft",
                "created_at": NOW.isoformat(),
                "updated_at": NOW.isoformat(),
                "provenance": {"source": "client-presentation"},
                "edit_history": [],
            }
        ]
    )
    with pytest.raises(OrthoWorkbenchExportError, match="require current calibration"):
        build_ortho_workbench_export(
            db,
            analysis=analysis,
            employer_id=dentiste.id,
            request=request,
            exported_at=EXPORT_AT,
        )


def test_lot07g_export_server_binds_display_structure_to_case_and_timepoint(db, dentiste):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id)
    request = _request(
        traced_structures=[
            {
                "structure_id": "soft_tissue_profile",
                "structure_class": "SOFT_TISSUE_PROFILE",
                "authority_state": "DISPLAY_TEMPLATE_ONLY",
                "coordinate_space": "IMAGE_PIXEL",
                "version": "1",
                "source_record_id": "client-session:soft",
                "created_at": NOW.isoformat(),
                "updated_at": NOW.isoformat(),
                "provenance": {"source": "client-presentation"},
                "edit_history": [],
            }
        ]
    )
    exported = build_ortho_workbench_export(
        db,
        analysis=analysis,
        employer_id=dentiste.id,
        request=request,
        exported_at=EXPORT_AT,
    )
    binding = exported["traced_structures"]["items"][0]["server_binding"]
    assert binding == {
        "patient_id": patient.id,
        "analysis_id": analysis.id,
        "case_id": CASE_ID,
        "timepoint_id": "T0",
        "persistence_state": "SESSION_PRESENTATION_ONLY",
    }


def test_lot07g_export_rejects_duplicate_structure_ids(db, dentiste):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id)
    structure = {
        "structure_id": "soft_tissue_profile",
        "structure_class": "SOFT_TISSUE_PROFILE",
        "authority_state": "DISPLAY_TEMPLATE_ONLY",
        "coordinate_space": "IMAGE_PIXEL",
        "version": "1",
        "source_record_id": "client-session:soft",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
        "provenance": {"source": "client-presentation"},
        "edit_history": [],
    }
    with pytest.raises(OrthoWorkbenchExportError, match="duplicate traced structure"):
        build_ortho_workbench_export(
            db,
            analysis=analysis,
            employer_id=dentiste.id,
            request=_request(traced_structures=[structure, structure]),
            exported_at=EXPORT_AT,
        )


def test_lot07g_route_preserves_tenant_isolation(client, db, dentiste, auth_headers):
    other = models.User(
        email="lot07g-other@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Other LOT07G",
        is_active=True,
        is_licensed=True,
    )
    db.add(other)
    db.commit()
    db.refresh(other)
    patient = _patient(db, other.id)
    analysis = _analysis(db, patient.id)
    response = client.post(
        f"/api/ia/analyses/{analysis.id}/ortho-workbench-export",
        headers=auth_headers,
        json=_request().model_dump(mode="json"),
    )
    assert response.status_code in {403, 404}


def test_lot07g_export_rejects_tampered_persisted_correction_history(db, dentiste):
    patient = _patient(db, dentiste.id)
    analysis = _analysis(db, patient.id)
    previous = analysis.angles_data[EVIDENCE_GRAPH_KEY]
    edited = [dict(item) for item in analysis.landmarks_data]
    target = next(item for item in edited if item["id"] == "A")
    target["x"] += 2.0
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(edited))
    revised = rebuild_evidence_after_landmark_edit(
        previous_payload=previous,
        patient_id=patient.id,
        image_record_id="radio-lot07g.jpg",
        result=result,
        runtime_landmarks=edited,
        clinician_id=str(dentiste.id),
        validated_at=LATER,
    )
    manual = next(
        item for item in revised["landmarks"] if item.get("origin") == "MANUAL_CORRECTED"
    )
    forged = dict(manual)
    forged["validated_by"] = None
    revised["history"].append(
        {
            "revision": 999,
            "landmarks": [forged],
            "sources": [],
            "constructions": [],
            "measurements": [],
        }
    )
    analysis.angles_data = {**result.model_dump(), EVIDENCE_GRAPH_KEY: revised}
    db.commit()
    db.refresh(analysis)

    with pytest.raises(OrthoWorkbenchExportError, match="invalid landmark evidence"):
        build_ortho_workbench_export(
            db,
            analysis=analysis,
            employer_id=dentiste.id,
            request=_request(),
            exported_at=EXPORT_AT,
        )


def test_lot07g_request_rejects_unstructured_session_audit_event():
    with pytest.raises(ValueError):
        _request(
            session_edit_audit=[
                {
                    "sequence": 1,
                    "action": "EDIT",
                    "transactionId": "landmark-edit-1",
                    "changedLandmarkIds": ["A"],
                    "scientificAuthority": "CLIENT_FORGED",
                }
            ]
        )
