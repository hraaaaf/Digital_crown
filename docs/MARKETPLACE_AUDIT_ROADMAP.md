# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : CLOSED**  
**Baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Lot actif :** aucun — chantier Marketplace clôturé  
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
| P8 — Finance & monétisation | 6 | CLOSED | scénarios financiers serveur + merge vérifié |
| P9 — Automatisation fournisseur | 5 | CLOSED | idempotence/retry/sync + audit + merge vérifié |
| P10 — Superadmin Marketplace | 4 | CLOSED | RBAC + audit trail global + merge vérifié |
| **P11 — Certification finale** | **5** | **CLOSED** | tous gates finaux verts sur HEAD exact + merge vérifié |
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
- P9 : 5/5 CLOSED — PR #321 ; squash merge `ff661156e3edb4181b895765d17bbd5e23825298`.
- P10 : 4/4 CLOSED — PR #322 ; squash merge `7ec007ce677fdb342d9cd304d41997babab1f7f2`.
- P11 : 5/5 CLOSED — PR #323 ; squash merge `dbb35b524282d85e0fa881ce5f2ba1ad56e64e03`.
- **Global CLOSED : 100/100 = 100 %.**

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
Conserve P2 comme seule autorité de reconnaissance de revenu ; facture fournisseur idempotente ; coût attendu déterministe ; rapprochement commande ↔ réception ↔ facture ; audit ; reporting tenant-scoped ; Superadmin-only.  
HEAD mergé `538ce138987cbe6b147770c210bf3df2f19782db` : CI #2368, Catalog #745, T2 #1472, Patient #771, Portability #353, Onboarding #160 SUCCESS. Tests ciblés : 9 scénarios.  
**Gate : CLOSED — 6/6 EP.**

## P9 — Automatisation fournisseur — CLOSED

### Goal
Synchroniser un catalogue fournisseur API sans duplication, corruption locale ni perte de baseline exploitable.

### Implémenté
- endpoint fournisseur `/catalog` avec garde HTTPS/SSRF héritée de P6 ;
- snapshot canonique + hash déterministe ;
- upsert prix/disponibilité en préservant merchandising local ;
- produits précédemment gérés par la sync et absents du snapshot → `DISCONTINUED`, jamais supprimés ;
- produits manuels non gérés par la sync préservés ;
- même payload = `NO_CHANGE` seulement si l'état local est déjà conforme ; sinon réparation du drift ;
- retry/backoff exponentiel + force retry Superadmin ;
- freshness `FRESH/STALE/DEGRADED/NEVER_SYNCED` ;
- protection contre identités locales SKU/externalProductId ambiguës ;
- audit append-only `SUPPLIER_SYNC_APPLIED`, `SUPPLIER_SYNC_NO_CHANGE`, `SUPPLIER_SYNC_FAILED` ;
- tenant/supplier scoping et RBAC.

### Preuve
HEAD certifié `65d502d15faf05be88a9abec91649af4de6967ea` :
- CI #2388 SUCCESS ;
- Catalog #763 SUCCESS ;
- T2 #1490 SUCCESS ;
- Patient #789 SUCCESS ;
- Portability #371 SUCCESS ;
- Onboarding #178 SUCCESS ;
- M6-I #290 skipped par périmètre.

PR #321 squash-mergée ; master `ff661156e3edb4181b895765d17bbd5e23825298`.

### Gate
**CLOSED — 5/5 EP crédités après certification du HEAD et merge vérifié.**

## P10 — Superadmin Marketplace — CLOSED

### Goal
Supervision Marketplace globale cross-cabinet avec RBAC Superadmin, métriques, incidents sync, gouvernance/accords fournisseur, catalogue global et audit append-only.

### Implémenté
- overview global cabinets/fournisseurs/produits/commandes/revenus/factures/incidents/accords ;
- commandes cross-cabinet sans exposition des coordonnées client ;
- incidents sync globaux ;
- gouvernance fournisseur + accords avec confirmation explicite ;
- audit append-only des mutations plateforme ;
- CRUD global fournisseurs/produits avec cabinet explicite ;
- `employerId` limité aux propriétaires de cabinet ;
- identités SKU/externalProductId case-insensitive compatibles P9 ;
- validation des dates d’accord sur l’état final persisté ;
- routes exactes sous `/api/superadmin/marketplace` ;
- boundary web-only : sessions mobiles refusées ; mutations cookie protégées par Origin ;
- cycle d'import supprimé par montage depuis le router Superadmin canonique.

### Preuve
HEAD certifié `10d48268c6fd8daa5441527571a326321607c963` :
- CI #2400 SUCCESS ;
- Catalog #773 SUCCESS ;
- T2 #1500 SUCCESS ;
- Patient #799 SUCCESS ;
- M6-I #300 skipped par périmètre.

PR #322 squash-mergée ; master `7ec007ce677fdb342d9cd304d41997babab1f7f2`.

### Gate
**CLOSED — 4/4 EP crédités après certification du HEAD et merge vérifié.**

## P11 — Certification finale — CLOSED

### Goal
Reconstruire et exécuter sur master post-P10 un gate final Marketplace qui couvre les preuves backend, frontend et visuelles réellement encore pertinentes, sans ressusciter des contrats historiques obsolètes.

### Preuve
HEAD candidat certifié `dee60c11cce9d268bdcb315a2a0f826162ecf2c9` :
- Marketplace Final Certification #7 SUCCESS ;
- backend Marketplace P1-P10 : **105/105 tests** ;
- frontend Marketplace : **8/8 tests** + build production SUCCESS ;
- visuel : 390×844 / 430×932 / 768×1024 / 1280×800, 4/4 HTTP 200, aucun overflow horizontal, H1 visible, aucun page/console error, `invalidCount=0` ;
- checkout : exactement 1 POST, même URL après submit, commande DRAFT confirmée ;
- artefact `marketplace-p11-final-visual` : 416131 octets, digest `sha256:b92f3e7e9cff2a836508d12f373da01c08b5e6a92d3ddfbb9d9c327636c77568` ;
- CI #2421 SUCCESS ;
- Catalog #792 SUCCESS ;
- T2 #1519 SUCCESS ;
- Patient #818 SUCCESS ;
- M6-I #319 skipped par périmètre.

PR #323 squash-mergée ; master `dbb35b524282d85e0fa881ce5f2ba1ad56e64e03`.

### Gate
**CLOSED — 5/5 EP crédités après certification du HEAD exact et merge vérifié.**

## Règles
Backend = vérité financière/statuts. Frontend jamais autorité sécurité. Scoping obligatoire. Aucun Vercel sans autorisation. CI pending n'arrête pas le travail indépendant. Aucun EP CLOSED sans closeout complet.

## Reprise
`P0 CLOSED → P1 CLOSED → P2 CLOSED → P3 CLOSED → P4 CLOSED → P5 CLOSED → P6 CLOSED → P7 CLOSED → P8 CLOSED → P9 CLOSED → P10 CLOSED → P11 CLOSED`

**Crédit CLOSED : 100/100 EP.**  
**Next exact :** aucun pour ce chantier ; ouvrir un nouveau lot uniquement sur un nouveau Goal explicite.
