# SEC-P1.2 — FastAPI + native backend module parity lab

## Goal / success evidence

This is a **stacked, draft-only** experiment based on SEC-P1.1 branch
`experiment/sec-p1-nuitka-native-parity`. It validates that an actual,
unmodified Digital Crown Python backend module (`backend/core/key_material.py`)
can be compiled to a Nuitka Python extension and called through **synthetic**
FastAPI routes using `TestClient`. Its test matrix is Python 3.12 on Linux
and Windows. Each environment must prove native ELF / Windows PE .pyd loading,
12 source-vs-native HTTP request/response comparisons, and successful cleanup.

Test cases cover auth-gate 401, valid key fingerprint HTTP 200, invalid key
HTTP 422, request validation HTTP 422 and normal/rejection mobile key paths.
Only synthetic hexadecimal fixtures are used. HTTP payloads return SHA-256
fingerprints of synthetic outputs, never actual keys; no public network listener
is started.

Workflow: [SEC-P1.2 Experimental FastAPI Native HTTP Parity](../../.github/workflows/sec-p1-2-fastapi-native-parity.yml).
Script: `scripts/security/sec_p1_2_fastapi_parity_lab.py`.

## Isolation / limitations

- **Not the clinical FastAPI application**: the routes are intentionally
  synthetic; no actual `backend.main` or production router is imported.
- The native module is only `key_material.py`, not a native-compiled FastAPI
  service or full backend. This alone cannot justify changing `DigitalCrown.spec`.
- `TestClient` exercises ASGI requests in-process; no real LAN binding, TLS,
  browser/PWA, packaging installer, SQLCipher file, medical image or recovery
  flow is tested.
- Existing real key-material fallback behavior is kept for parity only, not
  approved or adopted as a new security control.
- Compilation does not prevent code extraction, tampering or license cracking.
- This test runs without Firebase, production secrets, patients, clinical
  databases, actual devices or paid product keys.
- The test imports native extensions in a child process so Windows unlocks
  loaded `.pyd` files before cleanup.
- It does not modify the P1.1 proof, commercial build, `master`, or deployed
  software. Never merge/deploy or change repository visibility from this lab.

## Gates

EXPERIMENTAL (lab only): successful exact-SHA Linux and Windows jobs, all 12
HTTP parity cases each, plus review of the same HEAD.

REQUIRED before any commercial packaging switch: compile representative
FastAPI actual application modules; SQLCipher real-file + multi-process
behavior; imaging and scientific dependencies; Windows installer identity,
signing, rollback and recovery; patient access in all licensing failure
modes; approval from the owner. These are **not** claimed here.

This stacked PR deliberately leaves SEC-P0 #898 and the licencing architecture
as separate workstreams so functional development can continue.
