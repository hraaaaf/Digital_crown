# Digital Crown — V1 installed cabinet baseline

Status: **CANONICAL INSTALLED BASELINE — V1_OPERATIONAL**

Date: **2026-09-29**

## Installed identity

- Source repository: `hraaaaf/Digital_crown`
- Final certified/installed V1 SHA: `bce60b26059054ba43cf8ec13cd210098e648ea4`
- Installed release: `dc-cabinet-bce60b260590-run36628947897`
- Certification level: `INSTALLABLE_CERTIFIED`
- Cabinet Certified Release run: `36628947897`
- Environment: `cabinet`

This SHA/release pair, not a moving branch or current `master`, is the installed V1 software identity.

## Operational proof

Observed on the real cabinet after activation and again through the normal user launcher:

- `/api/health`: HTTP 200, `status=ok`, `database=ok`, version `bce60b260590`
- `/api/health/db`: HTTP 200
- `/api/health/storage`: HTTP 200
- post-restart certified release remained clean with `.pyc = 0`

## Data-preservation baseline

POSTUPDATE proof:

- Alembic: `v7100000020`
- historical document archives: **434 / 434**
- media: **2915 files**, **372138855 bytes**
- table-data SHA256: `d0155d5741348e36ea223600ca4bb5c2b8943b78132ca9d34e1145a24e716fae`
- historical-relations SHA256: `f96cf443afbf63170926529f14811238bd868b839464b567f413b13734e331ec`
- media manifest SHA256: `e817aa9e598e56a8c4aa1f062d8afe32cd9c26ded7f722fa065756ea3e31325c`
- preservation: **PASS**

These fingerprints are evidence for the V0→V1 update event. They are not a requirement that the living cabinet dataset remain byte-identical after normal clinical use.

## Rollback / backup reference

Fresh encrypted pre-activation backup retained:

- DB: `db_backup_20260929_213539.sql.enc`
- DB SHA256: `3ba34ad02539ebd0219a52a19d91100bad27c08d8ae828252861e3eae7198bb2`
- media: `media_backup_20260929_213539.zip.enc`
- media SHA256: `2d0e15eb385409edc7893e756987677e14d951a7e3da4987cf8a81b54bd42f8c`

Rollback rehearsal was proven on an isolated scratch target, not by destructive downgrade on the live cabinet.

## Authority

For V1 history and closeout evidence:

- `STATE.md`
- `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md`
- `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`
- `docs/migrations/V1_10_REAL_CABINET_CLOSEOUT.md`

The previous `DIGITALCROWN_V0_INSTALLED_BASELINE.md` remains historical evidence of the source baseline and must not be treated as the currently installed version.

## Boundary

V1 is **CLOSED / V1_OPERATIONAL**. Future V1.5 development must not silently mutate or replace this cabinet baseline. Any future real-cabinet upgrade requires its own candidate identity, data-preservation gate, backup, authorization and post-update proof.
