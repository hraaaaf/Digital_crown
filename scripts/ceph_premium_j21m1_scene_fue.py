"""Isolated J2.1-M1 FUE harness: load ONLY schema and pinned model constants.

The normal backend package has intentional runtime/model initialization side
effects, so this schema-only laboratory never imports it or creates a database.
Pydantic model code is loaded unchanged from the checkout on exact GitHub HEAD.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def namespace(name: str, relative: str):
    module = types.ModuleType(name)
    module.__path__ = [str(REPO / relative)]
    sys.modules[name] = module


def load_source(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load isolated source: {name}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run() -> int:
    namespace("backend", "backend")
    namespace("backend.services", "backend/services")
    namespace("backend.schemas", "backend/schemas")
    load_source(
        "backend.services.srpose38_contract",
        "backend/services/srpose38_contract.py",
    )
    contract = load_source(
        "backend.schemas.cephalo_premium_scene_contract",
        "backend/schemas/cephalo_premium_scene_contract.py",
    )
    test_path = REPO / "backend/tests/test_ceph_premium_j21m1_scene_contract.py"
    if pytest.main(["--noconftest", str(test_path), "-q", "--disable-warnings"]) != 0:
        return 1

    fixture = load_source(
        "dc_premium_j21m1_fue_fixture",
        "backend/tests/test_ceph_premium_j21m1_scene_contract.py",
    )
    scene = contract.CephaloPremiumSceneDraft.model_validate(fixture._scene())
    schema = contract.CephaloPremiumSceneDraft.model_json_schema()
    head = os.environ.get("PRODUCT_HEAD", "")
    if len(head) != 40 or not all(char in "0123456789abcdef" for char in head):
        raise RuntimeError("J2.1 FUE requires literal exact 40-hex HEAD")
    report = {
        "case_id": "CEPH-PREMIUM-J2.1-M1",
        "status": "NONCLINICAL_SCENE_SCHEMA_CONTRACT_PASS",
        "head": head,
        "schema_version": contract.SCENE_VERSION,
        "scene_sha256": scene.sha256(),
        "contract_source_sha256": hashlib.sha256(
            (REPO / "backend/schemas/cephalo_premium_scene_contract.py").read_bytes()
        ).hexdigest(),
        "landmark_count_synthetic": len(scene.landmarks),
        "pinned_model_sha256": scene.identity.detector_sha256,
        "mapping_authority": scene.identity.detector_mapping_authority,
        "immutable_value_contract": True,
        "malformed_and_unsafe_contract_inputs_rejected": True,
        "source_sha256_declared_not_authenticated": True,
        "real_source_bytes_verified": False,
        "study_media_runtime_binding": False,
        "scene_persistence_implemented": False,
        "actual_onnx_inference_executed": False,
        "clinical_release": False,
        "approved_contour_exists": False,
        "database_migration_executed": False,
        "production_endpoint_mounted": False,
    }
    evidence = Path(os.environ.get("CEPH_J21M1_EVIDENCE_DIR", "artifacts/j21m1"))
    evidence.mkdir(parents=True, exist_ok=True)
    for filename, payload in (
        ("j21m1-schema.json", schema),
        ("j21m1-synthetic-scene.json", scene.canonical_dict()),
        ("j21m1-report.json", report),
    ):
        (evidence / filename).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print("CEPH_J21M1_NONCLINICAL_FUE_PASS", json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
