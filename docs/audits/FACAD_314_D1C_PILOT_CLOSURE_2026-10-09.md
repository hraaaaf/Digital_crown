# Facad 3.14 — D1C editor pilot: closure and controlled expansion (2026-10-09)

**Scope:** Facad Quick Demo 3.14.1.1111, official Robert example (disposable copy), `feat/cephalo-facad-direct-parity-runtime-probe`. **No patient analysis Load, no Save, no numeric parity claim.**

## Pilot outcome — CLOSED only at `EDITOR_DEFINITION_LOADED_NOT_SAVED` / observed-editor level

| Definition | Exact run | Evidence | Caveat |
|---|---|---|---|
| Steiner | [#37857655276](https://github.com/hraaaaf/Digital_crown/actions/runs/37857655276) | Definition opened and photographed in non-patient editor per canonical handover | Overall run FAILURE due to second preset modal. This is an observed editor pilot, **not** a passed full-run test. |
| Tweed | [#37861203066](https://github.com/hraaaaf/Digital_crown/actions/runs/37861203066) | SUCCESS; editor Measurements / Lines and calc. points / Markers; unsaved | UIA text element counts are not measurement counts. |
| McNamara | [#37862652488](https://github.com/hraaaaf/Digital_crown/actions/runs/37862652488) on `159946de89f31a3de7b099d1ef063d40701b398b` | SUCCESS; [artifact #11587710606](https://github.com/hraaaaf/Digital_crown/actions/runs/37862652488/artifacts/11587710606); verified editor field = `McNamara`; `d1c-McNamara-measurements.png`, `d1c-McNamara-lines.png`, `d1c-McNamara-markers.png` visually reviewed | 67 / 20 / 123 are UIA **Text** node counts, not clinical measurements, line definitions or landmark totals. |

McNamara CSV verdict: `EDITOR_DEFINITION_LOADED_NOT_SAVED` with one selected named profile. Status text records `D1C_EDITOR_SAVE_BUTTON_NOT_INVOKED=true`, `D1C_PATIENT_ANALYSIS_LOAD_NOT_INVOKED=true`, `D1C_PRESETS_LOADED_IN_EDITOR=1/1`. Source and copied `Robert-2.0.fcd` hashes before and after match: `67A81AD8D2C2489FFE84A1DFBBB897761AE855ECE4EBF948C12AF232562EC089`. The screenshots expose McNamara measurement names/types, references, line constructs, and marker labels; this is **definition visibility**, not validation of factors or normal values.

**Not proven:** clinical calculation execution, patient-specific analysis loading, shared app storage isolation, correctness of reference norms, equivalence to Digital Crown, export quality, reproducibility across new clinical cases. `CLINICAL_EDIT_ALLOWED=false`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`. No global D1C 65/65 completion.

## R1 — 62 remaining definitions, one profile per fresh runner

Canonical source of exact names: `docs/audits/data/FACAD_314_D1_LATERAL_STANDARD_65.csv`.
Evidence-state ledger: `docs/audits/data/FACAD_314_D1C_EDITOR_DEFINITIONS_LEDGER_2026-10-09.csv` (snapshot; not live CI status).
PowerShell harness: `scripts/facad_314_d1c_editor_pilot.ps1` now checks names **exactly** against all 65 Standard lateral entries before any Facad interaction.

- Each run installs *official* Quick Demo on fresh `windows-latest`, opens Robert **copy**, uses **editor-only Load**, and opens each of the three tabs.
- Refuse ambiguous UIA selection, unexpected marker overwrite modal, patient Load, clinical edits, Save, and noncanonical names.
- Require evidence: run SHA, success of parser + probe, selected-before-load screenshot, editor field name, three tab screenshots/UIA/text, CSV verdict, Save/Load guard and original/copy SHA256 before/after.
- When application-level shared storage isolation is unproven, do **not** optimize by loading two distinct definitions in one running Facad process.
- Record exact state per preset: `DISCOVERED_ONLY`, `EDITOR_DEFINITION_LOADED_NOT_SAVED`, `DEFINITION_EXTRACTED`, `PATIENT_CALC_TESTED`, `PARITY_VERIFIED`. These states are **not interchangeable**.

First extension: **Ricketts (32 F)** [#37863549712](https://github.com/hraaaaf/Digital_crown/actions/runs/37863549712), run submitted at `9bc6efd80a089e0bd4913585b12e5ea9e09aa7ec`. **Execution result not certified here.** Check its job, artifact and hashes when it finishes.

## Two adversarial internal perspectives (not independent external reviewers)

**A — evidence integrity.** BLOCKER for any claim that catalog selection = clinical Load or that UIA text counts = distinct clinical factors. McNamara's CSV, editor title/name, screenshots and two hash comparisons support the narrower editor-definition claim. Keep Steiner's red overall-run status visible. CI success without artifact is not enough.

**B — clinical/safety & privacy.** The copied `.fcd` unchanged does **not** prove isolation of registry, Facad settings or shared databases. No authorized patient edit, Save, new license/activation, prescription or unsourced norm conversion. D3 isolation gate remains open. Do not use the vendor demo case as an independent clinical oracle.

**Additional harness risk to revisit:** bootstrap code contains an early `exit 0` if `FACAD_ADMIN_SETTINGS_FOUND=true` is absent, so a workflow can in principle report green without entering D1C. For every run, **require the D1C CSV and expected screenshots** rather than trusting green CI; subsequently harden this fail-open path in a targeted change (avoid overlapping running Windows sessions).

**Convergence state:** **OPEN** for 65-definition extraction, app isolation and direct clinical parity. The three-profile *observation pilot only* is closed to its limited target. Real independent review and confirmation on exact later HEAD have not been performed.

**Next:** Inspect first Ricketts32F runner proof; if failed, diagnose exact failure; if passed, update row state and expand one named analysis at a time without violating D3.
