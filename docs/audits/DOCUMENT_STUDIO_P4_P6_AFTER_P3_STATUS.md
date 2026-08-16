# Document Studio — P4/P5/P6 après P3 : statut d’intégration

## Baseline

- Branche : `agent/p4-p6-after-p3`.
- Base exacte : head P3 `338a35d99c30abe77a353f919f424a313eff4a64` (PR #77).
- Objectif : empiler P4 Note Honoraires, P5 Suivi Paiement et le baseline P6 Document Libre sur le code P3 Devis réellement convergé, sans écraser ses contrats.
- Cette branche ne revendique ni certification runtime, ni certification financière, ni production-ready.

## P3 → P4/P5 : intégration réalisée

### Contrat commun `backend/schemas/documents.py`

Fusion manuelle effectuée :
- garde-fous Devis P3 conservés : phases de présentation retirées, FDI adulte/pédiatrique validé, échéancier interdit dans Devis, au moins un acte réel ;
- `payment_status` fermé sur `EN_ATTENTE | PAYE | PARTIEL`, avec `PARTIEL` refusé dans ce flux sans montant encaissé explicite ;
- Honoraires : acte non vide, montant fini, strictement positif et borné ;
- Honoraires `PAYE` : mode de règlement explicite obligatoire ;
- Honoraires `EN_ATTENTE` : aucun mode de règlement requis puisqu’aucun Payment n’est créé ;
- note globale : réconciliation exacte des échéances ;
- échéancier direct : titre, total, lignes, dates et réconciliation contrôlés avant écriture.

## P4 — Note Honoraires

### Implémenté

- validation request + pré-PDF + persistance ;
- aucun Acte nul/négatif/non fini ;
- aucun fallback silencieux vers Espèces pour un encaissement ;
- `PAYE` exige un choix praticien explicite ;
- `EN_ATTENTE` reste neutre ;
- `Acte ↔ Payment` exact conservé ;
- conversion Devis → Honoraires : actes conservés, champs financiers réinitialisés (`paymentMode`, statut, plan global, échéances) ;
- chargement historique P5 retiré du store partagé P3/P4 ;
- suggestion radio financière supprimée du parcours frontend ;
- tests backend et store ajoutés.

### Encore ouvert

- régression full-repo/build réelle ;
- runtime authentifié Honoraires ;
- PDF réel et responsive ;
- rapprochement dossier financier ;
- certification financière séparée.

## P5 — Suivi Paiement

### Implémenté

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

- full-suite/build ;
- runtime authentifié et rapprochement Payment ↔ installment ;
- preview/PDF réel ;
- responsive/accessibilité ;
- certification financière finale.

## P6 — Document Libre

Aucun nouveau P0 statique démontré. Le socle existant reste : contrat/PDF sûr, markup allowlisté, multipage, dirty-state, permission clinique, impression fraîche, archive/réouverture.

### Encore ouvert

- régression réelle frontend/backend/PDF ;
- runtime authentifié ;
- inspection PDF A4/A5, long/multipage/tableaux/caractères spéciaux ;
- responsive 1440/768/390 et clavier/accessibilité.

## Tests ajoutés sur la branche

Backend :
- `test_document_financial_contract_p4_p5.py` ;
- `test_honoraires_financial_contract_p4.py` ;
- `test_honoraires_prearchive_contract_p4.py` ;
- `test_installment_contract_p5.py` ;
- fixtures/régressions historiques Honoraires et Installments réalignées.

Frontend :
- `InstallmentStudio.p5.test.tsx` ;
- `useAccountingStore.p4.test.ts`.

## Infrastructure CI

Les branches P3 et P4/P5 ont rencontré des runs GitHub Actions dont les jobs échouent avant tout step (`steps=null`). Ce défaut d’infrastructure ne vaut ni PASS ni échec applicatif.

## Verdict

**Intégration de code P3 → P4/P5 : réalisée.**

**Certification P4/P5/P6 : encore ouverte** tant qu’une suite réelle, le runtime authentifié et les PDF finaux n’ont pas été exécutés/inspectés.
