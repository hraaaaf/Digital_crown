# Céphalométrie R18 — concordance source-strict + tracing scientifique

## Goal

Faire de chaque mesure affichée une construction visuellement vérifiable :

`landmarks source → construction versionnée → mesure → rendu du même contrat géométrique`.

La sélection d'une analyse doit limiter le tracé aux points et constructions nécessaires, sans constructions étrangères persistantes à l'écran.

## Succès observable

1. audit frontend/backend R18 : `concordance_certified=true`, 0 divergence ;
2. Steiner : SN, NA, NB + axes incisifs nécessaires, sans McNamara/Ricketts ;
3. Tweed : Frankfort, plan mandibulaire + axes incisifs nécessaires ;
4. COM/McNamara : Frankfort, N-perp et projections A/B + Co-A, Co-Gn, ANS-Me + Wits ;
5. Ricketts : profil cutané + E-line et constructions dures disponibles, sans constructions étrangères ;
6. mode Tous disponible pour inspection globale ;
7. BEFORE/AFTER aux mêmes viewports 390x844, 768x1024, 1280x900 ;
8. aucune overflow, erreur runtime ou egress externe dans le harness visuel ;
9. aucune modification rétroactive de la sémantique Ricketts E-line V1 persistée.

## Preuve mathématique

Première certification source-strict : R18 Scientific Concordance run `34881504311` / #5, HEAD `595780ca3f17271a668f04b5a9e226f81303929e`, SUCCESS avec hard gate, `concordance_certified=true`, 0 divergence sur 90 comparaisons.

Preuve candidate produit finale : run `34889128107` / #19, HEAD `39660fa45471dbcd8c773148172ec03a854c931f`, **SUCCESS**.

Les distances linéaires Steiner U1-NA/L1-NB restent `NOT_COMPUTABLE` automatiquement tant que le landmark coronaire requis n'existe pas ; le bord incisif n'est plus utilisé comme substitut silencieux.

## Contrat Ricketts E-line

- V1 historique : distance parallèle à Frankfort conservée pour lecture des snapshots existants ;
- V2 active : plus courte distance/perpendiculaire du point labial à Prn-Pog', Frankfort servant uniquement à orienter le signe antérieur/postérieur ;
- identifiants de construction et méthode versionnés séparément (`*_V2`).

Références enregistrées dans le code : DOI `10.1016/S0002-9416(68)90278-9`, PMCID `PMC6007603`, `PMC10973926`, `PMC12569150`.

## BEFORE figé

Workflow `Cephalo R18 Tracing BEFORE`, run `34882384184` / #3, SUCCESS, HEAD `26d0aaf7c1b674227de310715ef35ccf27c82c04`.

Viewports : 390x844, 768x1024, 1280x900. Le BEFORE prouve : sélecteur absent, superposition globale non filtrée, zéro overflow horizontal.

Artefact : `10362879498`, digest `sha256:586528cc04dbf3e90ae71ea71e65a89542c48f6cfeeda333adbbf005d3412954`.

Le workflow BEFORE est manuel et pinne ce HEAD ; il ne doit pas être recalculé sur l'UI AFTER.

## Référence d'interaction finale

Sélecteur compact intégré au viewer :

`[ Tous ] [ Steiner ] [ Tweed ] [ McNamara / COM ] [ Ricketts ]`

- desktop/tablette : groupe centré sous les contrôles supérieurs ;
- mobile : groupe placé sous les badges d'état pour empêcher tout conflit tactile ;
- mobile 390 : `McNamara / COM` devient `COM` uniquement visuellement afin que les cinq choix restent simultanément visibles ;
- état actif : tokens existants cyan/sombre ;
- changement immédiat, sans recalcul ni mutation des landmarks ;
- corrections de landmarks d'une vue filtrée fusionnées dans le jeu complet afin de ne jamais perdre les points masqués.

Le sélecteur de tracing est local au viewer R18. `etape3Data.selectedAnalysis` n'est pas étendu à Ricketts dans ce lot afin de ne pas modifier silencieusement le contrat clinique du Step 3. Une unification de ces deux sélections nécessiterait un contrat explicite séparé.

## Architecture

Le moteur historique est conservé byte-for-byte dans `frontend/src/features/ortho/CephaloTracingLayerBase.tsx`.

`frontend/src/features/ortho/CephaloTracingLayer.tsx` est le contrôleur R18 : il filtre landmarks + ghosts par analyse, délègue le rendu historique au moteur Base et ajoute les constructions Ricketts dures/Wits nécessaires.

## AFTER final candidat

Workflow `Cephalo R18 Tracing AFTER`, run `34889128064` / #7, HEAD `39660fa45471dbcd8c773148172ec03a854c931f` : **SUCCESS**.

Artefact : `10365503287`, digest `sha256:7dc74cfeb29f18158d817d987fa33345498fc543528b81a1a89d69016146b804`.

Preuves du rapport :
- `invalidCount=0` ;
- 390x844 / 768x1024 / 1280x900 valides au premier essai ;
- 5 modes valides sur chaque viewport ;
- zéro page error ;
- zéro console error ;
- zéro overflow horizontal ;
- aucune requête externe bloquée ;
- séparation structurelle des constructions par analyse.

Inspection visuelle réelle :
- 390 : cinq onglets visibles simultanément, aucune collision avec le badge calibration ;
- 768 : lecture nette des familles d'analyse, Ricketts conserve le profil cutané ;
- 1280 : séparation clinique nette, le mode Tous garde volontairement la vue globale dense.

**Score visuel/HFE : 9,4/10.**

## Invariants

- un filtre d'affichage ne modifie jamais la mesure ;
- profil cutané/E-line uniquement en Ricketts ou Tous ;
- projections McNamara uniquement en McNamara/COM ou Tous ;
- aucune norme, diagnostic ou traitement n'est introduit par ce chantier ;
- aucun déploiement Vercel.

## État

**CANDIDAT CLOSEOUT PRÉ-MERGE.** Mathématiques, tracing AFTER, T2, PostgreSQL, R15 et R15bis sont certifiés sur le candidate produit `39660fa45471dbcd8c773148172ec03a854c931f`. Le merge reste interdit tant que le HEAD documentaire de closeout n'a pas franchi les gates de PR requis.
