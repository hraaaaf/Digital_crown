"""SEC-P1.3 isolated executable probe (NEVER DigitalCrown.exe).

This file is copied into a temporary staging directory by the comparison
harness. It imports a byte-identical copy of backend/core/key_material.py
from the synthetic package created there. No production backend init or
external listener. Both packaging candidates run this exact entrypoint.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from dc_p13_synthetic_backend.key_material import (
    keys_equal,
    mobile_pairing_key_hex,
    sqlcipher_passphrase,
)


def app_for_case() -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

    @app.get("/lab/storage")
    async def storage() -> dict[str, object]:
        try:
            value = sqlcipher_passphrase()
        except ValueError:
            raise HTTPException(status_code=422, detail="invalid-material") from None
        return {"digest": hashlib.sha256(value.encode("utf-8")).hexdigest(), "length": len(value)}

    @app.get("/lab/mobile")
    async def mobile() -> dict[str, object]:
        try:
            value = mobile_pairing_key_hex()
        except ValueError:
            raise HTTPException(status_code=422, detail="invalid-material") from None
        return {"digest": hashlib.sha256(value.encode("utf-8")).hexdigest(), "length": len(value)}

    @app.get("/lab/compare")
    async def compare() -> dict[str, bool]:
        return {"equal": keys_equal("AA" * 32, "aa" * 32)}

    return app


def run() -> None:
    if sys.argv[1:]:
        raise SystemExit("SEC-P1.3 probe does not accept application arguments")

    app = app_for_case()
    cases = [
        ("normal-storage", "/lab/storage",
         {"SQLCIPHER_KEY_HEX": "11" * 32, "SECRET_KEY": "22" * 32}, 200),
        ("bad-storage", "/lab/storage",
         {"SQLCIPHER_KEY_HEX": "invalid"}, 422),
        ("shared-storage-key", "/lab/storage",
         {"SQLCIPHER_KEY_HEX": "11" * 32, "SECRET_KEY": "11" * 32}, 422),
        ("normal-mobile", "/lab/mobile",
         {"CABINET_MASTER_KEY_HEX": "44" * 32}, 200),
        ("dedicated-mobile", "/lab/mobile",
         {"CABINET_MASTER_KEY_HEX": "44" * 32, "MOBILE_PAIRING_KEY_HEX": "55" * 32,
          "SQLCIPHER_KEY_HEX": "11" * 32, "SECRET_KEY": "22" * 32}, 200),
        ("missing-mobile-root", "/lab/mobile", {}, 422),
        ("shared-mobile-key", "/lab/mobile",
         {"CABINET_MASTER_KEY_HEX": "44" * 32, "MOBILE_PAIRING_KEY_HEX": "11" * 32,
          "SQLCIPHER_KEY_HEX": "11" * 32}, 422),
        ("hex-equality", "/lab/compare", {}, 200),
    ]

    records: list[dict[str, object]] = []
    with TestClient(app) as client:
        for label, path, fake_env, expected in cases:
            with patch.dict(os.environ, fake_env, clear=True):
                response = client.get(path)
            if response.status_code != expected:
                raise AssertionError(f"{label}: {response.status_code} != {expected}")
            body = response.json()
            if expected == 200 and label == "hex-equality":
                if body != {"equal": True}:
                    raise AssertionError("Key byte-equivalence changed")
            elif expected == 200:
                if set(body) != {"digest", "length"} or len(body["digest"]) != 64:
                    raise AssertionError(f"{label}: unexpected response fields")
            else:
                if body != {"detail": "invalid-material"}:
                    raise AssertionError(f"{label}: exception handling changed")
            records.append({"label": label, "status": response.status_code, "body": body})

    print(json.dumps(
        {"kind": "SEC-P1.3-NONINSTALLABLE-PROBE", "scenarios": len(records),
         "results": records}, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ))


if __name__ == "__main__":
    run()
