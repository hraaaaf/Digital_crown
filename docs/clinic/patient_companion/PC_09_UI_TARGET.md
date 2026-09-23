# PC-09 — Teleconsultation — UI Target

Status: TARGET LOCKED
Date: 2026-09-23

## Goal
Make teleconsultation feel like a normal clinical action, not a networking tool.

The dentist and patient must never see STUN/TURN/SDP/ICE/WebRTC jargon.

## Success
- explicit patient acceptance before camera/microphone permission;
- explicit decline action without activating camera/microphone;
- clear waiting / connecting / connected / ended states;
- no false “connected” state;
- local + remote video surfaces are readable;
- end-call action remains obvious;
- touch targets >= 44px;
- no horizontal overflow;
- 200% text scaling remains usable;
- patient and staff surfaces stay visually consistent with Patient Companion.

## BEFORE
No PC-09 teleconsultation surface exists in the current certified Patient Companion UI.

Canonical BEFORE evidence is the final certified PC-08 runtime artifact, captured immediately before PC-09 implementation at the same Patient Companion/staff surfaces:
- approved pre-PC-09 HEAD: `1bbc1621a90a681cc1fb34fa846dbb3ec3c68c26`;
- runtime run: `35859746972` → SUCCESS;
- artifact: `10750431243`;
- digest: `sha256:9181923334458fe680cd8c93beac24d08f2e0c724ea2ea6a0264727b913b287a`;
- patient Chromium: 360×800 + 390×844;
- patient WebKit: existing PC-08 runtime captures;
- staff: 390×844 + 768×1024 + 1280×900.

The BEFORE evidence proves absence of the PC-09 surface. PC-09 AFTER must use the same target viewport classes.

## Reference / mockup

### Patient — idle

┌─────────────────────────────────┐
│  ◉ Téléconsultation             │
│  Consultation vidéo             │
│  En rejoignant, vous acceptez     │
│  cette téléconsultation.        │
│  Caméra + micro uniquement      │
│  après votre action.            │
│  Aucun enregistrement.          │
│                                 │
│  Aucune téléconsultation        │
│  en attente                     │
└─────────────────────────────────┘

### Patient — available

┌─────────────────────────────────┐
│  Téléconsultation               │
│  Consultation vidéo             │
│                                 │
│  Prête à rejoindre               │
│  [ Accepter et rejoindre ]       │
│  [ Refuser ]                     │
│  Créée aujourd’hui              │
└─────────────────────────────────┘

### Patient — active

┌─────────────────────────────────┐
│  Cabinet                        │
│  [       remote video       ]   │
│                                 │
│  Vous                           │
│  [       local video        ]   │
│                                 │
│          [ Terminer ]           │
└─────────────────────────────────┘

### Staff — idle

┌──────────────────────────────────────────────┐
│  Téléconsultation                           │
│  Consultation vidéo avec le patient.        │
│                                              │
│  [ Démarrer une téléconsultation ]          │
└──────────────────────────────────────────────┘

### Staff — active desktop

┌───────────────────────┬───────────────────────┐
│ Patient               │ Cabinet               │
│ [ remote video ]      │ [ local video ]       │
├───────────────────────┴───────────────────────┤
│ Connexion en cours / En consultation [End]   │
└───────────────────────────────────────────────┘

## Wording policy
Allowed:
- Téléconsultation
- Consultation vidéo
- Accepter et rejoindre
- Refuser
- Connexion en cours
- En consultation
- Terminer
- Connexion impossible sur ce réseau

Forbidden in end-user UI:
- WebRTC
- SDP
- ICE
- STUN
- TURN
- peer connection
- signaling

## Viewports

Patient:
- 360×800 Chromium
- 390×844 Chromium
- 390×844 WebKit

Staff:
- 390×844
- 768×1024
- 1280×900

## Human gate
AFTER captures must be inspected at the same target viewports before merge.

No Vercel deployment.
