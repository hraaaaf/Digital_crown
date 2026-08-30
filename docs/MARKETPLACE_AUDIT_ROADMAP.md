# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `master` — prochain lot P4  
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
| **P1 — Trust & sécurité** | **14** | autorité serveur, isolation, RBAC, anti-falsification | tests ciblés + CI |
| **P2 — Order Engine** | **12** | machine d'état, vérité financière, audit trail | graphe/revenus/événements testés |
| **P3 — Multi-fournisseurs** | **8** | split/routage par fournisseur | 2 fournisseurs → 2 commandes atomiques |
| **P4 — Catalogue & produits** | **8** | cache/TTL, recherche, merchandising, pagination | fraîcheur/filtres/pagination testés |
| **P5 — UX/UI Marketplace** | **14** | navigation, panier, checkout, CTA, a11y, responsive | BEFORE/AFTER + E2E + score |
| **P6 — Procurement** | **8** | transport réel, suivi, réception | création → transport → réception |
| **P7 — Stock Intelligence** | **8** | réception-stock, lots/péremptions, min/max, réassort | stock sans double saisie |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revente, rapprochement/reporting | scénarios financiers serveur |
| **P9 — Automatisation fournisseur** | **5** | imports/API, sync prix/dispo, retries | idempotence/retry/sync |
| **P10 — Superadmin Marketplace** | **4** | CRUD complet, supervision, gouvernance | RBAC + audit trail |
| **P11 — Certification finale** | **5** | E2E, sécurité, performance, accessibilité, closeout | tous gates verts |
| **Total** | **100** |  |  |

## Avancement vérifié
- **P0 : 8/8 CLOSED** — PR #301 mergée.
- **P1 : 14/14 CLOSED** — PR #302 ; merge `master` `9900aaddebffc593afcd436b5ecceefaf9814f48`.
- **P2 : 12/12 CLOSED** — PR #306 ; merge `master` `cbffb626d099af98f6536a2694930753d637522c`.
- **P3 : 8/8 CLOSED** — PR #309 ; merge `master` `5f773491a58bc552c35aeb7dddd078a058f3c417`.
- **P4 : 0/8 EN COURS** — implémentation non visuelle préparée ; reconstruction sur le `master` post-P3 requise avant certification.
- **Global CLOSED : 42/100 = 42 %.**

## P1 — Trust & sécurité — CLOSED

### Goal
Un client modifié ne peut pas falsifier prix, total, fournisseur ou stratégie commerciale ; données commerciales administratives protégées ; panier et visibilité fournisseur isolés.

### Preuve finale
HEAD certifié `e8380bd895fc37759fe783fa854d4fcbb39a2932` : CI #2246 SUCCESS, T2 #1361 SUCCESS, Patient P7 #660 SUCCESS. PR #302 mergée puis `master` vérifié.

## P2 — Order Engine — CLOSED

### Goal
Transitions serveur autorisées uniquement ; total fournisseur modifié conservé comme vérité financière ; annulation et changements auditables.

### Preuve finale
HEAD certifié `fa7fba4ad518d0e04c7367156415a56687aed907` : CI #2260 SUCCESS, T2 #1374 SUCCESS, Patient P7 #673 SUCCESS. PR #306 mergée ; `master` vérifié à `cbffb626d099af98f6536a2694930753d637522c`.

## P3 — Multi-fournisseurs — CLOSED

### Goal
Un panier contenant plusieurs fournisseurs produit exactement une commande canonique par fournisseur, atomiquement et de façon déterministe.

### Implémenté
1. validation complète des lignes avant écriture ;
2. groupement serveur par fournisseur dans l'ordre d'apparition ;
3. une commande canonique par fournisseur ;
4. commit DB unique et rollback intégral ;
5. `batchId` commun dans l'audit trail ;
6. compatibilité mono-fournisseur conservée ;
7. invariant P1 mono-fournisseur conservé ;
8. gate Catalog historique réparé pour synchroniser les dépendances AFTER du HEAD sans affaiblir les tests.

### Preuve finale
HEAD produit `a7c26947d1ebcfde0bc95149237d1058245eee1a` : CI #2310 SUCCESS, Catalog #696 SUCCESS, T2 #1423 SUCCESS, Patient #722 SUCCESS.  
HEAD closeout `b2c18bc458a953e8d470f0dc9231a616e2602d8f` : CI #2317 SUCCESS, Catalog #703 SUCCESS, T2 #1430 SUCCESS, Patient #729 SUCCESS.  
PR #309 squash-mergée ; `master` vérifié à **`5f773491a58bc552c35aeb7dddd078a058f3c417`**.

### Gate
**CLOSED — 8/8 EP crédités.**

## P4 — Catalogue & produits — EN COURS

Lot non visuel déjà préparé et à reconstruire sur le master post-P3 :
- cache Marketplace TTL 15 min ;
- contrôle scope embarqué + purge cache périmé/invalide ;
- `isFeatured` / `sortOrder` conservés dans le modèle frontend ;
- recherche backend étendue au descriptif long ;
- pagination `offset/limit` produits/fournisseurs avec bornes ;
- tests cache frontend + filtres/recherche/pagination HTTP.

Le réordonnancement visible reste P5 afin de respecter le protocole UI/UX.

## P5 — UI/UX obligatoire
`BEFORE 390/430/768/1280 → Goal → mockup/référence → implémentation → AFTER mêmes viewports → comparaison → accessibilité/E2E → score visuel`.

Le harness BEFORE existe mais son ancien run est resté bloqué lors de l'arrêt du serveur Vite ; correctif d'infrastructure préparé, sans changement UI.

## P6 — Procurement — préparation parallèle, 0/8 crédité
Travail non crédité tant que rebase/certification absents : réception partielle idempotente, réconciliation, accusé fournisseur/ETA/backorder, et transport HTTP fournisseur avec preuve/idempotence en cours de validation. Aucun envoi externe réel n'est revendiqué sans test/CI.

## Idées prioritaires
Split fournisseur (10/10 valeur), réassort consommation/min-max (10/10), réception-stock (10/10), lots/péremptions (10/10), historique prix/MOQ/délai (9/10), rapprochement facture (9/10).

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas le travail indépendant. Aucun EP CLOSED sans closeout complet.

## Reprise
`P0 CLOSED → P1 CLOSED → P2 CLOSED → P3 CLOSED → P4 EN COURS → P5 → P6 → P7 → P8 → P9 → P10 → P11`

**Crédit CLOSED : 42/100 EP.**  
**Next exact :** reconstruire P4 sur `master` `5f773491a58bc552c35aeb7dddd078a058f3c417`, certifier son diff strict, puis merge P4 ; en parallèle obtenir l'artefact P5 BEFORE corrigé et faire tourner les tests P6.
