# HANDOVER — DIGITAL CROWN / CÉPHALOMÉTRIE — R15bis UI/UX

**Date :** 2026-09-13  
**Repo :** `hraaaaf/Digital_crown`  
**Canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Gate d’entrée :** SATISFAIT — R15 mergé, closeouté et vérifié sur `master` `3dbab4e1fe722265932799eff01d4de8de252da9`.  
**Branche active :** `feat/cephalo-r15bis-uiux`  
**PR active :** #477  
**Référence visuelle :** `docs/assets/cephalo/r15bis-ui-reference.jpg`

## GOAL

Transformer le studio céphalométrique issu de R15 en une interface clinique plus lisible, plus structurée et plus rapide à parcourir, **sans modifier aucune logique scientifique, clinique, diagnostique ou thérapeutique**.

Le lot reprend uniquement les qualités structurelles du visuel de référence :
- navigation principale immédiatement lisible ;
- radio/viewer dominant ;
- panneau de résultats séparé et hiérarchisé ;
- sections cliniques regroupées avec icônes simples ;
- tableaux valeur/libellé compacts ;
- états et complétude visibles sans bruit visuel.

Le thème sombre du mockup n’est **pas** une cible. La cible reste l’identité Digital Crown et ses tokens existants.

## SUCCÈS OBSERVABLE

R15bis est réussi seulement si les preuves montrent :

1. navigation principale cohérente et explicite : `Accueil / Patients / Imagerie / Tracés / Analyses / Rapports` lorsque ces destinations existent réellement dans le produit ;
2. viewer/radio reste la surface dominante aux viewports adaptés ;
3. résultats scientifiques/COM/cliniciens regroupés en panneaux lisibles sans masquer la provenance ni la calculabilité ;
4. icônes homogènes, décoratives seulement quand elles n’ajoutent aucune action ;
5. aucun bouton, onglet ou destination factice ;
6. aucun contenu R11/R12/R13/R14 synthétisé ou auto-validé pour remplir l’UI ;
7. aucun changement de calcul, contrat backend, règle de sécurité, norme, source ou validation praticien ;
8. overflow horizontal = 0 aux viewports 390 / 768 / 1280+ ;
9. console/page errors = 0 sur le scénario de certification ;
10. comparaison BEFORE/AFTER documentée + score visuel explicite.

## RÉFÉRENCE VISUELLE

![Référence R15bis UI/UX](../assets/cephalo/r15bis-ui-reference.jpg)

### À reprendre

- top navigation claire avec destinations majeures ;
- séparation forte `viewer` / `résultats` ;
- panneaux de résultats avec titres + icônes ;
- tableaux compacts libellé / valeur ;
- badge de complétude/état seulement s’il est dérivé d’un état réel ;
- hiérarchie visuelle forte et faible densité cognitive.

### À ne pas reprendre

- dark theme comme identité finale ;
- couleurs arbitraires hors tokens Digital Crown ;
- faux écrans ou fausses destinations ;
- métriques mockées dans le runtime ;
- duplication d’informations déjà exposées proprement par R15 ;
- style “dashboard générique” si cela réduit la lisibilité clinique.

## BEFORE OBLIGATOIRE

État courant : **harness dédié ajouté, capture exacte encore à obtenir avant toute modification UI**.

Baseline exacte : `3dbab4e1fe722265932799eff01d4de8de252da9`.

Workflow : `.github/workflows/cephalo-r15bis-before.yml`.

Méthode : réutiliser le harness R15 AFTER certifié sur la baseline exacte ; conserver son `report.json` brut inchangé et ajouter `r15bis-before-metadata.json` pour qualifier explicitement cette capture comme BEFORE R15bis.

Avant toute modification UI :

1. obtenir le run BEFORE vert ;
2. vérifier artifact + baseline SHA + 390 / 768 / 1280+ ;
3. inventorier navigation, viewer, panneaux, actions, états et densité ;
4. comparer au Goal R15bis ;
5. figer mockup/tokens final ;
6. seulement ensuite modifier les fichiers UI.

## IMPLÉMENTATION AUTORISÉE

- layout, spacing, typographie, cartes, tableaux, sections, icônes ;
- navigation uniquement vers routes réelles ;
- responsive/adaptation viewer + panneau latéral ;
- regroupement visuel des informations existantes ;
- amélioration accessibilité clavier/ARIA/touch si nécessaire ;
- réutilisation stricte des tokens et composants Digital Crown quand disponibles.

## HORS SCOPE / INTERDITS

- aucune modification des formules céphalométriques ;
- aucune modification COM ou CRANIOM ;
- aucune nouvelle norme ni interprétation ;
- aucune modification du contrat R11/R12/R13/R14 ;
- aucune auto-validation praticien ;
- aucun PDF/restitution R16 ;
- aucun déploiement Vercel sans autorisation explicite.

## AFTER / CERTIFICATION

Après implémentation :

`AFTER 390 / 768 / 1280+ → comparaison avec BEFORE → overflow → console/page errors → interactions essentielles → clavier/touch → score visuel`

Le score visuel doit être argumenté sur :
- hiérarchie ;
- lisibilité ;
- densité ;
- cohérence ;
- séparation viewer/résultats ;
- responsive ;
- fidélité à Digital Crown.

Aucun “10/10” sans captures et comparaison réelles.

## NEXT EXACT

Obtenir et auditer l’artifact **Cephalo R15bis BEFORE** sur la baseline `3dbab4e1fe722265932799eff01d4de8de252da9`. Tant que cette preuve n’est pas verte, **aucun fichier UI ne doit être modifié**.

## SÉQUENCE RESTANTE CÉPHALO

`R15bis BEFORE → Goal/mockup/tokens final → implémentation R15bis → AFTER/certification → closeout R15bis → R16 PDF/restitution → R17 certification/closeout`
