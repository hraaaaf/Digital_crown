"""SEC-P1 experimental native-compilation parity lab (no production build).

Usage: python scripts/security/sec_p1_nuitka_lab.py
Prerequisite: python -m pip install Nuitka==4.3

Copies a single dependency-free backend module to a temporary directory,
compiles that copy into a native extension, compares behaviors with the source,
and deletes all build outputs on exit. Real credentials are never read.
"""

from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import platform
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend" / "core" / "key_material.py"
MODULE_NAME = "sec_p1_key_material"


def invoke(module: dict | object, method: str, args: tuple, environment: dict[str, str]) -> tuple:
    """Compare only results and error types/messages under fake isolated keys."""
    fn = module[method] if isinstance(module, dict) else getattr(module, method)
    with patch.dict(os.environ, environment, clear=True):
        try:
            return ("OK", fn(*args))
        except Exception as exc:
            return ("ERR", type(exc).__name__, str(exc))


def verify_native_extension(library: Path) -> None:
    """Run parity inside a short-lived process so Windows releases the .pyd."""
    if not SOURCE.is_file():
        raise RuntimeError("Expected backend/core/key_material.py missing")

    original = runpy.run_path(str(SOURCE), run_name="__sec_p1_reference__")
    cases: list[tuple[str, str, tuple, dict[str, str]]] = [
        ("hex-case equality", "keys_equal", ("AA" * 32, "aa" * 32), {}),
        ("unequal keys", "keys_equal", ("11" * 32, "22" * 32), {}),
        ("dedicated SQLCipher key", "sqlcipher_passphrase", (), {
            "SQLCIPHER_KEY_HEX": "11" * 32, "SECRET_KEY": "22" * 32,
        }),
        ("reject weak SQLCipher material", "sqlcipher_passphrase", (), {
            "SQLCIPHER_KEY_HEX": "not-hex",
        }),
        ("reject shared auth and storage key", "sqlcipher_passphrase", (), {
            "SQLCIPHER_KEY_HEX": "11" * 32, "SECRET_KEY": "11" * 32,
        }),
        ("legacy SQLCipher derivation preserved", "sqlcipher_passphrase", (), {
            "CABINET_MASTER_KEY_HEX": "33" * 32, "SECRET_KEY": "22" * 32,
        }),
        ("mobile derived key", "mobile_pairing_key_hex", (), {
            "CABINET_MASTER_KEY_HEX": "44" * 32,
        }),
        ("mobile dedicated key", "mobile_pairing_key_hex", (), {
            "MOBILE_PAIRING_KEY_HEX": "55" * 32,
            "SQLCIPHER_KEY_HEX": "11" * 32,
            "CABINET_MASTER_KEY_HEX": "44" * 32,
            "SECRET_KEY": "22" * 32,
        }),
        ("reject shared mobile and storage key", "mobile_pairing_key_hex", (), {
            "MOBILE_PAIRING_KEY_HEX": "11" * 32,
            "SQLCIPHER_KEY_HEX": "11" * 32,
            "CABINET_MASTER_KEY_HEX": "44" * 32,
        }),
        ("reject missing mobile master key", "mobile_pairing_key_hex", (), {}),
        ("reject invalid mobile master key", "mobile_pairing_key_hex", (), {
            "CABINET_MASTER_KEY_HEX": "not-hex",
        }),
    ]


    # Verify that the compiler produced the platform's native extension,
    # rather than a renamed Python file or a portable bytecode archive.
    with library.open("rb") as stream:
        header = stream.read(4)
    system = platform.system()
    if system == "Windows":
        if library.suffix.lower() != ".pyd" or not header.startswith(b"MZ"):
            raise AssertionError("Expected a Windows PE .pyd extension")
        print("SEC_P1_NATIVE_FORMAT=PE/PYD")
    elif system == "Linux":
        if not header.startswith(b"\x7fELF"):
            raise AssertionError("Expected a Linux ELF native extension")
        print("SEC_P1_NATIVE_FORMAT=ELF")
    else:
        raise RuntimeError(f"Unsupported experimental lab platform: {system}")
    spec = importlib.util.spec_from_file_location(MODULE_NAME, library)
    if spec is None or spec.loader is None:
        raise RuntimeError("Native extension cannot be imported")
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)

    # These assertions are behavioral guardrails, not proof of IP protection.
    count = 0
    for title, method, args, fake_env in cases:
        expected = invoke(original, method, args, fake_env)
        actual = invoke(native, method, args, fake_env)
        if expected != actual:
            raise AssertionError(f"Native/Python behavioral mismatch: {title}")
        count += 1
        print(f"PARITY PASS: {title}")
    if invoke(native, "sqlcipher_passphrase", (), {"SQLCIPHER_KEY_HEX": "11" * 32}) != (
        "OK", "11" * 32
    ):
        raise AssertionError("Dedicated storage key does not match fixture")

    print(f"SEC_P1_NUITKA_PARITY={count}/{len(cases)}")
    print(f"SEC_P1_NATIVE_EXTENSION_SHA256={hashlib.sha256(library.read_bytes()).hexdigest()}")
    print(f"SEC_P1_NATIVE_EXTENSION_BYTES={library.stat().st_size}")
    print(f"SEC_P1_PYTHON={platform.python_version()}")
    print(f"SEC_P1_PLATFORM={platform.system()}")
    print("SEC_P1_RELEASE_PACKAGING_CHANGED=NO")


def run_lab() -> None:
    """Compile and verify outside the parent process, then clean up reliably."""
    if not SOURCE.is_file():
        raise RuntimeError("Expected backend/core/key_material.py missing")

    with tempfile.TemporaryDirectory(prefix="dc-sec-p1-nuitka-") as name:
        work = Path(name)
        module_source = work / f"{MODULE_NAME}.py"
        module_source.write_bytes(SOURCE.read_bytes())
        compiled_dir = work / "compiled"
        compiled_dir.mkdir()

        command = [
            sys.executable, "-m", "nuitka", "--mode=module",
            "--nofollow-imports", "--output-dir=" + str(compiled_dir),
            str(module_source),
        ]
        result = subprocess.run(
            command, cwd=str(work), text=True, capture_output=True,
            timeout=600, check=False,
        )
        if result.returncode:
            raise RuntimeError(
                f"Nuitka compilation failed (exit {result.returncode}):\n"
                + (result.stdout + "\n" + result.stderr)[-3500:]
            )

        candidates = [
            path for path in compiled_dir.iterdir()
            if path.name.startswith(MODULE_NAME)
            and any(path.name.endswith(ext) for ext in importlib.machinery.EXTENSION_SUFFIXES)
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one native extension; found {len(candidates)}")
        library = candidates[0]

        # Windows refuses to unlink a loaded .pyd. Import and test it in a
        # separate Python process; its exit releases the DLL before cleanup.
        worker = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--verify-native", str(library)],
            cwd=str(work), text=True, capture_output=True, timeout=120, check=False,
        )
        if worker.returncode:
            raise RuntimeError(
                "Native parity worker failed (exit "
                + str(worker.returncode)
                + "):\\n"
                + (worker.stdout + "\\n" + worker.stderr)[-3500:]
            )
        print(worker.stdout, end="")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-native":
        verify_native_extension(Path(sys.argv[2]))
    elif len(sys.argv) == 1:
        run_lab()
    else:
        raise SystemExit("SEC-P1: unsupported lab invocation")
