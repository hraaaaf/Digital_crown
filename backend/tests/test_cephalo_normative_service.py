"""
Tests for the cephalometric normative service core
(backend/services/cephalo_normative_service.py).

Two groups:
  1. Synthetic-fixture tests (in-memory registry snapshots, never touching
     the real YAML data) covering every gate/matching/ambiguity/
     classification scenario, including VALIDATED_FOR_PROFILE — which no
     real profile uses today.
  2. Real-registry tests (no fixture injection) proving the current
     production data behaves exactly as the master audit predicts: no
     authoritative classification anywhere, quarantine holds, and multiple
     undifferentiated legacy origins per measurement correctly resolve to
     AMBIGUOUS_MATCH rather than a silently-picked single reference.

Exécuter avec : pytest backend/tests/test_cephalo_normative_service.py -v
"""
import datetime
import random
from pathlib import Path

import pytest

from backend.schemas.cephalo_normative import (
    AgeDependencyType,
    ClassificationRule,
    CodeOrigin,
    DefinitionStatus,
    MeasurementDefinition,
    NormativeContext,
    NormativeProfile,
    ReferenceType,
    Sex,
    ValidationStatus,
)
from backend.services import cephalo_normative_service as svc
from backend.services.cephalo_normative_service import (
    NormativeEvaluationStatus as Status,
    _RegistrySnapshot,
    evaluate_measurement,
    get_plausibility_bounds,
    reset_cache,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ORIGIN = CodeOrigin(file="backend/tests/test_cephalo_normative_service.py", symbol="fixture", line="1")


# ============================================================
# Synthetic fixture helpers
# ============================================================

def _definition(measurement_id="X", status=DefinitionStatus.ACTIVE, version="v1"):
    return MeasurementDefinition(
        measurement_id=measurement_id, canonical_name=measurement_id, display_name=measurement_id,
        analysis_family="Test", unit="mm", definition_version=version,
        required_landmarks=["A"], definition_status=status, origin=_ORIGIN,
    )


def _profile(
    profile_id, measurement_id="X", version="v1", mean=10.0, sd=2.0,
    age_min=None, age_max=None, age_dep=AgeDependencyType.AGE_INDEPENDENT,
    sex=Sex.POOLED, population_id="POP", status=ValidationStatus.LEGACY_UNVALIDATED,
):
    return NormativeProfile(
        profile_id=profile_id, measurement_id=measurement_id, measurement_definition_version=version,
        reference_type=ReferenceType.MEAN_SD, unit="mm", mean=mean, sd=sd,
        age_min=age_min, age_max=age_max, age_dependency_type=age_dep, sex=sex,
        population_id=population_id, validation_status=status, profile_version="v1",
        effective_from=datetime.date(2026, 1, 1), origin=_ORIGIN,
    )


def _rule(rule_id, measurement_id="X", version="v1", thresholds=(5.0,), labels=("Low", "High"), profile_id=None, status=ValidationStatus.VALIDATED_FOR_PROFILE):
    return ClassificationRule(
        rule_id=rule_id, measurement_id=measurement_id, measurement_definition_version=version,
        profile_id=profile_id, thresholds=list(thresholds), labels=list(labels),
        validation_status=status, origin=_ORIGIN,
    )


@pytest.fixture
def install_registry():
    """Installs a synthetic registry snapshot; auto-restores the real
    registry (lazily reloaded) after the test.
    """
    def _install(definitions=(), profiles=(), rules=(), bounds=()):
        svc._cache = _RegistrySnapshot(
            definitions=list(definitions), profiles=list(profiles), rules=list(rules), bounds=list(bounds),
        )
    yield _install
    reset_cache()


# ============================================================
# 1. Definition gates
# ============================================================

class TestDefinitionGates:
    def test_unknown_measurement(self, install_registry):
        install_registry()
        result = evaluate_measurement("GHOST", 1.0, "v1", NormativeContext())
        assert result.status == Status.UNKNOWN_MEASUREMENT
        assert result.classification is None

    def test_version_mismatch_blocks_even_a_valid_profile(self, install_registry):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
        )
        result = evaluate_measurement("X", 10.0, "v2", NormativeContext(population_id="POP"))
        assert result.status == Status.DEFINITION_VERSION_MISMATCH
        assert result.classification is None

    def test_case_a_quarantined_definition_blocks_validated_profile(self, install_registry):
        # Mission §8/§25 Case A: definition QUARANTINED, profile VALIDATED_FOR_PROFILE -> blocked.
        install_registry(
            definitions=[_definition(status=DefinitionStatus.QUARANTINED)],
            profiles=[_profile("P1", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
        )
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.DEFINITION_QUARANTINED
        assert result.classification is None

    def test_case_b_quarantined_profile_blocks_even_active_definition(self, install_registry):
        # Mission §9/§25 Case B: definition active, profile QUARANTINED -> blocked.
        install_registry(
            definitions=[_definition(status=DefinitionStatus.ACTIVE)],
            profiles=[_profile("P1", status=ValidationStatus.QUARANTINED)],
        )
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.PROFILE_QUARANTINED
        assert result.classification is None
        assert result.matched_profile_id == "P1"

    def test_quarantine_gate_checked_before_any_context_is_needed(self, install_registry):
        install_registry(definitions=[_definition(status=DefinitionStatus.QUARANTINED)])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext())  # fully empty context
        assert result.status == Status.DEFINITION_QUARANTINED


# ============================================================
# 2. Age matching
# ============================================================

class TestAgeMatching:
    def _install_age_bound(self, install_registry, age_min=5.0, age_max=15.0):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", age_min=age_min, age_max=age_max, age_dep=AgeDependencyType.TWO_BUCKET)],
        )

    def test_age_equals_min_is_eligible(self, install_registry):
        self._install_age_bound(install_registry)
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(age=5.0, population_id="POP"))
        assert result.status == Status.PROFILE_UNVALIDATED
        assert result.matched_profile_id == "P1"

    def test_age_equals_max_is_eligible(self, install_registry):
        self._install_age_bound(install_registry)
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(age=15.0, population_id="POP"))
        assert result.status == Status.PROFILE_UNVALIDATED

    def test_age_just_below_min_is_not_eligible(self, install_registry):
        self._install_age_bound(install_registry)
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(age=4.999, population_id="POP"))
        assert result.status == Status.NO_PROFILE

    def test_age_just_above_max_is_not_eligible(self, install_registry):
        self._install_age_bound(install_registry)
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(age=15.001, population_id="POP"))
        assert result.status == Status.NO_PROFILE

    def test_age_missing_when_required_is_missing_context(self, install_registry):
        self._install_age_bound(install_registry)
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))  # no age
        assert result.status == Status.MISSING_CONTEXT

    def test_age_irrelevant_for_age_independent_profile(self, install_registry):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", age_min=None, age_max=None, age_dep=AgeDependencyType.AGE_INDEPENDENT)],
        )
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))  # no age supplied
        assert result.status == Status.PROFILE_UNVALIDATED


# ============================================================
# 3. Sex matching
# ============================================================

class TestSexMatching:
    def test_pooled_profile_matches_male(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", sex=Sex.POOLED)])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(sex=Sex.MALE, population_id="POP"))
        assert result.status == Status.PROFILE_UNVALIDATED

    def test_pooled_profile_matches_female(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", sex=Sex.POOLED)])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(sex=Sex.FEMALE, population_id="POP"))
        assert result.status == Status.PROFILE_UNVALIDATED

    def test_pooled_profile_matches_missing_sex(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", sex=Sex.POOLED)])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.PROFILE_UNVALIDATED

    def test_male_specific_profile_matches_male_context(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", sex=Sex.MALE)])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(sex=Sex.MALE, population_id="POP"))
        assert result.status == Status.PROFILE_UNVALIDATED

    def test_male_specific_profile_rejects_female_context(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", sex=Sex.MALE)])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(sex=Sex.FEMALE, population_id="POP"))
        assert result.status == Status.NO_PROFILE

    def test_male_specific_profile_rejects_missing_sex(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", sex=Sex.MALE)])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.MISSING_CONTEXT


# ============================================================
# 4. Population matching
# ============================================================

class TestPopulationMatching:
    def test_exact_population_match(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", population_id="MOROCCO_2026")])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="MOROCCO_2026"))
        assert result.status == Status.PROFILE_UNVALIDATED

    def test_wrong_population_no_match(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", population_id="MOROCCO_2026")])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="CAUCASIAN_CLASSIC"))
        assert result.status == Status.NO_PROFILE

    def test_missing_population_is_missing_context(self, install_registry):
        install_registry(definitions=[_definition()], profiles=[_profile("P1", population_id="MOROCCO_2026")])
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext())
        assert result.status == Status.MISSING_CONTEXT


# ============================================================
# 5. Ambiguity
# ============================================================

class TestAmbiguity:
    def test_two_equally_eligible_profiles_are_ambiguous(self, install_registry):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", population_id="POP"), _profile("P2", population_id="POP")],
        )
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.AMBIGUOUS_MATCH
        assert result.classification is None
        assert result.matched_profile_id is None
        assert sorted(result.ambiguous_profile_ids) == ["P1", "P2"]

    def test_ambiguity_applies_even_when_one_candidate_is_validated(self, install_registry):
        # Confirms ambiguity is checked across ALL eligible profiles regardless
        # of validation_status (user-confirmed design decision).
        install_registry(
            definitions=[_definition()],
            profiles=[
                _profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE),
                _profile("P2", population_id="POP", status=ValidationStatus.LEGACY_UNVALIDATED),
            ],
        )
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.AMBIGUOUS_MATCH
        assert result.classification is None


# ============================================================
# 6. VALIDATED_FOR_PROFILE + classification rule execution
# ============================================================

class TestClassificationExecution:
    def test_validated_profile_without_compatible_rule_has_no_classification(self, install_registry):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
        )
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.VALIDATED_PROFILE_MATCH
        assert result.matched_profile_id == "P1"
        assert result.reference is not None
        assert result.classification is None

    @pytest.mark.parametrize("value,expected_label", [
        (4.999, "Low"),
        (5.0, "Low"),
        (5.001, "High"),
    ])
    def test_one_threshold_rule_boundary_semantics(self, install_registry, value, expected_label):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
            rules=[_rule("R1", thresholds=(5.0,), labels=("Low", "High"))],
        )
        result = evaluate_measurement("X", value, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.VALIDATED_PROFILE_MATCH
        assert result.classification == expected_label

    @pytest.mark.parametrize("value,expected_label", [
        (-1.0, "Below"),      # below lower threshold
        (0.0, "Middle"),      # exactly at lower threshold (inclusive-middle, matches ANB source)
        (2.0, "Middle"),      # inside
        (4.5, "Middle"),      # exactly at upper threshold (inclusive-middle)
        (5.0, "Above"),       # above upper threshold
    ])
    def test_two_threshold_rule_boundary_semantics(self, install_registry, value, expected_label):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
            rules=[_rule("R1", thresholds=(0.0, 4.5), labels=("Below", "Middle", "Above"))],
        )
        result = evaluate_measurement("X", value, "v1", NormativeContext(population_id="POP"))
        assert result.classification == expected_label

    def test_ambiguous_rule_selection_yields_no_classification(self, install_registry):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
            rules=[
                _rule("R1", thresholds=(5.0,), labels=("Low", "High")),
                _rule("R2", thresholds=(5.0,), labels=("Low", "High")),
            ],
        )
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.VALIDATED_PROFILE_MATCH  # profile itself wasn't ambiguous
        assert result.classification is None
        assert result.matched_profile_id == "P1"

    def test_rule_tied_to_a_different_profile_id_is_not_compatible(self, install_registry):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
            rules=[_rule("R1", thresholds=(5.0,), labels=("Low", "High"), profile_id="SOME_OTHER_PROFILE")],
        )
        result = evaluate_measurement("X", 10.0, "v1", NormativeContext(population_id="POP"))
        assert result.status == Status.VALIDATED_PROFILE_MATCH
        assert result.classification is None

    def test_three_threshold_rule_is_not_implemented(self, install_registry):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
            rules=[_rule("R1", thresholds=(1.0, 2.0, 3.0), labels=("A", "B", "C", "D"))],
        )
        with pytest.raises(NotImplementedError):
            evaluate_measurement("X", 1.5, "v1", NormativeContext(population_id="POP"))


# ============================================================
# 7. Determinism / order independence
# ============================================================

class TestDeterminism:
    def test_repeated_calls_are_identical(self, install_registry):
        install_registry(
            definitions=[_definition()],
            profiles=[_profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE)],
            rules=[_rule("R1", thresholds=(5.0,), labels=("Low", "High"))],
        )
        results = [evaluate_measurement("X", 7.0, "v1", NormativeContext(population_id="POP")) for _ in range(5)]
        assert len(set(r.classification for r in results)) == 1
        assert all(r == results[0] for r in results)

    def test_shuffled_profile_and_rule_order_does_not_change_result(self, install_registry):
        profiles = [_profile("P1", population_id="POP", status=ValidationStatus.VALIDATED_FOR_PROFILE)]
        rules = [
            _rule("R1", thresholds=(5.0,), labels=("Low", "High")),
        ]
        results = []
        for _ in range(5):
            shuffled_profiles = profiles[:]
            shuffled_rules = rules[:]
            random.shuffle(shuffled_profiles)
            random.shuffle(shuffled_rules)
            install_registry(definitions=[_definition()], profiles=shuffled_profiles, rules=shuffled_rules)
            results.append(evaluate_measurement("X", 7.0, "v1", NormativeContext(population_id="POP")))
        assert all(r == results[0] for r in results)

    def test_shuffled_order_does_not_change_ambiguity_outcome(self, install_registry):
        base_profiles = [_profile("P1", population_id="POP"), _profile("P2", population_id="POP"), _profile("P3", population_id="POP")]
        results = []
        for _ in range(5):
            shuffled = base_profiles[:]
            random.shuffle(shuffled)
            install_registry(definitions=[_definition()], profiles=shuffled)
            results.append(evaluate_measurement("X", 7.0, "v1", NormativeContext(population_id="POP")))
        for r in results:
            assert r.status == Status.AMBIGUOUS_MATCH
            assert sorted(r.ambiguous_profile_ids) == ["P1", "P2", "P3"]


# ============================================================
# 8. get_plausibility_bounds — thin pass-through
# ============================================================

class TestPlausibilityBoundsPassthrough:
    def test_returns_all_bounds_for_a_measurement(self, install_registry):
        from backend.schemas.cephalo_normative import PlausibilityBounds
        b1 = PlausibilityBounds(bounds_id="B1", measurement_id="X", hard_min=0.0, hard_max=10.0, soft_min=2.0, soft_max=8.0, origin=_ORIGIN)
        b2 = PlausibilityBounds(bounds_id="B2", measurement_id="X", hard_min=1.0, hard_max=9.0, soft_min=3.0, soft_max=7.0, origin=_ORIGIN)
        install_registry(bounds=[b1, b2])
        result = get_plausibility_bounds("X")
        assert {b.bounds_id for b in result} == {"B1", "B2"}

    def test_returns_empty_list_for_unknown_measurement(self, install_registry):
        install_registry(bounds=[])
        assert get_plausibility_bounds("GHOST") == []


# ============================================================
# 9. Real production registry (no fixture injection)
# ============================================================

class TestRealRegistryBehavior:
    """No synthetic data here — exercises the actual migrated Phase 2
    inventory. Every outcome below is a direct, predictable consequence of
    that data (see the master audit and Phase 2 report), not a new claim.
    """

    def setup_method(self):
        reset_cache()

    def teardown_method(self):
        reset_cache()

    def test_fully_empty_context_yields_missing_context_for_sna(self):
        # population_id is a required field on every migrated profile —
        # an empty context can never match it, by design (no fallback).
        result = evaluate_measurement("SNA", 82.0, "v1", NormativeContext())
        assert result.status == Status.MISSING_CONTEXT
        assert result.classification is None

    @pytest.mark.parametrize("measurement_id", ["SNA", "SNB", "ANB", "Inter_Incisif", "Ligne_E_Ls"])
    def test_multi_origin_measurements_are_ambiguous_under_generic_context(self, measurement_id):
        result = evaluate_measurement(
            measurement_id, 1.0, "v1", NormativeContext(population_id="UNSPECIFIED_LEGACY"),
        )
        assert result.status == Status.AMBIGUOUS_MATCH
        assert result.classification is None
        assert result.ambiguous_profile_ids and len(result.ambiguous_profile_ids) >= 2

    def test_single_origin_measurement_fmia_is_unvalidated_not_ambiguous(self):
        result = evaluate_measurement("FMIA", 65.0, "v1", NormativeContext(population_id="UNSPECIFIED_LEGACY"))
        assert result.status == Status.PROFILE_UNVALIDATED
        assert result.classification is None
        assert result.matched_profile_id == "FMIA_STEP3_LEGACY_V1"
        assert result.reference is not None

    @pytest.mark.parametrize("measurement_id", ["Wits_Appraisal", "Angle_Nasolabial", "Situation_B", "Decalage_A_B"])
    def test_quarantined_measurements_are_blocked_with_no_context_needed(self, measurement_id):
        result = evaluate_measurement(measurement_id, 0.0, "v1", NormativeContext())
        assert result.status == Status.DEFINITION_QUARANTINED
        assert result.classification is None
        assert result.reason  # explicit, non-empty reason string

    def test_no_real_profile_ever_produces_a_classification(self):
        # Exhaustive sweep: whatever the status, classification must be None
        # for every real measurement under any of a few representative contexts,
        # since zero profiles are VALIDATED_FOR_PROFILE today.
        from backend.services.cephalo_normative_registry import load_measurement_definitions
        contexts = [
            NormativeContext(),
            NormativeContext(population_id="UNSPECIFIED_LEGACY"),
            NormativeContext(age=10, sex=Sex.FEMALE, population_id="UNSPECIFIED_LEGACY"),
            NormativeContext(age=30, sex=Sex.MALE, population_id="UNSPECIFIED_LEGACY"),
        ]
        for definition in load_measurement_definitions():
            for ctx in contexts:
                result = evaluate_measurement(definition.measurement_id, 1.0, definition.definition_version, ctx)
                assert result.classification is None, (
                    f"{definition.measurement_id} produced a classification under {ctx} — "
                    "no real profile should be VALIDATED_FOR_PROFILE yet."
                )


# ============================================================
# 10. Isolation guard
# ============================================================

class TestIsolationGuard:
    # CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-STEINER-4A intentionally wired
    # cephalo_engine.py and bilan_ortho_engine.py to the normative service
    # for SNA/SNB/ANB, and CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-
    # FRANCFORT-4C wired ai_advisor.py for Angle_de_Tweed/IMPA/I_Francfort —
    # all excluded from this "must stay unwired" list on purpose. The
    # validator and every frontend file are explicitly still forbidden from
    # referencing it.
    _CONSUMER_FILES = [
        "backend/services/cephalo_consistency_validator.py",
        "frontend/src/features/ortho/cephaloUtils.ts",
        "frontend/src/features/ortho/orthoExpertSystem.ts",
        "frontend/src/features/ortho/components/Step3Clinical.tsx",
        "frontend/src/features/ortho/components/Step4Documents.tsx",
    ]

    def test_no_unwired_consumer_references_the_normative_service(self):
        for rel_path in self._CONSUMER_FILES:
            text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
            assert "cephalo_normative_service" not in text, (
                f"{rel_path} references the normative service — "
                "it must stay unwired (not part of the Steiner SNA/SNB/ANB wiring)."
            )

    def test_wired_consumers_use_the_service_not_a_reimplementation(self):
        # Mission §30: consumers must call evaluate_measurement, never
        # re-derive profile matching/validation/classification themselves.
        for rel_path in [
            "backend/services/cephalo_engine.py",
            "backend/services/bilan_ortho_engine.py",
            "backend/services/ai_advisor.py",
        ]:
            text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
            assert "cephalo_normative_service" in text
            assert "evaluate_measurement" in text
            # No local re-derivation of the old ANB/Tweed/IMPA/I_Francfort
            # cutoffs should remain.
            assert "anb > 4.5" not in text
            assert "anb < 0" not in text
            assert "tweed_status" not in text
            assert "impa_status" not in text
            assert "if_status" not in text
