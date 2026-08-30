# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Chantiers actifs :** P5 UX/UI PR #313 + P6 closeout PR #314  
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
- **P3 : 8/8 CLOSED** — PR #309 ; merge `master` `5f773491a58bc552c35aeb7dddd078a058f3c417` ; closeout `bab82326f7d40e6639f5a1407cf54a9b72807d8c`.
- **P4 : 8/8 CLOSED** — PR #311 ; merge `master` `5ccbf52fd87b59f5c3fbf6f128933a3e651f7cb1`.
- **P5 : 0/14 EN COURS** — PR #313 ; AFTER #2 rouge uniquement sur densité mobile.
- **P6 : 8/8 CERTIFIED / MERGE READY** — PR #314 ; HEAD produit `6d52cd53ba38f1c08e70d615ea30e22d22d311ba`.
- **Global CLOSED : 50/100 = 50 %.**
- **Global certifié incluant P6 : 58/100 = 58 %.**

## P1 — Trust & sécurité — CLOSED

### Preuve finale
HEAD `e8380bd895fc37759fe783fa854d4fcbb39a2932` : CI #2246 SUCCESS, T2 #1361 SUCCESS, Patient P7 #660 SUCCESS. PR #302 mergée puis `master` vérifié.

## P2 — Order Engine — CLOSED

### Preuve finale
HEAD `fa7fba4ad518d0e04c7367156415a56687aed907` : CI #2260 SUCCESS, T2 #1374 SUCCESS, Patient P7 #673 SUCCESS. PR #306 mergée ; `master` vérifié à `cbffb626d099af98f6536a2694930753d637522c`.

## P3 — Multi-fournisseurs — CLOSED

### Preuve finale
HEAD produit `a7c26947d1ebcfde0bc95149237d1058245eee1a` : CI #2310 SUCCESS, Catalog #696 SUCCESS, T2 #1423 SUCCESS, Patient #722 SUCCESS.  
HEAD closeout `b2c18bc458a953e8d470f0dc9231a616e2602d8f` : CI #2317 SUCCESS, Catalog #703 SUCCESS, T2 #1430 SUCCESS, Patient #729 SUCCESS.  
PR #309 squash-mergée ; `master` vérifié à `5f773491a58bc552c35aeb7dddd078a058f3c417`.

### Gate
**CLOSED — 8/8 EP crédités.**

## P4 — Catalogue & produits — CLOSED

### Preuve finale
HEAD runtime `ccb09ed2908f62e50fdd185e5081a61d1145063d` : CI #2333 SUCCESS, Catalog #717 SUCCESS, T2 #1444 SUCCESS, Patient #743 SUCCESS.  
HEAD closeout `bacbef138dc0fb1e50d7fc933a1b384ef09c4cef` : CI #2334 SUCCESS, Catalog #718 SUCCESS, T2 #1445 SUCCESS, Patient #744 SUCCESS.  
PR #311 squash-mergée ; `master` vérifié à `5ccbf52fd87b59f5c3fbf6f128933a3e651f7cb1`.

### Gate
**CLOSED — 8/8 EP crédités.**

## P5 — UX/UI Marketplace — EN COURS

### Protocole obligatoire
`BEFORE 390/430/768/1280 → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison → accessibilité/E2E → score visuel`.

### BEFORE
Run **Marketplace P5 BEFORE #5** : **SUCCESS**, HEAD `4aece82bee3b7285b1df0dbdeea06fa7e28cf67a`.  
Artefact : 4 captures 390×844, 430×932, 768×1024, 1280×800 + rapport runtime.  
Constats : aucun page error ; aucun overflow document ; H1 visuellement rogné à 390 px ; hero trop dominant.

### Goal
Prioriser l'achat réel : recherche/catalogue/panier visibles plus tôt, hero compact, titre non rogné, CTA conforme au statut DRAFT, checkout cohérent, interaction sans reload, contrôles accessibles.

### Référence figée avant code
PR #313 :
- `docs/marketplace/P5_UI_REFERENCE.md`
- `docs/marketplace/P5_UI_REFERENCE.svg`

### AFTER #2 — rouge diagnostiqué
HEAD `d0be12618da7a9aad226ca36b8c3118e77ee97d2` :
- CI #2339 SUCCESS ;
- Catalog #721 SUCCESS ;
- T2 #1448 SUCCESS ;
- Patient #747 SUCCESS ;
- Marketplace P5 AFTER #2 **FAILURE**.

Cause exacte :
- 390×844 : H1 visible, recherche top `593 px`, premier produit top `1624 px` ;
- 430×932 : H1 visible, recherche top `522 px`, premier produit top `1420 px` ;
- aucun overflow, page error, console error ou fuite de données commerciales ;
- CTA et disclosure DRAFT corrects.

**Conclusion :** la densité mobile reste trop forte avant la grille produit. Corriger la hiérarchie UI ; ne pas affaiblir le gate.

### Gate
**0/14 EP** tant que AFTER corrigé + interaction panier/checkout + comparaison BEFORE/AFTER + score visuel + merge ne sont pas prouvés.

## P6 — Procurement — CERTIFIED / MERGE READY

### Goal
Une commande ne devient envoyée qu'avec preuve de transport fournisseur ; suivi et réceptions sont tenant-scoped, idempotents et réconciliés avec la commande canonique.

### Implémenté
1. dispatch fournisseur HTTP API avec HTTPS public + garde SSRF ;
2. clé d'idempotence stable et hash du payload canonique ;
3. succès uniquement sur 2xx + référence fournisseur ;
4. échec enregistré sans faux passage en `SENT_TO_PARTNER` ;
5. blocage du PATCH manuel `DRAFT → SENT_TO_PARTNER` ;
6. référence fournisseur, ETA et backorders ;
7. réceptions partielles puis complètes avec clé idempotente ;
8. lots/péremptions capturés dans les lignes de réception ;
9. réconciliation quantités commandées/reçues ;
10. `CONFIRMED → FULFILLED` seulement à réception complète ;
11. audit trail associé.

### Preuve produit
HEAD `6d52cd53ba38f1c08e70d615ea30e22d22d311ba` :
- CI #2340 SUCCESS ;
- Catalog #722 SUCCESS ;
- T2 #1449 SUCCESS ;
- Patient #748 SUCCESS ;
- Portability #334 SUCCESS ;
- Onboarding Settings #141 SUCCESS ;
- M6-I #249 SKIPPED par périmètre.

### Limite explicitement assumée
L'idempotence externe dépend du respect de l'en-tête `Idempotency-Key` par l'API fournisseur. Digital Crown conserve sa propre preuve et réutilise la même clé lors des retries.

### Gate
**CERTIFIED — 8/8 EP prouvés ; closeout CI + merge #314 + vérification master requis avant crédit CLOSED.**

## P7 — Stock Intelligence — préparation active, 0/8

### Goal
Une réception Marketplace appliquée une seule fois alimente le stock existant sans double saisie, avec traçabilité produit/source/lot/péremption ; consommation et seuils permettent un réassort déterministe.

### Architecture retenue
- `StockItem` existant reste la vérité de stock du cabinet ;
- mapping explicite `PartnerCatalogProduct → StockItem`, jamais matching fuzzy par nom/SKU ;
- ledger immuable et idempotent des mouvements Marketplace ;
- une ligne de réception ne peut produire qu'un seul mouvement de stock ;
- lot/péremption conservés par mouvement ;
- stock agrégé mis à jour transactionnellement ;
- consommation tracée avant suggestion de réassort.

Branche de préparation : `marketplace/p7-stock-intelligence`, basée sur P6 propre. **Aucun EP crédité.**

## Idées prioritaires
Réassort consommation/min-max (10/10), réception-stock (10/10), lots/péremptions (10/10), historique prix/MOQ/délai (9/10), rapprochement facture (9/10).

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas le travail indépendant. Aucun EP CLOSED sans closeout complet.

## Reprise
`P0 CLOSED → P1 CLOSED → P2 CLOSED → P3 CLOSED → P4 CLOSED → P5 EN COURS → P6 CERTIFIED/MERGE READY → P7 PREP → P8 → P9 → P10 → P11`

**Crédit CLOSED : 50/100 EP ; certifié : 58/100 EP.**  
**Next exact :** closeout/merge P6 ; corriger la densité P5 mobile puis renforcer l'AFTER avec panier→checkout→POST DRAFT ; poursuivre P7 ledger/mapping/lots.
