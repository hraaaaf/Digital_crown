# HANDOVER — Digital Crown V1-07 — Global Interactive Certification

Date: 2026-09-23
Repository: `hraaaaf/Digital_crown`
Main work branch: `audit/g0-global-interactive-inventory`
PR: #633
PR state at handover: OPEN / DRAFT / mergeable
Live PR HEAD verified at handover: `82eca76cae2863d191d0fe17d2fafe4ff1ab31bd`
Base branch: `master`

## Goal

Close Digital Crown V1-07 global interactive certification G0→G10 with zero unclassified blocking red gates, verified exact-head evidence, canonical documentation, and only then proceed toward final V1 closure.

Success = every blocking exact-head gate either SUCCESS or explicitly proven non-blocking/pre-job infrastructure; all real product defects fixed and revalidated; no merge before the human/closeout gate.

Proof = GitHub exact-head runs + code/log inspection + canonical Notion handover + post-fix reruns.

## Current live state

PR #633 currently points to `82eca76cae2863d191d0fe17d2fafe4ff1ab31bd`.

Latest commit message:
`fix(v1-07): close final browser certification blockers`

Files changed by that live commit:
- `frontend/scripts/certify-v1-07-g1-browser-actions.mjs`
- `frontend/scripts/certify-v1-07-g2-browser-actions.mjs`
- `frontend/scripts/certify-v1-07-g6-browser-actions.mjs`
- `frontend/src/components/Header.tsx`
- `frontend/src/features/agenda/AgendaModal.tsx`
- `frontend/src/pages/StockPage.g7Interactive.test.tsx`

Important: this HEAD was created after the previous candidate `0d17e67a...`. Treat `82eca76c...` as source of truth on resume. Do not continue from older SHAs without first rechecking PR #633.

## Exact-head CI snapshot

For `82eca76c...`, observed aggregate state:
- 89 completed runs
- 64 SUCCESS
- 23 FAILURE
- 2 SKIPPED

Blocking/structural target gates observed:
- PostgreSQL Alembic Schema Certification: SUCCESS
- G1 Browser Action Certification: FAILURE
- G2 Browser Action Certification: FAILURE
- G3 Browser Action Certification: FAILURE
- G5 Browser Action Certification: FAILURE
- G6 Browser Action Certification: FAILURE
- G7 Browser Action Certification: FAILURE
- CI: FAILURE

Several failures are known pre-job/workflow-class failures and must not be misclassified as product defects:
- `cust-05-stock-lab-visual.yml`
- `patient-companion-d2-visual-cert.yml`
- `pc08-staff-before-visual.yml`
- `pc08-staff-after-visual.yml`

## What was already fixed and proven

### PostgreSQL / Alembic

Previously there were two Alembic heads from PR/master convergence:
- `cust02000015`
- `pc080000015`

The branch was converged with merge revision `v1070000016`, and runtime schema head was aligned accordingly.

Current proof:
- PostgreSQL Alembic Schema Certification = SUCCESS on the latest candidate family.

This is no longer the primary blocker.

### P3 Document Provenance

Previous real defect:
- archive payload could expose `tags=None` while schema requires `List[str]`.

Fix:
- normalize to `[]`.

Proof from prior exact-head run:
- Clinic P3 Document Provenance Certification = SUCCESS.

### PC-00 Patient Companion

Previous harness defect:
- IndexedDB opened with forced version 1 while DB was already version 2.

Fix:
- open current DB version instead of forcing version 1.

Proof from prior exact-head run:
- PC-00 Patient Companion Visual Certification = SUCCESS.

### G6 product mutation

A real product issue was identified earlier:
- plan mutation used `PATCH(..., null, { params })`
- backend middleware could reject it with HTTP 411 Content-Length.

Fix was applied in the candidate chain:
- send an explicit JSON body `{}`.

Subsequent G6 failures progressed past this issue and became selector/harness failures, which supports that the 411 blocker was fixed.

## Important remaining classifications

### G1

Earlier root cause was real product behavior:
- `authService.logout()` navigated to `/login`
- `Header.handleLogout()` then navigated to `/landing`
- double navigation produced `net::ERR_ABORTED`.

The latest live commit `82eca76c...` modifies both G1 harness and `Header.tsx`, so this area has changed again.

Resume action:
- read latest G1 failure log at exact HEAD `82eca76c...`
- verify whether the double-navigation product defect is gone
- do not assume the earlier diagnosis still applies unchanged.

### G2

Previous failure:
- browser harness timed out waiting for fail-closed anti-duplicate message.

Product source already contains the fail-closed catch/message:
`Vérification anti-doublon indisponible. Réessayez avant de créer le patient.`

Latest live commit modifies the G2 browser harness.

Resume action:
- inspect latest G2 log on `82eca76c...`
- determine whether the new failure is still harness timing/routing or a real product regression.

### G3

Previous failure:
- browser harness timed out waiting for POST appointment ACK.

The latest live commit modifies `AgendaModal.tsx`, so a product-side appointment change is now present.

Resume action:
- inspect latest G3 failure log first
- verify whether the modal change actually addresses the missing request/ACK path.

### G5

Previous failure was deterministic harness strict-mode:
- text `Configuration enregistrée` existed both in toast and save bar.

A technical branch had prepared scoping to `settings-save-bar`, but the current PR HEAD must be checked because the live HEAD changed after that preparation.

Resume action:
- inspect latest G5 log and current script before porting anything.

### G6

Previous failure after the 411 fix:
- global `getByTitle('Suspendre')` resolved multiple client cards.

Expected harness fix:
- scope Suspendre/Réactiver checks to the `Dr T2 Browser` card.

The live commit modifies G6 harness, but G6 is still red.

Resume action:
- inspect exact latest G6 log; do not blindly reapply the old selector patch.

### G7

Earlier configuration issue was fixed by providing both:
- `SUPERADMIN_EMAIL`
- `T2_SUPERADMIN_EMAIL`

Then G7 still redirected `/approvisionnement/admin`.

Root cause identified:
- route authorization reads `useAuthStore().user?.is_superadmin`
- browser harness had only seeded localStorage access/refresh tokens
- token presence alone does not guarantee the persisted Zustand user is hydrated before route evaluation.

A technical branch prepared:
- GET `/api/auth/me` with superadmin token
- seed `auth-storage` with the returned user and `isAuthenticated=true`

Important: that prepared change was not yet proven merged into the live PR HEAD when this handover was written.

Resume action:
- inspect current G7 script on `82eca76c...`
- if auth-store seed is absent, port it once
- rerun only after grouping with the other proven blockers.

### CI / Stock focus

Prior CI frontend failure:
- 10/11 StockPage G7 interactive tests passed
- only failure: expected focus to return to delete opener after closing dialog with Escape.

`CrownDialog` already contains opener capture and cleanup focus restoration.

Latest live commit modifies `StockPage.g7Interactive.test.tsx`.

Resume action:
- inspect exact current CI failure
- classify whether current test still races JSDOM cleanup or whether latest change introduced a different failure.

## Rules for the next window

1. Re-read this handover.
2. Re-fetch PR #633 live HEAD before any action.
3. If HEAD != `82eca76c...`, treat the newer SHA as source of truth and diff it first.
4. Fetch exact-head workflow runs.
5. Read current failure logs for G1/G2/G3/G5/G6/G7/CI.
6. Do not reuse stale logs from `0d17e67a...` or older candidates as current proof.
7. Batch only proven fixes into one commit.
8. Avoid a global rerun storm.
9. No Vercel deployment without explicit user approval.
10. No merge until exact-head certification and closeout gates are genuinely satisfied.

## Known non-goals / constraints

- Digital Crown remains local-first/on-prem.
- Firebase is only for auth/licensing.
- Zero-runtime-LLM doctrine remains in force.
- No Vercel deployment is authorized.
- Odontogramme Premium stays after V1 closure unless explicitly reprioritized.

## Canonical Notion handover

Page ID:
`3e477c66-3362-812e-a7b0-d40511e4545f`

Title:
`🧭 HANDOVER PROPRE — Digital Crown V1-07 — G4 → fermeture V1 — 2026-09-23`

Notion remains the narrative source of truth for the handover timeline; GitHub remains the source of truth for code/HEAD/run status.

## Next exact

1. Fetch PR #633 and confirm current HEAD.
2. Fetch exact-head runs for that HEAD.
3. Read latest G1/G2/G3/G5/G6/G7/CI failures.
4. Reclassify each as product / harness / workflow-pre-job.
5. Apply only still-valid proven fixes.
6. Produce one grouped candidate commit.
7. Consume exact-head results.
8. If green enough for final closure: G9 → heavy gates → G10 → closeout docs → human merge gate.

## Stop condition

Do not declare V1-07 closed, certified, production-ready, or 100% until exact-head proof supports it.
