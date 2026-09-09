import os
from pathlib import Path

from backend.services.disaster_recovery_service import BUNDLE_PREFIX, DisasterRecoveryService


def _verified_pair(root: Path, name: str, *, mtime: int) -> Path:
    bundle = root / name
    bundle.write_bytes(name.encode("utf-8"))
    sidecar = bundle.with_name(bundle.name + ".sha256")
    sidecar.write_text(f"{'a' * 64}  {bundle.name}\n", encoding="utf-8")
    os.utime(bundle, (mtime, mtime))
    os.utime(sidecar, (mtime, mtime))
    return bundle


def test_retention_never_lets_crash_orphan_evict_verified_generation(tmp_path):
    valid_old = _verified_pair(
        tmp_path,
        f"{BUNDLE_PREFIX}20260101T000000Z-valid-old.dcbundle",
        mtime=100,
    )
    valid_new = _verified_pair(
        tmp_path,
        f"{BUNDLE_PREFIX}20260102T000000Z-valid-new.dcbundle",
        mtime=200,
    )
    orphan = tmp_path / f"{BUNDLE_PREFIX}20990101T000000Z-crash-orphan.dcbundle"
    orphan.write_bytes(b"interrupted-after-promotion-before-sidecar")
    os.utime(orphan, (999, 999))

    removed = DisasterRecoveryService._cleanup_verified_bundles(tmp_path, keep=1)

    assert orphan.exists()
    assert not DisasterRecoveryService._is_verified_pair(orphan)
    assert valid_new.exists()
    assert DisasterRecoveryService._is_verified_pair(valid_new)
    assert not valid_old.exists()
    assert removed == [valid_old.name]


def test_malformed_sidecar_is_not_a_verified_retention_marker(tmp_path):
    bundle = tmp_path / f"{BUNDLE_PREFIX}20260103T000000Z-malformed.dcbundle"
    bundle.write_bytes(b"candidate")
    bundle.with_name(bundle.name + ".sha256").write_text("not-a-digest\n", encoding="utf-8")

    assert DisasterRecoveryService._is_verified_pair(bundle) is False
