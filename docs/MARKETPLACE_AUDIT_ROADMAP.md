# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p0-trust-integrity`  
**Canonique initial :** PR #301 mergée sur `master`  
**Déploiement Vercel :** aucun sans autorisation explicite.

## Goal
Marketplace d'approvisionnement fiable : découverte → panier → commande → fournisseur → réception → stock → réassort.

## Score baseline
UX **7.2/10** · UI statique **7.4/10** non certifiée runtime · Fonctionnalités **6.8/10** · Engineering **5.8/10** · Sécurité/fiabilité **5.2/10** · **Pondéré 6.5/10** · Potentiel **9.0/10**.

## Roadmap canonique P0 → P11 — 100 EP

Les anciens lots A/B/C/... sont remplacés par P0→P11.

| Phase | EP | Mission | Gate |
|---|---:|---|---|
| **P0 — Baseline & audit** | **8** | audit, scores, findings, roadmap, canonique | canonique mergé et vérifié |
| **P1 — Trust & sécurité** | **14** | serveur autoritaire, isolation cabinet, RBAC, anti-tampering | tests intégrité + RBAC verts |
| **P2 — Order Engine** | **10** | cycle commande et machine d'état | transitions + audit trail testés |
| **P3 — Multi-fournisseurs** | **8** | split/routage des commandes | panier multi → commandes mono cohérentes |
| **P4 — Catalogue & produits** | **8** | catalogue, recherche, disponibilité, fraîcheur | cohérence + TTL + filtres + pagination |
| **P5 — UX/UI Marketplace** | **16** | expérience task-first, responsive, a11y | BEFORE/AFTER 390/430/768/1280 + E2E |
| **P6 — Procurement** | **10** | transmission fournisseur, suivi, réception | preuve d'envoi + réception traçable |
| **P7 — Stock Intelligence** | **8** | réception→stock, lots, seuils, reorder | mouvements stock + réassort testés |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revenus/rapprochement | calculs serveur + événements auditables |
| **P9 — Automatisation fournisseur** | **4** | API/import, sync prix/stock, retry | sync idempotente + fraîcheur prouvée |
| **P10 — Superadmin Marketplace** | **3** | gouvernance fournisseurs/catalogues/accords/incidents | opérations sensibles + audit log |
| **P11 — Certification finale** | **5** | E2E, sécurité, perf, a11y, docs, closeout | matrice finale verte |
| **Total** | **100** |  |  |

**Séquence :** `P0 ✅ → P1 EN COURS → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11`

**Avancement vérifié : P0 8/8 EP ✅ · P1 0/14 EP · global 8/100 EP = 8 %.**

## P1 — Trust & sécurité — ACTIF

### Sous-lots
- **P1.1** autorité financière serveur
- **P1.2** anti-tampering client
- **P1.3** isolation cabinet
- **P1.4** fournisseur/produit achetable
- **P1.5** RBAC commandes
- **P1.6** tests intégrité + RBAC

### PR #302 — état implémenté, non encore crédité
- fournisseur, noms, SKU, prix et totaux reconstruits serveur ;
- stratégies limitées aux presets serveur ;
- rejet multi-fournisseurs sur endpoint mono-fournisseur ;
- rejet fournisseur inactif, produit discontinué, produit hors cabinet, ligne dupliquée ;
- GET `/partner-orders` réservé Superadmin ;
- PATCH `/partner-orders/{id}` réservé Superadmin ;
- POST de création conserve la permission cabinet `patients` ;
- **9 tests ciblés** intégrité/RBAC.

**Preuve requise avant 14 EP : tests ciblés + CI verte + revue finale.**

## P2 — Order Engine
`DRAFT → SENT_TO_PARTNER → CONFIRMED → FULFILLED`, avec `MODIFIED_AFTER_SEND` / `CANCELLED` contrôlés. Gate : transitions légales explicites, illégales rejetées, événements, idempotence, tests complets.

## P3 — Multi-fournisseurs
Recommandation : **split automatique par fournisseur**. Gate : panier ≥2 fournisseurs → N commandes mono-fournisseur, totaux/références/erreurs séparés.

## P4 — Catalogue & produits
Fournisseurs actifs ; disponibilité ; `isFeatured`/`sortOrder` ; pagination ; recherche ; TTL cache/fraîcheur ; politique cache périmé ; visuels réels.

## P5 — UX/UI Marketplace
Obligatoire : **BEFORE → Goal → mockup/référence → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel**. Viewports 390/430/768/1280.

## P6 — Procurement
Transport réel email/API/EDI ; preuve d'envoi ; référence fournisseur ; ETA/backorder ; réception ; rapprochement commande-réception.

## P7 — Stock Intelligence
Réception→stock ; lots/péremptions ; seuils ; consommation ; réassort 1 clic ; suggestions ; zéro double saisie.

## P8 — Finance & monétisation
Commission/remise/revente/forfait ; revenu reconnu ; annulation ; rapprochement commande-réception-facture ; reporting interne.

## P9 — Automatisation fournisseur
Import/sync ; prix/disponibilité ; idempotence ; retry/backoff ; fraîcheur visible ; mode dégradé explicite.

## P10 — Superadmin Marketplace
CRUD fournisseurs/produits ; activation ; accords ; commandes ; incidents sync ; métriques ; actions sensibles ; audit log.

## P11 — Certification finale
Backend/frontend/E2E ; multi-tenant ; RBAC ; finance ; UI BEFORE/AFTER ; a11y ; performance ; docs/HEAD/PR/CI cohérents.

## Findings baseline restant à fermer
Machine d'état permissive ; panier multi-fournisseurs ; formulaire divergent ; faux CTA d'envoi ; cache sans TTL ; panier local non scopé ; merchandising ; données commerciales dans parcours achat ; admin édition ; pagination ; réception/stock ; densité UI ; accessibilité ; visuels ; reload produit.

## Idées prioritaires
Split multi-fournisseur ; réassort 1 clic ; suggestions min/max ; réception→stock ; lots/péremptions ; historique prix/MOQ/délai ; RFQ ; score SLA fournisseur ; alertes ETA ; rapprochement facture.

## Règles
Crédit uniquement après preuve du gate. CI en cours n'arrête pas le travail indépendant. Aucun UI certifié sans BEFORE/AFTER. Aucun déploiement Vercel sans autorisation explicite. Closeout : validation → canonique → roadmap/% → merge → post-merge → phase suivante.

## Reprise
**Chantier : Marketplace Digital Crown**  
**Phase : P1 — Trust & sécurité**  
**PR : #302**  
**Branche : `marketplace/p0-trust-integrity`**  
**Avancement : 8/100 EP = 8 %**  
**Next exact :** inspecter tests/CI P1 → corriger si rouge → merge si vert → post-merge + crédit P1 → P2.
