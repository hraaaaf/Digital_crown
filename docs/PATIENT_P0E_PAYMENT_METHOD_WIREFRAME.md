# P0-E — Paiement explicite — Goal visuel + wireframe

## Chantier
Page Patient — P0-E Paiements / échéances

## Baseline vérifiée
Workflow `Patient P0-E Payment Baseline` sur `692225a31dbd427732810f4a59dd3107d92819e2` :
- 8 captures : QuickPay + PayActe × 390 / 430 / 768 / 1280 px ;
- `Espèces` préselectionné dans 8/8 captures ;
- 0 overflow document ;
- 0 erreur runtime / HTTP pertinente.

## Goal
Supprimer toute méthode de paiement implicite sans changer le langage visuel existant.

## Succès observable
1. À l'ouverture de `QuickPayModal` et `PayActeModal`, aucune méthode n'est sélectionnée.
2. Les quatre choix existants restent identiques : Espèces, Carte, Virement, Chèque.
3. Le bouton `Encaisser` reste désactivé tant que montant valide ET méthode explicite ne sont pas fournis.
4. Après clic sur une méthode, une seule méthode est visuellement sélectionnée selon le style existant.
5. Aucun nouveau composant, couleur, hiérarchie ou wording étranger à l'application.
6. Même comportement sur 390, 430, 768 et 1280 px.

## Wireframe de référence

### État initial
```text
┌───────────────────────────────────┐
│ Saisir un paiement / Paiement acte│
│                                   │
│ Montant                           │
│ [ ............... MAD ]           │
│                                   │
│ MÉTHODE                           │
│ [ Espèces ]     [ Carte ]         │
│ [ Virement ]    [ Chèque ]        │
│   ↑ aucun bouton sélectionné      │
│                                   │
│ Notes ...                         │
│                                   │
│ [      ENCAISSER      ] disabled  │
└───────────────────────────────────┘
```

### Après sélection explicite
```text
│ MÉTHODE                           │
│ [ Espèces ]     [ Carte ✓ ]       │
│ [ Virement ]    [ Chèque ]        │
│                                   │
│ [      ENCAISSER      ] enabled   │
```

## Contraintes d'implémentation
- Conserver les modals, espacements, icônes, styles et grille actuels.
- Ne pas préselectionner `ESPECES` ni une autre méthode.
- Type d'état : méthode nullable/indéfinie jusqu'au clic utilisateur.
- Ne pas envoyer de requête sans méthode.
- Réinitialiser le choix après paiement réussi / fermeture si le composant reste monté.
- Backend reste source de vérité et exige toujours `payment_method`.

## Preuve requise après implémentation
- 8 captures après sur exactement les mêmes viewports et les deux mêmes modals ;
- 8/8 avec aucune sélection initiale ;
- test frontend de contrat pour les deux modals ;
- build frontend GREEN ;
- CI générale exact-head GREEN ;
- T2 exact-head GREEN.
