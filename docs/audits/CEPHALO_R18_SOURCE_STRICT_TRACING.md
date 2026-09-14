# Céphalométrie R18 — concordance source-strict + tracing scientifique

## Goal

Faire de chaque mesure affichée une construction visuellement vérifiable :

`landmarks source → construction versionnée → mesure → rendu du même contrat géométrique`.

La sélection d'une analyse doit limiter le tracé aux points et constructions nécessaires à cette analyse, sans constructions étrangères persistantes à l'écran.

## Succès observable

1. audit frontend/backend R18 : `concordance_certified=true`, 0 divergence ;
2. Steiner : SN, NA, NB + axes incisifs nécessaires, sans McNamara/Ricketts ;
3. Tweed : Frankfort, plan mandibulaire + axes incisifs nécessaires ;
4. COM/McNamara : Frankfort, N-perp et projections A/B + Co-A, Co-Gn, ANS-Me ;
5. Ricketts : profil cutané + E-line Prn-Pog' + projections Ls/Li, sans constructions squelettiques non nécessaires ;
6. mode Tous disponible pour l'inspection globale ;
7. BEFORE/AFTER aux mêmes viewports 390x844, 768x1024, 1280x900 ;
8. aucune overflow, erreur runtime ou egress externe dans le harness visuel ;
9. aucune modification rétroactive de la sémantique Ricketts E-line V1 persistée.

## Preuve mathématique acquise

R18 Scientific Concordance run #5, HEAD `595780ca3f17271a668f04b5a9e226f81303929e` : audit SUCCESS avec hard gate ; artefact `concordance-report.json` : `concordance_certified=true`, 0 divergence sur 90 comparaisons (41 PASS, 49 PASS_UNAVAILABLE).

Les distances linéaires Steiner U1-NA/L1-NB restent `NOT_COMPUTABLE` automatiquement tant que le landmark de couronne requis n'existe pas ; le bord incisif n'est plus utilisé comme substitut silencieux.

## Contrat Ricketts E-line

- V1 historique : distance parallèle à Frankfort conservée pour la lecture des snapshots existants ;
- V2 active : plus courte distance/perpendiculaire du point labial à Prn-Pog', Frankfort servant uniquement à orienter le signe antérieur/postérieur ;
- identifiants de construction et méthode versionnés séparément (`*_V2`).

Références enregistrées dans le code : DOI `10.1016/S0002-9416(68)90278-9`, PMCID `PMC6007603`, `PMC10973926`, `PMC12569150`.

## BEFORE

Harness dédié : `.github/workflows/cephalo-r18-tracing-before.yml` + `frontend/scripts/capture-cephalo-r18-tracing-before.mjs`.

Le BEFORE doit prouver l'état réel antérieur : pas de sélecteur de tracé au Step 1 et superposition globale non filtrée. Le run/artefact exact est inscrit ici seulement après succès.

## Mockup / référence d'interaction

Sélecteur compact intégré au viewer, sans nouveau panneau :

`[ COM ] [ Steiner ] [ Tweed ] [ Ricketts ] [ Tous ]`

- desktop/tablette : groupe centré sous les contrôles supérieurs ;
- mobile : largeur contrainte, défilement horizontal interne sans overflow du document ;
- état actif : token accent existant, pas de couleur clinique nouvelle ;
- changement immédiat, sans recalcul ni mutation des landmarks ;
- le choix est partagé avec `etape3Data.selectedAnalysis` pour qu'une seule source UI pilote mesures et tracé.

## Invariants

- un filtre d'affichage ne modifie jamais les coordonnées ni la mesure ;
- profil cutané/E-line uniquement en Ricketts ou Tous ;
- projections McNamara uniquement en COM/McNamara ou Tous ;
- Wits reste compatible au niveau tracing interne mais n'est pas promu comme nouvelle analyse clinique dans ce lot ;
- aucune norme/diagnostic/traitement n'est introduit par ce chantier ;
- aucun déploiement.

## État

EN COURS — mathématiques certifiées ; BEFORE visuel lancé ; implémentation UI interdite tant que le BEFORE n'est pas produit avec succès.
