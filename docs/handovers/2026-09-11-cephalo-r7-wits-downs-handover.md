# Céphalométrie R7 — Wits / Jacobson + Downs handover

Date: 2026-09-11

## Goal
Versionner uniquement les géométries patient Wits/Jacobson et Downs scientifiquement sourcées, fail-closed et auditables, sans norme, classification, diagnostic ni traitement.

## Base vérifiée
- master après R6: `8e9f89bfa006534518d940f877725df41c020668`.
- R6 PR #422 fusionnée après CI #3356 SUCCESS et T2 #2344 SUCCESS.
- ZERO LLM. Aucun Vercel.

## Sources primaires vérifiées
1. Jacobson A. The "Wits" appraisal of jaw disharmony. Am J Orthod. 1975;67(2):125-138. DOI: `10.1016/0002-9416(75)90065-2`.
2. Downs WB. Variations in facial relationships; their significance in treatment and prognosis. Am J Orthod. 1948;34(10):812-840. DOI: `10.1016/0002-9416(48)90015-3`.

## Wits — gate actuel
La source Jacobson définit Wits par projection perpendiculaire des points A et B sur le plan occlusal, donnant AO et BO, puis mesure AO-BO le long de ce plan.

État Digital Crown: `BLOCKED_LANDMARK_CONVENTION`.

Raison: le contrat SRPose38 expose U6/L6 et les incisives, mais la nomenclature clinique exacte nécessaire pour construire le plan occlusal Jacobson n'est pas encore certifiée/versionnée. Le runtime historique accepte des alias `Occ_Ant`/`Occ_Post`, mais ces alias ne constituent pas une preuve scientifique suffisante pour une nouvelle evidence typée.

Interdit en R7 tant que le gate n'est pas levé:
- inventer `Occ_Ant` / `Occ_Post` à partir de U6/L6 ou des incisives;
- utiliser une simple droite U6-L6 ou incisive sans convention sourcée;
- produire un Wits à partir d'un plan occlusal implicite.

## Downs — gate initial
La source primaire 1948 est vérifiée. Le prochain lot doit inventorier les mesures Downs une par une et les classer:
- implémentable avec landmarks/versioned axes actuels;
- déjà présente sous un contrat CRANIOM/runtime existant et nécessitant parité;
- bloquée par landmark/convention/protocole.

Un nom "Downs" existant dans le code n'est pas suffisant: définition, landmarks, orientation, unité, arrondi et ordre des opérations doivent être recoupés avec la source primaire et au moins une corroboration fiable avant activation.

## Double-check obligatoire R7
Pour chaque mesure candidate:
1. source primaire + corroboration indépendante;
2. définition exacte et landmarks;
3. géométrie/orientation/signature;
4. runtime legacy éventuel, arrondi et ordre des opérations;
5. fail-closed missing / degenerate / cross-image;
6. création -> edit landmarks -> calibration -> nouvel edit -> read path;
7. aucune norme/diagnostic/traitement.

## Next exact
1. inventorier les mesures Downs de la source 1948;
2. mapper chaque mesure aux landmarks SRPose38 et aux champs runtime actuels;
3. implémenter uniquement le sous-ensemble non ambigu;
4. garder Wits bloqué jusqu'à certification du plan occlusal;
5. tests ciblés + CI/T2 exact-head;
6. closeout R7 puis R8 McNamara.
