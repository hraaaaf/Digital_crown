# Digital Crown — Windows installable runtime audit — 2026-09-17

## Goal

Produce a cabinet-safe path from current `master` to an immutable `INSTALLABLE_CERTIFIED` runtime without touching the live cabinet database/media until all gates are proven.

## Success

Observable success requires all of the following on one exact SHA:

1. backend boot on Windows without mock substitution;
2. exact runtime asset certification and composition;
3. successful `INSTALLABLE_CERTIFIED` verification;
4. fresh rehearsal on clones of the cabinet DB/media;
5. authenticated read-path smoke for patients, documents, media and clinical records;
6. `EXECUTION_SCORE` and `ADVERSARIAL_SCORE` computed from evidence, with `VERIFIED=YES` only if every required gate passes.

## Evidence baseline received from cabinet rehearsal

Historical master candidate tested on cabinet: `b91924d67aa0f0d8d79af32c9c028ccb874e7af4`.

The clone rehearsal preserved counts/hashes and reached `/api/health` HTTP 200, but full Windows backend startup failed while importing/loading PyTorch with `OSError: [WinError 1455]` (insufficient paging-file/commit limit). No real cabinet checkout, migration or activation was performed.

## Re-baseline

Repository master observed at audit start:

`fb47c6779e53dd2172b68409f719f18e9a131322`

The prior cabinet result therefore remains strong compatibility evidence for the data path but is not sufficient certification for the newer master.

## Finding 1 — eager legacy PyTorch loading was a backend boot hazard

`backend/services/vision_service.py` imported PyTorch at module import and initialized the legacy CephLD-CCA model from the singleton constructor, even though SRPose38 ONNX is the certified primary path.

On Windows, a PyTorch import may raise an `OSError` such as WinError 1455 rather than `ImportError`, so the existing `except ImportError` did not protect backend boot.

### Remediation

PR #573, head `ebc5ca0a4cb2b32c9bab572d1cca6177361a28e5`:

- removes PyTorch/model loading from backend boot;
- keeps SRPose38 ONNX as the first inference path;
- lazy-loads the legacy PyTorch fallback only if SRPose cannot produce landmarks;
- catches PyTorch import/runtime failures fail-closed;
- preserves manual-placement fallback when no inference engine is available;
- adds regression tests for lightweight construction, SRPose bypass and WinError 1455 handling.

CI general run `35236240846`: SUCCESS on this head.

This change removes the pagefile error from the mandatory backend-boot path. It does not certify the legacy PyTorch fallback itself on the cabinet machine.

## Finding 2 — SRPose38 certified asset is recoverable and byte-identical

`backend/scientific_assets.json` pins:

- path: `backend/ai_models/srpose38-tta-1024.onnx`
- size: `267484931` bytes
- SHA-256: `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`

Historical GitHub Actions artifact:

- run: `34281082926`
- artifact id: `10077697721`
- artifact name: `cephalo-srpose38-onnx-parity`
- artifact currently unexpired at audit time.

The downloaded ONNX inside that artifact was independently re-hashed during this audit:

- size: `267484931` bytes
- SHA-256: `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`

Result: exact match to the scientific registry.

The artifact also contains parity evidence with ONNX-vs-PyTorch heatmap max absolute error `5.960464477539062e-07` and coordinate max delta `0.0001999200562387517 px` for the recorded parity sample.

## Finding 3 — legacy U-Net and panoramic assets are not scientifically pinned

`backend/scientific_assets.json` currently records:

- `cephalo_legacy`: external, unpinned;
- `panoramic`: external, unpinned.

`runtime_asset_certification.py` requires every pinned scientific asset to exist and match its pin. Therefore an `INSTALLABLE_CERTIFIED` release cannot omit the pinned SRPose38 asset, but the current policy does not require an unpinned legacy U-Net or panoramic model to exist.

Clinical behavior remains fail-closed when panoramic inference is unavailable in `production`/`cabinet` mode. The legacy U-Net is a fallback behind SRPose38 after PR #573.

Conclusion: do not invent or substitute U-Net/panoramic binaries. Their absence is a feature-availability limitation, not a reason to package unknown bytes as clinically validated assets.

## Finding 4 — dependency environments are not yet one reproducible cabinet environment

Three dependency contracts currently diverge:

- root `requirements.txt`: `torch` and several packages are unpinned;
- `backend/requirements-p5-native.txt`: `torch==2.10.0`, `torchvision==0.25.0` plus a pinned native-test stack;
- `.github/workflows/cabinet-release-certification.yml`: backend certification explicitly installs `torch==2.12.0` and `torchvision==0.27.0` before installing the remainder of `requirements.txt`.

Therefore the raw Git checkout is not itself a reproducible Windows cabinet runtime. This is consistent with the repository policy that only `INSTALLABLE_CERTIFIED` is installable, but the final Windows build environment still needs one explicit dependency/build contract before production installation can be claimed reproducible.

Do not resolve this by arbitrarily choosing 2.10 vs 2.12. The selected build/runtime stack must be validated by the Windows portability gate and by the final installer build/rehearsal.

## Windows memory/pagefile interpretation

WinError 1455 is a Windows commit-limit/pagefile exhaustion condition. The safe remediation is operational: ensure the system-managed pagefile has sufficient disk headroom and measure peak commit on the target machine. There is no universal fixed pagefile size that can be certified from repository code alone.

After PR #573, this issue should no longer block ordinary backend boot when SRPose38 ONNX is available, because the legacy PyTorch runtime is no longer eagerly loaded.

## Current verdict

`VERIFIED = NO`

Reason: code boot hazard is corrected on PR #573 and SRPose38 bytes are recovered/verified, but the exact final master SHA, final `CODE_CERTIFIED`, composed `INSTALLABLE_CERTIFIED`, Windows build/runtime proof, fresh clone rehearsal and authenticated read smokes do not yet all exist for one immutable candidate.

## Next exact

1. complete remaining PR #573 gates and merge only if exact-head CI is green;
2. re-baseline master after merge and after concurrent chantier merges settle;
3. run the canonical `Cabinet Certified Release` workflow on the final intended master SHA;
4. recover SRPose38 from artifact `10077697721` and place it at the canonical ai-model path for runtime-asset certification;
5. certify runtime assets and compose `INSTALLABLE_CERTIFIED` for the same SHA;
6. build/verify the Windows distribution from that immutable release;
7. perform a fresh isolated cabinet rehearsal and authenticated read-only smoke;
8. compute evidence-backed execution/adversarial scores;
9. only after all gates pass, consider real cabinet activation with the already-defined backup/rollback procedure.
