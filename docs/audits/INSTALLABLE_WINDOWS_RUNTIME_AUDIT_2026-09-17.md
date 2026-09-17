# Digital Crown — Windows installable runtime audit — 2026-09-17

## Goal

Produce a cabinet-safe path from canonical V0 (`76547ed178b98b4d8cf14c0fdc691ff3f787076e`) to one immutable future V1 `INSTALLABLE_CERTIFIED`, without touching the live cabinet DB/media before all gates are proven.

## Success

Success requires, on one exact SHA:

1. Windows backend boot without mock substitution;
2. one reproducible cabinet runtime/build dependency contract;
3. exact runtime-asset certification and `INSTALLABLE_CERTIFIED` composition;
4. Windows package build from that immutable release;
5. fresh rehearsal on isolated clones of cabinet DB/media;
6. authenticated read-only smoke for patients, documents, media and clinical records;
7. evidence-backed execution/adversarial scoring with every binary gate green.

Until then: `VERIFIED = NO`.

## Cabinet data compatibility baseline

Historical candidate rehearsed against cabinet data: `b91924d67aa0f0d8d79af32c9c028ccb874e7af4`.

Observed clone result:

- tables `81 -> 91`;
- total rows `3489 -> 3489`;
- patients `300 -> 300`;
- document archives `407 -> 407`;
- media `2812 files`, `362015320 bytes`, unchanged fingerprint;
- data and historical-relation fingerprints unchanged;
- Alembic second upgrade no-op;
- `/api/health` HTTP 200.

No real cabinet checkout, migration or activation was performed. This remains compatibility evidence, not certification for current master.

## Closed blocker — eager PyTorch boot / WinError 1455

PR #573 removed PyTorch/CephLD-CCA loading from the mandatory backend boot path. SRPose38 ONNX remains the primary path; legacy PyTorch is lazy and fail-closed.

Final PR head:

`00350cd8f06cb9bb7d04b872347a820994059a70`

Exact-head gates before merge:

- CI `35237538086`: SUCCESS;
- Portability P5 `35237538474`: SUCCESS on Windows and macOS, including lazy-PyTorch/WinError-1455 contract;
- T2 `35237538407`: SUCCESS.

Merged master SHA:

`3beea0a4cee0eb227bd531d1aaf0ea29d13c4118`

Result: legacy PyTorch memory/pagefile exhaustion is no longer allowed to take down ordinary backend boot. This does not claim that legacy PyTorch inference itself is certified on the cabinet machine.

## Recovered scientific asset — SRPose38

Canonical registry pin:

- path `backend/ai_models/srpose38-tta-1024.onnx`;
- size `267484931` bytes;
- SHA-256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`.

Recovered source:

- workflow run `34281082926`;
- artifact `10077697721` (`cephalo-srpose38-onnx-parity`).

Downloaded ONNX size/hash exactly match the scientific registry. No reconstruction/substitution is required.

`cephalo_legacy` and `panoramic` remain external and scientifically unpinned. Unknown replacement bytes must not be invented or represented as clinically validated. Missing panoramic inference remains fail-closed in cabinet/production.

## Open lot — reproducible Windows runtime/build contract

Branch:

`fix/windows-build-dependency-contract`

Base:

`3beea0a4cee0eb227bd531d1aaf0ea29d13c4118`

### Findings

The previous runtime/build definitions diverged:

- root `requirements.txt` contained a second, partially unpinned stack;
- P5 certified `torch==2.10.0 / torchvision==0.25.0 / torchaudio==2.10.0`;
- release certification temporarily installed `torch==2.12.0 / torchvision==0.27.0`;
- root Windows requirements installed both `onnxruntime` and `onnxruntime-directml` variants.

ONNX Runtime upstream requires one Python runtime variant per environment. The certified SRPose38 path uses CPU execution, so the cabinet baseline is now CPU ONNX; DirectML is not an implicit dependency of the installable baseline.

### Implemented on the branch, not yet certified

- `backend/requirements.txt` is being converted into the exact top-level cabinet runtime lock;
- root `requirements.txt` is now a pure alias to that canonical lock;
- native stack remains aligned with `backend/requirements-p5-native.txt`;
- required cabinet packages that are genuinely imported/used are restored with exact pins, including Alembic, Firebase Admin, Sentry SDK, WebAuthn and python-magic;
- `backend/requirements-windows-build.txt` adds the pinned Windows build toolchain with `pyinstaller==6.22.3`;
- `backend/scripts/windows_build_dependency_contract.py` rejects unpinned top-level requirements, native-stack drift, conflicting ONNX Runtime variants and root-lock duplication;
- `backend/scripts/build_installable_windows.ps1` refuses non-Windows execution, verifies `INSTALLABLE_CERTIFIED` before consuming build inputs, builds from a temporary venv outside the immutable release, runs `pip check`, then invokes PyInstaller and records environment/source/executable hashes;
- `.github/workflows/windows-build-dependency-contract.yml` prepares a clean Windows Python 3.12 install/import/version gate and captures the fully resolved environment for the next lock-tightening pass;
- `Cabinet Certified Release` is updated to certify against the canonical dependency contract rather than the old transient torch 2.12 stack.

These changes are **not yet proven** until the clean Windows workflow runs on the final branch head.

## Post-merge evidence for #573

Master CI run `35238446687`:

- frontend: SUCCESS;
- production-negative guard: SUCCESS;
- full backend regression: still in progress at last deliberate check.

Cabinet Upgrade PostgreSQL run `35238446469`:

- Windows PowerShell 5.1 release guards: SUCCESS;
- PostgreSQL job: CANCELLED during dependency installation; no preservation verdict may be inferred from that cancelled job.

Therefore #573's PR proof is strong, but current master closeout is not upgraded to `VERIFIED` from these post-merge runs alone.

## Current verdict

`VERIFIED = NO`

Current blocker to the next gate: the clean Windows dependency/build contract has not yet run on its final branch head. No cabinet data or runtime has been changed.

## Next exact

1. finish static branch preparation;
2. run exactly one clean Windows dependency/build-contract benchmark on the final branch head;
3. if it exposes resolver/import drift, correct the lock and rerun the failed gate;
4. require P5 + relevant CI gates green, then merge with exact-head guard;
5. re-baseline master;
6. only after the product feature chantiers settle and a V1 candidate SHA is intentionally selected, run `Cabinet Certified Release` on that exact SHA;
7. recover the proven SRPose38 artifact, certify runtime assets and compose `INSTALLABLE_CERTIFIED` for the same SHA;
8. build the Windows distribution from that immutable release;
9. perform fresh isolated cabinet rehearsal + authenticated read-only smokes;
10. compute final scores and only then consider real cabinet activation with backup/rollback revalidated.
