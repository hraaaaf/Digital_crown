# CB-01 — GitHub Actions as the technical T2 evidence runner

**Status:** automated synthetic-lab protocol. **Not** human usability certification, a physical Windows workstation proof, production deployment or approval to activate Crown Bot.

## Why this exists

CB-01 technical certification must **not depend on a connected Desktop Commander computer**. GitHub-hosted Ubuntu and Windows workers already boot a disposable T2 lab and exercise the real web application plus FastAPI. The existing PR workflows are extended to run **again on pushes to master**, on the same guarded file paths, so the merge commit gets its own reproducible proof.

This replaces the *technical-runner dependency*, not the separately scoped staff/physical gate: no unattended GitHub runner can prove a real receptionist completed a human workflow in a cabinet.

## Run it in GitHub Actions

1. **Sidecar + S01–S12:** [CB-01 Associate Sidecar Visual (EXPERIMENTAL)](https://github.com/hraaaaf/Digital_crown/actions/workflows/cb01-associate-sidecar-visual.yml). Automatically starts on a PR touching guarded files and on relevant `master` pushes; manual **Run workflow** available. Read the actual SHA of each run and its job/artifact, not a previous run's result.
2. **Windows real NVDA + native 200% zoom:** [CB-01 Windows FUE-G MainLayout FastAPI NVDA Zoom (EXPERIMENTAL)](https://github.com/hraaaaf/Digital_crown/actions/workflows/cb01-windows-fueg-mainlayout.yml), same triggers. The Windows runner is hosted and its identities/database are synthetic only.
3. Before interpreting a result, verify **checkout SHA equals event SHA**, GitHub-hosted runner, `DIGITALCROWN_ISOLATED_RUNTIME=1`, disposable localhost backend and test DB. No clinic tokens/secrets or real patient data may enter the runner. `VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED=true` and `VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED=true` exist **only inside isolated CI job env**; do not set them on production, Vercel or a real cabinet.
4. **Artifacts:** Sidecar emits `cb01-synthetic-associate-sidecar-evidence` including screenshots at web 390/430, dock 1280/1440, sidecar 1600/1920, `s01-s12-synthetic-matrix.json`, cross-gate evidence, and HTTP p50/p95; Windows emits `cb01-windows-fueg-real-fastapi-nvda-zoom` with real NVDA speech/native zoom/clinical state report. Verify their embedded source SHA, browser outcomes, rights denials and immutable state. A green job without the required artifact/attestation is not sufficient.
5. **Fail closed:** 401/403/404/409/423, wrong tenant, wrong patient, CSRF/workstation identity, replay/ABA, non-read-only mutation, unread alert ACK errors, or clinical UI covered by bot => STOP and correct on an isolated branch. Do not relax negative assertions.
6. **Postmerge:** the source merge `c70ef93a51bf92a30b2b3b68c394757747145f08` was previously proven tree-identical to reviewed candidate `6177f38c61d03f86eae0ec0bad8e2611ae458f4b`, with [Cabinet Upgrade PostgreSQL push run #39830692217](https://github.com/hraaaaf/Digital_crown/actions/runs/39830692217) SUCCESS. **These facts do not replace new Actions results when this workflow changes.**

## S01–S12 evidence truth (no automatic "12/12 full E2E")

The existing `frontend/scripts/certify-cb01-s01-s12-matrix.mjs` asserts and records:

| Scenario | GitHub synthetic proof | Human cabinet proof |
| --- | --- | --- |
| S01 agenda tomorrow | Actual Chromium Agenda navigation + authorized date-specific GET | NOT_RUN |
| S02 homonyms | Protected preview disambiguation | NOT_RUN |
| S03 ID/dossier | Authenticated fictitious patient read | NOT_RUN |
| S04 name lookup | Bounded surname disambiguation | NOT_RUN |
| S05 reception RDV | `proposal_only`; zero execution | NOT_RUN |
| S06 no-Agenda reception | 403, no identity leakage | NOT_RUN |
| S07 adjacent bookings | Isolated PostgreSQL/FastAPI/SQLCipher technical tests, **not full staff journey** | NOT_RUN |
| S08 estimate | `OPEN_DEVIS_EDITOR` draft-only, not an invoice or medical action | NOT_RUN |
| S09 stale ABA | Isolated concurrency/HTTP technical tests, **not staff UI** | NOT_RUN |
| S10 409 conflict | React simulated 409 recovery, **not live human conflict** | NOT_RUN |
| S11 cross-tenant patient | Same 404 shape for foreign/unknown IDs | NOT_RUN |
| S12 GhostBrain read ACK | Backend/UI simulated ACK/refusal, **not staff usability** | NOT_RUN |

**Matrix claim:** 7 scoped HTTP PASS + 1 Agenda browser PASS, 4 scenarios NOT_RUN in the scoped journey; supplemental tests for S07/S09/S10/S12 have their own evidence and limitations. **0/12 human tests** remains true. Treat S05 as proposal-only and do not promise real RDV confirmation in CB-01. CB-02 and Pocket are separate lots.

## Exit criteria

- Exact-SHA **Linux Sidecar/S01–S12** and **Windows FUE-G/NVDA/200%** completed SUCCESS; inspected artifacts source-bound, no privacy/clinical regressions, negative tests retained.
- Evidence ledger separates **automated technical PASS**, **partial**, **NOT_RUN**, **N/A**, and **human/physical OPEN**.
- A genuine clinic release or feature-flag activation requires a **separate explicit GO** and physical/staff proof (RPG-P) under its own scope. GitHub Actions green can close the technical CI gate, **not** the real-cabinet usability or release gate.

**Operational rule:** No Desktop Commander is needed to execute or view these GitHub Actions proofs. If a later physical pilot is commissioned, choose any separately authorized test device; don't block the software-only CI stage on the old remote workstation.
