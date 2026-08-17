# Page Patient P0-B — Goal visuel identité

Baseline certifiée : workflow `Patient Identity Baseline`, run `32041088848`, 8 captures sur 390×844 / 430×932 / 768×1024 / 1280×900.

## Goal

Conserver le langage visuel actuel des formulaires Add/Edit tout en supprimant les vérités d'identité et de disponibilité inventées.

## Critères visuels et fonctionnels

### Sexe
- création : aucun sexe pré-sélectionné ; placeholder explicite `Sélectionner` ; choix M/F requis avant soumission ;
- édition : utiliser uniquement la valeur backend ; une valeur absente/legacy reste vide et doit être choisie explicitement, jamais transformée en F ;
- ne pas ajouter de troisième valeur clinique ou administrative sans audit dédié.

### Numéro de dossier
- `checking` : état existant conservé ;
- `available` : seulement après réponse backend positive ;
- `taken` : état existant conservé ;
- erreur réseau/API : nouvel état neutre `unknown`, texte `Vérification indisponible — réessayez` ; ne jamais afficher `Numéro disponible` par fallback.

### Anti-doublon création
- si `/patients/check-duplicate` échoue, ne pas poursuivre silencieusement vers la création ;
- afficher une erreur explicite et demander une nouvelle tentative ;
- le `force_create` existant reste réservé à une décision explicite après doublon réellement renvoyé par le backend.

### Responsive
- ne pas redessiner le formulaire ;
- corriger seulement les contraintes de largeur/padding responsables du cadrage mobile trop étroit ;
- aucune régression desktop/tablette.

## Wireframe basé sur l'écran actuel

```text
IDENTITÉ CIVILE
Date de naissance *      Sexe *
                         [ Sélectionner  v ]

NUMÉRO DE DOSSIER
[ T2-0001 / prochain numéro ] [état]

États possibles :
- vérification…
- disponible
- déjà utilisé
- vérification indisponible — réessayez
```

## Succès

- `sexe` vide avant choix sur Add dans les 4 viewports ;
- aucun fallback `F` à l'édition ;
- erreur de vérification dossier != disponible ;
- erreur anti-doublon bloque le submit ;
- 8 captures après sur les mêmes viewports ;
- zéro overflow / erreur runtime ;
- build/typecheck + tests exacts.
