# Document Studio — Master Consolidation 2026-09-09

## Goal
Rebaseliner Document Studio sur le `master` courant et ne porter que les deltas encore absents et utiles, sans réintroduire les branches historiques divergentes.

## Baseline vérifiée
- repository: `hraaaaf/Digital_crown`
- master: `6301f737f59e1f5c6c0e1e79402fbd5270637617`
- branche de consolidation: `refactor/document-studio-master-consolidation`

## Règle
Aucune ancienne PR stackée n'est mergée telle quelle. Chaque delta est classé KEEP / SUPERSEDED / REBUILD / DROP après comparaison avec `master`.

## Matrice initiale

### PR #18 — R2 prescription persistence
**Verdict: PARTIAL KEEP / PARTIAL SUPERSEDED**

Déjà absorbé/supersédé par `master`:
- save des `DoctorPrescriptionPreference` avec rollback + propagation;
- delete sur la table correcte et isolation praticien;
- lecture stable des presets.

Encore utile à porter:
- `record_medication_usage()` fail-visible au lieu du legacy qui rollback puis masque l'erreur;
- recherche non vide strictement local-first: `master` délègue encore au service legacy, lequel contient un fallback HTTP vers `medicament.ma`.

### PR #77 — P3 Devis
**Verdict: REBUILD ON MASTER**

La branche historique diverge fortement de `master` et ne doit pas être mergée/rebasée mécaniquement.
Deltas prouvés encore absents à réévaluer/porter:
- cohérence `items ↔ teeth_data` côté `DevisData`;
- protections de transition/dirty-state accounting;
- protections odontogramme/source/conversion utiles qui ne sont pas déjà remplacées par le code courant.

### PR #90 — P4 Honoraires
**Verdict: REBUILD ON MASTER**

PR fermée non mergée, stackée sur #77. Les invariants financiers restent utiles mais doivent être comparés au code courant avant port.

### PR #95 — P5 Suivi Paiement
**Verdict: REBUILD ON MASTER**

PR fermée non mergée, stackée sur P4. Reprendre uniquement les invariants absents du backend/runtime courant.

### PR #96 — P6 Document Libre
**Verdict: REBUILD ON MASTER**

PR fermée non mergée. Reprendre uniquement les protections dirty/archive encore absentes après comparaison.

### PR #97 — P7 Compagnon Diagnostique
**Verdict: REBUILD ON MASTER / SCIENTIFIC GATE**

PR fermée non mergée. Ne porter que la frontière non-prescriptive et les dirty-state prouvés utiles. Toute logique clinique reste sous gate scientifique séparé.

### PR #101 — T1 transversal
**Verdict: REBUILD ON MASTER**

La PR est encore ouverte mais stackée sur l'ancienne branche P7, pas sur `master`.
Delta clairement absent de `master`:
- `DocumentNavigationPolicy.ts` n'existe pas sur `master`.
D'autres protections lifecycle/dirty/archive doivent être portées une par une après comparaison.

### PR #336 — premium header specialties
**Verdict: SUPERSEDED**

`master` possède déjà une implémentation plus générale:
- rendu de toutes les lignes configurées;
- gestion dynamique de la profondeur des blocs;
- séparateurs repositionnés sous les blocs rendus;
- gestion Heritage dense.
Ne pas porter #336.

### PR #353 — certificate signature caption
**Verdict: KEEP**

`master` affiche encore `Signature manuscrite du praticien` dans le PDF. Le delta de #353 reste nécessaire: conserver la ligne et le nom du praticien, retirer l'instruction imprimée.

## Chemin critique
1. porter les petits deltas KEEP prouvés sur cette branche;
2. ajouter leurs tests de régression;
3. scanner #77/#90/#95/#96/#97/#101 fichier par fichier contre `master`;
4. produire une matrice KEEP/DROP finale;
5. implémenter uniquement les deltas KEEP sur `master`;
6. exécuter tests ciblés puis full-app/build;
7. runtime authentifié + PDF + 390/430/768/1280 selon surfaces touchées;
8. closeout canonique;
9. merge uniquement après preuves.

## État
**IN PROGRESS — rebaseline master commencé.**

Aucun pourcentage global n'est déclaré avant la matrice finale et les gates mesurables.
