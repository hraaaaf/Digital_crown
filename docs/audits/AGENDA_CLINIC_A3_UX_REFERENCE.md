# Agenda clinique — A3 UX reference

## Goal
Rendre visibles et configurables les disponibilités propres à chaque praticien sans casser la grille synchronisée A2.

Succès observable :
- disponibilité effective = horaires cabinet ∩ horaires praticien ;
- absence de configuration praticien = héritage cabinet strict ;
- plusieurs plages par jour permettent plusieurs pauses ;
- congés/absences bloquent uniquement le praticien ciblé ;
- fermetures cabinet restent absolues ;
- axe horaire commun, lanes A2 et bloqueurs historiques non assignés restent inchangés.

## BEFORE immuable
- baseline produit : `63d3902656d0525dccac60cbc15cf2aa21b1ffd9`
- HEAD de capture : `01eab652ce5960137a582c79265e82ab964a7335`
- run : `35106951485` — SUCCESS
- vues : Agenda Multi + Réglages > Horaires & Agenda
- viewports : 390×844, 768×1024, 1280×900
- preuve : 6 captures + géométrie sans overflow + synchronisation des cartes 09:00.

## Référence AFTER / mockup fonctionnel

### Agenda Multi
Conserver exactement la structure A2 : colonne Heure fixe, une lane par praticien, scroll horizontal interne sur mobile, rendez-vous non assignés en bande transversale.

Ajouter uniquement un langage d’état des créneaux :
- Libre : blanc ;
- Cabinet fermé / hors horaires cabinet : gris soutenu ;
- Hors horaires praticien : gris très clair ;
- Pause praticien : ambre très léger ;
- Absence / congé praticien : rose très léger.

La couleur est secondaire : les créneaux non disponibles sont aussi réellement désactivés. Aucun créneau individuel ne peut réouvrir une période fermée par le cabinet.

### Réglages > Horaires & Agenda
Sous les horaires cabinet, ajouter une section `Disponibilités par praticien` :
- sélecteur horizontal des praticiens assignables ;
- état par défaut `Hérite du cabinet` ;
- action `Personnaliser` qui initialise les plages avec les horaires cabinet ;
- 0..n plages par jour ; 0 plage = jour off ;
- action `Hériter du cabinet` pour supprimer l’override ;
- bloc `Absences & congés` avec début, fin et motif ;
- copie explicite : `disponibilité effective = cabinet ∩ praticien`.

## Invariants UI
- aucune régression Jour / Semaine / Mois / Multi A2 ;
- aucune largeur de page supérieure au viewport ;
- sur 390 px, les lanes restent lisibles via scroll interne ;
- les mêmes viewports BEFORE et AFTER sont obligatoires ;
- AFTER doit fournir une preuve automatisée de la présence des 5 états et un score visuel calculé sur les critères ci-dessus.
