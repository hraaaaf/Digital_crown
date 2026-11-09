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
