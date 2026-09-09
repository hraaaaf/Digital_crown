import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "p13_real_cabinet_evidence.py"
SPEC = importlib.util.spec_from_file_location("p13_real_cabinet_evidence", SCRIPT)
assert SPEC and SPEC.loader
p13 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p13)


def _gates(status: str = "PASS"):
    return {gate: {"status": status, "note": "observed"} for gate in p13.REQUIRED_GATES}


def _base(platform_name: str):
    document = {
        "schema": p13.SCHEMA,
        "operator": "AB",
        "release_id": "rc-p13",
        "machine": {"platform": platform_name},
        "package": {"sha256": "a" * 64},
        "health": {"reachable": True, "status_code": 200, "payload": {"status": "ok", "db": "ok"}},
        "artifacts": {
            "dr_bundle": {"sha256": "b" * 64},
            "dr_sidecar": {"sha256": "c" * 64, "matches_bundle": True},
            "media_sentinel": {"sha256": "d" * 64},
        },
        "gates": _gates(),
        "attestation": {"contains_real_patient_data": False},
    }
    if platform_name == "Windows":
        document["machine"].update(
            {
                "windows_model": {"Manufacturer": "Example", "Model": "Cabinet-PC"},
                "windows_os": {"Caption": "Windows", "Version": "10.0", "BuildNumber": "26100"},
            }
        )
        document["package"]["authenticode"] = {"Status": "Valid", "Thumbprint": "ABC123"}
    else:
        document["machine"].update(
            {"model": "Mac15,3", "macos_version": "15.6", "macos_build": "24G84"}
        )
        document["package"]["installed_app"] = {
            "bundle_id": "ma.digitalcrown.app",
            "short_version": "1.0.1",
            "codesign_verify": {"returncode": 0},
        }
    return document


def test_all_pass_windows_and_macos_documents_validate():
    assert p13.validate_document(_base("Windows"), require_pass=True) == []
    assert p13.validate_document(_base("Darwin"), require_pass=True) == []


def test_require_pass_rejects_unhealthy_runtime_and_pending_gate():
    document = _base("Windows")
    document["health"]["payload"]["db"] = "error"
    document["gates"]["clean_install"]["status"] = "PENDING"
    errors = p13.validate_document(document, require_pass=True)
    assert "health payload must contain status=ok and db=ok" in errors
    assert "gate not acceptable for closure review: clean_install=PENDING" in errors


def test_ci_substitution_is_limited_to_failure_gates_and_requires_note():
    document = _base("Windows")
    document["gates"]["tampered_bundle_rejected"] = {
        "status": "CI_SUBSTITUTED",
        "note": "P9 tamper proof run 33276520623",
    }
    assert p13.validate_document(document, require_pass=True) == []

    document["gates"]["clean_install"] = {
        "status": "CI_SUBSTITUTED",
        "note": "not allowed for a physical core gate",
    }
    errors = p13.validate_document(document, require_pass=True)
    assert any("clean_install=CI_SUBSTITUTED" in error for error in errors)


def test_secret_bearing_keys_are_rejected():
    document = _base("Windows")
    document["recovery_secret"] = "must-never-be-written"
    errors = p13.validate_document(document, require_pass=True)
    assert any("forbidden secret-bearing key" in error for error in errors)


def test_dr_sidecar_must_match_bundle(tmp_path):
    bundle = tmp_path / "cabinet.dcbundle"
    bundle.write_bytes(b"portable-cabinet")
    sidecar = tmp_path / "cabinet.dcbundle.sha256"
    sidecar.write_text(p13.sha256_file(bundle) + "  cabinet.dcbundle\n", encoding="utf-8")

    bundle_info, sidecar_info = p13.dr_artifacts(bundle, sidecar)
    assert bundle_info is not None
    assert sidecar_info is not None
    assert sidecar_info["matches_bundle"] is True

    sidecar.write_text("0" * 64 + "  cabinet.dcbundle\n", encoding="utf-8")
    _, bad_sidecar = p13.dr_artifacts(bundle, sidecar)
    assert bad_sidecar is not None
    assert bad_sidecar["matches_bundle"] is False


def test_pair_requires_windows_and_macos_same_release(tmp_path, capsys):
    windows = _base("Windows")
    macos = _base("Darwin")
    first = tmp_path / "windows.json"
    second = tmp_path / "macos.json"
    first.write_text(json.dumps(windows), encoding="utf-8")
    second.write_text(json.dumps(macos), encoding="utf-8")

    args = type("Args", (), {"first": str(first), "second": str(second)})()
    assert p13.validate_pair(args) == 0
    assert "P13_PAIR_EVIDENCE_VALID=PASS_ATTESTED" in capsys.readouterr().out

    macos["release_id"] = "different"
    second.write_text(json.dumps(macos), encoding="utf-8")
    assert p13.validate_pair(args) == 2
