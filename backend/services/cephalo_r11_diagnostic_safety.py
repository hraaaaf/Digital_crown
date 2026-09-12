"""R11 fail-closed safety gates for cephalometric diagnostic evidence.

This module adds the R11 diagnostic contract on top of the generic evidence-
graph integrity validator. It deliberately does not implement a clinical rule,
classification threshold, diagnosis, or treatment recommendation.
"""

from __future__ import annotations

from typing import Dict, Set

from backend.services.cephalo_diagnostic_rule_registry import (
    DiagnosticRuleRegistry,
    registry as default_diagnostic_rule_registry,
)
from backend.services.cephalo_evidence_graph import (
    EvidenceGraphSnapshot,
    EvidenceGraphValidationError,
    validate_evidence_graph,
)
from backend.services.cephalo_norm_registry import (
    NormRegistry,
    ReferenceKind,
    registry as default_norm_registry,
)


def _expected_reference_payload(reference) -> Dict[str, object]:
    if reference.kind == ReferenceKind.EXTREME_RANGE:
        return {
            "kind": ReferenceKind.EXTREME_RANGE.value,
            "lower": reference.lower,
            "upper": reference.upper,
        }
    if reference.kind == ReferenceKind.MEAN_SD:
        return {
            "kind": ReferenceKind.MEAN_SD.value,
            "mean": reference.mean,
            "sd": reference.sd,
        }
    raise EvidenceGraphValidationError(
        f"R11 does not support normative reference kind {reference.kind.value}"
    )


def validate_r11_diagnostic_graph(
    graph: EvidenceGraphSnapshot,
    *,
    norm_registry: NormRegistry = default_norm_registry,
    rule_registry: DiagnosticRuleRegistry = default_diagnostic_rule_registry,
) -> None:
    """Validate R11 diagnostic-safety invariants without activating clinical rules.

    R11 treats every currently registered normative reference as descriptive and
    inert. Exact registry payload/provenance may be carried for traceability, but
    an inactive normative evaluation cannot support or oppose a finding. Findings
    and hypotheses must bind to exact source-locked rule id/version pairs.
    """

    validate_evidence_graph(graph, norm_registry=norm_registry)

    measurements = {item.measurement_id: item for item in graph.measurements}
    constructions = {item.construction_id: item for item in graph.constructions}
    evaluations = {item.evaluation_id: item for item in graph.normative_evaluations}
    findings = {item.finding_id: item for item in graph.findings}

    inactive_evaluation_ids: Set[str] = set()
    active_evaluation_ids: Set[str] = set()

    for evaluation in graph.normative_evaluations:
        registered = norm_registry.get_reference(evaluation.norm_profile_id)
        if registered is None:
            raise EvidenceGraphValidationError(
                f"R11 normative evaluation {evaluation.evaluation_id} has unknown reference "
                f"{evaluation.norm_profile_id}"
            )

        expected_payload = _expected_reference_payload(registered)
        if evaluation.reference != expected_payload:
            raise EvidenceGraphValidationError(
                f"R11 normative evaluation {evaluation.evaluation_id} reference payload "
                f"does not exactly match registry {evaluation.norm_profile_id}"
            )

        if set(evaluation.source_refs) != set(registered.source_ids):
            raise EvidenceGraphValidationError(
                f"R11 normative evaluation {evaluation.evaluation_id} source_refs must "
                f"exactly match registry {evaluation.norm_profile_id}"
            )

        measurement = measurements[evaluation.measurement_ref]
        if registered.construction_gate:
            definition_ids = {
                constructions[construction_ref].definition_id
                for construction_ref in measurement.construction_refs
                if construction_ref in constructions
            }
            if registered.construction_gate not in definition_ids:
                raise EvidenceGraphValidationError(
                    f"R11 normative evaluation {evaluation.evaluation_id} requires "
                    f"construction gate {registered.construction_gate}"
                )

        if registered.active_for_patient_classification:
            active_evaluation_ids.add(evaluation.evaluation_id)
        else:
            inactive_evaluation_ids.add(evaluation.evaluation_id)
            if (
                evaluation.classification is not None
                or evaluation.classification_rule_id is not None
            ):
                raise EvidenceGraphValidationError(
                    f"R11 inactive normative evaluation {evaluation.evaluation_id} cannot "
                    "carry a patient classification"
                )

    for finding in graph.findings:
        rule = rule_registry.get_finding_rule(finding.rule_id, finding.rule_version)
        if rule is None:
            raise EvidenceGraphValidationError(
                f"R11 finding {finding.finding_id} uses unregistered rule version "
                f"{finding.rule_id}@{finding.rule_version}"
            )
        if finding.domain != rule.domain:
            raise EvidenceGraphValidationError(
                f"R11 finding {finding.finding_id} rule domain does not match registry"
            )

        supporting = set(finding.supporting_evidence_refs)
        opposing = set(finding.opposing_evidence_refs)
        overlap = supporting & opposing
        if overlap:
            raise EvidenceGraphValidationError(
                f"R11 finding {finding.finding_id} cannot use the same evidence as both "
                f"supporting and opposing: {', '.join(sorted(overlap))}"
            )

        unsafe_norm_refs = (supporting | opposing) & inactive_evaluation_ids
        if unsafe_norm_refs:
            raise EvidenceGraphValidationError(
                f"R11 finding {finding.finding_id} cannot use inactive normative "
                f"evaluation(s) as supporting/opposing evidence: "
                f"{', '.join(sorted(unsafe_norm_refs))}"
            )

        if rule.requires_active_normative_reference:
            used_active_norms = (supporting | opposing) & active_evaluation_ids
            if not used_active_norms:
                raise EvidenceGraphValidationError(
                    f"R11 finding {finding.finding_id} rule {rule.rule_id}@{rule.version} "
                    "requires an active normative evaluation"
                )

        missing = set(finding.missing_evidence_refs)
        active_claim_refs = supporting | opposing
        duplicated_missing = missing & active_claim_refs
        if duplicated_missing:
            raise EvidenceGraphValidationError(
                f"R11 finding {finding.finding_id} cannot mark active evidence as missing: "
                f"{', '.join(sorted(duplicated_missing))}"
            )

    for diagnosis in graph.diagnoses:
        if not diagnosis.rule_id or not diagnosis.rule_version:
            raise EvidenceGraphValidationError(
                f"R11 diagnosis {diagnosis.diagnosis_id} requires a versioned rule binding"
            )
        rule = rule_registry.get_diagnostic_rule(
            diagnosis.rule_id, diagnosis.rule_version
        )
        if rule is None:
            raise EvidenceGraphValidationError(
                f"R11 diagnosis {diagnosis.diagnosis_id} uses unregistered rule version "
                f"{diagnosis.rule_id}@{diagnosis.rule_version}"
            )
        if diagnosis.domain != rule.domain:
            raise EvidenceGraphValidationError(
                f"R11 diagnosis {diagnosis.diagnosis_id} rule domain does not match registry"
            )

        supporting = set(diagnosis.supporting_finding_refs)
        opposing = set(diagnosis.opposing_finding_refs)
        overlap = supporting & opposing
        if overlap:
            raise EvidenceGraphValidationError(
                f"R11 diagnosis {diagnosis.diagnosis_id} cannot use the same finding as both "
                f"supporting and opposing: {', '.join(sorted(overlap))}"
            )

        referenced_finding_ids = supporting | opposing
        used_rule_bindings = {
            (findings[item].rule_id, findings[item].rule_version)
            for item in referenced_finding_ids
        }
        outside_rule = sorted(
            used_rule_bindings - set(rule.finding_rule_bindings),
            key=lambda item: (item[0], item[1]),
        )
        if outside_rule:
            rendered = ", ".join(
                f"{rule_id}@{version}" for rule_id, version in outside_rule
            )
            raise EvidenceGraphValidationError(
                f"R11 diagnosis {diagnosis.diagnosis_id} uses finding rule version(s) "
                f"outside registered diagnostic rule {rule.rule_id}@{rule.version}: {rendered}"
            )

        missing = set(diagnosis.missing_data_refs)
        referenced_evaluations = missing & set(evaluations)
        for evaluation_id in referenced_evaluations:
            if evaluation_id not in inactive_evaluation_ids:
                continue
            # Explicitly allowed: an inert/unusable normative evaluation may be surfaced
            # as missing/blocked context. It must never become positive/negative evidence.
            continue
