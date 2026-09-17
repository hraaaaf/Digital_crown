# Digital Crown — V1 Consolidated Roadmap

Status: AUDIT CONSOLIDATED — V1 CANDIDATE NOT SELECTED  
Date: 2026-09-17  
Repository: `hraaaaf/Digital_crown`  
Initial audit baseline: `master@3beea0a4cee0eb227bd531d1aaf0ea29d13c4118`  
Live master after in-audit merge of #557: `7c175bdd37b2f53afb7b05fd8cf21aaf4bda2164`

## Goal

Reach one intentionally frozen Digital Crown V1 candidate SHA only after the active V1 workstreams are either closed with evidence or explicitly deferred, then prove that exact SHA installable from canonical cabinet V0 without data loss.

Canonical V0: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`.

V1 is not `latest master`. The final candidate remains `NOT SELECTED` until this roadmap reaches the freeze gate.

## Success

The consolidation phase is successful when:

1. every PR open at audit start is classified against live `master`;
2. stale/superseded branches are not merged merely because they remain open;
3. each surviving workstream has a dependency order and explicit closure gate;
4. pharmacology remains fail-closed until the independent qualified clinical/scientific review required by its own gate is completed;
5. Agenda A4/A5, the Ortho/Céphalo re-baseline, and the Orthalis benchmark are resolved before candidate freeze;
6. FAR is either integrated after its own gates or explicitly deferred before freeze;
7. already-merged Connect Hub is verified post-merge rather than kept as false remaining work;
8. only after the functional freeze is complete is one immutable V1 SHA selected and passed through the managed V0 -> V1 installation certification.

## Proof baseline

- `master` verified first at `3beea0a4...`, then re-verified at `7c175bdd...` after #557 merged during this audit;
- canonical V1 objective and V0 -> V1 handover read from current master;
- the 14 PRs open at audit start were inventoried and compared to master;
- exact-head CI/workflow state checked for the active near-master PRs;
- current Agenda and Céphalo canonical handovers read;
- current Orthalis public capability surface re-checked on official Orthalis pages on 2026-09-17;
- this roadmap is proposed through documentation-only PR #577.

## PR inventory — classification against current master

| PR | Workstream | Divergence at audit | Classification | V1 action |
|---|---|---:|---|---|
| #576 | FAR -> ordonnance bridge | +24 / -18 commits | ACTIVE STACKED on #559 | Do not merge independently. Reconcile #559 first; then retain only the fail-closed bridge delta and certify it. |
| #575 | Agenda A4 resources | +11 / -14 | ACTIVE / INCOMPLETE | Keep. Reconcile current master, update schema runtime head to `a4rs0000004`, rerun PostgreSQL gate, wire create/update/bulk/check-conflicts, then UI BEFORE/AFTER and closeout. |
| #572 | Pharmacology gap denominator | +127 / -482 | SUPERSEDED by later #565 lineage | Preserve useful evidence through the later branch; close separately after consolidation. |
| #565 | Pharmacology Core-5 / fail-closed | +127 / -482 | ACTIVE SCIENTIFIC CORPUS / STALE INTEGRATION BASE | Never brute-force merge. Preserve/review scientific assets, rebuild the accepted minimal delta from current master, keep `clinical_activation=NO` until qualified independent review. |
| #563 | Mobile numeric-sub license regression | +2 / -38 | FUNCTIONALLY SUPERSEDED | Master already contains the canonical 422/403 regression logic. Optionally port only the explicit T2 targeted-check idea; close old PR. |
| #559 | FAR derived-reference runtime/UI | +22 / -18 | ACTIVE | Reconcile current master. Backend contract is green; FAR visual capture is red. Diagnose capture, re-certify source/rendering/CNSS-CNOPS regressions, then closeout. |
| #557 | Connect Hub Lot E | +22 / -18 effective delta | MERGED DURING AUDIT | Merge `7c175bdd...` is now on master. Treat product work as acquired; only post-merge CI/PostgreSQL verification remains before closeout proof. |
| #505 | ACIGAM catalog supplement | +17 / -499 | OBSOLETE / SUPERSEDED | Do not merge. The medication-source direction was superseded by the later merged AMMPS-based catalog work. Close. |
| #407 | Digital Crown vs Orthalis roadmap | +3 / -1140 | HISTORICAL STRATEGY INPUT | Do not merge as canonical. Reuse its domain structure only; rebuild benchmark against current master and current official Orthalis claims. |
| #401 | P5 installment runtime invariants | +1 / -1163 | ALREADY ABSORBED | `backend/tests/test_installments_p5_runtime.py` is already on master. Close. |
| #383 | Portability P13 physical cabinet certification | +3 / -1469 | HISTORICAL HUMAN-GATE RUNBOOK | Do not certify old release as V1. Re-issue physical/installation certification against the final locked V1 SHA. |
| #289 | SEC-2 device binding | +69 / -2065 | STALE / DEPENDS ON #288 | Not part of the immediate first-installable-V1 critical path unless explicitly promoted into V1 scope. Rebuild from current master only after SEC-1 decision. |
| #288 | SEC-1 signed licenses / OWNER entitlement | +225 / -2031 | LARGE STALE SECURITY PROGRAM | Do not rebase/merge wholesale. Treat as separate security program; promote only with an explicit V1 scope decision and reconstruct in bounded current-master lots. |
| #279 | Mobile mDNS bootstrap | +1 / -2085 | SUPERSEDED IMPLEMENTATION | Current master has a newer `mobile_mdns.py` using the stable HTTPS origin/port 8005 and safer threaded lifecycle. Do not merge old branch; optionally add current-implementation tests if coverage is missing. |

## Verified active gaps

### 1. Pharmacology / Ordonnance

Current state: the scientific branch contains substantial Morocco-specific evidence and deterministic fail-closed tooling, but it is 482 commits behind the audit master lineage. Automatic clinical activation remains off. The Core-5 review packet explicitly requires an independent dentist/pharmacist/qualified clinical reviewer.

Closure contract:

- complete an independent documentary/source review of the branch assets;
- separate regulatory/commercial presence from clinical indication and exact product/form/strength suitability;
- resolve internal contradictions or malformed mappings;
- rebuild only accepted assets/tests on a clean branch from current master;
- keep every medicine fail-closed while any required domain is unresolved;
- submit the Core-5 packet to the qualified independent human reviewer;
- after that review, apply corrections and only then perform any technical activation review;
- deterministic negative tests + exact-head CI + integration review before merge.

Human gate: qualified independent clinical/scientific review if automatic prescription activation is required for V1.

### 2. Agenda

Current canonical state on master: A1/A2/A3 CLOSED; A4 and A5 open.

A4 current PR #575 has already created the minimal resource model, nullable appointment `resource_id`, tenant-scoped resource CRUD and capacity-1 conflict service. Its PostgreSQL certification fails before migration because `backend/core/schema_runtime.py` still declares `CURRENT_ALEMBIC_HEAD = "a3pa0000003"` while A4 adds `a4rs0000004`.

A4 closure order:

`reconcile master -> align runtime schema head -> PostgreSQL from-scratch/no-op proof -> wire create/update/bulk/check-conflicts -> targeted backend tests -> UI BEFORE -> implementation -> AFTER same 390/768/1280 viewports -> visual comparison -> exact-head CI -> closeout -> merge`

Then A5:

`explicit cabinet timezone -> soft-delete/history policy -> legacy treatment/migration strategy -> transversal regressions -> final Agenda documentation/certification`.

### 3. Ortho / Céphalo

R20 itself is CLOSED and must not be reopened without new evidence. The next lot is intentionally undefined by the canonical handover.

Before declaring additional Céphalo work mandatory for V1:

`live master re-baseline -> read canonical scientific inventory -> search remaining BLOCKED/TODO/legacy/scientific gaps -> select only the highest-priority genuine open gap -> Goal/Success/Proof -> execute if no human scientific gate`.

If that re-baseline finds no critical unresolved V1 blocker, the correct action is to record Céphalo as non-blocking for the V1 freeze rather than create work artificially.

### 4. Orthalis comparative

PR #407 is not a valid current scorecard: its internal baseline predates more than one thousand master commits.

The domain model remains useful, but all scores must be recalculated from current evidence. Official Orthalis pages checked on 2026-09-17 still advertise, among other capabilities, multi-practitioner planning, a digital media library/Kitview, Ceph with more than 25 methods and automatic tracings, patient-facing/options, external gateways, and Orthalis Connect cloud access.

Re-benchmark contract:

- current Digital Crown inventory from code/tests/runtime only;
- current Orthalis claims from official sources, with marketing claims labelled as claims rather than independent validation;
- comparable domain-by-domain evidence matrix;
- no inherited 70.0/90.5 score without recalculation;
- produce gaps relevant to Morocco/local-first/clinical workflow rather than cloning France-specific features;
- convert only verified high-value gaps into V1 blockers; push the rest to post-V1.

Official sources re-checked:
- `https://www.orthalis.com/orthalis/`
- `https://www.orthalis.com/ceph/`
- `https://www.orthalis.com/kitview/`
- `https://www.orthalis.com/les-passerelles/`
- `https://www.orthalis.com/orthalis-connect-2/`

### 5. FAR

FAR is active near-master work but is not intrinsically required by the canonical installability definition of V1.

Rule before freeze: FAR must be either (A) reconciled, fully certified and merged, or (B) explicitly deferred with no dependency left in the chosen V1 candidate. A half-integrated branch is not acceptable.

Dependency: FAR base #559 before stacked ordonnance bridge #576.

### 6. Connect Hub

#557 merged during this audit as `master@7c175bdd...`.

Pre-merge exact-head proof already included green dedicated Connect Hub BEFORE/AFTER/backend, CI and T2. One legacy Patient UX1-C workflow had failed while starting the isolated backend on the pre-#573 base; the later master contains the #573 boot fix. Post-merge master CI and Cabinet Upgrade PostgreSQL must be read once when complete; they were still `in_progress` at the roadmap re-baseline and therefore are not claimed green here.

## Consolidated execution order

### Phase 0 — Repository hygiene / re-baseline

Goal: remove false work from the V1 plan.

Actions: mark #401/#505/#279/#563/#572 as close/supersede candidates; preserve only explicitly identified reusable tests/docs; never merge stale historical branches to clear the queue. Verify Connect Hub post-merge runs without waiting passively.

### Phase 1 — Finish autonomous high-value active work

1. Agenda A4 (#575) through PostgreSQL + functional wiring + UI proof.
2. Agenda A5 final robustness/closeout.
3. Reconcile FAR #559, then #576 if FAR remains in V1 scope.

Reason: these can progress without waiting for the pharmacology human gate.

### Phase 2 — Pharmacology / Ordonnance scientific closeout

Run the independent documentary review and clean-current-master reconstruction in parallel with Phase 1 where possible. Prepare the qualified reviewer packet completely. When the human review arrives, apply corrections, technical activation review if authorized, exact-head CI and closeout.

Do not use waiting for the human review as a reason to stop other work.

### Phase 3 — Ortho/Céphalo re-baseline

Re-baseline current master and select at most the genuine next critical scientific lot. Execute only if evidence shows a V1-relevant gap; otherwise record the domain as non-blocking.

### Phase 4 — Orthalis benchmark refresh

Rebuild the competitive matrix against the now-near-final Digital Crown state. Convert only evidence-backed critical gaps into bounded final V1 lots. No stale score carry-over.

### Phase 5 — Functional freeze

Requirements:
- all selected V1 workstreams closed and on master;
- all intentionally deferred work documented as non-dependent on V1 candidate;
- no open migration-head inconsistency;
- no unresolved red exact-head workflow relevant to included scope;
- no unreviewed clinical activation;
- FAR either closed or explicitly deferred;
- current master cleanly represents the intended feature freeze.

Output: choose one exact candidate SHA. Do not move it afterward.

### Phase 6 — V0 -> V1 installability certification

Execute the canonical managed-update contract:

`candidate SHA lock -> candidate CI -> fresh real-cabinet PREUPDATE -> verified PostgreSQL + media/document backups -> isolated restore -> exact migrations -> row/PK/FK/orphan/document/media integrity comparison -> second Alembic upgrade no-op -> app startup -> /api/health + critical smoke -> INSTALLABLE_CERTIFIED -> real cabinet update from same SHA -> post-update integrity/startup/smoke -> V1 baseline closeout`.

No code-certified SHA becomes V1 merely because CI is green.

## Critical path

Current critical path is:

`Agenda A4/A5 + pharmacology review/reconstruction -> Céphalo re-baseline -> refreshed Orthalis gap check -> functional freeze -> exact V1 SHA -> installation rehearsal/certification -> real cabinet update`.

FAR runs alongside this path and must be resolved (merge or explicit defer) before freeze. Connect Hub is now acquired on master, pending only post-merge verification evidence.

SEC-1/SEC-2 and the historical P13 release are not merged into the first V1 critical path by default because their current branches are massively stale and the canonical V1 installability objective does not require those specific feature sets. If they are later declared mandatory for V1, they require clean current-master reconstruction rather than branch resurrection.

## Freeze gates

V1 candidate selection is blocked if any of these are true:

- selected functional lot still open;
- schema runtime head differs from the unique Alembic head;
- required CI/certification red or absent on included changes;
- pharmacology has automatic clinical activation without the required independent qualified review;
- FAR code is half-integrated rather than merged or explicitly deferred;
- Orthalis benchmark still relies on the stale #407 score without current recalculation;
- candidate SHA is moving;
- fresh cabinet PREUPDATE/backups/rehearsal proof has not been completed for installation certification.

## Next exact

Start with Agenda A4 because it is a near-master active implementation with a precisely identified technical blocker and no human gate. In parallel, continue the pharmacology documentary review/reconstruction up to the qualified-review gate. After A4/A5, resolve FAR, re-baseline Céphalo, refresh the Orthalis benchmark, then freeze the V1 candidate.

No Vercel deployment is part of this roadmap without explicit user authorization.
