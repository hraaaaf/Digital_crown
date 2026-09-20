# PC-02 UI implementation plan

Status: PREPARED — do not modify PatientCompanionApp until BEFORE artifact passes.

## Existing screen anchors verified

The current home renders:
1. Patient Companion header.
2. Mon espace card with local-vault state, cabinet reachability, sync.
3. Read-only Mes rendez-vous wallet section.
4. Documents & media.
5. dossier/device controls.

The current appointment card renders motif first and a compact datetime/status line. There are no booking/reschedule/cancel actions.

## Planned minimal delta after BEFORE gate

- Preserve Mon espace and device security controls.
- Promote Mes rendez-vous immediately after Mon espace.
- Add one primary 48px+ CTA: Prendre un rendez-vous.
- Confirmed cards: date/time strongest, Confirmé chip, then motif.
- Eligible cards: Déplacer + Annuler.
- Inline booking panel: practitioner display name -> date -> cabinet-issued slot.
- Local request state machine:
  - local_queued: “Enregistrée sur ce téléphone — pas encore envoyée”
  - remote_pending: “Demande envoyée — en attente du cabinet”
  - confirmed: only from verified cabinet ACK
  - rejected: return to slot selection with stable neutral error.
- Cancel requires explicit second-step confirmation.
- No numeric internal IDs in state, DOM test fixtures, or request payload.

## Proof

AFTER must reproduce the BEFORE matrix:
- Chromium 360x800
- Chromium 390x844
- WebKit 360x800
- WebKit 390x844

No horizontal overflow. Screenshots plus evidence JSON retained as CI artifact.
