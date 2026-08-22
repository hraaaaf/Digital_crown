# DECOMP-P0 — Décomposition des fichiers source volumineux

## Goal

Décomposer les fichiers source volumineux de Digital Crown en modules cohésifs sans changement fonctionnel, métier, API, schéma DB ou comportement visuel.

## Baseline vérifiée

Référence courante : `master` @ `a25893c7c1c3bb5bbecd6fb8ff54a0d81ab440a0`.

Le scan global initial a détecté 23 fichiers de production non explicitement Legacy >= 30 000 octets. Entre le scan et le verrouillage de cette roadmap, `master` a avancé de 34 commits. Une comparaison Git a confirmé que, parmi les trois P0, seul `backend/models.py` a été modifié (+5/-2). `AccountingPage.tsx` et `CephaloTracingLayer.tsx` sont restés inchangés.

### P0 courant

1. `frontend/src/pages/AccountingPage.tsx` — 77 175 B — 1 448 lignes
2. `backend/models.py` — 74 684 B — 1 444 lignes
3. `frontend/src/features/ortho/CephaloTracingLayer.tsx` — 61 545 B — 1 263 lignes

## Ordre d'exécution

### P0-A — AccountingPage

Responsabilités actuellement mélangées :

- orchestrateur page + navigation des tabs ;
- History / honoraires ;
- Treasury ;
- Financial Insights ;
- Unpaid / patient debts ;
- types et helpers purs : grouping, breakdown, chart/trend ;
- actions document/export/email/edit/delete/encaissement.

Frontières cibles :

- `accounting/types.ts`
- `accounting/utils.ts`
- `accounting/components/AccountingHeader.tsx`
- `accounting/components/AccountingTabs.tsx`
- `accounting/components/HistoryPanel.tsx`
- `accounting/components/TreasuryPanel.tsx`
- `accounting/components/InsightsPanel.tsx`
- `accounting/components/UnpaidPanel.tsx`
- `accounting/useAccountingPageController.ts`
- `AccountingPage.tsx` conservé comme orchestrateur mince.

Ordre sûr : présentational extraction -> helpers/types -> controller/hooks.

Succès : `AccountingPage.tsx` devient un orchestrateur mince et les quatre surfaces restent strictement équivalentes.

Preuve :

- build/typecheck frontend ;
- tests ciblés helpers/contrôleur ;
- régression accounting existante ;
- aucune modification des endpoints, paramètres, labels ou actions.

### P0-B — CephaloTracingLayer

Responsabilités actuellement mélangées :

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

Succès : orchestrateur mince, aucune variation de coordonnées, formules, normes ou interaction.

Preuve :

- tests math / VTO / coordonnées ;
- tests ortho existants ;
- capture BEFORE puis AFTER sur les mêmes viewports ;
- validation explicite du drag, calibration, loupe, IMPA et I/F.

### P0-C — models.py

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
