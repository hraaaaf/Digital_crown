"""Fail-closed tests for the R11 diagnostic rule registry."""

import pytest

from backend.services.cephalo_diagnostic_rule_registry import (
    DiagnosticRuleDefinition,
    DiagnosticRuleRegistry,
    FindingRuleDefinition,
    registry as production_registry,
)


def _finding_rule(**changes) -> FindingRuleDefinition:
    values = {
        "rule_id": "R11_TEST_FINDING",
        "version": "1",
        "domain": "synthetic",
        "source_ids": ("CRANIOM_PART2_2011",),
        "description": "Synthetic rule for registry tests only.",
        "requires_active_normative_reference": False,
    }
    values.update(changes)
    return FindingRuleDefinition(**values)


def test_production_rule_registry_starts_empty():
    assert dict(production_registry.finding_rules) == {}
    assert dict(production_registry.diagnostic_rules) == {}


def test_finding_rule_requires_known_scientific_source():
    registry = DiagnosticRuleRegistry()
    with pytest.raises(ValueError, match="Unknown diagnostic rule source"):
        registry.register_finding_rule(_finding_rule(source_ids=("UNKNOWN_SOURCE",)))


def test_duplicate_finding_rule_is_rejected():
    registry = DiagnosticRuleRegistry()
    registry.register_finding_rule(_finding_rule())
    with pytest.raises(ValueError, match="Duplicate finding rule"):
        registry.register_finding_rule(_finding_rule())


def test_diagnostic_rule_requires_registered_finding_rule():
    registry = DiagnosticRuleRegistry()
    with pytest.raises(ValueError, match="unknown finding rule"):
        registry.register_diagnostic_rule(
            DiagnosticRuleDefinition(
                rule_id="R11_TEST_DIAGNOSIS",
                version="1",
                domain="synthetic",
                source_ids=("CRANIOM_PART2_2011",),
                finding_rule_ids=("R11_TEST_FINDING",),
                description="Synthetic diagnostic registry test only.",
            )
        )


def test_source_bound_finding_and_diagnostic_rules_register_together():
    registry = DiagnosticRuleRegistry()
    finding_rule = _finding_rule()
    registry.register_finding_rule(finding_rule)
    diagnostic_rule = DiagnosticRuleDefinition(
        rule_id="R11_TEST_DIAGNOSIS",
        version="1",
        domain="synthetic",
        source_ids=("CRANIOM_PART2_2011",),
        finding_rule_ids=(finding_rule.rule_id,),
        description="Synthetic diagnostic registry test only.",
    )
    registry.register_diagnostic_rule(diagnostic_rule)
    assert registry.get_finding_rule(finding_rule.rule_id) == finding_rule
    assert registry.get_diagnostic_rule(diagnostic_rule.rule_id) == diagnostic_rule
