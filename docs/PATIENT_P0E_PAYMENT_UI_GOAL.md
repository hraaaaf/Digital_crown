# Patient P0-E2 — Goal visuel paiement explicite

## Référence
Baseline réelle certifiée : workflow `Patient P0-E Payment Baseline` #4, artifact `9306442110`.
Viewports : 390x844, 430x932, 768x1024, 1280x900. Deux surfaces : QuickPay et PayActe.

## Avant vérifié
- 8/8 captures : `Espèces` est sélectionné automatiquement sans action utilisateur.
- Aucun overflow horizontal.
- Aucune erreur page/runtime pertinente.

## Goal
Conserver strictement la modale existante : dimensions, grille, typographie, couleurs, icônes et hiérarchie inchangées.
Seul changement visuel autorisé à l'ouverture : aucune des quatre méthodes n'est sélectionnée.
Après clic utilisateur, la méthode choisie reprend exactement le style sélectionné existant.

## Succès observable
- 0/8 capture after avec une méthode sélectionnée au chargement.
- bouton `Encaisser` désactivé sans méthode explicite ;
- après sélection, le bouton peut être activé si le montant est valide ;
- aucune nouvelle disposition, aucun redesign ;
- mêmes viewports, aucun overflow, aucune erreur runtime pertinente.
