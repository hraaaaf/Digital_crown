from __future__ import annotations

import argparse
import hashlib
import json
import platform
import plistlib
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

SCHEMA = "digital-crown-p13-evidence-v1"
ALLOWED_STATUS = {"PENDING", "PASS", "FAIL", "NOT_APPLICABLE", "CI_SUBSTITUTED"}
REQUIRED_GATES = (
    "clean_install",
    "first_launch",
    "normal_relaunch",
    "single_instance",
    "synthetic_fixture",
    "off_machine_dr",
    "cross_os_restore",
    "authenticated_update",
    "rollback",
    "wrong_secret_rejected",
    "tampered_bundle_rejected",
    "offline_destination_fail_closed",
    "unready_second_instance_recovery",
    "insufficient_space_fail_closed",
    "interrupted_operation_recoverable",
)
CI_SUBSTITUTABLE_GATES = {
    "wrong_secret_rejected",
    "tampered_bundle_rejected",
    "offline_destination_fail_closed",
    "unready_second_instance_recovery",
    "insufficient_space_fail_closed",
    "interrupted_operation_recoverable",
}
FORBIDDEN_KEYS = {
    "recovery_secret",
    "private_key",
    "private_signing_key",
    "pfx_password",
    "password",
    "passphrase",
    "secret_value",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def machine_facts() -> dict[str, Any]:
    system = platform.system()
    facts: dict[str, Any] = {
        "platform": system,
        "architecture": platform.machine(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "processor": platform.processor(),
        "hostname_sha256": hashlib.sha256(socket.gethostname().encode()).hexdigest(),
    }
    if system == "Darwin":
        facts["model"] = run(["sysctl", "-n", "hw.model"]).get("stdout") or None
        facts["macos_version"] = run(["sw_vers", "-productVersion"]).get("stdout") or None
        facts["macos_build"] = run(["sw_vers", "-buildVersion"]).get("stdout") or None
    elif system == "Windows":
        ps = shutil.which("powershell") or shutil.which("pwsh")
        if ps:
            commands = {
                "windows_model": "Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model | ConvertTo-Json -Compress",
                "windows_os": "Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | ConvertTo-Json -Compress",
            }
            for key, command in commands.items():
                raw = run([ps, "-NoProfile", "-Command", command]).get("stdout")
                if raw:
                    try:
                        facts[key] = json.loads(raw)
                    except json.JSONDecodeError:
                        facts[key] = {"raw": raw}
    return facts


def package_facts(package: Path, app_path: Path | None) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "filename": package.name,
        "size_bytes": package.stat().st_size,
        "sha256": sha256_file(package),
    }
    system = platform.system()
    if system == "Windows":
        ps = shutil.which("powershell") or shutil.which("pwsh")
        if ps:
            escaped = str(package.resolve()).replace("'", "''")
            command = (
                "$s=Get-AuthenticodeSignature -LiteralPath '" + escaped + "'; "
                "[pscustomobject]@{Status=$s.Status.ToString();Thumbprint=$s.SignerCertificate.Thumbprint} | ConvertTo-Json -Compress"
            )
            raw = run([ps, "-NoProfile", "-Command", command]).get("stdout")
            if raw:
                try:
                    facts["authenticode"] = json.loads(raw)
                except json.JSONDecodeError:
                    facts["authenticode"] = {"raw": raw}
    elif system == "Darwin" and app_path:
        info_path = app_path / "Contents" / "Info.plist"
        app: dict[str, Any] = {"path_name": app_path.name}
        if info_path.is_file():
            with info_path.open("rb") as handle:
                info = plistlib.load(handle)
            app.update(
                bundle_id=info.get("CFBundleIdentifier"),
                bundle_version=info.get("CFBundleVersion"),
                short_version=info.get("CFBundleShortVersionString"),
            )
        app["codesign_verify"] = run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app_path)])
        app["gatekeeper_assess"] = run(["spctl", "-a", "-vv", "--type", "execute", str(app_path)])
        facts["installed_app"] = app
    return facts


def health_probe(url: str) -> dict[str, Any]:
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=8) as response:
            text = response.read(1024 * 1024).decode("utf-8", errors="replace")
            try:
                payload: Any = json.loads(text)
            except json.JSONDecodeError:
                payload = {"raw": text}
            return {"reachable": True, "status_code": response.status, "payload": payload}
    except (URLError, OSError, TimeoutError) as exc:
        return {"reachable": False, "error": str(exc)}


def artifact(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return {"filename": path.name, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}


def dr_artifacts(bundle_path: Path | None, sidecar_path: Path | None):
    bundle = artifact(bundle_path)
    sidecar = artifact(sidecar_path)
    if bundle and sidecar and sidecar_path:
        raw = sidecar_path.read_text(encoding="utf-8", errors="replace").strip()
        declared = raw.split()[0].lower() if raw else ""
        sidecar["declared_bundle_sha256"] = declared
        sidecar["matches_bundle"] = declared == bundle["sha256"]
    return bundle, sidecar


def assert_no_secrets(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if lowered in FORBIDDEN_KEYS or lowered.endswith("_password") or lowered.endswith("_private_key"):
                raise SystemExit(f"forbidden secret-bearing key at {path}.{key}")
            assert_no_secrets(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_secrets(child, f"{path}[{index}]")


def validate_document(document: dict[str, Any], require_pass: bool = False) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    if not str(document.get("operator", "")).strip():
        errors.append("operator is required")
    if not str(document.get("release_id", "")).strip():
        errors.append("release_id is required")

    machine = document.get("machine")
    if not isinstance(machine, dict) or machine.get("platform") not in {"Windows", "Darwin"}:
        errors.append("machine.platform must be Windows or Darwin")
    package = document.get("package")
    if not isinstance(package, dict) or len(str(package.get("sha256", ""))) != 64:
        errors.append("package.sha256 must be present")

    gates = document.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
    else:
        for gate in REQUIRED_GATES:
            entry = gates.get(gate)
            if not isinstance(entry, dict):
                errors.append(f"missing gate: {gate}")
                continue
            status = entry.get("status")
            if status not in ALLOWED_STATUS:
                errors.append(f"invalid gate status: {gate}={status!r}")
            if require_pass:
                acceptable = status == "PASS" or (gate in CI_SUBSTITUTABLE_GATES and status == "CI_SUBSTITUTED")
                if not acceptable:
                    errors.append(f"gate not acceptable for closure review: {gate}={status}")
                if status == "CI_SUBSTITUTED" and not str(entry.get("note", "")).strip():
                    errors.append(f"CI_SUBSTITUTED gate requires evidence note: {gate}")

    attestation = document.get("attestation")
    if not isinstance(attestation, dict) or attestation.get("contains_real_patient_data") is not False:
        errors.append("attestation must explicitly confirm contains_real_patient_data=false")

    if require_pass:
        health = document.get("health")
        payload = health.get("payload") if isinstance(health, dict) else None
        if not isinstance(health, dict) or health.get("reachable") is not True or health.get("status_code") != 200:
            errors.append("health must be reachable with HTTP 200")
        if not isinstance(payload, dict) or payload.get("status") != "ok" or payload.get("db") != "ok":
            errors.append("health payload must contain status=ok and db=ok")

        artifacts = document.get("artifacts")
        if not isinstance(artifacts, dict):
            errors.append("artifacts must be an object")
        else:
            for name in ("dr_bundle", "dr_sidecar", "media_sentinel"):
                item = artifacts.get(name)
                if not isinstance(item, dict) or len(str(item.get("sha256", ""))) != 64:
                    errors.append(f"required artifact missing or unhashed: {name}")
            sidecar = artifacts.get("dr_sidecar")
            if isinstance(sidecar, dict) and sidecar.get("matches_bundle") is not True:
                errors.append("DR sidecar does not match DR bundle SHA-256")

        if isinstance(machine, dict) and machine.get("platform") == "Windows":
            model = machine.get("windows_model")
            os_info = machine.get("windows_os")
            if not isinstance(model, dict) or not model.get("Model"):
                errors.append("Windows physical model evidence missing")
            if not isinstance(os_info, dict) or not os_info.get("BuildNumber"):
                errors.append("Windows exact build evidence missing")
            auth = package.get("authenticode") if isinstance(package, dict) else None
            if not isinstance(auth, dict) or auth.get("Status") != "Valid":
                errors.append("Windows Authenticode status must be Valid")
            if not isinstance(auth, dict) or not auth.get("Thumbprint"):
                errors.append("Windows signer certificate thumbprint missing")

        if isinstance(machine, dict) and machine.get("platform") == "Darwin":
            if not machine.get("model") or not machine.get("macos_version") or not machine.get("macos_build"):
                errors.append("macOS model/version/build evidence missing")
            installed = package.get("installed_app") if isinstance(package, dict) else None
            if not isinstance(installed, dict):
                errors.append("macOS installed app evidence missing")
            else:
                if not installed.get("bundle_id") or not installed.get("short_version"):
                    errors.append("macOS bundle id/version evidence missing")
                codesign = installed.get("codesign_verify")
                if not isinstance(codesign, dict) or codesign.get("returncode") != 0:
                    errors.append("macOS strict codesign verification must pass")

    try:
        assert_no_secrets(document)
    except SystemExit as exc:
        errors.append(str(exc))
    return errors


def collect(args: argparse.Namespace) -> int:
    package = Path(args.package).expanduser().resolve()
    if not package.is_file():
        raise SystemExit(f"package not found: {package}")
    app_path = Path(args.app_path).expanduser().resolve() if args.app_path else None
    if app_path and not app_path.exists():
        raise SystemExit(f"app path not found: {app_path}")
    machine = machine_facts()
    if machine.get("platform") not in {"Windows", "Darwin"}:
        raise SystemExit(f"P13 collection only supports Windows or macOS, got {machine.get('platform')!r}")

    data_path = Path(args.data_path).expanduser().resolve() if args.data_path else package.parent
    disk = shutil.disk_usage(data_path)
    bundle_path = Path(args.dr_bundle).expanduser().resolve() if args.dr_bundle else None
    sidecar_path = Path(args.dr_sidecar).expanduser().resolve() if args.dr_sidecar else None
    bundle, sidecar = dr_artifacts(bundle_path, sidecar_path)

    document = {
        "schema": SCHEMA,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "operator": args.operator.strip(),
        "release_id": args.release_id.strip(),
        "machine": machine,
        "storage": {"probe_path_name": data_path.name or str(data_path.anchor), "free_bytes": disk.free, "total_bytes": disk.total},
        "package": package_facts(package, app_path),
        "health": health_probe(args.health_url),
        "artifacts": {
            "dr_bundle": bundle,
            "dr_sidecar": sidecar,
            "media_sentinel": artifact(Path(args.media_sentinel).expanduser().resolve()) if args.media_sentinel else None,
        },
        "gates": {gate: {"status": "PENDING", "note": ""} for gate in REQUIRED_GATES},
        "attestation": {
            "scope": "operator-recorded physical evidence; completeness is machine-validated, execution remains human-observed",
            "contains_real_patient_data": False,
        },
    }
    assert_no_secrets(document)
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"P13_EVIDENCE_COLLECTED={output}")
    return 0


def set_gate(args: argparse.Namespace) -> int:
    path = Path(args.file).expanduser().resolve()
    document = json.loads(path.read_text(encoding="utf-8"))
    document.setdefault("gates", {})[args.gate] = {
        "status": args.status,
        "note": args.note.strip(),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    assert_no_secrets(document)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"P13_GATE_RECORDED={args.gate}:{args.status}")
    return 0


def validate(args: argparse.Namespace) -> int:
    document = json.loads(Path(args.file).expanduser().resolve().read_text(encoding="utf-8"))
    errors = validate_document(document, require_pass=args.require_pass)
    if errors:
        for error in errors:
            print(f"P13_EVIDENCE_ERROR={error}", file=sys.stderr)
        return 2
    print("P13_EVIDENCE_VALID=" + ("PASS_ATTESTED" if args.require_pass else "STRUCTURE_OK"))
    return 0


def validate_pair(args: argparse.Namespace) -> int:
    paths = [Path(args.first).expanduser().resolve(), Path(args.second).expanduser().resolve()]
    documents = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    errors: list[str] = []
    for path, document in zip(paths, documents):
        errors.extend(f"{path.name}: {error}" for error in validate_document(document, require_pass=True))
    platforms = {doc.get("machine", {}).get("platform") for doc in documents if isinstance(doc.get("machine"), dict)}
    if platforms != {"Windows", "Darwin"}:
        errors.append(f"pair must contain one Windows and one Darwin file, got {sorted(str(p) for p in platforms)}")
    release_ids = {str(doc.get("release_id", "")) for doc in documents}
    if len(release_ids) != 1 or "" in release_ids:
        errors.append("both evidence files must share the same non-empty release_id")
    if errors:
        for error in errors:
            print(f"P13_PAIR_ERROR={error}", file=sys.stderr)
        return 2
    print(f"P13_PAIR_EVIDENCE_VALID=PASS_ATTESTED release_id={next(iter(release_ids))}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Collect and validate Digital Crown P13 physical-cabinet evidence without storing secrets.")
    sub = root.add_subparsers(dest="command", required=True)

    p = sub.add_parser("collect")
    p.add_argument("--operator", required=True)
    p.add_argument("--release-id", required=True)
    p.add_argument("--package", required=True)
    p.add_argument("--app-path")
    p.add_argument("--health-url", required=True)
    p.add_argument("--data-path")
    p.add_argument("--dr-bundle")
    p.add_argument("--dr-sidecar")
    p.add_argument("--media-sentinel")
    p.add_argument("--output", required=True)
    p.set_defaults(func=collect)

    p = sub.add_parser("set-gate")
    p.add_argument("--file", required=True)
    p.add_argument("--gate", required=True, choices=REQUIRED_GATES)
    p.add_argument("--status", required=True, choices=sorted(ALLOWED_STATUS))
    p.add_argument("--note", default="")
    p.set_defaults(func=set_gate)

    p = sub.add_parser("validate")
    p.add_argument("--file", required=True)
    p.add_argument("--require-pass", action="store_true")
    p.set_defaults(func=validate)

    p = sub.add_parser("validate-pair")
    p.add_argument("--first", required=True)
    p.add_argument("--second", required=True)
    p.set_defaults(func=validate_pair)
    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
