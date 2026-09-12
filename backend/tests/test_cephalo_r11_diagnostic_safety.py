"""R11 diagnostic-safety golden tests.

These tests verify fail-closed graph behavior only. They do not activate a
clinical classification, diagnosis, or treatment rule.
"""

from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    DiagnosticHypothesisEvidence,
    EvidenceStatus,
    FindingEvidence,
    LandmarkEvidence,
    LandmarkOrigin,
    MeasurementEvidence,
    NormativeEvaluationEvidence,
    ReviewState,
    SourceEvidence,
)
from backend.services.cephalo_diagnostic_rule_registry import (
    DiagnosticRuleDefinition,
    DiagnosticRuleRegistry,
    FindingRuleDefinition,
)
from backend.services.cephalo_evidence_graph import (
    EvidenceGraphSnapshot,
    EvidenceGraphValidationError,
)
from backend.services.cephalo_r11_diagnostic_safety import validate_r11_diagnostic_graph


NOW = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)


def _rule_registry() -> DiagnosticRuleRegistry:
    registry = DiagnosticRuleRegistry()
    registry.register_finding_rule(
        FindingRuleDefinition(
            rule_id="R11_SYNTHETIC_TEST_ONLY",
            version="1",
            domain="dentoalveolar",
            source_ids=("CRANIOM_PART2_2011",),
            description="Synthetic non-clinical finding rule used only for R11 safety tests.",
            requires_active_normative_reference=False,
        )
    )
    registry.register_diagnostic_rule(
        DiagnosticRuleDefinition(
            rule_id="R11_SYNTHETIC_DIAGNOSIS_TEST_ONLY",
            version="1",
            domain="synthetic",
            source_ids=("CRANIOM_PART2_2011",),
            finding_rule_bindings=(("R11_SYNTHETIC_TEST_ONLY", "1"),),
            description="Synthetic non-clinical diagnostic rule used only for R11 safety tests.",
        )
    )
    return registry


def _source() -> SourceEvidence:
    return SourceEvidence(
        evidence_id="source:ceph:r11",
        patient_id=1,
        kind="lateral_ceph",
        source_record_id="record:r11",
        recorded_at=NOW,
        operator_id="clinician:1",
    )


def _landmark(name: str, x: float, y: float) -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"landmark:{name}",
        landmark_id=name,
        x=x,
        y=y,
        source_image_ref="source:ceph:r11",
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["source:ceph:r11"],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _craniom_graph(*, include_finding: bool = False) -> EvidenceGraphSnapshot:
    source = _source()
    po = _landmark("Po", 10.0, 20.0)
    orbitale = _landmark("Or", 30.0, 20.0)
    construction = ConstructionEvidence(
        construction_id="construction:FH_PO_OR_V1",
        definition_id="FH_PO_OR_V1",
        definition_version="1",
        landmark_refs=[po.evidence_id, orbitale.evidence_id],
        geometry={"kind": "axis", "start": "Po", "end": "Or"},
        evidence_refs=[po.evidence_id, orbitale.evidence_id],
    )
    measurement = MeasurementEvidence(
        measurement_id="measurement:U1_FH:r11",
        analysis_id="CRANIOM",
        method_id="U1_TO_FRANKFORT_ANGLE",
        method_version="2010-2011",
        value=112.0,
        unit="deg",
        construction_refs=[construction.construction_id],
        evidence_refs=[construction.construction_id],
    )
    evaluation = NormativeEvaluationEvidence(
        evaluation_id="evaluation:U1_FH:r11",
        measurement_ref=measurement.measurement_id,
        norm_profile_id="CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1",
        norm_profile_version="2010-2011",
        context={"mode": "r11_traceability_only"},
        reference={"kind": "EXTREME_RANGE", "lower": 97.5, "upper": 130.1},
        source_refs=["CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"],
        evidence_refs=[measurement.measurement_id],
    )
    findings = []
    if include_finding:
        findings = [
            _finding(
                "finding:unsafe_norm:r11",
                supporting=[evaluation.evaluation_id],
            )
        ]
    return EvidenceGraphSnapshot(
        sources=[source],
        landmarks=[po, orbitale],
        constructions=[construction],
        measurements=[measurement],
        normative_evaluations=[evaluation],
        findings=findings,
    )


def _mcnamara_graph() -> EvidenceGraphSnapshot:
    source = _source()
    co = _landmark("Co", 5.0, 5.0)
    gn = _landmark("Gn", 50.0, 70.0)
    construction = ConstructionEvidence(
        construction_id="construction:MCNAMARA_CO_GN_V1",
        definition_id="MCNAMARA_CO_GN_V1",
        definition_version="1",
        landmark_refs=[co.evidence_id, gn.evidence_id],
        geometry={"kind": "distance", "start": "Co", "end": "Gn"},
        evidence_refs=[co.evidence_id, gn.evidence_id],
    )
    measurement = MeasurementEvidence(
        measurement_id="measurement:MCNAMARA_CO_GN:r11",
        analysis_id="MCNAMARA",
        method_id="MCNAMARA_CO_GN_MM_V1",
        method_version="1",
        value=120.2,
        unit="mm",
        construction_refs=[construction.construction_id],
        evidence_refs=[construction.construction_id],
    )
    evaluation = NormativeEvaluationEvidence(
        evaluation_id="evaluation:MCNAMARA_CO_GN:r11",
        measurement_ref=measurement.measurement_id,
        norm_profile_id="MCNAMARA_CO_GN_ANN_ARBOR_FEMALE_MEAN_SD_V1",
        norm_profile_version="1",
        context={"mode": "r11_traceability_only", "scale": "blocked_8_percent"},
        reference={"kind": "MEAN_SD", "mean": 120.2, "sd": 5.3},
        source_refs=["MCNAMARA_1984"],
        evidence_refs=[measurement.measurement_id],
    )
    return EvidenceGraphSnapshot(
        sources=[source],
        landmarks=[co, gn],
        constructions=[construction],
        measurements=[measurement],
        normative_evaluations=[evaluation],
    )


def _replace(graph: EvidenceGraphSnapshot, **changes) -> EvidenceGraphSnapshot:
    return EvidenceGraphSnapshot(**{**graph.__dict__, **changes})


def _finding(
    finding_id: str,
    *,
    supporting=None,
    opposing=None,
    missing=None,
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE,
) -> FindingEvidence:
    return FindingEvidence(
        finding_id=finding_id,
        domain="dentoalveolar",
        rule_id="R11_SYNTHETIC_TEST_ONLY",
        rule_version="1",
        supporting_evidence_refs=list(supporting or []),
        opposing_evidence_refs=list(opposing or []),
        missing_evidence_refs=list(missing or []),
        statement="Synthetic R11 safety-test finding.",
        availability_status=availability_status,
    )


def _diagnosis(
    diagnosis_id: str,
    *,
    supporting=None,
    opposing=None,
    missing=None,
    contradictions=None,
    state: ReviewState = ReviewState.PROPOSED,
) -> DiagnosticHypothesisEvidence:
    return DiagnosticHypothesisEvidence(
        diagnosis_id=diagnosis_id,
        domain="synthetic",
        rule_id="R11_SYNTHETIC_DIAGNOSIS_TEST_ONLY",
        rule_version="1",
        supporting_finding_refs=list(supporting or []),
        opposing_finding_refs=list(opposing or []),
        missing_data_refs=list(missing or []),
        contradictions=list(contradictions or []),
        statement="Synthetic R11 safety-test hypothesis.",
        state=state,
    )


def _unavailable_measurement(graph: EvidenceGraphSnapshot) -> MeasurementEvidence:
    return graph.measurements[0].model_copy(
        update={"value": None, "availability_status": AvailabilityStatus.NOT_COMPUTABLE}
    )


def test_r11_accepts_exact_inert_extreme_range_for_traceability_only():
    validate_r11_diagnostic_graph(_craniom_graph())


def test_r11_requires_exact_registered_normative_sources():
    graph = _craniom_graph()
    evaluation = graph.normative_evaluations[0].model_copy(
        update={"source_refs": ["CRANIOM_PART2_2011"]}
    )
    with pytest.raises(EvidenceGraphValidationError, match="source_refs must exactly match"):
        validate_r11_diagnostic_graph(_replace(graph, normative_evaluations=[evaluation]))


def test_r11_requires_exact_construction_gate_for_normative_reference():
    graph = _craniom_graph()
    construction = graph.constructions[0].model_copy(
        update={"definition_id": "SYNTHETIC_WRONG_CONSTRUCTION"}
    )
    with pytest.raises(EvidenceGraphValidationError, match="requires construction gate"):
        validate_r11_diagnostic_graph(_replace(graph, constructions=[construction]))


def test_r11_accepts_exact_mean_sd_payload_as_inert_traceability():
    validate_r11_diagnostic_graph(_mcnamara_graph())


def test_r11_rejects_mean_sd_payload_drift():
    graph = _mcnamara_graph()
    evaluation = graph.normative_evaluations[0].model_copy(
        update={"reference": {"kind": "MEAN_SD", "mean": 120.2, "sd": 5.4}}
    )
    with pytest.raises(EvidenceGraphValidationError, match="does not exactly match registry"):
        validate_r11_diagnostic_graph(_replace(graph, normative_evaluations=[evaluation]))


def test_r11_rejects_extra_fields_in_normative_payload():
    graph = _mcnamara_graph()
    evaluation = graph.normative_evaluations[0].model_copy(
        update={
            "reference": {
                "kind": "MEAN_SD",
                "mean": 120.2,
                "sd": 5.3,
                "lower": 0.0,
            }
        }
    )
    with pytest.raises(
        EvidenceGraphValidationError,
        match=r"reference payload does not (exactly )?match registry",
    ):
        validate_r11_diagnostic_graph(_replace(graph, normative_evaluations=[evaluation]))


def test_r11_production_registry_rejects_unregistered_finding_rule():
    graph = _craniom_graph()
    finding = _finding(
        "finding:unregistered:r11",
        supporting=[graph.measurements[0].measurement_id],
    )
    with pytest.raises(EvidenceGraphValidationError, match="unregistered rule"):
        validate_r11_diagnostic_graph(_replace(graph, findings=[finding]))


def test_r11_inactive_normative_reference_cannot_support_finding():
    with pytest.raises(EvidenceGraphValidationError, match="inactive normative"):
        validate_r11_diagnostic_graph(
            _craniom_graph(include_finding=True), rule_registry=_rule_registry()
        )


def test_r11_inactive_normative_reference_may_be_exposed_as_missing_context():
    graph = _craniom_graph()
    finding = _finding(
        "finding:blocked_norm:r11",
        supporting=[graph.measurements[0].measurement_id],
        missing=[graph.normative_evaluations[0].evaluation_id],
    )
    validate_r11_diagnostic_graph(
        _replace(graph, findings=[finding]), rule_registry=_rule_registry()
    )


def test_r11_available_normative_evaluation_rejects_unavailable_measurement():
    graph = _craniom_graph()
    measurement = _unavailable_measurement(graph)
    with pytest.raises(EvidenceGraphValidationError, match="cannot be AVAILABLE"):
        validate_r11_diagnostic_graph(_replace(graph, measurements=[measurement]))


def test_r11_finding_rejects_unavailable_measurement_as_support():
    graph = _craniom_graph()
    measurement = _unavailable_measurement(graph)
    finding = _finding(
        "finding:unavailable_support:r11",
        supporting=[measurement.measurement_id],
    )
    with pytest.raises(EvidenceGraphValidationError, match="unavailable evidence"):
        validate_r11_diagnostic_graph(
            _replace(
                graph,
                measurements=[measurement],
                normative_evaluations=[],
                findings=[finding],
            ),
            rule_registry=_rule_registry(),
        )


def test_r11_finding_rejects_unavailable_measurement_as_opposition():
    graph = _craniom_graph()
    measurement = _unavailable_measurement(graph)
    finding = _finding(
        "finding:unavailable_opposition:r11",
        supporting=[graph.sources[0].evidence_id],
        opposing=[measurement.measurement_id],
    )
    with pytest.raises(EvidenceGraphValidationError, match="unavailable evidence"):
        validate_r11_diagnostic_graph(
            _replace(
                graph,
                measurements=[measurement],
                normative_evaluations=[],
                findings=[finding],
            ),
            rule_registry=_rule_registry(),
        )


def test_r11_finding_rejects_available_evidence_marked_missing():
    graph = _craniom_graph()
    finding = _finding(
        "finding:false_missing:r11",
        supporting=[graph.sources[0].evidence_id],
        missing=[graph.measurements[0].measurement_id],
    )
    with pytest.raises(EvidenceGraphValidationError, match="available evidence as missing"):
        validate_r11_diagnostic_graph(
            _replace(graph, normative_evaluations=[], findings=[finding]),
            rule_registry=_rule_registry(),
        )


def test_r11_finding_rejects_same_evidence_as_supporting_and_opposing():
    graph = _craniom_graph()
    measurement_id = graph.measurements[0].measurement_id
    finding = _finding(
        "finding:contradictory:r11",
        supporting=[measurement_id],
        opposing=[measurement_id],
    )
    with pytest.raises(EvidenceGraphValidationError, match="both supporting and opposing"):
        validate_r11_diagnostic_graph(
            _replace(graph, findings=[finding]), rule_registry=_rule_registry()
        )


def test_r11_diagnosis_requires_versioned_registered_rule():
    graph = _craniom_graph()
    finding = _finding(
        "finding:neutral:r11",
        supporting=[graph.measurements[0].measurement_id],
    )
    diagnosis = DiagnosticHypothesisEvidence(
        diagnosis_id="diagnosis:unbound:r11",
        domain="synthetic",
        supporting_finding_refs=[finding.finding_id],
        statement="Synthetic unbound R11 diagnosis safety test only.",
    )
    with pytest.raises(EvidenceGraphValidationError, match="requires a versioned rule binding"):
        validate_r11_diagnostic_graph(
            _replace(graph, findings=[finding], diagnoses=[diagnosis]),
            rule_registry=_rule_registry(),
        )


def test_r11_diagnosis_rejects_unavailable_finding_as_support():
    graph = _craniom_graph()
    unavailable = _finding(
        "finding:missing:r11",
        missing=[graph.measurements[0].measurement_id],
        availability_status=AvailabilityStatus.NOT_COMPUTABLE,
    )
    diagnosis = _diagnosis(
        "diagnosis:unsafe_missing_support:r11",
        supporting=[unavailable.finding_id],
    )
    with pytest.raises(EvidenceGraphValidationError, match="unavailable finding"):
        validate_r11_diagnostic_graph(
            _replace(graph, findings=[unavailable], diagnoses=[diagnosis]),
            rule_registry=_rule_registry(),
        )


def test_r11_diagnosis_rejects_unavailable_finding_as_opposition():
    graph = _craniom_graph()
    available = _finding(
        "finding:available:r11",
        supporting=[graph.measurements[0].measurement_id],
    )
    unavailable = _finding(
        "finding:missing:r11",
        missing=[graph.measurements[0].measurement_id],
        availability_status=AvailabilityStatus.NOT_COMPUTABLE,
    )
    diagnosis = _diagnosis(
        "diagnosis:unsafe_missing_opposition:r11",
        supporting=[available.finding_id],
        opposing=[unavailable.finding_id],
    )
    with pytest.raises(EvidenceGraphValidationError, match="unavailable finding"):
        validate_r11_diagnostic_graph(
            _replace(graph, findings=[available, unavailable], diagnoses=[diagnosis]),
            rule_registry=_rule_registry(),
        )


def test_r11_distinct_supporting_and_opposing_findings_preserve_contradiction():
    graph = _craniom_graph()
    supporting = _finding(
        "finding:support:r11",
        supporting=[graph.measurements[0].measurement_id],
    )
    opposing = _finding(
        "finding:oppose:r11",
        supporting=[graph.sources[0].evidence_id],
    )
    diagnosis = _diagnosis(
        "diagnosis:contradiction_visible:r11",
        supporting=[supporting.finding_id],
        opposing=[opposing.finding_id],
        contradictions=["Synthetic contradiction retained explicitly."],
    )
    validate_r11_diagnostic_graph(
        _replace(graph, findings=[supporting, opposing], diagnoses=[diagnosis]),
        rule_registry=_rule_registry(),
    )
    assert diagnosis.contradictions == ["Synthetic contradiction retained explicitly."]


def test_r11_insufficient_data_hypothesis_keeps_missing_evidence_explicit():
    graph = _craniom_graph()
    measurement = _unavailable_measurement(graph)
    diagnosis = _diagnosis(
        "diagnosis:insufficient:r11",
        missing=[measurement.measurement_id],
        state=ReviewState.INSUFFICIENT_DATA,
    )
    validate_r11_diagnostic_graph(
        _replace(
            graph,
            measurements=[measurement],
            normative_evaluations=[],
            diagnoses=[diagnosis],
        ),
        rule_registry=_rule_registry(),
    )
    assert diagnosis.missing_data_refs == [measurement.measurement_id]


def test_r11_insufficient_data_hypothesis_rejects_available_measurement_as_missing():
    graph = _craniom_graph()
    diagnosis = _diagnosis(
        "diagnosis:false_missing:r11",
        missing=[graph.measurements[0].measurement_id],
        state=ReviewState.INSUFFICIENT_DATA,
    )
    with pytest.raises(EvidenceGraphValidationError, match="available evidence as missing"):
        validate_r11_diagnostic_graph(
            _replace(graph, normative_evaluations=[], diagnoses=[diagnosis]),
            rule_registry=_rule_registry(),
        )


def test_r11_diagnosis_rejects_same_finding_as_supporting_and_opposing():
    graph = _craniom_graph()
    finding = _finding(
        "finding:neutral:r11",
        supporting=[graph.measurements[0].measurement_id],
    )
    diagnosis = _diagnosis(
        "diagnosis:contradictory:r11",
        supporting=[finding.finding_id],
        opposing=[finding.finding_id],
    )
    with pytest.raises(EvidenceGraphValidationError, match="same finding as both"):
        validate_r11_diagnostic_graph(
            _replace(graph, findings=[finding], diagnoses=[diagnosis]),
            rule_registry=_rule_registry(),
        )
