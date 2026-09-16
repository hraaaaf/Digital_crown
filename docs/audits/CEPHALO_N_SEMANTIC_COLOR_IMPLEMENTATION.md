# Céphalo-N — Semantic Color Implementation Gate

## Goal

Appliquer un code couleur Céphalo global sans créer de design system parallèle et sans modifier les calculs, constructions ou données patient.

## Implémentation présente sur la branche

- contrat central : `frontend/src/features/ortho/cephaloVisualSemantics.ts`
- tableau : famille scientifique distincte du statut clinique
- tracé R19 : constructions reliées au même contrat
- moteur historique : palette migrée vers contrat scientifique + tokens Digital Crown
- tissus mous / ligne E / VTO : famille `soft_tissue`
- landmarks : familles sémantiques + focus piloté par le thème
- calibration / sélecteur / loupe : tokens du thème
- tests unitaires et audit anti-couleurs historiques ajoutés

## Invariants

- aucun changement backend
- aucune migration DB
- aucune nouvelle mesure
- aucune nouvelle norme
- aucun changement de formule
- aucun déploiement

## BEFORE

Référence verrouillée dans `CEPHALO_N_SEMANTIC_COLOR_MOCKUP.md` : R19 Analysis Reference Workbench, 18/18 états, 390x844 / 768x1024 / 1280x900.

## Proof restante obligatoire

1. frontend tests ciblés + build
2. CI exacte du HEAD
3. AFTER mêmes viewports et mêmes états
4. comparaison BEFORE/AFTER
5. score visuel argumenté
6. merge uniquement après autorisation explicite utilisateur sur HEAD certifié
