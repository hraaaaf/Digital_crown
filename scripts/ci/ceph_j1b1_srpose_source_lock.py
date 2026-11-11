"""J1.B1 scientific source-lock: inspect exact upstream numeric labels, NEVER infer anatomy.

Nonclinical CI proof only. No model, X-ray, patient, clinical inference, download
of weights, clinical interpretation, or runtime activation.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request

SOURCE_COMMIT = "18d17d1934970016e7610c4849311900b8d1f191"
SOURCE_BLOB_SHA1 = "82d4fffcc0c74736edc43a12110bed322b67e839"
SOURCE_PATH = "mmpose_package/mmpose/configs/_base_/datasets/cephalometric.py"
SOURCE_URL = (
    "https://raw.githubusercontent.com/5k5000/CLdetection2023/"
    + SOURCE_COMMIT + "/" + SOURCE_PATH
)
MODEL_NAME = "srpose38-tta-1024.onnx"
MODEL_SHA256 = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
MODEL_SIZE = 267_484_931
MODEL_CHECKPOINT_SHA256 = "fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc"


class SourceLockError(RuntimeError):
    """No evidence means no clinical or anatomical promotion."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceLockError(message)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _upstream_labels(raw: bytes, *, expected_blob: str = SOURCE_BLOB_SHA1) -> dict:
    require(git_blob_sha1(raw) == expected_blob, "UPSTREAM_BLOB_IDENTITY_DRIFT")
    try:
        tree = ast.parse(raw.decode("utf-8"))
        outer = next(
            node.value for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "dataset_info" for t in node.targets)
        )
        require(isinstance(outer, ast.Call) and isinstance(outer.func, ast.Name)
                and outer.func.id == "dict", "UPSTREAM_CONFIG_SHAPE_DRIFT")
        keypoints = next(k.value for k in outer.keywords if k.arg == "keypoint_info")
        labels = ast.literal_eval(keypoints)
    except (ValueError, TypeError, StopIteration, SyntaxError, UnicodeError) as exc:
        raise SourceLockError(f"UPSTREAM_SOURCE_UNREADABLE: {exc}") from exc
    require(isinstance(labels, dict) and set(labels) == set(range(38)),
            "UPSTREAM_38_CHANNEL_INDICES_CHANGED")
    for idx in range(38):
        point = labels[idx]
        require(isinstance(point, dict) and point.get("id") == idx
                and point.get("name") == str(idx), f"UPSTREAM_CHANNEL_{idx}_NOT_NUMERIC")
    return labels


def _literal_name(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values = [
        node.value for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(isinstance(t, ast.Name) and t.id == name
                for t in (node.targets if isinstance(node, ast.Assign) else [node.target]))
    ]
    require(len(values) == 1, f"MISSING_OR_AMBIGUOUS_CONSTANT_{name}")
    return ast.literal_eval(values[0])


def _current_aliases() -> tuple[dict[int, str], dict]:
    contract = Path("backend/services/srpose38_contract.py")
    require(contract.is_file(), "RUNTIME_CONTRACT_MISSING")
    mapping = _literal_name(contract, "SOTA_LANDMARKS_MAPPING")
    require(isinstance(mapping, dict) and set(mapping) == set(range(38)),
            "RUNTIME_INDEX_SET_DRIFT")
    require(all(isinstance(v, str) and v for v in mapping.values())
            and len(set(mapping.values())) == 38, "RUNTIME_ALIAS_IDENTITY_DRIFT")
    require(_literal_name(contract, "SRPOSE38_MODEL_NAME") == MODEL_NAME, "MODEL_NAME_DRIFT")
    require(_literal_name(contract, "SRPOSE38_MODEL_SHA256") == MODEL_SHA256, "MODEL_SHA_DRIFT")
    require(_literal_name(contract, "SRPOSE38_MODEL_SIZE_BYTES") == MODEL_SIZE, "MODEL_SIZE_DRIFT")

    registry = json.loads(Path("backend/scientific_assets.json").read_text(encoding="utf-8"))
    assets = [item for item in registry.get("assets", []) if item.get("id") == "cephalo_sota"]
    require(len(assets) == 1, "SCIENTIFIC_REGISTRY_MODEL_MISSING_OR_DUPLICATED")
    asset = assets[0]
    require(asset.get("canonical_path") == f"backend/ai_models/{MODEL_NAME}"
            and asset.get("sha256") == MODEL_SHA256
            and asset.get("size_bytes") == MODEL_SIZE, "SCIENTIFIC_REGISTRY_PIN_DRIFT")
    require(asset.get("anatomical_mapping_validation") == "SOURCE_LOCK_REQUIRED",
            "UNSUPPORTED_ANATOMICAL_VALIDATION_CLAIM")
    require(asset.get("clinical_activation_authorized") is False,
            "UNSUPPORTED_CLINICAL_ACTIVATION_CLAIM")
    require("NOT independently source-verified" in asset.get("note", ""),
            "SCIENTIFIC_REGISTRY_LEGACY_VALIDATED_CLAIM")
    provenance = asset.get("provenance") or {}
    require(provenance.get("source_commit") == SOURCE_COMMIT
            and provenance.get("checkpoint_sha256") == MODEL_CHECKPOINT_SHA256,
            "CHECKPOINT_PROVENANCE_DRIFT")
    return mapping, asset


def _check_documented_legacy_aliases(mapping: dict[int, str]) -> None:
    doc = Path("docs/SRPOSE38_LANDMARK_CONTRACT.md").read_text(encoding="utf-8")
    require("LEGACY_AUTO_UNVERIFIED / SOURCE_LOCK_REQUIRED" in doc
            and "NON CERTIFIÉS" in doc and "activation clinique en HOLD" in doc,
            "DOCUMENT_SOURCE_LOCK_NOT_DECLARED")
    rows = re.findall(r"^\|(\d+)\|(\d+)\|([^|]+)\|([^|]+)\|$", doc, flags=re.M)
    require(len(rows) == 38, "DOCUMENT_38_ROW_COUNT_DRIFT")
    for expected, (idx, challenge_number, description, legacy_alias) in enumerate(rows):
        require(int(idx) == expected and int(challenge_number) == expected + 1,
                "DOCUMENT_NUMERIC_ORDER_DRIFT")
        require(legacy_alias.strip() == mapping[expected],
                f"DOCUMENT_ALIAS_DRIFT_AT_INDEX_{expected}")
        require(bool(description.strip()), f"DOCUMENT_EMPTY_DESCRIPTION_{expected}")


def selftest() -> None:
    # Negative test: fake upstream names cannot pass a forged/non-matching blob.
    raw = b"dataset_info=dict(keypoint_info={0:{'name':'S','id':0}})\n"
    try:
        _upstream_labels(raw)
    except SourceLockError as exc:
        require("UPSTREAM_BLOB_IDENTITY_DRIFT" in str(exc), "NEGATIVE_BLOB_GATE_WRONG_ERROR")
    else:
        raise SourceLockError("NEGATIVE_BLOB_GATE_BYPASS")
    # Even if the SHA pin were changed to this one-point fixture, the 38-channel
    # numeric contract still refuses the source, never invents 37 missing labels.
    try:
        _upstream_labels(raw, expected_blob=git_blob_sha1(raw))
    except SourceLockError as exc:
        require("UPSTREAM_38_CHANNEL_INDICES_CHANGED" in str(exc),
                "NEGATIVE_38_LABEL_GATE_WRONG_ERROR")
    else:
        raise SourceLockError("NEGATIVE_38_LABEL_GATE_BYPASS")
    print("J1B1_SOURCE_LOCK_NEGATIVE_SOURCE_AND_CHANNEL_GATES_PASS")


def run(output_path: Path) -> None:
    mapping, _ = _current_aliases()
    _check_documented_legacy_aliases(mapping)
    request = urllib.request.Request(
        SOURCE_URL, headers={"User-Agent": "DigitalCrown-J1B1-nonclinical-source-lock"}
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            original_bytes = response.read(100_000)
    except Exception as exc:
        raise SourceLockError(f"PINNED_SOURCE_UNAVAILABLE_FAIL_CLOSED: {exc}") from exc
    _upstream_labels(original_bytes)
    rows = [{
        "runtime_index": i,
        "challenge_numeric_id": i + 1,
        "upstream_source_label": str(i),
        "legacy_local_alias_NOT_ATTESTED": mapping[i],
        "index_to_anatomy_status": "SOURCE_LOCK_REQUIRED",
        "source_to_anatomy_direct_evidence": None,
        "clinical_use_authorized": False,
    } for i in range(38)]
    report = {
        "lot": "CEPH-J1.B1-S1",
        "source_commit": SOURCE_COMMIT,
        "source_blob_sha1_verified": git_blob_sha1(original_bytes),
        "source_exact_path": SOURCE_PATH,
        "onnx_model_sha256_from_registry_not_rehashed": MODEL_SHA256,
        "channel_count": len(rows),
        "upstream_label_mode": "numeric_0_through_37",
        "number_of_anatomical_mappings_source_verified": 0,
        "anatomical_mapping_status": "SOURCE_LOCK_REQUIRED",
        "clinical_activation_authorized": False,
        "clinical_release": False,
        "patient_data_used": False,
        "onnx_model_downloaded": False,
        "inference_performed": False,
        "notes": "Source verifies channel numbering, NOT anatomy. Local aliases remain unreviewed hypotheses.",
        "channels": rows,
    }
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("J1B1_PINNED_UPSTREAM_NUMERIC_38_SOURCE_AND_LOCAL_CONTRACT_PASS")
    print("J1B1_ANATOMICAL_MAPPING_HOLD_38_OF_38_NO_CLINICAL_GO")
    print(json.dumps({k: v for k, v in report.items() if k != "channels"}, sort_keys=True))


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("action", choices=("selftest", "verify"))
        parser.add_argument("--report", default="j1b1-source-lock-metadata.json")
        args = parser.parse_args()
        selftest()
        if args.action == "verify":
            run(Path(args.report))
    except (OSError, SourceLockError, ValueError, SyntaxError) as exc:
        print(f"J1B1_SOURCE_LOCK_FAIL_CLOSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
