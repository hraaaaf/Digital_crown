# P4 — Note Honoraires : audit canonique exhaustif

## Baseline

- Branche audit : `agent/p4-p6-audit-baselines`.
- Baseline source : `master` à `026f78290cda53ea1b07ba5e8bfd39836448d6ce`.
- Portée : page P4 Note Honoraires, panier financier partagé, statut de paiement, modes de règlement, création Acte/Payment, échéancier global, PDF, archive et connexions P3/P5.
- **CODE VÉRIFIÉ** : oui pour les constats ci-dessous.
- **TESTS HISTORIQUES EXÉCUTÉS** : anciens lots P2-B/P2-E/P2-F certifiés par CI exacte selon la roadmap.
- **TEST EXÉCUTÉ SUR CET AUDIT** : non revendiqué.
- **INTERACTION RUNTIME / VISUELLE** : non exécutée dans cette session.
- **CERTIFICATION FINANCIÈRE / PRODUCTION** : non revendiquée.

---

## 1. Architecture réelle P4

Flux principal :

`DocumentHub` → `AccountingStudio` → `AccountingStudioLegacy` → `useAccountingStore` → `useDocumentGenerator` → `/documents/generate` → `HonorairesData` → `create_note_honoraires()` → archive → `persist_honoraires_lines()` → `Acte` / `Payment`.

État partagé important : P3 Devis et P4 Honoraires réutilisent le même panier et plusieurs champs comptables du store.

---

## 2. Matrice produit

### GARDER

1. Permission backend `accounting` + contrôle d'accès patient avant génération.
2. `PARTIEL` refusé fail-closed dans le flux documentaire tant qu'aucun montant encaissé explicite n'existe.
3. Réconciliation exacte des échéances d'une note globale via validation backend avant écriture.
4. Pour `PAYE`, allocation exacte par Acte avec `Payment.acte_id` grâce à `persist_honoraires_lines()`.
5. Méthodes inconnues explicitement rejetées lorsqu'une valeur non vide non reconnue est fournie.
6. Transaction comptable regroupée sous un commit unique pour Acte/Payment/plan.

### AMÉLIORER

1. P3 → P4 doit être une conversion explicite, pas seulement un switch d'onglet sur état partagé.
2. Réimpression/correction immédiate après archivage : le panier est réinitialisé côté frontend ; le workflow doit être testé et rendu explicite.
3. Séparer visuellement « facturé », « encaissé », « restant dû » et « échéancier ».
4. Preview/PDF et responsive à recertifier comme pour P3.

### CORRIGER — P0

#### P0-1 — montants Honoraires non fail-closed au contrat serveur
`PaymentItem.montant` est un `float` par défaut à `0.0` sans borne stricte. `persist_honoraires_lines()` crée une ligne `Acte` avec ce montant, y compris s'il est nul ou négatif.

Pour un document `PAYE`, `is_collected` est dérivé du statut global. Le service saute seulement la création du `Payment` lorsque `amount <= 0`.

**Risque** : ligne Acte marquée PAYE/collectée sans Payment correspondant, ou montant financier invalide accepté dans le document.

**Décision** : backend Honoraires doit refuser toute prestation vide, montant non fini, négatif ou nul selon contrat métier avant PDF/archive/écriture comptable.

#### P0-2 — mode de règlement manquant transformé silencieusement en Espèces
`normalize_document_payment_method(value)` utilise `value or "Espèces"`.

**Risque** : sur un Honoraires `PAYE`, une méthode non renseignée devient un encaissement `ESPECES` sans consentement explicite du praticien.

**Décision** : pour tout encaissement réellement persisté, méthode obligatoire et explicite. Aucun fallback financier silencieux.

### CORRIGER — P1

#### P1-1 — statut de paiement trop permissif dans `DocumentRequest`
`payment_status` est un `Optional[str]` et non un enum/Literal strict. Les valeurs invalides ne sont pas éliminées au contrat d'entrée.

**Décision** : contrat fermé sur `EN_ATTENTE | PAYE` dans ce flux tant que PARTIEL reste dédié au flux d'encaissement explicite.

#### P1-2 — recommandations automatiques non contractuelles après document financier
`/documents/generate` peut produire une suggestion RDV « +4 semaines » selon mots-clés et une suggestion radio après mots-clés prothétiques.

**Décision** : une note d'honoraires ne prouve ni indication clinique, ni timing de contrôle, ni besoin radiographique. Retirer de P4 ou déplacer vers un moteur clinique explicite et validé.

#### P1-3 — apprentissage d'actes couplé à la génération financière
Après génération non-preview, chaque ligne Honoraires est enregistrée comme usage d'acte. La politique doit garantir une source autoritative unique et ne pas compter une tentative échouée/dupliquée.

#### P1-4 — état partagé P3/P4
Le même panier rend la continuité pratique mais crée un risque de transfert implicite de contexte (prix, statut, échéances, mode global) entre pages.

**Décision** : conversion explicite avec snapshot d'origine et champs autorisés, ou reset ciblé des champs non transférables.

---

## 3. Contrat cible P4

Chaque ligne Honoraires persistée doit avoir :
- acte non vide ;
- montant fini et strictement valide ;
- dent(s) structurées si applicable ;
- statut financier explicite ;
- méthode de règlement obligatoire uniquement lorsqu'un encaissement est effectivement créé ;
- correspondance `Acte ↔ Payment` vérifiable ;
- absence de fallback financier silencieux ;
- archive/PDF/écritures comptables issus du même snapshot.

---

## 4. Connexions inter-pages

| Connexion | État code | Verdict |
|---|---|---|
| P3 → P4 | état partagé / switch direct | **P1 AMÉLIORER/CORRIGER** |
| P4 → P5 | plan global possible | **GARDER**, sous contrat exact |
| P4 → dossier patient | archive + Acte/Payment | **GARDER**, après hardening P0 |
| P4 → agenda | suggestion 4 semaines par mots-clés | **SUPPRIMER de P4** |
| P4 → radio | suggestion par mots-clés | **SUPPRIMER de P4** |

---

## 5. Lots correctifs canoniques

1. **P4-A — Contrat financier Honoraires** : montants/actes/statuts stricts, zéro fallback financier.
2. **P4-B — Encaissement explicite** : méthode obligatoire, cohérence `Acte ↔ Payment`.
3. **P4-C — Conversion P3 → P4** : snapshot explicite et isolation de l'état partagé.
4. **P4-D — Échéancier global / P5** : connexion explicite et réconciliation conservée.
5. **P4-E — Nettoyage clinique** : retirer suggestions RDV/radio non contractuelles de la page financière.
6. **P4-F — PDF / UX / responsive / accessibilité**.
7. **P4-G — Recertification finale** : tests ciblés + runtime authentifié + inspection PDF + certification financière séparée.

---

## 6. Gates runtime encore ouverts

- Note vide / ligne vide / montant nul, négatif, très élevé, non fini ;
- EN_ATTENTE vs PAYE ;
- méthode de règlement absente/invalide/valide ;
- plusieurs actes PAYE et rapprochement exact des Payments ;
- note globale avec échéances exactement équilibrées et déséquilibrées ;
- conversion depuis P3 ;
- preview, archive, doublon, réouverture, impression ;
- 1440 / 768 / 390 ; clavier/tactile ;
- lecture du dossier financier après archivage.

Aucune fermeture P4 n'est revendiquée avant ces preuves.
