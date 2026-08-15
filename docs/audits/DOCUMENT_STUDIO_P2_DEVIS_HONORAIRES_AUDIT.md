# P2 — Devis + Honoraires : audit vérifié en cours

## Statut de preuve

Audit **partiel** basé sur `AccountingStudio.tsx`, `DocumentHub.tsx` et le contrat backend déjà durci sur les paiements.

- **CODE VÉRIFIÉ** : oui, pour les points listés ci-dessous.
- **TESTS IDENTIFIÉS/EXÉCUTÉS** : à compléter par lot.
- **INTERACTION RUNTIME** : non exécutée à ce stade.
- **CERTIFICATION FINANCIÈRE / PRODUCTION** : non revendiquée.

## P2-1 — Recherche catalogue : prix local perdu

### Fait vérifié
`TREATMENT_TEMPLATES` transporte bien `act.base_price`, mais `handleActSearch()` transforme les résultats locaux avec `base_price: 0`.

### Conséquence
Une suggestion issue du catalogue local affiche/applique 0 MAD alors que le prix de base existe dans le catalogue.

### Décision
**P0 fonctionnel P2.** Conserver le `base_price` source lors de la construction des suggestions locales.

### Correctif préparé
`AccountingActSuggestionPolicy.ts` + test dédié préservent le prix catalogue. Intégration dans `AccountingStudio` encore à faire.

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

### Fait vérifié
La modale d’encaissement expose `EN_ATTENTE`, `PARTIEL`, `PAYE`.

Le contrat backend `DocumentRequest` refuse déjà `payment_status=PARTIEL` lorsqu’aucun montant encaissé explicite n’est fourni, afin d’empêcher l’ancienne inférence arbitraire de 50 %.

### Conséquence
L’UI propose actuellement une action que le backend doit refuser. Le praticien peut donc sélectionner `Partiel`, confirmer, puis tomber sur une erreur de validation plutôt que saisir un montant réel.

### Décision
**P0 cohérence financière.** Soit masquer/désactiver `PARTIEL` dans ce flux tant qu’aucun montant explicite n’est saisi, soit ajouter un champ montant encaissé et transmettre ce montant via le flux comptable dédié. Aucune valeur ne doit être estimée.

---

## P2-5 — Total

### Fait vérifié
Le total affiché est la somme directe des `item.price` numériques :
`items.reduce((acc, it) => acc + (Number(it.price) || 0), 0)`.

### Statut
Pas de bug arithmétique identifié dans cette expression. Les prochaines vérifications doivent porter sur : lignes de phase à 0, doublons issus de l’odontogramme, arrondis, persistance et correspondance avec le payload généré.

---

## P2-6 — Odontogramme / modes

### Faits vérifiés
Trois modes sont présents :
- `individual` → soins ciblés 1 dent ;
- `group` → bridge/prothèses + sélections Q1-Q4/S1-S6 ;
- `ortho` → libellé UI `Soins Généraux` et panneau d’actes globaux.

Le `TreatmentSelector` ajoute les traitements sélectionnés au panier et enregistre les prix positifs dans `PriceBrain`.

### Points à certifier ensuite
- déduplication dent/traitement ;
- retour/annulation sans mutation ;
- cohérence surfaces/dents ;
- prix 0 quand `PriceBrain` n’a pas de suggestion en mode groupe ;
- comportement tactile/mobile de la barre flottante.

---

## Ordre de correction P2 recommandé

1. **P2-A — Prix catalogue local conservé**.
2. **P2-B — PARTIEL fail-closed cohérent UI/backend**.
3. **P2-C — Actes rapides tactile + terminologie déterministe**.
4. **P2-D — Odontogramme/déduplication/prix groupe**.
5. **P2-E — Totaux, payload, preview et persistance**.
6. **P2-F — Honoraires/échéances/encaissement complet**.
7. Recertification runtime ciblée.
