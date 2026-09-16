# Céphalo-N — Semantic Color Implementation Gate

## Goal

Appliquer un code couleur Céphalo global sans créer de design system parallèle et sans modifier les calculs, constructions ou données patient.

## Implémentation présente sur la branche

- contrat central : `frontend/src/features/ortho/cephaloVisualSemantics.ts`
- familles scientifiques : squelettique bleu, dentaire violet, tissus mous vert, références ambre/orange, auxiliaire neutre
- rendu adaptatif : hue scientifique 60% + token Digital Crown `--text-main` 40% via `color-mix(...)`
- tableau : famille scientifique distincte du statut clinique
- statut clinique : normal/validé = success, vigilance/limite/compensation = warning, erreur/hors norme explicite = error, inconnu/N/A = neutre
- tracé R19 : constructions reliées au même contrat
- moteur historique : palette migrée vers contrat scientifique + tokens Digital Crown
- tissus mous / ligne E / VTO : famille `soft_tissue`
- landmarks : familles sémantiques + focus piloté par le thème
- calibration / sélecteur / loupe : tokens du thème
- tests unitaires et audit anti-couleurs historiques ajoutés
- contraste scientifique vérifié par test sur `--card-bg` et `--input-bg` des thèmes Digital Crown avec seuil >= 4.5:1
- harness R19 aligné sur le heading produit actuel `Céphalométrie` sans modifier sa fixture ni son contrat de capture

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

1. frontend tests ciblés + build sur le HEAD exact
2. CI exacte du HEAD
3. AFTER mêmes viewports et mêmes états
4. comparaison Target/BEFORE ↔ AFTER réelle
5. `EXECUTION_SCORE`, `ADVERSARIAL_SCORE`, `RETAINED_SCORE` selon la règle globale
6. Perfection Pass finale si le score atteint 9.0
7. validation visuelle humaine explicite requise par la règle globale
8. merge uniquement après autorisation explicite utilisateur sur HEAD final certifié
