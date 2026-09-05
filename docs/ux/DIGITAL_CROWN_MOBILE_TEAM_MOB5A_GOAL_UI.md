# MOB-5A — Équipe / praticiens — Goal UI

Status: ACTIVE
Branch: `audit/mobile-secondary-value-mob5`

## BEFORE — audit vérifié

- La route dédiée `/mobile/dentists` existe déjà.
- La vue actuelle charge `/api/mobile/dentists` et affiche nom, email et nombre de RDV du jour.
- L’endpoint backend est protégé par la permission mobile `agenda`.
- La navigation canonique `Plus` n’expose pas encore Équipe / praticiens.
- La vue actuelle force `font-outfit` localement et contient un fallback de couleur de marque `rgba(0,51,128,0.10)`, incompatibles avec l’invariant thème/typographie.
- La vue dédiée quitte le shell principal au lieu de fonctionner comme une destination secondaire canonique.

## Goal

Rendre **Équipe / praticiens** accessible depuis `Plus`, dans le shell mobile canonique, en conservant la même donnée backend et la permission `agenda`.

## Success observable

1. `Plus` expose `Équipe` pour `ADMIN`, `DENTISTE`, `SECRETAIRE`.
2. La destination reste dans le shell mobile et la barre canonique `Aujourd’hui / Patients / + / Assistant / Plus` reste visible.
3. La vue affiche praticiens + RDV du jour, avec loading / empty / error / refresh.
4. Aucune police de marque locale figée ; `--app-font-family` reste source de vérité.
5. Aucun fallback couleur de marque codé en dur.
6. Aucun overflow horizontal à 390 / 430 / 768.
7. Build frontend et tests ciblés verts avant certification.

## Référence / mockup fonctionnel

Structure cible :

- Header compact du shell existant.
- `Plus` → item `Équipe` avec icône utilisateurs.
- Vue `Équipe` :
  - titre + sous-titre `Praticiens du cabinet` ;
  - action rafraîchir ;
  - cartes praticiens ;
  - badge `Praticien principal` si applicable ;
  - compteur `N RDV` si > 0 ;
  - états erreur / vide / chargement.
- Pas de nouvelle navigation parallèle ni de FAB additionnel.

## AFTER attendu

Captures aux mêmes viewports `390×844`, `430×932`, `768×1024`, comparaison au Goal UI, zéro overflow, zéro erreur runtime app, score visuel documenté.
