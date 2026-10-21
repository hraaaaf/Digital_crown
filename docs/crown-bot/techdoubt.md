# Digital Crown — Crown Bot #894 integration reservations

## CB894-MASTER-20261021-01 — Historical merge conflicts (RESOLVED ON ISOLATED CANDIDATE; NOT MERGED)

- Base `master`: `b6eafd2cec5516a64c5d8013ffd3b3f54430000f`. Upstream [PR #894](https://github.com/hraaaaf/Digital_crown/pull/894) exact source `9cf19e68026fa92d31fb704f5b81b9cd667e5254` remained DRAFT/mergeable=false on its old branch.
- Original 2 conflicted files / 3 hunks: `backend/routers/appointments.py` (CREATE/UPDATE atomic AuditLog plus permission-scoped `_agenda_visible_appointment`) and `backend/routers/frontdesk.py` (single in-transaction `_frontdesk_audit` plus redacted `_visible_frontdesk_fields`). Never choose unredacted source returns or separate the audit from its appointment commit.
- The reviewed clinical code, including guards for cabinet isolation, overlaps, session races, and booking locks, was actually executed in the merged sandbox product candidate `9c30c1391190a570ed1ef6c3f030be10634a0bef`. [Assemble run #39691104809](https://github.com/hraaaaf/Digital_crown/actions/runs/39691104809): 48 targeted API/Pocket/Agenda PASS, read-only byte equality of product tree; [specialist run #39691104849](https://github.com/hraaaaf/Digital_crown/actions/runs/39691104849): 5/5 jobs PASS incl PG two sessions, SQLCipher, migrated PG/SQLCipher real clinical HTTP; [scope #39691104808](https://github.com/hraaaaf/Digital_crown/actions/runs/39691104808): SUCCESS.
- Promotion to master is **OPEN**: original upstream #894 and dependent #902/#903 are still separately DRAFT. Prepare a clean DRAFT product PR (not diagnostic PR #1005), verify CI on its own final HEAD and any applicable human/visual/release gates. No permission to merge, deploy Vercel, activate flags, or install at a cabinet. Prior historical RED [run #39689032580](https://github.com/hraaaaf/Digital_crown/actions/runs/39689032580) was the one-shot candidate republish lease; the underlying 48 tests passed and [run #39691104809](https://github.com/hraaaaf/Digital_crown/actions/runs/39691104809) resolved CI idempotence without changing product code.

## CB894-MASTER-20261021-02 — Practitioner required on Pocket Frontdesk (SAFETY GUARD RETAINED)

- Earlier [Mobile Pocket runtime run #39673525369](https://github.com/hraaaaf/Digital_crown/actions/runs/39673525369) failed because an old test expected HTTP 200 for confirmation of a pending appointment with no `praticien_id`; safe backend rejected HTTP 422. Do **not** weaken this guard.
- Merged candidate test explicitly requires HTTP 422 and unchanged appointment/confirmed_by before practitioner assignment; an authorized same-cabinet dentist must then be assigned for valid HTTP 200 confirmation. The targeted run and specialist suite above passed. User-interface assignment ergonomics and physical cabinet validation have **not** been certified here.

## CB894-MASTER-20261021-03 — Release and dependency boundary (OPEN)

- This commit is for #894 integration only. #902→#903/CB-01 are downstream and remain out of this PR; CB-02 remains frozen; Lot 10 physical/cabinet tests are separate.
- The Vercel configuration in both master and the reviewed candidate contains `git.deploymentEnabled=false`, and the Vercel connector exposed no linked Digital_crown project; this is not authorization to deploy. If any unexpected preview/deployment occurs, STOP and re-evaluate.
- The clean merge tree must be proven byte-equivalent to reviewed candidate code excluding diagnostic-only files, with any new SHA CI still checked independently. **NO-GO master merge** until an explicit separate user GO and all applicable REQUIRED gates.
