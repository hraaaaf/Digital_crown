# V1-07 — Commercial Pack Button-State Matrix

Date: 2026-09-19  
Repository: `hraaaaf/Digital_crown`  
Baseline: `master@ceae1624c5f1311eb7ffcf512785b8a30fe438fc`  
Audit PR: #628  
Audit branch: `audit/v1-07-commercial-pack-button-matrix`

## Goal

Verify the observable outcome of the commercial-pack actions for GOLD, PREMIUM and ELITE across success, capacity, pending, rejection, suspension, deletion, confirmation/cancel, duplicate action, backend refusal and stale-auth states.

## Success

The pack/button surface is ready for V1 freeze only when:

1. GOLD/PREMIUM/ELITE seat semantics match the canonical commercial policy.
2. A pending member reserves capacity and approval does not double-count the seat.
3. Rejection/deletion frees capacity.
4. Incompatible downgrades are refused before mutation.
5. A rejected or otherwise unapproved team identity cannot be reactivated through the generic status endpoint and cannot reuse stale access/refresh tokens.
6. UI actions call the intended endpoint and do not report success when the backend refused the action.
7. Load/error/confirmation states cannot be confused with an empty/success state.
8. Mutation buttons are safe against accidental duplicate submission.
9. The same server refusal is intelligible on desktop and mobile.

## Canonical pack policy verified from code

| Pack | Dentists total | Assistants | Unlimited semantics |
| --- | ---: | ---: | --- |
| GOLD | 1, owner included | 2 | No |
| PREMIUM | 2, owner included | 6 | No |
| ELITE | Unlimited | Unlimited | `None`, not a synthetic ceiling |

Reserved usage = approved + pending. Rejected members are excluded.

## Executable matrix

| Surface | Action/state | GOLD | PREMIUM | ELITE | Proof |
| --- | --- | --- | --- | --- | --- |
| Team backend | create dentist until cap | owner already 1/1 → 402 | +1 then 402 | repeated creates allowed | targeted pytest |
| Team backend | create assistant until cap | 2 then 402 | 6 then 402 | repeated creates allowed | targeted pytest |
| Team backend | pending reserves seat | yes | yes | yes | targeted pytest |
| Team backend | approve pending | no double count | no double count | no double count | targeted pytest |
| Team backend | reject pending | frees seat | frees seat | capacity remains unlimited | targeted pytest |
| Team backend | delete member | frees seat | frees seat | capacity remains unlimited | targeted pytest |
| Team backend | duplicate create | 409, no extra reservation | 409 | 409 | targeted pytest |
| Team backend | suspend/reactivate approved | reserved usage preserved | preserved | preserved | targeted pytest |
| Team backend | permission update | sanitized | sanitized | sanitized | targeted pytest |
| Team backend | rejected → generic reactivate | **409 after audit fix** | same invariant | same invariant | targeted pytest |
| Auth | stale access after rejection | **401 after audit fix** | same invariant | same invariant | targeted pytest |
| Auth | stale refresh after rejection | **401 after audit fix** | same invariant | same invariant | targeted pytest |
| SuperAdmin backend | target pack compatible | success | success | success | targeted pytest |
| SuperAdmin backend | finite downgrade over capacity | 409, no mutation | 409, no mutation | n/a | targeted pytest |
| TeamManager UI | add/cancel + password reveal | exercised | exercised | exercised | Vitest |
| TeamManager UI | quota refusal on create | exact backend detail | exact backend detail | n/a | Vitest |
| TeamManager UI | approve/reject/delete | exercised | exercised | exercised | Vitest |
| TeamManager UI | permissions/suspend/reactivate/delete | exercised | exercised | exercised | Vitest |
| Desktop SuperAdmin | pack selector | GOLD↔others | PREMIUM↔others | ELITE↔others | Vitest |
| Desktop SuperAdmin | +1m/+3m/+6m/+1y | exercised | exercised | exercised | Vitest |
| Desktop SuperAdmin | notes/history/renewal/suspend/archive | exercised | exercised | exercised | Vitest |
| Mobile SuperAdmin | pack selector confirmation | exercised | exercised | exercised | Vitest |
| Mobile SuperAdmin | licence/CRM/sensitive confirmations | exercised | exercised | exercised | Vitest |
| Mobile request layer | real set-plan request | exercised | exercised | exercised | hook Vitest |
| Mobile request layer | downgrade 409 detail | surfaced | surfaced | n/a | hook Vitest |

## Confirmed findings

### PACK-BTN-01 — BLOCKER — rejected identity could be reactivated into an inconsistent active state

Observed pre-fix:
- `reject_member` sets `approval_status=rejected`, `is_active=false`.
- generic `PUT /team/{id}` accepted `is_active=true` without checking approval state.
- `get_current_user` and refresh validation only required `is_active`.
- a previously approved collaborator could therefore retain stale tokens, be rejected, then regain token usability if put back into the contradictory rejected+active state.

Candidate correction on PR #628:
- generic activation now refuses any team account whose approval status is not `approved`;
- access and refresh token validation fail closed for team accounts whose approval status is not `approved`;
- regression test covers an intentionally corrupted legacy rejected+active row.

Status: **FIX CANDIDATE — exact-head CI required before closure.**

### PACK-BTN-02 — MUST-FIX — TeamManager load failure is rendered as a false empty team

`fetchMembers` catches the request failure, logs to console, then sets `loading=false`. Since `members` defaults to `[]`, the user sees “Aucun membre dans l'équipe”.

Risk: network/API failure is indistinguishable from a real empty team.

Status: **OPEN.**

### PACK-BTN-03 — MUST-FIX — quota banner can mislead GOLD owners

On GOLD the owner consumes the single dentist seat by design. Therefore `can_add_dentiste=false` from the start, even while the two assistant seats remain available. The current generic banner is displayed when either role is full and says only “Quota atteint — passez au plan supérieur”.

Risk: valid assistant capacity is visually presented as if the whole pack were exhausted.

Status: **OPEN.**

### PACK-BTN-04 — MUST-FIX — several TeamManager mutations lack a duplicate-action lock

Create and Approve have busy locks. Reject, Delete, Suspend/Reactivate and Save permissions do not.

Risk: rapid double activation can issue duplicate POST/PUT/DELETE calls and surface a second failure after the first success.

Status: **OPEN.**

### PACK-BTN-05 — MUST-FIX — desktop hides the actionable downgrade refusal

Backend returns exact 409 detail with current reserved team and target limits. Mobile request handling surfaces that detail. Desktop replaces it with the generic “Erreur lors du changement de pack.”

Risk: SuperAdmin cannot tell what must be changed before retrying the downgrade.

Status: **OPEN.**

### PACK-BTN-06 — MUST-FIX — desktop “Email de relance” does not match the backend action

Desktop title/success copy says email. Backend endpoint actually sends WhatsApp when a phone is present. If no phone exists, backend still returns HTTP success with “Aucun numéro…” while desktop unconditionally reports “Email de relance envoyé !”. The audit history action is also currently `renewal_whatsapp_sent` even when no phone exists.

Risk: false operational success and inaccurate audit trail.

Status: **OPEN.**

## Current executable proof

Dedicated workflow: `V1-07 Commercial Pack Button Matrix`.

The workflow checks out the exact PR head and runs:
- targeted backend pytest matrix;
- TeamManager real-click Vitest;
- desktop SuperAdmin real-click Vitest;
- mobile SuperAdmin confirmation/button Vitest;
- mobile SuperAdmin real request-layer action Vitest.

First meaningful frontend run before synchronization fix:
- 19 tests total;
- 16 passed;
- 3 failed;
- all 3 failures came from the same test race: the next pack selection ran while the confirmation dialog still showed `Traitement…`.
- No product defect was inferred from that failure; the test now waits for the async confirmation to close before the next target.

Latest exact-head evidence must be recorded here only after the run completes.

## Freeze decision

**NOT READY TO CLOSE.**

The pack quota engine is internally coherent in the inspected paths, but the button-state surface still has open MUST-FIX findings. V1-08 must not use a green test run as a substitute for closing those findings.

## No deployment

No Vercel deployment was requested or performed.
