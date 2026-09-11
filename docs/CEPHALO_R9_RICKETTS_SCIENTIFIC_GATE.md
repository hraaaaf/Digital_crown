# Céphalométrie R9 — gate scientifique Ricketts / tissus mous

Date du gate : 2026-09-12

## Goal

N'activer dans le runtime que les mesures Ricketts dont la définition, les landmarks, la géométrie, l'orientation et les unités sont source-verrouillés. Aucune norme, interprétation, diagnostic, croissance ou recommandation thérapeutique n'est activé dans R9.

## ACTIVE — Facial Depth

- Method ID : `RICKETTS_FACIAL_DEPTH_DEG_V1`
- Construction : `RICKETTS_FACIAL_DEPTH_V1`
- Landmarks : `Po`, `Or`, `N`, `Pog`
- Définition : angle postérieur entre le plan de Frankfort et le plan facial N-Pog.
- Convention numérique : vecteur Frankfort `Po -> Or` et vecteur facial postérieur `Pog -> N`, angle dans `[0, 180]` sans rabattement aigu.
- Unité : degré.
- Calibration : non requise.
- Invariance miroir : requise et testée.
- Provenance primaire :
  - Ricketts RM. A foundation for cephalometric communication. Am J Orthod. 1960;46(5):330-357. DOI `10.1016/0002-9416(60)90047-6`.
  - Ricketts RM. Perspectives in the clinical application of cephalometrics. Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

## BLOCKED — Facial Axis

- Candidate : `RICKETTS_FACIAL_AXIS_DEG_V1`, cranial axis `Ba-N` et facial axis `Pt-Gn'`.
- État : `BLOCKED_LANDMARK_CONVENTION`.
- Le contrat `docs/SRPOSE38_LANDMARK_CONTRACT.md` certifie bien les labels `Ba`, `PT_point` et `Gn` du modèle.
- Blocage réel : les sources Ricketts et des études méthodologiques décrivent le Facial Axis avec un **Gnathion construit**. SRPose38 fournit un `Gn` annoté, sans preuve suffisante qu'il soit mathématiquement identique au Gn' requis par Ricketts.
- Les sources secondaires ne sont pas uniformes sur la construction de Gnathion : midpoint Pog-Me dans une publication méthodologique, construction géométrique/bissectrice dans d'autres conventions céphalométriques.
- Règle : aucun alias `Gn -> Gn'` et aucun proxy `Ptm -> Pt` sans contrat géométrique explicite et testé.

Sources de contrôle :
- Ricketts RM. Perspectives in the clinical application of cephalometrics. Angle Orthod. 1981;51(2):115-150.
- Cephalometric Evaluation of Maxillary Incisors Inclination, Facial, and Growth Axes in Different Vertical and Sagittal Patterns. `PMC7402251`.
- Accuracy of computerized automatic identification of cephalometric landmarks by a designed software. `PMC3746488`.

## BLOCKED — Convexity of Point A

- Candidate : `RICKETTS_CONVEXITY_A_NPOG_MM_V1`.
- État : `BLOCKED_GEOMETRIC_CONVENTION`.
- Motif : les sources concordent sur `A` par rapport au plan facial `N-Pog`, mais divergent sur l'opération exacte : distance point-droite perpendiculaire vs mesure linéaire parallèle à Frankfort.
- Règle : ne pas choisir arbitrairement une géométrie et ne pas transformer une distance non signée en mesure clinique signée sans source primaire explicite.

## BLOCKED — E-line Ls / Li

- Candidates : `RICKETTS_E_LINE_LS_MM_V1`, `RICKETTS_E_LINE_LI_MM_V1`.
- Landmarks : `Prn`, `Pog_soft`, `Ls_soft`, `Li_soft` sont bien liés par le contrat SRPose38 canonique ; le blocage landmark précédent est levé.
- Définition commune verrouillée : E-line entre Pronasale et Pogonion cutané ; signe clinique `+` en avant et `-` en arrière.
- État : `BLOCKED_GEOMETRIC_CONVENTION`.
- Motif : deux sources méthodologiques récentes divergent sur l'opération exacte. Scientific Reports 2025 définit UL-EP/LL-EP comme distance **horizontale** ; Applied Sciences 2025 décrit Ls/Li-E comme distance à **90°** de l'E-plane.
- Sources : DOI `10.1038/s41598-025-98777-4` et DOI `10.3390/app15179265`, recoupées avec la source primaire Ricketts 1968 DOI `10.1016/S0002-9416(68)90278-9`.
- Règle : aucune fonction de distance E-line n'est active tant que la convention géométrique canonique n'est pas rattachée sans ambiguïté à la méthode choisie. Le legacy `Ligne_E_Ls/Li` pourra servir plus tard à la parité, jamais comme autorité scientifique.

## Invariants R9

- Fail-closed si landmark manquant/indisponible, image source croisée, géométrie dégénérée ou valeur non finie.
- Pas de norme ou classification dans ce lot.
- Pas de LLM.
- Pas de déploiement Vercel.
- Une mesure bloquée reste absente du runtime jusqu'à levée explicite du gate par preuve source + tests.
