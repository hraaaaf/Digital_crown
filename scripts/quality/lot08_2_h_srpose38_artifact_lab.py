"""LOT08.2-H — SRPose38 REAL existing artifact → isolated packaging selection FUE.

Only a GitHub-hosted disposable runner, with externally retrieved pinned ONNX.
No redistribution, build of installer, clinical data, or certification is allowed.
Scientific landmark mapping and commercial model-weight licensing remain HOLD.
"""
from __future__ import annotations

import argparse
from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

MODEL = "srpose38-tta-1024.onnx"
EXPECTED_SIZE = 267_484_931
EXPECTED_HASH = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
EXACT_CODE_SHA = "bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4"
UPSTREAM_RUN_ID = 34281082926
UPSTREAM_ARTIFACT_ID = 10077697721
UPSTREAM_ARTIFACT_SHA = "ad1caa8ee1474a1405305fc91a29eaa3c0c5b20572095faad0c2e63723284e17"


class UnsafeAsset(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as reader:
        for chunk in iter(lambda: reader.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_single_file(root: Path, name: str, size: int, digest: str) -> Path:
    """Reject symlinks, nested files, unexpected extras, corrupt or stale bytes."""
    if not root.is_dir() or root.is_symlink():
        raise UnsafeAsset("SOURCE_ROOT_NOT_DIRECTORY_OR_SYMLINK")
    entries = list(root.iterdir())
    if len(entries) != 1 or entries[0].name != name:
        raise UnsafeAsset("SOURCE_NOT_SINGLE_EXPECTED_ONNX")
    candidate = entries[0]
    if candidate.is_symlink() or not stat.S_ISREG(candidate.lstat().st_mode):
        raise UnsafeAsset("MODEL_NOT_REGULAR_FILE")
    if candidate.stat().st_size != size:
        raise UnsafeAsset("MODEL_SIZE_PIN_MISMATCH")
    if sha256(candidate) != digest:
        raise UnsafeAsset("MODEL_SHA256_PIN_MISMATCH")
    return candidate


def assert_registry_identity(registry: Path) -> None:
    from backend.services.srpose38_contract import (
        SRPOSE38_MODEL_NAME, SRPOSE38_MODEL_SHA256, SRPOSE38_MODEL_SIZE_BYTES,
    )
    if (SRPOSE38_MODEL_NAME, SRPOSE38_MODEL_SHA256, SRPOSE38_MODEL_SIZE_BYTES) != (
        MODEL, EXPECTED_HASH, EXPECTED_SIZE
    ):
        raise UnsafeAsset("RUNTIME_CONTRACT_DIFFERS_FROM_PIN")
    data = json.loads(registry.read_text(encoding="utf-8"))
    if data.get("asset_policy") != "external-not-versioned":
        raise UnsafeAsset("REGISTRY_UNEXPECTED_POLICY")
    matches = [a for a in data.get("assets", []) if a.get("id") == "cephalo_sota"]
    if len(matches) != 1:
        raise UnsafeAsset("REGISTRY_MISSING_UNIQUE_SRPOSE38")
    asset = matches[0]
    if (
        asset.get("canonical_path") != "backend/ai_models/" + MODEL
        or asset.get("size_bytes") != EXPECTED_SIZE
        or asset.get("sha256") != EXPECTED_HASH
        or asset.get("runtime_provider") != "CPUExecutionProvider"
    ):
        raise UnsafeAsset("REGISTRY_SRPOSE38_PIN_CHANGED")


def assert_packaging_selection(model_path: Path, registry: Path) -> dict:
    """Reproduce the exact DigitalCrown.spec file selector in a disposable tree."""
    from backend.runtime_asset_certification import (
        iter_runtime_asset_files, verify_pinned_registry_assets,
    )
    with tempfile.TemporaryDirectory(prefix="lot08h-runtime-selector-") as tmp:
        root = Path(tmp)
        model_root = root / "backend" / "ai_models"
        model_root.mkdir(parents=True)
        shutil.copyfile(model_path, model_root / MODEL)
        shutil.copyfile(registry, root / "backend" / "scientific_assets.json")
        selected = list(iter_runtime_asset_files(model_root))
        if [p.relative_to(model_root).as_posix() for p in selected] != [MODEL]:
            raise UnsafeAsset("PYINSTALLER_ASSET_SELECTOR_MISMATCH")
        pinned, unpinned = verify_pinned_registry_assets(root)
        if "cephalo_sota" not in pinned:
            raise UnsafeAsset("REAL_MODEL_REGISTRY_PIN_NOT_VERIFIED")
        if sorted(unpinned) != ["cephalo_legacy", "panoramic"]:
            raise UnsafeAsset("REGISTRY_UNPINNED_LIST_CHANGED")
        if sha256(selected[0]) != EXPECTED_HASH:
            raise UnsafeAsset("COPIED_MODEL_BYTES_CHANGED")
        return {"selected_files": 1, "pinned_verified": pinned, "scientifically_unpinned": unpinned}


def real_cpu_load_and_synthetic_inference(model_path: Path) -> tuple[list[int], list[int]]:
    import numpy as np
    import onnxruntime as ort

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    opts.inter_op_num_threads = 1
    session = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])
    if session.get_providers() != ["CPUExecutionProvider"]:
        raise UnsafeAsset("PROVIDER_NOT_CPU_ONLY")
    inputs, outputs = session.get_inputs(), session.get_outputs()
    if len(inputs) != 1 or len(outputs) != 1:
        raise UnsafeAsset("ONNX_IO_CONTRACT_CHANGED")
    if list(inputs[0].shape) != [1, 3, 1024, 1024] or inputs[0].type != "tensor(float)":
        raise UnsafeAsset("ONNX_INPUT_CONTRACT_CHANGED")
    dummy = np.zeros((1, 3, 1024, 1024), dtype=np.float32)
    result = session.run(None, {inputs[0].name: dummy})
    if len(result) != 1 or result[0].ndim != 4 or tuple(result[0].shape[:2]) != (1, 38):
        raise UnsafeAsset("ONNX_HEATMAP_CONTRACT_CHANGED")
    if not np.isfinite(result[0]).all():
        raise UnsafeAsset("ONNX_SYNTHETIC_NONFINITE_HEATMAPS")
    return list(dummy.shape), list(result[0].shape)


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="lot08h-negative-") as tmp:
        root = Path(tmp)
        for expected in ("SOURCE_NOT_SINGLE_EXPECTED_ONNX", "MODEL_SIZE_PIN_MISMATCH", "MODEL_SHA256_PIN_MISMATCH"):
            if expected == "SOURCE_NOT_SINGLE_EXPECTED_ONNX":
                (root / "unexpected").write_bytes(b"no")
                call = lambda: assert_single_file(root, MODEL, 3, "a" * 64)
            else:
                (root / "unexpected").unlink(missing_ok=True)
                (root / MODEL).write_bytes(b"abc")
                call = (lambda: assert_single_file(root, MODEL, 99, "a"*64)) if expected == "MODEL_SIZE_PIN_MISMATCH" else (lambda: assert_single_file(root, MODEL, 3, "a"*64))
            try:
                call()
            except UnsafeAsset as err:
                if str(err) != expected:
                    raise
            else:
                raise UnsafeAsset("NEGATIVE_GATE_ACCEPTED_UNSAFE_ASSET")
            with suppress(FileNotFoundError):
                (root / MODEL).unlink()
        target = root / "target"
        target.write_bytes(b"abc")
        one = root / "isolated-source"
        one.mkdir()
        alias = one / MODEL
        try:
            alias.symlink_to(target)
        except (OSError, NotImplementedError):
            pass
        else:
            try:
                assert_single_file(one, MODEL, 3, hashlib.sha256(b"abc").hexdigest())
            except UnsafeAsset as err:
                if str(err) != "MODEL_NOT_REGULAR_FILE":
                    raise
            else:
                raise UnsafeAsset("SYMLINK_ACCEPTED")
    print("LOT08H_NEGATIVE_FILE_SIZE_DIGEST_SYMLINK_GATES_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument("--registry", type=Path, default=Path("backend/scientific_assets.json"))
    parser.add_argument("--expected-code-sha", default=EXACT_CODE_SHA)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--negative-only", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.negative_only:
        return 0

    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
        raise UnsafeAsset("EPHEMERAL_GITHUB_RUNNER_REQUIRED")
    if args.expected_code_sha != EXACT_CODE_SHA:
        raise UnsafeAsset("CERTIFIED_MASTER_SHA_CHANGED")
    if args.artifact_dir is None:
        raise UnsafeAsset("REAL_ARTIFACT_DIR_REQUIRED")
    assert_registry_identity(args.registry)
    model = assert_single_file(args.artifact_dir, MODEL, EXPECTED_SIZE, EXPECTED_HASH)
    selection = assert_packaging_selection(model, args.registry)
    input_shape, output_shape = real_cpu_load_and_synthetic_inference(model)
    report = {
        "lot": "08.2-H",
        "code_certified_master_sha": EXACT_CODE_SHA,
        "source_run_id": UPSTREAM_RUN_ID,
        "source_artifact_id": UPSTREAM_ARTIFACT_ID,
        "source_artifact_zip_sha256_metadata": UPSTREAM_ARTIFACT_SHA,
        "actual_onnx_sha256": EXPECTED_HASH,
        "actual_onnx_size_bytes": EXPECTED_SIZE,
        "cpu_execution_provider_verified": True,
        "synthetic_input_shape": input_shape,
        "synthetic_output_shape": output_shape,
        "pyinstaller_runtime_asset_selection": selection,
        "scientific_landmark_mapping_certified": False,
        "commercial_model_weight_redistribution_authorized": False,
        "runtime_asset_zip_emitted": False,
        "installer_built": False,
        "clinical_release": False,
        "installable_go": False,
        "test_data": "zero-only synthetic tensor; no patient images",
        "verdict": "LAB_MODEL_BYTES_AND_PACKAGING_SELECTOR_ONLY",
    }
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("LOT08H_REAL_SRPOSE38_ONNX_CPU_AND_SELECTOR_PASS_NONCLINICAL")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
