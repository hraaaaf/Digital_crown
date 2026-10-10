# FUE-G 00 — Hub / Dispatcher integrated first-user proof (isolated T2)

Date: 2026-10-10
Status: **FUE-G00 intégré T2 LAB PASS 34/34 sur d181f969 ; nouvelle épreuve navigateur vierge en cours, FUE-G00 canonique global PARTIEL.**
Canonical requirement: authorized user on first-use workstation, desktop 1280 × 900 and tablet 768 × 1024, choose Hub → experience → Hub without dead ends.
Canonical sources: [FUE plan](https://app.notion.com/p/3f177c66336281c49a48d1361307f458), [roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb), retrospective [18-sublot matrix](./V1_5_FUE_00_TO_03_RETROSPECTIVE_MATRIX.md).

## Important independence

GitHub #820 postmerge [run #38014691497](https://github.com/hraaaaf/Digital_crown/actions/runs/38014691497) was verified COMPLETED/SUCCESS on `master@4edd5975cb9c247d50d2581e3f5f72f6354ce941`. It was never a mandatory prerequisite to **start** isolated FUE-G00 on a separate exact-master branch: it is merge closeout only. New FUE-G00 tests run on their own candidate HEAD, with no merge/release/deployment.

## Proof contract and intended observations

- **Real, isolated APIs**: the T2 server uses disposable SQLite with local 127.0.0.1 networking and generated credential. Legitimate owner API login and enrollment create **a real workstation identity** prior to launching the browser; only its `dc_workstation` cookie is transferred, never auth tokens.
- **Fresh user session** in Chromium with zero user-auth localStorage and exactly three Hub choices; Cabinet direct URL anonymous denied and card selection goes to true UI login.
- **Authenticated Cabinet** reached by real login form, dashboard visible.
- **Control Center** selected by actual Hub card; return to Hub via its **real on-screen button**, not direct URL shortcut.
- **Owner PIN** configured or rotated through the real Hub UI and a server HTTP 200; mode Station selected/applied through UI and real backend (never injected state).
- **Station lock**: direct URL Hub and Control routes denied by the authoritative workstation mode, including after reload.
- **Owner escape** via production keyboard shortcut, invalid PIN rejected by server HTTP 403 without leaving Station, valid PIN accepted HTTP 200 and UI returns Hub.
- **Proof**: both tablet 768×1024 + desktop 1280×900; 17 explicit checks per viewport, 10 before/action/after PNG each = **34 checks and 20 PNG expected**, plus `report.json` exact candidate SHA; no pageerror, HTTP 5xx, horizontal overflow. Screenshots must be opened/reviewed; synthetic success alone is not UX certification.
- **REQUIRED**: new FUE-G00 workflow on exact SHA + Scope Gate, frontend/backend contractual tests, two *internal* adversarial reviews (A UX/a11y, B security/fake-green), same-HEAD confirmation. Experimental M6-I biometric does not silently block LAB when skipped.

## Known limits / gating

- The browser is **first-login but not a physically unprovisioned workstation**: workstation enrollment is deliberately performed with the real API before the browser starts; this does not certify physical first-use enrollment.
- No real physical 3-PC TLS LAN, real hardware reboot, camera, NFC or production patient/tenant data. No claim to human user testing.
- FUE-G00 complete **only** if every relevant full-path condition is actually covered; until then classify **PARTIEL** even if this integrated LAB segment passes.
- Existing FUE-I 00.2 LAB targeted proof from [PR #820](https://github.com/hraaaaf/Digital_crown/pull/820) is 9.1/10 and is independent; 00.4 synthetic Hub proof from [#37797275871](https://github.com/hraaaaf/Digital_crown/actions/runs/37797275871) covered 12/12 paths but not true PIN/owner escape.
- No changes to product runtime, backend auth, PIN, patient flow; no Vercel/installer/real device. PR remains DRAFT until explicit owner merge approval.

## PRE — vraie UI d'enrôlement d'un navigateur vierge, sans cookie injecté (2026-10-10)

L'ancienne preuve [run #38034317309](https://github.com/hraaaaf/Digital_crown/actions/runs/38034317309) sur `d181f9692cd6be4f19fd5d13f0c0e3efd0749e3a` est GREEN, 34/34 assertions et 20 captures + revues internes A 9.0/B 9.1. Elle **n'atteste pas la nouvelle révision**.

Nouveau script `frontend/scripts/audit-v15-fue-g00-fresh-enrollment-t2.mjs`, exécuté **après** le script intégré créant des postes légitimes chez le tenant T2 jetable. Deux navigateurs neufs **sans storageState/cookie/identité poste injecté** : Hub 3 cartes → clic Cabinet exige login → vrai login propriétaire → `/hub?enroll=1`, refus `/workstation/state`=423 et Dashboard refusé → mauvais password propriétaire via vraie UI `/workstation/enroll`=403 sans cookie → bon password via même UI `/workstation/enroll`=200, cookie `dc_workstation` créé **alors seulement** → Dashboard accessible et Centre de contrôle → bouton visible retour Hub. Attendu = **20 assertions par profil × 2 = 40 et 8 captures × 2 = 16**, plus les 34 checks/20 captures du script initial, **total 74 checks et 36 PNG, 2 report.json**. Aucune validation avant CI exacte et inspection réelle.

Limite structurelle : le navigateur neuf arrive dans un tenant contenant déjà des postes ; **premier poste d'un cabinet ne contenant aucun poste** utilise `GET /workstation/state` pour auto-création, non couvert. Aucun essai machine physique vierge, reboot, TLS LAN, patient ou utilisateur humain ; FUE-G00 global PARTIEL.

## Next

Execute [FUE-G00 workflow](../../.github/workflows/v15-fue-g00-integrated-t2.yml), inspect genuine PNG and JSON on exact SHA. If RED, classify harness or product finding and correct on a NEW SHA without weakening denial tests. Do not assign a score, external review or `CONVERGED` before proofs and adversarial confirmation.
