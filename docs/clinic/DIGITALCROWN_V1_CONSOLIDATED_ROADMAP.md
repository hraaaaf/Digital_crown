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

Status: **CLOSED — POST-MERGE MASTER CERTIFIED**

Goal: establish one coherent, reproducible runtime/build dependency contract on the actual current master, including clean Windows Python 3.12 validation and stable Linux CI consumers.

Certified foundation product HEAD: `cc34fdf42874f06d4ac3ec45073e1cbb012c6007`.

Foundation evidence:
- Windows Build Dependency Contract `35261174495` — **SUCCESS** on Windows Server 2025 / CPython 3.12.10; exact 140-package runtime lock; `pip check` green; cabinet import smoke green;
- CI `35261174409` — **SUCCESS**;
- P5 Native `35261174502`, Media C4 `35261174469`, Patient UX1-C `35261174611`, Patient P7 `35261174478`, T2 `35261174525`, Catalog `35261174529`, Marketplace `35261174526` — **SUCCESS**;
- foundation docs commit `41978064008deab3f7e91866d2a858ec21100e7e`;
- PR `#582` merged as `15b5c2084b890c8375558c80b6bd7a44f577c016`.

Post-merge repair evidence:
- first master CI `35267802853` exposed Linux dependency/Connect Hub contract drift; PostgreSQL certification `35267803004` remained **SUCCESS**;
- PR `#583` repaired Linux torch/httpx/Connect Hub/T2 contracts; exact repair HEAD `7b3d89248405296b8503d5eb16d4e54059057dee`;
- exact-head CI `35282100416`, T2 `35282100475`, Connect Hub E `35282100413`, PR Merge Summary `35282100436` — **SUCCESS**;
- PR `#583` merged as `bc7e1e1f1762431a048661ad9495a3430774f6e0`;
- subsequent master CI `35282593094` exposed one stale insurance-validator assertion while PostgreSQL certification `35282593275` remained **SUCCESS**;
- PR `#585` aligned that assertion and repaired file-backed SQLite/SQLCipher pooling after T2 `35283365207` exposed `SingletonThreadPool` detached-connection failures;
- final PR `#585` HEAD `244b452bde8eacdd873b87ef80f31a38b297af8a`: CI `35283989343`, T2 `35283989391`, FAR `35283989308`, CNOPS `35283989425`, PR Merge Summary `35283989374`, UI Human Visual Approval `35283987548` — **SUCCESS**; M6-I `35283989353` skipped by workflow conditions;
- PR `#585` merged as master `9b448dea18b1943f8b15beebf7cada1a75e96af9`.

Remaining Success criterion:
- Cabinet Upgrade PostgreSQL Certification `35284854114` — **SUCCESS** on current master `9b448dea18b1943f8b15beebf7cada1a75e96af9`;
- master CI `35284853774` — **FAILURE** after `2055 passed, 5 skipped`; the only failure was `test_zeroconf_runtime_dependency_is_declared`, whose static assertion still required the obsolete range `zeroconf>=0.131.0,<1.0` while the canonical mirrored runtime lock pins `zeroconf==0.150.0`;
- repair PR `#587`, HEAD `330994e4454a30074e8ee4e1c7e301f071cb060b`, changes only that stale test assertion; exact-head CI `35286042393`, T2 `35286042275`, PR Merge Summary `35286042260`, UI Human Visual Approval `35286041958` — **SUCCESS**; M6-I `35286042180` skipped by workflow conditions.

Remaining Success criterion:
- PR `#587` merged under expected-head guard as master `1edd440bf69ca4a79c5e265b20957148297adb3f`;
- final master CI `35286577382` — **SUCCESS**;
- final Cabinet Upgrade PostgreSQL Certification `35286577467` — **SUCCESS**.

V1-00 Success criterion is satisfied on exact master `1edd440bf69ca4a79c5e265b20957148297adb3f`. V1-01 is unlocked after this canonical closeout is merged.

Next exact: merge this canonical closeout PR after its exact-head checks/coherence are green, then start V1-01 against the resulting current master.

### LOT V1-01 — Agenda A4: physical resources and capacity

Status: **IMPLEMENTED — EXACT-HEAD CERTIFIED; MERGE GATE PENDING**

Working reference: stale PR `#575` was revalidated against certified master and used only as extraction evidence; V1-01 was rebuilt on clean branch `feat/v1-01-agenda-a4-rebuild`, PR `#588`.

Implementation candidate: `0354bdcba7d7c7390e96a94ec5e3f0e778cf28d0`.

Verified scope: tenant-scoped physical resources; canonical nullable `Appointment.resource_id` with `ON DELETE SET NULL`; resource CRUD; deterministic capacity-1 resource conflicts wired through create/update/bulk/check-conflicts; Alembic head advanced from A3 to `a4rs0000004`; A3 certification now verifies ancestry instead of incorrectly requiring A3 to remain the terminal head. No product frontend/UI files were changed.

Exact-head proof:
- CI `35316680604` — SUCCESS.
- PostgreSQL Alembic Schema Certification `35316680541` — SUCCESS.
- Agenda A3 Certification `35316680555` — SUCCESS.
- T2 Runtime Browser Certification `35316680538` — SUCCESS.
- Portability Runtime Certification `35316680511` — SUCCESS.
- Settings TemplateEngine Reachability `35316680524` — SUCCESS.
- Settings R11 TemplateBuilder Dependency `35316680605` — SUCCESS.
- Settings R11 TemplateBuilder Reachability `35316680465` — SUCCESS.
- UI Human Visual Approval `35316678700` — SUCCESS; no V1-01 product UI delta.
- M6-I `35316680502` — SKIPPED by workflow conditions.

Next exact: human merge authorization for PR `#588`; after merge, certify exact master CI/PostgreSQL before unlocking V1-02.

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

- active lot: **V1-00 — CLOSED / CANONICAL CLOSEOUT PR PENDING MERGE**
- next lot: **V1-01 — UNLOCKED AFTER CANONICAL CLOSEOUT MERGE**
- current master: `1edd440bf69ca4a79c5e265b20957148297adb3f`
- certified V1-00 foundation product HEAD: `cc34fdf42874f06d4ac3ec45073e1cbb012c6007`
- final repair PR: `#587` / `330994e4454a30074e8ee4e1c7e301f071cb060b` — **MERGED** as `1edd440bf69ca4a79c5e265b20957148297adb3f`
- merge authorization: **SATISFIED for PR #582, #583, #585 and #587**
- final post-merge master proof: **CI 35286577382 SUCCESS / PostgreSQL 35286577467 SUCCESS**
- V1 candidate SHA: **NOT SELECTED**
- V1 state: **EXECUTION LOCKED / NOT OPERATIONAL**
- production/cabinet mutation: **NOT AUTHORIZED**
- Vercel deployment: **NOT AUTHORIZED**

## 7. Maintenance rule

At every lot closeout update this file with exact result, exact evidence/run IDs, relevant PR/merge/master SHA, remaining blocker, newly unlocked lot, and V1 state. Never claim COMPLETE / VERIFIED / INSTALLABLE_CERTIFIED / V1_OPERATIONAL without the corresponding proof.
