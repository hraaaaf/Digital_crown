# PC-00 Patient Companion — UI Target Reference

Reference status: TARGET BEFORE AFTER-CAPTURE

## 360×800 / 390×844 — Welcome

┌──────────────────────────────────┐
│ Digital Crown                    │
│ Patient Companion                │
│                                  │
│ Vos informations restent dans    │
│ votre cabinet et sur cet appareil│
│                                  │
│ ┌──────────────────────────────┐ │
│ │ Appairer ce téléphone        │ │
│ │ QR unique du cabinet         │ │
│ │                              │ │
│ │ [ Scanner le QR ]            │ │
│ │ -------- ou --------         │ │
│ │ [ CODE-MANUEL       ]        │ │
│ │ [ Appairer avec le code ]    │ │
│ │                              │ │
│ │ QR/code = 1 usage, expirant  │ │
│ └──────────────────────────────┘ │
└──────────────────────────────────┘

## Home

┌──────────────────────────────────┐
│ Digital Crown                    │
│ Patient Companion                │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ Mon espace                   │ │
│ │ PRENOM NOM                   │ │
│ │ Patient / Parent / Tuteur    │ │
│ │                              │ │
│ │ ✓ Coffre local actif         │ │
│ └──────────────────────────────┘ │
│                                  │
│ [ Mes rendez-vous ] [ Mes docs ]│
│      PC-01              PC-01    │
│                                  │
│ [Ajouter dossier] [Effacer tél.]│
└──────────────────────────────────┘

## Visual rules

- inherit Digital Crown tokens; no new brand system;
- mobile-first, safe-area aware;
- no staff navigation, accounting, clinical tools or admin controls;
- no false enabled features;
- primary trust message = local-first;
- destructive erase action visually separate;
- touch targets >= 48 px;
- no QR secret displayed after pairing.
