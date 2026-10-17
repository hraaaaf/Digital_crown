# SEC-P1.3 — Experimental Windows executable packaging comparison

## Product goal

Evaluate whether Nuitka standalone is a feasible packaging technology for a
later release of Digital Crown **without rebuilding or modifying the certified
commercial executable**. Compare against PyInstaller onedir as a technology
baseline on the exact same test code and Windows runner.

### Precise probe identity

Both build methods receive one identical synthetic staging tree:

- the **byte-identical** production source
  `backend/core/key_material.py` copied only into temporary
  `dc_p13_synthetic_backend/key_material.py`;
- the synthetic entrypoint
  `scripts/security/sec_p1_3_windows_probe_entry.py`, which uses
  FastAPI `TestClient` to invoke the real module on **eight synthetic**
  success and denial cases;
- trivial synthetic package `__init__.py`, avoiding the commercial
  `backend/__init__.py` that eagerly imports database/clinical models.

One `PyInstaller --onedir` and one `Nuitka --mode=standalone` executable
are created. Both run in separate processes three times each, returning
precisely the same JSON as ordinary source Python. The test verifies
real PE executable headers, runtime responses, strict expected HTTP statuses,
hashes, executable and distribution directory sizes, startup median, and
build duration. Results are printed to GitHub Actions logs.

### Strict exclusions and threat model

**Neither executable is the Digital Crown application.** No real
`backend.main`, Windows installable release, real Uvicorn socket, SQLCipher
file, Firebase credentials, scientific AI model, imaging driver, frontend,
medical records, real license, or patient information are loaded or packaged.

- The official `DigitalCrown.spec` mandates
  `verify_installable_release_directory` (release certification and
  provenance checks); the commercial launcher `run.py` mandates
  `verify_installable_release_identity`. The lab checks that both gates
  remain present, but **does not call, bypass, relax, or claim to satisfy**
  either requirement. The technology baseline uses the CLI with a distinct
  `dc_p13_pyinstaller.exe` identity, never the actual spec.
- Both temporary distribution directories are automatically deleted at
  successful exit; no uploaded public `.exe` CI artifact.
- The synthetic HTTP app does not listen on any port, interact with actual
  Windows installations, or use external patient/device data.
- Temporary env is narrowed before running the executables.
- No compiler/packaging alone prevents reverse engineering or cracking.
  Private commercial license signing keys must remain external to client
  installers, even if the backend is compiled with Nuitka.
- Windows native packaging with FastAPI `TestClient` and one genuine
  key-material module **cannot validate** all Windows DLLs, post-boot
  configuration, encrypted database, AI, Imaging Bridge, updater, browser UI,
  antivirus false positives, code signing, rollback, or backup/export.

## Repro / evidence

Workflow: [SEC-P1.3 Windows experimental comparison](../../.github/workflows/sec-p1-3-windows-packaging.yml).
Harness: `scripts/security/sec_p1_3_windows_packaging_compare.py`.

Runs on Windows 64-bit Python 3.12, pinned
`Nuitka==4.3`, `PyInstaller==6.16.0`,
`FastAPI==0.115.6`, `Pydantic==2.6.3`,
`Starlette==0.41.3`, `httpx==0.28.1`.

Required experimental proof: immutable PR SHA, successful source and both
packaged probes (8/8 HTTP cases each, repeated 3 times), PE validity,
cleanup and metrics in the same CI run. Startup measurements are descriptive,
**not** a dependable cross-hardware performance benchmark.

**No go-live approval, no deployment, no merge, and no change to the
public repository visibility.**

## Future REQUIRED release gates, not accomplished here

1. Build the actual complete commercial backend **only from an authorized
   INSTALLABLE_CERTIFIED release** (never spoof certification).
2. Ensure deployment integrity, code-signing, installer, Windows dependency
   resolution, comprehensive SQLCipher PostgreSQL and offline/restore behavior.
3. Confirm FastAPI real endpoints, actual frontend desktop/mobile feature
   availability, clinical and Imaging Bridge workflows.
4. Rehearse update / rollback / data extraction with patient continuity.
5. Perform true independent security and integration reviews at one immutable
   release HEAD and obtain explicit owner GO before packaging changes.

This PR is stacked on SEC-P1.2d [#939](https://github.com/hraaaaf/Digital_crown/pull/939)
and remains **EXPERIMENTAL / DRAFT**.
