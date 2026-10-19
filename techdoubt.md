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
