# Document Studio — Master Consolidation 2026-09-09

## Goal
Rebaseliner Document Studio sur le `master` courant et ne porter que les deltas encore absents et utiles, sans réintroduire les branches historiques divergentes.

## Baseline vérifiée
- repository: `hraaaaf/Digital_crown`
- master de départ: `6301f737f59e1f5c6c0e1e79402fbd5270637617`
- branche de consolidation: `refactor/document-studio-master-consolidation`
- PR de consolidation: `#379`

## Règle
Aucune ancienne PR stackée n'est mergée telle quelle. Chaque delta est classé KEEP / SUPERSEDED / REBUILD / DROP après comparaison avec `master`.

## Matrice courante

### PR #18 — R2 prescription persistence
**Verdict final: SUPERSEDED BY #379 — CLOSED**

Déjà absorbé/supersédé par `master`:
- save des `DoctorPrescriptionPreference` avec rollback + propagation;
- delete sur la table correcte et isolation praticien;
- lecture stable des presets.

Porté sur #379:
- `record_medication_usage()` fail-visible avec rollback + propagation;
- recherche non vide strictement local-first, sans fallback HTTP `medicament.ma`;
- tests négatifs réseau + échec de commit.

### PR #77 — P3 Devis
**Verdict: REBUILD ON MASTER**

La branche historique diverge fortement de `master` et ne doit pas être mergée/rebasée mécaniquement.

Porté sur #379:
- cohérence `items ↔ teeth_data` côté `DevisData`;
- tests orphan tooth / orphan treatment / divergence de prix.

Encore à réévaluer:
- protections de transition/dirty-state accounting;
- protections odontogramme/source/conversion qui ne sont pas déjà remplacées par le code courant.

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
**Verdict: PARTIAL SUPERSEDED / PARTIAL RECONCILE**

La PR historique est stackée sur l'ancienne branche P7 et ne doit pas être mergée.

Déjà superseded par l'architecture courante `master`:
- navigation clic + URL centralisée via `useDocumentHubNavigation`;
- dirty-state multi-pages via `DocumentTabNavigationPolicy` + states spécialisés;
- `DocumentNavigationPolicy.ts` historique n'a donc pas à être recréé.

Encore à réconcilier:
- lifecycle archive/preview/print/duplicate;
- ancienne désactivation du flux legacy `echeancier` à confronter au contrat courant, qui possède aujourd'hui un onglet/flux dédié explicite;
- callbacks/branches mortes éventuels dans les composants partagés.

### PR #336 — premium header specialties
**Verdict final: SUPERSEDED — CLOSED**

`master` possède déjà une implémentation plus générale:
- rendu de toutes les lignes configurées;
- gestion dynamique de la profondeur des blocs;
- séparateurs repositionnés sous les blocs rendus;
- gestion Heritage dense.

### PR #353 — certificate signature caption
**Verdict final: SUPERSEDED BY #379 — CLOSED**

Porté sur #379:
- ligne de signature conservée;
- nom praticien conservé;
- mention imprimée `Signature manuscrite du praticien` retirée;
- test de régression dédié porté.

## Preuves exactes déjà obtenues
- branche de consolidation créée depuis le `master` courant;
- PR #379 ouverte en draft;
- PR #18 fermée après port des résidus utiles;
- PR #336 fermée comme superseded;
- PR #353 fermée après port du correctif;
- CI exact-head relancée automatiquement après chaque nouveau commit; aucun PASS final n'est revendiqué tant que le HEAD courant n'est pas vert.

## Chemin critique
1. scanner #77/#90/#95/#96/#97/#101 fichier par fichier contre `master`;
2. compléter la matrice KEEP/DROP finale;
3. implémenter uniquement les deltas KEEP sur #379;
4. exécuter tests ciblés puis full-app/build exact-head;
5. runtime authentifié + PDF + 390/430/768/1280 selon surfaces touchées;
6. closeout canonique;
7. ready/merge seulement après preuves.

## État
**IN PROGRESS — rebaseline actif sur #379.**

Aucun pourcentage global n'est déclaré avant la matrice finale et les gates mesurables.
