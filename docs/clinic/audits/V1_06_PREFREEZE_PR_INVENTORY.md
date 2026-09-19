# V1-06 — Pre-freeze Open PR Inventory

Date: 2026-09-19  
Repository: `hraaaaf/Digital_crown`  
Audit base: `master@455cff05de35166eed62ae58eb1ae9d9014503dd`

## Goal

Classify every open pull request against the canonical V1 path before candidate freeze. No stale or unrelated PR may be silently merged into V1.

## Classification rules

- **REQUIRED_FOR_V1** — must be reconciled/merged/closed before V1-06 can close.
- **SUPERSEDED_CLOSEABLE** — replaced by a later certified implementation or evidence; preserve any unique evidence first, then close without merge.
- **PARKED_POST_V1** — explicitly outside the mandatory V1 path; remains isolated and must not be merged into V1 without a future canonical roadmap decision.
- **HUMAN_GATE_PARKED** — cannot advance without a non-substitutable human/physical/production gate and is outside the current mandatory path.

## Fresh open PR inventory

| PR | Title | Classification | Evidence / action |
|---|---|---|---|
| #623 | docs(v1): close V1-05 and unlock V1-06 | **REQUIRED_FOR_V1** | Docs-only canonical roadmap reconciliation. Merge after exact-head checks. |
| #593 | docs(v1-05): F0 Ortho Journey current-master gap matrix | **SUPERSEDED_CLOSEABLE** | Branch has 3 unique commits / 2 unique docs and is 154 commits behind current master. Extract `V1_05_F0_ORTHO_JOURNEY_GAP_MATRIX.md` + `V1_05_F1A_ORTHO_CASE_IMPLEMENTATION_CONTRACT.md` onto current docs branch, then close without merge. |
| #607 | docs(v1-05): F1B structured orthodontic control contract | **SUPERSEDED_CLOSEABLE** | One unique docs commit, 121 commits behind current master; F1B product #598 is already merged/certified. Extract `V1_05_F1B_CONTROL_CONTRACT.md`, then close without merge. |
| #575 | feat(agenda): A4 physical resources and collision foundation | **SUPERSEDED_CLOSEABLE** | 11 unique commits, 323 commits behind current master. Canonical roadmap records #575 as stale extraction evidence and V1-01 rebuilt cleanly as PR #588. Do not merge old code. Close without merge. |
| #618 | docs(ui): isolated Design System specimen v0.5 | **PARKED_POST_V1** | Isolated specimen only; no route/product integration; not part of mandatory V1-06→V1-10 path. Keep draft/isolated. |
| #288 | SEC-1 signed licenses / OWNER entitlement / platform RBAC | **PARKED_POST_V1** | Canonical roadmap explicitly excludes security/physical historical programs #288/#289/#383 from mandatory V1 path unless a proven blocker requires a bounded delta. Also carries unresolved external production-control-plane requirements. Do not merge into V1. |
| #289 | SEC-2 cryptographic device binding | **PARKED_POST_V1** | Depends on SEC-1 and is explicitly outside mandatory V1 path. Do not merge into V1. |
| #383 | Portability P13 physical cabinet certification | **HUMAN_GATE_PARKED** | Real Windows/macOS/off-machine-storage execution is non-substitutable; roadmap keeps #383 outside mandatory path unless a proven V1 blocker requires it. Do not merge into V1. |

## Evidence extraction

The unique V1-05 documentation from #593/#607 is preserved on the current docs branch before closing those stale PRs:
- `docs/clinic/audits/V1_05_F0_ORTHO_JOURNEY_GAP_MATRIX.md`
- `docs/clinic/audits/V1_05_F1A_ORTHO_CASE_IMPLEMENTATION_CONTRACT.md`
- `docs/clinic/audits/V1_05_F1B_CONTROL_CONTRACT.md`

These are historical design/audit records. Their original gate language is not current runtime status.

## Expected open PR set after safe cleanup

After #623 is merged and #593/#607/#575 are closed without merge, the only intentionally open PRs should be:
- #618 — PARKED_POST_V1
- #288 — PARKED_POST_V1
- #289 — PARKED_POST_V1
- #383 — HUMAN_GATE_PARKED

Any additional open PR appearing after this snapshot must be separately classified before V1-06 closes.

## Next

1. merge #623 after checks;
2. close #593/#607/#575 without merge;
3. re-query open PRs and prove only explicitly parked items remain;
4. inventory non-PR branches that could contaminate freeze;
5. close V1-06 only after branch/PR reconciliation is documented and current master is coherent.


## Cleanup actions executed

Closed without merge after evidence extraction / supersession proof:
- #593 — CLOSED / merged=false.
- #607 — CLOSED / merged=false.
- #575 — CLOSED / merged=false.

Their branch refs may remain as historical Git refs; they are not canonical and must not be merged by branch name.
