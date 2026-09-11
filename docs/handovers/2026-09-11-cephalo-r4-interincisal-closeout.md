# Céphalométrie R4 — Inter-incisif closeout

Date: 2026-09-11

## Goal
Certifier l’angle inter-incisif CRANIOM à partir des axes dentaires versionnés, sans norme, diagnostic ni traitement, avec parité stricte au runtime existant et comportement fail-closed.

## État vérifié
- PR #413 fusionnée.
- HEAD exact certifié avant fusion: `3ce931d624cd520e2addc5db434eeb5806138141`.
- CI #3296 / run `34618235047`: SUCCESS.
- T2 #2291 / run `34618235088`: SUCCESS.
- squash merge sur master: `f5b3a688634d600afedc2ab32c7468235eca586a`.

## Contrat scientifique/runtime
- construction: `CRANIOM_INTERINCISAL_ANGLE_V1`.
- mesure: `CRANIOM_INTERINCISAL_DEG_V1`.
- alias versionné: `CRANIOM_U1_L1_INTERINCISAL_V1`.
- axe U1: apex -> incisal.
- axe L1: apex -> incisal.
- parité stricte avec le champ runtime historique `Inter_Incisif`.
- unité: degré.
- aucune calibration requise.
- missing / géométrie dégénérée / cross-image: fail-closed.
- aucune norme, interprétation, classification, diagnostic ou proposition thérapeutique activée.

## Résiduels R4 explicitement non masqués
- overjet / overbite: `BLOCKED_SOURCE_FRAME`.
- Stomion: `BLOCKED_LANDMARK`.
- A''B'' NHP / horizontal gaze: `BLOCKED_PROTOCOL`.
- forme mandibulaire Ar.Gs / Gi.Me: `BLOCKED_LANDMARK`.
- CRANIOM SN / mandibular plane: `BLOCKED_SOURCE_GEOMETRY`.

Ces blocages sont des limites scientifiques/données explicites et ne sont pas substitués par des approximations.

## Safety
ZERO LLM. Aucun changement Vercel. Aucun élargissement à des normes, diagnostics ou traitements.
