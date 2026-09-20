# PC-02 — Patient Agenda UI Target

## Goal

Make appointment self-service feel simple and premium while never confusing a request with a confirmed cabinet appointment.

## Reference state

Existing Patient Companion home at PC-01: one mobile column, local-vault status, sync control, then wallet sections. The appointment wallet is read-only and renders synchronized appointment cards.

## Target mobile hierarchy

1. **Mes rendez-vous** becomes the first action surface after “Mon espace”.
2. Confirmed appointment cards keep a calm status chip: **Confirmé**.
3. Primary action: **Prendre un rendez-vous**.
4. Per eligible appointment: **Déplacer** and **Annuler** as secondary actions.
5. Slot picker shows only cabinet-issued options: date/time + duration. No practitioner/resource/internal IDs.
6. Submission state is explicit: **Demande envoyée — en attente du cabinet**.
7. Only a verified cabinet ACK may switch the card to **Confirmé**.
8. Offline state: **Demande enregistrée sur ce téléphone — pas encore envoyée**. Never “confirmé”.
9. Rejected/conflict state returns to slot choice with a neutral explanation; never silently chooses another slot.

## Visual constraints

- preserve current max-width mobile shell and design tokens;
- minimum 48px touch targets;
- one primary CTA per state;
- no modal stack; use an inline agenda panel/sheet inside the existing flow;
- appointment time is the strongest visual datum;
- destructive cancel requires a confirmation step;
- local/offline/remote status remains text-visible, not color-only.

## Evidence gate

BEFORE and AFTER must use the same 360x800 and 390x844 viewports on Chromium and WebKit.
