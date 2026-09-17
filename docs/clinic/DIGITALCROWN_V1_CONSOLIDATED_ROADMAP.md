# Digital Crown — V1 Consolidated Roadmap

Status: **CANONICAL / EXECUTION LOCKED / NOT OPERATIONAL**

Effective date: 17 September 2026

## 1. Authority — single roadmap

This file is the **sole execution roadmap for Digital Crown until `V1_OPERATIONAL`**.

Until `V1_OPERATIONAL` is explicitly recorded here:

- only the current unlocked lot may advance;
- fixes/tests/docs strictly required to pass that lot are allowed;
- later-lot PRs remain parked and cannot authorize work or merge;
- every other ROADMAP/PLAN/HANDOVER/BACKLOG/OBJECTIVE is evidence/context only;
- no competing V1 roadmap may be created or used;
- no Vercel deployment is authorized;
- no real cabinet/production mutation is authorized before the final cabinet-update lot and explicit human authorization.

## 2. Global Goal / Success / Proof

**Goal:** produce the first operational V1 cabinet release from canonical V0 while preserving real cabinet data, historical integrity and rollback capability.

**Canonical V0 SHA:** `76547ed178b98b4d8cf14c0fdc691ff3f787076e`

**V1 candidate SHA:** **NOT SELECTED**

**Success:** all mandatory lots below close in order; one exact candidate is frozen; that exact candidate reaches `INSTALLABLE_CERTIFIED` on a fresh isolated restore of real PREUPDATE cabinet data; the same SHA is installed only after explicit human authorization; post-update integrity/startup/smokes pass; rollback remains verified.

**Proof:** exact SHAs + run IDs + tests/runtime evidence + migration/integrity evidence + lot closeouts recorded in this file.

## 3. Verified starting baseline — 17 September 2026

Master before this roadmap refresh: `0483883445d432ce6c7887dfab800a559c99dec4`.

Already acquired on master and therefore **not future V1 lots**:

- Connect Hub: PR `#557` integrated.
- Céphalo injected legacy fallback repair: PR `#579` merged.
- FAR / Mutuelles: PR `#559` merged at `20d2e01aa1f097ca93dd0a5a6699a596a392d7d8`; FAR global closeout then reached master `0483883445d432ce6c7887dfab800a559c99dec4`.
- obsolete/superseded PRs `#279`, `#401`, `#407`, `#505`, `#563`, `#578` are closed and are not future execution lots.

Important correction: the previous draft roadmap incorrectly listed already-integrated Connect Hub and FAR as future mandatory lots and referenced closed PRs as future work. This consolidated roadmap removes those contradictions.

Security/physical historical programs `#288`, `#289`, `#383` are **not promoted into the mandatory V1 path by default**. They remain parked unless a concrete requirement from a mandatory lot proves a bounded delta necessary for V1 installability/safety. They must not be resurrected wholesale.

The stale documentation PR `#577` is a competing pre-consolidation roadmap and is to be closed without merge.

## 4. Mandatory execution sequence

### LOT V1-00 — Foundation: CI / Windows / dependency contract

Status: **MERGE_READY — HUMAN MERGE AUTHORIZATION REQUIRED — NOT CLOSED**

Current working reference: PR `#582`, branch `fix/v1-00-foundation-contract-current-master`.

Reconstruction base master: `569f0771ded59c4409c17155d659d037bc9b2b40`.

Certified product HEAD: `cc34fdf42874f06d4ac3ec45073e1cbb012c6007`.

PR `#580` / HEAD `3ce59839156e053fb12ba920b94838c9cbc11a42` is retained only as historical baseline evidence; it was not rebased or merged into the current reconstruction.

Goal: establish one coherent, reproducible runtime/build dependency contract on the actual current master, including clean Windows Python 3.12 validation and stable Linux CI consumers.

Pre-merge Success evidence on certified product HEAD `cc34fdf42874f06d4ac3ec45073e1cbb012c6007`:
- root `requirements.txt` and `backend/requirements.txt` are an exact 140-package lock mirror;
- WebAuthn/cryptography contract is pinned to `webauthn==3.0.0` + `cryptography==49.0.0`;
- `svglib==1.5.1` is retained in the default lock to avoid the Cairo regression introduced by the previous `svglib==1.6.0` dependency shape;
- Windows build-only toolchain is isolated in `backend/requirements-windows-build.txt` with `pyinstaller==6.22.3`;
- Media C4 now supplies the explicit DB-isolation attestation required by `backend/core/runtime_safety.py`; Patient UX1-C already carried the same contract;
- Windows Build Dependency Contract run `35261174495` — **SUCCESS** on Windows Server 2025 / CPython 3.12.10; static contract reported `ROOT_REQUIREMENTS_MIRROR=OK`, `WINDOWS_RUNTIME_LOCK=OK (140 exact top-level dependencies)`, `WINDOWS_P5_NATIVE_PARITY=OK`, `WINDOWS_BUILD_TOOLCHAIN=OK`, `WINDOWS_BUILD_DEPENDENCY_CONTRACT=SUCCESS`; clean install completed; `python -m pip check` reported `No broken requirements found`; version proof passed; cabinet import smoke reported `WINDOWS_CABINET_IMPORT_SMOKE=OK`;
- CI run `35261174409` — **SUCCESS**;
- Portability P5 Native Dependency Certification `35261174502` — **SUCCESS**;
- Media C4 Visual Certification `35261174469` — **SUCCESS**, including isolated backend start and responsive browser matrix;
- Patient UX1-C Overlay Visual Certification `35261174611` — **SUCCESS**, including isolated backend start and 390 / 768 / 1280 capture matrix;
- Patient P7 Final Certification `35261174478` — **SUCCESS**;
- T2 Runtime Browser Certification `35261174525` — **SUCCESS**;
- Catalog Connected Truth Certification `35261174529` — **SUCCESS**;
- Marketplace Final Certification `35261174526` — **SUCCESS**;
- M6-I Biometric Passkey Certification `35261174425` — skipped by workflow conditions, not a failure;
- PR Merge Summary `35261174500` — skipped by workflow conditions, not a failure.

Remaining Success criterion:
- merge PR `#582` only after explicit human authorization;
- require post-merge master proof green;
- only then mark V1-00 closed and unlock V1-01.

Next exact: obtain explicit human authorization to merge PR `#582`; merge with an expected-head guard; verify exact post-merge master SHA and required master CI; if green, record V1-00 closeout here and unlock V1-01. No V1-01 work starts before that proof.

### LOT V1-01 — Agenda A4: physical resources and capacity

Status: **BLOCKED BY V1-00**

Working reference: PR `#575` is evidence/WIP only until revalidated against the then-current master.

Goal: complete Agenda physical-resource scheduling.

Success: resource persistence/API/runtime wiring complete; create/update/bulk/check-conflicts enforce deterministic practitioner/resource capacity rules; migrations have one coherent head; targeted/global regressions green; any UI change has mandatory BEFORE → Goal → implementation → AFTER at 390×844 / 768×1024 / 1280×900 → comparison/tests/visual score.

Proof: current-master reconciliation + PostgreSQL migration rehearsal from scratch + second upgrade no-op + tests/runtime + UI evidence when applicable + exact-head CI + closeout.

### LOT V1-02 — Agenda A5: temporal/history finalization

Status: **BLOCKED BY V1-01**

Goal: finish Agenda V1 hardening.

Scope: explicit cabinet timezone behavior, soft-delete/history policy, legacy treatment/migration strategy, transversal regressions and final Agenda certification.

Success/Proof: deterministic temporal/history behavior + no Agenda regression + required tests/runtime/CI + closeout.

### LOT V1-03 — Pharmacology Morocco evidence reconstruction

Status: **BLOCKED BY V1-02**

Working references: PR `#565` and divergent evidence PR `#572`; both are stale evidence branches, not merge-as-is product branches.

Goal: reconstruct only accepted Morocco pharmacology assets/tests on a clean then-current-master branch while preserving fail-closed clinical activation.

Rules:
- regulatory/catalogue presence != dental clinical suitability;
- no unsourced indication/dose/duration/pediatric/contraindication/interaction/renal-hepatic claim;
- malformed/duplicate/boundary mappings remain fail-closed;
- `clinical_activation=NO` remains default unless qualified independent clinical/scientific review explicitly clears activation.

Success: accepted evidence extracted from #565/#572; contradictions resolved/documented; negative tests green; automatic prescribing remains disabled unless the human scientific gate is satisfied; stale evidence PRs closed after extraction.

Proof: source evidence + validators + negative tests + qualified review if activation is requested + exact-head CI + closeout.

### LOT V1-04 — Céphalométrie scientific re-baseline

Status: **BLOCKED BY V1-03**

Goal: inspect current master after all preceding integrations and identify only genuine remaining V1-relevant scientific/runtime gaps; do not manufacture work or reopen already certified lots.

Success: canonical scientific inventory/provenance rebaselined; BLOCKED/TODO/legacy gaps classified; only evidence-backed V1 blockers corrected; no diagnostic/treatment inference introduced without required evidence/review.

Proof: code + scientific tests + provenance + runtime evidence + mandatory UI BEFORE/AFTER if visual changes + review + exact-head CI + closeout. If no genuine V1 blocker remains, record that finding and close the lot without invented implementation.

### LOT V1-05 — Orthalis current benchmark / gap decision

Status: **BLOCKED BY V1-04**

Goal: refresh the Orthalis comparison from current Digital Crown evidence and current official Orthalis claims, without inheriting historical scores from closed PR `#407`.

Success: current feature/evidence matrix; marketing claims labeled as such; Morocco/local-first/clinical workflow relevance explicit; only high-value verified V1 blockers, if any, converted into bounded corrections inside this lot.

Proof: current code/tests/runtime + current primary Orthalis sources + sourced matrix + tests/CI for any accepted correction + closeout.

### LOT V1-06 — Pre-freeze repository reconciliation

Status: **BLOCKED BY V1-05**

Goal: ensure no stale PR or undocumented branch can silently contaminate the V1 freeze.

Scope: fresh open-PR inventory; classify every remaining PR as required-for-V1, parked-post-V1, or superseded/closed. Security/physical PRs #288/#289/#383 remain outside the mandatory path unless a proven V1 blocker requires a bounded delta.

Success: every open PR classified against current master; no half-integrated mandatory feature; no competing roadmap PR remains open; no stale branch is blindly merged.

Proof: inventory + compare/tests where needed + canonical closeout.

### LOT V1-07 — Master stabilization

Status: **BLOCKED BY V1-06**

Goal: establish a stable pre-candidate master.

Success: required global CI/regressions green; migrations coherent; no known unresolved mandatory V1 blocker; canonical docs coherent; open PR inventory reconciled.

Proof: exact master SHA + required global run IDs + regression evidence + final pre-freeze audit.

### LOT V1-08 — Freeze exact V1 candidate

Status: **BLOCKED BY V1-07**

Goal: intentionally select one immutable exact 40-character SHA as V1 candidate.

Success: candidate SHA recorded here and in `DIGITALCROWN_V1_OBJECTIVE.md`; moving branch names are not install identity.

Rule: any code change after freeze creates a new candidate SHA and restarts candidate certification.

### LOT V1-09 — V0 → V1 installability certification

Status: **BLOCKED BY V1-08**

Goal: certify the locked candidate against a fresh isolated restore of the real cabinet PREUPDATE state.

Success:
- fresh PREUPDATE fingerprints;
- verified PostgreSQL + media/document backups;
- isolated restore;
- exact candidate migrations succeed;
- historical rows/PK/FK preserved, no new orphans;
- document archives resolve;
- media/file manifest preserved;
- second migration no-op;
- app startup + `/api/health` + critical cabinet smokes pass;
- rollback point verified;
- exact candidate reaches `INSTALLABLE_CERTIFIED`.

Proof: complete rehearsal/certification report tied to the exact candidate SHA.

### LOT V1-10 — Real cabinet update + V1 operational closure

Status: **BLOCKED BY V1-09 + EXPLICIT HUMAN AUTHORIZATION**

Goal: install the exact `INSTALLABLE_CERTIFIED` candidate on the real cabinet and prove operational integrity.

Success: explicit authorization immediately before mutation; writes frozen as required; backups revalidated; same locked SHA installed; post-update integrity/startup/critical smokes pass; rollback remains executable; `V1_OPERATIONAL` recorded here.

Proof: installed SHA + POSTUPDATE integrity + health/smoke evidence + rollback identity.

## 5. Unlock / closeout rule

Only one lot may be `IN_PROGRESS` at a time. Lot N+1 unlocks only when lot N has Goal met, observable Success met, Proof captured, impacted tests/CI green, canonical closeout written here, and merge/post-merge completed when applicable.

Pending CI does not unlock the next lot. Independent work is permitted only inside the same unlocked lot.

## 6. Current canonical state

- active lot: **V1-00 — MERGE_READY / NOT CLOSED**
- next lot: **V1-01 — BLOCKED**
- certified V1-00 product HEAD: `cc34fdf42874f06d4ac3ec45073e1cbb012c6007`
- merge authorization: **REQUIRED**
- post-merge master proof: **PENDING**
- V1 candidate SHA: **NOT SELECTED**
- V1 state: **EXECUTION LOCKED / NOT OPERATIONAL**
- production/cabinet mutation: **NOT AUTHORIZED**
- Vercel deployment: **NOT AUTHORIZED**

## 7. Maintenance rule

At every lot closeout update this file with exact result, exact evidence/run IDs, relevant PR/merge/master SHA, remaining blocker, newly unlocked lot, and V1 state. Never claim COMPLETE / VERIFIED / INSTALLABLE_CERTIFIED / V1_OPERATIONAL without the corresponding proof.
