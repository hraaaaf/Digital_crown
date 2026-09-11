# Céphalométrie R8 — McNamara scientific gate

Date: 2026-09-11

## Sources vérifiées
1. McNamara JA Jr. A method of cephalometric evaluation. Am J Orthod. 1984;86(6):449-469. DOI: `10.1016/S0002-9416(84)90352-X`.
2. Corroboration peer-reviewed moderne: inventaire McNamara comprenant A-N perpendicular, Co-A, Co-Gn, ANS-Me/LAFH et Pog-N perpendicular.

## Landmarks repo vérifiés
SRPose38 expose `Co`, `A`, `Gn`, `ANS`, `Me`, `Pog`, `N`, `Po`, `Or`.

La nomenclature SRPose38 reste un gate clinique séparé; R8 ne doit pas élargir ce qui n'est pas nécessaire au sous-ensemble ci-dessous.

## Mesures immédiatement implémentables
### MCNAMARA_CO_A_MM_V1 — IMPLEMENTABLE
- distance euclidienne Co-A;
- calibration requise;
- source image unique;
- fail-closed si landmark/calibration absent ou géométrie invalide.

### MCNAMARA_CO_GN_MM_V1 — IMPLEMENTABLE
- distance euclidienne Co-Gn;
- calibration requise;
- source image unique;
- fail-closed.

### MCNAMARA_ANS_ME_MM_V1 — IMPLEMENTABLE
- distance euclidienne ANS-Me;
- calibration requise;
- source image unique;
- fail-closed.

## Nasion perpendicular
### MCNAMARA_A_NPERP_MM_V1 — GEOMETRY_IMPLEMENTABLE / SIGN_SOURCE_LOCK_REQUIRED
- géométrie: distance AP de A à la ligne passant par N et perpendiculaire à Frankfort Po-Or;
- calibration requise;
- le repo possède déjà `nasion_vertical_offset_mm_v1`, orienté selon Po->Or et positif vers l'antérieur;
- une convention positive antérieure / négative postérieure est cohérente avec les références modernes consultées;
- avant activation, verrouiller cette convention avec une source clinique suffisamment autoritative et l'inscrire dans le contrat McNamara source-spécifique.

### MCNAMARA_POG_NPERP_MM_V1 — GEOMETRY_IMPLEMENTABLE / SIGN_SOURCE_LOCK_REQUIRED
- même construction N-perpendicular, cible Pog;
- calibration requise;
- même gate de signe.

## Réutilisation / non-duplication
### Mandibular plane angle
La géométrie FH vs Go-Me est déjà versionnée en R6 par `TWEED_FMA_DEG_V1`. R8 ne doit pas créer une seconde valeur numérique divergente sans preuve d'une convention McNamara distincte.

### Client projections
`CephaloEngine.calculate_metrics(..., mcnamara_projections=...)` conserve l'argument uniquement pour compatibilité puis l'ignore explicitement. Aucune projection dérivée côté client ne doit devenir autorité R8.

## Différé
- maxillo-mandibular differential: calcul dérivé uniquement après certification séparée de Co-A et Co-Gn;
- mesures dentaires: point/surface incisive exact à source-locker;
- airway: landmarks pharyngés non certifiés/versionnés dans SRPose38 actuel;
- normes âge/sexe, classification, diagnostic, croissance et traitement: hors scope.

## Gate d'implémentation
1. implémenter d'abord Co-A, Co-Gn, ANS-Me;
2. versionner une primitive de distance linéaire source-bound si aucune primitive existante n'est adéquate;
3. adapter evidence typée `analysis_id=MCNAMARA`;
4. prouver calibration requise + fail-closed;
5. intégrer au seam de rematérialisation;
6. prouver création -> edit -> calibration -> nouvel edit -> typed read;
7. ne débloquer A-Nperp/Pog-Nperp qu'après sign source-lock.

## Safety
ZERO LLM. Aucun Vercel. Aucune norme, classification, diagnostic ou traitement activé.
