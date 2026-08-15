# P2 — Devis + Honoraires : audit vérifié en cours

## Statut de preuve

Audit **partiel** basé sur `AccountingStudio.tsx`, `DocumentHub.tsx`, `useDocumentGenerator.ts` et le contrat backend déjà durci sur les paiements.

- **CODE VÉRIFIÉ** : oui, pour les points listés ci-dessous.
- **TESTS IDENTIFIÉS/EXÉCUTÉS** : à compléter par lot.
- **INTERACTION RUNTIME** : non exécutée à ce stade.
- **CERTIFICATION FINANCIÈRE / PRODUCTION** : non revendiquée.

## P2-1 — Recherche catalogue : prix local perdu

### Fait vérifié
`TREATMENT_TEMPLATES` transporte bien `act.base_price`, mais le legacy `handleActSearch()` transforme les résultats locaux avec `base_price: 0`.

### Conséquence
Une suggestion issue du catalogue local affiche/applique 0 MAD alors que le prix de base existe dans le catalogue.

### Décision
**P0 fonctionnel P2.** Conserver le `base_price` source lors de la construction des suggestions locales.

### Correctif candidat
Le lot P2-A conserve le legacy intact derrière un wrapper et répare uniquement les suggestions locales depuis le catalogue existant. Prix distant/non local inchangé ; prix catalogue nul/absent reste nul ; aucun prix inventé.

---

## P2-2 — Smart Acts dépend du hover

### Fait vérifié
La barre `Smart Acts` est visuellement repliée (`max-w-[220px]`, `max-h-[46px]`, contenu `opacity-0`) et s’ouvre principalement via `group-hover`.

### Conséquence
Le chemin principal des actes rapides est peu fiable sur tactile/mobile, où le hover n’est pas un contrat d’interaction robuste.

### Décision
**REFAIRE L’INTERACTION, PAS LA SOURCE DE DONNÉES.** Contrôle explicite ouvrir/fermer ou quick-picks toujours visibles sur mobile.

---

## P2-3 — Terminologie IA/Ghost non alignée avec moteur déterministe

### Faits vérifiés
Labels visibles dans le flux comptable :
- `Smart Acts`
- `Combo IA Détecté`
- `Intelligence appliquée`
- `Studio Clinique Elite`
- `Odontogramme & Catalogue Ghost`
- `Séquencer avec l'IA`
- `Ghost Treasury`
- `Flux d'encaissement intelligent`

Le séquençage inspecté est une classification regex déterministe côté frontend.

### Décision
**R7/P6 transversal à appliquer à P2** : terminologie fonctionnelle (`Actes rapides`, `Suggestions complémentaires`, `Organiser par phases`, `Encaissement`).

---

## P2-4 — Statut PARTIEL exposé mais contrat backend fail-closed

### Faits vérifiés
La modale d’encaissement expose `EN_ATTENTE`, `PARTIEL`, `PAYE`.

`useDocumentGenerator.buildPayload()` transmet `payment_status` au niveau racine vers `/documents/generate`.

Le contrat backend `DocumentRequest` refuse déjà `payment_status=PARTIEL` lorsqu’aucun montant encaissé explicite n’est fourni, afin d’empêcher l’ancienne inférence arbitraire de 50 %.

### Conséquence
Le mismatch est certain : l’UI propose une valeur que ce flux backend doit refuser. Aucun champ montant encaissé explicite n’est transmis par ce payload.

### Décision
**P0 cohérence financière.** Masquer/désactiver `PARTIEL` dans ce flux tant qu’aucun montant explicite n’est saisi, ou ajouter un vrai flux de montant encaissé explicite. Aucune valeur ne doit être estimée.

---

## P2-5 — Total et payload

### Faits vérifiés
Le total affiché est la somme directe des `item.price` numériques :
`items.reduce((acc, it) => acc + (Number(it.price) || 0), 0)`.

Pour Devis/Honoraires, `buildPayload()` filtre les descriptions vides puis transporte chaque ligne sous : `acte`, `dent`, `dents`, `prix_unitaire`, `montant`, `date`, `mode_reglement`.

Les champs `installments` et `is_global_note` sont bien envoyés dans `payload.data` pour les deux variantes. Honoraires est normalisé en type backend `note`.

### Statut
Pas de bug arithmétique identifié dans l’expression de total elle-même. Restent à certifier : arrondis, doublons odontogramme, correspondance stricte total/payload/backend et effets des lignes de phase à 0.

---

## P2-6 — Odontogramme / modes

### Faits vérifiés
Trois modes sont présents :
- `individual` → soins ciblés 1 dent ;
- `group` → bridge/prothèses + sélections Q1-Q4/S1-S6 ;
- `ortho` → libellé UI `Soins Généraux` et panneau d’actes globaux.

Le `TreatmentSelector` ajoute les traitements sélectionnés au panier et enregistre les prix positifs dans `PriceBrain`.

En mode groupe, plusieurs actes utilisent `PriceBrain.suggestPrice(act) || 0` : un acte peut donc être ajouté à 0 MAD lorsque le moteur n’a aucun historique/prix suggéré.

### Points à certifier ensuite
- déduplication dent/traitement ;
- retour/annulation sans mutation ;
- cohérence surfaces/dents ;
- traitement explicite des prix groupe inconnus ;
- comportement tactile/mobile de la barre flottante.

---

## P2-7 — Effets après archivage Honoraires

### Fait vérifié
Après génération archivée réussie d’un document Honoraires, le frontend :
- réinitialise sélection groupe + mode odontogramme ;
- enregistre les actes comme habitudes de manière best-effort ;
- remplace ensuite les lignes Honoraires par une ligne vide.

### Risque UX à certifier
Une archive réussie efface donc immédiatement le panier Honoraires actif. Ce comportement peut être voulu, mais doit être testé en runtime et protégé contre les cas d’erreur partielle ou de besoin de réimpression/correction immédiate.

---

## Ordre de correction P2 recommandé

1. **P2-A — Prix catalogue local conservé**.
2. **P2-B — PARTIEL fail-closed cohérent UI/backend**.
3. **P2-C — Actes rapides tactile + terminologie déterministe**.
4. **P2-D — Odontogramme/déduplication/prix groupe**.
5. **P2-E — Totaux, payload, preview et persistance**.
6. **P2-F — Honoraires/échéances/encaissement complet**.
7. Recertification runtime ciblée.
