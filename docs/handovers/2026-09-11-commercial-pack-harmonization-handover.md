# Digital Crown — Commercial Pack Harmonization

Date: 2026-09-11
Status: IMPLEMENTED / PRE-MERGE CLOSEOUT
Canonical file: `docs/handovers/2026-09-11-commercial-pack-harmonization-handover.md`
Repository: `hraaaaf/Digital_crown`
Branch: `feat/commercial-pack-harmonization`
PR: #424
Deployment: none requested / none authorized

## Goal
One commercial pack must produce the same team quota semantics everywhere while keeping license validity/device authorization, subscription plan, and cabinet structure independent.

## Proven commercial policy
- GOLD: 1 dentist total, owner included + 2 assistants.
- PREMIUM: 2 dentists total + 6 assistants.
- ELITE: genuinely unlimited, represented by `None`, never a numeric sentinel.
- Approved and pending members reserve quota.
- Incompatible downgrade is rejected before mutation; no member is auto-disabled.

## Architecture preserved
- License: validity / expiration / device authorization.
- Subscription plan: GOLD / PREMIUM / ELITE.
- Cabinet type: structural PRIVE / CLINIQUE axis.
- No runtime coupling between cabinet type and subscription plan was introduced.

## Implemented
### R1 — inventory
Direct quota consumers and tests were audited. `TeamManager.tsx` required nullable maxima support; the admin dashboard was also verified as a quota consumer.

### R2 — canonical policy
`backend/services/subscription_policy.py` is the canonical source for GOLD/PREMIUM/ELITE team limits. ELITE uses `None` for both limits.

### R3 — team quota semantics
`backend/routers/team.py` derives quota behavior from the canonical policy. ELITE remains addable without an artificial ceiling. Approved + pending reservations are counted consistently, with the owner occupying one dentist seat.

### R4 — downgrade guard
`backend/routers/superadmin.py` checks current reserved usage against the target plan before mutation. An incompatible downgrade returns HTTP 409 and leaves the current plan unchanged.

### R5 — frontend coherence
`frontend/src/features/admin/TeamManager.tsx` accepts nullable maxima and renders `Illimité` for ELITE while preserving the existing layout.

UI protocol completed:
- BEFORE/Goal: `.audit/commercial-pack-harmonization-goal.md`
- reference: `.audit/commercial-pack-harmonization-mockup.svg`
- AFTER: 390 / 768 / 1280 exact-HEAD captures
- observed: `7/Illimité` and `18/Illimité`, no `Quota atteint`, no horizontal overflow, no console errors on the successful certification run
- visual score: 9.5/10

### R6 — tests
Regression coverage includes:
- GOLD 1/2 and PREMIUM 2/6 policy limits
- ELITE nullable/unlimited semantics
- approved + pending quota reservation; rejected excluded
- quota API construction for ELITE
- incompatible downgrade blocked and non-mutating
- compliant downgrade succeeds
- upgrade to ELITE succeeds
- admin dashboard exposes ELITE semantic unlimited without upgrade warning

## Exact product HEAD proof before this closeout-only commit
Product HEAD: `a5339ae0baeae2e02663a6b453a723344fe91a8d`

Successful GitHub Actions on that exact HEAD:
- CI #3372 — SUCCESS
- T2 Runtime Browser Certification #2358 — SUCCESS
- Commercial Pack Team Visual Certification #6 — SUCCESS
- Settings R10 Team Password Visual Certification #17 — SUCCESS
- M6-I #1158 — SKIPPED (not a failure)

PR #424 was verified open, draft and mergeable on the product HEAD before this closeout commit.

## R8 — remaining pre-merge sequence
This file update is documentation-only and intentionally creates the final closeout commit. Required next steps:
1. verify the branch HEAD equals the closeout commit returned by GitHub;
2. verify exact-HEAD CI after this documentation-only commit;
3. if green, mark PR #424 ready and merge;
4. verify post-merge `master` contains the commercial policy and this closeout;
5. do not deploy to Vercel.

## Deployment guard
No Vercel deployment is authorized. Repository `vercel.json` has Git deployment disabled; this lot performs no deployment action.

## Proof rule
Do not call the lot fully closed until the closeout commit itself has passed the required exact-HEAD checks and the merge/post-merge state has been verified.
