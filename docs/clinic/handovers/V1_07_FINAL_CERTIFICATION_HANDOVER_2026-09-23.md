# HANDOVER — Digital Crown V1-07 — final certification continuation — 2026-09-23

## Goal
Close V1-07 with a clean, evidence-backed exact-head certification, then continue to G9 → heavy gates → G10 → human merge gate. No Vercel deployment is authorized.

## Repository state — verified
- Repository: `hraaaaf/Digital_crown`
- PR: #633 — `audit(v1-07): global interactive certification G0→G10`
- PR state: OPEN / DRAFT / mergeable=true at last check
- PR branch: `audit/g0-global-interactive-inventory`
- Current PR HEAD: `82eca76cae2863d191d0fe17d2fafe4ff1ab31bd`
- Current HEAD commit: `fix(v1-07): close final browser certification blockers`
- No merge performed.
- No Vercel deployment performed.

## Exact-head CI snapshot — verified
For HEAD `82eca76cae2863d191d0fe17d2fafe4ff1ab31bd`:
- 85/85 runs completed
- 64 SUCCESS
- 19 FAILURE
- 2 SKIPPED

Important green proof:
- PostgreSQL Alembic Schema Certification = SUCCESS
- Previous exact-head work already validated PC-00, Clinic P3 Provenance, G0, G8, G4 Treasury AFTER and multiple settings/portability gates on prior candidates.
- Alembic convergence is no longer the blocker.

## Corrections already present in current HEAD
The current HEAD already contains the corrections prepared during this window:
- G1 browser harness/navigation updates.
- G2 duplicate-check harness changes.
- G6 lifecycle selector scoping changes.
- Product logout double-navigation fix in `frontend/src/components/Header.tsx`.
- G3 product fix in `frontend/src/features/agenda/AgendaModal.tsx`: submit guard now uses `dateValue` rather than `selectedDate`.
- Stock G7 JSDOM-only focus assertion adjustment.
- G5 scoped save acknowledgements.
- G7 superadmin auth-store hydration.
- G6 product plan mutation sends explicit JSON body `{}`.
- PostgreSQL runtime head aligned to merge revision `v1070000016`.

## Current failing gates — exact latest causes

### G1 Browser — run #35925423074
FAIL at logout confirmation:
`Error: logout confirm kept access token`
at `certify-v1-07-g1-browser-actions.mjs:347`.

Interpretation:
- Earlier double-navigation defect was fixed.
- New remaining issue is token persistence/cleanup semantics after logout.
- Next step: inspect `authService.logout()`, cookie/session fallback and the mocked `/api/auth/logout` behavior in G1. Do not weaken the assertion until proving whether token cleanup is product or harness.

### G2 Browser — run #35925423373
Still fails waiting for:
`Vérification anti-doublon indisponible`
at line 317.

Interpretation:
- Product `AddPatientForm` contains the fail-closed catch path.
- Harness route broadening alone did not make the scenario reach that path.
- Next step: capture actual request sequence around submit (dossier availability, validation, duplicate POST) and prove which request is or is not emitted before changing code.

### G3 Browser — run #35925423327
Still fails:
`page.waitForResponse: Timeout 10000ms`
at line 247 waiting for appointment POST.

Interpretation:
- Current HEAD already changed `AgendaModal.handleSubmit` guard from `selectedDate` to `dateValue`.
- This did not clear the browser gate.
- Next step: instrument/inspect browser request sequence around `Confirmer le RDV` and determine whether HTML/form state, route interception, or modal instance selection prevents POST.

### G5 Browser — run #35925423319
Now fails later than previous save-ack ambiguity:
timeout waiting for exact text `À actualiser`
at line 356.

Interpretation:
- G5 progressed past the previous strict-mode `Configuration enregistrée` duplicate.
- Next step: inspect the exact settings state/control expected around line 356; classify product state vs stale harness copy before editing.

### G6 Browser — run #35925422941
Now fails later:
strict mode violation on global `getByTitle('Archiver')` resolving 4 elements
at line 194.

Interpretation:
- Previous `Suspendre/Réactiver` ambiguity was cleared.
- Remaining issue is the same harness class: archive control must be scoped to the `Dr T2 Browser` card.
- This is a high-confidence targeted harness fix.

### G7 Browser — run #35925423264
Fails immediately:
`Error: G7 superadmin /auth/me failed`
at line 16.

Interpretation:
- `SUPERADMIN_EMAIL` and `T2_SUPERADMIN_EMAIL` are now correctly set.
- The added direct `superApi.get('/api/auth/me', { Authorization: Bearer ... })` is not accepted in this context.
- Previous browser redirect was caused by Zustand `auth-storage` not being hydrated.
- Next step: reuse the login payload / existing authenticated browser or request context without introducing a failing extra `/auth/me` preflight; then seed `auth-storage` with a verified superadmin-shaped user only from a proven source.

### CI — run #35925423184
Frontend failure is now a stale test expectation in SuperAdmin plan mutation:
expected:
`api.patch(path, null, { params })`
received:
`api.patch(path, {}, { params })`

Interpretation:
- Product change to `{}` is intentional and previously required to avoid 411 Content-Length.
- Update the affected SuperAdmin tests to expect `{}`, not `null`.
- Do not revert product behavior.

## Known workflow/config failures
Several workflows still fail pre-job / configuration and should not be treated as product defects without job evidence:
- `.github/workflows/cust-05-stock-lab-visual.yml`
- `.github/workflows/patient-companion-d2-visual-cert.yml`
- `.github/workflows/pc08-staff-before-visual.yml`
- `.github/workflows/pc08-staff-after-visual.yml`

## Safety / execution doctrine
- Do not merge PR #633 until the final certification sequence is proven.
- Do not deploy Vercel.
- Do not run a global rerun storm.
- Batch remaining deterministic fixes into one commit when practical.
- Before any new commit, re-fetch PR HEAD because it changed during this window.
- If HEAD changes concurrently, do not force-update; compare file SHAs and preserve concurrent changes.
- For UI changes: BEFORE → written goal → mock/reference → implementation → AFTER same viewports → comparison/tests → visual score.
- No current planned fix requires a visual product change unless a new product defect is proven.

## Next exact
1. Re-fetch PR #633 HEAD and exact-head state.
2. Fix the deterministic items first:
   - CI SuperAdmin tests: `null` → `{}`.
   - G6 archive selector scoped to `Dr T2 Browser`.
3. Diagnose, without guessing:
   - G1 logout token retention.
   - G2 duplicate-check request sequence.
   - G3 appointment POST request sequence.
   - G5 `À actualiser` expected state.
   - G7 authenticated superadmin bootstrap without failing extra `/auth/me`.
4. Build one grouped commit.
5. Consume only exact-head targeted verdicts first.
6. When browser/CI gates are clean, continue G9 → heavy gates → G10 → human merge gate.
7. Update Notion and this handover after the next significant verified transition.

## Canonical project handover / Notion
Notion handover page:
`3e477c66-3362-812e-a7b0-d40511e4545f`
Title:
`🧭 HANDOVER PROPRE — Digital Crown V1-07 — G4 → fermeture V1 — 2026-09-23`

## Resume instruction for the next window
Start by reading this file, then:
- verify PR #633 HEAD,
- verify exact-head runs,
- verify whether any concurrent commit landed,
- continue from **Next exact** above.
