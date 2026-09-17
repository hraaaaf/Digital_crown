# CÉPHALO-N — CANONICAL RESUME / ROADMAP ENTRY

Last verified: 2026-09-17.

## RESUME RULE

This is the stable canonical entry point for the Céphalo-N workstream.

Before any conclusion or write, verify live GitHub state: `master` HEAD, open/merged Céphalo PRs, exact-head CI/T2/PostgreSQL certification and any newer commits on `master`.

Historical runs never override current GitHub state.

No Vercel deployment is authorized by this file.

## GOAL

Deliver a Céphalo-N workflow that is scientifically constrained, deterministic, auditable and visually usable, while preserving the invariant:

`measurement != diagnosis != indication != treatment`

R20 specifically closes the Workbench UX redesign without changing or inventing scientific semantics.

## SUCCESS

R20 is declared `CEPHALO_N_CLOSEOUT_VERIFIED` only when all of the following are true on the final integrated state:

1. Product/UI implementation is merged and visual evidence remains valid.
2. Scientific/calculation architecture and fail-closed contracts are preserved.
3. Repository-wide backend regression completes green on an exact final SHA.
4. PostgreSQL certification is green on the relevant integrated SHA.
5. No corrective PR reintroduces removed legacy runtime behavior or accidental unrelated deletions.
6. Canonical documentation is coherent with the real merge/run chronology.

## LOCKED PRODUCT / UI PROOF

R20 product candidate: `2cfc3ba66b8c0dc9a99e89a8da51ed53247a12e3`.

Original R20 PR: `#540`.
Original R20 merge SHA: `7821819b237aebdc7e3de1d2646510434251d2eb`.

Human product-owner visual validation: PASS on 2026-09-16.

Exact-head product certification on `2cfc3ba...` was green, including CI, R19/R1/R15/R15bis visual workflows, T2 and PR Merge Summary. R19 evidence covered 390x844, 768x1024 and 1280x900 with no page/console errors, no horizontal overflow and no blocked external requests.

## SCIENTIFIC LOCKS

- Single canonical measure registry: `backend/services/cephalo_measure_registry.py`.
- Normative registry remains separate.
- Unknown canonical unit fails closed.
- `M_OVERBITE_V1` has no locked unit and remains `None` until evidenced.
- Lateral and PA/frontal are distinct acquisition/analysis domains.
- New measurements require source, landmarks, construction, unit, calibration contract, canonical ID, centralized calculation and deterministic positive/negative tests.
- Missing scientific evidence means BLOCKED, not inferred.

## POST-MERGE REGRESSION CHAIN

The R20 post-merge full backend suite initially could not finish because default-branch CI used `cancel-in-progress: true`.

PR `#554` fixed orchestration so default-branch regressions survive newer pushes. Its post-merge backend suite then exposed genuine stale tests rather than being cancelled.

Successive repository-wide stale-test fixes:

- `#558` — removed a stale expectation around deprecated FCM registration without restoring `/api/mobile/register-device`.
- `#562` — moved the mobile license regression to the canonical `POST /api/appointments/` mutation path.
- `#564` — aligned a second removed-FCM test with deliberate 404 behavior.
- `#566` — aligned the NGAP migration test with the current Alembic-head contract while preserving the NGAP revision-chain invariant.

## FINAL VERIFIED STATE

Repository: `hraaaaf/Digital_crown`.

PR `#566` is MERGED.

PR `#566` head: `7f79c16b0c8e8066ea55c0ede178b1b0a83d5dbd`.
Merge SHA: `24844a5d19a6bd575d175b331a1bba68bc3c0b0f`.

Final proof on merge SHA `24844a5d...`:

- Cabinet Upgrade PostgreSQL Certification run `35203491675` / #943: SUCCESS.
- Manual CI run `35204697524` / #4760: SUCCESS.
- `Full backend regression (post-merge)` job `105147523280`: SUCCESS.
- `Frontend (tests & build)` job `105147523277`: SUCCESS.
- `Garde production (négatif)` job `105147523081`: SUCCESS.

Current `master` at final reconciliation: `ec6bf4f40137f6e7d395effd97e0be3b0f6a2362`.

Verified delta `24844a5d... -> ec6bf4f...`: only Agenda closeout documentation changed (`docs/audits/AGENDA_CLINIC_A3_CLOSEOUT.md` and `docs/audits/AGENDA_CLINIC_CANONICAL.md`). No application/runtime change exists in that delta.

## CLOSEOUT

Status: `CEPHALO_N_CLOSEOUT_VERIFIED`.

R20 product/UI, scientific invariants, repository-wide backend regression and PostgreSQL certification are all evidenced. The corrective regression chain did not require restoring deprecated FCM/mobile runtime behavior.

## NEXT EXACT

Merge this documentation-only canonicalization lot after its PR diff/CI are coherent, then perform one post-merge documentation verification on `master`.

After that, unpark the next Ortho/Céphalo lot from this canonical baseline. Do not reopen R20 unless a new regression is evidenced.

## REMAINING SEQUENCE

`docs PR -> docs CI/diff coherence -> merge -> post-merge canonical verification -> next Ortho/Céphalo lot`

## SOURCE / HISTORY

Detailed R20 chronology is preserved in `docs/audits/CEPHALO_N_R20_CLOSEOUT_HANDOVER.md`.

The active Céphalo-N roadmap is `docs/CEPHALO_N_ROADMAP.md`.
The global scientific constraints remain governed by `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md`.
The historical product trajectory remains governed by `docs/ROADMAP_DIGITAL_CROWN_V2.md` and is intentionally left read-only.
