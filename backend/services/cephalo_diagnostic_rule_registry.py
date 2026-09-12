"""Versioned source-bound rule registry for R11 cephalometric diagnosis.

The registry stores rule metadata only. It contains no patient thresholds and no
rule evaluator. Production starts with an empty registry so a diagnostic rule
cannot become active merely because a schema object carries a familiar name.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple

from backend.services.cephalo_norm_registry import (
    NormRegistry,
    SourceTier,
    registry as default_norm_registry,
)


_ADMISSIBLE_RULE_SOURCE_TIERS = frozenset(
    {
        SourceTier.PRIMARY_ARTICLE,
        SourceTier.PEER_REVIEWED_POPULATION_STUDY,
        SourceTier.PEER_REVIEWED_REVIEW,
    }
)


@dataclass(frozen=True)
class FindingRuleDefinition:
    rule_id: str
    version: str
    domain: str
    source_ids: Tuple[str, ...]
    description: str
    requires_active_normative_reference: bool = True


@dataclass(frozen=True)
class DiagnosticRuleDefinition:
    rule_id: str
    version: str
    domain: str
    source_ids: Tuple[str, ...]
    finding_rule_ids: Tuple[str, ...]
    description: str


class DiagnosticRuleRegistry:
    """Fail-closed registry for source-bound R11 rule metadata."""

    def __init__(self, *, norm_registry: NormRegistry = default_norm_registry) -> None:
        self._norm_registry = norm_registry
        self._finding_rules: Dict[str, FindingRuleDefinition] = {}
        self._diagnostic_rules: Dict[str, DiagnosticRuleDefinition] = {}

    @staticmethod
    def _nonempty(value: str, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be non-empty")

    def _validate_sources(self, source_ids: Tuple[str, ...]) -> None:
        if not source_ids:
            raise ValueError("Diagnostic rule requires at least one scientific source")
        unknown = sorted(set(source_ids) - set(self._norm_registry.sources))
        if unknown:
            raise ValueError(f"Unknown diagnostic rule source(s): {', '.join(unknown)}")
        resolved = [self._norm_registry.get_source(source_id) for source_id in source_ids]
        if not any(
            source is not None and source.tier in _ADMISSIBLE_RULE_SOURCE_TIERS
            for source in resolved
        ):
            raise ValueError(
                "Diagnostic rule requires at least one peer-reviewed scientific source"
            )

    def register_finding_rule(self, rule: FindingRuleDefinition) -> None:
        self._nonempty(rule.rule_id, "rule_id")
        self._nonempty(rule.version, "version")
        self._nonempty(rule.domain, "domain")
        self._nonempty(rule.description, "description")
        if rule.rule_id in self._finding_rules:
            raise ValueError(f"Duplicate finding rule: {rule.rule_id}")
        self._validate_sources(rule.source_ids)
        self._finding_rules[rule.rule_id] = rule

    def register_diagnostic_rule(self, rule: DiagnosticRuleDefinition) -> None:
        self._nonempty(rule.rule_id, "rule_id")
        self._nonempty(rule.version, "version")
        self._nonempty(rule.domain, "domain")
        self._nonempty(rule.description, "description")
        if rule.rule_id in self._diagnostic_rules:
            raise ValueError(f"Duplicate diagnostic rule: {rule.rule_id}")
        self._validate_sources(rule.source_ids)
        if not rule.finding_rule_ids:
            raise ValueError("Diagnostic rule requires at least one finding rule")
        unknown = sorted(set(rule.finding_rule_ids) - set(self._finding_rules))
        if unknown:
            raise ValueError(
                f"Diagnostic rule references unknown finding rule(s): {', '.join(unknown)}"
            )
        self._diagnostic_rules[rule.rule_id] = rule

    @property
    def finding_rules(self) -> Mapping[str, FindingRuleDefinition]:
        return MappingProxyType(dict(self._finding_rules))

    @property
    def diagnostic_rules(self) -> Mapping[str, DiagnosticRuleDefinition]:
        return MappingProxyType(dict(self._diagnostic_rules))

    def get_finding_rule(self, rule_id: str) -> Optional[FindingRuleDefinition]:
        return self._finding_rules.get(rule_id)

    def get_diagnostic_rule(self, rule_id: str) -> Optional[DiagnosticRuleDefinition]:
        return self._diagnostic_rules.get(rule_id)


# Production registry intentionally empty. R11 must source-lock and review every
# rule before registration; tests construct isolated synthetic registries.
registry = DiagnosticRuleRegistry()
