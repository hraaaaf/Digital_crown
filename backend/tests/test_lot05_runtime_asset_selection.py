"""LOT05 J10D: only production scientific model weights enter an installer.

Synthetic bytes: checks selection policy, not scientific model validity.
"""
from pathlib import Path

import pytest

from backend.runtime_asset_certification import (
    RUNTIME_MODEL_ALLOWLIST,
    ASSET_SELECTION_POLICY_VERSION,
    iter_runtime_asset_files,
    require_v15_installable_model_coverage,
    RuntimeAssetCertificationError,
)


def test_v15_installer_selects_only_one_cephalo_and_panoramic_model(tmp_path: Path):
    paths = {
        "srpose38-tta-1024.onnx": b"srpose",
        "panoramic_model.onnx": b"panoramic",
        "best.onnx": b"orphan",
        "best.pt": b"orphan",
        "panoramic_model.pt": b"training",
        "ceph_weights.pth": b"legacy",
        "cephld_cca/ceph_weights.pth": b"legacy",
        "cephld_cca/model/checkpoint.pth": b"training",
        "nested/srpose38-tta-1024.onnx": b"copy",
        "srpose38-tta-1024.onnx.backup": b"copy",
    }
    for name, data in paths.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    selected = {path.relative_to(tmp_path).as_posix() for path in iter_runtime_asset_files(tmp_path)}
    assert selected == {"srpose38-tta-1024.onnx", "panoramic_model.onnx"}
    assert selected == RUNTIME_MODEL_ALLOWLIST
    assert ASSET_SELECTION_POLICY_VERSION == 2


def test_empty_or_orphan_only_asset_root_selects_nothing(tmp_path: Path):
    (tmp_path / "best.onnx").write_bytes(b"orphan")
    (tmp_path / "ceph_weights.pth").write_bytes(b"legacy")
    assert list(iter_runtime_asset_files(tmp_path)) == []


def test_symlink_to_scientific_weight_is_not_packed(tmp_path: Path):
    source = tmp_path / "best.onnx"
    source.write_bytes(b"orphan")
    target = tmp_path / "srpose38-tta-1024.onnx"
    try:
        target.symlink_to(source.name)
    except (OSError, NotImplementedError):
        return  # Unprivileged Windows setup may disallow symlinks.
    assert list(iter_runtime_asset_files(tmp_path)) == []


def test_complete_v15_installer_rejects_unpinned_panoramic():
    registry = {"assets": [
        {
            "id": "cephalo_sota",
            "canonical_path": "backend/ai_models/srpose38-tta-1024.onnx",
            "sha256": "a" * 64,
            "size_bytes": 123,
        },
        {"id": "panoramic", "lifecycle": "external"},
    ]}
    paths = {"backend/ai_models/srpose38-tta-1024.onnx"}
    with pytest.raises(RuntimeAssetCertificationError, match="not scientifically pinned: panoramic"):
        require_v15_installable_model_coverage(registry, paths)


def test_complete_v15_installer_requires_both_pinned_files():
    registry = {"assets": [
        {
            "id": "cephalo_sota",
            "canonical_path": "backend/ai_models/srpose38-tta-1024.onnx",
            "sha256": "a" * 64,
            "size_bytes": 123,
        },
        {
            "id": "panoramic",
            "canonical_path": "backend/ai_models/panoramic_model.onnx",
            "sha256": "b" * 64,
            "size_bytes": 456,
        },
    ]}
    with pytest.raises(RuntimeAssetCertificationError, match="missing from bundle: panoramic"):
        require_v15_installable_model_coverage(registry, {"backend/ai_models/srpose38-tta-1024.onnx"})

    require_v15_installable_model_coverage(
        registry,
        {
            "backend/ai_models/srpose38-tta-1024.onnx",
            "backend/ai_models/panoramic_model.onnx",
        },
    )
