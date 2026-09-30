# V1.5-00.4 — Hub & Dispatcher final integration audit

Date: 2026-09-30
Base inspected: certified `master@efc21e1a193c9adcf0ff057c25cde36e4a04d8cd`, merged into the 00.4 branch after the initial prep commit `981d7742…`
Implementation branch: `feat/v1.5-00-4-final-integration`

## Goal

Close V1.5-00 without inventing new product scope: map every retained Hub/Dispatcher requirement to code, tests and observed proof, then repair only real residual gaps.

## Requirement matrix

| Requirement | Code / proof path | Classification |
|---|---|---|
| First launch lands on Hub; configured workstation dispatches to remembered experience | `App.tsx`, `WorkstationModeGate.tsx`, workstation bootstrap state | already satisfied |
| PC Hub exposes Cabinet / Station / Control Center only | `HubPage.tsx` cards + HubPage tests | already satisfied |
| Mobile and Patient Companion remain outside PC Hub | dedicated routes in `App.tsx`; workstation backend tests cover paired mobile boundary | already satisfied |
| Workstation mode is server authority, not local storage/user preference | `backend/routers/workstation_mode.py`; mode/cookie/tenant tests | already satisfied |
| Station direct URL cannot bypass lock; exit requires owner PIN | `WorkstationModeGate.tsx`, `WorkstationExperiencePage.tsx`, backend escape contract | already satisfied |
| Backend unavailable keeps Hub usable without clinical payload | `HubPage.tsx` fail-soft identity fetch | already satisfied |
| Backend unavailable keeps local Control Center reachable | pre-00.4 gate redirected Control Center back to Hub | **real residual gap — fixed in 00.4** |
| Hub contains no patient/business clinical data | only clinic identity `nom_cabinet/cabinet_type` is fetched; no patient/agenda/accounting payload | already satisfied; footer wording tightened |
| Control Center remains a truthful technical shell, not V1.5-01 topology implementation | `WorkstationExperiencePage.tsx` explicitly says “en cours de construction” | already satisfied |
| Touch/responsive Station remains usable | existing Station UI + prior 390x844/768x1024/1280x900 visual evidence | already satisfied; targeted recheck required only for changed Hub copy |
| LAN topology / failover / discovery | not part of current code delta | V1.5-01+ |

## Residual gap found

The current contract says the local Control Center must remain reachable when cabinet backend/workstation authority is unavailable. Before 00.4, `WorkstationModeGate` treated `control-center` exactly like protected clinical routes and redirected it to `/hub?mode-check=failed`.

This contradicted both the product contract and the Control Center screen copy (“Le diagnostic local restera accessible même si le serveur cabinet est indisponible.”).

## Minimal correction

- `control-center` is now allowed when bootstrap authority cannot be read.
- `protected` clinical routes still fail closed.
- when bootstrap authority is unavailable, Station remains on its restrictive non-clinical shell; no clinical route is opened.
- Station lock still wins when state is available and mode is `station`.
- Hub offline copy now distinguishes recovery surfaces from locked clinical spaces.
- Hub footer now says “aucune donnée patient ni donnée métier clinique”, which is truthful while still allowing canonical clinic identity.

## Closeout evidence

- candidate HEAD: `f406ae767f2585e468a15cbc65ce5d106573e9f1`
- PR: #724
- merge commit: `2f0fdeb4583e633e479627a275d7da2d6bc1375e`
- targeted Hub/Gate/Station/Admin tests: **17/17 PASS**
- Hub Visual Proof: run `36788607154` — **SUCCESS**
- Human Visual Approval: run `36790450196` — **SUCCESS**
- double-check exact-head: **9.3/10**
- triple-check adversarial exact-head: **9.0/10**
- post-merge targeted identity check: `HubPage.tsx`, `HubPage.test.tsx`, `WorkstationModeGate.tsx`, and `WorkstationModeGate.test.tsx` have identical blob SHAs on candidate HEAD and merge commit
- no Vercel deployment; no cabinet runtime mutation

### Closeout status

V1.5-00 is closed on the merged code above. V1.5-01 may unlock only after this documentation closeout is merged and re-read on `master`.
