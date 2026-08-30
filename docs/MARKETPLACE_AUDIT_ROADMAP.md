# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Lot actif :** P8 — Finance & monétisation  
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
| **P8 — Finance & monétisation** | **6** | **EN COURS** | scénarios financiers serveur |
| P9 — Automatisation fournisseur | 5 | À FAIRE | idempotence/retry/sync |
| P10 — Superadmin Marketplace | 4 | À FAIRE | RBAC + audit trail global |
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
- **Global CLOSED : 80/100 = 80 %.**

## P5 — UX/UI Marketplace — CLOSED

### BEFORE
Marketplace P5 BEFORE #5 : SUCCESS sur 390×844 / 430×932 / 768×1024 / 1280×800.  
Défauts : H1 rogné à 390 px, hero trop dominant, catalogue trop bas.

### Goal / référence
Procurement-first ; recherche/catalogue/panier prioritaires ; CTA DRAFT exact ; aucune donnée commerciale interne ; contrôles quantité accessibles ; aucun reload.  
Référence figée avant code : `docs/marketplace/P5_UI_REFERENCE.md` + SVG.

### AFTER / preuve
HEAD `65ff91d4d4e841a5886051ddacdabc935c49cc43` : AFTER #6 SUCCESS, CI #2363 SUCCESS, Catalog #742 SUCCESS, T2 #1469 SUCCESS, Patient #768 SUCCESS.  
E2E : ajout panier → formulaire → POST → succès DRAFT sans reload.  
Inspection visuelle réelle des 4 captures : objectif atteint ; **score visuel 9.2/10**.  
PR #319 squash-mergée ; master vérifié à `5dec8add36c6ae839155f36697672f5e5fb1228b`.

## P6 — Procurement — CLOSED

Transport HTTP fournisseur avec HTTPS public + garde SSRF ; idempotence/hash canonique ; succès seulement 2xx + référence ; blocage du faux DRAFT→SENT manuel ; référence/ETA/backorders ; réceptions partielles/complètes idempotentes ; réconciliation ; audit trail.  
HEAD closeout `3ab5863d79adc0f11e09052fe6c59789ecd1edbf` : CI #2342, Catalog #724, T2 #1451, Patient #750, Portability #336, Onboarding #143 SUCCESS.  
PR #316 mergée ; master `1cee3f30168845602a2f8fdfb2a5bbf1694e9c71`.

## P7 — Stock Intelligence — CLOSED

`StockItem` reste l'agrégat canonique ; mapping produit→stock explicite ; facteur d'unité/min/cible ; ledger append-only/idempotent ; réception→stock automatique ; `PENDING_MAPPING` sans stock partiel ; replay sans double incrément ; lots/péremptions ; lots expirés exclus du stock utilisable ; consommation FEFO ; suggestions de réassort ; tenant scoping.  
HEAD `77da0418d10548d279ce0dbdbf2d460b2362e492` : CI #2359, Catalog #739, T2 #1466, Patient #765, Portability #348, Onboarding #155 SUCCESS.  
PR #318 mergée ; master `7b7aeb4569d31e1fb26460d032523344a7f21d21`.

## P8 — Finance & monétisation — EN COURS — 0/6

### Goal
Avoir une vérité financière serveur par commande, cohérente avec annulations/réceptions, permettant reporting et rapprochement sans calcul financier autoritaire côté frontend.

### Succès observable
1. modèles commission / remise / revente / frais fixes calculés côté serveur ;
2. revenu reconnu et reversal d'annulation déterministes ;
3. rapprochement commande ↔ réception ↔ montant financier ;
4. reporting cabinet interne agrégé ;
5. tenant scoping + RBAC ;
6. scénarios ciblés + CI verts.

### Preuve attendue
Tests backend couvrant les modèles financiers, transitions, annulations, réception/rapprochement et isolation cabinet ; closeout + merge vérifié avant crédit.

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas le travail indépendant. Aucun EP CLOSED sans closeout complet.

## Reprise
`P0 CLOSED → P1 CLOSED → P2 CLOSED → P3 CLOSED → P4 CLOSED → P5 CLOSED → P6 CLOSED → P7 CLOSED → P8 EN COURS → P9 → P10 → P11`

**Crédit CLOSED : 80/100 EP.**  
**Next exact :** implémenter P8 sur une branche propre issue de `master` puis certifier les scénarios financiers serveur.
