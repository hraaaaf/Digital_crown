from __future__ import annotations

import plistlib
from pathlib import Path

from backend.services.macos_update_apply import (
    MACOS_APP_NAME,
    MACOS_BUNDLE_ID,
    MACOS_EXECUTABLE_REL,
    MacOSUpdateApplyService,
)
from backend.services.update_engine import UpdatePreparationError


PRIVATE_TRUST_MODE = "signed-manifest+adhoc-codesign-v1"


def _verify_private_app_bundle(cls, app: Path, *, expected_version: str) -> dict[str, str]:
    """Verify a private-distribution app without paid Apple Developer credentials.

    Authenticity of the update artifact is provided by Digital Crown's already-signed
    update manifest + exact SHA-256. macOS ad-hoc code signing is used as an additional
    bundle-integrity check, not as a public publisher identity claim.
    """
    if not app.is_dir() or app.name != MACOS_APP_NAME:
        raise UpdatePreparationError("UPDATE_MACOS_DMG_APP_MISSING")
    info_path = app / "Contents" / "Info.plist"
    executable = app / MACOS_EXECUTABLE_REL
    if not info_path.is_file() or not executable.is_file():
        raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_INVALID")
    try:
        info = plistlib.loads(info_path.read_bytes())
    except Exception as exc:
        raise UpdatePreparationError("UPDATE_MACOS_INFO_PLIST_INVALID") from exc
    if info.get("CFBundleIdentifier") != MACOS_BUNDLE_ID:
        raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_ID_MISMATCH")
    if str(info.get("CFBundleShortVersionString") or "") != expected_version:
        raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_VERSION_MISMATCH")

    cls._run_checked(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=4", str(app)],
        "UPDATE_MACOS_PRIVATE_CODESIGN_VERIFY_FAILED",
    )
    details = cls._run_checked(
        ["/usr/bin/codesign", "-d", "--verbose=4", str(app)],
        "UPDATE_MACOS_PRIVATE_CODESIGN_DETAILS_FAILED",
    )
    # A paid Developer ID is intentionally not required. Ad-hoc signatures report
    # Signature=adhoc; reject unsigned or unexpectedly identity-signed bundles so the
    # private policy cannot silently drift into a different trust model.
    if "Signature=adhoc" not in details:
        raise UpdatePreparationError("UPDATE_MACOS_PRIVATE_ADHOC_SIGNATURE_REQUIRED")

    return {
        "bundle_id": MACOS_BUNDLE_ID,
        "version": expected_version,
        "developer_id": "not_required_private_distribution",
        "hardened_runtime": "not_claimed_private_distribution",
        "secure_timestamp": "not_required_private_distribution",
        "private_codesign": "adhoc_valid",
        "trust_mode": PRIVATE_TRUST_MODE,
    }


def _verify_private_distribution(cls, dmg: Path, *, expected_version: str) -> dict[str, str]:
    # The exact DMG bytes were already size/SHA-256 checked against the verified,
    # signed update manifest by _validate_prepared_job before this boundary.
    with cls._mounted_dmg(dmg) as mount:
        result = cls._verify_app_bundle(mount / MACOS_APP_NAME, expected_version=expected_version)
    result.update(
        notarization="not_required_private_distribution",
        gatekeeper="manual_first_launch_required",
    )
    return result


def install_private_macos_trust_policy() -> None:
    MacOSUpdateApplyService._verify_app_bundle = classmethod(_verify_private_app_bundle)
    MacOSUpdateApplyService._verify_macos_distribution = classmethod(_verify_private_distribution)


install_private_macos_trust_policy()
