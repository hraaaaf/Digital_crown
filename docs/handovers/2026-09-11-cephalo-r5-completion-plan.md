# Céphalométrie R5 — Steiner completion plan

Date: 2026-09-11

## Goal
Clore R5 Steiner uniquement avec des géométries source-bound, versionnées, fail-closed et compatibles avec le contrat de landmarks certifié. Aucun substitut implicite n’est autorisé pour une mesure bloquée.

## Déjà dans PR #417
- SNA / SNB / ANB.
- U1-NA° / L1-NB°.
- parité runtime stricte pour SNA/SNB/ANB, incluant la convention d’arrondi runtime ANB.
- angles dentaires orientation-invariant.
- préservation après calibration manuelle / auto et rematérialisation après édition des landmarks.
- aucune norme, classification, diagnostic, croissance ou traitement.

## Scope R5 restant vérifié
### SN-MP — IMPLEMENTABLE
- définition retenue: angle minimal entre S-N et le plan mandibulaire Go-Gn.
- sources Steiner 1953 et 1959 concordantes.
- landmarks S, N, Go, Gn disponibles dans le contrat SRPose38.
- doit être versionné comme géométrie patient, calibration-independent, fail-closed missing / degenerate / cross-image.

### SN-OP — BLOCKED_LANDMARK
La mesure plan occlusal / S-N est scientifiquement supportée, mais le contrat SRPose38 certifié ne fournit pas une paire de landmarks occlusaux versionnés permettant de définir le plan sans approximation. Aucun `Occ_Ant` / `Occ_Post` inventé ou dérivé silencieusement.

### Steiner S-line — BLOCKED_SIGN_CONVENTION
La ligne de référence est scientifiquement supportée et les landmarks mous nécessaires existent. L’activation d’une distance signée Ls/Li reste bloquée tant que la convention antérieur/postérieur et le signe clinique ne sont pas explicitement sourcés et versionnés.

### U1-NA mm / L1-NB mm — BLOCKED_LANDMARK_CONVENTION
Le landmark incisal actuel ne remplace pas silencieusement le point coronaire décrit dans la source Steiner primaire.

## Séquence de clôture
1. fusionner #417 uniquement après CI + T2 exact-head verts sur master courant;
2. créer une branche propre depuis le master fusionné;
3. implémenter SN-MP par patch minimal sur le code #417, sans réutiliser les remplacements larges de la branche exploratoire;
4. tests géométrie + evidence + runtime chain + calibration transitions + landmark revision;
5. CI + T2 exact-head;
6. fusionner SN-MP;
7. documenter les trois blockers restants comme limites explicites du R5;
8. créer le closeout R5 et le handover canonique vers R6 Tweed/Merrifield.

## Safety
ZERO LLM. Aucun Vercel. Aucun score clinique/norme/diagnostic/traitement activé.
