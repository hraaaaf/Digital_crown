# Digital Crown — V1 Consolidated Roadmap

Status: AUDIT CONSOLIDATED — V1 CANDIDATE NOT SELECTED  
Date: 2026-09-17  
Repository: `hraaaaf/Digital_crown`  
Canonical roadmap: this file is the single V1 execution ledger. No competing V1 roadmap is authoritative.  
Initial audit baseline: `master@3beea0a4cee0eb227bd531d1aaf0ea29d13c4118`  
Live master: `7c175bdd37b2f53afb7b05fd8cf21aaf4bda2164` (`#557` Connect Hub merged)

## Goal

Reach one intentionally frozen Digital Crown V1 candidate SHA only after the selected V1 workstreams are either closed with evidence or explicitly deferred, then prove that exact SHA installable from canonical cabinet V0 without data loss.

Canonical V0: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`.

V1 is not `latest master`. The final candidate remains `NOT SELECTED` until the functional freeze gate is closed.

## Success

The consolidation/execution phase is successful only when:

1. every surviving open PR is classified against live `master`;
2. stale/superseded branches are closed or reduced to explicitly reusable evidence, never merged merely to clear the queue;
3. each surviving workstream has a dependency order and explicit closure gate;
4. master regressions are repaired before they are treated as baseline;
5. pharmacology remains fail-closed until the qualified independent clinical/scientific gate required by its own contract is completed, unless V1 intentionally keeps automatic clinical activation disabled;
6. Agenda A4/A5, Ortho/Céphalo re-baseline, Windows build/installability prerequisites and the refreshed Orthalis comparison are resolved before candidate freeze;
7. FAR is either fully integrated after its gates or explicitly deferred before freeze;
8. only after the functional freeze is complete is one immutable V1 SHA selected and passed through the managed V0 -> V1 installation certification.

## Proof baseline

- `master` verified at `7c175bdd37b2f53afb7b05fd8cf21aaf4bda2164` after merge of #557;
- canonical V1 objective and V0 -> V1 handover were used as constraints;
- the 14 PRs open at the initial audit were classified;
- live refresh after cleanup shows exactly 10 open PRs: `#288 #289 #383 #559 #565 #572 #575 #577 #578 #579`;
- stale/superseded PRs `#279 #401 #407 #505 #563` were closed on 2026-09-17 without merge after repository proof;
- `#576` is closed/merged into the #559 branch, not into master; merge commit `28e9a13f19c299cb3bbae8a8ffb7b5b542b1a85f`;
- post-#557 master Cabinet Upgrade PostgreSQL run `35245309371` is `SUCCESS`;
- post-#557 master CI run `35245309329` is `FAILURE` with exactly one backend failure after `3746 passed, 10 skipped`: `test_pytorch_landmarks_do_not_gain_synthetic_incisor_apices`;
- targeted regression PR #579 exact head `b00f44acffff3687b6034686254bf7def6be3922` has CI `35248190003` SUCCESS, P5 Native `35248189724` SUCCESS and T2 Runtime `35248189918` SUCCESS;
- Windows build contract #578 exact head `da74620da0c89de26fc7d59c82725e55f4d5969e` remains red: Windows Build Dependency Contract `35248048864` fails during dependency installation because the branch pins `cryptography==47.0.0` while `webauthn==3.0.0` requires `cryptography>=49.0.0`;
- no V1 candidate SHA has been selected.

## Checklist protocol — mandatory

This file is the live V1 execution ledger.

- `[ ]` = not yet proven complete.
- `[x]` = complete only after observable proof has been obtained.
- A step MUST NOT be checked merely because code was written, a PR exists, or a workflow started.
- Proof may be an exact commit SHA, merged PR, successful exact-head CI/certification run, deterministic test result, UI BEFORE/AFTER evidence, qualified human review where required, or installation/data-integrity evidence.
- After every completed step, update this same roadmap in the workstream closeout and add the proof reference.
- If later evidence invalidates a checked item, revert it to `[ ]` and record why.
- V1 candidate selection is forbidden while a mandatory item below remains unchecked.

## Master execution checklist

### Phase 0 — Consolidation / repository hygiene / master health

- [x] Audit and classify the 14 PRs open at audit start against live master. Proof: PR #577 consolidation audit.
- [x] Record Connect Hub #557 as merged/acquired rather than remaining product work. Proof: master `7c175bdd37b2f53afb7b05fd8cf21aaf4bda2164`.
- [x] Verify post-#557 Cabinet Upgrade PostgreSQL. Proof: run `35245309371` SUCCESS.
- [x] Diagnose post-#557 master CI rather than claiming it green. Proof: run `35245309329` FAILURE; only failing test is `backend/tests/test_vision_apex_provenance.py::test_pytorch_landmarks_do_not_gain_synthetic_incisor_apices`; `3746 passed, 10 skipped`.
- [x] Close obsolete/superseded #279, #401, #407, #505 and #563 without merge after preserving repository evidence.
- [ ] Integrate the targeted master regression fix #579 after explicit merge authorization. Exact-head proof already green: CI `35248190003`, P5 `35248189724`, T2 `35248189918`.
- [ ] After #579 integration, prove the resulting master CI green; do not treat #579 PR-head green as post-merge proof.
- [ ] Extract the unique deterministic denominator/Core-8 evidence from #572 into the accepted pharmacology reconstruction, then close #572. Do not close it as merely superseded: #572 and #565 diverged from common ancestor `34ee8c627bc9ec5e2af5628a80405bd0f9790854` and #572 still contains unique tests/data.

### Phase 1A — Agenda A4 #575

- [ ] Re-baseline/reconcile A4 against current master after the master regression baseline is healthy, without resurrecting stale deltas.
- [ ] Align runtime schema head with unique Alembic head `a4rs0000004`.
- [ ] Prove PostgreSQL from-scratch migration.
- [ ] Prove second Alembic upgrade is a no-op.
- [ ] Wire appointment create/update/bulk/check-conflicts to the A4 resource model.
- [ ] Pass targeted backend/resource/conflict tests.
- [ ] Capture UI BEFORE at 390/768/1280.
- [ ] Implement required Agenda A4 UI only after BEFORE is locked.
- [ ] Capture AFTER at the same 390/768/1280 viewports.
- [ ] Compare BEFORE/AFTER and record visual score + regressions.
- [ ] Pass exact-head CI/certification relevant to A4.
- [ ] Write A4 closeout/canonical evidence.
- [ ] Merge A4 to master and verify post-merge state.

### Phase 1B — Agenda A5

- [ ] Make cabinet timezone explicit and tested.
- [ ] Close soft-delete/history policy.
- [ ] Close legacy treatment/migration strategy.
- [ ] Pass transversal Agenda regressions.
- [ ] Complete final Agenda documentation/certification.
- [ ] Merge A5 to master and verify post-merge state.

### Phase 1C — FAR / mutuelles

- [x] Preserve the fail-closed FAR -> ordonnance bridge inside the FAR branch. Proof: #576 closed/merged into #559 branch at `28e9a13f19c299cb3bbae8a8ffb7b5b542b1a85f`.
- [ ] Reconcile #559, including the already-merged #576 bridge, against current master. No separate #576 merge remains.
- [ ] Diagnose and fix FAR visual capture failure.
- [ ] Re-certify FAR source/rendering and CNSS/CNOPS regressions.
- [ ] Capture required UI BEFORE/AFTER evidence for any visual change.
- [ ] Re-prove the FAR -> ordonnance bridge copies only explicit archived ordonnance data and remains fail-closed with no medication inference.
- [ ] Pass exact-head FAR tests/CI on the reconciled candidate.
- [ ] Merge #559 as one coherent FAR stack or explicitly defer FAR before V1 freeze.

### Phase 2 — Pharmacology / Ordonnance

- [ ] Complete documentary/source review of #565 scientific assets plus the unique #572 evidence.
- [ ] Separate Morocco regulatory/commercial presence from clinical indication and exact product/form/strength suitability.
- [ ] Resolve internal contradictions and malformed mappings.
- [ ] Preserve the deterministic 68-row fail-closed denominator and accepted Core-8 triage evidence from #572 where it survives review.
- [ ] Rebuild only accepted assets/tests on a clean current-master branch; never brute-force merge the stale #565/#572 histories.
- [ ] Prove fail-closed behavior for unresolved medication domains.
- [x] Core-5 qualified-review packet prepared on #565; automatic activation remains `0/5` and `clinical_activation=NO`.
- [ ] Obtain qualified independent human clinical/scientific review if automatic prescription activation is required for V1.
- [ ] Apply reviewer corrections and document dispositions.
- [ ] Pass deterministic negative tests + exact-head CI + integration review.
- [ ] Merge the accepted pharmacology/ordonnance V1 delta or explicitly keep automatic clinical activation disabled for V1.
- [ ] Close #565 and #572 only after accepted evidence is safely reconstructed or explicitly archived as non-product evidence.

### Phase 3 — Ortho / Céphalo

R20 remains CLOSED. #579 is a runtime regression repair, not a reopening of R20 or a new scientific lot.

- [x] Identify the current master Céphalo runtime regression. Proof: master CI `35245309329`, single failing apex-provenance test after 3746 passes.
- [x] Produce and exact-head certify targeted fix #579. Proof: head `b00f44acffff3687b6034686254bf7def6be3922`; CI/P5/T2 all SUCCESS.
- [ ] Merge #579 after explicit authorization and prove subsequent master CI green.
- [ ] Re-baseline healthy live master against the canonical Céphalo scientific inventory.
- [ ] Search remaining BLOCKED/TODO/legacy/scientific gaps.
- [ ] Select only the highest-priority genuine V1-relevant open scientific gap, if one exists.
- [ ] Define Goal / Success / Proof for that lot.
- [ ] Execute and certify the lot, or document Céphalo as non-blocking if no genuine V1 blocker exists.

### Phase 4 — Orthalis benchmark refresh

Historical PR #407 was closed without merge and is not a competing roadmap. Its domain structure may be reused as historical input only; its old scores are not current evidence.

- [ ] Inventory current Digital Crown capabilities from code/tests/runtime only.
- [ ] Re-check current Orthalis official capability claims and label marketing claims as claims.
- [ ] Build a domain-by-domain evidence matrix.
- [ ] Recalculate from current evidence; do not reuse historical #407 scores.
- [ ] Identify only Morocco/local-first/clinical-workflow-relevant gaps.
- [ ] Convert only verified high-value gaps into bounded V1 lots; defer the rest.
- [ ] Close every resulting V1-critical Orthalis gap or document it as non-blocking/deferred before freeze.

### Phase 4B — Windows cabinet dependency/build contract #578

This is a V1 installability prerequisite for the Windows cabinet target, not proof of a V1 candidate by itself.

- [x] Establish a static Windows dependency/build contract harness on #578. Proof: static contract step reports `WINDOWS_BUILD_DEPENDENCY_CONTRACT=SUCCESS` on run `35248048864` before install.
- [ ] Replay/rebuild #578 on the then-current master after #579 integration; current branch is stale and must not merge as-is.
- [ ] Resolve the real dependency conflict: current #578 pins `cryptography==47.0.0` while `webauthn==3.0.0` requires `cryptography>=49.0.0`; choose and lock an actually resolvable compatible set rather than loosening blindly.
- [ ] Pass clean Windows Python 3.12 dependency installation and `pip check` on exact head.
- [ ] Pass cabinet import smoke and Windows build guard.
- [ ] Pass exact-head Windows Build Dependency Contract; current run `35248048864` is FAILURE and therefore not proof.
- [ ] Re-run relevant CI/P5/T2/package workflows on the reconciled exact head and close unrelated failures introduced by stale branch drift.
- [ ] Merge only the accepted current-master Windows dependency/build contract before V1 candidate freeze.

### Phase 5 — Functional freeze

- [ ] Master CI is green after all included regression fixes.
- [ ] All selected V1 workstreams are closed and on master.
- [ ] All intentionally deferred work is documented and non-dependent on the candidate.
- [ ] Unique Alembic head equals runtime schema head.
- [ ] No relevant red/absent exact-head workflow remains for included scope.
- [ ] Windows cabinet dependency/build contract is resolvable and certified on the included code line.
- [ ] No unreviewed automatic clinical activation exists.
- [ ] FAR is fully merged or explicitly deferred with no half-integration.
- [ ] Orthalis benchmark is current and no stale #407 score is used as a decision basis.
- [ ] Select and record one immutable exact V1 candidate SHA.

### Phase 6 — V0 -> V1 installability certification

- [ ] Lock exact candidate SHA.
- [ ] Pass candidate exact-head CI/certification.
- [ ] Build/certify the Windows cabinet package from the locked dependency/build contract.
- [ ] Execute fresh real-cabinet PREUPDATE.
- [ ] Create and verify PostgreSQL backup.
- [ ] Create and verify media/document backup.
- [ ] Restore backups in isolated rehearsal environment.
- [ ] Run exact candidate migrations.
- [ ] Compare row counts / PK / FK / orphan integrity / documents / media.
- [ ] Prove second Alembic upgrade is a no-op.
- [ ] Prove application startup.
- [ ] Prove `/api/health` and critical smoke paths.
- [ ] Record `INSTALLABLE_CERTIFIED` for the exact candidate SHA.
- [ ] Update the real cabinet from that same immutable SHA.
- [ ] Re-run post-update integrity/startup/critical smoke checks.
- [ ] Close V1 baseline documentation with final installed SHA and evidence.

## Live PR inventory — 2026-09-17 refresh

Current open PRs: `#288 #289 #383 #559 #565 #572 #575 #577 #578 #579`.

| PR | Workstream | Live classification | V1 action |
|---|---|---|---|
| #579 | Céphalo runtime regression | ACTIVE TARGETED FIX / EXACT-HEAD GREEN | CI `35248190003`, P5 `35248189724`, T2 `35248189918` SUCCESS. Merge requires explicit authorization; then prove master CI green. |
| #578 | Windows dependency/build contract | ACTIVE / BROKEN / STALE BASE | Static contract exists, but Windows install run `35248048864` fails: `cryptography==47.0.0` conflicts with `webauthn==3.0.0` requiring `>=49.0.0`. Rebuild on current master after #579. |
| #577 | V1 consolidated roadmap | ACTIVE CANONICAL LEDGER | This file is the single V1 roadmap. Keep updated; no parallel V1 roadmap. |
| #575 | Agenda A4 resources | ACTIVE / INCOMPLETE | Reconcile healthy current master, align runtime/Alembic head, PostgreSQL proof, functional wiring, UI BEFORE/AFTER, exact-head CI, closeout. |
| #572 | Pharmacology denominator/Core-8 evidence | EVIDENCE TO EXTRACT THEN CLOSE | Not literally absorbed by #565; branches diverged. Preserve accepted unique tests/data into clean reconstruction, then close. |
| #565 | Pharmacology Core-5 / fail-closed | ACTIVE SCIENTIFIC CORPUS / STALE INTEGRATION BASE | Never brute-force merge. Review/reconstruct accepted evidence on current master. Keep automatic activation fail-closed pending qualified review if activation is required. |
| #559 | FAR derived-reference runtime/UI + ordonnance bridge | ACTIVE STACK | #576 already merged into this branch at `28e9a13f...`; reconcile whole stack to current master, certify visual/source/regressions/bridge, then merge or explicitly defer. |
| #383 | Portability P13 physical certification | HISTORICAL HUMAN-GATE RUNBOOK | Do not certify old release as V1. Re-issue physical/installability certification against final locked V1 SHA where applicable. |
| #289 | SEC-2 device binding | STALE / DEPENDS ON #288 | Separate security program unless explicitly promoted into V1. Rebuild from current master only after SEC-1 scope decision. |
| #288 | SEC-1 signed licenses / OWNER entitlement | LARGE STALE SECURITY PROGRAM / EXTERNAL PRODUCTION GATE | Do not resurrect wholesale. Production control-plane inputs remain absent; promote only by explicit V1 scope decision and bounded current-master reconstruction. |

## Closed during consolidation — do not resurrect as branches

| PR | Final classification | Proof/action |
|---|---|---|
| #576 | CLOSED / MERGED INTO #559 BRANCH | Merge commit `28e9a13f19c299cb3bbae8a8ffb7b5b542b1a85f`; not on master independently. |
| #563 | CLOSED / FUNCTIONALLY SUPERSEDED | Master already contains canonical numeric-sub license regression on `/api/appointments/`: licensed path reaches 422 validation; unlicensed path returns 403 `NOT_LICENSED`. |
| #505 | CLOSED / OBSOLETE SOURCE DIRECTION | Current master AMMPS 2026 catalog contains ACIGAM 200 MG; old 100 MG supplement relied on historical/cross-check evidence and was not current-directory matched. |
| #407 | CLOSED / HISTORICAL STRATEGY INPUT | Competing historical roadmap closed. Reuse domain structure only; no inherited score. |
| #401 | CLOSED / ALREADY ABSORBED | `backend/tests/test_installments_p5_runtime.py` exists on master. |
| #279 | CLOSED / SUPERSEDED IMPLEMENTATION | Current master `mobile_mdns.py` uses stable HTTPS origin on port 8005 and newer threaded lifecycle; old PR targeted port 5173. |
| #557 | MERGED / ACQUIRED | Master `7c175bdd...`; PostgreSQL green, master CI regression separately tracked by #579. |

## Verified active gaps

### 1. Master health / Céphalo regression

Current master is not yet a clean V1 integration baseline because post-#557 CI `35245309329` is red. The failure is bounded to one Céphalo legacy-injected-model regression after 3746 passing backend tests. #579 provides a targeted one-file repair and is exact-head green on CI/P5/T2.

Closure contract:

`explicit merge authorization -> merge #579 -> master CI rerun -> require green -> only then treat master as healthy baseline for subsequent integration lots`.

### 2. Pharmacology / Ordonnance

#565 contains substantial Morocco-specific scientific evidence and deterministic fail-closed tooling but has a stale/diverged integration base. #572 contains additional unique deterministic denominator/Core-8 evidence and diverged independently from the same ancestor; it must not be discarded merely because #565 is newer.

Closure contract:

- independent documentary/source review of #565 + #572 assets;
- separate regulatory/commercial presence from clinical indication and exact product/form/strength suitability;
- resolve malformed mappings/contradictions;
- reconstruct only accepted assets/tests on clean current master;
- preserve fail-closed behavior for unresolved dimensions;
- if automatic prescription activation is required, complete qualified independent human review before activation;
- deterministic negative tests + exact-head CI + integration review;
- then close the stale evidence branches.

Human gate: qualified independent clinical/scientific review only if automatic clinical activation is required for V1. V1 may instead deliberately ship with automatic clinical activation disabled.

### 3. Agenda

Canonical state: A1/A2/A3 CLOSED; A4 and A5 open.

A4 #575 has the minimal resource model, nullable appointment `resource_id`, tenant-scoped resource CRUD and capacity-1 conflict service. Its known closure sequence remains:

`healthy master -> reconcile A4 -> align runtime schema head to a4rs0000004 -> PostgreSQL from-scratch/no-op proof -> wire create/update/bulk/check-conflicts -> targeted backend tests -> UI BEFORE -> implementation -> AFTER same 390/768/1280 viewports -> visual comparison -> exact-head CI -> closeout -> merge`.

Then A5:

`explicit cabinet timezone -> soft-delete/history policy -> legacy treatment/migration strategy -> transversal regressions -> final Agenda documentation/certification`.

### 4. FAR

FAR remains active but is not intrinsically required by the canonical installability definition of V1.

#576 no longer exists as a separate future integration step: it is already merged into the #559 branch. The whole #559 stack must now be reconciled together.

Rule before freeze: FAR must be either (A) reconciled, fully certified and merged, or (B) explicitly deferred with no dependency left in the chosen V1 candidate. A half-integrated branch is not acceptable.

### 5. Ortho / Céphalo scientific scope

R20 itself is CLOSED and must not be reopened without new scientific evidence. #579 is only a regression fix needed to restore the already-intended legacy injected-model contract.

After the runtime baseline is healthy:

`live master re-baseline -> read canonical scientific inventory -> search remaining BLOCKED/TODO/legacy/scientific gaps -> select only the highest-priority genuine V1-relevant open gap -> Goal/Success/Proof -> execute if required`.

If no critical unresolved V1 scientific blocker exists, record Céphalo as non-blocking rather than manufacturing work.

### 6. Orthalis comparative

#407 is closed and is not a current scorecard. Any comparative score must be recalculated from current Digital Crown evidence and current official Orthalis material. Historical scores may not be carried forward as truth.

Re-benchmark contract:

- current Digital Crown inventory from code/tests/runtime only;
- current Orthalis claims from official sources, with marketing claims labelled as claims rather than independent validation;
- comparable domain-by-domain evidence matrix;
- no inherited historical score;
- gaps relevant to Morocco/local-first/clinical workflow;
- only verified high-value gaps may become V1 blockers; the rest is post-V1.

### 7. Windows cabinet dependency/build contract

#578 exposes a real installability problem rather than a cosmetic CI issue. Its static contract passes, but the clean Windows dependency install is unsatisfiable as pinned: `webauthn==3.0.0` requires `cryptography>=49.0.0`, while the branch pins `cryptography==47.0.0`.

Closure contract:

`#579 integrated -> replay #578 on current master -> choose exact compatible dependency set -> clean Windows install -> pip check -> import smoke -> build guard -> exact-head Windows contract green -> relevant package/certification wave -> merge accepted contract`.

Do not weaken security/dependency constraints merely to make the resolver green.

### 8. Connect Hub

#557 is acquired on master. PostgreSQL post-merge certification is green (`35245309371`). The global post-merge CI is not green because of the separate Céphalo regression now isolated in #579. Connect Hub itself must not be treated as false remaining product work.

## Consolidated execution order

### Gate 0 — Restore healthy master

1. #579 exact-head proof is already green.
2. Human gate: explicit authorization to merge #579.
3. Merge #579.
4. Require post-merge master CI green.

Independent analysis work may continue while merge authorization is absent, but subsequent product integration must not pretend the current red master is fully healthy.

### Phase 1 — Finish autonomous high-value active work

1. Agenda A4 (#575) through PostgreSQL + functional wiring + UI proof.
2. Agenda A5 final robustness/closeout.
3. Reconcile FAR #559 as one stack including the already-merged #576 bridge if FAR remains in V1 scope.

### Phase 2 — Pharmacology / Ordonnance scientific closeout

Review #565 and #572 together as evidence sources, reconstruct accepted material on current master, and keep unresolved medication domains fail-closed. Prepare/execute the qualified review gate only if automatic clinical activation is in V1 scope.

Do not use a human clinical-review wait as a reason to stop independent engineering work.

### Phase 3 — Ortho/Céphalo scientific re-baseline

After #579 is integrated and master green, re-baseline current scientific inventory and select at most the genuine next critical scientific lot. If none blocks V1, record the domain non-blocking.

### Phase 4 — Orthalis benchmark refresh

Rebuild the comparative matrix against near-final Digital Crown. Convert only evidence-backed critical gaps into bounded final V1 lots. No stale #407 score carry-over.

### Phase 4B — Windows installability foundation

Rebuild #578 on the then-current master, resolve the real dependency conflict, prove clean Windows dependency installation/build contract, and merge the accepted foundation before candidate freeze.

### Phase 5 — Functional freeze

Requirements:

- master green for included scope;
- all selected V1 workstreams closed and on master;
- all intentionally deferred work documented as non-dependent on V1 candidate;
- no migration-head inconsistency;
- no unresolved red exact-head workflow relevant to included scope;
- Windows dependency/build contract resolvable and certified;
- no unreviewed automatic clinical activation;
- FAR either merged or explicitly deferred;
- Orthalis benchmark current;
- current master represents the intended feature freeze.

Output: choose one exact candidate SHA. Do not move it afterward.

### Phase 6 — V0 -> V1 installability certification

Execute the canonical managed-update contract:

`candidate SHA lock -> candidate CI -> Windows package/build proof -> fresh real-cabinet PREUPDATE -> verified PostgreSQL + media/document backups -> isolated restore -> exact migrations -> row/PK/FK/orphan/document/media integrity comparison -> second Alembic upgrade no-op -> app startup -> /api/health + critical smoke -> INSTALLABLE_CERTIFIED -> real cabinet update from same SHA -> post-update integrity/startup/smoke -> V1 baseline closeout`.

No code-certified SHA becomes V1 merely because CI is green.

## Critical path

Current critical path:

`#579 integration + master green -> Agenda A4/A5 -> pharmacology evidence reconstruction/review decision -> Céphalo scientific re-baseline -> Orthalis refresh -> Windows build/dependency contract -> functional freeze -> exact V1 SHA -> V0→V1 installation rehearsal/certification -> real cabinet update`.

FAR runs alongside this path and must be resolved by merge or explicit defer before freeze. Connect Hub is already acquired on master.

SEC-1/#288, SEC-2/#289 and historical P13/#383 remain separate from the first V1 functional path unless explicitly promoted. Their stale branches must never be brute-force merged into V1; any promotion requires bounded current-master reconstruction and the relevant human/external gates.

## Freeze gates

V1 candidate selection is blocked if any of these are true:

- master CI remains red for included scope;
- selected functional lot still open;
- schema runtime head differs from the unique Alembic head;
- required CI/certification is red or absent on included changes;
- Windows cabinet dependency/build contract is unresolved;
- pharmacology has automatic clinical activation without the required qualified independent review;
- FAR code is half-integrated rather than merged or explicitly deferred;
- Orthalis benchmark relies on stale #407 scores rather than current evidence;
- candidate SHA is moving;
- fresh cabinet PREUPDATE/backups/rehearsal proof has not been completed for installation certification.

## Next exact

Human merge gate: #579 is exact-head green but is not merged. After explicit merge authorization, merge #579 and require post-merge master CI green.

Until that gate is crossed, the next independent executable work is to re-baseline Agenda A4 #575 and continue the pharmacology documentary/evidence review without performing product integration that assumes master is green.

No Vercel deployment is part of this roadmap without explicit user authorization.
