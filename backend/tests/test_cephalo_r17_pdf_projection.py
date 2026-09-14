"""R17 authoritative PDF projection contracts."""
from backend.services import cephalo_pdf_projection as projection
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def _studio(*, blockers=None, stages=None, active=True):
    return {
        "active_runtime_chain_verified": active,
        "evidence_graph_present": active,
        "blocking_gates": list(blockers or []),
        "stages": list(stages or []),
        "clinical_validation_available": False,
        "clinical_validation_reason": "R14 authority unavailable",
    }


def test_pdf_projection_is_explicitly_incomplete_without_typed_graph(monkeypatch):
    monkeypatch.setattr(
        projection,
        "build_r15_clinical_studio_snapshot",
        lambda **kwargs: _studio(blockers=["typed_evidence_graph_missing"], active=False),
    )

    result = projection.build_cephalo_pdf_projection(
        patient_id=7,
        analysis_id=9,
        angles_data={"ai_diagnostic": {"strategie_therapeutique": "Damon"}},
    )

    assert result["document_state"] == "INCOMPLETE"
    assert result["measurements"] == []
    assert "typed_evidence_graph_missing" in result["blocking_gates"]
    assert "Damon" not in str(result)


def test_pdf_projection_ignores_legacy_clinical_narrative(monkeypatch):
    fake_measurement = type(
        "Measurement",
        (),
        {
            "measurement_id": "measurement:test:SNA",
            "analysis_id": "analysis:test",
            "method_id": "method:test",
            "method_version": "1",
            "value": 81.5,
            "unit": "deg",
            "availability_status": type("Status", (), {"value": "AVAILABLE"})(),
            "requires_calibration": False,
            "calibration_ref": None,
            "landmark_refs": ["landmark:N", "landmark:S"],
            "construction_refs": [],
            "evidence_refs": ["landmark:N", "landmark:S"],
        },
    )()
    fake_chain = type("Chain", (), {"measurements": {"SNA": fake_measurement}})()
    monkeypatch.setattr(projection, "deserialize_evidence_snapshot", lambda payload: object())
    monkeypatch.setattr(projection, "validate_active_runtime_chain", lambda payload, graph: fake_chain)
    monkeypatch.setattr(
        projection,
        "build_r15_clinical_studio_snapshot",
        lambda **kwargs: _studio(
            stages=[{
                "stage_id": "R13",
                "title": "Options thérapeutiques",
                "presentation_state": "BLOCKED",
                "authoritative_status": None,
                "summary": "Évaluable n'est jamais une prescription.",
                "blocking_gates": ["r13_authoritative_snapshot_not_persisted"],
                "missing_data_refs": [],
                "contradictions": [],
                "contraindications": [],
                "provenance": [],
                "clinician_action": {"available": False},
            }],
            blockers=["r13_authoritative_snapshot_not_persisted"],
        ),
    )

    result = projection.build_cephalo_pdf_projection(
        patient_id=7,
        analysis_id=9,
        angles_data={
            EVIDENCE_GRAPH_KEY: {"contract": "typed"},
            "ai_diagnostic": {
                "synthese_diagnostique": "CLIENT_INJECTION",
                "strategie_therapeutique": "Damon CLIENT_INJECTION",
            },
            "clinical_data": {"plan_traitement": "CLIENT_PLAN"},
        },
    )

    assert result["measurements"][0]["availability_status"] == "AVAILABLE"
    assert result["measurements"][0]["value"] == 81.5
    assert result["stages"][0]["presentation_state"] == "BLOCKED"
    serialized = str(result)
    assert "CLIENT_INJECTION" not in serialized
    assert "CLIENT_PLAN" not in serialized
    assert "Damon" not in serialized


def test_pdf_projection_preserves_not_computable_measurement(monkeypatch):
    fake_measurement = type(
        "Measurement",
        (),
        {
            "measurement_id": "measurement:test:Situation_A",
            "analysis_id": "analysis:test",
            "method_id": "method:test",
            "method_version": "1",
            "value": None,
            "unit": "mm",
            "availability_status": type("Status", (), {"value": "NOT_COMPUTABLE"})(),
            "requires_calibration": True,
            "calibration_ref": None,
            "landmark_refs": ["landmark:A"],
            "construction_refs": ["construction:nasion_vertical"],
            "evidence_refs": ["landmark:A", "construction:nasion_vertical"],
        },
    )()
    fake_chain = type("Chain", (), {"measurements": {"Situation_A": fake_measurement}})()
    monkeypatch.setattr(projection, "deserialize_evidence_snapshot", lambda payload: object())
    monkeypatch.setattr(projection, "validate_active_runtime_chain", lambda payload, graph: fake_chain)
    monkeypatch.setattr(
        projection,
        "build_r15_clinical_studio_snapshot",
        lambda **kwargs: _studio(blockers=["r11_authoritative_snapshot_not_persisted"]),
    )

    result = projection.build_cephalo_pdf_projection(
        patient_id=7,
        analysis_id=9,
        angles_data={EVIDENCE_GRAPH_KEY: {"contract": "typed"}},
    )

    measurement = result["measurements"][0]
    assert measurement["availability_status"] == "NOT_COMPUTABLE"
    assert measurement["value"] is None
    assert measurement["requires_calibration"] is True


def test_pdf_projection_preserves_stage_blockers_missing_contradictions_and_contraindications(monkeypatch):
    stage = {
        "stage_id": "R13",
        "title": "Options thérapeutiques",
        "presentation_state": "BLOCKED",
        "authoritative_status": "BLOCKED",
        "summary": "Blocage explicite",
        "blocking_gates": ["missing:e1", "contraindication:c1"],
        "missing_data_refs": ["e1"],
        "contradictions": ["upstream contradiction"],
        "contraindications": ["c1"],
        "provenance": [{"label": "source", "value": "S1"}],
        "clinician_action": {"available": False},
    }
    monkeypatch.setattr(
        projection,
        "build_r15_clinical_studio_snapshot",
        lambda **kwargs: _studio(stages=[stage], blockers=stage["blocking_gates"], active=False),
    )

    result = projection.build_cephalo_pdf_projection(
        patient_id=7,
        analysis_id=9,
        angles_data={},
    )

    projected = result["stages"][0]
    assert projected["missing_data_refs"] == ["e1"]
    assert projected["contradictions"] == ["upstream contradiction"]
    assert projected["contraindications"] == ["c1"]
    assert projected["provenance"] == [{"label": "source", "value": "S1"}]
