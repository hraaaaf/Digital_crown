"""Cross-object integrity validation for the cephalometric evidence graph.

Pydantic models validate one object at a time. This module validates that links
between objects actually resolve and that downstream objects cannot silently
reference invented evidence.

No clinical rules, norms, diagnosis or treatment-selection logic lives here.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Dict, Mapping, Sequence, Set, TypeVar

from backend.schemas.cephalo_evidence import (
    ClinicianValidationEvidence,
    ConstructionEvidence,
    DiagnosticHypothesisEvidence,
    FinalPlanEvidence,
    FindingEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
    NormativeEvaluationEvidence,
    ObjectiveEvidence,
    ProblemEvidence,
    ReviewState,
    SourceEvidence,
    TreatmentOptionEvidence,
    TreatmentOptionStatus,
    ValidationAction,
)
from backend.services.cephalo_norm_registry import NormRegistry, registry as default_norm_registry


class EvidenceGraphValidationError(ValueError):
    """Raised when a cross-object evidence link is missing or inconsistent."""


T = TypeVar("T")


def _index_unique(items: Iterable[T], attr: str, label: str) -> Dict[str, T]:
    indexed: Dict[str, T] = {}
    for item in items:
        key = getattr(item, attr)
        if key in indexed:
            raise EvidenceGraphValidationError(f"Duplicate {label} id: {key}")
        indexed[key] = item
    return indexed


def _require_refs(refs: Iterable[str], allowed: Set[str], context: str) -> None:
    missing = sorted({ref for ref in refs if ref not in allowed})
    if missing:
        raise EvidenceGraphValidationError(
            f"{context} references missing object(s): {', '.join(missing)}"
        )


@dataclass(frozen=True)
class EvidenceGraphSnapshot:
    sources: Sequence[SourceEvidence] = ()
    landmarks: Sequence[LandmarkEvidence] = ()
    constructions: Sequence[ConstructionEvidence] = ()
    measurements: Sequence[MeasurementEvidence] = ()
    normative_evaluations: Sequence[NormativeEvaluationEvidence] = ()
    findings: Sequence[FindingEvidence] = ()
    diagnoses: Sequence[DiagnosticHypothesisEvidence] = ()
    problems: Sequence[ProblemEvidence] = ()
    objectives: Sequence[ObjectiveEvidence] = ()
    treatment_options: Sequence[TreatmentOptionEvidence] = ()
    validations: Sequence[ClinicianValidationEvidence] = ()
    final_plans: Sequence[FinalPlanEvidence] = ()


def validate_evidence_graph(
    graph: EvidenceGraphSnapshot,
    *,
    norm_registry: NormRegistry = default_norm_registry,
) -> None:
    """Validate referential and provenance integrity across one graph snapshot."""

    sources = _index_unique(graph.sources, "evidence_id", "source")
    landmarks = _index_unique(graph.landmarks, "evidence_id", "landmark evidence")
    constructions = _index_unique(graph.constructions, "construction_id", "construction")
    measurements = _index_unique(graph.measurements, "measurement_id", "measurement")
    evaluations = _index_unique(
        graph.normative_evaluations, "evaluation_id", "normative evaluation"
    )
    findings = _index_unique(graph.findings, "finding_id", "finding")
    diagnoses = _index_unique(graph.diagnoses, "diagnosis_id", "diagnosis")
    problems = _index_unique(graph.problems, "problem_id", "problem")
    objectives = _index_unique(graph.objectives, "objective_id", "objective")
    options = _index_unique(graph.treatment_options, "option_id", "treatment option")
    validations = _index_unique(graph.validations, "validation_id", "validation")
    plans = _index_unique(graph.final_plans, "plan_id", "final plan")

    namespaces: Mapping[str, Mapping[str, object]] = {
        "source": sources,
        "landmark": landmarks,
        "construction": constructions,
        "measurement": measurements,
        "normative_evaluation": evaluations,
        "finding": findings,
        "diagnosis": diagnoses,
        "problem": problems,
        "objective": objectives,
        "treatment_option": options,
        "validation": validations,
        "final_plan": plans,
    }

    global_ids: Set[str] = set()
    for label, index in namespaces.items():
        overlap = global_ids.intersection(index)
        if overlap:
            raise EvidenceGraphValidationError(
                f"Evidence/object ids must be globally unique; collision in {label}: "
                + ", ".join(sorted(overlap))
            )
        global_ids.update(index)

    source_ids = set(sources)
    landmark_ids = set(landmarks)
    construction_ids = set(constructions)
    measurement_ids = set(measurements)
    evaluation_ids = set(evaluations)
    finding_ids = set(findings)
    diagnosis_ids = set(diagnoses)
    problem_ids = set(problems)
    objective_ids = set(objectives)
    option_ids = set(options)
    validation_ids = set(validations)
    plan_ids = set(plans)

    geometric_upstream = source_ids | landmark_ids | construction_ids
    measurement_upstream = geometric_upstream | measurement_ids
    interpretation_upstream = measurement_upstream | evaluation_ids
    diagnostic_upstream = interpretation_upstream | finding_ids | diagnosis_ids
    planning_upstream = diagnostic_upstream | problem_ids | objective_ids

    for landmark in graph.landmarks:
        _require_refs(
            [landmark.source_image_ref],
            source_ids,
            f"Landmark {landmark.evidence_id} source_image_ref",
        )
        _require_refs(
            landmark.evidence_refs,
            source_ids,
            f"Landmark {landmark.evidence_id} evidence_refs",
        )

    for construction in graph.constructions:
        _require_refs(
            construction.landmark_refs,
            landmark_ids,
            f"Construction {construction.construction_id} landmark_refs",
        )
        _require_refs(
            construction.evidence_refs,
            source_ids | landmark_ids,
            f"Construction {construction.construction_id} evidence_refs",
        )

    for measurement in graph.measurements:
        _require_refs(
            measurement.landmark_refs,
            landmark_ids,
            f"Measurement {measurement.measurement_id} landmark_refs",
        )
        _require_refs(
            measurement.construction_refs,
            construction_ids,
            f"Measurement {measurement.measurement_id} construction_refs",
        )
        _require_refs(
            measurement.evidence_refs,
            geometric_upstream,
            f"Measurement {measurement.measurement_id} evidence_refs",
        )
        if measurement.calibration_ref is not None:
            _require_refs(
                [measurement.calibration_ref],
                source_ids,
                f"Measurement {measurement.measurement_id} calibration_ref",
            )

    norm_source_ids = set(norm_registry.sources)
    norm_reference_ids = set(norm_registry.references)
    for evaluation in graph.normative_evaluations:
        _require_refs(
            [evaluation.measurement_ref],
            measurement_ids,
            f"Normative evaluation {evaluation.evaluation_id} measurement_ref",
        )
        _require_refs(
            [evaluation.norm_profile_id],
            norm_reference_ids,
            f"Normative evaluation {evaluation.evaluation_id} norm_profile_id",
        )
        registered = norm_registry.get_reference(evaluation.norm_profile_id)
        assert registered is not None
        measurement = measurements[evaluation.measurement_ref]

        if evaluation.norm_profile_version != registered.method_version:
            raise EvidenceGraphValidationError(
                f"Normative evaluation {evaluation.evaluation_id} version does not "
                f"match registered reference {evaluation.norm_profile_id}"
            )
        if registered.method_id != measurement.analysis_id:
            raise EvidenceGraphValidationError(
                f"Normative evaluation {evaluation.evaluation_id} method does not "
                f"match measurement analysis {measurement.analysis_id}"
            )
        if registered.measurement_id != measurement.method_id:
            raise EvidenceGraphValidationError(
                f"Normative evaluation {evaluation.evaluation_id} reference targets "
                f"{registered.measurement_id}, not measurement method {measurement.method_id}"
            )
        if registered.unit != measurement.unit:
            raise EvidenceGraphValidationError(
                f"Normative evaluation {evaluation.evaluation_id} unit does not match measurement"
            )

        reference_payload = evaluation.reference
        if (
            reference_payload.get("kind") != registered.kind.value
            or reference_payload.get("lower") != registered.lower
            or reference_payload.get("upper") != registered.upper
        ):
            raise EvidenceGraphValidationError(
                f"Normative evaluation {evaluation.evaluation_id} reference payload "
                f"does not match registry {evaluation.norm_profile_id}"
            )
        if (
            evaluation.classification is not None
            and not registered.active_for_patient_classification
        ):
            raise EvidenceGraphValidationError(
                f"Normative evaluation {evaluation.evaluation_id} cannot classify with "
                f"an inactive reference"
            )

        _require_refs(
            evaluation.source_refs,
            norm_source_ids,
            f"Normative evaluation {evaluation.evaluation_id} source_refs",
        )
        outside_reference = sorted(set(evaluation.source_refs) - set(registered.source_ids))
        if outside_reference:
            raise EvidenceGraphValidationError(
                f"Normative evaluation {evaluation.evaluation_id} cites source(s) not "
                f"registered for {evaluation.norm_profile_id}: {', '.join(outside_reference)}"
            )
        _require_refs(
            evaluation.evidence_refs,
            measurement_upstream,
            f"Normative evaluation {evaluation.evaluation_id} evidence_refs",
        )

    for finding in graph.findings:
        _require_refs(
            finding.supporting_evidence_refs,
            interpretation_upstream,
            f"Finding {finding.finding_id} supporting_evidence_refs",
        )
        _require_refs(
            finding.opposing_evidence_refs,
            interpretation_upstream,
            f"Finding {finding.finding_id} opposing_evidence_refs",
        )
        _require_refs(
            finding.missing_evidence_refs,
            interpretation_upstream,
            f"Finding {finding.finding_id} missing_evidence_refs",
        )

    for diagnosis in graph.diagnoses:
        _require_refs(
            diagnosis.supporting_finding_refs,
            finding_ids,
            f"Diagnosis {diagnosis.diagnosis_id} supporting_finding_refs",
        )
        _require_refs(
            diagnosis.opposing_finding_refs,
            finding_ids,
            f"Diagnosis {diagnosis.diagnosis_id} opposing_finding_refs",
        )
        _require_refs(
            diagnosis.missing_data_refs,
            interpretation_upstream,
            f"Diagnosis {diagnosis.diagnosis_id} missing_data_refs",
        )

    for problem in graph.problems:
        _require_refs(
            problem.diagnosis_refs,
            diagnosis_ids,
            f"Problem {problem.problem_id} diagnosis_refs",
        )
        _require_refs(
            problem.evidence_refs,
            diagnostic_upstream,
            f"Problem {problem.problem_id} evidence_refs",
        )

    for objective in graph.objectives:
        _require_refs(
            objective.problem_refs,
            problem_ids,
            f"Objective {objective.objective_id} problem_refs",
        )

    for option in graph.treatment_options:
        _require_refs(
            option.objective_refs,
            objective_ids,
            f"Treatment option {option.option_id} objective_refs",
        )
        _require_refs(
            option.required_evidence_refs,
            planning_upstream,
            f"Treatment option {option.option_id} required_evidence_refs",
        )

    validation_target_ids: Mapping[str, Set[str]] = {
        "source": source_ids,
        "landmark": landmark_ids,
        "construction": construction_ids,
        "measurement": measurement_ids,
        "normative_evaluation": evaluation_ids,
        "finding": finding_ids,
        "diagnosis": diagnosis_ids,
        "problem": problem_ids,
        "objective": objective_ids,
        "treatment_option": option_ids,
        "final_plan": plan_ids,
    }
    for validation in graph.validations:
        allowed_targets = validation_target_ids.get(validation.target_type)
        if allowed_targets is None:
            raise EvidenceGraphValidationError(
                f"Validation {validation.validation_id} has unknown target_type "
                f"{validation.target_type}"
            )
        _require_refs(
            [validation.target_id],
            allowed_targets,
            f"Validation {validation.validation_id} target_id",
        )

    for plan in graph.final_plans:
        _require_refs(
            [plan.selected_option_ref],
            option_ids,
            f"Final plan {plan.plan_id} selected_option_ref",
        )
        selected_option = options[plan.selected_option_ref]
        if selected_option.status != TreatmentOptionStatus.CLINICIAN_SELECTED:
            raise EvidenceGraphValidationError(
                f"Final plan {plan.plan_id} requires a CLINICIAN_SELECTED option"
            )
        if selected_option.clinician_id != plan.clinician_id:
            raise EvidenceGraphValidationError(
                f"Final plan {plan.plan_id} clinician differs from selected option"
            )

        _require_refs(
            plan.validated_diagnosis_refs,
            diagnosis_ids,
            f"Final plan {plan.plan_id} validated_diagnosis_refs",
        )
        for diagnosis_ref in plan.validated_diagnosis_refs:
            diagnosis = diagnoses[diagnosis_ref]
            if diagnosis.state not in {ReviewState.ACCEPTED, ReviewState.EDITED}:
                raise EvidenceGraphValidationError(
                    f"Final plan {plan.plan_id} references unvalidated diagnosis {diagnosis_ref}"
                )
            if diagnosis.clinician_id != plan.clinician_id:
                raise EvidenceGraphValidationError(
                    f"Final plan {plan.plan_id} clinician differs from diagnosis {diagnosis_ref}"
                )

        _require_refs(
            plan.validated_problem_refs,
            problem_ids,
            f"Final plan {plan.plan_id} validated_problem_refs",
        )
        for problem_ref in plan.validated_problem_refs:
            problem = problems[problem_ref]
            if problem.state not in {ReviewState.ACCEPTED, ReviewState.EDITED}:
                raise EvidenceGraphValidationError(
                    f"Final plan {plan.plan_id} references unvalidated problem {problem_ref}"
                )
            if problem.clinician_id != plan.clinician_id:
                raise EvidenceGraphValidationError(
                    f"Final plan {plan.plan_id} clinician differs from problem {problem_ref}"
                )

        _require_refs(
            plan.validated_objective_refs,
            objective_ids,
            f"Final plan {plan.plan_id} validated_objective_refs",
        )
        for objective_ref in plan.validated_objective_refs:
            objective = objectives[objective_ref]
            if objective.state not in {ReviewState.ACCEPTED, ReviewState.EDITED}:
                raise EvidenceGraphValidationError(
                    f"Final plan {plan.plan_id} references unvalidated objective {objective_ref}"
                )
            if objective.clinician_id != plan.clinician_id:
                raise EvidenceGraphValidationError(
                    f"Final plan {plan.plan_id} clinician differs from objective {objective_ref}"
                )

        _require_refs(
            [plan.validation_ref],
            validation_ids,
            f"Final plan {plan.plan_id} validation_ref",
        )
        validation = validations[plan.validation_ref]
        if validation.target_type != "final_plan" or validation.target_id != plan.plan_id:
            raise EvidenceGraphValidationError(
                f"Final plan {plan.plan_id} validation must target that final plan"
            )
        if validation.action not in {ValidationAction.ACCEPT, ValidationAction.EDIT}:
            raise EvidenceGraphValidationError(
                f"Final plan {plan.plan_id} cannot reference a rejected validation"
            )
        if validation.clinician_id != plan.clinician_id:
            raise EvidenceGraphValidationError(
                f"Final plan {plan.plan_id} clinician differs from validation record"
            )
        if validation.validated_at != plan.clinician_validated_at:
            raise EvidenceGraphValidationError(
                f"Final plan {plan.plan_id} validation timestamp differs from plan audit"
            )
        for phase in plan.phases:
            _require_refs(
                phase.objective_refs,
                objective_ids,
                f"Final plan {plan.plan_id} phase {phase.phase_id} objective_refs",
            )
