# Marketplace P5 — UI reference

## Goal
Transformer `/approvisionnement` d'une landing marketing en outil d'achat clinique : **rechercher → comparer → ajouter → vérifier le panier → enregistrer la commande**, avec le catalogue visible immédiatement.

## Source BEFORE
Marketplace P5 BEFORE run #5 — HEAD `4aece82bee3b7285b1df0dbdeea06fa7e28cf67a` — 390×844 / 430×932 / 768×1024 / 1280×800.

Constats vérifiés : H1 rogné à 390 px ; hero disproportionné sur mobile ; recherche/catalogue repoussés très bas ; densité marketing excessive ; données de stratégie/revenu commercial visibles dans le parcours acheteur.

## Référence figée
Voir `P5_UI_REFERENCE.svg`.

### Mobile 390/430
1. Header achat compact, 96–120 px maximum après le chrome applicatif.
2. H1 `Approvisionnement` sur 1 ligne si possible, jamais rogné.
3. Search pleine largeur avant `y=180`.
4. Chips catégories horizontales sous la recherche.
5. Premier produit visible avant `y=330`.
6. Panier accessible par bouton compact avec compteur ; checkout après catalogue ou panneau dédié, pas de colonne écrasée.
7. Aucun bloc éditorial/marketing avant le catalogue.

### Tablette 768
1. Header compact + search.
2. Grille produits 2 colonnes.
3. Panier résumé visible sans masquer le catalogue.

### Desktop 1280
1. Header compact ≤ 150 px.
2. Ligne recherche + filtres immédiatement sous le header.
3. Catalogue 2 colonnes + panier sticky à droite dans le premier viewport.
4. Les informations fournisseur restent secondaires.

## Suppressions / déplacements
- supprimer le hero long et ses métriques marketing ;
- supprimer les 4 cartes `Collection` avant le catalogue ;
- supprimer la section éditoriale volumineuse avant le catalogue ;
- ne pas exposer `stratégie active`, `revenu simulé`, commission/remise au cabinet acheteur ;
- déplacer l'information fournisseur dans une ligne secondaire / lien ;
- CTA final = **Enregistrer la commande** tant qu'aucun transport fournisseur n'est exécuté par ce flow.

## Comportement
- ajout panier sans reload ;
- `−` / `+` avec `aria-label` comprenant le nom du produit ;
- état disponibilité lisible sans dépendre uniquement de la couleur ;
- recherche et filtres conservés au clavier ;
- focus visible ;
- aucun overflow horizontal.

## Gate visuel AFTER
Même harness et mêmes données que BEFORE aux viewports 390×844 / 430×932 / 768×1024 / 1280×800.

Succès observable :
- H1 non rogné ;
- search visible dans le premier écran aux 4 viewports ;
- au moins une carte produit visible dans le premier écran sur 390/430 ;
- zéro page error / console error / overflow horizontal ;
- aucune donnée commerciale interne dans le parcours acheteur ;
- CTA reflète la création locale DRAFT ;
- score visuel cible **≥ 9.0/10**, uniquement après comparaison BEFORE/AFTER.
