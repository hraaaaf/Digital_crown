# Patient P0-E — Goal visuel migration échéancier

## Baseline requise

La baseline dédiée est capturée par `Patient Installment Modal Baseline` sur :

- 390×844
- 430×932
- 768×1024
- 1280×900

Aucune implémentation frontend de l'échéancier moderne n'est autorisée tant que ces quatre captures ne sont pas acquises.

## Goal

Conserver le modal d'échéancier actuel et sa logique visuelle, tout en remplaçant uniquement sa persistance legacy par le contrat `/installments` lié explicitement à l'acte concerné.

Ce lot n'est **pas** un redesign.

## Succès observable

1. Le modal s'ouvre depuis le même bouton `Plan` de l'acte impayé.
2. Le titre, le montant de l'acte, les lignes d'échéances et les contrôles conservent la hiérarchie existante.
3. Le montant à couvrir est le **reste dû réel** de l'acte, pas nécessairement son montant initial.
4. La somme des échéances doit être exactement égale au reste dû avant activation de l'action de création.
5. Une somme insuffisante ou excessive est affichée comme non réconciliée et ne peut pas être enregistrée.
6. Le submit envoie `patient_id + acte_id + total_amount + installments` vers `/installments`.
7. Le succès n'est affiché qu'après réponse backend positive.
8. Une erreur backend reste visible ; le modal ne prétend pas avoir créé un plan.
9. Aucun nouveau composant décoratif, badge ou animation n'est ajouté.
10. Le modal reste utilisable sans débordement horizontal aux quatre viewports de référence.

## Wireframe cible

```text
┌──────────────────────────────────────────────┐
│ Échéancier de paiement                  [×] │
│ Acte : <libellé>                            │
│ Reste dû : <montant> MAD                    │
├──────────────────────────────────────────────┤
│ Versement 1   [ montant ]   [ date ]   [×] │
│ Versement 2   [ montant ]   [ date ]   [×] │
│ [+ Ajouter une échéance]                    │
├──────────────────────────────────────────────┤
│ Total échéancier : X MAD                    │
│ Reste à couvrir : Y MAD                     │
│                                              │
│ [Annuler]          [Créer l'échéancier]     │
└──────────────────────────────────────────────┘
```

États :

- `Y = 0` → action de création disponible ;
- `Y > 0` → couverture insuffisante, action bloquée ;
- `Y < 0` → dépassement, action bloquée ;
- requête en cours → action désactivée ;
- erreur backend → message explicite, modal maintenu ouvert.

## Preuve après implémentation

- tests frontend/contrat ciblés ;
- tests backend P0-E acte↔échéancier ;
- CI exacte sur HEAD ;
- captures après sur les quatre mêmes viewports ;
- comparaison baseline / wireframe / après ;
- score visuel uniquement après inspection des captures.
