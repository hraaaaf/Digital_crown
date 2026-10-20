# TECHDOUBT — Digital Crown

## GLOBAL-G10-S / LOT10 — 2026-10-18 — Two-agent isolation requirement withdrawn

**Status: RESOLVED AS A FALSE DEPENDENCY (doctrine correction, not proof of a completed FUE).**

**Previous concern:** The merged PR #960 required two AI BLIND USER agents running in independent contexts, with separate browsers and withheld reports. That had been documented as a blocking precondition even for ordinary internal adversarial review. The product owner clarified that the **same ChatGPT conversation should perform both specialized perspectives A/B itself** rather than waiting for humans or two separate AI agents.

**Resolution rule:** `AGENTS.md`, `.claude/rules/execution-scoring-verification.md` and `docs/quality/REALITY_PROOF_GATE.md` now instruct the assistant to write two distinct, task-specific *internal adversarial* reviews, correct/test, rerun on new HEAD and confirm. This is not evidence of two genuinely independent reviewers; it is sufficient for the **internal A/B double-review procedure**. Self-review is capped at 9.4/10 and normal VERIFIED starts at 9.0/10 when required proofs/gates pass. No external reviewer or two-agent orchestration is a prerequisite.

**Distinct unclosed verification work — GLOBAL-G10-S:** Inventory V1+V1.5 routes/features, execute actual frontend/backend FUE journeys on fictitious tenants starting at login (or a public entry where applicable), preserve BEFORE/ACTION/AFTER, negative RBAC/tenant checks, exact-HEAD evidence and CI statuses. **These tests have NOT been executed by this documentation correction.** An imagined browser session or two written perspectives are not executable test proof.

**Unchanged gates:** Specifically required human clinical/regulatory/visual approvals and LOT10 hardware/person-on-device observations remain separate from conversation-based A/B review. No deployment, merge or clinical activation is authorized by this documentation.

**Historical origin:** PR #960, master merge `3cbd1d83cdbcbf97e71019a3182f4699d9645421`. This file supersedes the inaccurate "two-agent independence not yet demonstrated" as an *internal review blocker*.


## 2026-10-19 — FUE-first governance migration (#988)
- ACTIVE doctrine migrated in AGENTS.md, CLAUDE.md, scoring, RPG, visual closeout, PR template, policy contract test and G10-S documentary checker.
- RESERVE: historical audit/handover files and specialist skills may still describe mandatory A/B reviews. They are historical or domain-specific evidence, not an override of active FUE-first policy; assess applicability before changing them, do not rewrite old evidence.
- RESERVE: repository-wide policy contract tests and G10-S have not been executed locally in this connector session; CI on final HEAD and applicable gate must be checked before merge. FUE-0 documentary only, no UI journey or clinical/physical certification claimed.

- CLOSEOUT RESERVE (2026-10-19): active `skills/reality-proof-gate/SKILL.md` still imposed mandatory two A/B reviews; corrected in PR #988. Final HEAD after this consistency correction requires fresh exact-HEAD CI results. Previous GREEN on `c91776c` does not certify later commits. PR remains DRAFT/OPEN; no merge or deployment authorized. Historical files remain out of scope.


## LOT07 / 07-C — 2026-10-20 — PR #989 trusted visual approval, FUE-0

- **Scope / evidence:** PR #989 corrects only the trusted `pull_request_target` label revocation script and its tests. Canonical FUE level: **FUE-0**, not FUE-I/G; no first-user Cabinet journey or screenshots are claimed. CI on `c54b118e60516ef86b38eddf172d0b30e8980d40`: 22/22 mocked GitHub API contract tests pass in both Visual Gate Security Regression and UI Visual Approval Contract; CI Scope Gate GREEN. Human Visual Approval GREEN is **`skipped-non-ui`**, not proof of an actual UI owner `labeled` approval event.
- **RESERVE (expected gate restriction):** Until this PR is reviewed and merged with explicit authorization to trusted `master`, the `pull_request_target` workflow still runs the older script; PR #971 still needs fresh exact-HEAD visual evidence plus a genuine owner-applied approval label event. Its `synchronize` failing closed is expected, not a defect to bypass.
- **RESERVE (proof boundary):** GitHub API failure, absent label, SHA race, label-removal no-op, and owner identity paths are exercised via mocked Node tests, **not** a real GitHub owner-label workflow on a UI PR. This is sufficient FUE-0 code/contract evidence, not a verified FUE-I/G user journey or live end-to-end approval certification.
- **Next:** confirm final HEAD targeted CI after this documentary reservation; keep PR #989 DRAFT/no merge/deploy without approval; after trusted patch lands, acquire fresh screenshots and exact-head human visual approval for #971.

## LOT07 / 07-C — 2026-10-20 — Integration reconciliation after research PR #961

**Active reservation:** The isolated Command React target has no Cabinet backend, real login, RBAC, patient records, production UI integration or clinical certification. Shared CSS still requests Google Fonts, so fully offline/private egress is NOT certified. Keep 07-D/E frozen.

**Merge conflict and safety decision:** PR #971 diverged from #989's trusted visual approval gate. Resolve by preserving the **unchanged master script** from merged #989 (owner-only labeled event, SHA match and fail-closed synchronize); additionally retain two targeted sanitized 403/500 regression tests from the research branch. Preserve visual UI blobs exactly, do not merge deprecated trusted script from #971. The merge reconciliation creates a new source HEAD, invalidating the previous SHA-bound owner approval until fresh exact-HEAD screenshots and a genuine authorized owner `labeled` event succeed. DO NOT describe the old GREEN as approval of the new SHA. Do not merge #971 until the trusted gate is GREEN again.

**Historical context, not active release gates:** The following #971 branch notes are preserved as an audit trail of earlier experiments. Any historical claim that two independent blind-user agents are mandatory, or that the visual-gate fix/approval remains OPEN on the old SHA, is superseded by the canonical FUE-first policy and later GitHub evidence.

## LOT07 / 07-C — 2026-10-19 — visual approval revocation error cause unknown

**Status: OPEN / MAJOR gate availability; fail-closed retained.**

**Evidence:** Human Visual Gate run https://github.com/hraaaaf/Digital_crown/actions/runs/39313124584 failed with `Failed to revoke stale visual approval`. The `synchronize` handler attempts DELETE of `visual-approved-by-achraf`, tolerates 404, verifies label disappearance and refuses stale approval. Original HTTP status was not visible in CI log. Commit `b499e9604e6336bc7a4e509e184148841c74f91f` adds only sanitized HTTP status reporting; it does not change approval or revocation semantics.

**Unresolved:** Actual HTTP status and cause (workflow token permission `issues:write`, API behavior or other), whether label existed, trusted workflow configuration, rerun outcome, and human approval remain unverified. No Cabinet integration or production proof. React synthetic screenshot disables sticky only during full-page snapshot; actual sticky scrolling requires separate verification. Whole-app TypeScript and full accessibility audit remain unproven.

**Resolution gate:** Inspect exact trusted workflow permissions and event payload; run tests for 403, 404, 500 and label absence; rerun gate against new exact HEAD, diagnose sanitized status, preserve fail-closed and require fresh owner-labeled approval. Repeat independent A/B review on same final HEAD. Keep PR #971 DRAFT and CONVERGED=NO until verified.


## LOT07 / 07-C — 2026-10-19 — FUE evidence gate on exact HEAD

**Status: OPEN / REQUIRED evidence, no product defect asserted.** FUE replaces additional independent reviewer opinions for this sublot, but passing unit tests and older Chromium artifacts are not two blind-user FUE traces.

**Evidence:** HEAD c7d57d31db8d02daf13d8917c383b0f164dab5bf: Visual Gate Security Regression, UI Visual Approval Contract and CI Scope Gate SUCCESS. React target is standalone synthetic-only; patient switch uses confirmation and an inert dialog; session reducer rejects unauthorized mock transitions. The last cited screenshot artifact belongs to older HEAD e3ff472485731961238ea2fac1a1fb72ae55ab59, so it cannot certify current HEAD. Trusted pull_request_target workflow checks out default branch, so PR-only gate diagnostic changes do not run in that privileged workflow until separately promoted through an authorized safe process.

**FUE-A / REQUIRED — clinical workflow:** From fresh isolated browser profile at exact HEAD, execute TEST-001 consultation pause/resume/finish, same-practitioner next patient, A→B→A and Dossier→Imagerie→Dossier; capture before/action/after, patient IDs, keyboard focus, 390/430/768/1280, 200% zoom. Confirm no patient A content under B and all nonfunctional actions explicitly synthetic.

**FUE-B / REQUIRED — safety and accessibility:** Separate fresh profile and independent trace; attempt stale pending switch, Escape/cancel/focus restoration, keyboard-only tabs, rapid patient switching, no backend requests, no cross-patient leakage, mobile sticky context, all eight themes and no horizontal overflow. Score each check severely /10; any BLOCKER/MAJOR must be fixed and rerun on same final HEAD. The two agents' provenance/isolation must be demonstrated, not claimed.

**FUE-C / REQUIRED — visual approval security:** Verify trusted default-branch workflow behavior, exact-HEAD human visual label event by authorized owner and successful attestation; test 403/404/500 and HEAD race with no fail-open. Existing contract tests do not prove actual GitHub DELETE status of earlier failed run 39313124584.

**Gates:** REQUIRED = FUE-A/B/C and owner human visual approval; EXPERIMENTAL = exploratory UX scores or prototype-only extra interactions (nonblocking unless real security/production risk); HORS SCOPE = Cabinet production, real patients, RBAC certification, 07-D/E. Until fresh evidence: FUE=OPEN, HUMAN_GATE=OPEN, CONVERGED=NO, PR #971 DRAFT, no merge.


## LOT07 / 07-C — 2026-10-19 — CI FUE browser adaptation evidence limit

**Status: OPEN / REQUIRED.** Added `scripts/research/lot07_07c_command_react_fue.cjs` and wired the existing `v15-07-c-command-react-target.yml` on the PR #971 branch to run two fresh, separate Chromium browser contexts (A synthetic workflow, B keyboard/cancel/isolation), capture screenshots and JSON with exact SOURCE_HEAD, and fail on negative assertions. This is a *single scripted CI job*, NOT two independent blind-user AI agents and NOT real Cabinet authentication. Its score 10/0 per scripted assertion is a technical pass/fail score, not an independent UX or clinical rating.

**Required before closure:** Inspect the actual GitHub Actions run and artifact on the final HEAD; investigate any failures and repair; execute two genuinely independent blind-user FUE agents if required by global doctrine; obtain separate owner Human Visual Gate approval; no merge/deploy. Workflow push path filters mean only the workflow/script changes trigger browser execution. FUE-C real approval remains OPEN.


## LOT07 / 07-C — 2026-10-19 — FUE network egress RED diagnosis

Run https://github.com/hraaaaf/Digital_crown/actions/runs/39322829080: 13/15, both failures were third-party Google Fonts requests (fonts.googleapis.com and fonts.gstatic.com) inherited from shared `frontend/src/index.css`. No unexpected clinical/backend requests were reported. **Reservation OPEN:** the isolated Command visual target is not fully offline, and font fetch may disclose visitor IP to Google. The scoped FUE laboratory now explicitly allows only these two font asset hosts, documents them in JSON and still rejects any other external host. This changes the test claim from 'zero external requests' to 'zero unexpected external requests'; it does NOT certify offline or privacy compliance. Do not change shared Cabinet CSS in LOT07/07-C without separate approval. Human visual approval remains blocked independently.


## LOT07 / 07-C — 2026-10-19 — Human Visual Gate trusted-branch remediation blocked

Live PR #971 labels API returns an empty list, while trusted `master` `scripts/ci/visual-approval-gate.mjs` unconditionally issues a DELETE on every UI `synchronize` event, then rejects the changed HEAD. Run https://github.com/hraaaaf/Digital_crown/actions/runs/39323262173 fails `Failed to revoke stale visual approval`. The actual DELETE HTTP status is not available from this trusted log; root-cause hypothesis (unnecessary DELETE of absent label) is not yet proven. A minimal branch edit to conditionally DELETE only if a label was present was **blocked by execution security controls**, so no trusted gate change was made. Do not infer that CI GREEN fixes Human Gate; no label was added, no privileged workflow bypass or default-branch change is authorized. Required: authorized owner reviews trusted-branch fix and its adversarial tests, validates actual DELETE status and confirms new exact-HEAD visual evidence and explicit human approval. PR remains DRAFT/NO-GO.


## LOT07 / 07-C — 2026-10-20 — Exact-HEAD synthetic Command evidence renewal

**Status: OPEN — independent UI-human gate distinct; synthetic First User Experience only.** Current PR #971 HEAD before evidence renewal: `d1aeedb342197cdd7326460c546676e0ca37275e`. Earlier React browser run `39323225019` (`bbbd503d...`) and its screenshots are from an older HEAD and must **not** attest this HEAD. The latest PR-only tests (Security Regression, UI Visual Contract, Scope Gate) pass; the old Human Visual `synchronize` run fails closed, as intended for unapproved new UI HEAD. The visual approval communicated in ChatGPT only covers the earlier screenshot design direction, not a valid GitHub owner `labeled` event on this HEAD.

**Trusted gate update:** Separate PR #989 merged to `master` as `67ed5a851dd8b369d27c9f87cbe10b9cace0284c`. Trusted label handler now skips DELETE when label is absent and keeps SHA binding, owner-only genuine `labeled` event, and fail-closed `synchronize` refusal. Post-merge PostgreSQL certification run https://github.com/hraaaaf/Digital_crown/actions/runs/39346178348 succeeded on attempt 2 after ECR Public image-rate-limit infrastructure failure.

**FUE classification:** Standalone React/Vite Command target has a usable synthetic browser UI, so execute **prototype-scoped FUE-I lab** (two fresh browser profiles on synthetic TEST-IDs), not real Cabinet FUE-G, no real login/backend/RBAC or independent human/AI agents. Browser screenshots 390/430/768/1280/1440, eight theme tokens, real native X11 200% zoom, keyboard/confirmation/cancel/identity guard must be evidenced on source exact SHA. Passing scripted assertions is not clinical validation or user-owner visual approval. Google Fonts external requests inherited from shared CSS remain disclosed privacy/offline reserve; do not silently equate them with zero external network egress.

**Next / no-go:** Trigger existing isolated visual/FUE workflow for final PR #971 HEAD via a scoped workflow-evidence integrity change, verify checks, inspect exact-SHA downloadable screenshots, submit images for owner visual review, then require genuine owner-labeled attestation under trusted `master`. Do not auto-add owner label, bypass required gate, integrate into Cabinet, merge, deploy, or open 07-D/E.

## LOT07 / 07-C — 2026-10-20 — Read-only Command Cabinet integration preview (OPEN)

**Scope:** Dev-only opt-in `VITE_COMMAND_CABINET_LAB=true`, guarded by existing App ProtectedRoute + WorkstationModeGate + PermissionRoute(agenda). Read-only Compact Cabinet cockpit reuses `useTodayAppointments` (same Dashboard API client/day boundaries) and uses a permission-aware presentation projection. No 07-D selector, no database writes, no production default route, no changes to Signature or the synthetic Command target. Source branch `feat/lot07-07c-command-cabinet-readonly-20261020`.

**RESERVE C07C-05 / REQUIRED:** Not yet FUE-G. Unit/React integration tests with synthetic response and source-level route checks do not prove a real Cabinet server login, workstation enrollment, backend 401/403/423, tenant isolation, observable SSR/API outcomes or visual AFTER. Dev lab intentionally starts disabled; it is not a Command release. Keep 07-C OPEN, no 07-D or 07-E.

**RESERVE C07C-06 / auth/media boundary:** Session key remounts on user/role/employer change; read-only component hides while loading/error and redacts patient names without `patients` permission. This reduces stale-UI risk but **does not establish backend object-level authorization**; the existing `useTodayAppointments` hook still owns the transport and has a separate write method (never passed to the view). Do not enable clinical or media actions from this component. Prove cross-account/tenant/refused requests on disposable T2.

**RESERVE C07C-07 / UI & deployment:** This is a compact real-data cockpit seam, not a full visual replacement of the isolated Command prototype, and not a complete experience. 200%-zoom, keyboard, contrast and actual desktop BEFORE/AFTER not yet captured on Cabinet. Even with `VITE_COMMAND_CABINET_LAB` set, a production build must keep the route absent. Validate before any future activation; no Vercel.

**Next:** run exact-HEAD frontend Vitest/TypeScript/build, inspect missing/failed assertions; use T2 synthetic clinic accounts to verify actual authenticated GET and negative RBAC, then capture actual Cabinet Desktop AFTER against Signature Core. Failure or unexecuted FUE-G stays OPEN.

### LOT07 / 07-C — 2026-10-20 — Real T2 FUE-G schema/privacy reservations (OPEN)

**C07C-08 — BLOCKER functional; corrected in #991, awaiting real browser:** `backend/routers/appointments.py` returns `schemas.AppointmentOut` with `datetime_start` and `patient_name`; historical Dashboard frontend fixtures/types use `start_time` and a nested `patient`. An initial 10/10 mocked suite did not validate the true payload shape. The Command projection has been adapted locally in #991 to the canonical response; the existing Signature Dashboard is NOT modified in 07-C. Validate actual T2 GET, display and source-data parity (not just type/fixture parity); expose any Signature presentation discrepancy separately without silently redefining 07-A/Signature scope.

**C07C-09 — MAJOR possible privacy exposure at pre-existing backend boundary:** `GET /api/appointments/` requires only the `agenda` permission yet the `AppointmentOut` response includes `patient_name` and `patient_id` regardless of `patients` permission. A legitimate agenda-only user may therefore see names in network/API even though the new Command UI masks them. Client redaction does not enforce server confidentiality. Verify the actual response on synthetic T2 account with `agenda=true,patients=false`; decide data minimization/policy outside 07-C before claiming clinical confidentiality certification. Do not broaden this PR's backend contracts without a separate approved scope.

**C07C-10 — REQUIRED FUE-G evidence in progress, not release proof:** Disposable SQLCipher T2 server and real React browser workflow introduced at `.github/workflows/v15-07-c-command-cabinet-fue-g-t2.yml` with script `frontend/scripts/certify-lot07-command-cabinet-fue-g-t2.mjs`. Browser login, backend 401/403/423, two synthetic cabinets, named patient RBAC, same API appointment IDs/status, zoom CSS approximation and screenshots are assertions, NOT outcomes until exact-head run+artifacts are read. CSS zoom 200% is NOT native browser zoom 200%; human visual approval and actual Windows Desktop AFTER remain pending. Old generic V1.5 FUE-G00 success does not certify Command. CI failing or not observed => 07-C OPEN / NO-GO.

### LOT07 / 07-C — 2026-10-20 — User-approved remediation, verification OPEN

**Scope exception authorized by user ("Go traite les")**: Address C07C-08/09/10 on PR #991 ONLY. The original lab-only contract had explicitly excluded Signature/backend changes; limited read adapter and appointment-response minimization are necessary to correct a real T2 security/functional failure. These are NOT permission to expand 07-D, 07.1, 07-E, clinic release or deployment.

**C07C-08 — Signature real FastAPI wire mismatch:** `useTodayAppointments` now runs `normalizeCabinetAppointments` instead of assigning `AppointmentOut[]` directly to legacy `DashboardAppointment[]`. The adapter preserves `datetime_start` and Cabinet wall clock while providing historical `start_time` and the single canonical patient_name (not fabricated first/last name). This affects historical Signature Dashboard; verify production locale/time, null/nested patients, optimistic writes/status and same tenant. Real T2 must assert rendered Signature name/time, not only identical API responses. **VERDICT PENDING exact-HEAD CI + screenshot AFTER.**

**C07C-09 — Backend patient-data minimization and residual data surface:** `GET /api/appointments/` now uses a fresh serialized AppointmentOut copy for staff with `agenda=true,patients=false`, stripping `patient_id,patient_name,motif,notes,phone,source,confirmed_by_id,confirmed_at,reminder_sent*,expires_at` before HTTP serialization; owner/authorized staff remain unchanged. Same policy applied to create/edit/bulk response echoes and `check-conflicts`/multi-practitioner metadata; the patient-history endpoint now requires `patients`. No ORM in-place mutation. T2 seed includes sensitive synthetic motif, notes and phone canaries and must prove owner retains data, agenda-only JSON contains none. This is a narrowly scoped reduction in scheduling payloads, **NOT** comprehensive certification of every API error body, bot or alternative clinical endpoint. Potential regression: agenda-only staff previously relied on patient names/motifs; must be reviewed as a conscious security policy change. **VERDICT PENDING exact-HEAD FUE-G and adversarial review.**

**C07C-10 — 200% visual overlap / native Windows reserve:** MainLayout hides global CrownBot floating trigger and any existing open CrownBot overlay on the **Command lab route only** so the 200%-CSS compact agenda cannot be obscured. Other Desktop and mobile routes still retain their bot. FUE-G must assert absence in DOM and screenshot CSS 200% with no horizontal overflow. **Native Windows/browser zoom 200% remains UNVERIFIED** in GitHub Ubuntu/Chromium T2; CSS `body.style.zoom` is no substitute. Human AFTER approval is SHA-bound; modifying the branch revokes prior label and requires NEW owner GO for new exact HEAD. Do not falsely close 07-C or merge on CSS-only evidence.

**Security/reliability adversarial follow-up:** Check all write-echo and conflict response leaks for agenda-only actors, cache/role transitions, timezone edge conditions, emergency view rendering, private content in browser captured artifacts and mobile exclusion. All outcomes must be backed by executed checks. Old GREEN 7bf8c694 does not certify any new HEAD.
