"""SEC-P1.2 isolated FastAPI request parity against a native compiled backend module.

This is NOT the clinical FastAPI app. Only an existing dependency-free Digital
Crown module is compiled, with synthetic keys and no network/server socket.
A child process unloads the native Windows .pyd before temporary cleanup.
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

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend" / "core" / "key_material.py"
MODULE = "sec_p1_2_native_key_material"
TEST_TOKEN = "synthetic-fastapi-only"


class StorageRequest(BaseModel):
    sqlcipher_key: str | None = None
    auth_key: str | None = None


class MobileRequest(BaseModel):
    master_key: str | None = None
    mobile_key: str | None = None
    storage_key: str | None = None
    auth_key: str | None = None


def authorized(x_lab_token: str | None = Header(default=None)) -> None:
    if x_lab_token != TEST_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


def safe_hash(value: str) -> dict[str, object]:
    return {"sha256": hashlib.sha256(value.encode()).hexdigest(), "length": len(value)}


def build_app(module: dict | object) -> FastAPI:
    get = ((lambda key: module[key]) if isinstance(module, dict)
           else (lambda key: getattr(module, key)))
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

    @app.post("/lab/storage", dependencies=[Depends(authorized)])
    async def storage(payload: StorageRequest) -> dict[str, object]:
        env: dict[str, str] = {}
        if payload.sqlcipher_key is not None:
            env["SQLCIPHER_KEY_HEX"] = payload.sqlcipher_key
        if payload.auth_key is not None:
            env["SECRET_KEY"] = payload.auth_key
        with patch.dict(os.environ, env, clear=True):
            try:
                key = get("sqlcipher_passphrase")()
            except ValueError:
                raise HTTPException(status_code=422, detail="invalid-key") from None
        return safe_hash(key)

    @app.post("/lab/mobile", dependencies=[Depends(authorized)])
    async def mobile(payload: MobileRequest) -> dict[str, object]:
        env: dict[str, str] = {}
        for name, value in (
            ("CABINET_MASTER_KEY_HEX", payload.master_key),
            ("MOBILE_PAIRING_KEY_HEX", payload.mobile_key),
            ("SQLCIPHER_KEY_HEX", payload.storage_key),
            ("SECRET_KEY", payload.auth_key),
        ):
            if value is not None:
                env[name] = value
        with patch.dict(os.environ, env, clear=True):
            try:
                key = get("mobile_pairing_key_hex")()
            except ValueError:
                raise HTTPException(status_code=422, detail="invalid-key") from None
        return safe_hash(key)

    return app


def http_results(module: dict | object) -> list[tuple[int, object]]:
    auth = {"X-Lab-Token": TEST_TOKEN}
    cases: list[tuple[str, dict[str, object], dict[str, str], int]] = [
        ("storage unauthorized", {"sqlcipher_key": "11" * 32}, {}, 401),
        ("storage accepted", {"sqlcipher_key": "11" * 32, "auth_key": "22" * 32}, auth, 200),
        ("storage shared secret rejected", {"sqlcipher_key": "11" * 32, "auth_key": "11" * 32}, auth, 422),
        ("storage malformed key rejected", {"sqlcipher_key": "invalid"}, auth, 422),
        ("storage unauthorized missing payload", {}, {}, 401),
        ("mobile derived", {"master_key": "44" * 32}, auth, 200),
        ("mobile missing root rejected", {}, auth, 422),
        ("mobile malformed root rejected", {"master_key": "broken"}, auth, 422),
        ("mobile dedicated", {
            "master_key": "44" * 32, "mobile_key": "55" * 32,
            "storage_key": "11" * 32, "auth_key": "22" * 32,
        }, auth, 200),
        ("mobile shared storage key rejected", {
            "master_key": "44" * 32, "mobile_key": "11" * 32,
            "storage_key": "11" * 32, "auth_key": "22" * 32,
        }, auth, 422),
        ("mobile forbidden without token", {"master_key": "44" * 32}, {"X-Lab-Token": "bad"}, 401),
        ("storage invalid payload type", {"sqlcipher_key": ["invalid"]}, auth, 422),
    ]
    results: list[tuple[int, object]] = []
    with TestClient(build_app(module)) as client:
        for name, body, headers, expected in cases:
            endpoint = "/lab/mobile" if name.startswith("mobile") else "/lab/storage"
            reply = client.post(endpoint, json=body, headers=headers)
            if reply.status_code != expected:
                raise AssertionError(f"Unexpected status {reply.status_code} in case {name}")
            payload = reply.json()
            if expected == 200 and (
                set(payload) != {"sha256", "length"}
                or len(payload["sha256"]) != 64
            ):
                raise AssertionError("Unexpected response fields or fingerprint")
            results.append((reply.status_code, payload))
    return results


def verify(native_path: Path) -> None:
    original = runpy.run_path(str(SOURCE), run_name="__sec_p1_2_source__")
    with native_path.open("rb") as stream:
        header = stream.read(4)
    system = platform.system()
    if system == "Windows":
        if native_path.suffix.lower() != ".pyd" or not header.startswith(b"MZ"):
            raise AssertionError("Not a native Windows PE/PYD")
    elif system == "Linux":
        if not header.startswith(b"\x7fELF"):
            raise AssertionError("Not a native Linux ELF")
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
    spec = importlib.util.spec_from_file_location(MODULE, native_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import native extension")
    compiled = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compiled)
    original_responses = http_results(original)
    compiled_responses = http_results(compiled)
    for i, (before, after) in enumerate(zip(original_responses, compiled_responses, strict=True), 1):
        if before != after:
            raise AssertionError(f"Native/Python FastAPI response mismatch case {i}")
        print(f"HTTP PARITY PASS {i}/{len(original_responses)}")
    print(f"SEC_P1_2_HTTP_PARITY={len(original_responses)}/{len(original_responses)}")
    print(f"SEC_P1_2_NATIVE_FORMAT={system}")
    print("SEC_P1_2_PATIENT_DATA_USED=NO")
    print("SEC_P1_2_COMMERCIAL_BUILD_CHANGED=NO")


def run_lab() -> None:
    if not SOURCE.is_file():
        raise RuntimeError("Expected real key_material.py source missing")
    with tempfile.TemporaryDirectory(prefix="dc-sec-p1-2-") as root:
        work = Path(root)
        source_copy = work / f"{MODULE}.py"
        source_copy.write_bytes(SOURCE.read_bytes())
        out = work / "compiled"
        out.mkdir()
        build = subprocess.run([
            sys.executable, "-m", "nuitka", "--mode=module", "--nofollow-imports",
            "--output-dir=" + str(out), str(source_copy),
        ], cwd=str(work), capture_output=True, text=True, timeout=600, check=False)
        if build.returncode:
            raise RuntimeError(
                f"Native compilation failed ({build.returncode}):\n"
                + (build.stdout + "\n" + build.stderr)[-3500:]
            )
        libraries = [
            p for p in out.iterdir()
            if p.name.startswith(MODULE)
            and any(p.name.endswith(ext) for ext in importlib.machinery.EXTENSION_SUFFIXES)
        ]
        if len(libraries) != 1:
            raise RuntimeError("Expected exactly one native extension")
        worker = subprocess.run([
            sys.executable, str(Path(__file__).resolve()), "--verify-native", str(libraries[0]),
        ], cwd=str(work), capture_output=True, text=True, timeout=120, check=False)
        if worker.returncode:
            raise RuntimeError(
                f"Native worker failed ({worker.returncode}):\n"
                + (worker.stdout + "\n" + worker.stderr)[-3500:]
            )
        print(worker.stdout, end="")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-native":
        verify(Path(sys.argv[2]))
    elif len(sys.argv) == 1:
        run_lab()
    else:
        raise SystemExit("SEC-P1.2 unsupported invocation")
