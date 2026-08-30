# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p3-multi-supplier`  
**Déploiement Vercel :** aucun sans autorisation explicite.

## Goal chantier
Marketplace d'approvisionnement fiable : produit → panier → commande → fournisseur → réception → stock → réassort, avec autorité serveur, UX claire et preuves automatisées.

## Baseline

| Axe | Poids | Baseline |
|---|---:|---:|
| UX | 20 % | 7.2/10 |
| UI / interaction | 15 % | 7.4/10 non certifié visuellement |
| Fonctionnalités | 25 % | 6.8/10 |
| Engineering | 25 % | 5.8/10 |
| Sécurité / fiabilité | 15 % | 5.2/10 |
| **Pondéré** | **100 %** | **6.5/10** (`6.48` arrondi) |

Potentiel produit séparé : **9.0/10**.

## Roadmap P0 → P11 — 100 EP

| Phase | EP | Résultat | Gate |
|---|---:|---|---|
| **P0 — Baseline & audit** | **8** | audit, score, risques, canonique | mergé/relu sur master |
| **P1 — Trust & sécurité** | **14** | autorité serveur, isolation, RBAC, anti-falsification | 15 tests ciblés + CI backend/frontend + diff |
| **P2 — Order Engine** | **12** | machine d'état serveur, fulfillment, vérité financière, audit trail | transitions/revenus/événements testés |
| **P3 — Multi-fournisseurs** | **8** | split/routage par fournisseur | 2 fournisseurs → 2 commandes E2E |
| **P4 — Catalogue & produits** | **8** | sync/cache/TTL, recherche, merchandising, pagination | fraîcheur/filtres/pagination testés |
| **P5 — UX/UI Marketplace** | **14** | navigation, panier, checkout, contrat formulaire/CTA, accessibilité, responsive | BEFORE/AFTER + E2E + score |
| **P6 — Procurement** | **8** | transport réel, suivi, réception, retours | création → transport → réception |
| **P7 — Stock Intelligence** | **8** | réception-stock, lots/péremptions, min/max, réassort | stock sans double saisie |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revente, rapprochement/reporting | scénarios financiers serveur |
| **P9 — Automatisation fournisseur** | **5** | imports/API, sync prix/dispo, retries | idempotence/retry/sync |
| **P10 — Superadmin Marketplace** | **4** | CRUD complet, supervision, gouvernance | RBAC + audit trail |
| **P11 — Certification finale** | **5** | E2E, sécurité, performance, accessibilité, closeout | tous gates verts |
| **Total** | **100** |  |  |

## Avancement vérifié
- **P0 : 8/8 CLOSED** — PR #301 mergée.
- **P1 : 14/14 CLOSED** — PR #302 mergée sur `master` à `9900aaddebffc593afcd436b5ecceefaf9814f48`.
- **P2 : 12/12 CLOSED** — PR #306 mergée sur `master` à `cbffb626d099af98f6536a2694930753d637522c`.
- **P3 : 0/8 ACTIVE** — PR #304, HEAD `a04f15cdc05fcd172ab038f27d3399dfe41728c7`, gates en cours.
- **P4 : 0/8 DRAFT** — PR #305, implémentation non visuelle déjà préparée, réalignement post-P3 requis avant certification.
- **Global crédité : 34/100 = 34 %.**

## P1 — Trust & sécurité — CLOSED

### Goal
Un client modifié ne peut pas falsifier prix, total, fournisseur ou stratégie commerciale ; les données commerciales administratives sont protégées ; panier et visibilité fournisseur sont isolés.

### Implémenté
1. fournisseur, noms, SKU, prix et totaux reconstruits serveur ;
2. stratégies limitées aux presets serveur ;
3. fournisseur inactif, produit discontinué, produit cross-cabinet et doublon rejetés ;
4. GET commandes et PATCH commercial réservés Superadmin ; POST conservé au cabinet autorisé ;
5. storefront cabinet masque fournisseur inactif + produits associés ;
6. panier local isolé par `employer + user` ; ancienne clé globale ignorée.

### Preuve finale
HEAD certifié `e8380bd895fc37759fe783fa854d4fcbb39a2932` : CI #2246 SUCCESS, T2 #1361 SUCCESS, Patient P7 #660 SUCCESS. PR #302 mergée puis `master` vérifié.

### Gate
**CLOSED — 14/14 EP crédités.**

## P2 — Order Engine — CLOSED

### Goal
Une commande ne peut suivre que des transitions serveur autorisées ; le total fournisseur modifié reste la vérité financière jusqu'au fulfillment ; annulation et changements sont auditables.

### Implémenté
1. graphe serveur explicite `DRAFT → SENT_TO_PARTNER → MODIFIED_AFTER_SEND/CONFIRMED → FULFILLED/CANCELLED` ;
2. `FULFILLED` et `CANCELLED` terminaux ;
3. `currentTotal` modifiable uniquement via `MODIFIED_AFTER_SEND` ;
4. snapshot `sentTotal` conservé ;
5. `currentTotal` fournisseur conservé après confirmation/fulfillment ;
6. annulation remet le revenu reconnu à zéro avec delta ;
7. transitions exposées dans l'API et journalisées ;
8. frontend checkout/CTA volontairement reporté à P5 ; transport fournisseur réel reporté à P6.

### Tests ciblés
- `backend/tests/test_partner_order_engine.py` : **9 invariants**.

### Preuve finale
HEAD certifié avant merge : `fa7fba4ad518d0e04c7367156415a56687aed907`.
- CI #2260 : **SUCCESS** ;
- T2 #1374 : **SUCCESS** ;
- Patient P7 #673 : **SUCCESS** ;
- draft #303 fermé uniquement car l'action connecteur Ready-for-review était cassée ;
- PR #306 recréée non-draft sur le même HEAD certifié puis mergée ;
- merge `master` : `cbffb626d099af98f6536a2694930753d637522c` ;
- post-merge `master` vérifié sur ce SHA.

### Gate
**CLOSED — 12/12 EP crédités.**

## P3 — Multi-fournisseurs — ACTIVE

### Goal
Un panier contenant plusieurs fournisseurs produit exactement une commande canonique par fournisseur, de façon atomique et déterministe.

### Implémenté sur #304
1. validation complète de toutes les lignes avant création ;
2. groupement serveur par fournisseur dans l'ordre d'apparition ;
3. une commande canonique par fournisseur ;
4. commit DB unique pour le lot ; rollback intégral en cas d'erreur ;
5. `batchId` commun dans l'audit trail ;
6. compatibilité mono-fournisseur conservée ;
7. invariant P1 conservé : un builder de commande unitaire reste mono-fournisseur.

### Tests P3
- HTTP réel : 2 fournisseurs → 2 commandes ;
- prix/SKU/fournisseur reconstruits serveur ;
- même `batchId` dans les événements ;
- ligne invalide → 0 commande / 0 événement ;
- ordre fournisseurs/lignes déterministe.

### Gate
CI backend/frontend + T2/Patient sur le HEAD final P3. Aucun EP avant preuve verte.

## P4 — Catalogue & produits — DRAFT

Implémentation déjà préparée sur #305, sans changement visuel :
- cache Marketplace TTL 15 min ;
- contrôle du scope embarqué et purge du cache périmé/invalide ;
- `isFeatured` / `sortOrder` conservés dans le modèle frontend ;
- recherche backend étendue au descriptif long ;
- pagination optionnelle `offset/limit` produits/fournisseurs ;
- tests cache frontend + filtres/recherche/pagination HTTP.

Le réordonnancement visible des cartes reste P5 pour respecter le protocole UI/UX.

## P5 — UI/UX obligatoire
`BEFORE 390/430/768/1280 → Goal → mockup/référence → implémentation → AFTER mêmes viewports → comparaison → accessibilité/E2E → score visuel`.

## Idées prioritaires
Split fournisseur (10/10 valeur), réassort consommation/min-max (10/10), réception-stock (10/10), lots/péremptions (10/10), historique prix/MOQ/délai (9/10), rapprochement facture (9/10).

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas le travail indépendant. Aucun EP sans preuve.

## Reprise
`P0 CLOSED → P1 CLOSED → P2 CLOSED → P3 ACTIVE → P4 DRAFT → P5 → P6 → P7 → P8 → P9 → P10 → P11`

**PR #304 — branche `marketplace/p3-multi-supplier` — P3 ACTIVE.**  
**PR #305 — branche `marketplace/p4-catalog-products` — P4 DRAFT.**  
**Crédit global : 34/100 EP.**  
**Next exact :** certifier P3 ; si vert → merger #304, vérifier master, réaligner #305 sur master puis certifier P4 ; si rouge → diagnostiquer/corriger sans attendre les autres workflows.
