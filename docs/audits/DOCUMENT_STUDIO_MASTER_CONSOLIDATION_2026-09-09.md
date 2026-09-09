# Document Studio — Master Consolidation 2026-09-09

## Goal
Rebaseliner Document Studio sur le `master` courant et ne porter que les deltas encore absents et utiles, sans réintroduire les branches historiques divergentes.

## Baseline vérifiée
- repository: `hraaaaf/Digital_crown`
- master de départ: `6301f737f59e1f5c6c0e1e79402fbd5270637617`
- branche de consolidation: `refactor/document-studio-master-consolidation`
- PR de consolidation: `#379`

## Règle
Aucune ancienne PR stackée n'est mergée telle quelle. Chaque delta est classé KEEP / SUPERSEDED / MOVE TO SCIENTIFIC GATE après comparaison avec `master`.

## Matrice finale de reprise

### PR #18 — R2 prescription persistence
**SUPERSEDED BY #379 — CLOSED**

Porté sur #379 :
- `record_medication_usage()` fail-visible avec rollback + propagation ;
- suggestions non vides strictement local-first, sans fallback HTTP `medicament.ma` ;
- tests négatifs réseau + échec de commit.

Le reste est déjà absorbé par `master` : save/delete/read des `DoctorPrescriptionPreference` et isolation praticien.

### PR #77 — P3 Devis
**SUPERSEDED BY CURRENT MASTER + #379 — CLOSED**

Porté sur #379 :
- cohérence `items ↔ teeth_data` côté `DevisData` ;
- tests orphan tooth / orphan treatment / divergence de prix.

Déjà plus récent sur `master` :
- source odontogramme canonique + normalisation/hydratation ;
- conversion P7→Devis financièrement neutre ;
- navigation/dirty-state via l'orchestration courante.

### PR #90 — P4 Honoraires
**SUPERSEDED BY CURRENT MASTER — historical PR already closed**

Le `master` courant n'utilise plus l'ancien `honoraires_gen.py`/schéma P4 stacké. Il possède :
- `TenantAwareAccountingGenerator` ;
- `honoraires_contract.py` fail-closed avant PDF ;
- contrôles request/persistence pour PAYE/EN_ATTENTE ;
- dates d'échéances explicites, sans synthèse silencieuse ;
- générateur comptable courant avec readability/pagination.

Aucun ancien fichier P4 n'est porté mécaniquement.

### PR #95 — P5 Suivi Paiement
**SUPERSEDED BY CURRENT MASTER — historical PR already closed**

Le backend courant possède un flux échéancier dédié et plus strict :
- liste + `latest` déterministe ;
- création liée à l'acte avec contrôle du reste dû ;
- réconciliation exacte ;
- échéance PAYE non réouvrable/non rechiffrable sans contrepassation ;
- mode de règlement explicite ;
- création d'une vraie ligne `Payment` liée à l'échéance ;
- mise à jour de l'état de paiement de l'acte ;
- rollback fail-visible.

Le frontend courant possède en plus un dirty-state échéancier et un flux dédié de preview/génération.

### PR #96 — P6 Document Libre
**SUPERSEDED BY CURRENT MASTER — historical PR already closed**

Le `master` courant possède :
- dirty-state dédié ;
- beforeunload ;
- reset dirty uniquement après génération réussie avec `archive=true` et hors preview ;
- preview/erreur/409 ne passent pas ce reset ;
- lifecycle courant intégré dans `useDocumentGenerator`.

### PR #97 — P7 Compagnon Diagnostique
**MOVE TO SCIENTIFIC CORE / MEDICAL GATE — historical PR already closed**

Le `master` actuel contient encore dans `TreatmentPlanStudio` un arbre déterministe produisant des diagnostics nommés et des actes thérapeutiques prédéfinis.

Ce point n'est pas traité comme un simple delta Document Studio. Il doit rester sous le chantier Scientific Core avec gate médicale/scientifique. Aucun port clinique silencieux sur #379.

### PR #101 — T1 transversal
**SUPERSEDED BY CURRENT MASTER — CLOSED**

Le `master` courant possède déjà une architecture plus récente :
- navigation UI + URL via `useDocumentHubNavigation` ;
- `DocumentTabNavigationPolicy` + dirty-states spécialisés ;
- lifecycle archive/preview/duplicate/print courant dans `useDocumentGenerator` ;
- impression armée seulement après réception du nouveau PDF ;
- échéancier via flux dédié ;
- aucun chemin `ai-diagnostic` trouvé dans la surface générateur Document Studio courante.

L'ancien `DocumentNavigationPolicy.ts` n'est donc pas recréé.

### PR #336 — premium header specialties
**SUPERSEDED — CLOSED**

`master` rend déjà toutes les lignes configurées, suit la profondeur des blocs, repositionne les séparateurs et gère le cas Heritage dense.

### PR #353 — certificate signature caption
**SUPERSEDED BY #379 — CLOSED**

Porté sur #379 :
- ligne de signature conservée ;
- nom praticien conservé ;
- mention imprimée `Signature manuscrite du praticien` retirée ;
- test de régression dédié.

### PR #1 — prescriptions / PWA / OAuth / PDF arabe
**OUTSIDE CURRENT CONSOLIDATION — REVIEW SEPARATELY**

PR historique multi-domaines, 1729 commits derrière `master`. Elle ne doit pas être utilisée comme branche Document Studio. Ses sujets PWA/OAuth/packaging dépassent ce chantier ; elle n'est pas fermée ici sans réconciliation dédiée.

## Deltas réellement portés sur #379
1. prescription local-first stricte + DB failures visibles ;
2. caption de signature certificat nettoyée ;
3. intégrité Devis `items ↔ teeth_data` ;
4. tests de régression associés ;
5. canonique de reprise unique.

## Preuves de nettoyage
- #18 CLOSED sans merge après port utile ;
- #77 CLOSED sans merge après port/supersession ;
- #101 CLOSED sans merge comme superseded ;
- #336 CLOSED sans merge comme superseded ;
- #353 CLOSED sans merge après port utile ;
- #90/#95/#96/#97 étaient déjà fermées non mergées ;
- PR #379 est la seule branche de consolidation Document Studio basée directement sur le master courant.

## Gates restants de #379
1. CI/tests exact-head ;
2. full frontend/backend/build proportionnel au scope ;
3. runtime authentifié des chemins touchés ;
4. PDF certificat + Devis réel ;
5. responsive/visuel uniquement si une surface UI est finalement modifiée ;
6. closeout canonique ;
7. ready/merge après preuves.

## État
**IN PROGRESS — consolidation fonctionnelle effectuée ; certification exact-head restante.**

Aucun pourcentage global n'est déclaré sans preuve mesurable des gates restants.
