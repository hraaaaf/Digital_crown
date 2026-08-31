# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Lot actif :** P9 — Automatisation fournisseur  
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

| Phase | EP | État | Gate |
|---|---:|---|---|
| P0 — Baseline & audit | 8 | CLOSED | audit/canonique mergé |
| P1 — Trust & sécurité | 14 | CLOSED | autorité serveur + RBAC + tests |
| P2 — Order Engine | 12 | CLOSED | machine d'état/revenus/audit |
| P3 — Multi-fournisseurs | 8 | CLOSED | 2 fournisseurs → 2 commandes atomiques |
| P4 — Catalogue & produits | 8 | CLOSED | cache/recherche/pagination |
| P5 — UX/UI Marketplace | 14 | CLOSED | BEFORE/AFTER + E2E + score visuel |
| P6 — Procurement | 8 | CLOSED | transport → suivi → réception |
| P7 — Stock Intelligence | 8 | CLOSED | réception → stock sans double saisie |
| **P8 — Finance & monétisation** | **6** | **CLOSED** | scénarios financiers serveur + merge vérifié |
| **P9 — Automatisation fournisseur** | **5** | **ACTIF** | idempotence/retry/sync |
| P10 — Superadmin Marketplace | 4 | PRÉPARATION | RBAC + audit trail global |
| P11 — Certification finale | 5 | À FAIRE | tous gates verts |
| **Total** | **100** |  |  |

## Avancement vérifié
- P0 : 8/8 CLOSED — PR #301.
- P1 : 14/14 CLOSED — PR #302.
- P2 : 12/12 CLOSED — PR #306.
- P3 : 8/8 CLOSED — PR #309.
- P4 : 8/8 CLOSED — PR #311.
- P5 : 14/14 CLOSED — PR #319 ; merge `5dec8add36c6ae839155f36697672f5e5fb1228b`.
- P6 : 8/8 CLOSED — PR #316 ; merge `1cee3f30168845602a2f8fdfb2a5bbf1694e9c71`.
- P7 : 8/8 CLOSED — PR #318 ; merge `7b7aeb4569d31e1fb26460d032523344a7f21d21`.
- P8 : 6/6 CLOSED — PR #320 ; merge `538ce138987cbe6b147770c210bf3df2f19782db`.
- **Global CLOSED : 86/100 = 86 %.**

## P5 — UX/UI Marketplace — CLOSED
Marketplace P5 BEFORE #5 : SUCCESS sur 390×844 / 430×932 / 768×1024 / 1280×800. Défauts : H1 rogné à 390 px, hero trop dominant, catalogue trop bas.  
Référence figée avant code : `docs/marketplace/P5_UI_REFERENCE.md` + SVG.  
HEAD `65ff91d4d4e841a5886051ddacdabc935c49cc43` : AFTER #6, CI #2363, Catalog #742, T2 #1469, Patient #768 SUCCESS.  
E2E ajout panier → formulaire → POST → DRAFT sans reload. Inspection visuelle réelle : **9.2/10**. PR #319 mergée.

## P6 — Procurement — CLOSED
Transport fournisseur prouvé/idempotent + garde SSRF ; référence/ETA/backorders ; réception partielle/complète idempotente ; réconciliation ; audit trail.  
HEAD closeout `3ab5863d79adc0f11e09052fe6c59789ecd1edbf` : CI #2342, Catalog #724, T2 #1451, Patient #750, Portability #336, Onboarding #143 SUCCESS. PR #316 mergée.

## P7 — Stock Intelligence — CLOSED
`StockItem` canonique ; mapping produit→stock ; facteur/min/cible ; ledger idempotent ; réception→stock ; PENDING_MAPPING sans stock partiel ; replay sans double incrément ; lots/péremptions ; lots expirés exclus ; FEFO ; réassort ; tenant scoping.  
HEAD `77da0418d10548d279ce0dbdbf2d460b2362e492` : CI #2359, Catalog #739, T2 #1466, Patient #765, Portability #348, Onboarding #155 SUCCESS. PR #318 mergée.

## P8 — Finance & monétisation — CLOSED

### Goal
Conserver P2 comme seule autorité de reconnaissance de revenu et ajouter un rapprochement serveur commande ↔ réception ↔ facture fournisseur, avec reporting interne tenant-scoped.

### Implémenté
- `PartnerOrder.recognized_*` reste la vérité P2 ; aucun second moteur de revenu ;
- facture fournisseur idempotente par commande ;
- coût fournisseur attendu déterministe selon commission / remise-revente / frais fixes ;
- statuts de rapprochement `WAITING_INVOICE`, `WAITING_RECEIPT`, `AMOUNT_MISMATCH`, `MATCHED`, `CANCELLED` ;
- audit `SUPPLIER_INVOICE_RECORDED` ;
- reporting financier agrégé cabinet ;
- rapprochement MAD uniquement ;
- Superadmin-only + employer scoping.

### Preuve produit
HEAD mergé `538ce138987cbe6b147770c210bf3df2f19782db` :
- CI #2368 SUCCESS ;
- Catalog #745 SUCCESS ;
- T2 #1472 SUCCESS ;
- Patient #771 SUCCESS ;
- Portability #353 SUCCESS ;
- Onboarding #160 SUCCESS ;
- M6-I skipped par périmètre.

Tests ciblés P8 : 9 scénarios couvrant modèles financiers, matching facture/réception, réception partielle, mismatch, annulation, idempotence/conflits, devise, reporting/isolation et RBAC HTTP.

### Gate
**CLOSED — 6/6 EP crédités après certification du HEAD, merge #320 et vérification `merged=true` sur master.**

## P9 — Automatisation fournisseur — ACTIF
Goal : automatiser la synchronisation fournisseur sans corruption locale ni duplication : snapshot canonique, upsert prix/disponibilité, idempotence, retry/backoff, degraded mode, audit et isolation tenant.

Préparation existante à reconstruire/vérifier sur master post-P8 : moteur API `/catalog`, préservation merchandising local, hash idempotent, fraîcheur, retry forcé Superadmin, garde SSRF P6, protection contre identités locales SKU/externalProductId ambiguës. **0/5 EP avant implémentation vérifiée + CI + merge.**

## P10 — Superadmin Marketplace — PRÉPARATION
Supervision globale cross-cabinet, accords fournisseur, incidents sync, métriques, mutation avec confirmation explicite et audit append-only préparés. Aucune EP créditée avant reconstruction post-P9 et CI.

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas le travail indépendant. Aucun EP CLOSED sans closeout complet.

## Reprise
`P0 CLOSED → P1 CLOSED → P2 CLOSED → P3 CLOSED → P4 CLOSED → P5 CLOSED → P6 CLOSED → P7 CLOSED → P8 CLOSED → P9 ACTIF → P10 PREP → P11`

**Crédit CLOSED : 86/100 EP.**  
**Next exact :** créer/reconstruire P9 depuis master post-P8, auditer les préparations existantes, combler les gaps, tester puis certifier avant merge.
