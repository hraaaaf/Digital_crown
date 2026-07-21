"""
Tests unitaires de complétude et de traçabilité pour l'inventaire legacy
migré en Phase 2 du registre normatif céphalométrique.

Ces tests ne valident AUCUNE valeur scientifique — ils vérifient
uniquement que la migration est structurellement complète, que les
conflits connus (audit CEPHALOMETRY_NORMATIVE_SYSTEM_MASTER_AUDIT_COMPLETE)
sont bien préservés tels quels (pas arbitrés), que chaque littéral migré
reste traçable jusqu'à son fichier d'origine, et que le statut QUARANTINED
est correctement appliqué aux quatre mesures déjà mises en quarantaine.

Exécuter avec : pytest backend/tests/test_cephalo_normative_legacy_inventory.py -v
"""
from collections import defaultdict
from pathlib import Path

import pytest

from backend.schemas.cephalo_normative import DefinitionStatus, ValidationStatus
from backend.services.cephalo_normative_registry import (
    load_classification_rules,
    load_measurement_definitions,
    load_normative_profiles,
    load_plausibility_bounds,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

QUARANTINED_MEASUREMENT_IDS = {
    "Wits_Appraisal",
    "Angle_Nasolabial",
    "Situation_B",
    "Decalage_A_B",
}

# Measurements the master audit found with more than one DISTINCT-VALUE
# origin (not just a duplicate of the same literal) — the real conflicts
# that must survive the migration unresolved.
MEASUREMENTS_WITH_KNOWN_CONFLICTS = {
    "ANB",  # engine's own evaluate-band (0-4) vs classification cutoff (4.5/0) vs Step4/validator band (-2/6)
    "Angle_de_Tweed",  # engine rule 22/30 vs cephaloUtils.ts rule 20/30
    "Inter_Incisif",  # engine ±10 vs Step3/Step4 ±13
    "Surplomb",  # engine 2.25±0.75 vs Step3 2.2±0.8
    "Recouvrement",  # engine 2.25±0.75 vs Step3 2.2±0.8
    "Ligne_E_Ls",  # engine -4±2 vs Step3 -2±2
    "Ligne_E_Li",  # engine -2±2 vs Step3 -1±2
}


@pytest.fixture(scope="module")
def registry():
    return dict(
        definitions=load_measurement_definitions(),
        profiles=load_normative_profiles(),
        rules=load_classification_rules(),
        bounds=load_plausibility_bounds(),
    )


# --- Referential integrity: every reference resolves to a real definition ---

class TestReferentialIntegrity:
    def test_every_profile_measurement_id_has_a_definition(self, registry):
        known_ids = {d.measurement_id for d in registry["definitions"]}
        for profile in registry["profiles"]:
            assert profile.measurement_id in known_ids, (
                f"NormativeProfile {profile.profile_id} references unknown "
                f"measurement_id {profile.measurement_id!r}"
            )

    def test_every_rule_measurement_id_has_a_definition(self, registry):
        known_ids = {d.measurement_id for d in registry["definitions"]}
        for rule in registry["rules"]:
            assert rule.measurement_id in known_ids, (
                f"ClassificationRule {rule.rule_id} references unknown "
                f"measurement_id {rule.measurement_id!r}"
            )

    def test_every_bounds_measurement_id_has_a_definition(self, registry):
        known_ids = {d.measurement_id for d in registry["definitions"]}
        for b in registry["bounds"]:
            assert b.measurement_id in known_ids, (
                f"PlausibilityBounds {b.bounds_id} references unknown "
                f"measurement_id {b.measurement_id!r}"
            )


# --- Structural completeness against the master audit's own measurement list ---

class TestStructuralCompleteness:
    _EXPECTED_MEASUREMENT_IDS = {
        "SNA", "SNB", "ANB", "Angle_de_Tweed", "IMPA", "I_Francfort", "FMIA",
        "Inter_Incisif", "I_NA_angle", "I_NA_mm", "I_NB_angle", "I_NB_mm",
        "Surplomb", "Recouvrement", "Longueur_Maxillaire", "Longueur_Mandibulaire",
        "Differentiel_Maxillo_Mandibulaire", "Etage_Inferieur_Face", "Situation_A",
        "Ligne_E_Ls", "Ligne_E_Li",
        "Wits_Appraisal", "Angle_Nasolabial", "Situation_B", "Decalage_A_B",
    }

    def test_every_expected_measurement_has_a_definition(self, registry):
        found_ids = {d.measurement_id for d in registry["definitions"]}
        missing = self._EXPECTED_MEASUREMENT_IDS - found_ids
        assert not missing, f"Measurements missing a MeasurementDefinition: {missing}"

    def test_no_unexpected_extra_measurements_this_phase(self, registry):
        # Not a hard requirement of the architecture, but catches accidental
        # scope creep in this specific migration mission.
        found_ids = {d.measurement_id for d in registry["definitions"]}
        extra = found_ids - self._EXPECTED_MEASUREMENT_IDS
        assert not extra, f"Unexpected measurements found beyond the planned Phase 2 inventory: {extra}"


# --- Conflicts must be preserved, not silently collapsed ---

class TestKnownConflictsArePreserved:
    def _distinct_values_for(self, measurement_id, profiles):
        values = set()
        for p in profiles:
            if p.measurement_id != measurement_id:
                continue
            if p.mean is not None:
                values.add(("mean_sd", p.mean, p.sd, p.age_min, p.age_max))
            elif p.range is not None:
                values.add(("range", p.range, None, p.age_min, p.age_max))
            elif p.single_value is not None:
                values.add(("single", p.single_value, None, p.age_min, p.age_max))
        return values

    @pytest.mark.parametrize("measurement_id", sorted(MEASUREMENTS_WITH_KNOWN_CONFLICTS))
    def test_measurement_has_at_least_two_distinct_values(self, registry, measurement_id):
        distinct = self._distinct_values_for(measurement_id, registry["profiles"])
        rule_thresholds = {
            tuple(r.thresholds) for r in registry["rules"] if r.measurement_id == measurement_id
        }
        total_distinct_signals = len(distinct) + len(rule_thresholds)
        assert total_distinct_signals >= 2, (
            f"{measurement_id} is flagged as a known conflict in the master audit "
            f"but only {total_distinct_signals} distinct value(s) were migrated — "
            "the conflict must survive the migration, not be silently collapsed."
        )


# --- Quarantine: two independent gates must both agree ---

class TestQuarantineTwoGateInvariant:
    @pytest.mark.parametrize("measurement_id", sorted(QUARANTINED_MEASUREMENT_IDS))
    def test_definition_status_is_quarantined(self, registry, measurement_id):
        matches = [d for d in registry["definitions"] if d.measurement_id == measurement_id]
        assert len(matches) == 1
        assert matches[0].definition_status == DefinitionStatus.QUARANTINED

    @pytest.mark.parametrize("measurement_id", sorted(QUARANTINED_MEASUREMENT_IDS))
    def test_every_profile_for_a_quarantined_measurement_is_quarantined(self, registry, measurement_id):
        matches = [p for p in registry["profiles"] if p.measurement_id == measurement_id]
        assert matches, f"expected at least one migrated profile for {measurement_id}"
        for p in matches:
            assert p.validation_status == ValidationStatus.QUARANTINED, (
                f"{p.profile_id} is for a QUARANTINED measurement but has "
                f"validation_status={p.validation_status} instead of QUARANTINED — "
                "both gates must agree per the two-gate design."
            )

    def test_no_active_measurement_profile_is_quarantined(self, registry):
        quarantined_definitions = {
            d.measurement_id for d in registry["definitions"]
            if d.definition_status == DefinitionStatus.QUARANTINED
        }
        assert quarantined_definitions == QUARANTINED_MEASUREMENT_IDS
        for p in registry["profiles"]:
            if p.measurement_id not in quarantined_definitions:
                assert p.validation_status != ValidationStatus.QUARANTINED, (
                    f"{p.profile_id} is QUARANTINED but its measurement "
                    f"{p.measurement_id} is not — quarantine must originate "
                    "from the measurement definition, not appear ad hoc on a profile."
                )


# --- No value silently promoted beyond LEGACY_UNVALIDATED/QUARANTINED this phase ---

class TestNoPrematureValidation:
    def test_no_profile_is_validated_for_profile_yet(self, registry):
        for p in registry["profiles"]:
            assert p.validation_status != ValidationStatus.VALIDATED_FOR_PROFILE, (
                f"{p.profile_id} is VALIDATED_FOR_PROFILE — Phase 2 must not "
                "validate any constant, only migrate it as LEGACY_UNVALIDATED "
                "or QUARANTINED."
            )

    def test_no_rule_is_validated_for_profile_yet(self, registry):
        for r in registry["rules"]:
            assert r.validation_status != ValidationStatus.VALIDATED_FOR_PROFILE


# --- Traceability: every origin file path actually exists in the repo ---

class TestOriginTraceability:
    def _all_origins(self, registry):
        for d in registry["definitions"]:
            yield d.measurement_id, d.origin
        for p in registry["profiles"]:
            yield p.profile_id, p.origin
        for r in registry["rules"]:
            yield r.rule_id, r.origin
        for b in registry["bounds"]:
            yield b.bounds_id, b.origin

    def test_every_origin_file_exists_in_the_repo(self, registry):
        missing = []
        for entry_id, origin in self._all_origins(registry):
            if not (REPO_ROOT / origin.file).exists():
                missing.append((entry_id, origin.file))
        assert not missing, f"Entries with an origin.file that doesn't exist on disk: {missing}"


# --- Isolation guard, extended to backend AND frontend for Phase 2 ---

class TestPhase2IsolationGuard:
    # CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-STEINER-4A intentionally wired
    # cephalo_engine.py and bilan_ortho_engine.py to the normative service
    # for SNA/SNB/ANB, and CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-
    # FRANCFORT-4C wired ai_advisor.py for Angle_de_Tweed/IMPA/I_Francfort —
    # all excluded from this list on purpose. The validator and every
    # frontend file remain fully unwired.
    _BACKEND_CONSUMER_FILES = [
        "backend/services/cephalo_consistency_validator.py",
    ]
    _FRONTEND_CONSUMER_FILES = [
        "frontend/src/features/ortho/cephaloUtils.ts",
        "frontend/src/features/ortho/orthoExpertSystem.ts",
        "frontend/src/features/ortho/components/Step3Clinical.tsx",
        "frontend/src/features/ortho/components/Step4Documents.tsx",
    ]

    def test_no_unwired_consumer_imports_the_registry(self):
        for rel_path in self._BACKEND_CONSUMER_FILES + self._FRONTEND_CONSUMER_FILES:
            text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
            assert "cephalo_normative" not in text, (
                f"{rel_path} references the normative registry — it must stay "
                "unwired (not part of the Steiner SNA/SNB/ANB wiring)."
            )

    def test_frontend_stays_completely_untouched_by_steiner_wiring(self):
        for rel_path in self._FRONTEND_CONSUMER_FILES:
            text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
            assert "cephalo_normative_service" not in text
            assert "evaluate_measurement" not in text
