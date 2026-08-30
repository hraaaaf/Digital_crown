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

Le Marketplace n'est pas une maquette. Les capacités suivantes existent :

- catalogue fournisseurs + produits ;
- recherche et filtres ;
- pages fournisseur et produit ;
- panier persistant local ;
- gestion des quantités ;
- formulaire de commande ;
- création de commande serveur ;
- stratégies commerciales / simulation de revenu ;
- interface superadmin de création catalogue ;
- interface superadmin de rapprochement de commandes ;
- backend de création/mise à jour fournisseurs et produits ;
- backend de création/liste/mise à jour commandes + événements/revenu.

---

## 4. Score baseline

Le score mesure l'état initial audité, pas le potentiel ni les corrections P1 non encore certifiées.

| Axe | Poids | Score | Confiance | Justification synthétique |
|---|---:|---:|---|---|
| UX | 20 % | **7.2/10** | moyenne | parcours riche et compréhensible, mais densité marketing, contrat formulaire et sémantique d'envoi perfectibles |
| UI / interaction | 15 % | **7.4/10** | moyenne-faible | composants structurés et responsive ; validation visuelle runtime non réalisée dans ce lot |
| Fonctionnalités | 25 % | **6.8/10** | élevée | catalogue/panier/commande/admin présents ; cycle fournisseur→réception→stock incomplet |
| Engineering | 25 % | **5.8/10** | élevée | architecture séparée correcte, mais autorité financière serveur, état commande et couverture tests insuffisants au baseline |
| Sécurité / fiabilité | 15 % | **5.2/10** | élevée | permissions commande trop larges et données commerciales modifiables via contrat client au baseline |
| **Score pondéré baseline** | **100 %** | **6.5/10** | — | `(7.2×.20)+(7.4×.15)+(6.8×.25)+(5.8×.25)+(5.2×.15)=6.48` |

### Potentiel produit

**9.0/10** — potentiel séparé du score de capacité actuel. Le Marketplace peut devenir un vrai moteur d'approvisionnement cabinet, surtout s'il est relié au stock, à la consommation, aux lots/péremptions et à la performance fournisseur.

### Limite importante

Le **7.4/10 UI n'est pas un score visuel certifié**. Il s'agit d'un score statique basé sur le code et la structure des interactions. La certification visuelle exige des captures runtime BEFORE puis AFTER aux mêmes viewports.

---

## 5. Findings baseline et affectation aux phases

| Finding | Phase | État actuel |
|---|---|---|
| Autorité financière serveur absente | P1 | implémenté sur branche, certification finale P1 requise |
| RBAC commandes trop large | P1 | implémenté sur branche, certification finale P1 requise |
| Panier multi-fournisseurs incohérent avec commande mono-fournisseur | P1/P3 | rejet serveur sûr en P1 ; vrai split multi-fournisseurs en P3 |
| Panier local non scopé | P1 | implémenté sur branche, certification finale P1 requise |
| Fournisseur inactif potentiellement visible | P1 | implémenté sur branche, certification finale P1 requise |
| Contrat formulaire frontend/backend divergent | P2/P5 | ouvert |
| CTA « envoyer au partenaire » sans transport réel observé | P2/P6 | ouvert |
| Machine d'état commande trop permissive | P2 | ouvert |
| Cache catalogue sans TTL | P4 | ouvert |
| `isFeatured` / `sortOrder` sous-exploités storefront | P4 | ouvert |
| Administration édition incomplète | P10 | ouvert |
| Pagination / montée en charge | P4/P10 | ouvert |
| Accessibilité / densité visuelle | P5 | ouvert |
| Visuels produits sous-exploités | P5 | ouvert |
| Rechargement brutal fiche produit | P5 | ouvert |
| Données commerciales exposées parcours achat | P8/P10 | ouvert |

---

## 6. Roadmap canonique P0 → P11 — 100 EP

**Règle :** P = phase/lot avec un résultat métier observable. Aucun EP n'est accordé au simple motif que du code existe ; il faut le gate de preuve défini.

| Phase | EP | Ce qu'elle fait | Gate principal |
|---|---:|---|---|
| **P0 — Baseline & audit** | **8** | audit complet, score initial, architecture, risques, roadmap canonique et critères de certification | audit + canonique mergés et relus sur `master` |
| **P1 — Trust & sécurité** | **14** | autorité serveur prix/totaux/stratégies, isolation cabinet/utilisateur, RBAC commercial, fournisseurs actifs, anti-falsification, règle sûre avant multi-fournisseurs | 15 tests ciblés + backend/frontend CI verts + diff revu |
| **P2 — Order Engine** | **12** | contrat client, création, transitions d'état, envoi logique, confirmation, modification, annulation, fulfillment et audit trail | machine d'état + tests transitions/contrat |
| **P3 — Multi-fournisseurs** | **8** | panier multi-fournisseurs réel, split/routage des commandes et règles par fournisseur | panier 2 fournisseurs → 2 commandes correctes E2E |
| **P4 — Catalogue & produits** | **8** | fiabilité catalogue, sync/cache/TTL, recherche, catégories, merchandising, disponibilité, pagination et données produit | fraîcheur + filtres + pagination + tests |
| **P5 — UX/UI Marketplace** | **14** | parcours task-first, navigation, recherche/filtres, panier, checkout, accessibilité, responsive et états | BEFORE → Goal → mockup → AFTER 390/430/768/1280 → E2E + score visuel |
| **P6 — Procurement** | **8** | commande fournisseur réelle, preuve d'envoi, suivi logistique, réception, backorder/retours | création → transport → réception prouvés |
| **P7 — Stock Intelligence** | **8** | réception vers stock, lots/péremptions, min/max, consommation et suggestions de réassort | réception alimente stock sans double saisie + tests |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revente, rapprochement, avoirs/annulations et reporting | calculs serveur + scénarios financiers testés |
| **P9 — Automatisation fournisseur** | **5** | imports/API fournisseur, sync prix/disponibilité, retries et résilience locale | panne/retry/idempotence + preuve sync |
| **P10 — Superadmin Marketplace** | **4** | CRUD complet fournisseurs/catalogues/accords, supervision, métriques et gouvernance | RBAC + audit trail + actions administratives testées |
| **P11 — Certification finale** | **5** | E2E réel, sécurité, multi-cabinet, performance, accessibilité, docs et closeout | tous gates finaux verts + canonique cohérent |
| **Total** | **100** |  |  |

### Avancement vérifié

- **P0 : 8/8 EP — CLOSED.** PR #301 mergée sur `master`.
- **P1 : 0/14 EP — EN COURS.** Les changements sont présents sur PR #302, mais le HEAD final n'est pas encore certifié.
- **Global : 8/100 EP = 8 %.**

---

## 7. P1 — Trust & sécurité — état de travail

### Goal
Rendre impossible la création d'une commande financièrement falsifiée depuis un client modifié et empêcher qu'un utilisateur non autorisé lise/modifie les données commerciales d'administration, tout en isolant le panier et les fournisseurs inactifs.

### Implémenté sur la branche

1. fournisseur résolu depuis le catalogue serveur ;
2. nom, SKU, prix et line totals reconstruits serveur ;
3. total commande recalculé serveur ;
4. stratégies limitées aux presets serveur ;
5. fournisseur inactif refusé à la commande ;
6. produit discontinué, cross-cabinet et lignes dupliquées refusés ;
7. mélange fournisseurs refusé tant que P3 n'assure pas le split ;
8. GET global commandes + PATCH commercial réservés Superadmin ;
9. POST de création conservé aux utilisateurs cabinet autorisés ;
10. storefront cabinet masque fournisseurs inactifs et leurs produits ;
11. Superadmin conserve l'accès aux fournisseurs inactifs pour administration ;
12. panier local isolé par `employer + user`, ancienne clé globale non migrée.

### Preuves déjà obtenues sur un HEAD intermédiaire

- CI #2235 : **SUCCESS** sur `f9855bbd7cdb6786ce96d42c0239d2ef46320338` ; backend suite, frontend tests/build et gates de durcissement verts.
- T2 Runtime Browser Certification #1350 : **SUCCESS** sur ce même HEAD intermédiaire.
- Patient P7 Final Certification #649 : **SUCCESS** sur ce même HEAD intermédiaire.
- Catalog Connected Truth #623 : **FAILURE** à l'étape `Targeted backend truth tests`, qui exécute uniquement des suites Patient/Prescription historiques et ne constitue donc pas une preuve P1 verte. La cause exacte reste non attribuée ; elle ne sera pas masquée.

### Gate P1 final

P1 ne peut passer à 14/14 que si le HEAD final avec les 15 tests et les deux dernières corrections obtient :

- tests backend Marketplace ciblés verts ;
- test frontend panier ciblé vert ;
- CI backend complète verte ;
- CI frontend tests/build verte ;
- revue diff sans régression évidente ;
- statut du workflow Catalog Connected Truth documenté sans attribuer abusivement son rouge à Marketplace.

---

## 8. Idées produit — score valeur / effort

Échelle valeur : 1–10. Effort : 1 faible → 5 élevé.

| Idée | Valeur | Effort | Phase cible | Pourquoi |
|---|---:|---:|---|---|
| Réassort en 1 clic depuis commande précédente | 9 | 2 | P7 | gain de temps cabinet immédiat |
| Suggestions de réassort selon consommation/min-max | 10 | 4 | P7 | transforme Marketplace en outil opérationnel |
| Split automatique panier par fournisseur | 10 | 3 | P3 | contrat métier propre + UX cohérente |
| RFQ / comparaison fournisseurs | 8 | 4 | P6 | arbitrage prix/délai/MOQ |
| Historique prix + MOQ + délai + livraison | 9 | 3 | P4/P6 | décision achat factuelle |
| Score fournisseur SLA | 8 | 3 | P7 | OTD, fill-rate, retours, qualité |
| Workflow budget / approbation | 7 | 4 | P8 | utile cabinets multi-utilisateurs |
| Réception → stock automatique | 10 | 4 | P7 | supprime double saisie |
| Lots + péremptions à la réception | 10 | 4 | P7 | forte valeur logistique/clinique |
| Substitutions en rupture | 8 | 3 | P4/P6 | continuité d'approvisionnement |
| Alertes backorder / ETA | 8 | 3 | P6 | réduit incertitude fournisseur |
| Tarification contractuelle par cabinet | 8 | 4 | P8 | prix B2B réalistes |
| Facture / rapprochement commande-réception | 9 | 4 | P8 | boucle finance propre |

---

## 9. Protocole UI/UX obligatoire pour P5

Pour chaque changement visuel :

1. **BEFORE** : captures exactes 390 / 430 / 768 / 1280 ;
2. **Goal écrit** : hiérarchie, densité, tâche primaire, critères observables ;
3. **mockup/référence** avant implémentation ;
4. implémentation ;
5. **AFTER** aux mêmes viewports ;
6. comparaison BEFORE/AFTER ;
7. tests clavier/accessibilité/E2E ;
8. score visuel argumenté.

Aucun score visuel final n'est certifiable sans ces preuves.

---

## 10. Règles engineering du chantier

- backend source de vérité pour données financières et statuts ;
- frontend jamais autorité sécurité ;
- scoping cabinet obligatoire ;
- pas de confiance dans prix/total/identité fournisseur envoyés par le client ;
- transitions métier explicites ;
- opérations sensibles auditables ;
- comportement local-first conservé lorsque compatible avec la vérité métier ;
- pas de déploiement Vercel sans autorisation explicite ;
- CI en cours ne bloque jamais le travail indépendant ;
- aucun EP sans preuve.

---

## 11. Ordre critique

`P0 CLOSED → P1 ACTIVE → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11`

Le chantier ne saute pas vers l'automatisation ou les recommandations avant fermeture des contrats de confiance et de commande.

---

## 12. Reprise

**Lot actif : P1 — Trust & sécurité**  
**PR active : #302**  
**Branche : `marketplace/p0-trust-integrity`**  
**Avancement crédité : 8/100 EP**  
**Next exact :** certifier le HEAD final P1 ; si rouge, diagnostiquer/corriger ; si vert, créditer P1, merger #302, vérifier `master`, puis ouvrir P2 Order Engine.
