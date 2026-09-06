# Digital Crown — MOB-5D Stock — Goal UI

Status: GOAL LOCKED / BEFORE IMPLEMENTATION
Date: 2026-09-06
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-stock-mob5d`
Baseline: `aaa28ef97b22df2c5654c4e0da7efc15692787a8`
Audit: `docs/ux/DIGITAL_CROWN_MOBILE_STOCK_MOB5D_AUDIT.md`

## Goal
Permettre depuis le mobile d'identifier immédiatement ce qui manque et d'enregistrer un mouvement Stock courant en moins de 30 secondes, sans porter les réglages lourds du desktop.

## Success observable
- `Plus → Stock` sans modifier les 5 boutons canoniques ;
- deep-link `?tab=stock` ;
- source unique `/stock/items` + `/stock/alerts` ;
- état `Rupture` si quantité = 0 ; `Alerte` si le serveur renvoie `alerte=true` ; sinon `OK` ;
- recherche par article/fournisseur ;
- filtre `Tous / À traiter` ;
- `−1/+1` persiste via `PATCH /stock/items/{id}` ;
- quantité jamais négative ;
- ajout rapide via `POST /stock/items` ;
- aucun delete mobile ;
- erreurs inline et refresh manuel ;
- zéro overflow aux viewports 390×844, 430×932, 768×1024 ;
- thème/typographie issus du runtime ;
- zéro erreur console/page sur AFTER.

## Mockup textuel de référence

Header compact :
`Stock` + compteur d'articles + bouton actualiser.

Résumé : trois tuiles compactes
`Rupture` | `Alerte` | `OK`.

Sous-header :
champ `Rechercher…` puis `Tous | À traiter`.

Carte article :
1. état explicite (`Rupture`, `Alerte`, `OK`) ;
2. nom + catégorie ;
3. quantité et unité ;
4. seuil en texte secondaire ;
5. contrôles tactiles `−  quantité  +` ;
6. fournisseur en lecture seule si présent.

CTA principal flottant dans le contenu, pas dans la nav : `Ajouter`.

Ajout rapide :
`Nom`, `Catégorie`, `Quantité`, `Seuil`, `Unité`, puis `Ajouter`.

## Hiérarchie
1. rupture / alerte ;
2. quantité actuelle ;
3. mouvement court ;
4. recherche ;
5. ajout.

## Hors scope mobile V1
- suppression ;
- édition prix/fournisseur/notes ;
- inventaire avancé ;
- commandes fournisseur ;
- lots/date de péremption ;
- historique de mouvements inexistant côté backend ;
- paramétrage avancé.

## Référence desktop
Réutiliser `StockPage.tsx` existante pour le desktop. Son activation ne change pas la source métier et ne doit pas entraîner de nouvelle logique.

## BEFORE / AFTER
BEFORE : baseline exacte `aaa28ef9…`, `Plus` ouvert sans entrée Stock.
AFTER : même scénario déterministe avec `Plus → Stock` puis vue Stock aux viewports 390×844, 430×932, 768×1024.

Deployment: none. No Vercel deployment authorized.