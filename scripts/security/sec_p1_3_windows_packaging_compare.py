"""SEC-P1.3 Windows only: compare PyInstaller onedir vs Nuitka standalone.

Builds TWO clearly non-installable synthetic probes from one staged source tree.
Never imports the production app, runs DigitalCrown.spec, bundles frontend,
reads clinic configuration, or publishes binary artifacts.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
REAL_KEY_MODULE = ROOT / "backend/core/key_material.py"
PROBE_ENTRY = ROOT / "scripts/security/sec_p1_3_windows_probe_entry.py"
CERTIFIED_SPEC = ROOT / "DigitalCrown.spec"
CERTIFIED_LAUNCHER = ROOT / "run.py"


def require_release_boundary() -> None:
    if platform.system() != "Windows" or sys.maxsize <= 2**32:
        raise RuntimeError("SEC-P1.3 packaging lab requires 64-bit Windows")
    if not all(p.is_file() for p in (REAL_KEY_MODULE, PROBE_ENTRY, CERTIFIED_SPEC, CERTIFIED_LAUNCHER)):
        raise RuntimeError("SEC-P1.3 required canonical sources are missing")
    if "verify_installable_release_directory" not in CERTIFIED_SPEC.read_text(encoding="utf-8"):
        raise AssertionError("Commercial release build guard disappeared")
    if "verify_installable_release_identity" not in CERTIFIED_LAUNCHER.read_text(encoding="utf-8"):
        raise AssertionError("Commercial launch identity guard disappeared")
    if "DigitalCrown" in PROBE_ENTRY.read_text(encoding="utf-8").replace(
        "DigitalCrown.exe", ""
    ):
        # The synthetic entry is not allowed to re-brand itself as the app.
        raise AssertionError("Unexpected commercial identity in probe")


def stage_probe(folder: Path) -> Path:
    package = folder / "dc_p13_synthetic_backend"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Synthetic package; no production backend initialization."""\n',
        encoding="utf-8",
    )
    original = REAL_KEY_MODULE.read_bytes()
    (package / "key_material.py").write_bytes(original)
    if (package / "key_material.py").read_bytes() != original:
        raise AssertionError("Real backend key module changed during staging")
    path = folder / "probe.py"
    path.write_bytes(PROBE_ENTRY.read_bytes())
    return path


def execute(command: list[str], cwd: Path, timeout: int = 1500) -> float:
    beginning = time.monotonic()
    completed = subprocess.run(
        command, cwd=str(cwd), text=True, errors="replace",
        capture_output=True, timeout=timeout, check=False,
    )
    elapsed = time.monotonic() - beginning
    if completed.returncode:
        # Only compiler diagnostic tails, no external/production fixtures.
        raise RuntimeError(
            f"Build exited {completed.returncode}, command module={command[2] if len(command)>2 else 'unknown'}:\n"
            + (completed.stdout + "\n" + completed.stderr)[-4500:]
        )
    return elapsed


def clean_runtime_environment() -> dict[str, str]:
    # No repository, provider or database credentials cross into probe runs.
    allowed = ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "TEMP", "TMP",
               "LOCALAPPDATA", "APPDATA", "PATHEXT", "PYTHONUTF8")
    result = {name: os.environ[name] for name in allowed if name in os.environ}
    result["PYTHONIOENCODING"] = "utf-8"
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    return result


def smoke(command: list[str], cwd: Path) -> tuple[dict, float]:
    begin = time.perf_counter()
    proc = subprocess.run(
        command, cwd=str(cwd), env=clean_runtime_environment(),
        capture_output=True, text=True, errors="replace",
        timeout=75, check=False,
    )
    seconds = time.perf_counter() - begin
    if proc.returncode:
        raise RuntimeError(
            f"Packaged probe failed: status {proc.returncode}; "
            + (proc.stdout + "\n" + proc.stderr)[-2000:]
        )
    try:
        result = json.loads(proc.stdout.strip())
    except json.JSONDecodeError as exc:
        raise AssertionError("Probe did not emit exactly one JSON result") from exc
    if not isinstance(result, dict) or result.get("kind") != "SEC-P1.3-NONINSTALLABLE-PROBE":
        raise AssertionError("Packaged probe has the wrong product identity")
    if result.get("scenarios") != 8 or len(result.get("results", [])) != 8:
        raise AssertionError("Real key-material test scenario count mismatch")
    if any("SQLCIPHER_KEY_HEX" in str(v) or "SECRET_KEY" in str(v) for v in result.values()):
        raise AssertionError("Potential key identifier in probe output")
    return result, seconds


def folder_metrics(exe: Path) -> dict:
    folder = exe.parent
    files = [p for p in folder.rglob("*") if p.is_file()]
    if not exe.is_file() or exe.read_bytes()[:2] != b"MZ":
        raise AssertionError("Expected a genuine Windows PE executable")
    forbidden = [
        p.relative_to(folder).as_posix() for p in files
        if p.name.lower() in {
            ".env", "firebase_creds.json", "service-account.json",
            "private_key.pem", "private-key.pem", "signing_key.pem",
        }
        or "firebase_creds" in p.name.lower()
        or p.name.lower().endswith(".key")
        or (
            p.name.lower().endswith(".pem")
            and any(word in p.name.lower() for word in ("private", "secret", "signing"))
        )
    ]
    if forbidden:
        raise AssertionError(f"Forbidden credential-looking packaged file names: {forbidden}")
    return {
        "exe_bytes": exe.stat().st_size,
        "directory_bytes": sum(p.stat().st_size for p in files),
        "file_count": len(files),
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "forbidden_credential_files": 0,
    }


def find_native_exe(folder: Path) -> Path:
    candidates = [p for p in folder.rglob("dc_p13_nuitka.exe") if p.is_file()]
    if len(candidates) != 1 or not candidates[0].parent.name.endswith(".dist"):
        raise RuntimeError(f"Expected exactly one Nuitka standalone executable, got {len(candidates)}")
    return candidates[0]


def main() -> None:
    require_release_boundary()
    with tempfile.TemporaryDirectory(prefix="dc-sec-p13-windows-") as name:
        root = Path(name)
        stage = root / "staged"
        stage.mkdir()
        entry = stage_probe(stage)
        source_digest = hashlib.sha256(REAL_KEY_MODULE.read_bytes()).hexdigest()

        # The source (Python) benchmark is the independent behavioral oracle.
        reference, reference_seconds = smoke([sys.executable, str(entry)], stage)

        pyroot = root / "pyinstaller"
        pyroot.mkdir()
        py_build_s = execute([
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean", "--onedir", "--console",
            "--name", "dc_p13_pyinstaller",
            "--distpath", str(pyroot / "dist"),
            "--workpath", str(pyroot / "build"),
            "--specpath", str(pyroot / "spec"),
            "--paths", str(stage),
            str(entry),
        ], stage)
        pyexe = pyroot / "dist" / "dc_p13_pyinstaller" / "dc_p13_pyinstaller.exe"

        nroot = root / "nuitka"
        nroot.mkdir()
        native_build_s = execute([
            sys.executable, "-m", "nuitka", "--mode=standalone",
            # Only the throwaway, read-only CI laboratory may auto-fetch the
            # missing Dependency Walker. This MUST NOT be copied into release
            # builds: Nuitka 4.3 does not verify the tool's content digest.
            "--assume-yes-for-downloads", "--update-check=never",
            "--msvc=latest", "--follow-imports",
            "--output-dir=" + str(nroot),
            "--output-filename=dc_p13_nuitka.exe",
            str(entry),
        ], stage)
        native_exe = find_native_exe(nroot)

        outcomes: dict[str, dict] = {}
        for name, exe, build_time in (
            ("pyinstaller", pyexe, py_build_s),
            ("nuitka", native_exe, native_build_s),
        ):
            metadata = folder_metrics(exe)
            times = []
            for i in range(3):
                output, duration = smoke([str(exe)], stage)
                if output != reference:
                    raise AssertionError(f"{name} packaged response != Python source on repeat {i}")
                times.append(duration)
            outcomes[name] = {
                **metadata,
                "build_seconds": round(build_time, 3),
                "startup_median_seconds": round(statistics.median(times), 3),
                "scenarios": 8,
                "oracle_parity": "8/8",
            }
            print(f"SEC_P1_3_{name.upper()}_PE=PASS")
            print(f"SEC_P1_3_{name.upper()}_HTTP_PARITY=8/8")
            print(f"SEC_P1_3_{name.upper()}_STARTUP_MEDIAN_SECONDS={statistics.median(times):.3f}")
            print(f"SEC_P1_3_{name.upper()}_DIST_BYTES={metadata['directory_bytes']}")
            print(f"SEC_P1_3_{name.upper()}_EXE_SHA256={metadata['exe_sha256']}")

        print("SEC_P1_3_COMPARE_RESULTS_JSON=" + json.dumps(
            {"source_sha256": source_digest, "python_startup_seconds": round(reference_seconds, 3),
             "windows": platform.version(), "implementations": outcomes},
            sort_keys=True, separators=(",", ":"),
        ))
        print("SEC_P1_3_REAL_CODE_SOURCE=backend/core/key_material.py")
        print("SEC_P1_3_HTTP_SERVICE=synthetic_testclient_no_listener")
        print("SEC_P1_3_RELEASE_CERTIFICATION_GATE=UNCHANGED")
        print("SEC_P1_3_CLINICAL_APP_BUILT=NO")
        print("SEC_P1_3_SECRET_OR_PATIENT_DATA=NO")
        print("SEC_P1_3_INSTALLABLE_RELEASE=NO")


if __name__ == "__main__":
    main()
