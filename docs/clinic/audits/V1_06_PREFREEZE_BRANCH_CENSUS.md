# V1-06 — Pre-freeze Branch Census

Date: 2026-09-19  
Repository: `hraaaaf/Digital_crown`  
Reference master at census start: `455cff05de35166eed62ae58eb1ae9d9014503dd`

## Result

Fresh branch enumeration returned **404 branches**.

The presence of a branch is not release authority. For V1 freeze:
- only `master` and the later intentionally frozen exact 40-character candidate SHA are canonical;
- no non-master branch may enter V1 by branch name alone;
- any future integration from a non-master branch requires a fresh compare against then-current master and an explicitly classified PR;
- no mass branch deletion is performed in V1-06 because deletion is destructive and unnecessary for candidate integrity.

## Active open-PR branches at this census

Explicitly classified in `V1_06_PREFREEZE_PR_INVENTORY.md`:
- `docs/v1-05-closeout-v1-06-unlock` — REQUIRED_FOR_V1 (#623)
- `design/design-system-specimen-v05` — PARKED_POST_V1 (#618)
- `security/sec1-signed-licenses` — PARKED_POST_V1 (#288)
- `security/sec2-device-binding` — PARKED_POST_V1 (#289)
- `portability/p13-physical-certification` — HUMAN_GATE_PARKED (#383)

## Historical / evidence namespaces

The remaining branch set is dominated by explicitly non-canonical namespaces and historical work streams, including:
- `agent/*`
- `archive/*`
- `audit/*`
- `backup/*`
- `cert/*` / `certification/*`
- `ci/*`
- `docs/*`
- `feat/*` / `feature/*`
- `fix/*`
- `marketplace/*`
- `mobile/*`
- `portability/*`
- `research/*`
- `scratch/*`
- `security/*`
- `settings*`
- `staging/*`
- `temp*` / `tmp*`
- `test/*`
- `ux/*`
- `work-* / work/*`
- historical certification roots `S1...` etc.

These refs are retained as evidence/history only. They have no merge authority in V1-06.

## Individually checked ambiguous branch names

### `catalog-connected-truth`
- diverged from current master: 1 unique old commit / master thousands of commits ahead;
- current master contains an evolved `backend/services/catalog_connected_truth.py`;
- historical feature was merged through PR #195 as `5f6187b30906e5f51b6176fa3143702d4b6d62ed`;
- classification: **HISTORICAL_SUPERSEDED — DO NOT MERGE**.

### `p0-2-cmo-non-prescriptive-boundary`
- 3 unique old commits / master thousands of commits ahead;
- current master CMO service already implements a stronger documentary/non-prescriptive boundary, practitioner validation requirement, canonical employer derivation, and deleted-imaging filtering;
- earlier P0-2 implementation was merged through PR #6 as `6def2a2501cd687f5fa9be03741206b77b02643f`; later PR #7 was closed without merge;
- classification: **HISTORICAL_SUPERSEDED — DO NOT MERGE**.

### `diagnostics/p6-localmachine-trust`
- historical diagnostic branch with large unique portability delta;
- PR #290 was closed without merge after the proven Authenticode fix was ported to the production portability branch;
- classification: **DIAGNOSTIC_ARCHIVE — DO NOT MERGE**.

### `cephalo/nextgen-research`
- fully behind current master, 0 unique commits;
- classification: **ANCESTOR/RESEARCH POINTER — NO ACTION**.

### `release/v0-installed-cabinet`
- fully behind current master, 0 unique commits;
- represents historical installed-V0 identity context and is not a V1 candidate;
- classification: **PRESERVE HISTORICAL BASELINE — DO NOT MERGE**.

## Freeze contamination rule

V1-06 does not need to delete historical refs to guarantee candidate integrity. The contamination control is:

1. candidate identity = exact immutable SHA, never branch name;
2. candidate must descend from reconciled `master`;
3. only explicitly REQUIRED_FOR_V1 PRs can modify master during V1-06/V1-07;
4. parked/historical branches cannot be merged without reopening canonical roadmap classification;
5. a fresh open-PR inventory is required again immediately before V1-06 closeout.

## Next

- merge #623 after exact-head checks;
- re-query open PRs;
- prove only explicitly parked PRs remain;
- then close V1-06 and unlock V1-07 Master stabilization.
