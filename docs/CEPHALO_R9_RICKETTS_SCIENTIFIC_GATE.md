# Céphalométrie R9 — gate scientifique Ricketts / tissus mous

Date du gate : 2026-09-12

## Goal

N'activer dans le runtime que les mesures Ricketts dont la définition, les landmarks, la géométrie, l'orientation et les unités sont source-verrouillés. Aucune norme, interprétation, diagnostic, croissance ou recommandation thérapeutique n'est activé dans R9.

## ACTIVE — Facial Depth

- Method ID : `RICKETTS_FACIAL_DEPTH_DEG_V1`
- Construction : `RICKETTS_FACIAL_DEPTH_V1`
- Landmarks : `Po`, `Or`, `N`, `Pog`
- Définition : angle postérieur entre le plan de Frankfort et le plan facial N-Pog.
- Convention numérique : vecteur Frankfort `Po -> Or` et vecteur facial postérieur `Pog -> N`, angle orienté dans `[0, 180]` sans rabattement aigu.
- Unité : degré.
- Calibration : non requise.
- Invariance miroir : requise et testée.
- Provenance primaire :
  - Ricketts RM. A foundation for cephalometric communication. Am J Orthod. 1960;46(5):330-357. DOI `10.1016/0002-9416(60)90047-6`.
  - Ricketts RM. Perspectives in the clinical application of cephalometrics. Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.
- Corroboration méthodologique : littérature récente décrivant explicitement le Facial Depth comme l'angle postérieur entre `P-Or` et `N-Pog`.

## BLOCKED — Facial Axis

- Candidate : `RICKETTS_FACIAL_AXIS_DEG_V1`, `Ba-N` avec `Pt-Gn`.
- État : `BLOCKED_LANDMARK_CONVENTION`.
- Motif : le runtime expose un label technique `PT_point`, mais le code SRPose38 actuel précise lui-même que la validation clinique de la nomenclature est un gate séparé. Les ressources publiques CL-Detection 2023 vérifiées décrivent 38 indices sans fournir une liaison publique suffisamment probante entre l'index runtime et le Pt de Ricketts.
- Règle : aucun proxy `Ptm`, aucune réutilisation silencieuse de `PT_point`.

## BLOCKED — Convexity of Point A

- Candidate : `RICKETTS_CONVEXITY_A_NPOG_MM_V1`.
- État : `BLOCKED_GEOMETRIC_CONVENTION`.
- Motif : les sources concordent sur `A` par rapport au plan facial `N-Pog`, mais divergent sur l'opération exacte. Une source méthodologique l'exprime comme mesure parallèle à Frankfort, tandis que des publications 3D l'implémentent comme distance point-droite perpendiculaire.
- Règle : ne pas choisir arbitrairement l'une des deux géométries ; ne pas transformer une distance non signée en mesure clinique signée sans source primaire explicite.

## BLOCKED — E-line Ls / Li

- Candidates : `RICKETTS_E_LINE_LS_MM_V1`, `RICKETTS_E_LINE_LI_MM_V1`.
- Définition scientifique verrouillée : E-line entre Pronasale et Pogonion cutané ; distance des lèvres à la ligne. Les études méthodologiques recoupées utilisent `+` en avant de la ligne et `-` en arrière.
- État runtime : `BLOCKED_LANDMARK_CONVENTION`.
- Motif : `Prn`, `Pog_soft`, `Ls_soft`, `Li_soft` existent comme labels techniques dans `SOTA_LANDMARKS_MAPPING`, mais le fichier runtime documente explicitement que la validation clinique de cette nomenclature est un gate séparé. Une ancienne assertion de commit ne remplace pas cette preuve.
- Règle : legacy `Ligne_E_Ls/Li` utilisable plus tard pour parité seulement, jamais comme autorité scientifique.

## Invariants R9

- Fail-closed si landmark manquant/indisponible, image source croisée, géométrie dégénérée ou valeur non finie.
- Pas de norme ou classification dans ce lot.
- Pas de LLM.
- Pas de déploiement Vercel.
- Une mesure bloquée reste absente du runtime jusqu'à levée explicite du gate par preuve source + tests.
