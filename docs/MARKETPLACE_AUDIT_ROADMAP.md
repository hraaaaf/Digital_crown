# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p0-trust-integrity`  
**Référence code auditée initiale :** `master @ f19df12739fc262adb2238db1842813b4a820619`  
**Déploiement Vercel :** aucun, non requis pour ce chantier backend tant qu'aucun déploiement n'est explicitement autorisé.

---

## 1. Goal / Succès / Preuve

### Goal
Transformer le Marketplace Digital Crown en module d'approvisionnement fiable, rapide et cohérent : découverte produit → panier → commande → fournisseur → réception → stock → réassort, avec une UX claire et un contrat engineering sûr.

### Succès
Le chantier est terminé uniquement lorsque :

1. l'autorité serveur contrôle prix, totaux et termes commerciaux ;
2. le RBAC Marketplace est explicite et testé ;
3. les paniers multi-fournisseurs ont une règle métier déterministe ;
4. le cycle de commande est réel et traçable jusqu'à la réception ;
5. l'UI est validée BEFORE/AFTER aux mêmes viewports ;
6. les parcours critiques ont des tests backend/frontend/E2E ;
7. la réception peut alimenter le stock sans ressaisie incohérente ;
8. tous les gates finaux de cette roadmap sont verts.

### Preuve attendue
Code + tests automatisés + comportement runtime observé + captures BEFORE/AFTER + audit de cohérence + CI verte. Aucun score visuel « certifié » sans captures runtime.

---

## 2. Scope vérifié

### Frontend inspecté
- `frontend/src/pages/PartnerMarketplacePage.tsx`
- `frontend/src/pages/PartnerProductPage.tsx`
- `frontend/src/pages/PartnerSupplierPage.tsx`
- `frontend/src/pages/PartnerCatalogAdminPage.tsx`
- `frontend/src/features/partnerMarketplace/data.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/Sidebar.tsx`

### Backend inspecté
- `backend/routers/partner_catalog.py`
- `backend/routers/partner_orders.py`
- `backend/models.py`
- `backend/models_operations.py`
- `backend/routers/auth.py`

### Tests Marketplace ajoutés dans P1
- `backend/tests/test_partner_orders_integrity.py` — 9 tests intégrité/RBAC
- `backend/tests/test_partner_catalog_visibility.py` — 2 tests visibilité fournisseur
- `frontend/src/features/partnerMarketplace/data.test.ts` — 4 tests isolation panier

**Total ciblé P1 : 15 tests.** Aucun EP P1 n'est crédité tant que le HEAD final de P1 n'a pas les gates automatisés requis verts.

---

## 3. Baseline fonctionnelle vérifiée

Le Marketplace n'est pas une maquette. Capacités existantes : catalogue fournisseurs/produits, recherche/filtres, pages fournisseur/produit, panier persistant local, quantités, formulaire de commande, création serveur, stratégies commerciales, interface superadmin catalogue et rapprochement, CRUD catalogue et événements/revenu commandes.

---

## 4. Score baseline

| Axe | Poids | Score | Confiance | Justification synthétique |
|---|---:|---:|---|---|
| UX | 20 % | **7.2/10** | moyenne | parcours riche mais densité et contrat formulaire perfectibles |
| UI / interaction | 15 % | **7.4/10** | moyenne-faible | structure responsive ; pas encore de certification visuelle runtime |
| Fonctionnalités | 25 % | **6.8/10** | élevée | catalogue/panier/commande/admin présents ; cycle réception-stock incomplet |
| Engineering | 25 % | **5.8/10** | élevée | baseline sans autorité serveur suffisante ni tests Marketplace dédiés |
| Sécurité / fiabilité | 15 % | **5.2/10** | élevée | baseline avec données commerciales trop pilotables par client |
| **Score pondéré baseline** | **100 %** | **6.5/10** | — | résultat calculé 6.48, arrondi 6.5 |

**Potentiel produit : 9.0/10**, séparé du score courant.  
**UI 7.4 non certifié visuellement** tant que P5 n'a pas exécuté le protocole BEFORE/AFTER.

---

## 5. Findings baseline et affectation

| Finding | Phase | État |
|---|---|---|
| Autorité financière serveur absente | P1 | implémenté, certification finale P1 requise |
| RBAC commandes trop large | P1 | implémenté, certification finale P1 requise |
| Panier multi-fournisseurs incohérent | P1/P3 | rejet sûr P1 ; vrai split P3 |
| Panier local non scopé | P1 | implémenté, certification finale P1 requise |
| Fournisseur inactif visible | P1 | implémenté, certification finale P1 requise |
| Contrat formulaire divergent | P2/P5 | ouvert |
| CTA « envoyer » sans transport réel | P2/P6 | ouvert |
| Machine d'état permissive | P2 | ouvert |
| Cache sans TTL | P4 | ouvert |
| Merchandising `isFeatured`/`sortOrder` | P4 | ouvert |
| Administration édition incomplète | P10 | ouvert |
| Pagination | P4/P10 | ouvert |
| Accessibilité/densité | P5 | ouvert |
| Visuels produit | P5 | ouvert |
| Reload fiche produit | P5 | ouvert |
| Données commerciales dans parcours achat | P8/P10 | ouvert |

---

## 6. Roadmap canonique P0 → P11 — 100 EP

| Phase | EP | Ce qu'elle fait | Gate principal |
|---|---:|---|---|
| **P0 — Baseline & audit** | **8** | audit, score, architecture, risques, roadmap | canonique mergé et relu sur master |
| **P1 — Trust & sécurité** | **14** | autorité serveur, isolation, RBAC, fournisseurs actifs, anti-falsification | 15 tests ciblés + CI backend/frontend verts + diff revu |
| **P2 — Order Engine** | **12** | contrat client, transitions, envoi logique, confirmation, modification, annulation, fulfillment | machine d'état + tests transitions/contrat |
| **P3 — Multi-fournisseurs** | **8** | panier multi-fournisseurs, split/routage | 2 fournisseurs → 2 commandes correctes E2E |
| **P4 — Catalogue & produits** | **8** | sync/cache/TTL, recherche, merchandising, disponibilité, pagination | fraîcheur + filtres + pagination + tests |
| **P5 — UX/UI Marketplace** | **14** | navigation, panier, checkout, accessibilité, responsive | BEFORE/AFTER 390/430/768/1280 + E2E + score |
| **P6 — Procurement** | **8** | envoi fournisseur réel, suivi logistique, réception, retours/backorders | création → transport → réception prouvés |
| **P7 — Stock Intelligence** | **8** | réception-stock, lots/péremptions, min/max, réassort | stock alimenté sans double saisie + tests |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revente, rapprochement, annulations/reporting | scénarios financiers serveur testés |
| **P9 — Automatisation fournisseur** | **5** | imports/API, sync prix/dispo, retries | panne/retry/idempotence + preuve sync |
| **P10 — Superadmin Marketplace** | **4** | CRUD complet, supervision, métriques, gouvernance | RBAC + audit trail + actions testées |
| **P11 — Certification finale** | **5** | E2E réel, sécurité, multi-cabinet, performance, accessibilité, closeout | tous gates verts + canonique cohérent |
| **Total** | **100** |  |  |

### Avancement vérifié
- **P0 : 8/8 EP — CLOSED** via PR #301.
- **P1 : 0/14 EP — EN COURS** sur PR #302.
- **Global : 8/100 EP = 8 %.**

---

## 7. P1 — Trust & sécurité

### Goal
Rendre impossible la création d'une commande financièrement falsifiée depuis un client modifié et empêcher qu'un utilisateur non autorisé lise/modifie les données commerciales d'administration, tout en isolant panier et fournisseurs inactifs.

### Implémenté sur la branche
1. fournisseur résolu serveur ;
2. nom/SKU/prix/line total reconstruits serveur ;
3. total recalculé serveur ;
4. stratégies limitées aux presets serveur ;
5. fournisseur inactif refusé à la commande ;
6. produit discontinué, cross-cabinet et lignes dupliquées refusés ;
7. mélange fournisseurs refusé jusqu'au split P3 ;
8. GET commandes et PATCH commercial réservés Superadmin ;
9. POST commande conservé aux utilisateurs cabinet autorisés ;
10. storefront cabinet masque fournisseurs inactifs et leurs produits ;
11. Superadmin garde l'accès aux fournisseurs inactifs pour administration ;
12. panier isolé par `employer + user` ; ancienne clé globale ignorée, sans migration dangereuse.

### Preuves obtenues avant le HEAD final
- CI #2235 **SUCCESS** sur `f9855bbd7cdb6786ce96d42c0239d2ef46320338`, avec backend suite, frontend tests/build et durcissement verts.
- T2 Runtime #1350 **SUCCESS**.
- Patient P7 #649 **SUCCESS**.
- Catalog Connected Truth #623 **FAILURE** à `Targeted backend truth tests`, commande : `test_catalog_connected_truth.py`, `test_patient_p3_master_plan_revisions.py`, `TestCatalogQuickAdd`. Aucun de ces fichiers n'est modifié par PR #302. La cause exacte n'est pas inventée ni masquée.

### Gate P1 final
Le HEAD final doit prouver :
- 11 tests backend Marketplace ciblés verts ;
- 4 tests frontend panier verts ;
- CI backend complète verte ;
- CI frontend tests/build verte ;
- diff final revu ;
- état du workflow Catalog Connected Truth explicitement documenté.

---

## 8. Idées produit — valeur / effort

| Idée | Valeur | Effort | Phase |
|---|---:|---:|---|
| Réassort 1 clic | 9 | 2 | P7 |
| Suggestions min/max consommation | 10 | 4 | P7 |
| Split automatique par fournisseur | 10 | 3 | P3 |
| RFQ / comparaison fournisseurs | 8 | 4 | P6 |
| Historique prix/MOQ/délai | 9 | 3 | P4/P6 |
| Score fournisseur SLA | 8 | 3 | P7 |
| Budget / approbation | 7 | 4 | P8 |
| Réception → stock | 10 | 4 | P7 |
| Lots + péremptions | 10 | 4 | P7 |
| Substitutions rupture | 8 | 3 | P4/P6 |
| Backorder / ETA | 8 | 3 | P6 |
| Tarification contractuelle | 8 | 4 | P8 |
| Facture / rapprochement | 9 | 4 | P8 |

---

## 9. Protocole UI/UX P5 obligatoire

`BEFORE 390/430/768/1280 → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison → tests accessibilité/E2E → score visuel`.

---

## 10. Règles engineering

Backend = source de vérité financière/statuts. Frontend jamais autorité sécurité. Scoping cabinet obligatoire. Transitions explicites. Actions sensibles auditables. Aucun Vercel sans autorisation explicite. CI en cours n'arrête pas le travail indépendant. Aucun EP sans preuve.

---

## 11. Ordre critique

`P0 CLOSED → P1 ACTIVE → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11`

---

## 12. Reprise

**Lot actif : P1 — Trust & sécurité**  
**PR : #302**  
**Branche : `marketplace/p0-trust-integrity`**  
**Avancement crédité : 8/100 EP**  
**Next exact :** certifier le HEAD final P1 ; si rouge corriger ; si vert créditer P1 puis merger #302, vérifier master et ouvrir P2.
