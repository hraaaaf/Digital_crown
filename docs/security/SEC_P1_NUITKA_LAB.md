# SEC-P1 — Native backend feasibility laboratory (EXPERIMENTAL)

## Goal and boundary

Test whether Nuitka can compile **one existing, dependency-free backend module**
(`backend/core/key_material.py`) into an importable native Python extension
without changing its observable behavior. This is NOT a new Digital Crown EXE
and is NOT a licensed/security-certified release.

The experiment uses `Nuitka==4.3`, Python 3.12, Ubuntu **and Windows**, a temporary
copy of the source, and **synthetic** hexadecimal test fixtures only. All
compiled artifacts are automatically deleted after the comparison.

## Run

```bash
python -m pip install Nuitka==4.3
python scripts/security/sec_p1_nuitka_lab.py
```

Evidence target on **each OS**: a real native extension (`.so` with ELF signature
on Linux, `.pyd` with PE/MZ signature on Windows) can be compiled and imported;
11 comparisons of normal and rejection paths match the Python implementation,
including SQLCipher key separation and mobile key derivation. The script prints
the native format, extension SHA-256 digest and size, without secrets.

[Experimental Linux/Windows workflow](../../.github/workflows/sec-p1-nuitka-parity-lab.yml)
is **EXPERIMENTAL** and is not a release or required gate for unrelated PRs.

## Boundaries and security non-claims

- Existing `DigitalCrown.spec`, `run.py`, API routes, database keys, and
  production build/install policy are left unchanged.
- This prototype does not run the entire FastAPI backend as a compiled EXE.
- Nuitka compilation does **not** make reverse engineering impossible and
  provides no standalone enforcement of commercial licensing.
- No performance, startup-time, binary-signing, antimalware, Windows installer,
  native imaging, SQLCipher database runtime, frontend/mobile, or full
  FastAPI compatibility claims can be made from this lab. Successful Windows
  extension tests would not certify a complete Windows backend.
- No patient data, credentials or privileged Firebase service accounts are
  stored, read or emitted in this workflow.
- The original module retains its historical compatibility behavior; this
  experiment is not an audit/endorsement of any fallback-secret policy.
- Private license-signing keys must never be shipped in client executables,
  whether built with Nuitka or PyInstaller. Patients must be able to access
  and export their data during billing/license incidents.

## Follow-on gates (not achieved here)

1. Linux native extension parity (experimental CI).
2. Windows native extension parity in isolated CI (experimental CI); verify
   real PE/PYD output plus the same 11 parity cases before claiming a pass.
3. Representative FastAPI/SQLCipher/scientific runtime parity.
4. Installer signing, provenance, recovery, update/rollback rehearsals and
   actual distribution tests on supported Windows machines.
5. Separate commercial license design: asymmetric editor-issued signatures,
   client-side public verification, cabinet/device binding, offline grace,
   revocation and non-destructive clinical continuity.
6. Product owner approval **before** changing the canonical packaging,
   merging into the release branch, installing or deploying.

The separate SEC-P0 packaging hardening PR #898 must be assessed against the
current `master` before any decision to merge. It is not a prerequisite for
running this synthetic laboratory.
