"""Fail-closed source and rule registry for R13 therapeutic evaluation.

Production intentionally starts empty. Registering a therapeutic source or rule
requires explicit source/version identity plus review metadata. The registry
contains metadata only: it does not prescribe, select, sequence, or build a
final treatment plan.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple

from backend.schemas.cephalo_r13_therapeutic_options import TherapeuticCriterionType


SourceKey = Tuple[str, str]
RuleKey = Tuple[str, str]


class TherapeuticSourceType(str, Enum):
    PRIMARY_ARTICLE = "PRIMARY_ARTICLE"
    CLINICAL_GUIDELINE = "CLINICAL_GUIDELINE"
    CONSENSUS_STATEMENT = "CONSENSUS_STATEMENT"
    SYSTEMATIC_REVIEW = "SYSTEMATIC_REVIEW"
    REGULATORY_LABEL = "REGULATORY_LABEL"


@dataclass(frozen=True)
class TherapeuticSourceDefinition:
    source_id: str
    version: str
    source_type: TherapeuticSourceType
    citation: str
    context: Mapping[str, str]
    reviewed_by: str
    reviewed_at: datetime.datetime
    review_reference: str
    approved_for_clinical_rules: bool = False


@dataclass(frozen=True)
class TherapeuticCriterionRuleDefinition:
    rule_id: str
    version: str
    criterion_type: TherapeuticCriterionType
    source_bindings: Tuple[SourceKey, ...]
    required_context_keys: Tuple[str, ...]
    description: str
    reviewed_by: str
    reviewed_at: datetime.datetime
    review_reference: str


@dataclass(frozen=True)
class TherapeuticOptionRuleDefinition:
    rule_id: str
    version: str
    source_bindings: Tuple[SourceKey, ...]
    indication_rule_bindings: Tuple[RuleKey, ...]
    contraindication_rule_bindings: Tuple[RuleKey, ...]
    required_context_keys: Tuple[str, ...]
    label: str
    description: str
    reviewed_by: str
    reviewed_at: datetime.datetime
    review_reference: str


class TherapeuticRuleRegistry:
    """Exact-version therapeutic registry; absent registration means unusable."""

    def __init__(self) -> None:
        self._sources: Dict[SourceKey, TherapeuticSourceDefinition] = {}
        self._criterion_rules: Dict[RuleKey, TherapeuticCriterionRuleDefinition] = {}
        self._option_rules: Dict[RuleKey, TherapeuticOptionRuleDefinition] = {}

    @staticmethod
    def _nonempty(value: str, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be non-empty")

    @classmethod
    def _validate_review(cls, *, reviewed_by: str, review_reference: str) -> None:
        cls._nonempty(reviewed_by, "reviewed_by")
        cls._nonempty(review_reference, "review_reference")

    @classmethod
    def _validate_context_keys(cls, keys: Tuple[str, ...]) -> None:
        if len(keys) != len(set(keys)):
            raise ValueError("required_context_keys cannot contain duplicates")
        for key in keys:
            cls._nonempty(key, "required_context_key")

    def register_source(self, source: TherapeuticSourceDefinition) -> None:
        self._nonempty(source.source_id, "source_id")
        self._nonempty(source.version, "source version")
        self._nonempty(source.citation, "citation")
        self._validate_review(
            reviewed_by=source.reviewed_by,
            review_reference=source.review_reference,
        )
        if not source.context:
            raise ValueError("Therapeutic source requires explicit applicability context")
        if any(not key.strip() or not value.strip() for key, value in source.context.items()):
            raise ValueError("Therapeutic source context keys and values must be non-empty")
        if not source.approved_for_clinical_rules:
            raise ValueError("Therapeutic source must be explicitly approved for clinical rules")
        key = (source.source_id, source.version)
        if key in self._sources:
            raise ValueError(
                f"Duplicate therapeutic source version: {source.source_id}@{source.version}"
            )
        self._sources[key] = source

    def _validate_source_bindings(self, bindings: Tuple[SourceKey, ...]) -> None:
        if not bindings:
            raise ValueError("Therapeutic rule requires at least one source binding")
        if len(bindings) != len(set(bindings)):
            raise ValueError("Therapeutic source bindings cannot contain duplicates")
        unknown = sorted(set(bindings) - set(self._sources))
        if unknown:
            rendered = ", ".join(f"{sid}@{version}" for sid, version in unknown)
            raise ValueError(f"Unknown therapeutic source version(s): {rendered}")

    def register_criterion_rule(self, rule: TherapeuticCriterionRuleDefinition) -> None:
        self._nonempty(rule.rule_id, "rule_id")
        self._nonempty(rule.version, "rule version")
        self._nonempty(rule.description, "description")
        self._validate_review(
            reviewed_by=rule.reviewed_by,
            review_reference=rule.review_reference,
        )
        self._validate_context_keys(rule.required_context_keys)
        self._validate_source_bindings(rule.source_bindings)
        key = (rule.rule_id, rule.version)
        if key in self._criterion_rules:
            raise ValueError(
                f"Duplicate therapeutic criterion rule version: {rule.rule_id}@{rule.version}"
            )
        self._criterion_rules[key] = rule

    def register_option_rule(self, rule: TherapeuticOptionRuleDefinition) -> None:
        self._nonempty(rule.rule_id, "rule_id")
        self._nonempty(rule.version, "rule version")
        self._nonempty(rule.label, "label")
        self._nonempty(rule.description, "description")
        self._validate_review(
            reviewed_by=rule.reviewed_by,
            review_reference=rule.review_reference,
        )
        self._validate_context_keys(rule.required_context_keys)
        self._validate_source_bindings(rule.source_bindings)
        if not rule.indication_rule_bindings:
            raise ValueError("Therapeutic option rule requires at least one indication rule")
        all_bindings = set(rule.indication_rule_bindings) | set(rule.contraindication_rule_bindings)
        if len(rule.indication_rule_bindings) != len(set(rule.indication_rule_bindings)):
            raise ValueError("indication_rule_bindings cannot contain duplicates")
        if len(rule.contraindication_rule_bindings) != len(set(rule.contraindication_rule_bindings)):
            raise ValueError("contraindication_rule_bindings cannot contain duplicates")
        unknown = sorted(all_bindings - set(self._criterion_rules))
        if unknown:
            rendered = ", ".join(f"{rid}@{version}" for rid, version in unknown)
            raise ValueError(f"Unknown therapeutic criterion rule version(s): {rendered}")
        wrong_indications = sorted(
            binding
            for binding in rule.indication_rule_bindings
            if self._criterion_rules[binding].criterion_type != TherapeuticCriterionType.INDICATION
        )
        wrong_contraindications = sorted(
            binding
            for binding in rule.contraindication_rule_bindings
            if self._criterion_rules[binding].criterion_type
            != TherapeuticCriterionType.CONTRAINDICATION
        )
        if wrong_indications or wrong_contraindications:
            raise ValueError("Therapeutic option rule criterion bindings use the wrong criterion type")
        key = (rule.rule_id, rule.version)
        if key in self._option_rules:
            raise ValueError(
                f"Duplicate therapeutic option rule version: {rule.rule_id}@{rule.version}"
            )
        self._option_rules[key] = rule

    @property
    def sources(self) -> Mapping[SourceKey, TherapeuticSourceDefinition]:
        return MappingProxyType(dict(self._sources))

    @property
    def criterion_rules(self) -> Mapping[RuleKey, TherapeuticCriterionRuleDefinition]:
        return MappingProxyType(dict(self._criterion_rules))

    @property
    def option_rules(self) -> Mapping[RuleKey, TherapeuticOptionRuleDefinition]:
        return MappingProxyType(dict(self._option_rules))

    def get_source(self, source_id: str, version: str) -> Optional[TherapeuticSourceDefinition]:
        return self._sources.get((source_id, version))

    def get_criterion_rule(
        self, rule_id: str, version: str
    ) -> Optional[TherapeuticCriterionRuleDefinition]:
        return self._criterion_rules.get((rule_id, version))

    def get_option_rule(
        self, rule_id: str, version: str
    ) -> Optional[TherapeuticOptionRuleDefinition]:
        return self._option_rules.get((rule_id, version))


# Production is fail-closed. No therapeutic source, criterion rule, or option is
# active until it is explicitly source-locked and reviewed.
registry = TherapeuticRuleRegistry()
