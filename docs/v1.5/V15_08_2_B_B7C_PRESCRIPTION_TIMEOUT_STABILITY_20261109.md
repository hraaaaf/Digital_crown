# Digital Crown — LOT08.2-B / B-7c — PrescriptionForm test stability — 2026-11-09

**Scope:** explicit owner GO after B-7; fix the last observed frontend Vitest regression without modifying clinical prescription behavior, loosening patient safety assertions or using real patients. Starting branch `feat/v15-08-2-b-rbac-isolation-20261109`, remote PR [#1239](https://github.com/hraaaaf/Digital_crown/pull/1239) OPEN / DRAFT / not merged, starting SHA `82248e25c9eecc12c4b63052d40a9aee1c22a6f1`.

## BEFORE: measured RED

The third complete frontend Vitest run on Windows, tracked by the preceding B-7 Notion checkpoint, exited **1** after 456.19 s: **2022 PASSED / 1 FAILED** over **388 suites (387 passing)**. Its only failure was `src/features/admin/DocumentStudio/PrescriptionForm.g4Interactive.test.tsx`, test **`applies each quick prescription through the preset boundary`**; exact failure: **Test timed out in 5000ms**, at line 36. This is **not** evidence that any real medication or clinical prescription failed, and no runtime handler assertion was failing. A separate isolated Vitest run of the unchanged PrescriptionForm file returned **7/7 PASS** in 36.51 s total with **2.77 s actual tests**. The discrepancy is consistent with runner saturation, not proof of clinical validity.

The two prior load-sensitive test fixes `ClientFacingCopyCandidateAudit.test.ts` (20 s AST-audit timeout with full scan/zero bad wording still checked) and `PatientDraftRouteGuard.test.tsx` (checks both the new patient identity and the cleared editor after navigation) passed in prior focused runs; they existed as **uncommitted changes**, not part of SHA `82248e2`.

## ACTION: stronger oracle + bounded test budget

In the **test only**, `PrescriptionForm.g4Interactive.test.tsx` now checks **all four** quick-prescription buttons, and after each click it verifies the corresponding call to `onApplyPreset` in order, the **exact preset label**, and presence of a named drug in the callback payload, in addition to total call count four. Its explicit **20 s** timeout compensates for heavy concurrent jsdom/React runner activity during the full suite. No medication list/dose, runtime automatic behavior, `PrescriptionForm.tsx`, patient data or actual clinical treatment plan is changed. This verifies the UI callback wiring, **not** medical appropriateness of preset drugs or regimens.

## Success / proof gate

- Isolated PrescriptionForm BEFORE: **7/7 PASS** with tests 2.77 s, exact same 5-second default limit.
- **AFTER focused regression** (four high-risk suites, including PrescriptionForm, draft patient guard, M4-C documents and exhaustive batched copy audit): **34/34 PASS / exit 0**; 4/4 suites PASS, Vitest 78.20 s process summary (actual per-suite test clocks summed 54.31 s). No clinical/production code changed.
- **Audit refactor**: `ClientFacingCopyCandidateAudit.test.ts` still uses the **same** AST parser, all ~938 TS/TSX source-tree paths collected and its original source filter, unchanged technical-copy patterns and explicit empty findings oracle, but discovers all production source files once and tests consecutive **48-file batches**. Coverage test asserts every discovered file is scanned **exactly once**; no source file or pattern is excluded. This replaces the single heavy AST test that timed out even at 20 seconds when run concurrently.
- **Prescription test**: 7/7 PASS isolated before; stronger 4 preset callback payload/order assertions in the new focused 34/34 pass. No actual drug dose, product code, or treatment validation touched.
- TypeScript, complete frontend Vitest, source/hashes and GitHub exact-head candidate/Queue Core/Scope workflow outcomes must be reported only after verification.
- If the full suite is RED again, distinguish new functional failures from tests under heavy load; do not claim full green based only on isolated success.

**Never do without separate GO:** merge PR to master, create `CODE_CERTIFIED`, package EXE, run the installed clinic app, link real appointments, migrate real records, deploy to production, or perform physical LOT10 tests. B-6 remains `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO`.

**Next exact:** verify focused and full tests; commit safe test corrections only to PR #1239 after green evidence; inspect exact SHA GitHub Actions jobs and logs; synchronize Notion. Keep LOT08.2-B OPEN until all human/installable gates are satisfied.

## B-7c CLOSEOUT — exhaustive Windows frontend **sharded** regression (2026-11-09)

**Code actually tested:** `66c2f3d4fb0efc6fa5d99a2d15211a5b02c4203f` in the remote Windows checkout. **Execution:** 388 discovered TS/TSX test files, sorted into **9 separate Vitest invocations**, batches of 48 and a final batch of 4, with `--maxWorkers=2 --minWorkers=1 --reporter=dot`. The workstation has approximately **8 GB RAM**; the earlier uncontrolled single invocation was subject to resource saturation. No clinical DB, patient records, release artifact or installable involved.

**SUCCESS / independent recheck of raw log files:** each shard returned **exit 0**, and all **9 raw logs** were reparsed after stripping terminal ANSI escape sequences. Each file count, test count, expected shard size and no-fail summary matched the observed terminal verdict. An independent aggregate check returned **`ALL_VERIFIED=True FILES=388 TESTS=2035`, exit 0**. **0 test failures**, **9/9 shards passed**.

| Shard | Files passed | Tests passed |
|---|---:|---:|
| 01 | 48 | 271 |
| 02 | 48 | 264 |
| 03 | 48 | 215 |
| 04 | 48 | 263 |
| 05 | 48 | 274 |
| 06 | 48 | 237 |
| 07 | 48 | 268 |
| 08 | 48 | 224 |
| 09 | 4 | 19 |
| **TOTAL** | **388 / 388** | **2,035 / 2,035** |

**Verifiable machine-readable evidence:** `docs/v1.5/evidence/lot08_2_b7c_windows_vitest_shards_20261109.json` contains source SHA, all 9 actual per-log SHA-256 hashes, raw byte lengths, pass counts and exact per-shard exit evidence. The original logs remain exclusively in the owner's Windows test workspace `DigitalCrown-B7C-Shard-Evidence\shard-01.log` ... `shard-09.log`, **not committed**. For shards 02–09 the driver's `remaining-shards.json` was checked against counts and actual exit codes. Shard 01 exit 0 was observed independently in terminal output. The evidence manifest itself is a summary, not a substitute for raw-log integrity review.

**Reproduce (Windows PowerShell on a clean checkout, not clinic):** build sorted inventory with `Get-ChildItem frontend/src -Recurse -File` and pattern `\.(test|spec)\.[cm]?[jt]sx?$`, partition into 48-file slices, invoke `frontend/node_modules/.bin/vitest.cmd run <slice paths> --maxWorkers=2 --minWorkers=1 --reporter=dot` once per shard; require the expected Test Files pass count **and** process exit 0 on every shard. Validate hashes of stored raw logs against the JSON. The last batch contains four files. Do not reuse a machine's local fixtures, credentials or patient profile.

**LIMITATION (essential):** this is **exhaustive sharded Windows LAB regression**, NOT a single simultaneous `npm test` green run and **NOT** GitHub Linux candidate `CODE_CERTIFIED`. Separate test processes can avoid resource contention that appears in the monolithic default run; that difference must remain visible in closeout. It does not prove clinical prescription correctness, certified package, native installed execution, real patient mapping, physical LOT10 or cabinet readiness. The previous monolithic Vitest runs remain historically **RED** under heavy RAM pressure; none is rewritten as a pass. PR #1239 remains DRAFT and LOT08.2-B OPEN.

**GitHub gate, independently investigated:** the GitHub connector's **first-page-only** pull-request run lookup returned zero entries for the tested SHA, but a second **read-only public GitHub Actions API query with exact `head_sha=66c2f3d`** returned **one real run**: [UI Human Visual Approval #42686757746](https://github.com/hraaaaf/Digital_crown/actions/runs/42686757746), event `pull_request_target`, **COMPLETED/FAILURE**. Its actual job logs state: `Visual gate fails closed: PR HEAD changed: approval revoked; new screenshots and explicit approval required`. This is a legitimate human approval gate, **NOT** a Queue Core or CODE_CERT candidate CI failure; never bypass it. No Queue Core, Scope Gate or complete CODE_CERTIFIED **candidate** run at the tested HEAD was confirmed by the exact-head public API at that checkpoint. PR #1239 was **mergeable_state=dirty** (conflicts with master) when checked read-only. Neither CI nor release certification is accepted; even green candidate CI would not be official master `CODE_CERTIFIED`.

### Additional exact-source build and cleanup proof

With the tested source SHA still exactly `66c2f3d4fb0efc6fa5d99a2d15211a5b02c4203f`, Windows `tsc --noEmit -p tsconfig.app.json` **PASS** followed by safeguarded `npm run build:test` **PASS / exit 0**, Vite 7.3.8 with PWA 88-entry precache. Guard reported `mode=test outDir=dist-test port8005Live=false`; `dist-test/build-manifest.json` reported `environment=test`, `commit=66c2f3d4fb0efc6fa5d99a2d15211a5b02c4203f`, `mode=test`, `outputDir=dist-test`. The nonfatal chunk-size warning is not a test failure. **No installed Desktop EXE was built**.

A guarded cleanup after confirming no Vitest/Vite process remained deleted only the identified untracked synthetic audit `audit/out/frontend.json` and the generated `frontend/dist-test` after verifying its exact SHA/test-mode manifest, no tracked files, no clinical DB/secret, no reparse points. The nine raw logs were **retained on the test workstation** to enable verification against SHA-256 hashes. The only intentional Git changes afterward were this report, `STATE.md` and the machine-readable evidence manifest.
