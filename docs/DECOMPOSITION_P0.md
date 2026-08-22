# DECOMP-P0 — Décomposition des fichiers source volumineux

## Goal

Décomposer les fichiers source volumineux de Digital Crown en modules cohésifs sans changement fonctionnel, métier, API, schéma DB ou comportement visuel.

## Baseline vérifiée

Référence initiale : `master` @ `a25893c7c1c3bb5bbecd6fb8ff54a0d81ab440a0`.

Le scan global initial a détecté 23 fichiers de production non explicitement Legacy >= 30 000 octets.

### P0 initial

1. `frontend/src/pages/AccountingPage.tsx` — 77 175 B — 1 448 lignes
2. `backend/models.py` — 74 684 B — 1 444 lignes
3. `frontend/src/features/ortho/CephaloTracingLayer.tsx` — 61 545 B — 1 263 lignes

## P0-A — AccountingPage — CLOSED

Résultat vérifié :

- `AccountingPage.tsx` : 77 175 B -> 35 465 B (-54,1 %) ;
- 1 448 lignes -> environ 672 lignes ;
- le fichier sort du seuil P0 (>50 KB et >1 000 lignes) ;
- aucun endpoint, paramètre, label métier ou action volontairement modifié.

Extractions conservées :

- `features/accounting/types.ts`
- `features/accounting/utils.ts`
- `features/accounting/components/AccountingHeader.tsx`
- `features/accounting/components/AccountingTabs.tsx`
- `features/accounting/components/TreasuryPanel.tsx`
- `features/accounting/components/InsightsPanel.tsx`
- `features/accounting/components/UnpaidPanel.tsx`
- `features/accounting/hooks/useAccountingController.ts`

`HistoryPanel` n'est pas extrait dans P0-A : après extraction du controller, la page est déjà sortie du P0. Une extraction supplémentaire serait un refactor P1 séparé, non nécessaire au Goal P0.

Preuves :

- gates dédiés types/helpers/panneaux/header/tabs/controller ;
- TypeScript exact vert sur les extractions matérialisées ;
- run Tabs `32593406699` SUCCESS ;
- run Controller `32593747278` SUCCESS ;
- T2 et Catalog verts sur le HEAD ayant déclenché le controller ;
- harness temporaires supprimés après usage.

## P0-B — CephaloTracingLayer — CLOSED

Résultat vérifié :

- `CephaloTracingLayer.tsx` : 61 545 B -> 45 326 B (-26,4 %) ;
- 1 263 lignes -> 995 lignes ;
- le fichier sort des deux seuils P0 : <50 000 B et <1 000 lignes ;
- aucune formule céphalométrique, norme clinique, coordonnée ou interaction volontairement modifiée.

Extractions conservées :

- `components/CephaloCalibrationOverlay.tsx`
- `components/CephaloMagnifierOverlay.tsx`
- `hooks/useCephaloInteraction.ts`
- `components/CephaloLandmarkReticles.tsx`
- `components/CephaloSvgDefs.tsx`

Contrats v4.2 explicitement préservés :

- conversion canonique `getScreenCTM().inverse()` ;
- `setPointerCapture` ;
- `activeDragPos` utilisé pour `dispX/dispY` pendant le drag ;
- commit final via `onUpdateLandmarks` ;
- defs SVG loupe/glow/VTO conservées.

Preuves :

- overlays run `32594263257` SUCCESS ;
- interaction run `32594481359` SUCCESS ;
- sortie P0 / reticles + defs run `32594870931` SUCCESS ;
- TypeScript exact vert ;
- `cephaloUtils.test.ts` : 15/15 tests verts ;
- visual parity run `32595321289` SUCCESS ;
- 9/9 paires BEFORE/AFTER pixel-identiques : standard, calibration et pro en 1280 / 768 / 390 ;
- zéro erreur runtime dans le harness visuel ;
- artifact GitHub `9481401688`, digest `sha256:4fe1810dbe7403855ec171cff70bf13fa9d0360db9284b870b698e2ac84ae640` ;
- score visuel de parité : 10/10, fondé sur égalité pixel stricte des 9 paires ;
- harness temporaires retirés après certification.

## P0-C — models.py — CURRENT

Baseline revalidée sur `master` @ `d96c36cdf0d33a75d751f6aea3a9b89b6894683e` :

- `backend/models.py` — 74 684 B — 1 444 lignes ;
- ce merge master est docs-only et ne modifie pas le registre ORM ;
- satellites déjà existants à respecter : `models_catalog_plan.py`, `models_clinical_p3.py`, `models_identity_p4.py`, `models_imaging_p4.py`.

Nature : registre multi-domaines SQLAlchemy. Ce fichier ne doit pas être découpé comme un simple composant UI.

Architecture d'exécution verrouillée :

- une seule `Base`, déplacée dans un module neutre puis ré-exportée par `backend.models` ;
- `backend.models` reste la façade historique de compatibilité ;
- extraction mécanique des domaines de queue autonomes, sans architecture parallèle aux satellites existants ;
- aucune migration ni modification de schéma.

Succès :

- `backend/models.py` <50 000 B et <1 000 lignes ;
- tous les imports historiques continuent de fonctionner ;
- metadata SQLAlchemy et relations ORM strictement identiques avant/après ;
- aucune migration de schéma.

Preuve requise avant commit produit :

- snapshot avant/après de `Base.metadata` : tables, colonnes, FK, contraintes, indexes ;
- snapshot des relations ORM après `configure_mappers()` ;
- façade d'imports historique ;
- satellites existants sur la même `Base` ;
- `Base.metadata.create_all()` sur SQLite mémoire ;
- compilation Python et tests backend ciblés ;
- diff limité aux modules de modèles prévus ;
- un seul benchmark/run lourd après préparation complète.

## Hors scope

- fichiers explicitement Legacy jusqu'à preuve d'usage ou d'inutilisation ;
- migrations historiques ;
- assets, données, lockfiles ;
- refonte métier ou UX ;
- optimisation opportuniste ;
- déploiement Vercel.

## Règle d'exécution

Décomposition uniquement. Aucun changement fonctionnel opportuniste pendant ces lots.
