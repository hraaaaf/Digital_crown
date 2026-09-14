# Céphalométrie R18 — Concordance scientifique et tracés

Statut : EN COURS — ne pas déclarer CLOSE tant que CI générale, AFTER visuel, comparaison BEFORE/AFTER et merge ne sont pas prouvés.

## Goal

Faire coïncider, pour une même téléradiographie et les mêmes landmarks :

1. la convention scientifique versionnée ;
2. le calcul backend de production ;
3. le calcul frontend clinique ;
4. la construction graphique visible ;
5. la preuve d'audit reproductible.

Succès observable : zéro divergence R18 sur les golden cases, tracés filtrés par analyse aux viewports 390x844 / 768x1024 / 1280x900, CI générale verte, PR mergée et master revérifié.

## Décisions R18 source-strict

- Les angles de rayons/axes sont calculés par produit scalaire + `acos`, avec fail-closed sur géométrie dégénérée. Le `% 180` sur des angles `atan2` n'est plus une autorité géométrique.
- Steiner U1/NA et L1/NB sont des angles d'axes. Les distances U1-NA / L1-NB en mm ne sont pas fabriquées à partir du bord incisif : elles restent `NOT_COMPUTABLE` tant que le landmark coronaire nécessaire n'est pas disponible.
- Les conventions CRANIOM qui demandent explicitement un angle obtus conservent leur supplément clinique après calcul robuste de l'angle de base.
- Ricketts E-line V1 historique reste lisible. Les nouvelles preuves utilisent V2 = distance perpendiculaire la plus courte à la E-line ; le plan de Frankfort sert au signe/orientation, pas comme direction de mesure.
- Les IDs de preuve E-line sont versionnés `RICKETTS_E_LINE_*_MM_V2`. Les snapshots V1 ne sont pas réécrits rétroactivement.
- `RICKETTS_FACIAL_AXIS_DEG_V1` reste bloqué tant que sa convention de landmarks n'est pas source-lockée ; R18 ne l'invente pas.

## Concordance mathématique

Workflow : `Cephalo R18 Scientific Concordance Audit`.

Première preuve source-strict : run `34881504311` / #5, SUCCESS, head `595780ca3f17271a668f04b5a9e226f81303929e`.

Le workflow a été durci : son succès exige `concordance_certified=true` et zéro divergence frontend/backend. Les exécutions suivantes sur la branche doivent rester vertes avant closeout.

## BEFORE UI figé

Workflow : `Cephalo R18 Tracing BEFORE`.

Référence canonique :
- run `34882384184` / #3 : SUCCESS ;
- product HEAD `26d0aaf7c1b674227de310715ef35ccf27c82c04` ;
- viewports : `390x844`, `768x1024`, `1280x900` ;
- sélecteur d'analyse absent ;
- zéro overflow horizontal ;
- artefact `10362879498` ;
- digest `sha256:586528cc04dbf3e90ae71ea71e65a89542c48f6cfeeda333adbbf005d3412954`.

Le workflow BEFORE est ensuite passé en `workflow_dispatch` et pinne ce HEAD afin que la preuve pré-changement ne soit pas recalculée sur l'UI AFTER.

## Implémentation tracés R18

Le moteur historique est conservé byte-for-byte dans `frontend/src/features/ortho/CephaloTracingLayerBase.tsx`.

`frontend/src/features/ortho/CephaloTracingLayer.tsx` devient le contrôleur R18 :
- `Tous` : vue historique complète ;
- `Steiner` : S, N, A, B + axes incisifs nécessaires ;
- `Tweed` : Frankfort, plan mandibulaire, U1/L1 ;
- `McNamara / COM` : Frankfort, N-perpendiculaire, Co-A, Co-Gn, ANS-Me et Wits ;
- `Ricketts` : profil cutané, E-line + constructions dures Ricketts disponibles.

Le filtrage porte aussi sur les landmarks, ce qui empêche les constructions legacy non conditionnées de réapparaître dans une autre analyse. Les corrections manuelles d'un sous-ensemble sont fusionnées dans le jeu complet pour ne pas perdre les points masqués.

## AFTER UI

Workflow : `Cephalo R18 Tracing AFTER`.

Contrat : même fixture déterministe et mêmes trois viewports que BEFORE, avec captures `Tous / Steiner / Tweed / McNamara-COM / Ricketts` et assertions structurelles d'absence de constructions étrangères.

État actuel de ce document : AFTER en cours de certification. Ne pas renseigner de score visuel final avant inspection effective des captures.

## Git

Repo : `hraaaaf/Digital_crown`

Branche : `fix/cephalo-r18-source-strict-concordance`

PR : `#494` — `fix(cephalo): source-strict R18 scientific concordance`

Master observé pendant le chantier : `4cfa04d651a47fa0cc2c60482e5ff5729148fb86`. Le drift depuis la base précédente ne touche que `docs/audits/PRESCRIPTION_INTELLIGENCE_V1.md`, donc aucun conflit céphalométrique observé à ce stade.

## Séquence de closeout

1. AFTER exact-head SUCCESS ;
2. télécharger/inspecter l'artefact AFTER ;
3. comparer BEFORE/AFTER aux mêmes viewports et attribuer un score visuel basé sur preuve ;
4. CI backend/frontend + certifications pertinentes vertes ;
5. mettre à jour ce canonical avec les runs/HEAD finaux ;
6. mettre à jour la PR ;
7. merge ;
8. revérifier master et post-merge ;
9. aucun déploiement Vercel sans autorisation explicite.
