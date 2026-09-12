"""Focused tests for R13 therapeutic registry source-lock invariants."""

from datetime import datetime, timezone

import pytest

from backend.services.cephalo_evidence_graph import EvidenceGraphValidationError
from backend.services.cephalo_r13_therapeutic_safety import (
    _require_source_applicability_context,
)
from backend.services.cephalo_therapeutic_rule_registry import (
    TherapeuticRuleRegistry,
    TherapeuticSourceDefinition,
    TherapeuticSourceType,
)


NOW = datetime(2026, 9, 12, 13, 30, tzinfo=timezone.utc)


def _source(*, context, reviewed_at=NOW):
    return TherapeuticSourceDefinition(
        source_id="R13_REGISTRY_SYNTHETIC_SOURCE",
        version="1",
        source_type=TherapeuticSourceType.CLINICAL_GUIDELINE,
        citation="Synthetic registry test source; no clinical meaning.",
        context=context,
        reviewed_by="synthetic-reviewer",
        reviewed_at=reviewed_at,
        review_reference="synthetic-review:test-only",
        approved_for_clinical_rules=True,
    )


def test_registered_therapeutic_source_context_is_immutable_copy():
    mutable_context = {"population": "synthetic", "setting": "unit-test"}
    registry = TherapeuticRuleRegistry()
    registry.register_source(_source(context=mutable_context))

    mutable_context["population"] = "tampered-after-registration"
    stored = registry.get_source("R13_REGISTRY_SYNTHETIC_SOURCE", "1")

    assert stored is not None
    assert stored.context["population"] == "synthetic"
    with pytest.raises(TypeError):
        stored.context["population"] = "tampered-through-registry"


def test_therapeutic_source_review_timestamp_must_be_timezone_aware():
    registry = TherapeuticRuleRegistry()

    with pytest.raises(ValueError, match="timezone-aware"):
        registry.register_source(
            _source(
                context={"population": "synthetic", "setting": "unit-test"},
                reviewed_at=datetime(2026, 9, 12, 13, 30),
            )
        )


def test_therapeutic_evaluation_context_must_match_registered_source_applicability():
    registry = TherapeuticRuleRegistry()
    registry.register_source(
        _source(context={"population": "synthetic", "setting": "unit-test"})
    )
    binding = (("R13_REGISTRY_SYNTHETIC_SOURCE", "1"),)

    _require_source_applicability_context(
        {"population": "synthetic", "setting": "unit-test", "extra": "allowed"},
        binding,
        registry=registry,
        label="synthetic criterion",
    )

    with pytest.raises(EvidenceGraphValidationError, match="incompatible with source"):
        _require_source_applicability_context(
            {"population": "different-population", "setting": "unit-test"},
            binding,
            registry=registry,
            label="synthetic criterion",
        )
