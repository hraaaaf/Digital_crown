# PC-09 — Teleconsultation — UI Target

Status: TARGET LOCKED
Date: 2026-09-23

## Goal
Make teleconsultation feel like a normal clinical action, not a networking tool.

The dentist and patient must never see STUN/TURN/SDP/ICE/WebRTC jargon.

## Success
- explicit user action before camera/microphone permission;
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

## Reference / mockup

### Patient — idle

┌─────────────────────────────────┐
│  ◉ Téléconsultation             │
│  Consultation vidéo             │
│  La caméra et le microphone     │
│  ne s’activent qu’après votre   │
│  action.                        │
│                                 │
│  Aucune téléconsultation        │
│  en attente                     │
└─────────────────────────────────┘

### Patient — available

┌─────────────────────────────────┐
│  Téléconsultation               │
│  Consultation vidéo             │
│                                 │
│  Prête à rejoindre      [Join]  │
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
- Rejoindre
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
