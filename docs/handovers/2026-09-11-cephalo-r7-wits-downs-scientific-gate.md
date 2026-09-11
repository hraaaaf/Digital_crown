# Céphalométrie R7 — Wits / Downs scientific gate

Date: 2026-09-11

## Sources vérifiées
1. Jacobson A. The "Wits" appraisal of jaw disharmony. Am J Orthod. 1975;67(2):125-138. DOI: `10.1016/0002-9416(75)90065-2`.
2. Downs WB. Variations in facial relationships; their significance in treatment and prognosis. Am J Orthod. 1948;34(10):812-840. DOI: `10.1016/0002-9416(48)90015-3`.
3. Corroboration moderne peer-reviewed de l'inventaire Downs: facial angle, angle of convexity, A-B plane angle, mandibular plane angle, Y-axis, occlusal-plane cant, interincisal angle, lower-incisor/occlusal-plane, lower-incisor/mandibular-plane, U1-A-Pog.

## Wits / Jacobson
### WITS_AO_BO_MM_V1 — BLOCKED_LANDMARK_CONVENTION
Définition primaire: projections perpendiculaires de A et B sur le plan occlusal, puis distance AO-BO mesurée le long de ce plan.

Le plan occlusal fonctionnel n'est pas encore défini par une paire de landmarks SRPose38 scientifiquement certifiée/versionnée. Les alias runtime `Occ_Ant` / `Occ_Post` ne suffisent pas comme evidence source-bound.

Aucune implémentation Wits n'est autorisée tant que ce gate n'est pas levé.

## Downs — sous-ensemble implémentable
### DOWNS_FACIAL_ANGLE_V1 — IMPLEMENTABLE
- géométrie: angle entre N-Pog et Frankfort Po-Or;
- landmarks: N, Pog, Po, Or;
- calibration: non requise;
- orientation/signature à verrouiller par source + runtime éventuel.

### DOWNS_CONVEXITY_ANGLE_V1 — IMPLEMENTABLE
- géométrie: angle N-A-Pog / angle entre N-A et A-Pog;
- landmarks: N, A, Pog;
- calibration: non requise;
- signature clinique à versionner explicitement; ne pas réduire silencieusement à un angle absolu si la source exige un signe.

### DOWNS_AB_PLANE_ANGLE_V1 — IMPLEMENTABLE
- géométrie: angle entre la ligne A-B et N-Pog;
- landmarks: A, B, N, Pog;
- calibration: non requise;
- convention signée à vérifier avant activation.

### DOWNS_Y_AXIS_V1 — IMPLEMENTABLE
- géométrie: S-Gn vs Frankfort Po-Or;
- landmarks: S, Gn, Po, Or;
- calibration: non requise.

## Downs — géométries déjà couvertes par contrats existants
### Mandibular plane angle / MP-FH
Même géométrie de base que FMA: Go-Me vs Po-Or. R6 expose déjà `TWEED_FMA_DEG_V1` avec parité runtime `Angle_de_Tweed`.

R7 ne doit pas créer une seconde source de vérité numérique sans justification. Le besoin éventuel d'un alias/profil Downs doit rester un mapping sémantique, pas un calcul divergent.

### Interincisal angle
Déjà versionné en R4 via `CRANIOM_INTERINCISAL_DEG_V1` et parité runtime `Inter_Incisif`.

### Lower incisor / mandibular plane angle
La géométrie L1 vs Go-Me est déjà couverte en R6 par `TWEED_IMPA_DEG_V1`. Toute représentation Downs doit réutiliser ce contrat ou prouver une convention distincte.

## Downs — bloqué par le plan occlusal
### DOWNS_OCCLUSAL_PLANE_FH_V1 — BLOCKED_LANDMARK_CONVENTION
Plan occlusal vs Frankfort.

### DOWNS_L1_OCCLUSAL_PLANE_V1 — BLOCKED_LANDMARK_CONVENTION
Axe L1 vs plan occlusal.

Même blocker que Wits: absence d'une convention occlusale SRPose38 certifiée/versionnée.

## Downs — linéaire à ne pas activer encore
### DOWNS_U1_APOG_MM_V1 — BLOCKED_SOURCE_LANDMARK_CONVENTION
La mesure linéaire U1 vers A-Pog nécessite de verrouiller le point dentaire exact utilisé par la source et la convention de distance signée. Ne pas substituer automatiquement `U1_incisal` sans source/versioning dédiés.

## Next exact R7
1. vérifier signe/orientation primaire de Facial Angle, Convexity, AB Plane et Y-axis avec une seconde source fiable;
2. auditer les champs runtime existants correspondant à ces quatre mesures;
3. implémenter uniquement ce sous-ensemble non ambigu;
4. réutiliser FMA/interincisal/IMPA au lieu de dupliquer les calculs;
5. garder Wits + mesures occlusales bloqués;
6. tests fail-closed + transitions + CI/T2 exact-head.

## Safety
ZERO LLM. Aucun Vercel. Aucune norme, classification, diagnostic ou traitement activé.
