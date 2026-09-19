# Digital Crown — V1 Objective

Status: **CANONICAL / V1-08 FREEZE IN PROGRESS / NOT YET SELECTED**

## Goal

Produce one exact immutable V1 candidate SHA from the reconciled and stabilized master, certify installability against an isolated restore of the real cabinet PREUPDATE state, and install that exact SHA only after explicit human authorization.

## Current state

- canonical roadmap: `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`
- current lot: **V1-08 — Freeze exact V1 candidate**
- stabilized master before V1-07 closeout: `ceae1624c5f1311eb7ffcf512785b8a30fe438fc`
- V1 candidate SHA: **NOT SELECTED**
- installability status: **NOT CERTIFIED**
- V1 operational status: **NOT OPERATIONAL**

## Candidate identity rule

The V1 candidate is an exact 40-character Git commit SHA.

Moving branch names such as `master` are not release identity.

Once V1-08 freezes a candidate:
- any product/code/config/document change that is part of release identity creates a new candidate SHA;
- candidate certification must run against that exact SHA;
- cabinet installation must use the exact certified SHA.

## Success

V1 succeeds only when:
1. V1-07 master stabilization closes with required regressions green;
2. V1-08 selects and records one exact candidate SHA;
3. V1-09 certifies that exact candidate on an isolated PREUPDATE cabinet restore;
4. backups/rollback identity are proven;
5. explicit human authorization is obtained immediately before real cabinet mutation;
6. V1-10 installs the same exact candidate and post-update integrity/health/smokes pass;
7. the canonical roadmap explicitly records `V1_OPERATIONAL`.

## Safety / authority

Until V1-10 explicit authorization:
- no real cabinet mutation;
- no Vercel deployment;
- no branch-name install;
- no candidate substitution;
- no claim of `INSTALLABLE_CERTIFIED` without exact proof.

## Current open-PR boundary

At creation, only these intentionally parked PRs remain open:
- #618 — PARKED_POST_V1
- #383 — HUMAN_GATE_PARKED
- #289 — PARKED_POST_V1
- #288 — PARKED_POST_V1

They are not part of the mandatory V1 candidate unless the canonical roadmap is explicitly revised.

## Next exact

Merge the V1-07 closeout, then freeze that resulting exact master SHA as the sole V1 candidate identity. Record the same 40-character SHA here and in the canonical roadmap.
