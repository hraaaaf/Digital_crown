# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p0-trust-integrity`  
**Référence code auditée initiale :** `master @ f19df12739fc262adb2238db1842813b4a820619`  
**Déploiement Vercel :** aucun, non requis sans autorisation explicite.

---

## 1. Goal / Succès / Preuve

### Goal
Transformer le Marketplace Digital Crown en module d'approvisionnement fiable, rapide et cohérent : découverte produit → panier → commande → fournisseur → réception → stock → réassort, avec une UX claire et un contrat engineering sûr.

### Succès
Autorité serveur financière, RBAC Marketplace explicite, multi-fournisseurs déterministe, cycle commande traçable jusqu'à réception, UI certifiée BEFORE/AFTER, tests backend/frontend/E2E, réception-stock cohérente et tous gates finaux verts.

### Preuve
Code + tests automatisés + runtime observé + captures UI quand la phase est visuelle + CI + canonique cohérent. Aucun score visuel certifié sans captures runtime.

---

## 2. Baseline et score

Capacités vérifiées au baseline : catalogue fournisseurs/produits, recherche/filtres, pages fournisseur/produit, panier local, commande serveur, stratégies commerciales, superadmin catalogue/rapprochement, CRUD catalogue et événements/revenu.

| Axe | Poids | Baseline |
|---|---:|---:|
| UX | 20 % | 7.2/10 |
| UI / interaction | 15 % | 7.4/10 non certifié visuellement |
| Fonctionnalités | 25 % | 6.8/10 |
| Engineering | 25 % | 5.8/10 |
| Sécurité / fiabilité | 15 % | 5.2/10 |
| **Pondéré** | **100 %** | **6.5/10** (`6.48` arrondi) |

**Potentiel produit : 9.0/10**, distinct du score courant.

---

## 3. Roadmap canonique P0 → P11 — 100 EP

| Phase | EP | Ce qu'elle fait | Gate principal |
|---|---:|---|---|
| **P0 — Baseline & audit** | **8** | audit, score, risques, roadmap | canonique mergé/relu sur master |
| **P1 — Trust & sécurité** | **14** | autorité serveur, isolation, RBAC, fournisseurs actifs, anti-falsification | 15 tests ciblés + CI backend/frontend verts + diff revu |
| **P2 — Order Engine** | **12** | contrat client, transitions, envoi logique, confirmation, modification, annulation, fulfillment | machine d'état + tests transitions/contrat |
| **P3 — Multi-fournisseurs** | **8** | panier multi-fournisseurs et split/routage | 2 fournisseurs → 2 commandes correctes E2E |
| **P4 — Catalogue & produits** | **8** | sync/cache/TTL, recherche, merchandising, disponibilité, pagination | fraîcheur + filtres + pagination + tests |
| **P5 — UX/UI Marketplace** | **14** | navigation, panier, checkout, accessibilité, responsive | BEFORE/AFTER 390/430/768/1280 + E2E + score |
| **P6 — Procurement** | **8** | transport fournisseur, suivi, réception, retours/backorders | création → transport → réception prouvés |
| **P7 — Stock Intelligence** | **8** | réception-stock, lots/péremptions, min/max, réassort | stock alimenté sans double saisie + tests |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revente, rapprochement, annulations/reporting | scénarios financiers serveur testés |
| **P9 — Automatisation fournisseur** | **5** | imports/API, sync prix/dispo, retries | panne/retry/idempotence + preuve sync |
| **P10 — Superadmin Marketplace** | **4** | CRUD complet, supervision, métriques, gouvernance | RBAC + audit trail + actions testées |
| **P11 — Certification finale** | **5** | E2E réel, sécurité, multi-cabinet, performance, accessibilité, closeout | tous gates verts + canonique cohérent |
| **Total** | **100** |  |  |

### Avancement vérifié
- **P0 : 8/8 — CLOSED**, PR #301 mergée.
- **P1 : 0/14 — EN COURS**, PR #302.
- **Global : 8/100 = 8 %.**

---

## 4. P1 — Trust & sécurité

### Goal
Empêcher un client modifié de falsifier une commande financière et empêcher un utilisateur non autorisé d'exposer/modifier les données commerciales d'administration, tout en isolant panier et fournisseurs inactifs.

### Implémenté sur PR #302
1. fournisseur résolu serveur ;
2. nom/SKU/prix/line total reconstruits serveur ;
3. total recalculé serveur ;
4. stratégie limitée aux presets serveur ;
5. fournisseur inactif refusé à la commande ;
6. produit discontinué, cross-cabinet et doublon refusés ;
7. mélange fournisseurs rejeté jusqu'au split P3 ;
8. GET commandes et PATCH commercial réservés Superadmin ;
9. POST commande conservé au cabinet autorisé ;
10. storefront cabinet masque fournisseurs inactifs et produits associés ;
11. Superadmin conserve leur visibilité d'administration ;
12. panier isolé par `employer + user`, ancienne clé globale ignorée sans migration.

### Tests ciblés P1
- `backend/tests/test_partner_orders_integrity.py` : **9**
- `backend/tests/test_partner_catalog_visibility.py` : **2**
- `frontend/src/features/partnerMarketplace/data.test.ts` : **4**
- **Total : 15**

### Preuves intermédiaires
Sur `f9855bbd7cdb6786ce96d42c0239d2ef46320338` :
- CI #2235 : **SUCCESS**, backend suite + frontend tests/build + durcissement verts ;
- T2 Runtime #1350 : **SUCCESS** ;
- Patient P7 #649 : **SUCCESS** ;
- Catalog Connected Truth #623 : **FAILURE** à `Targeted backend truth tests`, qui exécute `test_catalog_connected_truth.py`, `test_patient_p3_master_plan_revisions.py` et `TestCatalogQuickAdd`. Aucun de ces fichiers n'est modifié par #302 ; cause exacte non attribuée sans preuve.

### Gate final P1
Le **HEAD final de #302** doit avoir : 11 tests backend Marketplace + 4 tests frontend panier verts, CI backend complète verte, CI frontend tests/build verte, diff final revu. Le workflow Catalog Connected Truth doit rester documenté séparément tant que sa cause n'est pas prouvée.

---

## 5. Findings restant après P1

- **P2/P5** : contrat formulaire frontend/backend ;
- **P2/P6** : CTA d'envoi sans transport réel ;
- **P2** : machine d'état trop permissive ;
- **P4** : cache TTL, merchandising `isFeatured`/`sortOrder`, pagination ;
- **P5** : accessibilité/densité, visuels produits, reload fiche produit ;
- **P8/P10** : séparation des données commerciales ;
- **P10** : administration édition complète.

---

## 6. Idées prioritaires

| Idée | Valeur | Effort | Phase |
|---|---:|---:|---|
| Split automatique fournisseur | 10 | 3 | P3 |
| Réassort selon consommation/min-max | 10 | 4 | P7 |
| Réception → stock | 10 | 4 | P7 |
| Lots + péremptions | 10 | 4 | P7 |
| Réassort 1 clic | 9 | 2 | P7 |
| Historique prix/MOQ/délai | 9 | 3 | P4/P6 |
| Facture/rapprochement | 9 | 4 | P8 |
| RFQ comparaison fournisseurs | 8 | 4 | P6 |
| Score SLA fournisseur | 8 | 3 | P7 |

---

## 7. Protocole P5 UI/UX

`BEFORE 390/430/768/1280 → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison → accessibilité/E2E → score visuel`.

---

## 8. Règles engineering

Backend source de vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Actions sensibles auditables. Aucun Vercel sans autorisation explicite. CI en cours ne bloque pas le travail indépendant. Aucun EP sans preuve.

---

## 9. Ordre critique / reprise

`P0 CLOSED → P1 ACTIVE → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11`

**PR active : #302**  
**Branche : `marketplace/p0-trust-integrity`**  
**Avancement crédité : 8/100 EP**  
**Next exact :** certifier le HEAD final P1 ; rouge → corriger ; vert → créditer P1, merger #302, vérifier master puis ouvrir P2.
