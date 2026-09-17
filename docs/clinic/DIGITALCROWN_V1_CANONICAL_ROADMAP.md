# Digital Crown — V1 Canonical Roadmap

Status: **CANONICAL / EXECUTION LOCKED**

Effective date: 17 September 2026

## Authority

This file is the **sole execution roadmap for Digital Crown until V1 is operational**.

Until `V1_OPERATIONAL` is explicitly recorded in this file:

- no new chantier, lot, feature, refactor, cleanup, research implementation, merge, release or deployment may be started outside the currently unlocked V1 lot;
- work is authorized only when it is explicitly part of the current lot, or is a correction/test/documentation change strictly required to make that lot pass its gates;
- existing open PRs that belong to later lots remain parked and must not be merged out of order;
- another file named `ROADMAP`, `PLAN`, `HANDOVER`, `BACKLOG`, `OBJECTIVE` or similar may provide evidence or local context, but **cannot authorize scope or alter this sequence**;
- the next lot remains blocked until the current lot has a documented closeout with its required proofs;
- no production/cabinet mutation is authorized before LOT V1-12 and explicit human authorization;
- no Vercel deployment is authorized by this roadmap.

Any requested work outside this roadmap must be refused or redirected to the currently unlocked lot until V1 is operational.

## Global Goal

Produce the first operational V1 cabinet release from canonical V0 while preserving cabinet data, historical integrity and rollback capability.

Canonical V0 SHA: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`

V1 candidate SHA: **NOT SELECTED**

V1 release rule: **do not select a candidate SHA before LOT V1-10**.

## Definition of `V1_OPERATIONAL`

`V1_OPERATIONAL` may be recorded only after all LOT V1-00 through V1-12 are closed and the same locked candidate has:

1. passed its required CI/certification gates;
2. passed fresh V0 → V1 rehearsal on an isolated restore of real cabinet PREUPDATE data;
3. reached `INSTALLABLE_CERTIFIED`;
4. been installed on the real cabinet only after explicit human authorization;
5. passed post-update integrity, startup and critical smoke checks;
6. retained a verified rollback point.

Until then, V1 is not operational.

## Mandatory lot sequence

### LOT V1-00 — CI / Windows / dependency contract

Status: **IN_PROGRESS — ONLY UNLOCKED LOT**

Current working reference:

- PR: `#580` — draft
- branch: `fix/windows-build-contract-post579`
- last known branch HEAD: `f84550c68368b9be3116b31a8b840a15ab9c4b48`
- exact-head CI after the latest corrections: **NOT YET VERIFIED GREEN**

Goal: restore a coherent, reproducible CI/runtime/build dependency contract, including clean Windows Python 3.12 validation.

Success:

- dependency source/alias contract is coherent;
- Linux CI consumers resolve the canonical dependency set without path breakage;
- Windows clean install resolves without broken requirements;
- runtime version proofs pass;
- cabinet import smoke passes only with explicit isolated-test attestation;
- all required exact-head checks for this lot are green.

Proof:

- exact PR HEAD;
- green workflow run IDs;
- resolver integrity (`pip check`);
- runtime/import smoke evidence;
- closeout recorded in this file before unlocking LOT V1-01.

Next exact: verify the CI on the latest #580 HEAD, correct any remaining failure, rerun impacted gates, then close out LOT V1-00.

### LOT V1-01 — Agenda A4: resources and physical capacity

Status: **BLOCKED BY V1-00**

Goal: complete Agenda physical-resource scheduling without breaking existing appointment behavior.

Scope: chairs/rooms/resources, capacity, optional allocation, practitioner/resource collision rules.

Success: backend + frontend behavior defined, targeted regressions green, no silent overbooking, required UI evidence captured if visual changes occur.

Proof: code/tests + runtime behavior + CI + canonical closeout.

### LOT V1-02 — Agenda A5: temporal/history finalization

Status: **BLOCKED BY V1-01**

Goal: finish Agenda V1 hardening.

Scope: timezone behavior, soft-delete/history, legacy/global regressions, final Agenda certification.

Success: deterministic temporal behavior and historical consistency with no Agenda regression.

Proof: targeted + global regression evidence, CI and closeout.

### LOT V1-03 — FAR / Mutuelles completion

Status: **BLOCKED BY V1-02**

Working reference: PR `#559` remains parked until this lot.

Goal: finish FAR support inside the existing Mutuelles/Honoraires engine without false provenance claims or prescription inference.

Success: exact cabinet reference path, FAR overlay inspection, FAR visual workflow, CNSS/CNOPS regressions, prescription boundary preserved, exact-head CI green.

Proof: source SHA/provenance + rendered PDF evidence + tests + CI + closeout.

### LOT V1-04 — Pharmacology Morocco evidence closure

Status: **BLOCKED BY V1-03**

Working references: PRs `#505` and `#565` remain parked until this lot.

Goal: reconcile Morocco medication-reference work under fail-closed scientific/documentary rules.

Success: no unsourced clinical activation; provenance explicit; disputed/duplicate/boundary rows never auto-merged; any ACIGAM 100 mg addition requires valid current documentary evidence.

Proof: source evidence + validators + negative mutation tests + CI + scientific/documentary review where required.

### LOT V1-05 — Cephalometry / Orthalis gap closure

Status: **BLOCKED BY V1-04**

Working references: useful remaining deltas from PRs `#403`, `#404` and `#407` may be reconciled only after live-master rebaseline.

Goal: close only the highest-priority remaining scientific/UX gaps without reopening already certified cephalometry lots.

Success: live master rebaselined; scientific state/provenance remains explicit; no diagnostic or treatment inference is introduced without the required evidence/review.

Proof: rebaseline + scientific tests + required visual BEFORE/AFTER + review + CI + closeout.

### LOT V1-06 — Connect Hub

Status: **BLOCKED BY V1-05**

Working reference: PR `#557` remains parked until this lot.

Goal: provide one unified communication surface over existing notification infrastructure, with no second transport/persistence engine.

Success: canonical sources reused, tenant/RBAC enforced at source boundary, simulated channels never mislabeled delivered, unified UI certified responsively.

Proof: backend/runtime/RBAC tests + BEFORE/AFTER evidence + exact-head CI + closeout.

### LOT V1-07 — Mobile / security / physical gates

Status: **BLOCKED BY V1-06**

Working references: PRs `#279`, `#288`, `#289`, `#383` are reconciled here according to current master state.

Goal: finish software-certifiable mobile/security work and explicitly isolate genuine physical human gates.

Success: no blind merge of stale branches; signed-license/device-binding/mDNS deltas reconciled where still applicable; physical Windows/macOS/biometric/push requirements remain explicit when not software-provable.

Proof: security tests + current-master reconciliation + CI + physical-gate evidence where available.

### LOT V1-08 — Technical debt / remaining PR reconciliation

Status: **BLOCKED BY V1-07**

Working reference: PR `#401` and any other still-open useful delta are handled here only after fresh inventory.

Goal: remove stale PR ambiguity and retain only useful, current, tested deltas needed before V1 stabilization.

Success: every open PR classified against current master; useful deltas integrated or explicitly parked; superseded work closed; no unreviewed historical code merged blindly.

Proof: current open-PR inventory + comparisons/tests + closeout.

### LOT V1-09 — Master stabilization

Status: **BLOCKED BY V1-08**

Goal: establish a stable pre-candidate master after all required V1 workstreams are integrated.

Success: required global CI/regressions green, no known unresolved V1 blocker, canonical docs coherent, open PR inventory reconciled.

Proof: exact master SHA + global CI run IDs + regression evidence + final pre-freeze audit.

### LOT V1-10 — Freeze exact V1 candidate

Status: **BLOCKED BY V1-09**

Goal: intentionally select one immutable exact SHA as the V1 candidate.

Success: candidate SHA recorded in this file and `DIGITALCROWN_V1_OBJECTIVE.md`; no moving branch name used as install identity.

Proof: exact 40-character SHA + candidate-state record.

Rule: any code change after freeze creates a new candidate SHA and restarts candidate certification.

### LOT V1-11 — V0 → V1 installable certification

Status: **BLOCKED BY V1-10**

Goal: certify the locked V1 candidate against a fresh copy of the real V0 cabinet state.

Success:

- fresh PREUPDATE fingerprints;
- verified PostgreSQL + media/document backup;
- isolated restore;
- exact candidate migration succeeds;
- historical rows/PK/FK preserved and no new orphans;
- document archives resolve;
- media/file manifest preserved;
- second migration is a no-op;
- application starts;
- `/api/health` + critical cabinet smoke tests pass;
- candidate reaches `INSTALLABLE_CERTIFIED`;
- rollback point is verified.

Proof: complete rehearsal/certification report tied to the exact candidate SHA.

### LOT V1-12 — Real cabinet update + operational closure

Status: **BLOCKED BY V1-11 + HUMAN AUTHORIZATION**

Goal: update the real cabinet from canonical V0 to the exact `INSTALLABLE_CERTIFIED` V1 candidate and prove operational integrity.

Success:

- explicit human authorization obtained immediately before real mutation;
- writes frozen as required;
- backups revalidated;
- same locked candidate installed;
- post-update integrity/startup/critical smoke tests pass;
- rollback remains executable;
- this file records `V1_OPERATIONAL` with installed SHA and proof references.

Proof: real cabinet post-update report + installed SHA + health/smoke/integrity evidence + rollback identity.

## Unlock rule

Only one lot may be `IN_PROGRESS` at a time.

To unlock lot `N+1`, lot `N` must have:

1. Goal met;
2. observable Success criteria met;
3. required Proof captured;
4. impacted CI/tests green;
5. canonical closeout written here;
6. merge/post-merge steps completed when applicable.

A CI that is pending does not authorize starting the next lot; independent work is allowed only if it belongs to the same unlocked lot.

## Existing PR rule

Open PRs associated with later lots are **parked, not authorized**. Their existence does not unlock their scope and does not authorize merge. When their lot arrives, each PR must be revalidated against the then-current master before use.

## Current canonical state

- active lot: **V1-00**
- V1 candidate SHA: **NOT SELECTED**
- V1 state: **EXECUTION LOCKED / NOT OPERATIONAL**
- next lot: **V1-01, blocked until V1-00 closeout**
- production/cabinet mutation: **NOT AUTHORIZED**

## Canonical maintenance rule

At every lot closeout, update this file with:

- exact result;
- exact evidence/run IDs;
- relevant PR/merge/master SHA;
- remaining blocker, if any;
- newly unlocked lot;
- V1 state.

Do not mark a lot complete, V1 certified, installable or operational without the corresponding proof.
