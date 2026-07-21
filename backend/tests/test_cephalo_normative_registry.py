"""
Tests unitaires purs pour les schemas + le loader du registre normatif
céphalométrique. Aucune connexion DB.

Ces tests couvrent la Phase 1 (schema/loader eux-mêmes) et restent valides
telles quelles après la Phase 2 (migration de l'inventaire legacy) — les
tests spécifiques à l'exhaustivité/traçabilité de l'inventaire migré vivent
dans test_cephalo_normative_legacy_inventory.py.
Exécuter avec : pytest backend/tests/test_cephalo_normative_registry.py -v
"""
import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.schemas.cephalo_normative import (
    AgeDependencyType,
    ClassificationRule,
    CodeOrigin,
    DefinitionStatus,
    MeasurementDefinition,
    NormativeProfile,
    PlausibilityBounds,
    ReferenceType,
    Sex,
    ValidationStatus,
)
from backend.services.cephalo_normative_registry import (
    load_classification_rules,
    load_measurement_definitions,
    load_normative_profiles,
    load_plausibility_bounds,
)

_EXAMPLE_ORIGIN = CodeOrigin(file="backend/services/example.py", symbol="EXAMPLE", line="1")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# --- Loader smoke tests against the real data files ---
# Phase 1 asserted these were empty; Phase 2 populated them with the legacy
# inventory by design. Detailed completeness/conflict/quarantine checks on
# that inventory live in test_cephalo_normative_legacy_inventory.py — these
# tests only confirm the loader itself still works end-to-end.

class TestLoaderReturnsValidatedData:
    def test_measurement_definitions_load_without_error(self):
        defs = load_measurement_definitions()
        assert len(defs) > 0
        assert len({d.measurement_id for d in defs}) == len(defs), "measurement_id must be unique"

    def test_normative_profiles_load_without_error(self):
        profiles = load_normative_profiles()
        assert len(profiles) > 0
        assert len({p.profile_id for p in profiles}) == len(profiles), "profile_id must be unique"

    def test_classification_rules_load_without_error(self):
        rules = load_classification_rules()
        assert len(rules) > 0
        assert len({r.rule_id for r in rules}) == len(rules), "rule_id must be unique"

    def test_plausibility_bounds_load_without_error(self):
        bounds = load_plausibility_bounds()
        assert len(bounds) > 0
        assert len({b.bounds_id for b in bounds}) == len(bounds), "bounds_id must be unique"


# --- Pydantic model acceptance of a valid synthetic example ---
# These examples exist only in this test file — they are not written into
# the real (empty) data files, per "zero active norms migrated this phase".

class TestMeasurementDefinitionSchema:
    def _valid_kwargs(self):
        return dict(
            measurement_id="EXAMPLE_MEASUREMENT",
            canonical_name="Example Measurement",
            display_name="Example",
            analysis_family="Example Family",
            unit="mm",
            definition_version="v1",
            required_landmarks=["A", "B"],
            definition_status=DefinitionStatus.ACTIVE,
            origin=_EXAMPLE_ORIGIN,
        )

    def test_valid_entry_accepted(self):
        MeasurementDefinition(**self._valid_kwargs())

    def test_missing_required_field_rejected(self):
        kwargs = self._valid_kwargs()
        del kwargs["definition_version"]
        with pytest.raises(ValidationError):
            MeasurementDefinition(**kwargs)

    def test_invalid_status_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["definition_status"] = "NOT_A_REAL_STATUS"
        with pytest.raises(ValidationError):
            MeasurementDefinition(**kwargs)

    def test_empty_required_landmarks_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["required_landmarks"] = []
        with pytest.raises(ValidationError):
            MeasurementDefinition(**kwargs)

    def test_unknown_field_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["mean"] = 82.0  # a normative concept, does not belong here
        with pytest.raises(ValidationError):
            MeasurementDefinition(**kwargs)


class TestNormativeProfileSchema:
    def _valid_kwargs(self, **overrides):
        base = dict(
            profile_id="EXAMPLE_PROFILE_V1",
            measurement_id="EXAMPLE_MEASUREMENT",
            measurement_definition_version="v1",
            reference_type=ReferenceType.MEAN_SD,
            unit="mm",
            mean=1.0,
            sd=0.5,
            age_dependency_type=AgeDependencyType.AGE_INDEPENDENT,
            sex=Sex.POOLED,
            population_id="EXAMPLE_POPULATION",
            source_id="example-source-2026",
            validation_status=ValidationStatus.LEGACY_UNVALIDATED,
            profile_version="v1",
            effective_from=datetime.date(2026, 1, 1),
            origin=_EXAMPLE_ORIGIN,
        )
        base.update(overrides)
        return base

    def test_valid_mean_sd_entry_accepted(self):
        NormativeProfile(**self._valid_kwargs())

    def test_missing_required_field_rejected(self):
        kwargs = self._valid_kwargs()
        del kwargs["population_id"]
        with pytest.raises(ValidationError):
            NormativeProfile(**kwargs)

    def test_source_id_is_optional(self):
        # Phase 2 legacy entries have no reviewed scientific source yet —
        # source_id must be omittable, not forced to a placeholder string.
        kwargs = self._valid_kwargs()
        del kwargs["source_id"]
        profile = NormativeProfile(**kwargs)
        assert profile.source_id is None

    def test_invalid_validation_status_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["validation_status"] = "APPROVED"  # not a real status value
        with pytest.raises(ValidationError):
            NormativeProfile(**kwargs)

    def test_mean_sd_reference_type_requires_mean_and_sd(self):
        kwargs = self._valid_kwargs()
        kwargs["sd"] = None
        with pytest.raises(ValidationError):
            NormativeProfile(**kwargs)

    def test_fixed_range_reference_type_requires_range(self):
        kwargs = self._valid_kwargs(reference_type=ReferenceType.FIXED_RANGE, mean=None, sd=None)
        with pytest.raises(ValidationError):
            NormativeProfile(**kwargs)
        kwargs["range"] = (0.0, 2.0)
        NormativeProfile(**kwargs)

    def test_quarantined_status_is_a_representable_value(self):
        # The registry must be ABLE to represent a quarantined profile
        # (Wits_Appraisal, Angle_Nasolabial, Situation_B, Decalage_A_B) —
        # whether that quarantine is actually enforced at lookup time is a
        # Phase 3 concern, not tested here.
        kwargs = self._valid_kwargs(validation_status=ValidationStatus.QUARANTINED)
        NormativeProfile(**kwargs)


class TestClassificationRuleSchema:
    def _valid_kwargs(self, **overrides):
        base = dict(
            rule_id="EXAMPLE_RULE_V1",
            measurement_id="EXAMPLE_MEASUREMENT",
            measurement_definition_version="v1",
            thresholds=[0.0, 4.5],
            labels=["Classe III", "Classe I", "Classe II"],
            validation_status=ValidationStatus.LEGACY_UNVALIDATED,
            origin=_EXAMPLE_ORIGIN,
        )
        base.update(overrides)
        return base

    def test_valid_entry_accepted(self):
        ClassificationRule(**self._valid_kwargs())

    def test_labels_thresholds_count_mismatch_rejected(self):
        kwargs = self._valid_kwargs(labels=["Only one label"])
        with pytest.raises(ValidationError):
            ClassificationRule(**kwargs)

    def test_profile_id_and_source_id_are_optional(self):
        kwargs = self._valid_kwargs()
        rule = ClassificationRule(**kwargs)
        assert rule.profile_id is None
        assert rule.source_id is None


class TestPlausibilityBoundsSchema:
    def test_valid_entry_accepted(self):
        PlausibilityBounds(
            bounds_id="EXAMPLE_BOUNDS_V1", measurement_id="EXAMPLE_MEASUREMENT",
            hard_min=0.0, hard_max=100.0, soft_min=10.0, soft_max=50.0, origin=_EXAMPLE_ORIGIN,
        )

    def test_disordered_bounds_rejected(self):
        with pytest.raises(ValidationError):
            PlausibilityBounds(
                bounds_id="EXAMPLE_BOUNDS_V1", measurement_id="EXAMPLE_MEASUREMENT",
                hard_min=0.0, hard_max=100.0, soft_min=60.0, soft_max=50.0, origin=_EXAMPLE_ORIGIN,
            )

    def test_multiple_bounds_ids_may_share_one_measurement(self):
        # The same measurement can have more than one bounds origin (e.g.
        # the validator's own bound and a frontend card's duplicated hard
        # range) — bounds_id, not measurement_id, is what makes each unique.
        a = PlausibilityBounds(
            bounds_id="EXAMPLE_BOUNDS_ORIGIN_A", measurement_id="EXAMPLE_MEASUREMENT",
            hard_min=0.0, hard_max=100.0, soft_min=10.0, soft_max=50.0, origin=_EXAMPLE_ORIGIN,
        )
        b = PlausibilityBounds(
            bounds_id="EXAMPLE_BOUNDS_ORIGIN_B", measurement_id="EXAMPLE_MEASUREMENT",
            hard_min=5.0, hard_max=95.0, soft_min=15.0, soft_max=45.0, origin=_EXAMPLE_ORIGIN,
        )
        assert a.measurement_id == b.measurement_id
        assert a.bounds_id != b.bounds_id


# --- Loader error handling on malformed input ---

class TestLoaderRejectsMalformedEntries:
    def test_malformed_entry_raises_clear_error(self, tmp_path, monkeypatch):
        import backend.services.cephalo_normative_registry as registry_module

        bad_dir = tmp_path / "cephalometry"
        bad_dir.mkdir()
        (bad_dir / "measurement_definitions.yaml").write_text(
            "measurements:\n  - measurement_id: BAD\n    canonical_name: Bad\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(registry_module, "_DATA_DIR", bad_dir)

        with pytest.raises(ValueError, match="BAD"):
            registry_module.load_measurement_definitions()

    def test_missing_list_key_raises_clear_error(self, tmp_path, monkeypatch):
        import backend.services.cephalo_normative_registry as registry_module

        bad_dir = tmp_path / "cephalometry"
        bad_dir.mkdir()
        (bad_dir / "measurement_definitions.yaml").write_text("not_the_right_key: []\n", encoding="utf-8")
        monkeypatch.setattr(registry_module, "_DATA_DIR", bad_dir)

        with pytest.raises(ValueError, match="measurements"):
            registry_module.load_measurement_definitions()


# --- Duplicate-ID rejection: a scientific registry must fail loudly, never guess ---

class TestLoaderRejectsDuplicateIds:
    _VALID_DEF = (
        "measurements:\n"
        "  - measurement_id: DUP\n"
        "    canonical_name: Dup\n"
        "    display_name: Dup\n"
        "    analysis_family: Test\n"
        "    unit: mm\n"
        "    definition_version: v1\n"
        "    required_landmarks: [A]\n"
        "    definition_status: ACTIVE\n"
        "    origin: {file: x.py, symbol: x, line: '1'}\n"
    )

    def test_duplicate_measurement_id_raises_clear_error(self, tmp_path, monkeypatch):
        import backend.services.cephalo_normative_registry as registry_module

        bad_dir = tmp_path / "cephalometry"
        bad_dir.mkdir()
        (bad_dir / "measurement_definitions.yaml").write_text(self._VALID_DEF + self._VALID_DEF.replace("measurements:\n", ""), encoding="utf-8")
        monkeypatch.setattr(registry_module, "_DATA_DIR", bad_dir)

        with pytest.raises(ValueError, match="duplicate measurement_id 'DUP'"):
            registry_module.load_measurement_definitions()

    def test_duplicate_profile_id_raises_clear_error(self, tmp_path, monkeypatch):
        import backend.services.cephalo_normative_registry as registry_module

        entry = (
            "  - profile_id: DUP\n"
            "    measurement_id: X\n"
            "    measurement_definition_version: v1\n"
            "    reference_type: MEAN_SD\n"
            "    unit: mm\n"
            "    mean: 1.0\n"
            "    sd: 0.5\n"
            "    age_dependency_type: AGE_INDEPENDENT\n"
            "    sex: POOLED\n"
            "    population_id: TEST\n"
            "    validation_status: LEGACY_UNVALIDATED\n"
            "    profile_version: v1\n"
            "    effective_from: '2026-01-01'\n"
            "    origin: {file: x.py, symbol: x, line: '1'}\n"
        )
        bad_dir = tmp_path / "cephalometry"
        bad_dir.mkdir()
        (bad_dir / "normative_profiles.yaml").write_text("profiles:\n" + entry + entry, encoding="utf-8")
        monkeypatch.setattr(registry_module, "_DATA_DIR", bad_dir)

        with pytest.raises(ValueError, match="duplicate profile_id 'DUP'"):
            registry_module.load_normative_profiles()

    def test_duplicate_rule_id_raises_clear_error(self, tmp_path, monkeypatch):
        import backend.services.cephalo_normative_registry as registry_module

        entry = (
            "  - rule_id: DUP\n"
            "    measurement_id: X\n"
            "    measurement_definition_version: v1\n"
            "    thresholds: [1.0]\n"
            "    labels: ['Low', 'High']\n"
            "    validation_status: LEGACY_UNVALIDATED\n"
            "    origin: {file: x.py, symbol: x, line: '1'}\n"
        )
        bad_dir = tmp_path / "cephalometry"
        bad_dir.mkdir()
        (bad_dir / "classification_rules.yaml").write_text("rules:\n" + entry + entry, encoding="utf-8")
        monkeypatch.setattr(registry_module, "_DATA_DIR", bad_dir)

        with pytest.raises(ValueError, match="duplicate rule_id 'DUP'"):
            registry_module.load_classification_rules()

    def test_duplicate_bounds_id_raises_clear_error(self, tmp_path, monkeypatch):
        import backend.services.cephalo_normative_registry as registry_module

        entry = (
            "  - bounds_id: DUP\n"
            "    measurement_id: X\n"
            "    hard_min: 0.0\n"
            "    hard_max: 100.0\n"
            "    soft_min: 10.0\n"
            "    soft_max: 50.0\n"
            "    origin: {file: x.py, symbol: x, line: '1'}\n"
        )
        bad_dir = tmp_path / "cephalometry"
        bad_dir.mkdir()
        (bad_dir / "plausibility_bounds.yaml").write_text("bounds:\n" + entry + entry, encoding="utf-8")
        monkeypatch.setattr(registry_module, "_DATA_DIR", bad_dir)

        with pytest.raises(ValueError, match="duplicate bounds_id 'DUP'"):
            registry_module.load_plausibility_bounds()


# --- Isolation guard: nothing existing consumes this module yet ---

class TestPhase1IsolationGuard:
    # CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-STEINER-4A intentionally wired
    # cephalo_engine.py and bilan_ortho_engine.py to the normative service
    # for SNA/SNB/ANB, and CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-
    # FRANCFORT-4C wired ai_advisor.py for Angle_de_Tweed/IMPA/I_Francfort —
    # all three are excluded from this "must stay isolated" list on purpose.
    # Everything else must remain at zero references.
    _CONSUMER_FILES = [
        "backend/services/cephalo_consistency_validator.py",
    ]

    def test_no_unwired_backend_consumer_imports_the_registry(self):
        for rel_path in self._CONSUMER_FILES:
            text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
            assert "cephalo_normative" not in text, (
                f"{rel_path} references the normative registry/schema — "
                "it must stay unwired (not part of the Steiner SNA/SNB/ANB wiring)."
            )
