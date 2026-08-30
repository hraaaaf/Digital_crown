# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p4-catalog-products-v3` — P4 closeout  
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
- **P4 : 8/8 CERTIFIED / MERGE READY** — PR #311 ; HEAD runtime `ccb09ed2908f62e50fdd185e5081a61d1145063d`.
- **Global CLOSED : 42/100 = 42 %.**
- **Global certifié incluant P4 : 50/100 = 50 %.**

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

## P4 — Catalogue & produits — CERTIFIED / MERGE READY

### Goal
Le catalogue ne sert pas de données périmées ou d'un autre scope ; recherche et pagination sont déterministes ; le merchandising backend est conservé sans modifier visuellement P5 avant son protocole.

### Implémenté
1. cache Marketplace TTL **15 min** ;
2. scope cache embarqué et vérifié ; cache expiré/invalide supprimé ;
3. `isFeatured` / `sortOrder` conservés dans le modèle frontend ;
4. recherche backend étendue au descriptif long ;
5. pagination `offset/limit` fournisseurs et produits ;
6. bornes de pagination invalides rejetées ;
7. aucun réordonnancement visible avant P5.

### Diff certifié
PR #311 reconstruite directement sur `master` post-P3 closeout `bab82326f7d40e6639f5a1407cf54a9b72807d8c` : **1 commit, 4 fichiers, +311/-9**, sans changement UI.

### Preuve runtime
HEAD `ccb09ed2908f62e50fdd185e5081a61d1145063d` :
- CI #2333 : **SUCCESS** ;
- Catalog Connected Truth #717 : **SUCCESS** ;
- T2 Runtime #1444 : **SUCCESS** ;
- Patient P7 #743 : **SUCCESS** ;
- M6-I #244 : **SKIPPED** par périmètre.

### Gate
**CERTIFIED — 8/8 EP prouvés ; merge #311 + vérification master restent requis avant crédit CLOSED.**

## P5 — UX/UI Marketplace — BEFORE CERTIFIED

### Protocole obligatoire
`BEFORE 390/430/768/1280 → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison → accessibilité/E2E → score visuel`.

### BEFORE
Run **Marketplace P5 BEFORE #5** : **SUCCESS**, HEAD `4aece82bee3b7285b1df0dbdeea06fa7e28cf67a`.
Artefact : 4 captures 390×844, 430×932, 768×1024, 1280×800 + rapport runtime.
Constats vérifiés : aucun page error ; aucun overflow document détecté ; **H1 visuellement rogné à 390 px malgré la métrique overflow** ; hero trop dominant sur le premier écran mobile.

### Goal P5
Prioriser l'achat réel plutôt que le marketing : recherche/catalogue/panier visibles plus tôt, hero compact, titre non rogné, CTA conforme au vrai statut DRAFT, checkout cohérent avec le contrat serveur, interaction sans reload, contrôles accessibles.

### Critères observables
- H1 entièrement visible à 390/430/768/1280 ;
- recherche + premier produit accessibles dans le premier écran ou immédiatement sous un hero compact ;
- aucun overflow horizontal ;
- aucun `window.location.reload()` après ajout panier ;
- boutons quantité nommés pour lecteur d'écran ;
- CTA ne prétend pas envoyer au fournisseur si seule une commande locale est créée ;
- AFTER sur les 4 viewports, mêmes données/harness, sans page/console errors.

Le **mockup/référence reste à figer avant toute modification UI produit**.

## P6 — Procurement — préparation parallèle, 0/8 crédité
Travail non crédité tant que rebase/certification absents : réception partielle idempotente, réconciliation, accusé fournisseur/ETA/backorder, transport HTTP fournisseur avec preuve/idempotence et blocage du faux `DRAFT → SENT` manuel. Aucun envoi externe réel n'est revendiqué sans test/CI.

## Idées prioritaires
Split fournisseur (10/10 valeur), réassort consommation/min-max (10/10), réception-stock (10/10), lots/péremptions (10/10), historique prix/MOQ/délai (9/10), rapprochement facture (9/10).

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas le travail indépendant. Aucun EP CLOSED sans closeout complet.

## Reprise
`P0 CLOSED → P1 CLOSED → P2 CLOSED → P3 CLOSED → P4 CERTIFIED/MERGE READY → P5 BEFORE CERTIFIED → P6 → P7 → P8 → P9 → P10 → P11`

**Crédit CLOSED : 42/100 EP ; certifié : 50/100 EP.**  
**Next exact :** merger #311 après closeout CI, vérifier `master`, créditer P4 ; figer le mockup/référence P5 puis seulement implémenter l'AFTER ; certifier P6 en parallèle.
