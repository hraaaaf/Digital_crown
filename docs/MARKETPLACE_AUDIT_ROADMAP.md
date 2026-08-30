# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p0-trust-integrity`  
**Baseline auditée :** `master @ f19df12739fc262adb2238db1842813b4a820619`  
**Canonique initial mergé :** PR #301 → `master @ 3da5b6858d95d527766b4c4986fee4eca3c12d75`  
**Déploiement Vercel :** interdit sans autorisation explicite ; aucun requis ici.

## 1. Goal / Succès / Preuve

### Goal
Transformer le Marketplace Digital Crown en module d'approvisionnement fiable, rapide et cohérent : découverte produit → panier → commande → fournisseur → réception → stock → réassort, avec une UX claire et un contrat engineering sûr.

### Succès final
Le chantier est terminé uniquement lorsque : serveur autoritaire sur les montants ; RBAC explicite ; multi-fournisseurs déterministe ; cycle traçable jusqu'à réception ; UI certifiée BEFORE/AFTER ; tests critiques backend/frontend/E2E ; réception reliée au stock ; intégrations fournisseur prouvées ; gouvernance Superadmin ; gates P0→P11 verts.

### Preuve attendue
Code + tests automatisés + comportement runtime observé + captures BEFORE/AFTER + audit de cohérence + CI verte. Aucun score visuel certifié sans captures runtime.

## 2. Baseline fonctionnelle vérifiée

Existant : catalogue fournisseurs/produits, recherche/filtres, pages fournisseur/produit, panier persistant, quantités, formulaire de commande, création serveur, stratégies commerciales, administration catalogue, rapprochement commandes, backend fournisseurs/produits/commandes/événements.

| Axe | Poids | Score baseline |
|---|---:|---:|
| UX | 20 % | **7.2/10** |
| UI / interaction | 15 % | **7.4/10** non certifié runtime |
| Fonctionnalités | 25 % | **6.8/10** |
| Engineering | 25 % | **5.8/10** |
| Sécurité / fiabilité | 15 % | **5.2/10** |
| **Score pondéré** | **100 %** | **6.5/10** |

**Potentiel produit séparé : 9.0/10.**

## 3. Roadmap canonique P0 → P11 — 100 EP

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

**Ordre critique :** `P0 ✅ → P1 EN COURS → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11`

**Avancement vérifié :** P0 = **8/8 EP ✅** ; P1 = **0/14 EP** jusqu'à preuve complète ; global = **8/100 EP = 8 %**.

## 4. P1 — Trust & sécurité — ACTIF

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

**Preuve encore requise :** exécution des 9 tests + CI verte + revue finale du comportement. Aucun EP P1 avant ces preuves.

## 5. P2 — Order Engine

Goal : machine d'état métier explicite et non permissive. Contrat actuel à durcir autour de `DRAFT → SENT_TO_PARTNER → CONFIRMED → FULFILLED`, avec branches contrôlées `MODIFIED_AFTER_SEND` et `CANCELLED`. Décider en P2/P6/P8 où vivent `SHIPPED`, `RECEIVED`, `INVOICED`, `REJECTED`.

Gate : transitions autorisées explicites ; illégales rejetées ; événements horodatés ; idempotence ; tests du graphe complet.

## 6. P3 — Multi-fournisseurs

Recommandation canonique : **split automatique par fournisseur** au moment de préparer la commande, avec résumé avant validation. Gate : panier ≥2 fournisseurs → N commandes mono-fournisseur, totaux/références/erreurs séparés.

## 7. P4 — Catalogue & produits

Fournisseurs actifs seulement ; disponibilité fiable ; `isFeatured`/`sortOrder` respectés ; pagination ; recherche serveur si volume ; TTL cache + fraîcheur ; politique cache périmé ; photos réelles quand disponibles.

## 8. P5 — UX/UI Marketplace

Toute modification visuelle : **BEFORE → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel**. Viewports : 390, 430, 768, 1280 px.

Cibles : réduire densité marketing ; priorité recherche/catalogue/panier ; aligner validation frontend/backend ; corriger faux CTA d'envoi ; supprimer reload complet après ajout ; accessibilité boutons quantité ; séparer données acheteur/commerciales.

## 9. P6 — Procurement

Création réelle demande/commande ; transport email/API/EDI ; preuve d'envoi ; référence fournisseur ; ETA/backorder ; réception partielle/complète ; rapprochement commande-réception.

## 10. P7 — Stock Intelligence

Réception→stock ; lots/péremptions ; seuils min/max ; consommation ; réassort 1 clic ; suggestions ; prévention double saisie.

## 11. P8 — Finance & monétisation

Commission/remise/revente/forfait ; revenu reconnu selon événement ; modification/annulation ; rapprochement commande-réception-facture ; reporting séparé de l'UX acheteur.

## 12. P9 — Automatisation fournisseur

Import/sync ; prix/disponibilité ; idempotence ; retry/backoff ; dernière synchro visible ; mode dégradé local-first sans masquer obsolescence.

## 13. P10 — Superadmin Marketplace

CRUD complet ; activation ; accords commerciaux ; supervision commandes ; incidents sync ; métriques ; confirmations sensibles ; audit log.

## 14. P11 — Certification finale

Backend P1-P10 vert ; frontend build/tests ; E2E browse→panier→ordre→suivi→réception ; aucune fuite inter-cabinet ; matrice RBAC ; finance cohérente ; captures BEFORE/AFTER ; a11y ; performance ; docs alignées HEAD/PR/CI.

## 15. Findings à fermer

Critiques : autorité serveur, RBAC commandes, multi-fournisseurs, isolation/activation fournisseur, machine d'état. Fonctionnels : validation formulaire, faux envoi, TTL, panier non scopé, merchandising, exposition données commerciales, admin édition, pagination, réception/stock. UX/UI : densité, micro-labels, contrôles icon-only, visuels produits, reload.

## 16. Idées produit prioritaires

| Idée | Valeur | Effort | Phase |
|---|---:|---:|---|
| Split automatique multi-fournisseur | 10 | 3 | P3 |
| Réassort 1 clic | 9 | 2 | P7 |
| Suggestions consommation/min-max | 10 | 4 | P7 |
| Réception → stock automatique | 10 | 4 | P7 |
| Lots + péremptions | 10 | 4 | P7 |
| Historique prix/MOQ/délai | 9 | 3 | P4/P6 |
| RFQ / comparaison fournisseurs | 8 | 4 | P6 |
| Score fournisseur SLA | 8 | 3 | P6/P10 |
| Alertes backorder / ETA | 8 | 3 | P6 |
| Facture / rapprochement | 9 | 4 | P8 |

## 17. Règles de crédit / closeout

Un lot n'est crédité qu'après preuve de son gate. CI en cours n'arrête pas les travaux indépendants. Aucun changement UI certifié sans BEFORE/AFTER. Aucun déploiement Vercel sans autorisation explicite. Après lot : validation → canonique → cohérence roadmap/% → merge → post-merge → lot suivant.

## 18. Reprise

**Chantier : Marketplace Digital Crown**  
**Phase : P1 — Trust & sécurité**  
**PR : #302**  
**Branche : `marketplace/p0-trust-integrity`**  
**Avancement vérifié : 8/100 EP = 8 %**  
**Next exact :** inspecter tests/CI P1 → corriger si rouge → merge si vert → post-merge + crédit P1 → démarrer P2.
