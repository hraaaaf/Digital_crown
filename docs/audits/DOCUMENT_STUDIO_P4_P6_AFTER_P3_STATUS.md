# Document Studio — P4/P5/P6 après P3 : statut d’intégration

## Baseline

- Branche : `agent/p4-p6-after-p3`.
- Base courante : branche P3 `agent/p3d-devis-phases-learning`.
- Objectif : empiler P4 Note Honoraires, P5 Suivi Paiement et la recertification P6 Document Libre sur le code P3 Devis, sans écraser ses contrats.
- Cette branche ne revendique ni certification runtime, ni certification financière, ni production-ready.

## P3 → P4/P5 : intégration réalisée

### Contrat commun `backend/schemas/documents.py`

Fusion effectuée :
- garde-fous Devis P3 conservés : phases de présentation retirées, FDI adulte/pédiatrique validé, échéancier interdit dans Devis, au moins un acte réel ;
- `payment_status` fermé sur `EN_ATTENTE | PAYE | PARTIEL`, avec `PARTIEL` refusé dans ce flux sans montant encaissé explicite ;
- Honoraires : acte non vide, montant fini, strictement positif et borné ;
- Honoraires `PAYE` : mode de règlement explicite obligatoire ;
- Honoraires `EN_ATTENTE` : aucun mode de règlement requis ni conservé ;
- note globale : réconciliation exacte des échéances ;
- échéancier direct P5 : titre, total, lignes, dates et réconciliation contrôlés avant écriture.

## P4 — Note Honoraires

### Engineering implémenté

- validation request + pré-PDF + persistance ;
- aucun Acte nul/négatif/non fini ;
- aucun fallback silencieux vers Espèces ;
- `PAYE` exige un choix praticien explicite ;
- `EN_ATTENTE` reste neutre côté store, payload et serveur ;
- `Acte ↔ Payment` exact conservé ;
- conversion Devis → Honoraires : actes conservés, champs financiers réinitialisés (`paymentMode`, statut, plan global, échéances) ;
- historique P5 retiré du store partagé P3/P4 ;
- aucune indication radio déduite de mots-clés d’un document financier ;
- aucune suggestion RDV financière générique ;
- une note portant des échéances exige désormais des dates explicites avant PDF/archive : aucune date financière ne doit être synthétisée depuis l’horloge runtime ;
- tests backend et store ajoutés/alignés.

### Encore ouvert

- exécution réelle du harness et de la full-suite/build ;
- runtime authentifié Honoraires ;
- PDF réel et responsive ;
- rapprochement dossier financier ;
- certification financière séparée.

## P5 — Suivi Paiement

### Engineering implémenté

- contrat serveur strict pour création/preview/mutation ;
- réconciliation exacte au centime ;
- endpoint `/patient/{patient_id}/latest` déterministe ;
- plan payé non supprimable sans contrepassation ;
- échéance payée non réouvrable/rechiffrable ;
- UI `brouillon → équilibre → enregistrement → encaissement` ;
- aucun checkbox local présenté comme paiement réel ;
- aucun mode de règlement présélectionné ;
- encaissement impossible avant choix explicite ;
- montants persistés figés ;
- résumé total/payé/restant ;
- WhatsApp reste une ouverture manuelle ;
- P5 charge son propre plan et ne contamine plus le store P3/P4.

### Encore ouvert

- full-suite/build réelle ;
- runtime authentifié et rapprochement `Payment ↔ installment` ;
- preview/PDF réel ;
- responsive/accessibilité ;
- certification financière finale.

## P6 — Document Libre

Aucun nouveau P0 statique démontré. Le socle existant reste : contrat/PDF sûr, markup allowlisté, multipage, dirty-state, permission clinique, impression fraîche, archive/réouverture.

### Couverture automatisée identifiée/ajoutée

Déjà présente :
- titre/contenu explicites ;
- A4/A5 et alignements fermés ;
- échappement markup et balises déséquilibrées ;
- nom de fichier sûr ;
- âge à la date du document ;
- branding employeur ;
- PDF long multipage avec taille de corps minimale ;
- permission `clinical` ;
- titre avec caractères spéciaux ;
- erreurs frontend et toolbar non-submit.

Ajoutée sur cette branche :
- matrice PDF A4/A5 sur dimensions réelles ;
- destinataire/date personnalisés ;
- tableau Markdown lisible dans le PDF.

### Encore ouvert

- exécution réelle frontend/backend/PDF sur le head final ;
- runtime authentifié ;
- inspection visuelle PDF cabinet : A4/A5, long/multipage, tableaux, caractères spéciaux ;
- responsive 1440/768/390 et clavier/accessibilité.

## Harness de certification

`scripts/certify_document_studio_p3_p6.sh` est le gate automatisé fail-closed du stack P3→P6.

Il exige :
1. Python 3.12 / Node 20 / worktree propre ;
2. prod-safety positif ;
3. régression backend ciblée P3→P6 ;
4. full backend ;
5. régression frontend ciblée P4→P6 ;
6. full frontend ;
7. build frontend ;
8. prod-safety négatif.

Le script annonce explicitement que runtime authentifié, visuel PDF, responsive et certification financière restent des gates manuels séparés.

**État de preuve actuel : harness écrit mais pas encore exécuté avec résultat observé sur le head final.**

## Infrastructure CI

Les branches P3 et P4/P5 ont rencontré des runs GitHub Actions qui pouvaient échouer avant tout step (`steps=null`). Un défaut runner/billing ne vaut ni PASS ni échec applicatif.

La CI du head final doit être vérifiée une fois après le closeout documentaire. Si elle ne démarre pas réellement, la certification automatisée reste ouverte.

## Anomalie non bloquante consignée

Le commit de suppression de l’inférence radio a aussi compacté sur une ligne un appel de log RVG sans changer son comportement. C’est du bruit de diff, pas un changement fonctionnel ; ne pas l’interpréter comme une modification RVG.

## Verdict

**Intégration engineering P3 → P4/P5 : réalisée sur la branche.**

**Couverture automatisée P6 et harness P3→P6 : préparés mais non exécutés.**

**Certification P4/P5/P6 : ouverte** tant que la suite réelle, le runtime authentifié et les PDF finaux n’ont pas été exécutés/inspectés sur un head exact.
