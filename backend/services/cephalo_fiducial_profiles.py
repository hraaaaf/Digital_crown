"""Validated physical fiducial profile registry.

The production default is intentionally empty. A ruler profile may participate in
automatic calibration only after an explicit, versioned physical validation source
has been supplied by application configuration or a future validated integration.
"""
from __future__ import annotations

from collections.abc import Iterable

from backend.services.cephalo_auto_calibration_gate import ValidatedFiducialProfile


class FiducialProfileRegistryError(ValueError):
    pass


class FiducialProfileRegistry:
    def __init__(self, profiles: Iterable[ValidatedFiducialProfile] = ()) -> None:
        self._profiles: dict[tuple[str, str], ValidatedFiducialProfile] = {}
        for profile in profiles:
            key = (profile.profile_id, profile.version)
            if key in self._profiles:
                raise FiducialProfileRegistryError(
                    f"duplicate fiducial profile: {profile.profile_id}@{profile.version}"
                )
            self._profiles[key] = profile

    def resolve(self, *, profile_id: str, version: str) -> ValidatedFiducialProfile | None:
        if not isinstance(profile_id, str) or not profile_id.strip():
            return None
        if not isinstance(version, str) or not version.strip():
            return None
        return self._profiles.get((profile_id.strip(), version.strip()))

    @property
    def profile_count(self) -> int:
        return len(self._profiles)


# Safety default: no production fiducial is trusted merely because the detector
# found ruler-like geometry. Profiles must be introduced explicitly and audited.
validated_fiducial_profiles = FiducialProfileRegistry()
