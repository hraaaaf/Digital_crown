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

## P0-B — CephaloTracingLayer — NEXT

Responsabilités mélangées :

- conversion coordonnées SVG / pointer events ;
- drag landmarks + magnifier ;
- VTO et déplacement tissus mous ;
- rendu des analyses squelettiques ;
- wedges IMPA / I-F ;
- profil cutané spline ;
- projections N'/A'/B' + McNamara ;
- calibration ;
- loupe.

Ordre sûr :

1. extraire les couches purement visuelles de calibration et loupe ;
2. isoler pointeur / drag sans changer `getScreenCTM().inverse()` ;
3. extraire VTO et profil cutané avec tests purs ;
4. extraire projections et skeletal overlay sans toucher aux formules ni aux normes.

Succès : orchestrateur sous le seuil P0, aucune variation de coordonnées, formules, normes ou interaction.

Preuve :

- tests math / VTO / coordonnées ;
- tests ortho existants ;
- capture BEFORE puis AFTER sur les mêmes viewports si l'extraction affecte le rendu ;
- validation explicite du drag, calibration, loupe, IMPA et I/F.

## P0-C — models.py

Nature : registre multi-domaines SQLAlchemy. Ce fichier ne doit pas être découpé comme un simple composant UI.

Architecture cible : conserver `backend/models.py` comme agrégateur de compatibilité et déplacer les définitions vers des modules partageant une seule `Base`.

Domaines cibles :

- enums/base ;
- auth/cabinet ;
- patients/clinical ;
- imaging ;
- documents ;
- accounting ;
- intelligence/mobile ;
- lab/stock ;
- marketplace ;
- bot.

Succès : tous les imports historiques continuent de fonctionner, metadata SQLAlchemy identique, aucune migration de schéma.

Preuve :

- snapshot avant/après de `Base.metadata` : tables, colonnes, FK, contraintes et indexes ;
- import complet de l'agrégateur ;
- tests backend ciblés ;
- absence de changement de schéma.

## Hors scope

- fichiers explicitement Legacy jusqu'à preuve d'usage ou d'inutilisation ;
- migrations historiques ;
- assets, données, lockfiles ;
- refonte métier ou UX ;
- optimisation opportuniste ;
- déploiement Vercel.

## Règle d'exécution

Décomposition uniquement. Aucun changement fonctionnel opportuniste pendant ces lots.
