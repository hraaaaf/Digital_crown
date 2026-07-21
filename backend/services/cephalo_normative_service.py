"""
Cephalometric normative service — deterministic profile resolution and
scientific gating, isolated from every clinical consumer.

Not wired to cephalo_engine.py, cephalo_consistency_validator.py,
ai_advisor.py, bilan_ortho_engine.py, any PDF generator, or the frontend.
No geometry lives here and CephaloEngine is never imported — the caller
already has a computed raw_value; this module only decides what, if
anything, that raw_value is allowed to mean.

Five invariants hold unconditionally, and are each covered by tests in
test_cephalo_normative_service.py:

  1. No silent fallback, ever. Every dimension (age, sex, population,
     definition_version) either matches explicitly or the corresponding
     profile is excluded — never defaulted, never rounded to "nearest".
  2. LEGACY_UNVALIDATED is non-authoritative. A legacy profile may be
     resolved and its reference values returned for traceability, but
     `classification` stays None and no diagnostic label is ever produced
     from it.
  3. Quarantine is a double gate. MeasurementDefinition.definition_status
     and NormativeProfile.validation_status are checked independently;
     either one being QUARANTINED blocks classification regardless of the
     other.
  4. Ambiguity blocks classification. Two or more profiles eligible for
     the same (measurement, definition_version, context) never resolve by
     picking the first, the newest, or any other implicit priority —
     the result is AMBIGUOUS_MATCH with classification=None.
  5. Classification requires an explicit ClassificationRule. A mean/SD
     reference is never auto-thresholded into a High/Low/Class label —
     only a matching, validated ClassificationRule can produce one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from backend.schemas.cephalo_normative import (
    ClassificationRule,
    DefinitionStatus,
    MeasurementDefinition,
    NormativeContext,
    NormativeProfile,
    PlausibilityBounds,
    Sex,
    ValidationStatus,
)
from backend.services.cephalo_normative_registry import (
    load_classification_rules,
    load_measurement_definitions,
    load_normative_profiles,
    load_plausibility_bounds,
)


class NormativeEvaluationStatus(str, Enum):
    UNKNOWN_MEASUREMENT = "UNKNOWN_MEASUREMENT"
    DEFINITION_VERSION_MISMATCH = "DEFINITION_VERSION_MISMATCH"
    DEFINITION_QUARANTINED = "DEFINITION_QUARANTINED"
    PROFILE_QUARANTINED = "PROFILE_QUARANTINED"
    MISSING_CONTEXT = "MISSING_CONTEXT"
    NO_PROFILE = "NO_PROFILE"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
    PROFILE_UNVALIDATED = "PROFILE_UNVALIDATED"
    VALIDATED_PROFILE_MATCH = "VALIDATED_PROFILE_MATCH"


@dataclass(frozen=True)
class NormativeReference:
    """Reference metadata from a resolved profile — returned even when the
    result is non-authoritative, per the "legacy is traceable" invariant.
    """
    reference_type: str
    mean: Optional[float] = None
    sd: Optional[float] = None
    range: Optional[tuple] = None
    single_value: Optional[float] = None
    categorical_thresholds: Optional[List[str]] = None


@dataclass(frozen=True)
class NormativeEvaluationResult:
    measurement_id: str
    raw_value: float
    unit: Optional[str]
    status: NormativeEvaluationStatus
    reason: str
    matched_profile_id: Optional[str] = None
    ambiguous_profile_ids: Optional[List[str]] = None
    reference: Optional[NormativeReference] = None
    classification: Optional[str] = None
    source_id: Optional[str] = None


# --- Process-local registry cache (load once, reuse — no DB, no re-parsing per call) ---

@dataclass
class _RegistrySnapshot:
    definitions: List[MeasurementDefinition] = field(default_factory=list)
    profiles: List[NormativeProfile] = field(default_factory=list)
    rules: List[ClassificationRule] = field(default_factory=list)
    bounds: List[PlausibilityBounds] = field(default_factory=list)


_cache: Optional[_RegistrySnapshot] = None


def _registry() -> _RegistrySnapshot:
    global _cache
    if _cache is None:
        _cache = _RegistrySnapshot(
            definitions=load_measurement_definitions(),
            profiles=load_normative_profiles(),
            rules=load_classification_rules(),
            bounds=load_plausibility_bounds(),
        )
    return _cache


def reset_cache() -> None:
    """Test-only hook. Clears the process-local registry cache so tests can
    inject synthetic fixtures (via monkeypatching the loader functions) or
    verify the real registry is re-readable. Never called by clinical code.
    """
    global _cache
    _cache = None


# --- Matching helpers ---

def _age_eligible(profile: NormativeProfile, context: NormativeContext) -> Optional[bool]:
    """Returns True/False if determinable, or None if age is required but
    context.age is missing (caller distinguishes MISSING_CONTEXT from a
    genuine value mismatch using this).
    """
    if profile.age_min is None and profile.age_max is None:
        return True
    if context.age is None:
        return None
    if profile.age_min is not None and context.age < profile.age_min:
        return False
    if profile.age_max is not None and context.age > profile.age_max:
        return False
    return True


def _sex_eligible(profile: NormativeProfile, context: NormativeContext) -> Optional[bool]:
    if profile.sex == Sex.POOLED:
        return True
    if context.sex is None:
        return None
    return context.sex == profile.sex


def _population_eligible(profile: NormativeProfile, context: NormativeContext) -> Optional[bool]:
    if context.population_id is None:
        return None
    return context.population_id == profile.population_id


@dataclass
class _MatchOutcome:
    profile: NormativeProfile
    eligible: bool
    excluded_by_missing_context: bool


def _match_context(profiles: List[NormativeProfile], context: NormativeContext) -> List[_MatchOutcome]:
    outcomes = []
    for p in profiles:
        checks = [_age_eligible(p, context), _sex_eligible(p, context), _population_eligible(p, context)]
        if any(c is False for c in checks):
            outcomes.append(_MatchOutcome(p, eligible=False, excluded_by_missing_context=False))
        elif any(c is None for c in checks):
            outcomes.append(_MatchOutcome(p, eligible=False, excluded_by_missing_context=True))
        else:
            outcomes.append(_MatchOutcome(p, eligible=True, excluded_by_missing_context=False))
    return outcomes


def _to_reference(profile: NormativeProfile) -> NormativeReference:
    return NormativeReference(
        reference_type=profile.reference_type.value,
        mean=profile.mean,
        sd=profile.sd,
        range=profile.range,
        single_value=profile.single_value,
        categorical_thresholds=profile.categorical_thresholds,
    )


def _classify(value: float, thresholds: List[float], labels: List[str]) -> str:
    """Reproduces exactly the two threshold shapes found in every migrated
    ClassificationRule — never a guessed generalization for shapes that
    don't exist in the registry yet (see module docstring / plan for the
    derivation against the original source code).
    """
    n = len(thresholds)
    if n == 1:
        return labels[1] if value > thresholds[0] else labels[0]
    if n == 2:
        if value > thresholds[-1]:
            return labels[-1]
        if value < thresholds[0]:
            return labels[0]
        return labels[1]
    raise NotImplementedError(
        f"_classify: no verified semantics for a {n}-threshold rule — every rule "
        "migrated so far is 1 or 2 thresholds. Add the exact source-verified shape "
        "before supporting this, per the 'stop at the safe limit' principle."
    )


def _compatible_rules(rules: List[ClassificationRule], measurement_id: str, definition_version: str, profile_id: str) -> List[ClassificationRule]:
    return [
        r for r in rules
        if r.measurement_id == measurement_id
        and r.measurement_definition_version == definition_version
        and r.validation_status == ValidationStatus.VALIDATED_FOR_PROFILE
        and (r.profile_id is None or r.profile_id == profile_id)
    ]


# --- Public API ---

def evaluate_measurement(
    measurement_id: str,
    raw_value: float,
    definition_version: str,
    context: NormativeContext,
) -> NormativeEvaluationResult:
    reg = _registry()

    definition = next((d for d in reg.definitions if d.measurement_id == measurement_id), None)
    if definition is None:
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=None,
            status=NormativeEvaluationStatus.UNKNOWN_MEASUREMENT,
            reason=f"No MeasurementDefinition registered for '{measurement_id}'.",
        )

    if definition.definition_version != definition_version:
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
            status=NormativeEvaluationStatus.DEFINITION_VERSION_MISMATCH,
            reason=(
                f"Requested definition_version '{definition_version}' does not match "
                f"the registered version '{definition.definition_version}' — no profile evaluated."
            ),
        )

    if definition.definition_status == DefinitionStatus.QUARANTINED:
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
            status=NormativeEvaluationStatus.DEFINITION_QUARANTINED,
            reason=f"MeasurementDefinition '{measurement_id}' is QUARANTINED — no normative classification is permitted regardless of any profile's own status.",
        )

    candidates = [
        p for p in reg.profiles
        if p.measurement_id == measurement_id and p.measurement_definition_version == definition_version
    ]
    outcomes = _match_context(candidates, context)
    eligible = [o for o in outcomes if o.eligible]

    if not eligible:
        if candidates and all(o.excluded_by_missing_context for o in outcomes):
            return NormativeEvaluationResult(
                measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
                status=NormativeEvaluationStatus.MISSING_CONTEXT,
                reason="One or more profiles require age/sex/population context that was not supplied.",
            )
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
            status=NormativeEvaluationStatus.NO_PROFILE,
            reason="No normative profile matches the supplied context for this measurement.",
        )

    if len(eligible) > 1:
        ids = sorted(o.profile.profile_id for o in eligible)
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
            status=NormativeEvaluationStatus.AMBIGUOUS_MATCH,
            reason=f"{len(ids)} profiles are equally eligible for this context — refusing to pick one silently.",
            ambiguous_profile_ids=ids,
        )

    profile = eligible[0].profile

    if profile.validation_status == ValidationStatus.QUARANTINED:
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
            status=NormativeEvaluationStatus.PROFILE_QUARANTINED,
            reason=f"NormativeProfile '{profile.profile_id}' is QUARANTINED.",
            matched_profile_id=profile.profile_id,
        )

    if profile.validation_status != ValidationStatus.VALIDATED_FOR_PROFILE:
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
            status=NormativeEvaluationStatus.PROFILE_UNVALIDATED,
            reason=f"NormativeProfile '{profile.profile_id}' is {profile.validation_status.value} — reference available, no authoritative classification.",
            matched_profile_id=profile.profile_id,
            reference=_to_reference(profile),
            source_id=profile.source_id,
        )

    # profile.validation_status == VALIDATED_FOR_PROFILE
    compatible = _compatible_rules(reg.rules, measurement_id, definition_version, profile.profile_id)
    if not compatible:
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
            status=NormativeEvaluationStatus.VALIDATED_PROFILE_MATCH,
            reason=f"NormativeProfile '{profile.profile_id}' is validated but no compatible ClassificationRule exists — reference only.",
            matched_profile_id=profile.profile_id,
            reference=_to_reference(profile),
            source_id=profile.source_id,
        )
    if len(compatible) > 1:
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
            status=NormativeEvaluationStatus.VALIDATED_PROFILE_MATCH,
            reason=f"{len(compatible)} ClassificationRules are compatible with '{profile.profile_id}' — refusing to pick one silently, no classification produced.",
            matched_profile_id=profile.profile_id,
            reference=_to_reference(profile),
            source_id=profile.source_id,
        )

    rule = compatible[0]
    label = _classify(raw_value, rule.thresholds, rule.labels)
    return NormativeEvaluationResult(
        measurement_id=measurement_id, raw_value=raw_value, unit=definition.unit,
        status=NormativeEvaluationStatus.VALIDATED_PROFILE_MATCH,
        reason=f"Matched validated profile '{profile.profile_id}' and rule '{rule.rule_id}'.",
        matched_profile_id=profile.profile_id,
        reference=_to_reference(profile),
        classification=label,
        source_id=profile.source_id or rule.source_id,
    )


def get_plausibility_bounds(measurement_id: str) -> List[PlausibilityBounds]:
    """Thin pass-through — every PlausibilityBounds row for a measurement,
    unmodified. No matching, no gating, no clinical interpretation. Not
    wired into cephalo_consistency_validator.py by this mission.
    """
    return [b for b in _registry().bounds if b.measurement_id == measurement_id]
