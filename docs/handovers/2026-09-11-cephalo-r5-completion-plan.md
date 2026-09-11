# Céphalométrie R5 — Steiner completion plan

Date: 2026-09-11

## Goal
Clore R5 Steiner uniquement avec des géométries source-bound, versionnées, fail-closed et compatibles avec le contrat de landmarks certifié. Aucun substitut implicite n’est autorisé pour une mesure bloquée.

## Déjà fusionné via PR #417
- SNA / SNB / ANB.
- U1-NA° / L1-NB°.
- parité runtime stricte pour SNA/SNB/ANB.
- ANB suit exactement l’ordre du runtime historique: SNA et SNB sont arrondis individuellement à 0,1°, puis soustraits.
- angles dentaires orientation-invariant.
- préservation après calibration manuelle / auto et rematérialisation après édition des landmarks.
- aucune norme, classification, diagnostic, croissance ou traitement.

Merge #417: `b1c36bfb6a57b25c6ae290fdb0dd690d8f5d0b70`.

## Scope R5 restant vérifié
### SN-MP — IMPLEMENTABLE / PR #420 EN CERTIFICATION
- définition retenue: angle minimal entre S-N et le plan mandibulaire Go-Gn.
- sources Steiner 1953 et 1959 concordantes.
- landmarks S, N, Go, Gn disponibles dans le contrat SRPose38.
- versionné comme géométrie patient, calibration-independent, fail-closed missing / degenerate / cross-image.
- implémentation actuelle: `STEINER_SN_MP_V1` / `STEINER_SN_MP_DEG_V1` dans l’adapter squelettique Steiner existant.
- la création runtime l’inclut automatiquement; les edits de landmarks le rematérialisent; les transitions de calibration le préservent car `requires_calibration=False`.
- aucune duplication de champ runtime legacy.

### SN-OP — BLOCKED_LANDMARK_CONVENTION
La mesure plan occlusal / S-N est scientifiquement supportée. La littérature définit le plan occlusal à partir de la relation molaire et incisive. SRPose38 contient des identifiants `U6`, `L6` et incisifs, mais le code source indique explicitement que la validation clinique de cette nomenclature constitue un gate scientifique distinct. Aucun point `U6/L6` n’est donc promu silencieusement en cuspide occlusale certifiée et aucun `Occ_Ant` / `Occ_Post` n’est inventé.

### Steiner S-line — BLOCKED_LANDMARK_CONVENTION
SRPose38 contient `Sn_soft`, `Prn`, `Pog_soft`, `Ls_soft` et `Li_soft`. Le blocage n’est donc pas l’absence brute des points. Il reste à versionner et sourcer précisément la construction de la S-line, notamment le point de départ sur la courbe S entre subnasale et pronasale, ainsi que la convention de distance signée et son comportement en cas d’image miroir. Aucun midpoint ou signe clinique n’est activé par approximation.

### U1-NA mm / L1-NB mm — BLOCKED_LANDMARK_CONVENTION
La source Steiner primaire utilise le point coronaire le plus mésial. Le landmark incisal actuel ne le remplace pas silencieusement. Une convention landmark séparément sourcée et versionnée est requise avant activation.

## Double-check obligatoire R5 et suivants
Pour chaque mesure céphalométrique:
1. gate scientifique: définition, landmarks, géométrie, source primaire + corroboration;
2. gate runtime: formule réelle, orientation des axes, unités, arrondis, ordre des opérations et transitions;
3. test comportemental sur plusieurs états successifs, pas seulement une fixture statique;
4. fail-closed missing / degenerate / cross-image;
5. aucune tolérance élargie pour masquer une divergence numérique.

## Séquence de clôture
1. terminer la certification exact-head de PR #420;
2. si CI/T2 verts et master inchangé, fusionner SN-MP avec garde sur le SHA exact;
3. mettre à jour le scientific gate R5 avec SN-MP actif et les blockers ci-dessus;
4. fusionner le closeout R4 déjà préparé;
5. créer et fusionner le closeout R5 / handover vers R6 Tweed-Merrifield;
6. seulement ensuite reprendre les merges du chantier Media Core.

## Safety
ZERO LLM. Aucun Vercel. Aucun score clinique/norme/diagnostic/traitement activé.
