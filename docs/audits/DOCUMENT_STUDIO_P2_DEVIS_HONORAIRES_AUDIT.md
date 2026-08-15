# P2 — Devis + Honoraires : audit vérifié en cours

## Statut de preuve

Audit **partiel** basé sur `AccountingStudio.tsx`, `AccountingStudioLegacy.tsx`, `DocumentHub.tsx`, `useDocumentGenerator.ts` et les contrats backend documents/comptabilité.

- **CODE VÉRIFIÉ** : oui, pour les points listés ci-dessous.
- **TESTS EXÉCUTÉS** : P2-A et P2-B certifiés par CI exacte ; autres lots préparatoires non fusionnés restent à recertifier sur leur head final.
- **INTERACTION RUNTIME** : non exécutée à ce stade.
- **CERTIFICATION FINANCIÈRE / PRODUCTION** : non revendiquée.

## P2-A — Recherche catalogue : prix local perdu — CLOSED ✅

### Défaut vérifié
`TREATMENT_TEMPLATES` transporte bien `act.base_price`, mais le legacy `handleActSearch()` transformait les résultats locaux avec `base_price: 0`.

### Correctif fusionné
Le legacy est conservé derrière `AccountingStudio.tsx`, devenu un petit wrapper. Le wrapper répare uniquement les suggestions locales depuis le catalogue existant :
- prix distant/non local inchangé ;
- prix catalogue nul/absent reste nul ;
- aucun prix inventé.

### Preuve engineering
- PR `#27` — **MERGED**.
- Head final certifié : `7289d0bf64c8139838470923622f8c0b588206e1`.
- CI exacte : run `31882328096` — **SUCCESS**.
- Frontend tests/build : ✅ SUCCESS.
- Backend tests/durcissement : ✅ SUCCESS.
- Garde production négative : ✅ SUCCESS.
- Merge squash : `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc`.

---

## P2-B — PARTIEL fail-closed cohérent UI/backend — CLOSED ✅

### Faits vérifiés
La modale d’encaissement exposait `EN_ATTENTE`, `PARTIEL`, `PAYE` tandis que `DocumentRequest` n’a volontairement **aucun champ montant encaissé explicite** et refuse `payment_status=PARTIEL`.

`/documents/generate` crée les lignes `Acte` Honoraires mais ne retourne pas leurs IDs. Un paiement partiel générique ne peut donc pas être réparti proprement entre plusieurs actes depuis ce modal sans règle d’allocation supplémentaire.

Le flux dédié `/accounting/payments` exige un montant réel et accepte un `acte_id`/`installment_id` optionnel.

### Correctif fusionné
- le store comptable refuse `PARTIEL` avant qu’il puisse devenir l’état du document ;
- l’UI expose une raison explicite au lieu de laisser le backend découvrir le mismatch ;
- les statuts inconnus restent fail-closed ;
- `PaymentCreate.amount` doit être strictement positif ;
- les méthodes de règlement sont validées ;
- les alias UI connus sont normalisés explicitement (`TPE → CARTE`, `Espèces → ESPECES`, etc.) ;
- une méthode inconnue ne retombe plus silencieusement sur espèces.

### Historique CI
Premier head `1005f2281868f435b8fb2f56066bc920b3151df5` : frontend/build et garde production verts, backend en échec. La règle métier n’était pas en cause : le validator levait un `ValueError` brut, conservé dans le contexte Pydantic puis non sérialisable par le handler JSON global.

Correctif : `PydanticCustomError` pour l’erreur de méthode de paiement, sans modifier le handler global.

### Preuve engineering finale
- PR `#29` — **MERGED**.
- Head final certifié : `d60a99c290e0e27c84d73fb95d947fa111461f7a`.
- CI exacte : run `31884437013` — **SUCCESS**.
- Frontend tests/build : ✅ SUCCESS.
- Backend tests/durcissement : ✅ SUCCESS.
- Garde production négative : ✅ SUCCESS.
- Merge squash : `6543c3dad146bdbe055117fe0302b3fbe9cbda07`.
- PR préparatoire `#28` fermée sans merge, remplacée par #29.

Aucune certification financière production ni UX runtime n’est revendiquée.

---

## P2-C — Actes rapides, terminologie et organisation par phases

### Faits vérifiés
La barre `Smart Acts` est repliée et s’ouvre principalement via `group-hover`, ce qui n’est pas un contrat fiable sur tactile.

Labels visibles non alignés avec les moteurs réellement déterministes :
- `Smart Acts` ;
- `Combo IA Détecté` ;
- `Intelligence appliquée` ;
- `Studio Clinique Elite` ;
- `Odontogramme & Catalogue Ghost` ;
- `Séquencer avec l'IA` ;
- `Ghost Treasury` ;
- `Flux d'encaissement intelligent`.

Le séquençage est une classification regex frontend. Il injecte en plus `DÉLAI DE CICATRISATION (ESTIMÉ : 3 MOIS)` lorsque chirurgie + prothèse sont détectées, sans donnée patient ni source clinique dans ce flux.

### Décision
- interaction explicite ouvrir/fermer pour les actes rapides ;
- terminologie fonctionnelle (`Actes rapides`, `Suggestions complémentaires`, `Organiser par phases`, `Encaissement`) ;
- conserver un regroupement déterministe des phases mais **ne pas injecter de durée clinique estimée** depuis ce moteur documentaire.

### Préparation technique non fusionnée
Composant tactile `AccountingQuickActions` + tests, et policy déterministe de phases sans durée de cicatrisation préparés sur branche dédiée / PR draft `#32`.

---

## P2-D — Odontogramme / modes / déduplication

### Faits vérifiés
Trois modes sont présents :
- `individual` → soins ciblés 1 dent ;
- `group` → bridge/prothèses + sélections Q1-Q4/S1-S6 ;
- `ortho` → libellé UI `Soins Généraux` et panneau d’actes globaux.

Le `TreatmentSelector` ajoute directement les traitements sélectionnés au panier et enregistre les prix positifs dans `PriceBrain`.

Le composant contient bien `handleTeethFromOdontogram()` avec une stratégie `_odontogramKey = dent::traitement`, mais ce callback est **défini sans aucun appel dans le composant**. La logique de déduplication associée est donc orpheline dans le flux inspecté.

En mode groupe, plusieurs actes utilisent `PriceBrain.suggestPrice(act) || 0` : un acte peut donc être ajouté à 0 MAD lorsque le moteur n’a aucun historique/prix suggéré.

### Décision
- rétablir une source de vérité unique pour les sélections odontogramme ;
- fusion idempotente par clé stable `dent::traitement` ;
- ne jamais supprimer une ligne manuelle lors de la synchronisation ;
- exposer explicitement un prix inconnu plutôt que le traiter silencieusement comme un prix valide à 0.

### Préparation technique non fusionnée
Policy idempotente `AccountingOdontogramPolicy` + tests préparés sur branche dédiée / PR draft `#33`.

---

## P2-E — Total, payload, échéances et réconciliation — ACTIVE 🟡

### Faits vérifiés
Le total affiché est la somme directe des `item.price` numériques :
`items.reduce((acc, it) => acc + (Number(it.price) || 0), 0)`.

Pour Devis/Honoraires, `buildPayload()` filtre les descriptions vides puis transporte chaque ligne sous : `acte`, `dent`, `dents`, `prix_unitaire`, `montant`, `date`, `mode_reglement`.

Les champs `installments` et `is_global_note` sont envoyés dans `payload.data`. Honoraires est normalisé en type backend `note`.

Dans le backend Honoraires global, `InstallmentPlan.total_amount` prend le total facturé, puis chaque échéance est créée avec son montant propre. **Aucune vérification n’impose actuellement que la somme des échéances soit égale au total facturé.**

### Décision
- conserver le calcul total simple ;
- ajouter une réconciliation exacte au centime avant toute persistance d’un plan Honoraires ;
- chaque échéance doit être strictement positive ;
- une somme supérieure ou inférieure au total doit être bloquante, pas silencieuse.

### Préparation technique à reconstruire sur baseline post-P2-B
- policy frontend de réconciliation au centime + tests ;
- utilitaire backend `Decimal` + tests ;
- validation `DocumentRequest` pour Honoraires global uniquement ;
- PR draft `#30` a servi de banc de CI et a passé les trois jobs, mais **ne doit pas être mergée** car sa baseline précède P2-B.

Le flux direct `/accounting/plans` est un contrat partagé avec P4 Échéancier ; son durcissement est suivi séparément afin de ne pas étendre silencieusement P2-E.

---

## P2-F — Effets après archivage Honoraires / encaissement complet

### Faits vérifiés
Après génération archivée réussie d’un document Honoraires, le frontend :
- réinitialise sélection groupe + mode odontogramme ;
- enregistre les actes comme habitudes de manière best-effort ;
- remplace ensuite les lignes Honoraires par une ligne vide.

Le footer réel ne génère pas de document financier non-preview sans archivage : `Enregistrer` appelle `archive=true`, et `Imprimer` exige une confirmation qui relance avec `archive=true`. Le soupçon d’un mismatch archive=false a donc été écarté.

### Défaut comptable vérifié — paiement global non rattaché aux Acte
Pour `PAYE`, `documents/generate` :
1. crée une ligne `Acte` par prestation et la marque `PAYE` ;
2. crée ensuite **un seul `Payment` global** de `total_amount`, sans `acte_id`.

Or `/accounting/actes-billing/patient/{id}` calcule `total_paid` et `remaining_due` par acte uniquement à partir des `Payment.acte_id` correspondants.

Conséquence structurelle possible : un `Acte` est marqué `PAYE` alors que cette vue calcule `total_paid=0` et `remaining_due=montant` pour le même acte.

### Décision
Pour un document totalement réglé, créer une allocation exacte par ligne : un paiement positif par `Acte` créé, rattaché via `acte_id`, avec le montant exact de la ligne. La somme des allocations doit égaler le total facturé au centime. Ne pas conserver en parallèle un paiement global orphelin qui doublerait le total encaissé.

### Préparation technique non fusionnée
Service pur `payment_allocation.py` + tests préparés sur PR draft `#31`. L’intégration DB reste à faire après P2-E.

### Risque UX restant à certifier
Une archive réussie efface immédiatement le panier Honoraires actif. Ce comportement peut être voulu, mais doit être testé en runtime et protégé contre les cas d’erreur partielle ou de besoin de réimpression/correction immédiate.

---

## Ordre de correction P2

1. **P2-A — Prix catalogue local conservé** — ✅ CLOSED.
2. **P2-B — PARTIEL fail-closed cohérent UI/backend** — ✅ CLOSED.
3. **P2-E — Échéances/réconciliation financière exacte** — 🟡 ACTIVE.
4. **P2-F — Allocation PAYE exacte par Acte** — priorité intégrité après P2-E.
5. **P2-C — Actes rapides tactile + terminologie déterministe + phases neutres**.
6. **P2-D — Odontogramme/déduplication/prix groupe**.
7. Recertification runtime ciblée.
