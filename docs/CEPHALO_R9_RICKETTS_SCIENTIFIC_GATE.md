# Céphalométrie R9 — gate scientifique Ricketts / tissus mous

Date du gate : 2026-09-12

## Goal

Activer les mesures Ricketts dont la définition clinique **et les landmarks runtime** sont suffisamment étayés, en verrouillant explicitement les conventions géométriques lorsque la littérature secondaire diverge. Aucune convention alternative ne peut être substituée silencieusement.

Aucune norme, interprétation, diagnostic, croissance ou recommandation thérapeutique n'est activé dans R9.

## ACTIVE — Facial Depth

- `RICKETTS_FACIAL_DEPTH_DEG_V1` / `RICKETTS_FACIAL_DEPTH_V1`.
- Landmarks : `Po`, `Or`, `N`, `Pog`.
- Angle entre Frankfort et `N-Pog`; convention numérique `Po -> Or` contre `Pog -> N`, sans rabattement aigu.
- Degrés, sans calibration, miroir-invariant.
- Sources : Ricketts 1960 DOI `10.1016/0002-9416(60)90047-6`; Ricketts 1981 DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

## BLOCKED — Facial Axis

- Candidat : `RICKETTS_FACIAL_AXIS_DEG_V1` / `RICKETTS_FACIAL_AXIS_V1`.
- Définition scientifique : axe `Ba-N` avec `Pt-Gn_RICKETTS`.
- Ricketts définit son `Pt` au bord inférieur du foramen rotundum, à la racine des lames ptérygoïdes / paroi postérieure de la fissure ptérygomaxillaire.
- Le dataset CL-Detection/SRPose38 expose un landmark #28 nommé `PT`, distinct de `Ptm`, mais les sources publiques actuellement verrouillées ne donnent pas une définition anatomique assez explicite du #28 pour prouver son identité avec le `Pt` exact de Ricketts.
- `PT_point` runtime ne peut donc pas être aliasé à Ricketts `Pt` sur le seul nom du landmark.
- État : `BLOCKED_LANDMARK_CONVENTION`.
- Aucun MeasurementEvidence / ConstructionEvidence Facial Axis n'est matérialisé dans R9.
- La géométrie pure `Gn_RICKETTS` / angle Facial Axis peut rester testée comme primitive non activée afin de permettre un futur déblocage sans redéfinition silencieuse.
- Référence de définition : Ricketts RM, *Perspectives in the clinical application of cephalometrics. The first fifty years*, Angle Orthod. 1981;51(2):115-150, DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

### Gate de déblocage Facial Axis

Il faudra une source externe traçable du dataset/annotation protocol définissant explicitement CL-Detection #28 `PT` comme le point Ricketts au bord inférieur du foramen rotundum / paroi postérieure de la fissure ptérygomaxillaire. Sans cette preuve : aucun proxy.

## ACTIVE — Convexity of Point A

- `RICKETTS_CONVEXITY_A_NPOG_MM_V1` / `RICKETTS_CONVEXITY_A_NPOG_V1`.
- Landmarks : `A`, `N`, `Pog`; `Po-Or` oriente le signe.
- Convention R9 : plus courte distance **perpendiculaire** de A à la droite infinie `N-Pog`.
- Signe positif antérieur, négatif postérieur selon `Po -> Or`.
- mm, calibration requise, miroir-invariant.
- Sources : Ricketts 1981 DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`; PMCID `PMC3059215` formalise explicitement la « Ricketts Convexity of Point A » comme distance point-droite A à `Nasion-Pogonion`.

### Décision Convexity

Certaines publications secondaires utilisent une mesure AP parallèle à Frankfort. Le contrat `..._V1` retient la distance point-droite perpendiculaire, explicitement publiée comme Ricketts Convexity. La variante FH-parallèle n'est pas aliasée à ce contrat.

## ACTIVE — E-line Ls / Li

- `RICKETTS_E_LINE_LS_MM_V1` / `RICKETTS_E_LINE_LS_V1`.
- `RICKETTS_E_LINE_LI_MM_V1` / `RICKETTS_E_LINE_LI_V1`.
- E-line : `Prn-Pog_soft`; cibles : `Ls_soft` / `Li_soft`.
- Convention R9 : distance **horizontale parallèle à Frankfort** du point labial à l'E-line.
- Direction antérieure : `Po -> Or`; positif en avant, négatif en arrière.
- mm, calibration requise, miroir-invariant.
- Sources : Ricketts RM, *Esthetics, environment, and the law of lip relation*, Am J Orthod. 1968;54(4):272-289, DOI `10.1016/S0002-9416(68)90278-9`; PMCID `PMC10973926` mesure explicitement la horizontal lip distance à l'E-plane; PMCID `PMC12569150` définit Ls/Li-E-line comme horizontal distance. Des protocoles céphalométriques indépendants décrivent également cette distance comme parallèle au plan de Frankfort.
- Le contrat `docs/SRPOSE38_LANDMARK_CONTRACT.md` identifie `Prn`, `Pog_soft`, `Ls_soft`, `Li_soft`.

### Décision E-line

Certaines études calculent la plus courte distance perpendiculaire. R9 retient la distance parallèle à Frankfort parce que plusieurs protocoles 2D explicites la définissent horizontalement / parallèlement à Frankfort, ce qui verrouille l'axe antéro-postérieur. La variante perpendiculaire n'est pas aliasée à ce contrat.

## Contrats actifs R9

1. `RICKETTS_FACIAL_DEPTH_DEG_V1`
2. `RICKETTS_CONVEXITY_A_NPOG_MM_V1`
3. `RICKETTS_E_LINE_LS_MM_V1`
4. `RICKETTS_E_LINE_LI_MM_V1`

## Contrats bloqués R9

1. `RICKETTS_FACIAL_AXIS_DEG_V1` — `BLOCKED_LANDMARK_CONVENTION` (`PT_point`).
2. Mesures dépendantes de `Xi` — `BLOCKED_LANDMARK` tant que Xi n'est pas disponible comme landmark/construction source-certifiée.

## Invariants R9

- Landmark manquant/indisponible → `NOT_COMPUTABLE`.
- Cross-image, non-fini, construction non unique ou géométrie dégénérée → `INVALID`.
- Linéaires : couple cohérent `mm_per_pixel + calibration_ref` obligatoire.
- Angulaires : jamais de calibration.
- Invariance miroir obligatoire.
- Création → édition → calibration manuelle → AUTO_VERIFIED → nouvelle édition → read path doivent conserver une chaîne active cohérente.
- Le legacy `Ligne_E_Ls/Li` n'est jamais une autorité scientifique.
- Pas de norme, diagnostic, croissance, traitement, LLM ou déploiement Vercel dans ce lot.
