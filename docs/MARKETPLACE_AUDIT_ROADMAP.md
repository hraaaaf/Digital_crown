# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Chantiers actifs :** P5 UX/UI + P7 Stock Intelligence  
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
- **P0 : 8/8 CLOSED** — PR #301.
- **P1 : 14/14 CLOSED** — PR #302 ; merge `9900aaddebffc593afcd436b5ecceefaf9814f48`.
- **P2 : 12/12 CLOSED** — PR #306 ; merge `cbffb626d099af98f6536a2694930753d637522c`.
- **P3 : 8/8 CLOSED** — PR #309 ; merge `5f773491a58bc552c35aeb7dddd078a058f3c417`.
- **P4 : 8/8 CLOSED** — PR #311 ; merge `5ccbf52fd87b59f5c3fbf6f128933a3e651f7cb1`.
- **P5 : 0/14 EN COURS** — PR #313 ; AFTER #5 SUCCESS, CI générale encore requise + comparaison visuelle/score.
- **P6 : 8/8 CLOSED** — PR #316 ; merge `1cee3f30168845602a2f8fdfb2a5bbf1694e9c71`.
- **P7 : 0/8 EN COURS** — reconstruction propre post-P6 requise avant crédit.
- **Global CLOSED : 58/100 = 58 %.**

## P1 — Trust & sécurité — CLOSED
HEAD `e8380bd895fc37759fe783fa854d4fcbb39a2932` : CI #2246 SUCCESS, T2 #1361 SUCCESS, Patient #660 SUCCESS.

## P2 — Order Engine — CLOSED
HEAD `fa7fba4ad518d0e04c7367156415a56687aed907` : CI #2260 SUCCESS, T2 #1374 SUCCESS, Patient #673 SUCCESS.

## P3 — Multi-fournisseurs — CLOSED
HEAD produit `a7c26947d1ebcfde0bc95149237d1058245eee1a` : CI #2310 SUCCESS, Catalog #696 SUCCESS, T2 #1423 SUCCESS, Patient #722 SUCCESS.  
HEAD closeout `b2c18bc458a953e8d470f0dc9231a616e2602d8f` : CI #2317 SUCCESS, Catalog #703 SUCCESS, T2 #1430 SUCCESS, Patient #729 SUCCESS.

## P4 — Catalogue & produits — CLOSED
HEAD runtime `ccb09ed2908f62e50fdd185e5081a61d1145063d` : CI #2333 SUCCESS, Catalog #717 SUCCESS, T2 #1444 SUCCESS, Patient #743 SUCCESS.  
HEAD closeout `bacbef138dc0fb1e50d7fc933a1b384ef09c4cef` : CI #2334 SUCCESS, Catalog #718 SUCCESS, T2 #1445 SUCCESS, Patient #744 SUCCESS.

## P5 — UX/UI Marketplace — EN COURS

### BEFORE
Marketplace P5 BEFORE #5 : **SUCCESS** sur 390×844 / 430×932 / 768×1024 / 1280×800.  
Constats : H1 rogné à 390 px ; hero trop dominant ; recherche/catalogue trop bas.

### Goal
Achat réel prioritaire : recherche/catalogue/panier plus tôt, hero compact, titre entier, CTA DRAFT exact, checkout cohérent, aucun reload, contrôles accessibles.

### Référence figée avant code
- `docs/marketplace/P5_UI_REFERENCE.md`
- `docs/marketplace/P5_UI_REFERENCE.svg`

### AFTER
AFTER #2 : FAILURE sur densité mobile ; aucun overflow/error/fuite commerciale. Le gate mesurait aussi par erreur le second produit comme « premier produit » ; le test a été corrigé sans affaiblir le critère.  
HEAD actuel `f7210d35499c1947eb47208a2360ea856ea11de2` : **Marketplace P5 AFTER #5 SUCCESS**, Catalog #728 SUCCESS, T2 #1455 SUCCESS, Patient #754 SUCCESS ; CI #2346 restait en cours au dernier contrôle.  
Le gate #5 vérifie aussi le parcours réel ajout panier → formulaire → POST → succès DRAFT sans reload.

### Gate
**0/14 EP** tant que CI générale + lecture des captures AFTER + comparaison BEFORE/AFTER + score visuel + merge ne sont pas prouvés.

## P6 — Procurement — CLOSED

### Goal
Une commande ne devient envoyée qu'avec preuve de transport fournisseur ; suivi et réceptions sont tenant-scoped, idempotents et réconciliés avec la commande canonique.

### Implémenté
- dispatch HTTP fournisseur HTTPS public + garde SSRF ;
- clé d'idempotence + hash canonique ;
- succès uniquement 2xx + référence fournisseur ;
- échec enregistré sans faux `SENT_TO_PARTNER` ;
- PATCH manuel DRAFT→SENT bloqué ;
- référence fournisseur, ETA, backorders ;
- réceptions partielles/complètes idempotentes ;
- lot/péremption dans les lignes ;
- réconciliation quantités ;
- `CONFIRMED → FULFILLED` seulement à réception complète ;
- audit trail.

### Preuve finale
HEAD produit `6d52cd53ba38f1c08e70d615ea30e22d22d311ba` : CI #2340, Catalog #722, T2 #1449, Patient #748, Portability #334, Onboarding #141 **SUCCESS**.  
HEAD closeout `3ab5863d79adc0f11e09052fe6c59789ecd1edbf` : CI #2342, Catalog #724, T2 #1451, Patient #750, Portability #336, Onboarding #143 **SUCCESS**.  
PR #316 squash-mergée ; `master` vérifié à `1cee3f30168845602a2f8fdfb2a5bbf1694e9c71`.

### Limite explicite
L'idempotence externe dépend du respect de `Idempotency-Key` par l'API fournisseur ; Digital Crown conserve sa preuve et réutilise la même clé.

### Gate
**CLOSED — 8/8 EP crédités.**

## P7 — Stock Intelligence — EN COURS

### Goal
Une réception Marketplace alimente automatiquement le `StockItem` existant sans double saisie ni double incrément, avec traçabilité produit/lot/péremption ; consommation et seuils produisent un réassort déterministe.

### Architecture retenue
- `StockItem` existant reste l'agrégat canonique ;
- mapping explicite `PartnerCatalogProduct → StockItem` avec facteur d'unité, min et cible ;
- ledger append-only/idempotent ;
- lots/péremptions ;
- application réception→stock automatique si mapping complet ;
- mapping absent : réception conservée `PENDING_MAPPING`, aucun stock partiel ;
- replay de la même réception applique le stock après mapping sans dupliquer la réception ;
- endpoint d'application explicite conservé pour rattrapage ;
- consommation idempotente avec allocation FEFO ;
- suggestions min→cible ;
- tenant scoping.

PR de travail #315 est encore empilée sur l'ancien P6 ; reconstruction directe sur `master` post-P6 obligatoire avant certification.

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas le travail indépendant. Aucun EP CLOSED sans closeout complet.

## Reprise
`P0 CLOSED → P1 CLOSED → P2 CLOSED → P3 CLOSED → P4 CLOSED → P5 EN COURS → P6 CLOSED → P7 EN COURS → P8 → P9 → P10 → P11`

**Crédit CLOSED : 58/100 EP.**  
**Next exact :** reconstruire P7 sur `master` post-P6 et certifier ; terminer P5 par CI + comparaison visuelle + score puis merge.
