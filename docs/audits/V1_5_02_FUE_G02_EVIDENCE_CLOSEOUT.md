# V1.5-02 — FUE-G 02 patient photo: retrospective evidence and closeout boundary

Date: 2026-10-09  
Repository: `hraaaaf/Digital_crown`  
Baseline: `master@a7e3559c1eea922f95595f3025d8a3c9db5f0cb9` (after PR #813).  
Scope: **documentation/audit only**; does not change product or assert a new browser test run.

## Goal and required journey

Canonical [FUE plan](https://app.notion.com/p/3f177c66336281c49a48d1361307f458): V1.5-02.1 is FUE-0 (photo backend/permissions), 02.2 FUE-I (file/webcam → crop → confirmation), 02.3 FUE-I cross-surface (PatientList, dashboard search, waiting room, agenda, dossier), and 02.4 FUE-G 02 (no photo → add → replace → delete → initials; desktop/mobile).

**Do not equate** an existing CI success, a user-approved screenshot, or PostgreSQL post-merge success with an exhaustive first-user or physical-cabinet FUE. Keep the `FUE-G 01` physical multi-PC gate separate.

## Exact-head provenance

1. PR [#812](https://github.com/hraaaaf/Digital_crown/pull/812) merged at `bcbd03cf12dae6314298029fcfbe433c3a7058b1` from visual/head `c77a9bde00046bee43d33a6155acd6c67463a11d`, with targeted fixes for dashboard search overlap and patient list badges, plus corrected photographic fixture/capture oracle. PR [#810](https://github.com/hraaaaf/Digital_crown/pull/810) CLOSED/NOT MERGED, superseded by the changes in #812.
2. On final `master@a7e3559c1eea922f95595f3025d8a3c9db5f0cb9`, GitHub blob SHA is **identical to approved PR #812 HEAD** for **each** of:
   - `frontend/scripts/capture-v15-02-3-photo-ui-after.mjs` (`a6bae01e90495358d3bc43dd2fab38675e89f1d9`)
   - `frontend/src/features/patients/components/PatientPhotoEditor.tsx` (`01d6e7ee29736d8a9deee0fc66ae1447bb89b5eb`)
   - `frontend/src/features/dashboard/components/DashboardHeader.tsx` (`6b213157e3317db94dcd96a81dd6c48e15fc3e98`)
   - `frontend/src/features/patients/PatientList.tsx` (`afe815be9e460e5fe2440333e2f4992db017a8eb`)
   - `.github/workflows/v15-02-4-photo-lifecycle.yml` (`8ed4903dc3c9ea45f50d98c080122f8cd6de2661`).
3. Master-push PostgreSQL release-compatibility [run #37998922804](https://github.com/hraaaaf/Digital_crown/actions/runs/37998922804) succeeded on the actual final master SHA: **24 passed**, zero skips in its Pytest summary, Windows PowerShell 5.1 SUCCESS; PostgreSQL ECR image pulled by the immutable digest. **That run does not execute the Photo Lifecycle browser workflow.** The source parity in (2) is what permits attribution of the previously approved browser evidence to these unchanged specific files; it is not a new complete master FUE run.

## Evidence matrix and verdicts

| Sub-lot / requirement | Evidence | Strict conclusion |
| --- | --- | --- |
| 02.1 canonical backend photo contract | [Photo Lifecycle run #37990009915](https://github.com/hraaaaf/Digital_crown/actions/runs/37990009915) executed `backend/tests/test_patient_profile_photo_v15.py`: **8 passed** | **PASS scoped** on tested backend contract; not independent proof of all tenant/role combinations in a real cabinet |
| 02.2 file import → crop dialog → save; replacement | Current harness `uploadViaUi` uses `getByLabel('Importer une photo du patient').setInputFiles`, verifies `Recadrer la photo` dialog and clicks `Enregistrer la photo`, twice with different synthetic PNGs | **PASS scoped / file import**, webcam hardware and human first-time onboarding not shown |
| 02.3 propagation | Actual Chromium artifact [#11644568410](https://github.com/hraaaaf/Digital_crown/actions/runs/37990009915/artifacts/11644568410) has 4 phases × 5 surfaces × 2 viewport sizes, with `evidence.json` and unique hashes for add/replace | **PASS scoped**, no horizontal overflow or JS page errors in collected JSON; screenshots reviewed, not a universal layout proof |
| 02.4 removal and initials fallback | `removeViaUi` clicks actual visible **Supprimer** button, waits for **Initiales du patient**; `assertSurfaces` checks across all five surfaces afterward | **PASS scoped**, no direct API shortcut for final deletion; `resetNoPhoto` API call is test fixture reset only |
| Responsive UI regressions | `dashboard-search-proof.json`: `geometry.pass=true`, `titleOverlap=false`, `badgeGeometry.pass=true` and three badge labels within measured container at 390×844 and 1280×900; corresponding images in artifact | **PASS automatic geometry**; mobile screenshot first viewport crops the lower patient card below fold, so badge geometry is better substantiated in JSON than in that screenshot alone |
| Exact-head visual + human decision | [A/B review and confirmation #6089558942](https://github.com/hraaaaf/Digital_crown/pull/812#issuecomment-6089558942), security/proof 9.4/10, mobile **9.1/10**, desktop **9.2/10**; [Human Visual Approval #37993697685](https://github.com/hraaaaf/Digital_crown/actions/runs/37993697685) SUCCESS on approved `c77a9bd...` | **APPROVED only for that historical visual SHA**; blob comparisons above establish parity for five touched files at final master, but not fresh human approval of an entirely new full-product master snapshot |

Artifact verification (re-inspected 2026-10-09): the ZIP has **46 entries: 40 actual PNG scenario snapshots, four supplemental screenshot proofs, and two JSON proof files**. `evidence.json.productHead` and geometry `head` are exactly `c77a9bde...`, `success=true`. For both 390×844 and 1280×900, images are decoded during added/replaced, and no photos are present for initial/deleted. Distinct orange/purple and cyan/green mock portraits are visibly different in observed screenshots; snapshots cover all five surfaces and both viewport types. The explicit recorded backend fixture is isolated Vite/T2, not a real patient record.

## Adversarial review (internal, two perspectives)

**Perspective A — test integrity / release:** count the images from the actual ZIP instead of trusting the run name; cross-check report SHA, actual run logs (8 backend tests, 36 frontend tests, real Chromium), hashes for different photos, zero skips in reported tests, UI upload/delete selectors, absence of hidden retry/skip gate. Confirm files are byte-for-byte unchanged on merge master. **No significant regression or false-pass mechanism demonstrated in this reviewed narrow evidence.** Historic PR run is not rebranded as fresh master browser run.

**Perspective B — UX / authorization / scope:** verify mobile/desktop screenshots, check prior search overlapping title and mobile badge defects against AFTER, distinction between `photo` and `initials` across five surfaces, hover overlays and below-fold behavior. The test **injects an already-issued auth token via `page.addInitScript`** and mocks some appointment GET results; it does **not** prove genuine user signup/login from a completely blank profile, real webcam capture, real LAN/TLS, physical devices, multiple tenants, or cross-role permission negatives. Badge proof has a below-fold visual framing limitation. **No new BLOCKER in tested photo workflow; incomplete coverage prevents an exhaustive first-user/full-terrain FUE claim.** Reviews A/B here are internal, not external independent reviewers.

## Decision / gates

- **02.1 photo backend contract: scoped lab PASS.**
- **02.2–02.4 photo lifecycle: targeted browser FUE + exact-head visual approval PASS**, traceable to unchanged master sources.
- **FUE-G 02 exhaustive / V1.5-02 formal global closeout: OPEN / PARTIAL**, unless the project owner explicitly accepts a lab-only closeout and the remaining persona/device/authorization gaps are addressed or separately scoped out with proof.
- **FUE-G 01** remains a distinct physical server + two annexes / HTTPS LAN / outage-recovery validation, not supplied by this photo artifact.
- Required vs experimental vs out of scope: Photo Lifecycle tested targeted requirement is **REQUIRED** for this closeout, unrelated M6-I skipped workflow **HORS SCOPE**, synthetic/mock evidence is **EXPERIMENTAL for real-world claims**.
- No new runtime, DB, auth, workflow or Vercel changes; this document is **not a merge authorization**.

## Next executable validation

1. Extend/execute a fresh-profile FUE with **real login/auth UX** and test patient avatar upload/crop/delete end to end without preinjecting a token; confirm a role without patient photo permission cannot mutate, and a different tenant cannot see the photo. Use synthetic patient data only.
2. Add an auditable screenshot with the 390px patient badge row intentionally scrolled into view rather than only verifying off-screen geometry.
3. On the candidate exact SHA, collect screenshots and real CI, run two internal adversarial reviews and confirmation (P0/P1/P2 and strict scores); get the appropriate human visual gate if its source changes.
4. Reconcile this dossier with the [canonical V1.5 roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb); do not start V1.5-04 until the ongoing retrospective FUE campaign has been handled according to the owner’s earlier decision.
