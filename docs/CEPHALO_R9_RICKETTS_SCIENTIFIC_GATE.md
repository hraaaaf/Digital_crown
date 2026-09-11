# Céphalométrie R9 — gate scientifique Ricketts / tissus mous

Date du gate : 2026-09-12

## Goal

Activer les mesures Ricketts dont la définition clinique est suffisamment étayée, en verrouillant explicitement les conventions géométriques lorsque la littérature secondaire diverge. Les choix ci-dessous sont versionnés : aucune convention alternative ne peut être substituée silencieusement.

Aucune norme, interprétation, diagnostic, croissance ou recommandation thérapeutique n'est activé dans R9.

## ACTIVE — Facial Depth

- `RICKETTS_FACIAL_DEPTH_DEG_V1` / `RICKETTS_FACIAL_DEPTH_V1`.
- Landmarks : `Po`, `Or`, `N`, `Pog`.
- Angle entre Frankfort et `N-Pog`; convention numérique `Po -> Or` contre `Pog -> N`, sans rabattement aigu.
- Degrés, sans calibration, miroir-invariant.
- Sources : Ricketts 1960 DOI `10.1016/0002-9416(60)90047-6`; Ricketts 1981 DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

## ACTIVE — Facial Axis

- `RICKETTS_FACIAL_AXIS_DEG_V1` / `RICKETTS_FACIAL_AXIS_V1`.
- Axe : `Ba-N` avec `Pt-Gn_RICKETTS`.
- `Pt` = `PT_point` certifié par le contrat SRPose38.
- `Gn_RICKETTS` est construit, jamais aliasé au `Gn` annoté :
  `intersection(line(N,Pog), line(Go,Me))`.
- Angle non réflexe entre `Ba -> N` et `Pt -> Gn_RICKETTS`.
- Degrés, sans calibration, miroir-invariant.
- Fail-closed si l'intersection des plans facial et mandibulaire n'est pas unique.
- Source primaire : Ricketts RM, *The keystone triad: I. Anatomy, phylogenetics, and clinical references*, Am J Orthod. 1964;50(4):244-264, DOI `10.1016/S0002-9416(64)80003-8`. Ricketts y décrit le Gn clinique « in space » à l'intersection des plans facial et mandibulaire.
- Corroborations : PMCID `PMC12596171` et `PMC11674528`, Facial Axis = `Ba-N` avec `Pt-Gn`.

### Décision Gn

La littérature secondaire mélange Gn anatomique et constructions. R9 supprime l'ambiguïté en matérialisant son propre `Gn_RICKETTS`; aucune équivalence avec le landmark annoté `Gn` n'est supposée.

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
- Sources : Ricketts RM, *Esthetics, environment, and the law of lip relation*, Am J Orthod. 1968;54(4):272-289, DOI `10.1016/S0002-9416(68)90278-9`; PMCID `PMC10973926` mesure explicitement la horizontal lip distance à l'E-plane; PMCID `PMC12569150` définit Ls/Li-E-line comme horizontal distance.
- Le contrat `docs/SRPOSE38_LANDMARK_CONTRACT.md` identifie `Prn`, `Pog_soft`, `Ls_soft`, `Li_soft`.

### Décision E-line

Certaines études calculent la plus courte distance perpendiculaire. R9 retient la distance parallèle à Frankfort parce que plusieurs protocoles 2D explicites la définissent horizontalement, ce qui verrouille l'axe antéro-postérieur. La variante perpendiculaire n'est pas aliasée à ce contrat.

## Contrats actifs R9

1. `RICKETTS_FACIAL_DEPTH_DEG_V1`
2. `RICKETTS_FACIAL_AXIS_DEG_V1`
3. `RICKETTS_CONVEXITY_A_NPOG_MM_V1`
4. `RICKETTS_E_LINE_LS_MM_V1`
5. `RICKETTS_E_LINE_LI_MM_V1`

Les trois familles précédemment bloquées sont donc résolues dans R9 par des conventions versionnées et testées.

## Invariants R9

- Landmark manquant/indisponible → `NOT_COMPUTABLE`.
- Cross-image, non-fini, construction non unique ou géométrie dégénérée → `INVALID`.
- Linéaires : couple cohérent `mm_per_pixel + calibration_ref` obligatoire.
- Angulaires : jamais de calibration.
- Invariance miroir obligatoire.
- Création → édition → calibration manuelle → AUTO_VERIFIED → nouvelle édition → read path doivent conserver une chaîne active cohérente.
- Le legacy `Ligne_E_Ls/Li` n'est jamais une autorité scientifique.
- Pas de norme, diagnostic, croissance, traitement, LLM ou déploiement Vercel dans ce lot.

## Hors périmètre

Les facteurs dépendant de `Xi` restent hors R9 tant que Xi n'est pas disponible comme landmark/construction source-certifiée. Aucun proxy.
