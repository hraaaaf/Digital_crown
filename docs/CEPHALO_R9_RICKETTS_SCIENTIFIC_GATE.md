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
- Unité : degré ; calibration non requise ; invariance miroir requise.
- Sources : Ricketts 1960 DOI `10.1016/0002-9416(60)90047-6` ; Ricketts 1981 DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

## ACTIVE — E-line Ls / Li

- Method IDs : `RICKETTS_E_LINE_LS_MM_V1`, `RICKETTS_E_LINE_LI_MM_V1`.
- Constructions : `RICKETTS_E_LINE_LS_V1`, `RICKETTS_E_LINE_LI_V1`.
- Landmarks : `Prn`, `Pog_soft`, `Ls_soft` / `Li_soft`; `Po`, `Or` servent uniquement à orienter anatomiquement le signe.
- Définition : E-line entre Pronasale et Pogonion cutané ; distance perpendiculaire du point labial à cette droite.
- Signe : positif en avant/antérieur de l'E-line, négatif en arrière/postérieur.
- Convention numérique : magnitude = plus courte distance point-droite ; signe déterminé par le produit scalaire du résidu perpendiculaire avec l'axe antérieur `Po -> Or`. Cette convention ne modifie pas la magnitude et rend le signe invariant au miroir et à la rotation rigide.
- Unité : mm ; calibration requise.
- Landmark contract : `docs/SRPOSE38_LANDMARK_CONTRACT.md` certifie l'ordre/noms SRPose38 après l'intégration runtime, notamment Upper/Lower Lip, Soft Tissue Pogonion et Pronasale.
- Sources : Ricketts 1968 DOI `10.1016/S0002-9416(68)90278-9` ; Lepi et al. 2023 DOI `10.2174/0118742106268751231010073305` ; définitions soft-tissue recoupées dans la littérature clinique peer-reviewed.
- Le legacy `Ligne_E_Ls/Li` est uniquement une cible de parité secondaire, jamais l'autorité scientifique.

## BLOCKED — Facial Axis

- Candidate : `RICKETTS_FACIAL_AXIS_DEG_V1`, `Ba-N` avec `Pt-Gn`.
- État : `BLOCKED_LANDMARK_CONVENTION`.
- `PT_point` n'est plus le blocage : le contrat SRPose38 certifie l'index/nomenclature `PT`, et Ricketts définit Pt au bord inférieur du foramen rotundum.
- Blocage réel : Ricketts utilise un **cephalometric Gnathion construit** par les plans facial et mandibulaire, alors que le `Gn` annoté du dataset correspond au landmark anatomique Gnathion. Leur équivalence n'est pas source-certifiée.
- Règle : aucun alias silencieux `Gn -> constructed Ricketts Gn`, aucun proxy.

## BLOCKED — Convexity of Point A

- Candidate : `RICKETTS_CONVEXITY_A_NPOG_MM_V1`.
- État : `BLOCKED_GEOMETRIC_CONVENTION`.
- Motif : les sources concordent sur `A` par rapport au plan facial `N-Pog`, mais divergent sur l'opération exacte : mesure parallèle à Frankfort dans une littérature méthodologique versus plus courte distance point-droite/perpendiculaire dans d'autres implémentations publiées.
- Règle : ne pas choisir arbitrairement une géométrie ni un signe sans verrou source primaire explicite.

## Invariants R9

- Fail-closed si landmark manquant/indisponible, image source croisée, géométrie dégénérée, calibration incohérente ou valeur non finie.
- Création, édition, calibration manuelle, calibration AUTO_VERIFIED, nouvelle édition et read path doivent conserver une chaîne active cohérente.
- Pas de norme, classification, diagnostic, croissance ou traitement dans ce lot.
- Pas de LLM. Pas de déploiement Vercel.
- Une mesure bloquée reste absente du runtime jusqu'à levée explicite du gate par preuve source + tests.
