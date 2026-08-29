import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "p13_real_cabinet_closure_guard.py"
SPEC = importlib.util.spec_from_file_location("p13_real_cabinet_closure_guard", SCRIPT)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def _gates():
    return {gate: {"status": "PASS", "note": "observed"} for gate in guard.p13.REQUIRED_GATES}


def _evidence(platform_name: str, *, windows_caption: str = "Microsoft Windows 11 Pro"):
    document = {
        "schema": guard.p13.SCHEMA,
        "operator": "AB",
        "release_id": "rc-p13",
        "machine": {"platform": platform_name, "architecture": "AMD64" if platform_name == "Windows" else "arm64"},
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
                "windows_os": {"Caption": windows_caption, "Version": "10.0", "BuildNumber": "26100"},
            }
        )
        document["package"]["authenticode"] = {"Status": "Valid", "Thumbprint": "ABC123"}
    else:
        document["machine"].update({"model": "Mac16,10", "macos_version": "15.6", "macos_build": "24G84"})
        document["package"]["installed_app"] = {
            "bundle_id": "ma.digitalcrown.app",
            "short_version": "1.0.1",
            "codesign_verify": {"returncode": 0},
        }
    return document


def _destination(kind: str = "independent_network_storage"):
    return {
        "kind": kind,
        "description": "operator-observed independent destination",
        "source_machine_independent": True,
    }


def _remote_context():
    return {
        "schema": guard.SCHEMA,
        "windows": {
            "execution_context": "remote_bare_metal_rehearsal",
            "provider": "aws",
            "instance_type": "m6i.metal",
            "operator_attested": True,
            "dr_destination": _destination(),
        },
        "macos": {
            "execution_context": "remote_bare_metal_rehearsal",
            "provider": "aws",
            "instance_type": "mac2-m2.metal",
            "operator_attested": True,
            "dr_destination": _destination(),
        },
    }


def test_remote_bare_metal_pair_passes_rehearsal_but_not_final_closure():
    windows = _evidence("Windows", windows_caption="Microsoft Windows Server 2025 Datacenter")
    macos = _evidence("Darwin")
    context = _remote_context()

    assert guard.validate_pair_with_context(windows, macos, context, closure=False) == []
    errors = guard.validate_pair_with_context(windows, macos, context, closure=True)
    assert "final closure requires windows.execution_context=cabinet_local" in errors
    assert any("Windows 11" in error for error in errors)


def test_final_closure_accepts_local_windows11_usb_plus_remote_apple_silicon_bare_metal_mac():
    windows = _evidence("Windows")
    macos = _evidence("Darwin")
    context = _remote_context()
    context["windows"] = {
        "execution_context": "cabinet_local",
        "operator_attested": True,
        "dr_destination": _destination("usb"),
    }

    assert guard.validate_pair_with_context(windows, macos, context, closure=True) == []


def test_remote_context_rejects_non_metal_instance():
    windows = _evidence("Windows")
    macos = _evidence("Darwin")
    context = _remote_context()
    context["macos"]["instance_type"] = "m6i.large"

    errors = guard.validate_pair_with_context(windows, macos, context, closure=False)
    assert any("ending in .metal" in error for error in errors)


def test_final_closure_rejects_internal_disk_disguised_as_dr():
    windows = _evidence("Windows")
    macos = _evidence("Darwin")
    context = _remote_context()
    context["windows"] = {
        "execution_context": "cabinet_local",
        "operator_attested": True,
        "dr_destination": {
            "kind": "internal_disk",
            "description": "C:\\backup",
            "source_machine_independent": False,
        },
    }

    errors = guard.validate_pair_with_context(windows, macos, context, closure=True)
    assert any("dr_destination.kind" in error for error in errors)
    assert any("source_machine_independent" in error for error in errors)


def test_final_closure_rejects_windows_server_even_on_local_context():
    windows = _evidence("Windows", windows_caption="Microsoft Windows Server 2025 Datacenter")
    macos = _evidence("Darwin")
    context = _remote_context()
    context["windows"] = {
        "execution_context": "cabinet_local",
        "operator_attested": True,
        "dr_destination": _destination("nas"),
    }

    errors = guard.validate_pair_with_context(windows, macos, context, closure=True)
    assert any("Windows 11" in error for error in errors)


def test_operator_attestation_is_required():
    windows = _evidence("Windows")
    macos = _evidence("Darwin")
    context = _remote_context()
    context["macos"]["operator_attested"] = False

    errors = guard.validate_pair_with_context(windows, macos, context, closure=False)
    assert "macos.operator_attested must be true" in errors
