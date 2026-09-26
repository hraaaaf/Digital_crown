# V1-07 — Master Stabilization Audit

Status: **READY FOR MERGE — EXACT-HEAD CERTIFIED / POST-MERGE PENDING**

Date: 2026-09-19  
Baseline: `master@b891f0a7130a5993cee61f7b8340ba641c532647`

## Goal

Establish one stable pre-candidate master with required global regressions green, coherent migrations/docs, no unresolved mandatory V1 blocker, and no unclassified open PR.

## Success

- open PR invariant remains exactly the four classified parked PRs;
- Alembic has one unique head;
- `CURRENT_ALEMBIC_HEAD` matches it;
- canonical roadmap and objective file agree;
- required master CI/runtime/schema evidence is green;
- no proven mandatory V1 blocker remains;
- no product work is invented merely to create activity.

## Verified starting facts

- V1-06 closeout merged as `b891f0a7130a5993cee61f7b8340ba641c532647`.
- Open PRs: #618, #383, #289, #288 only; all classified as parked/human-gate parked.
- Runtime schema declares `CURRENT_ALEMBIC_HEAD = "ojf20000008"`.
- Latest migration is `ojf20000008_add_ortho_timepoints.py`, down-revision `ojf1b000007`.
- `backend/tests/test_schema_runtime_head_sync.py` asserts unique Alembic head equals runtime head.
- The roadmap references `DIGITALCROWN_V1_OBJECTIVE.md`; the file did not exist before V1-07. This audit creates it rather than deleting the canonical requirement.

## Product-change policy

No runtime/product change is authorized by this audit unless a failing proof exposes a concrete mandatory V1 blocker.

## Required proof

1. exact-head CI on V1-07 docs candidate;
2. T2 runtime certification;
3. Agenda A5 visual evidence as regression guard;
4. PostgreSQL/Alembic schema certification on stabilized master if available/required by workflow;
5. open-PR invariant re-query before closeout;
6. roadmap/objective coherence check.

## Final pre-merge proof

Exact-head certification on `0354bf6828e98ec50ec7afdef95941f621eb335b`:
- GitHub Actions matrix: **28 SUCCESS / 2 SKIPPED / 0 FAILURE / 0 active**.
- Patient P7 Final Certification `36205720352` — **SUCCESS**.
- V1-07 G3 Browser Action Certification `36205720410` — **SUCCESS**.
- V1-07 G1 Browser Action Certification `36205720287` — **SUCCESS**.
- CI `36205720407` — **SUCCESS**.
- T2 Runtime Browser Certification `36205720468` — **SUCCESS**.
- Catalog Connected Truth Certification `36205720217` — **SUCCESS**.
- PostgreSQL Alembic Schema Certification `36205720590` — **SUCCESS**.
- Windows Build Dependency Contract `36205720419` — **SUCCESS**.
- Exact UI proof retained at 390×844 / 768×1024 / 1280×900 with zero horizontal overflow; no new 390 regression versus retained baseline.
- Real cabinet port 8005 was not mutated.

## Next

Merge PR #692 under exact-head guard, certify the resulting master, then mark V1-07 CLOSED and unlock V1-08 candidate freeze.
