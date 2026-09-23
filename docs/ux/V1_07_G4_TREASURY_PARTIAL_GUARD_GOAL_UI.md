# Digital Crown V1-07 — G4 Treasury Partial Guard — UI Goal

Status: TARGET LOCKED — implementation waits for paired BEFORE evidence.

## Goal

When the user selects `Partiel` in the Honoraires `Encaissement` modal, the existing business guard must remain visible **and directly actionable inside the active modal layer**.

## Success

At both canonical viewports `390×844` and `1280×900`:

- selecting `Partiel` exposes the existing amber `Paiement partiel` guard;
- the guard is rendered inside the Treasury modal, above the `Statut de Règlement` controls;
- `Compris` is visible, focusable and clickable through the normal pointer path;
- clicking `Compris` clears the guard without closing Treasury;
- no status mutation to `PARTIEL` is accepted by the store;
- no persistence request is emitted by acknowledging the guard;
- no horizontal overflow or page error is introduced.

## Reference

Reuse the current guard copy, amber visual treatment and `Compris` action from `AccountingStudio.tsx`. Do not introduce a new dialog, toast or additional overlay.

Target composition inside Treasury:

1. Encaissement header
2. Existing amber `Paiement partiel` guard when present
3. Status / payment mode / plan controls
4. Existing footer actions

## BEFORE / AFTER protocol

BEFORE:
- `g4-honoraires-390x844-treasury-partial-guard-before.png`
- `g4-honoraires-1280x900-treasury-partial-guard-before.png`

AFTER must use the same viewports and state:
- `g4-honoraires-390x844-treasury-partial-guard-after.png`
- `g4-honoraires-1280x900-treasury-partial-guard-after.png`

No implementation may be promoted until both BEFORE images exist in exact-head evidence.

## Non-goals

- no change to the partial-payment business rule;
- no new payment persistence path;
- no change to Treasury confirmation semantics;
- no Vercel deployment.
