# V1.5 LOT08.1 — Queue Core contract closeout (2026-11-08)

Status: **CLOSED / POST-MERGE VERIFIED FOR CONTRACT-ONLY SCOPE**. No production or runtime certification.

## GOAL / SUCCESS / PROOF

**GOAL:** standalone Queue Core domain G1 with versioned event plans, isolated SQLAlchemy metadata and synthetic FUE-0; no clinical DB access.

**SUCCESS:** approved transitions and oracle 09:05/09:10, human-only NO_SHOW, distinct UNLOCATED_AFTER_CALL, explicit audited override, tenant/resource isolation, persisted active chair owner and resource audit, check-in provenance, constrained event/visit data checks, negative SQL tests. No API/auth/QR/engine/installer introduced.

**PROOF:**
- GitHub [PR #1234](https://github.com/hraaaaf/Digital_crown/pull/1234) **MERGED**. Final reviewed contributor SHA: `1df36d79a694f713cb19b112ae26831501cf1678`.
- Squash merge on `master`: `a5c47f5efcc7b9843a9fea13799bae073ca541e7` (parent `16f531f04eb7daff3bf5d75017717e12927f47ab`).
- Postmerge independent detached Windows worktree on exact merge SHA: `python -m pytest -q queue_core/tests` **29 PASSED** in 1.23 seconds, Python 3.12, exit 0; `python -m compileall -q queue_core` exit 0; clean git status.
- Final separate Codex CLI read-only source review of final contributor SHA against `origin/master`: **no definite, actionable defects identified**. Independent agent is not a human review. Its default Python 3.14 environment did not have pytest; only the independently executed Windows Python 3.12 run supports the PASS claim.
- Previous independent Codex review sessions found P1/P2 issues that were corrected and retested (NO_SHOW actor, CI artifact provenance, chair occupancy, persisted check-in method/resource audit, event enums, arrival and queue-sequence SQL invariants). See `techdoubt.md`, GitHub PR discussion and Notion.
- The prior green GitHub FUE-0 Actions tested older SHAs; intentionally **not** used for validation of the final head per owner's direct-Windows testing request. The squash merge includes `[skip ci]`.

**Perfection Pass:** read-only independent final-head review reported zero definite actionable defects, followed by 29/29 synthetic FUE-0 replay on the exact merged SHA; no scope regressions or clinical table changes found.

## Scope and gates

G1–G5 owner-validated at contract level; **FUE-0 applicable and satisfied** for domain/schema-only sublot. FUE-I/G, physical Windows kiosk/wall, patient safety certification, durable persistence, append-only enforcement and compliance/regulatory review **not applicable to delivery 08.1** and remain required when their sublots execute. Independent reviewer was a separate Codex CLI session, **not a human medical approver**. Owner gave GO **Green** for merge after counter-review.

Conservative closeout ratings (specific to contract-only scope): **EXECUTION 9.0/10; FUE_EVIDENCE 9.0/10; RETAINED 9.0/10 (minimum)**. No blanket app score or runtime claim.

## Mandatory boundary for future LOT08.3

`call_visit` is a pure function that accepts candidates; it **cannot independently prove completeness or freshness** of that list. The standalone server MUST load the full authorized tenant/queue/resource candidate set from its own DB, enforce RBAC, lock/serialize calls and resources, and commit state/version, event ledger, claim/release and idempotency atomically. Never trust a client-supplied candidate subset.

## No-release / next

- No patient/clinical database mutation, real patient data, clinical integration, migration, deploy or Vercel.
- 08.2–08.6 **not started** under this 08.1 GO. G7 release gate still later.
- **NEXT EXACT:** owner decision to begin 08.2 separately; preflight updated master, Windows workstation, G2 RBAC/QR/identity. Separate authorization for any deployment or migration.
- Canonical record: [Notion LOT08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86).
