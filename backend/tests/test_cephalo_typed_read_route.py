"""API-boundary proofs for the canonical cephalometric typed read path."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from backend import models
from backend.routers import cephalo_analysis_read, ia
from backend.routers.cephalo_analysis_read import get_analysis_with_typed_read_path
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.tests.test_cephalo_typed_read import _angles_with_graph

NOW = datetime(2026, 9, 10, 20, 0, tzinfo=timezone.utc)


class _Query:
    def __init__(self, analysis):
        self.analysis = analysis

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.analysis


class _DB:
    def __init__(self, analysis):
        self.analysis = analysis

    def query(self, model):
        assert model is models.CephaloAnalysis
        return _Query(self.analysis)


def _analysis(angles_data):
    return SimpleNamespace(
        id=41,
        patient_id=7,
        image_original_path="radio.jpg",
        angles_data=angles_data,
        landmarks_data=[],
        ai_diagnostic=None,
        is_calibrated=True,
        mm_per_pixel=0.2,
        created_at=NOW,
    )


def test_canonical_analysis_get_route_is_unique_and_uses_typed_handler():
    matches = [
        route
        for route in ia.router.routes
        if isinstance(route, APIRoute)
        and route.path == "/analyses/{analysis_id}"
        and "GET" in (route.methods or set())
    ]

    assert len(matches) == 1
    assert matches[0].endpoint is get_analysis_with_typed_read_path


def test_canonical_get_projects_typed_measurement_at_api_boundary(monkeypatch):
    angles, graph = _angles_with_graph(ratio=0.2, calibrated=True)
    typed_value = next(
        item["value"]
        for item in graph["measurements"]
        if item["method_id"] == "CRANIOM_SITUATION_A_MM_V1"
    )
    angles["metrics"]["analyse_osseuse"]["Situation_A"]["valeur"] = 999.0
    monkeypatch.setattr(cephalo_analysis_read, "assert_patient_access", lambda *_args: None)

    out = get_analysis_with_typed_read_path(
        41,
        db=_DB(_analysis(angles)),
        current_user=object(),
    )

    situation_a = out.angles_data["metrics"]["analyse_osseuse"]["Situation_A"]
    assert situation_a["valeur"] == typed_value
    assert situation_a["valeur"] != 999.0
    assert out.angles_data["scientific_read_path"]["authority"] == "EVIDENCE_GRAPH_V1"


def test_canonical_get_returns_409_when_typed_graph_is_incomplete(monkeypatch):
    angles, graph = _angles_with_graph(ratio=0.2, calibrated=True)
    angles[EVIDENCE_GRAPH_KEY] = {
        **graph,
        "measurements": graph["measurements"][:-1],
    }
    monkeypatch.setattr(cephalo_analysis_read, "assert_patient_access", lambda *_args: None)

    with pytest.raises(HTTPException) as caught:
        get_analysis_with_typed_read_path(
            41,
            db=_DB(_analysis(angles)),
            current_user=object(),
        )

    assert caught.value.status_code == 409
    assert "lecture scientifique bloquée" in caught.value.detail
