# V1.5 — FUE retrospective evidence reconciliation 00→03 (LAB-only)

Date: 2026-10-10
Authority: [canonical FUE sublot plan](https://app.notion.com/p/3f177c66336281c49a48d1361307f458), [unique V1.5 roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb), `master@b4287dc789ee7801c9b8c755414583d741dccc7b`.
Scope: V1.5-00 → V1.5-03 **retrospective first-user experience**. These classifications are NOT implementation statuses. A merged implementation, historical green CI, successful contract test or simulated Chrome alone does **not** prove a complete human or physical FUE.

## Classification

- **PROUVÉ (périmètre ciblé)**: existing exact-head or source-parity traceable, substantial runnable evidence covering the indicated *bounded* FUE and an adversarial review. Do not extrapolate to hardware.
- **PARTIEL**: relevant positive evidence exists but one or more required user steps (real auth, physical camera, complete integrated flow, or exact source attribution) are not covered.
- **À FAIRE**: no sufficient FUE-I/G user journey identified, even if feature is implemented.
- **FUE-0**: review tests/source/contracts, **never invent a browser FUE**.

## Matrix — every canonical 00.1–03.6 sublot

| ID | Canonical gate | Evidenced status (2026-10-10) | Evidence and limits | Next |
|---|---|---|---|---|
| 00.1 Hub IA | FUE-0 | PROUVÉ **code/contract scoped** | [source report](./V1_5_00_1_FUE_RECONCILIATION.md), route/Hub code + [#803](https://github.com/hraaaaf/Digital_crown/pull/803), not an end-user gate | Preserve contract regression |
| 00.2 Hub routes | FUE-I | **PARTIEL** | [report](./V1_5_00_2_FUE_I_HUB_RECONCILIATION.md), [Hub FUE #38010825935](https://github.com/hraaaaf/Digital_crown/actions/runs/38010825935) on PR #819 head: synthetic anonymous denial, Control/Station and recovery; script explicitly says no real authenticated Cabinet session | **NOW: true disposable T2 workstation cookie + actual UI login into Cabinet, with BEFORE/ACTION/AFTER** |
| 00.3 Workstation mode | FUE-I | PROUVÉ **LAB scoped** | [report](./V1_5_00_3_FUE_I_WORKSTATION_RECONCILIATION.md) and [#803](https://github.com/hraaaaf/Digital_crown/pull/803), 35 unit + 138 browser assertions/75 PNG, internal 9.5; real PIN/hardware reboot not certified | Transfer real backend/PIN/reboot only to integrated G01/G00 |
| 00.4 Hub integration | FUE-G 00 | **PARTIEL global**, PROUVÉ UI scoped | [report](./V1_5_00_4_FUE_I_HUB_DISPATCHER_RECONCILIATION.md), 12 browser paths/149 assertions/52 PNG (internal 9.3), [#38010825853](https://github.com/hraaaaf/Digital_crown/actions/runs/38010825853) latest passed; synthetic auth/PIN | End-to-end fresh real auth, app choice and no dead ends |
| 01.1 Topology contract | FUE-0 | PROUVÉ **LAB/code scoped** | [report](./V1_5_01_1_FUE_0_TOPOLOGY_RECONCILIATION.md), canonical resolver and tests, historical gate #37812050447 SUCCESS; internal 9.1 | Physical LAN remains G01, not 01.1 FUE-0 |
| 01.2 Annex setup | FUE-I | PROUVÉ **LAB scoped** | [PR #803](https://github.com/hraaaaf/Digital_crown/pull/803), [run #37841695892](https://github.com/hraaaaf/Digital_crown/actions/runs/37841695892) scoped 8.2/10, simulated workstation; real PC/LAN absent | Physical installer/user gate 01.4 |
| 01.3 Network diagnostic | FUE-I error | PROUVÉ **LAB scoped** | [PR #803](https://github.com/hraaaaf/Digital_crown/pull/803), [run #37852926051](https://github.com/hraaaaf/Digital_crown/actions/runs/37852926051), scoped 8.3; synthetic LAN errors only | Physical wrong-LAN/recovery 01.4 |
| 01.4 Multi-PC runbook | FUE-G 01 | **PARTIEL overall**: PROUVÉ cloud lab, real field À FAIRE | [PR #817](https://github.com/hraaaaf/Digital_crown/pull/817) targeted TLS SAN fail-closed [Cloud-Lab #38008001415](https://github.com/hraaaaf/Digital_crown/actions/runs/38008001415), 13 API states/4 browsers and internal 9.0; runbook physical [#816](https://github.com/hraaaaf/Digital_crown/pull/816) draft | 1 actual server + 2 physical clients, real LAN/trust/reboot; **not executable under LAB ONLY** |
| 02.1 Photo backend contract | FUE-0 | PROUVÉ **code/LAB scoped** | [#815](https://github.com/hraaaaf/Digital_crown/pull/815), tenant photo negative API and lifecycle tests, first-login lab | Continue tenant isolation regressions; physical camera not this gate |
| 02.2 Webcam/import/crop | FUE-I | **PARTIEL** | [Photo lifecycle run #38004636980](https://github.com/hraaaaf/Digital_crown/actions/runs/38004636980) & [#815](https://github.com/hraaaaf/Digital_crown/pull/815) synthetic/browser; **real webcam capture not performed** | Real camera when available; continue synthetic file-import/crop audit now |
| 02.3 Same photo across UI | FUE-I transverse | PROUVÉ **LAB scoped**, physical not certified | [#812](https://github.com/hraaaaf/Digital_crown/pull/812) UX repair merged, photo propagation [#815](https://github.com/hraaaaf/Digital_crown/pull/815), captures 5 surfaces × viewport and multiple states; provenance tracked in roadmap | Device/human visual review for completeness; no false hardware gate |
| 02.4 Add/replace/delete/fallback | FUE-G 02 | **PARTIEL global**, PROUVÉ targeted LAB | [Photo #38004636980](https://github.com/hraaaaf/Digital_crown/actions/runs/38004636980) + [#815](https://github.com/hraaaaf/Digital_crown/pull/815), 8 backend/36 frontend cases, synthetic/real UI login/tenant guards; **physical webcam and complete real user FUE missing** | Real hardware/human consent; until then retain LAB scoped |
| 03.1 Station shell | FUE-I patient | PROUVÉ **LAB scoped** | [#819](https://github.com/hraaaaf/Digital_crown/pull/819) merged, [Visual #38010825773](https://github.com/hraaaaf/Digital_crown/actions/runs/38010825773) 24 PNG 4 widths × text 200% × FR/AR/EN, screenshot inspection (previous hidden major fixed), two internal reviews 9.1/9.3, postmerge #38012110311 green | Real public touch flow & human session later |
| 03.2 Station pairing | FUE-I installer | **PARTIEL** | Existing backend workstation/pairing contracts and [03.6 security #38010825842](https://github.com/hraaaaf/Digital_crown/actions/runs/38010825842); no verified full first-time installer paired→revoked→reconnected on real device | Lab exact-head browser pairing lifecycle first |
| 03.3 QR/NFC identity | FUE-I patient | **PARTIEL** | [03.3 visual #38010825883](https://github.com/hraaaaf/Digital_crown/actions/runs/38010825883) SUCCESS on #819 head, simulated QR and backend tests; real NFC/device claim not proven | Isolated E2E real API QR claim/expiry/purge; physical NFC later |
| 03.4 Appointment arrival | FUE-I patient | **PARTIEL** | Unit/backend station arrival + [03.6 #38010825842](https://github.com/hraaaaf/Digital_crown/actions/runs/38010825842) offline rejected; not full 0/1/N arrival real staff handoff | End-to-end T2 synthetic real backend per appointment state |
| 03.5 Wall and staff call | FUE-I staff + public | **PARTIEL** | `StationWallDisplay` + staff components/tests exist on master; no audited browser E2E staff calls→bounded wall display evidence in this matrix | Scoped browser integration with negative privacy asserts |
| 03.6 Station security/UX | FUE-G 03 | **PARTIEL global**, PROUVÉ targeted LAB | [Security/offline #38010825842](https://github.com/hraaaaf/Digital_crown/actions/runs/38010825842) all three jobs success; 4 viewports × 200% and before/after, 37 security tests; mock identity/arrival not integrated complete visitor→purge→next visitor | Full isolated backend patient A→timeout→patient B, no leakage, reconnect/replay |

## Immediate execution order

1. **00.2**: authorize a *real* UI login in a disposable T2 environment, with workstation identity server-enrolled by public API, not fabricated mock/token in localStorage. Fail closed on anonymously accessible dashboard, missing workstation cookie, no UI login or missing route return. 768/1280 viewport captures. This is a **sub-scope**: it does not certify first physical enrollment nor a real cabinet.
2. Reconcile **00.4 FUE-G00** using 00.2 real positive + previous synthetic negative Hub/Station/Control, then determine remaining authentic real PIN/reboot cases without overclaim.
3. 01.4 physical, 02.2 physical and full G02: remain OPEN pending owner-controlled real devices; **do not simulate physical proof**.
4. Continue lab-only Station 03.2→03.6 integrated gaps in canonical order.

## Gate discipline

- No FUE user test for FUE-0-only 00.1/01.1/02.1.
- Claims must name source SHA, run, jobs, artifact, screenshots and gaps. GitHub green ≠ UX PASS; source parity ≠ new run.
- Two *internal* adversarial perspectives A UX/a11y and B security/false-proof, and same-HEAD confirmation after substantial changes; no claim of external independent reviewer.
- REQUIRED targeted CI gates block scope closeout when red; M6-I EXPERIMENTAL and physical/HORS SCOPE do not automatically block a LAB-only scope.
- **No master merge, Vercel, release, real device or V1.5-04** in this draft. Explicit separate owner authorization to merge.
