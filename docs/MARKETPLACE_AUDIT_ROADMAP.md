# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p0-trust-integrity`  
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
| **P2 — Order Engine** | **12** | contrat client + machine d'état + fulfillment | transitions/contrat testés |
| **P3 — Multi-fournisseurs** | **8** | split/routage par fournisseur | 2 fournisseurs → 2 commandes E2E |
| **P4 — Catalogue & produits** | **8** | sync/cache/TTL, recherche, merchandising, pagination | fraîcheur/filtres/pagination testés |
| **P5 — UX/UI Marketplace** | **14** | navigation, panier, checkout, accessibilité, responsive | BEFORE/AFTER + E2E + score |
| **P6 — Procurement** | **8** | transport réel, suivi, réception, retours | création → transport → réception |
| **P7 — Stock Intelligence** | **8** | réception-stock, lots/péremptions, min/max, réassort | stock sans double saisie |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revente, rapprochement/reporting | scénarios financiers serveur |
| **P9 — Automatisation fournisseur** | **5** | imports/API, sync prix/dispo, retries | idempotence/retry/sync |
| **P10 — Superadmin Marketplace** | **4** | CRUD complet, supervision, gouvernance | RBAC + audit trail |
| **P11 — Certification finale** | **5** | E2E, sécurité, performance, accessibilité, closeout | tous gates verts |
| **Total** | **100** |  |  |

### Avancement vérifié
- **P0 : 8/8 CLOSED** — PR #301 mergée.
- **P1 : 0/14 EN COURS** — PR #302.
- **Global : 8/100 = 8 %.**

## P1 — Trust & sécurité

### Goal
Un client modifié ne peut pas falsifier prix, total, fournisseur ou stratégie commerciale ; les données commerciales administratives sont protégées ; panier et visibilité fournisseur sont isolés.

### Implémenté sur #302
1. fournisseur, noms, SKU, prix et totaux reconstruits serveur ;
2. stratégies limitées aux presets serveur ;
3. fournisseur inactif, produit discontinué, produit cross-cabinet et doublon rejetés ;
4. mélange fournisseurs rejeté jusqu'au split P3 ;
5. GET commandes et PATCH commercial réservés Superadmin ; POST conservé au cabinet autorisé ;
6. storefront cabinet masque fournisseur inactif + produits associés, Superadmin les conserve en administration ;
7. panier local isolé par `employer + user` ; ancienne clé globale ignorée sans migration.

### Tests ciblés
- `backend/tests/test_partner_orders_integrity.py` : 9
- `backend/tests/test_partner_catalog_visibility.py` : 2
- `frontend/src/features/partnerMarketplace/data.test.ts` : 4
- **Total : 15**

### Preuves intermédiaires
Sur `f9855bbd7cdb6786ce96d42c0239d2ef46320338` : CI #2235 SUCCESS, T2 #1350 SUCCESS, Patient P7 #649 SUCCESS.

Catalog Connected Truth #623 a échoué à `Targeted backend truth tests`, exécutant uniquement `test_catalog_connected_truth.py`, `test_patient_p3_master_plan_revisions.py` et `TestCatalogQuickAdd`. Aucun de ces fichiers n'est modifié par #302. Cause exacte non attribuée sans preuve.

### Gate final P1
Le dernier HEAD de #302 doit prouver : 11 tests backend Marketplace + 4 tests frontend panier verts, suite backend complète verte, frontend tests/build vert et diff revu. Aucun EP avant cette preuve.

## Restant après P1
- P2 : formulaire/contrat, CTA/envoi logique, transitions ;
- P3 : vrai multi-fournisseurs ;
- P4 : TTL, merchandising, pagination ;
- P5 : accessibilité/densité, visuels, reload, responsive certifié ;
- P6 : transport/réception ;
- P7 : stock/réassort ;
- P8 : finance ;
- P9 : sync fournisseur ;
- P10 : admin complet ;
- P11 : certification.

## Idées prioritaires
Split fournisseur (10/10 valeur), réassort consommation/min-max (10/10), réception-stock (10/10), lots/péremptions (10/10), historique prix/MOQ/délai (9/10), rapprochement facture (9/10).

## P5 UI/UX obligatoire
`BEFORE 390/430/768/1280 → Goal → mockup/référence → implémentation → AFTER mêmes viewports → comparaison → accessibilité/E2E → score visuel`.

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas travail indépendant. Aucun EP sans preuve.

## Reprise
`P0 CLOSED → P1 ACTIVE → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11`

**PR #302 — branche `marketplace/p0-trust-integrity` — crédit 8/100 EP.**  
**Next exact :** certifier ce HEAD ; rouge → corriger ; vert → créditer P1, merger #302, vérifier master, démarrer P2.
