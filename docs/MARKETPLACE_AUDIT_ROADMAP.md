# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p0-trust-integrity`  
**Baseline auditée :** `master @ f19df12739fc262adb2238db1842813b4a820619`  
**Canonique initial mergé :** PR #301 → `master @ 3da5b6858d95d527766b4c4986fee4eca3c12d75`  
**Déploiement Vercel :** aucun sans autorisation explicite.

## Goal
Transformer le Marketplace Digital Crown en module d'approvisionnement fiable : découverte → panier → commande → fournisseur → réception → stock → réassort.

## Score baseline
UX **7.2/10** · UI statique **7.4/10** non certifiée runtime · Fonctionnalités **6.8/10** · Engineering **5.8/10** · Sécurité/fiabilité **5.2/10** · **Pondéré 6.5/10** · Potentiel produit **9.0/10**.

## Roadmap canonique P0 → P11 — 100 EP

La nomenclature P0→P11 est la seule nomenclature canonique. Les anciens lots A/B/C/... sont abandonnés.

| Phase | EP | Ce que fait le lot | Gate observable |
|---|---:|---|---|
| **P0 — Baseline & audit** | **8** | audit global, score, findings, roadmap, canonique | audit + canonique mergés et relus sur master |
| **P1 — Trust & sécurité** | **14** | autorité serveur, isolation cabinet, RBAC, anti-falsification, règles fournisseurs | tampering impossible + matrice RBAC + tests négatifs |
| **P2 — Order Engine** | **10** | panier → draft → envoi → confirmation → modification → annulation → fulfillment | machine d'état + audit trail + tests transitions |
| **P3 — Multi-fournisseurs** | **8** | routage/split commandes et contrats fournisseur | panier multi-fournisseurs → commandes cohérentes |
| **P4 — Catalogue & produits** | **8** | catalogue, recherche, disponibilité, merchandising, fraîcheur/cache | données cohérentes + TTL + filtres + pagination |
| **P5 — UX/UI Marketplace** | **16** | refonte task-first, panier/checkout, responsive, accessibilité | BEFORE → Goal → mockup → AFTER 390/430/768/1280 + E2E |
| **P6 — Procurement** | **10** | transmission fournisseur, suivi, ETA, réception | preuve transport + réception traçable |
| **P7 — Stock Intelligence** | **8** | réception→stock, seuils, consommation, lots/péremptions, reorder | mouvements stock + réassort testés |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revente, rapprochement, revenus, annulations | calculs serveur + événements auditables |
| **P9 — Automatisation fournisseur** | **4** | import/API, synchro prix/stock, retry, résilience | sync idempotente + retry + fraîcheur |
| **P10 — Superadmin Marketplace** | **3** | gouvernance fournisseurs/catalogues/accords/incidents | opérations sensibles + journal + supervision |
| **P11 — Certification finale** | **5** | E2E, sécurité, multi-cabinet, perf, a11y, docs, closeout | matrice finale verte + CI + runtime + docs |
| **Total** | **100** |  |  |

**Ordre :** `P0 ✅ → P1 EN COURS → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11`

**Avancement vérifié :** P0 = **8/8 EP ✅** ; P1 = **0/14 EP** jusqu'à preuve complète ; global = **8/100 EP = 8 %**.

## P1 — Trust & sécurité — ACTIF

### Goal
Faire du serveur l'autorité unique des commandes et réserver les contrôles commerciaux sensibles au rôle prévu.

### Sous-lots
- **P1.1** autorité financière serveur ;
- **P1.2** anti-tampering client ;
- **P1.3** isolation cabinet ;
- **P1.4** fournisseur/produit achetable ;
- **P1.5** RBAC commandes ;
- **P1.6** tests intégrité + RBAC.

### État courant — PR #302
Implémenté mais non crédité : reconstruction serveur fournisseur/noms/SKU/prix/totaux ; presets commerciaux serveur ; rejet multi-fournisseurs sur endpoint mono-fournisseur ; rejet fournisseur inactif ; produit discontinué ; produit hors cabinet ; ligne dupliquée ; GET `/partner-orders` Superadmin ; PATCH `/partner-orders/{id}` Superadmin ; POST conserve permission cabinet `patients` ; **9 tests ciblés**.

**Preuve requise :** exécution des 9 tests + CI verte + revue finale. Aucun EP P1 avant ces preuves.

## P2 — Order Engine
Machine d'état métier explicite autour de `DRAFT → SENT_TO_PARTNER → CONFIRMED → FULFILLED`, branches contrôlées `MODIFIED_AFTER_SEND` et `CANCELLED`. Gate : transitions autorisées, illégales rejetées, événements horodatés, idempotence, tests complets.

## P3 — Multi-fournisseurs
**Split automatique par fournisseur** recommandé. Gate : panier ≥2 fournisseurs → N commandes mono-fournisseur avec totaux/références/erreurs séparés.

## P4 — Catalogue & produits
Fournisseurs actifs uniquement ; disponibilité fiable ; `isFeatured`/`sortOrder` ; pagination ; recherche serveur si besoin ; TTL cache + fraîcheur ; politique cache périmé ; photos réelles lorsque disponibles.

## P5 — UX/UI Marketplace
Toute modification visuelle : **BEFORE → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel**. Viewports : 390, 430, 768, 1280 px. Cibles : densité, recherche/catalogue/panier, validation formulaire, faux CTA d'envoi, reload produit, accessibilité, séparation acheteur/commercial.

## P6 — Procurement
Transmission réelle email/API/EDI ; preuve d'envoi ; référence fournisseur ; ETA/backorder ; réception partielle/complète ; rapprochement commande-réception.

## P7 — Stock Intelligence
Réception→stock ; lots/péremptions ; seuils ; consommation ; réassort 1 clic ; suggestions ; prévention double saisie.

## P8 — Finance & monétisation
Commission/remise/revente/forfait ; revenu reconnu selon événement ; modification/annulation ; rapprochement commande-réception-facture ; reporting séparé acheteur.

## P9 — Automatisation fournisseur
Import/sync ; prix/disponibilité ; idempotence ; retry/backoff ; dernière synchro visible ; mode dégradé local-first sans masquer l'obsolescence.

## P10 — Superadmin Marketplace
CRUD complet ; activation ; accords ; supervision commandes ; incidents sync ; métriques ; confirmations sensibles ; audit log.

## P11 — Certification finale
Backend P1-P10 vert ; frontend build/tests ; E2E browse→panier→ordre→suivi→réception ; multi-tenant ; RBAC ; finance ; captures BEFORE/AFTER ; a11y ; performance ; docs alignées HEAD/PR/CI.

## Findings baseline à fermer
Critiques : autorité serveur, RBAC, multi-fournisseurs, isolation/activation fournisseur, machine d'état. Fonctionnels : formulaire, faux envoi, TTL, panier non scopé, merchandising, exposition données commerciales, admin édition, pagination, réception/stock. UX/UI : densité, micro-labels, contrôles icon-only, visuels produits, reload.

## Idées prioritaires
Split automatique multi-fournisseur ; réassort 1 clic ; suggestions min/max ; réception→stock ; lots/péremptions ; historique prix/MOQ/délai ; RFQ ; score fournisseur SLA ; alertes ETA/backorder ; rapprochement facture.

## Règles de crédit / closeout
Un lot n'est crédité qu'après preuve du gate. CI en cours n'arrête pas le travail indépendant. Aucun UI certifié sans BEFORE/AFTER. Aucun déploiement Vercel sans autorisation explicite. Après lot : validation → canonique → cohérence roadmap/% → merge → post-merge → lot suivant.

## Reprise
**Chantier : Marketplace Digital Crown**  
**Phase : P1 — Trust & sécurité**  
**PR : #302**  
**Branche : `marketplace/p0-trust-integrity`**  
**Avancement : 8/100 EP = 8 %**  
**Next exact :** inspecter tests/CI P1 → corriger si rouge → merge si vert → post-merge + crédit P1 → démarrer P2.
