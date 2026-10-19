# TECHDOUBT — Digital Crown

## GLOBAL-G10-S / LOT10 — 2026-10-18 — Two-agent isolation requirement withdrawn

**Status: RESOLVED AS A FALSE DEPENDENCY (doctrine correction, not proof of a completed FUE).**

**Previous concern:** The merged PR #960 required two AI BLIND USER agents running in independent contexts, with separate browsers and withheld reports. That had been documented as a blocking precondition even for ordinary internal adversarial review. The product owner clarified that the **same ChatGPT conversation should perform both specialized perspectives A/B itself** rather than waiting for humans or two separate AI agents.

**Resolution rule:** `AGENTS.md`, `.claude/rules/execution-scoring-verification.md` and `docs/quality/REALITY_PROOF_GATE.md` now instruct the assistant to write two distinct, task-specific *internal adversarial* reviews, correct/test, rerun on new HEAD and confirm. This is not evidence of two genuinely independent reviewers; it is sufficient for the **internal A/B double-review procedure**. Self-review is capped at 9.4/10 and normal VERIFIED starts at 9.0/10 when required proofs/gates pass. No external reviewer or two-agent orchestration is a prerequisite.

**Distinct unclosed verification work — GLOBAL-G10-S:** Inventory V1+V1.5 routes/features, execute actual frontend/backend FUE journeys on fictitious tenants starting at login (or a public entry where applicable), preserve BEFORE/ACTION/AFTER, negative RBAC/tenant checks, exact-HEAD evidence and CI statuses. **These tests have NOT been executed by this documentation correction.** An imagined browser session or two written perspectives are not executable test proof.

**Unchanged gates:** Specifically required human clinical/regulatory/visual approvals and LOT10 hardware/person-on-device observations remain separate from conversation-based A/B review. No deployment, merge or clinical activation is authorized by this documentation.

**Historical origin:** PR #960, master merge `3cbd1d83cdbcbf97e71019a3182f4699d9645421`. This file supersedes the inaccurate "two-agent independence not yet demonstrated" as an *internal review blocker*.


## CEPH-FAC / FACAD-REA-P0 — 2026-10-19 — Static interoperability experiment

**OPEN / EXPERIMENTAL / NO CLINICAL GO.** User approved an isolated, read-only REA pilot against the official public FACAD 3.14.1.1111 payload, not authorization to accept new EULAs, operate the GUI under an expired trial, evade protection, upload/distribute vendor binaries, copy vendor code into Digital Crown, or modify clinical calculations. The previous FACAD install occurred on a disposable GitHub Actions runner; it is not a persistent installation.

**Risk and missing proof:** REA 6.7.0 may reject or only partially inspect mixed/native assemblies; exact module identity and function/classification evidence are unknown until a real command executes on the GitHub runner. Native Ghidra analysis and full GUI export of Analysis Values, Analysis Properties and Marker Positions remain OUT OF SCOPE for P0. A green static triage cannot certify numeric parity, Ricketts 32F/13F calculations, or licensing permission for additional runtime use.

**Test/proof obligation:** exact HEAD and CI run; official download and extract verified, SHA-256 per inspected binary, REA CLI run and JSON validity; fail closed on missing official export plugin or REA failure. Do not upload raw installer, proprietary decompilation or patient data to artifacts. Next: inspect results, then separately authorize only minimal runtime/export experiment under appropriate vendor terms and official bundled Robert case.
