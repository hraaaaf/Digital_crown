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
