# TECHDOUBT — Digital Crown

## GLOBAL-G10-S / LOT10 — 2026-10-18 — blind-user independence not yet demonstrated

**Status: OPEN / verification required (documentation contract, not a confirmed product defect).**

**Question:** Can the FUE harness execute **two specialized AI BLIND USER agents in genuinely isolated contexts and independent browser/login sessions**, withholding both the implementation/change hints and the other agent's findings until each verdict is frozen, on the same exact source HEAD?

**Current evidence:** `AGENTS.md` and `docs/quality/REALITY_PROOF_GATE.md` now specify the protocol. No two-agent isolated run, agent identity provenance, independent report pairs, or full login-to-outcome artifact has been executed in this documentation PR. Sequential prompts by one agent **must not** be relabeled as two independent users. This question does not suggest that humans are required for the two agents.

**Resolution gate:** Implement the harness under GLOBAL-G10-S on a dedicated authorized follow-up, generate two isolated A/B first-user traces (role, specialty, separate profiles/tenants, real UI login, expected/actual before/action/after and exact SHA), independently time-stamp/save reports before unblinding, check cross-isolation and negative RBAC/patient data access, and run two new independent sessions after any product HEAD change. If not achievable, mark `BLIND_USER_GATE=OPEN` and report two internal non-independent perspectives only.

**Separate gates:** Human/practitioner approval where explicitly required, clinical review, and LOT10 physical observations from actual login on real supported hardware remain distinct and may never be satisfied by this synthetic trial.

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
