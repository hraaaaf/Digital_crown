"""LOT08.2-J: Windows frozen PyInstaller *witness*, never a DigitalCrown build.

Non-clinical, no patient data, no inference, no installer. The actual production
DigitalCrown.spec INSTALLABLE_CERTIFIED gate remains unmodified and mandatory.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

NAME = "srpose38-tta-1024.onnx"
SHA256 = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
SIZE = 267_484_931
SOURCE_RUN = 34281082926
SOURCE_ID = 10077697721
SOURCE_RUN_SHA = "39e3779d993224abe54382e8cddf09c08fafe2a0"
SOURCE_ZIP_SHA = "sha256:ad1caa8ee1474a1405305fc91a29eaa3c0c5b20572095faad0c2e63723284e17"
SOURCE_ARCHIVE_SIZE = 267_491_984
SOURCE_FILES = {
    NAME, "srpose38-onnx.sha256", "srpose38-onnx-parity.json",
    "srpose38-onnx-parity.log", "srpose38-checkpoint.sha256",
    "srpose-source.sha", "challenge-sample-source.sha",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def check_file(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        fail("MODEL_MISSING_OR_SYMLINK")
    if path.stat().st_size != SIZE:
        fail("MODEL_SIZE_MISMATCH")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != SHA256:
        fail("MODEL_SHA256_MISMATCH")


def load_plain_module(path: Path, name: str):
    if not path.is_file() or path.is_symlink():
        fail("WITNESS_SOURCE_MODULE_MISSING_OR_SYMLINK")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        fail("WITNESS_SOURCE_MODULE_UNLOADABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preflight() -> None:
    spec = Path("DigitalCrown.spec").read_text(encoding="utf-8")
    if "verify_installable_release_directory(_CERTIFIED_RELEASE_ROOT)" not in spec:
        fail("PRODUCTION_INSTALLABLE_GATE_NOT_FOUND")
    if Path("installable-certification.json").exists() or Path("release-certification.json").exists():
        fail("UNEXPECTED_RELEASE_CERTIFICATION_IN_LAB")
    if Path("backend/ai_models") .joinpath(NAME).exists():
        fail("UNEXPECTED_MODEL_IN_GIT_CHECKOUT")
    if not Path("backend/services/cephalo_runtime_gate.py").is_file():
        fail("CLINICAL_GATE_SOURCE_MISSING")
    print("LOT08J_PRODUCTION_SPEC_GATE_PRESERVED_NO_RELEASE_BUILD")


def source(source_dir: Path, run_json: Path, artifact_json: Path) -> None:
    run = json.loads(run_json.read_text(encoding="utf-8-sig"))
    artifact = json.loads(artifact_json.read_text(encoding="utf-8-sig"))
    if (run.get("id"), run.get("head_sha"), run.get("status"), run.get("conclusion")) != (
        SOURCE_RUN, SOURCE_RUN_SHA, "completed", "success"
    ):
        fail("UNTRUSTED_SOURCE_RUN")
    if (
        artifact.get("id") != SOURCE_ID
        or artifact.get("name") != "cephalo-srpose38-onnx-parity"
        or artifact.get("expired") is not False
        or artifact.get("digest") != SOURCE_ZIP_SHA
        or artifact.get("size_in_bytes") != SOURCE_ARCHIVE_SIZE
        or (artifact.get("workflow_run") or {}).get("head_sha") != SOURCE_RUN_SHA
    ):
        fail("UNTRUSTED_SOURCE_ARTIFACT")
    actual = list(source_dir.iterdir())
    if len(actual) != len(SOURCE_FILES) or {p.name for p in actual} != SOURCE_FILES:
        fail("UNEXPECTED_SOURCE_SEVEN_FILE_SET")
    if any(not p.is_file() or p.is_symlink() for p in actual):
        fail("NONREGULAR_SOURCE_FILE")
    if (source_dir / "srpose38-onnx.sha256").read_text(encoding="utf-8").strip() != f"{SHA256}  {NAME}":
        fail("SOURCE_MANIFEST_DRIFT")
    check_file(source_dir / NAME)
    registry = json.loads(Path("backend/scientific_assets.json").read_text(encoding="utf-8"))
    pins = [a for a in registry["assets"] if a.get("id") == "cephalo_sota"]
    if len(pins) != 1 or (pins[0].get("sha256"), pins[0].get("size_bytes"), pins[0].get("canonical_path")) != (
        SHA256, SIZE, f"backend/ai_models/{NAME}"
    ):
        fail("SCIENTIFIC_REGISTRY_PIN_DRIFT")
    selected = Path("backend/ai_models") / NAME
    selected.parent.mkdir(exist_ok=True, parents=True)
    shutil.copyfile(source_dir / NAME, selected)
    check_file(selected)
    selector = load_plain_module(Path("backend/runtime_asset_certification.py"), "lot08j_production_selector")
    files = list(selector.iter_runtime_asset_files(selected.parent))
    if len(files) != 1 or files[0].resolve() != selected.resolve():
        fail("PRODUCTION_ASSET_SELECTOR_DRIFT")
    print("LOT08J_SOURCE_RUN_ARTIFACT_PIN_AND_REAL_MODEL_SELECTOR_PASS")


def frozen() -> None:
    if not getattr(sys, "frozen", False) or not hasattr(sys, "_MEIPASS"):
        fail("NOT_A_REAL_FROZEN_WINDOWS_PROCESS")
    root = Path(sys._MEIPASS).resolve()
    model = root / "backend" / "ai_models" / NAME
    check_file(model)
    contract = load_plain_module(root / "backend/services/srpose38_contract.py", "lot08j_contract")
    if (contract.SRPOSE38_MODEL_NAME, contract.SRPOSE38_MODEL_SHA256, contract.SRPOSE38_MODEL_SIZE_BYTES) != (
        NAME, SHA256, SIZE
    ):
        fail("PACKAGED_CONTRACT_PIN_DRIFT")
    selector = load_plain_module(root / "backend/runtime_asset_certification.py", "lot08j_selector")
    selected = list(selector.iter_runtime_asset_files(root / "backend/ai_models"))
    if len(selected) != 1 or selected[0].resolve() != model.resolve():
        fail("PACKAGED_PRODUCTION_SELECTOR_DRIFT")
    gate = load_plain_module(root / "backend/services/cephalo_runtime_gate.py", "lot08j_clinical_gate")
    if gate.can_run_cephalo_auto_inference():
        fail("FROZEN_PRODUCTION_CLINICAL_GATE_OPEN")
    os.environ.update({
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite:///:memory:",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "GITHUB_ACTIONS": "true",
    })
    if gate.can_run_cephalo_auto_inference():
        fail("FROZEN_CLINICAL_GATE_BYPASS_BY_ENVIRONMENT")
    print(json.dumps({
        "lot": "08.2-J",
        "witness_os": sys.platform,
        "actually_frozen": True,
        "model_embedded_in_frozen_bundle": True,
        "model_size_bytes": SIZE,
        "model_sha256": SHA256,
        "selected_models": 1,
        "clinical_gate_deny_production": True,
        "clinical_gate_deny_even_lab_flags": True,
        "model_inference_executed": False,
        "patient_data_used": False,
        "actual_digitalcrown_app_exe": False,
        "installable_certified": False,
        "clinical_release": False,
    }, sort_keys=True))


def tamper(model: Path) -> None:
    check_file(model)
    with model.open("r+b") as stream:
        stream.seek(4096)
        value = stream.read(1)
        if len(value) != 1:
            fail("TAMPER_POSITION_INVALID")
        stream.seek(4096)
        stream.write(bytes((value[0] ^ 0x01,)))
    if model.stat().st_size != SIZE:
        fail("TAMPER_SHOULD_PRESERVE_SIZE")
    print("LOT08J_TEST_PACKAGE_BYTE_TAMPERED_EXPECT_FROZEN_DENIAL")


def report(witness_json: Path, failed_run_output: Path) -> None:
    evidence = json.loads(witness_json.read_text(encoding="utf-8-sig"))
    if (evidence.get("model_sha256"), evidence.get("model_size_bytes")) != (SHA256, SIZE):
        fail("EVIDENCE_PIN_MISMATCH")
    for flag in ("actually_frozen", "model_embedded_in_frozen_bundle",
                 "clinical_gate_deny_production", "clinical_gate_deny_even_lab_flags"):
        if evidence.get(flag) is not True:
            fail("EVIDENCE_FROZEN_FLAG_MISSING")
    for flag in ("model_inference_executed", "patient_data_used",
                 "actual_digitalcrown_app_exe", "installable_certified", "clinical_release"):
        if evidence.get(flag) is not False:
            fail("EVIDENCE_NO_RELEASE_FLAG_MISSING")
    if "MODEL_SHA256_MISMATCH" not in failed_run_output.read_text(encoding="utf-8-sig"):
        fail("NEGATIVE_TAMPER_TEST_NOT_PROVEN")
    evidence.update({
        "original_source_run": SOURCE_RUN,
        "original_source_artifact_id": SOURCE_ID,
        "original_source_artifact_digest": SOURCE_ZIP_SHA,
        "altered_same_size_model_denied": True,
        "production_spec_untouched": True,
        "distribution_artifact_contains_model": False,
        "scope": "isolated_windows_pyinstaller_nonclinical_witness_only",
    })
    Path("lot08j-win-frozen-meta.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("LOT08J_REAL_WINDOWS_FROZEN_MODEL_HASH_DENY_AND_TAMPER_EVIDENCE_PASS")


if __name__ == "__main__":
    try:
        if getattr(sys, "frozen", False):
            frozen()
        elif len(sys.argv) == 2 and sys.argv[1] == "preflight":
            preflight()
        elif len(sys.argv) == 5 and sys.argv[1] == "source":
            source(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
        elif len(sys.argv) == 3 and sys.argv[1] == "tamper":
            tamper(Path(sys.argv[2]))
        elif len(sys.argv) == 4 and sys.argv[1] == "report":
            report(Path(sys.argv[2]), Path(sys.argv[3]))
        else:
            fail("WITNESS_INVALID_INVOCATION")
    except Exception as exc:
        print(f"LOT08J_FAIL_CLOSED: {exc}", file=sys.stderr)
        sys.exit(2)
