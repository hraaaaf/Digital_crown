import pytest

from backend.services.cephalo_auto_calibration_gate import ValidatedFiducialProfile
from backend.services.cephalo_fiducial_profiles import (
    FiducialProfileRegistry,
    FiducialProfileRegistryError,
    validated_fiducial_profiles,
)


def _profile(*, version="1"):
    return ValidatedFiducialProfile(
        profile_id="VALIDATED_TEST_RULER",
        version=version,
        known_tick_spacing_mm=5.0,
        min_ticks=5,
        max_spacing_deviation_ratio=0.03,
        validation_reference=f"test-fixture://validated-ruler-{version}",
    )


def test_production_registry_contains_no_implicit_trusted_profile():
    assert validated_fiducial_profiles.profile_count == 0
    assert validated_fiducial_profiles.resolve(
        profile_id="VALIDATED_TEST_RULER", version="1"
    ) is None


def test_registry_requires_exact_profile_id_and_version():
    registry = FiducialProfileRegistry([_profile(version="1")])

    assert registry.resolve(profile_id="VALIDATED_TEST_RULER", version="1") == _profile(version="1")
    assert registry.resolve(profile_id="VALIDATED_TEST_RULER", version="2") is None
    assert registry.resolve(profile_id="", version="1") is None


def test_duplicate_profile_version_is_rejected():
    with pytest.raises(FiducialProfileRegistryError, match="duplicate"):
        FiducialProfileRegistry([_profile(), _profile()])
