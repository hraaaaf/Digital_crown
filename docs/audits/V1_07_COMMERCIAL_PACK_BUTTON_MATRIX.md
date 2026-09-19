# V1-07 — Commercial Pack Button-State Matrix

Date: 2026-09-19  
Repository: `hraaaaf/Digital_crown`  
Baseline: `master@ceae1624c5f1311eb7ffcf512785b8a30fe438fc`  
Canonical remediation PR: #629  
Original combined audit PR: #628

## Goal

Verify the observable outcome of the commercial-pack actions for GOLD, PREMIUM and ELITE across success, capacity, pending, rejection, suspension, deletion, confirmation/cancel, duplicate action, backend refusal, archived/suspended states and stale-auth states.

## Success

The pack/button surface is ready for V1 freeze only when:

1. GOLD/PREMIUM/ELITE seat semantics match the canonical commercial policy.
2. Pending members reserve capacity and approval does not double-count.
3. Rejection/deletion frees capacity.
4. Incompatible downgrades are refused before mutation.
5. Rejected/unapproved team identities cannot be reactivated or reuse stale access/refresh tokens.
6. UI actions call the intended endpoint and never report success after backend refusal.
7. Load/error/confirmation states cannot be confused with empty/success.
8. Mutation buttons are safe against accidental duplicate submission.
9. Desktop/mobile expose intelligible server refusal details.
10. Visual state changes are proven by matched BEFORE/AFTER viewports where UI changed.

## Canonical pack policy

| Pack | Dentists total | Assistants | Unlimited semantics |
| --- | ---: | ---: | --- |
| GOLD | 1, owner included | 2 | No |
| PREMIUM | 2, owner included | 6 | No |
| ELITE | Unlimited | Unlimited | `None`, not a synthetic ceiling |

Reserved usage = approved + pending. Rejected members are excluded.

## Isolation strategy

The original #628 became too broad for causal diagnosis, so the matrix was split into three independent proof lots:

| Lot | Scope | PR | Current proof |
| --- | --- | --- | --- |
| LOT1 | backend packs / quotas / downgrade invariants | #630 | dedicated `V1-07 LOT1 Pack Quotas` exact-head SUCCESS on `ed68623732b923f074d974509609d9f9a551d413`; T2 + Agenda also SUCCESS |
| LOT2 | TeamManager cabinet buttons + rejected identity safety | #631 | latest exact-head rerun required after coverage/accessibility additions |
| LOT3 | SuperAdmin desktop/mobile pack/licence/renewal actions | #632 | functional gate was SUCCESS before the final archived/suspended coverage addition; latest exact-head rerun required |

#629 is the intended reconciliation branch because it already contains the wider V1-07 adversarial remediation. Isolated lot PRs are proof/debug vehicles until exact deltas are reconciled.

## Executable matrix

| Surface | Action/state | GOLD | PREMIUM | ELITE | Proof |
| --- | --- | --- | --- | --- | --- |
| Team backend | create dentist until cap | owner already 1/1 → 402 | +1 then 402 | repeated creates allowed | LOT1 pytest |
| Team backend | create assistant until cap | 2 then 402 | 6 then 402 | repeated creates allowed | LOT1 pytest |
| Team backend | pending reserves seat | yes | yes | yes | LOT1 pytest |
| Team backend | approve pending | no double count | no double count | no double count | LOT1 pytest |
| Team backend | reject/delete | frees seat | frees seat | unlimited remains unlimited | LOT1 pytest |
| Team backend | suspend/reactivate approved | reserved usage preserved | preserved | preserved | LOT1 pytest |
| SuperAdmin backend | compatible target pack | success | success | success | LOT1 pytest |
| SuperAdmin backend | incompatible finite downgrade | 409 + non-mutation | 409 + non-mutation | n/a | LOT1 pytest |
| TeamManager UI | add / cancel / password reveal | exercised | exercised | exercised | LOT2 Vitest |
| TeamManager UI | successful assistant create | exercised | exercised | exercised | LOT2 Vitest |
| TeamManager UI | quota refusal | exact backend detail | exact backend detail | n/a | LOT2 Vitest |
| TeamManager UI | approve / reject / delete | exercised | exercised | exercised | LOT2 Vitest |
| TeamManager UI | retry after load error | recovers to true state | same | same | LOT2 Vitest |
| TeamManager UI | permissions open / save / cancel / close | exercised | exercised | exercised | LOT2 Vitest |
| TeamManager UI | suspend / reactivate approved | exercised | exercised | exercised | LOT2 Vitest |
| TeamManager UI | rejected identity | no Reactivate/Suspend | same invariant | same invariant | LOT2 Vitest + BEFORE/AFTER |
| TeamManager UI | rapid duplicate mutation | single-flight | single-flight | single-flight | LOT2 Vitest |
| Auth | stale access after rejection | 401 | same invariant | same invariant | LOT2 pytest |
| Auth | stale refresh after rejection | 401 | same invariant | same invariant | LOT2 pytest |
| Desktop SuperAdmin | pack selector | GOLD↔others | PREMIUM↔others | ELITE↔others | LOT3 Vitest |
| Desktop SuperAdmin | incompatible downgrade detail | exact 409 | exact 409 | source state | LOT3 Vitest + BEFORE/AFTER |
| Desktop SuperAdmin | +1m/+3m/+6m/+1y | exercised | exercised | exercised | LOT3 Vitest |
| Desktop SuperAdmin | notes/history/renewal/suspend/archive | exercised | exercised | exercised | LOT3 Vitest |
| Desktop SuperAdmin | archived/suspended state | pack/licence/renewal disabled; Reactivate/Désarchiver exposed | same | same | LOT3 Vitest |
| Mobile SuperAdmin | pack selector confirmation | exercised | exercised | exercised | LOT3 Vitest |
| Mobile SuperAdmin | licence/CRM/sensitive confirmations | exercised | exercised | exercised | LOT3 Vitest |
| Mobile request layer | real set-plan request | exercised | exercised | exercised | LOT3 hook Vitest |
| Mobile request layer | downgrade 409 detail | surfaced | surfaced | n/a | LOT3 hook Vitest |
| Renewal backend | no phone | 409 | 409 | 409 | LOT3 pytest |
| Renewal backend | transport failure | 502 | 502 | 502 | LOT3 pytest |
| Renewal backend | confirmed transport success | success only after `send_whatsapp_via_whatsmate() == true` | same | same | LOT3 pytest |

## Findings

### PACK-BTN-01 — BLOCKER — rejected identity could be reactivated
Implemented:
- generic reactivation refuses non-`approved` sub-accounts with 409;
- access/refresh auth fail closed for unapproved sub-accounts;
- stale-token regression test covers an intentionally corrupted `rejected + active` row;
- TeamManager no longer exposes Reactivate/Suspend on a rejected identity.

Status: **IMPLEMENTED — LOT2 exact-head proof pending.**

### PACK-BTN-02 — MUST-FIX — load failure looked like an empty team
Implemented:
- explicit `Équipe non chargée` state;
- retry button performs a real refetch;
- empty-team illustration is not shown while load failed.

Status: **IMPLEMENTED — LOT2 exact-head proof pending.**

### PACK-BTN-03 — MUST-FIX — GOLD partial quota banner was misleading
Implemented:
- saturated role is named;
- remaining opposite-role capacity is shown;
- GOLD 1/1 dentist + 0/2 assistants now says that two assistant places remain.

Status: **IMPLEMENTED — LOT2 exact-head proof pending.**

### PACK-BTN-04 — MUST-FIX — duplicate TeamManager mutations
Implemented:
- single-flight lock for reject/delete/suspend/reactivate/permission-save;
- Validate retains its dedicated busy lock;
- rapid double-click tests cover status mutation and Validate.

Status: **IMPLEMENTED — LOT2 exact-head proof pending.**

### PACK-BTN-05 — MUST-FIX — desktop downgrade hid server detail
Implemented:
- desktop surfaces backend 409 `detail`;
- mobile already preserved the detail;
- matched visual evidence checks generic BEFORE vs precise AFTER.

Status: **IMPLEMENTED — LOT3 latest exact-head proof pending.**

### PACK-BTN-06 — MUST-FIX — renewal action could report false success
Implemented:
- UI wording is WhatsApp;
- no phone → 409 + skipped audit event;
- transport false → 502 + failed audit event;
- success only after confirmed transport true + sent audit event.

Status: **IMPLEMENTED — LOT3 latest exact-head proof pending.**

### PACK-BTN-07 — BUILD REGRESSION IN TEST — TypeScript deferred inferred as `never`
Observed on #629 through unrelated Mobile Stock/Library certifications:
- their own mobile contracts were green;
- both failed at global `npm run build`;
- root cause: `TeamManager.buttonMatrix.test.tsx` deferred resolver invocation triggered TS2349.

Corrected:
- deferred changed to a stable callable `releasePut` closure;
- fix synchronized to LOT2, #628 and #629.

Status: **CORRECTED — #629 build rerun required.**

## Visual evidence protocol

LOT2 uses matched 1024×900 and 1440×1000 BEFORE/AFTER captures for:
1. GOLD partial quota;
2. Team load failure;
3. rejected identity action row.

LOT3 uses the same matched viewports for:
1. incompatible ELITE → GOLD downgrade;
2. renewal with no phone.

Assertions include exact expected textual delta, no horizontal overflow and no runtime page error.

## Freeze decision

**NOT READY TO CLOSE YET.**

LOT1 is proven. LOT2, LOT3 and the reconciled #629 exact head still need their final reruns after the latest coverage/test corrections. V1-08 remains blocked until those proofs are green and #629 has no unexplained required red checks.

## No deployment

No Vercel deployment was requested or performed.
