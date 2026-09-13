# HANDOVER — DIGITAL CROWN / CÉPHALOMÉTRIE — R15bis UI/UX

**Date :** 2026-09-13  
**Repo :** `hraaaaf/Digital_crown`  
**Canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Gate d’entrée :** R15 doit être mergé, closeouté et vérifié sur `master` avant toute implémentation R15bis.  
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

Avant toute modification :

1. vérifier `master`, HEAD, PRs et CI ;
2. confirmer que R15 est réellement fermé ;
3. capturer le studio R15 **réel** en 390 / 768 / 1280+ ;
4. inventorier navigation, viewer, panneaux, actions, états et densité ;
5. écrire les écarts visuels par rapport au Goal R15bis ;
6. ne modifier aucun fichier UI avant ces preuves.

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

**Attendre uniquement la fermeture réelle de R15. Dès R15 mergé + closeout vérifié sur master : relire ce fichier, capturer BEFORE R15bis aux trois viewports, puis réaliser le mockup/tokens final avant implémentation.**

## SÉQUENCE RESTANTE CÉPHALO

`R15 actif dans fenêtre dédiée → closeout R15 → R15bis UI/UX → R16 PDF/restitution → R17 certification/closeout`
