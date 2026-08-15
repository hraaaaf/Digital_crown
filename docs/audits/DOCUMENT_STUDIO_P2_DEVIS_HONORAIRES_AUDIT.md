# P2 — Devis + Honoraires : audit vérifié en cours

## Statut de preuve

Audit **partiel** basé sur `AccountingStudio.tsx`, `AccountingStudioLegacy.tsx`, `DocumentHub.tsx`, `useDocumentGenerator.ts` et les contrats backend documents/comptabilité.

- **CODE VÉRIFIÉ** : oui, pour les points listés ci-dessous.
- **TESTS EXÉCUTÉS** : P2-A, P2-B et P2-E certifiés par CI exacte ; autres lots restent à recertifier sur leur head final.
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
Composant tactile `AccountingQuickActions` + tests, et policy déterministe de phases sans durée de cicatrisation préparés sur branche dédiée / PR draft `#32`. Banc CI `31884466342` : 3/3 jobs SUCCESS.

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
Policy idempotente `AccountingOdontogramPolicy` + tests préparés sur branche dédiée / PR draft `#33`. Banc CI `31884472613` : 3/3 jobs SUCCESS.

---

## P2-E — Total, payload, échéances et réconciliation — CLOSED ✅

### Défaut vérifié
Pour Honoraires global, `InstallmentPlan.total_amount` prenait le total facturé, puis les échéances étaient persistées depuis les montants bruts sans imposer que leur somme soit égale au total facturé.

### Correctif fusionné
- réconciliation backend exacte au centime via `Decimal` ;
- chaque échéance doit être strictement positive ;
- sous-allocation et sur-allocation bloquées par `DocumentRequest` **avant écriture DB** ;
- validation limitée au flux global `note/honoraires` avec échéances ;
- Devis et Honoraires non global ne sont pas élargis silencieusement ;
- policy frontend miroir en centimes avec écart déterministe ;
- valeurs financières non finies/invalides fail-closed.

Le flux direct `/accounting/plans` reste un contrat partagé avec P4 Échéancier et n’a pas été modifié dans P2-E.

### Preuve engineering finale
- PR `#34` — **MERGED**.
- Head final certifié : `97c3f43019b5eee781da220ef27ef14053593311`.
- CI exacte : run `31885119569` — **SUCCESS**.
- Frontend tests/build : ✅ SUCCESS.
- Backend tests/durcissement : ✅ SUCCESS.
- Garde production négative : ✅ SUCCESS.
- Merge squash : `cb265a8070307d3e3be2e76b239af7762254dddd`.
- PR draft `#30` fermée sans merge ; elle ne servait que de banc de CI pré-P2-B.

Aucune certification financière production ni UX runtime n’est revendiquée.

---

## P2-F — Effets après archivage Honoraires / encaissement complet — ACTIVE 🟡

### Faits vérifiés
Après génération archivée réussie d’un document Honoraires, le frontend :
- réinitialise sélection groupe + mode odontogramme ;
- enregistre les actes comme habitudes de manière best-effort ;
- remplace ensuite les lignes Honoraires par une ligne vide.

Le footer réel ne génère pas de document financier non-preview sans archivage : `Enregistrer` appelle `archive=true`, et `Imprimer` exige une confirmation qui relance avec `archive=true`. Le soupçon d’un mismatch archive=false a donc été écarté.

### Défaut comptable confirmé statiquement ET dynamiquement
Pour `PAYE`, l’ancien `documents/generate` :
1. créait une ligne `Acte` par prestation et la marquait `PAYE` ;
2. créait ensuite **un seul `Payment` global** de `total_amount`, sans `acte_id`.

Or `/accounting/actes-billing/patient/{id}` calcule `total_paid` et `remaining_due` par acte uniquement à partir des `Payment.acte_id` correspondants.

Banc CI préparatoire `31885269345` : frontend/build et garde production SUCCESS ; backend échoue exactement sur le test d’intégration P2-F après création de deux actes PAYE : `assert len(payments) == 2`, valeur réelle `1`. Le run s’arrête à `1 failed, 788 passed, 3 skipped`.

### Candidat final en cours
PR `#36`, head `4d0268f3c910ea85acde3a951e818da9210610ab` :
- service transactionnel `persist_honoraires_lines()` ;
- un `Payment` exact par `Acte` PAYE, lié via `acte_id` ;
- mode de règlement normalisé par ligne, inconnu refusé ;
- plan global reste `EN_ATTENTE` sans encaissement immédiat ;
- suppression du paiement global orphelin ;
- commit unique du lot comptable Document Studio ;
- branche post-P2-E, ahead 6 / behind 0, diff 6 fichiers.

CI finale `31885911487` en cours. Aucun closeout P2-F revendiqué avant verdict exact-head complet.

### Risque UX restant à certifier
Une archive réussie efface immédiatement le panier Honoraires actif. Ce comportement peut être voulu, mais doit être testé en runtime et protégé contre les cas d’erreur partielle ou de besoin de réimpression/correction immédiate.

---

## Ordre de correction P2

1. **P2-A — Prix catalogue local conservé** — ✅ CLOSED.
2. **P2-B — PARTIEL fail-closed cohérent UI/backend** — ✅ CLOSED.
3. **P2-E — Échéances/réconciliation financière exacte** — ✅ CLOSED.
4. **P2-F — Allocation PAYE exacte par Acte** — 🟡 ACTIVE, PR #36.
5. **P2-C — Actes rapides tactile + terminologie déterministe + phases neutres**.
6. **P2-D — Odontogramme/déduplication/prix groupe**.
7. Recertification runtime ciblée.
