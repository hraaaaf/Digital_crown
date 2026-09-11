# Céphalométrie R5 — Steiner closeout / handover R6

Date: 2026-09-11

## Goal R5
Clore l’analyse Steiner avec des géométries patient source-bound, versionnées, fail-closed, sans normes, diagnostic ni traitement.

## État vérifié
### R5 core
- PR #417 fusionnée.
- merge master: `b1c36bfb6a57b25c6ae290fdb0dd690d8f5d0b70`.
- exact-head CI #3349: SUCCESS.
- exact-head T2 #2340: SUCCESS.

### R5 SN-MP completion
- PR #420 fusionnée.
- HEAD exact avant fusion: `eef3b6e70901318c7120882fc8198bf8bd43fd31`.
- exact-head CI #3352 / run `34633757638`: SUCCESS.
- exact-head T2 #2342 / run `34633757692`: SUCCESS.
- squash merge master: `981c721c939cbd01ffcaee43adbfaf5a5f6d3ce8`.

## Mesures Steiner actives
- `STEINER_SNA_DEG_V1`
- `STEINER_SNB_DEG_V1`
- `STEINER_ANB_DEG_V1`
- `STEINER_U1_NA_DEG_V1`
- `STEINER_L1_NB_DEG_V1`
- `STEINER_SN_MP_DEG_V1`

## Invariants certifiés
- SNA/SNB/ANB parity-bound au runtime existant.
- ANB respecte l’ordre runtime réel: arrondir SNA et SNB au dixième puis soustraire.
- U1-NA° / L1-NB° utilisent un angle d’axes non orientés et sont invariants à l’orientation.
- SN-MP = plus petit angle entre S-N et Go-Gn, invariant à l’orientation.
- toutes les mesures R5 actives sont calibration-independent.
- missing / cross-image / géométrie dégénérée: fail-closed.
- les éditions de landmarks rematérialisent les mesures Steiner concernées.
- calibration manuelle / auto préserve les mesures calibration-independent.

## Blockers R5 explicitement reportés
- U1-NA mm / L1-NB mm: `BLOCKED_LANDMARK_CONVENTION`.
- SN-OP: `BLOCKED_LANDMARK_CONVENTION`.
- Steiner S-line signée: `BLOCKED_LANDMARK_CONVENTION`.

Aucun substitut implicite n’est autorisé tant qu’une convention source-bound et versionnée n’est pas adoptée.

## Safety
- ZERO LLM.
- aucune norme activée.
- aucun diagnostic / classification / projection de croissance / traitement activé.
- aucun changement Vercel.

## Handover R6 — Tweed / Merrifield
### Goal
Construire le gate scientifique R6 avant code, puis n’implémenter que les mesures dont la définition, les landmarks, l’orientation, l’arrondi et les transitions sont certifiés.

### Scope attendu à auditer
- FMA.
- IMPA.
- FMIA.
- Merrifield Z-angle.

### Next exact
1. vérifier les sources primaires Tweed/Merrifield et leurs définitions exactes;
2. comparer aux champs runtime déjà existants (`FMA`, `IMPA`, etc.) et inspecter leurs formules/opérations réelles;
3. construire la matrice science/runtime R6;
4. identifier les blockers avant toute implémentation;
5. seulement ensuite créer la branche R6 et les tests comportementaux multi-états.

## Règle de reprise
À l’ouverture d’une nouvelle fenêtre: lire ce fichier, puis vérifier `master`, HEAD, PRs ouvertes et CI avant de poursuivre R6.
