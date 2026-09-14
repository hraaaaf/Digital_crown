# Céphalométrie R18 — Concordance scientifique et tracés

Statut : **CANDIDAT CLOSEOUT PRÉ-MERGE**. Le produit est certifié sur le HEAD `39660fa45471dbcd8c773148172ec03a854c931f`; R18 ne sera déclaré mergé/clos qu'après CI du commit documentaire, merge #494 et vérification `master` post-merge.

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

Références enregistrées dans le code/audit R18 : DOI `10.1016/S0002-9416(68)90278-9`, PMCID `PMC6007603`, `PMC10973926`, `PMC12569150`.

## Concordance mathématique

Workflow : `Cephalo R18 Scientific Concordance Audit`.

- première preuve source-strict : run `34881504311` / #5, SUCCESS, head `595780ca3f17271a668f04b5a9e226f81303929e` ;
- hard gate : `concordance_certified=true`, 0 divergence / 90 comparaisons ;
- preuve candidate produit finale : run `34889128107` / #19, **SUCCESS**, head `39660fa45471dbcd8c773148172ec03a854c931f`.

Le workflow refuse désormais le succès si `concordance_certified` n'est pas vrai ou si une divergence frontend/backend persiste.

## BEFORE UI figé

Workflow : `Cephalo R18 Tracing BEFORE`.

Référence canonique :
- run `34882384184` / #3 : SUCCESS ;
- product HEAD `26d0aaf7c1b674227de310715ef35ccf27c82c04` ;
- viewports : `390x844`, `768x1024`, `1280x900` ;
- sélecteur d'analyse absent ;
- constructions de plusieurs analyses superposées ;
- zéro overflow horizontal ;
- artefact `10362879498` ;
- digest `sha256:586528cc04dbf3e90ae71ea71e65a89542c48f6cfeeda333adbbf005d3412954`.

Le workflow BEFORE est manuel et pinne ce HEAD afin que la preuve pré-changement ne soit jamais recalculée sur l'UI AFTER.

## Implémentation tracés R18

Le moteur historique est conservé byte-for-byte dans `frontend/src/features/ortho/CephaloTracingLayerBase.tsx`.

`frontend/src/features/ortho/CephaloTracingLayer.tsx` est le contrôleur R18 :
- `Tous` : vue historique complète ;
- `Steiner` : S, N, A, B + axes incisifs nécessaires ;
- `Tweed` : Frankfort, plan mandibulaire, U1/L1 ;
- `McNamara / COM` : Frankfort, N-perpendiculaire, Co-A, Co-Gn, ANS-Me et Wits ;
- `Ricketts` : profil cutané, E-line + constructions dures Ricketts disponibles.

Le filtrage porte aussi sur les landmarks/ghosts, ce qui empêche les constructions legacy non conditionnées de réapparaître dans une autre analyse. Les corrections manuelles d'un sous-ensemble sont fusionnées dans le jeu complet pour ne pas perdre les points masqués.

Le sélecteur est local au viewer R18. Il n'est pas présenté comme synchronisé avec `etape3Data.selectedAnalysis`, dont le contrat clinique ne comporte pas Ricketts dans ce lot.

## AFTER UI final candidat

Workflow : `Cephalo R18 Tracing AFTER`.

Preuve candidate produit :
- run `34889128064` / #7 : **SUCCESS** ;
- HEAD `39660fa45471dbcd8c773148172ec03a854c931f` ;
- artefact `10365503287` ;
- digest `sha256:7dc74cfeb29f18158d817d987fa33345498fc543528b81a1a89d69016146b804` ;
- même fixture déterministe et mêmes viewports 390x844 / 768x1024 / 1280x900 que BEFORE ;
- 15 captures : `Tous / Steiner / Tweed / McNamara-COM / Ricketts` × 3 viewports ;
- `invalidCount=0` ;
- zéro page error, zéro console error, zéro overflow horizontal ;
- aucune construction Ricketts dans Steiner/Tweed/McNamara et séparation structurelle vérifiée ;
- mobile 390 : les cinq analyses sont visibles simultanément, `McNamara / COM` devient `COM` uniquement sous `sm` ;
- correction réelle du conflit tactile entre le badge de calibration et le sélecteur, sans contournement du harness.

### Comparaison visuelle

BEFORE : lecture globale dense, plusieurs familles géométriques superposées, aucune sélection d'analyse.

AFTER : chaque analyse devient une scène scientifique distincte ; le profil cutané/E-line reste propre à Ricketts, les constructions McNamara/Wits à COM, et Steiner/Tweed ne traînent plus les constructions étrangères. Le mode `Tous` conserve volontairement la vue globale.

**Score visuel/HFE après inspection réelle : 9,4/10.** La lisibilité et le contrôle clinique sont nettement améliorés sur 390/768/1280. Le mode `Tous` reste volontairement dense et n'est pas la vue de lecture clinique principale.

## Certifications candidate produit

Sur `39660fa45471dbcd8c773148172ec03a854c931f` :

- Scientific Concordance #19 : **SUCCESS** ;
- R18 Tracing AFTER #7 : **SUCCESS** ;
- T2 Runtime Browser #2992 : **SUCCESS** ;
- PostgreSQL #507 : **SUCCESS** ;
- Cephalo R15 AFTER #86 : **SUCCESS** ;
- Cephalo R15bis AFTER #47 : **SUCCESS** ;
- M6-I #1792 : **SKIPPED**, normal pour ce scope ;
- CI générale #4081 était encore en cours avant le commit documentaire de closeout. La CI du HEAD documentaire devient l'autorité finale pré-merge.

## Git

Repo : `hraaaaf/Digital_crown`

Branche : `fix/cephalo-r18-source-strict-concordance`

PR : `#494` — `fix(cephalo): source-strict R18 scientific concordance`

Candidate produit : `39660fa45471dbcd8c773148172ec03a854c931f`.

Master observé avant le commit documentaire : `4cfa04d651a47fa0cc2c60482e5ff5729148fb86`. Le drift ne touchait pas la céphalométrie et PR #494 était `mergeable=true`, sans commentaires/review threads.

## Limites explicites

- `RICKETTS_FACIAL_AXIS_DEG_V1` reste bloqué sans source-lock de sa convention de landmarks.
- Les linéaires Steiner U1-NA/L1-NB restent indisponibles tant que le landmark coronaire requis n'existe pas.
- Le sélecteur de tracé reste local au viewer ; l'unification avec le sélecteur Step 3 nécessitera un contrat explicite séparé si elle devient souhaitée.
- Aucun diagnostic, norme ou traitement nouveau n'est introduit par R18.
- Aucun déploiement Vercel.

## Closeout restant

1. certifier le HEAD documentaire ;
2. vérifier PR #494 / master / reviews ;
3. merger #494 ;
4. vérifier master post-merge exact ;
5. enregistrer le SHA de merge réel dans le closeout documentaire si nécessaire ;
6. R19 = fenêtre procédurale suivante uniquement, sans feature pré-planifiée.

## Fichier de reprise suivant

`docs/handovers/2026-09-14-cephalo-r18-final-handover.md`
