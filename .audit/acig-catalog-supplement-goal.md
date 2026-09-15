# ACIG catalog supplement — UI goal

## BEFORE
Le menu de recherche médicament affiche en dur `Référentiel CNOPS Open Data · snapshot 13/12/2021 · statut commercial actuel non certifié`, y compris si un résultat provient d'une autre source documentaire.

## Goal
Après saisie `ACIG`, afficher ACIGAM 100 MG et ACIGAM 200 MG sans sélectionner de présentation, tout en évitant d'attribuer à CNOPS un résultat provenant du supplément sourcé.

## Succès observable
- `ACIG` reste dans le champ ;
- exactement 2 suggestions ACIGAM visibles ;
- aucune présentation sélectionnée ;
- header du menu = `Référentiel documentaire Maroc · provenance par présentation · statut commercial actuel non certifié` si au moins un résultat n'est pas CNOPS ;
- le header CNOPS historique reste inchangé pour les résultats purement CNOPS ;
- aucune posologie/règle clinique/autofill ajouté.

## Preuve
Capture AFTER 1280×900 avec `ACIG` + 2 suggestions, tests frontend/backend, CI et non-régression DB/patients/documents.
