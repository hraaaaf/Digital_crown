# Portability P6 — Industrialized Windows packaging — CLOSEOUT

Status: **CLOSED / VERIFIED**

## Goal
Make the Windows distribution deterministic, reproducible and installable while preserving cabinet data and refusing unsafe or unqualified packaged content.

## Success verified
- the certification path builds with `DigitalCrown.spec`; the legacy `scripts/build_exe.py` path is quarantined by the static contract;
- PyInstaller is pinned at `6.16.0` for P6;
- frontend install/build uses `npm ci` + build;
- required bundle assets are fail-closed while `.env`, `firebase_creds.json` and unqualified scientific weights are forbidden;
- `VERSION` is the release identity used for Windows metadata and the Inno build;
- packaging dependencies install consistently and `pip check` passes;
- frozen and installed package self-tests both report `status=ok` with `scientific_capabilities=FAIL_CLOSED_NO_WEIGHTS`, no missing required resources and no forbidden/unqualified weights;
- exact Inno Setup `6.7.3` is downloaded from its official release, verified by SHA256 and by valid publisher Authenticode before compilation;
- clean install succeeds on `windows-2025`;
- the installed frozen runtime reaches `GET /health -> 200`;
- reinstall/upgrade succeeds;
- uninstall succeeds and reports no Windows restart required;
- the cabinet-data sentinel survives uninstall;
- the `console=False` frozen launcher keeps file logging and avoids Uvicorn console handlers that require unavailable stdout/stderr.

## Exact proof
- PR `#259`;
- certified product candidate HEAD: `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`;
- P6 Windows Packaging run `32999393374`, job `98276906459` — **SUCCESS**;
- successful critical steps: static contract, scientific policy, frontend build, packaging dependency install + `pip check`, version metadata, frozen build, frozen self-test, exact Inno setup, installer build, install/runtime/upgrade/uninstall lifecycle, lifecycle artifact, Authenticode status, installer artifact;
- exact-head regressions — **SUCCESS**: Runtime `32999393381`, T2 `32999393529`, P5 Native `32999393360`, Catalog `32999393394`, P11 `32999393369`, Patient P7 `32999393410`, CI `32999393419`, P8 Hardware `32999393352`.

### Retained artifacts
- lifecycle: `digitalcrown-p6-installer-lifecycle-logs`, id `9618198566`, archive digest `sha256:a68fbcdc17953a5995c50c1ea6271d710c997aa2a7b6aadcbe286656bde4fb7a`;
- installer: `digitalcrown-p6-windows-installer`, id `9618206397`, archive digest `sha256:de9b4a82ef39e51c755be578d04fd65334ad00cfe7c4255cb30104a3697e1398`;
- exact installer file: `DigitalCrownSetup-1.0.0.exe`, SHA256 `24e662dd88a941b7c10017e0c34470a1b4206185852102e79bd624f372163edd`.

### Lifecycle evidence
Frozen self-test and installed self-test both prove:
- `frozen=true`;
- `status=ok`;
- `version=1.0.0`;
- `missing=[]`;
- `forbidden_present=[]`;
- `scientific_capabilities=FAIL_CLOSED_NO_WEIGHTS`;
- `scientific_manifest_policy_ok=true`;
- `unqualified_scientific_weights_present=[]`.

The retained runtime log proves the installed frozen runtime answered `/health` with HTTP 200. Inno install and upgrade logs report `Installation process succeeded`; uninstall reports `Uninstallation process succeeded`, `Removed all? Yes`, `Need to restart Windows? No`. The workflow throws if the data sentinel is missing, so successful lifecycle completion proves preservation.

## Authenticode product truth
The product-signing path is implemented and performs `signtool sign` + timestamp + `signtool verify` when `WINDOWS_CODESIGN_PFX_B64` is provisioned.

For this certified candidate, the distribution certificate was **not configured**. The exact uploaded installer has PE Certificate Table `offset=0`, `size=0`, which cross-validates the workflow branch `P6_AUTHENTICODE=NOT_CONFIGURED`.

Therefore:
- **no signed Windows distribution is claimed**;
- P6 satisfies its canonical contract because signing/timestamp is required when the distribution certificate is available;
- provisioning the real distribution certificate remains required before claiming a signed public/cabinet release.

## Scope notes / limits
- P6 changes packaging/runtime behavior, not product UI; no visual BEFORE/mockup/AFTER gate applies.
- P6 deliberately packages no unqualified scientific weights and makes no clinical-accuracy claim.
- P12/P13 still own the final cross-platform matrix and real-cabinet certification.
- No Vercel deployment was performed or authorized.

## Progress
Previously credited: `73 EP`.
P6 credit: `8 EP`.
Credited effort: `81 EP` out of `162 EP` = **50.0%**.

No partial EP are credited for an open lot.

## Next exact
P7 — Native macOS packaging: audit the existing `macos/` surface, freeze an Apple Silicon `.app` packaging contract, integrate Developer ID / Hardened Runtime / notarization fail-closed, then certify clean install, upgrade and uninstall on macOS.
