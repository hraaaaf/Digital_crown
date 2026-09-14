"""R17 authoritative PDF projection contracts."""
from backend.services import cephalo_pdf_projection as projection
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def _studio(
    *,
    blockers=None,
    stages=None,
    active=True,
    clinical_validation_available=False,
    clinical_validation_reason="R14 authority unavailable",
):
    return {
        "active_runtime_chain_verified": active,
        "evidence_graph_present": active,
        "blocking_gates": list(blockers or []),
        "stages": list(stages or []),
        "clinical_validation_available": clinical_validation_available,
        "clinical_validation_reason": clinical_validation_reason,
    }


def _allow_runtime_read(monkeypatch):
    monkeypatch.setattr(
        projection,
        "project_runtime_chain_read_path",
        lambda payload, patient_id: {"scientific_read_path": {"active_chain": "VERIFIED"}},
    )


def _allow_empty_typed_chain(monkeypatch):
    _allow_runtime_read(monkeypatch)
    monkeypatch.setattr(projection, "deserialize_evidence_snapshot", lambda payload: object())
    monkeypatch.setattr(
        projection,
        "validate_active_runtime_chain",
        lambda payload, graph: type("Chain", (), {"measurements": {}})(),
    )


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
    assert result["active_runtime_chain_verified"] is False
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
    _allow_runtime_read(monkeypatch)
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

    assert result["active_runtime_chain_verified"] is True
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
    _allow_runtime_read(monkeypatch)
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


def test_pdf_projection_never_exposes_values_when_authoritative_runtime_read_fails(monkeypatch):
    monkeypatch.setattr(
        projection,
        "build_r15_clinical_studio_snapshot",
        lambda **kwargs: _studio(blockers=["active_runtime_chain_incoherent"], active=True),
    )

    def reject_runtime_read(payload, patient_id):
        raise ValueError("case integrity mismatch")

    monkeypatch.setattr(projection, "project_runtime_chain_read_path", reject_runtime_read)
    monkeypatch.setattr(
        projection,
        "validate_active_runtime_chain",
        lambda payload, graph: (_ for _ in ()).throw(AssertionError("must not expose chain after failed read")),
    )

    result = projection.build_cephalo_pdf_projection(
        patient_id=999,
        analysis_id=9,
        angles_data={EVIDENCE_GRAPH_KEY: {"contract": "typed"}},
    )

    assert result["measurements"] == []
    assert result["active_runtime_chain_verified"] is False
    assert "typed_measurement_projection_incoherent" in result["blocking_gates"]
    assert result["document_state"] == "INCOMPLETE"


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
    assert projected["presentation_state"] == "BLOCKED"
    assert projected["missing_data_refs"] == ["e1"]
    assert projected["contradictions"] == ["upstream contradiction"]
    assert projected["contraindications"] == ["c1"]
    assert projected["provenance"] == [{"label": "source", "value": "S1"}]
    assert "DROPPED" not in str(projected)


def test_pdf_projection_preserves_r13_evaluable_without_promoting_selection(monkeypatch):
    stage = {
        "stage_id": "R13",
        "title": "Options thérapeutiques",
        "presentation_state": "EVALUABLE",
        "authoritative_status": "EVALUABLE",
        "summary": "Évaluable n'est jamais une prescription.",
        "blocking_gates": [],
        "missing_data_refs": [],
        "contradictions": [],
        "contraindications": [],
        "provenance": [{"label": "source", "value": "R13_AUTHORITY"}],
        "clinician_action": {"available": True, "selected": False},
    }
    _allow_empty_typed_chain(monkeypatch)
    monkeypatch.setattr(
        projection,
        "build_r15_clinical_studio_snapshot",
        lambda **kwargs: _studio(stages=[stage], blockers=[], active=True),
    )

    result = projection.build_cephalo_pdf_projection(
        patient_id=7,
        analysis_id=9,
        angles_data={EVIDENCE_GRAPH_KEY: {"contract": "typed"}},
    )

    projected = result["stages"][0]
    assert projected["presentation_state"] == "EVALUABLE"
    assert projected["authoritative_status"] == "EVALUABLE"
    assert projected["clinician_action"] == {"available": True, "selected": False}
    assert "DROPPED" not in str(projected)
    assert result["document_state"] == "INCOMPLETE"


def test_pdf_projection_current_r14_awaiting_authority_stays_incomplete(monkeypatch):
    stage = {
        "stage_id": "R14",
        "title": "Validation clinique finale",
        "presentation_state": "AWAITING_CLINICIAN",
        "authoritative_status": "AWAITING_CLINICIAN",
        "summary": "Validation praticien requise.",
        "blocking_gates": ["r14_authoritative_snapshot_not_persisted"],
        "missing_data_refs": [],
        "contradictions": [],
        "contraindications": [],
        "provenance": [{"label": "authority", "value": "R14 snapshot absent"}],
        "clinician_action": {"available": False},
    }
    _allow_empty_typed_chain(monkeypatch)
    monkeypatch.setattr(
        projection,
        "build_r15_clinical_studio_snapshot",
        lambda **kwargs: _studio(
            stages=[stage],
            blockers=["r14_authoritative_snapshot_not_persisted"],
            active=True,
            clinical_validation_available=False,
            clinical_validation_reason="Final clinical validation has no persisted authoritative R14 snapshot yet.",
        ),
    )

    result = projection.build_cephalo_pdf_projection(
        patient_id=7,
        analysis_id=9,
        angles_data={EVIDENCE_GRAPH_KEY: {"contract": "typed"}},
    )

    assert result["active_runtime_chain_verified"] is True
    assert result["clinical_validation_available"] is False
    assert result["document_state"] == "INCOMPLETE"
    assert result["stages"][0]["presentation_state"] == "AWAITING_CLINICIAN"
    assert "r14_authoritative_snapshot_not_persisted" in result["blocking_gates"]


def test_pdf_projection_complete_gate_requires_validation_and_zero_blockers(monkeypatch):
    _allow_empty_typed_chain(monkeypatch)
    monkeypatch.setattr(
        projection,
        "build_r15_clinical_studio_snapshot",
        lambda **kwargs: _studio(
            stages=[],
            blockers=[],
            active=True,
            clinical_validation_available=True,
            clinical_validation_reason="authoritative validation resolved",
        ),
    )

    result = projection.build_cephalo_pdf_projection(
        patient_id=7,
        analysis_id=9,
        angles_data={EVIDENCE_GRAPH_KEY: {"contract": "typed"}},
    )

    assert result["active_runtime_chain_verified"] is True
    assert result["clinical_validation_available"] is True
    assert result["blocking_gates"] == []
    assert result["document_state"] == "COMPLETE"
