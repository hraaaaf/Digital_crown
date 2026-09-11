# Céphalométrie R8 — McNamara handover

Date: 2026-09-11

## Goal
Versionner un sous-ensemble McNamara strictement source-bound, fail-closed et audit-ready, sans normes, classification, diagnostic, croissance projetée ni traitement.

## Base vérifiée
- master après R7: `3439e7b2927c624c039084c122fe6ecd0fedf0a2`.
- R7 PR #425: merge après CI #3368 SUCCESS et T2 #2354 SUCCESS.
- ZERO LLM. Aucun Vercel.

## Sources scientifiques vérifiées
1. McNamara JA Jr. A method of cephalometric evaluation. Am J Orthod. 1984;86(6):449-469. DOI: `10.1016/S0002-9416(84)90352-X`.
2. Corroboration peer-reviewed moderne de l'inventaire McNamara: A-N perpendicular, Co-A, Co-Gn, ANS-Me/LAFH et Pog-N perpendicular sont décrits comme variables McNamara.

## Audit repo initial
SRPose38 expose les landmarks utiles suivants: `Co`, `A`, `Gn`, `ANS`, `Me`, `Pog`, `N`, `Po`, `Or`.

Le runtime `CephaloEngine` accepte encore un argument `mcnamara_projections` pour compatibilité mais le supprime explicitement avant calcul. Une projection dérivée côté client ne doit donc jamais devenir source de vérité clinique.

Le repo possède déjà `nasion_vertical_offset_mm_v1`, distance AP signée par rapport à la ligne passant par N et perpendiculaire à Frankfort, orientée selon l'axe anatomique Po->Or. Cette primitive peut être réutilisée seulement après vérification de parité avec la convention McNamara; le contrat McNamara doit rester source-spécifique.

## Sous-ensemble R8 candidat
### MCNAMARA_A_NPERP_MM_V1
- A vers N-perpendicular;
- landmarks: A, N, Po, Or;
- unité: mm;
- calibration requise;
- signe antérieur/postérieur à verrouiller explicitement.

### MCNAMARA_POG_NPERP_MM_V1
- Pog vers N-perpendicular;
- landmarks: Pog, N, Po, Or;
- unité: mm;
- calibration requise;
- même convention anatomique de signe à versionner.

### MCNAMARA_CO_A_MM_V1
- longueur effective maxillaire Co-A;
- landmarks: Co, A;
- unité: mm;
- calibration requise.

### MCNAMARA_CO_GN_MM_V1
- longueur effective mandibulaire Co-Gn;
- landmarks: Co, Gn;
- unité: mm;
- calibration requise.

### MCNAMARA_ANS_ME_MM_V1
- hauteur faciale antérieure inférieure ANS-Me;
- landmarks: ANS, Me;
- unité: mm;
- calibration requise.

## Hors scope initial
- normes selon âge/sexe;
- maxillo-mandibular differential tant que Co-A et Co-Gn ne sont pas d'abord versionnés séparément;
- mesures dentaires nécessitant la surface faciale exacte d'une incisive;
- voies aériennes tant que les landmarks pharyngés ne sont pas certifiés/versionnés;
- toute interprétation clinique automatique.

## Double-check obligatoire R8
1. source primaire + corroboration indépendante;
2. définition exacte et landmarks;
3. signe/orientation pour N-perpendicular;
4. calibration et unité;
5. audit runtime legacy + arrondi/opérations;
6. fail-closed missing / degenerate / cross-image;
7. création -> edit -> calibration -> nouvel edit -> read path;
8. aucune norme/diagnostic/traitement.

## Next exact
1. écrire le scientific gate R8 avec les cinq mesures candidates;
2. auditer les primitives de distance euclidienne et N-perpendicular existantes;
3. implémenter une géométrie McNamara source-spécifique minimale;
4. adapter evidence typée `analysis_id=MCNAMARA`;
5. intégrer au seam de rematérialisation sans modifier le moteur legacy;
6. tests ciblés + multi-états + CI/T2 exact-head.
