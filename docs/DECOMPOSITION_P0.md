# DECOMP-P0 — Décomposition des fichiers source volumineux

## Goal

Décomposer les fichiers source volumineux de Digital Crown en modules cohésifs sans changement fonctionnel, métier, API, schéma DB ou comportement visuel.

## Statut global — CLOSED

Les 3 lots P0 sont fermés et certifiés :

1. P0-A `AccountingPage.tsx` — CLOSED
2. P0-B `CephaloTracingLayer.tsx` — CLOSED
3. P0-C `backend/models.py` — CLOSED

Référence initiale : `master` @ `a25893c7c1c3bb5bbecd6fb8ff54a0d81ab440a0`.

Le scan global initial avait détecté 23 fichiers de production non explicitement Legacy >= 30 000 octets. Le chantier P0 ciblait les trois fichiers les plus critiques au-dessus des seuils de taille/complexité.

## P0-A — AccountingPage — CLOSED

Résultat vérifié :

- `AccountingPage.tsx` : 77 175 B -> 35 465 B (-54,1 %) ;
- 1 448 lignes -> environ 672 lignes ;
- sortie du seuil P0 ;
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

`HistoryPanel` n'a pas été extrait : après extraction du controller, la page était déjà hors P0. Une extraction supplémentaire relèverait d'un refactor P1 séparé.

Preuves :

- gates dédiés types/helpers/panneaux/header/tabs/controller ;
- TypeScript exact vert ;
- run Tabs `32593406699` SUCCESS ;
- run Controller `32593747278` SUCCESS ;
- T2 et Catalog verts sur le HEAD ayant déclenché le controller ;
- harness temporaires retirés après usage.

## P0-B — CephaloTracingLayer — CLOSED

Résultat vérifié :

- `CephaloTracingLayer.tsx` : 61 545 B -> 45 326 B (-26,4 %) ;
- 1 263 lignes -> 995 lignes ;
- sortie des deux seuils P0 : <50 000 B et <1 000 lignes ;
- aucune formule céphalométrique, norme clinique, coordonnée ou interaction volontairement modifiée.

Extractions conservées :

- `components/CephaloCalibrationOverlay.tsx`
- `components/CephaloMagnifierOverlay.tsx`
- `hooks/useCephaloInteraction.ts`
- `components/CephaloLandmarkReticles.tsx`
- `components/CephaloSvgDefs.tsx`

Contrats v4.2 préservés :

- `getScreenCTM().inverse()` ;
- `setPointerCapture` ;
- `activeDragPos` pour `dispX/dispY` pendant le drag ;
- commit final via `onUpdateLandmarks` ;
- defs SVG loupe/glow/VTO conservées.

Preuves :

- overlays run `32594263257` SUCCESS ;
- interaction run `32594481359` SUCCESS ;
- sortie P0 / reticles + defs run `32594870931` SUCCESS ;
- TypeScript exact vert ;
- `cephaloUtils.test.ts` : 15/15 verts ;
- visual parity run `32595321289` SUCCESS ;
- 9/9 paires BEFORE/AFTER pixel-identiques : standard, calibration et pro en 1280 / 768 / 390 ;
- zéro erreur runtime ;
- artifact GitHub `9481401688`, digest `sha256:4fe1810dbe7403855ec171cff70bf13fa9d0360db9284b870b698e2ac84ae640` ;
- score visuel de parité : 10/10 ;
- harness temporaires retirés après certification.

## P0-C — models.py — CLOSED

Baseline revalidée sur `master` @ `d96c36cdf0d33a75d751f6aea3a9b89b6894683e` : `backend/models.py` = 74 684 B / 1 444 lignes.

Résultat vérifié :

- `backend/models.py` : 74 684 B -> 45 988 B ;
- 1 444 lignes -> 922 lignes ;
- sortie des deux seuils P0 : <50 000 B et <1 000 lignes ;
- commit produit unique : `01da0073e31e2571081751c72fdccbdb1c58eaea` ;
- aucune migration de schéma ;
- `backend.models` reste la façade historique ;
- une seule `Base` SQLAlchemy partagée.

Extractions conservées :

- `backend/models_base.py`
- `backend/models_platform.py`
- `backend/models_operations.py`
- `backend/models_bot_settings.py`

Satellites existants conservés sur la même `Base` :

- `models_catalog_plan.py`
- `models_clinical_p3.py`
- `models_identity_p4.py`
- `models_imaging_p4.py`

Preuves :

- certification ORM run `32595937818` SUCCESS ;
- snapshot ORM BEFORE/AFTER strictement identique : 57 tables, 57 mappers, 75 exports ;
- tables, colonnes, defaults, FK, contraintes, indexes et relations inclus dans le snapshot ;
- `configure_mappers()` vert ;
- compilation Python des modules vertes ;
- imports historiques et Base unique verts ;
- `Base.metadata.create_all()` sur SQLite mémoire : 57/57 tables ;
- pytest backend ciblé run `32596963257` SUCCESS : 3/3 tests, 0,87 s ;
- pytest couvre réexports exacts de la façade, Base/registry unique, schéma complet et round-trips SQLite sur modèles extraits sûrs ;
- certification pytest read-only : `git status --porcelain` vide ;
- aucun fichier de migration touché.

## Hors scope

- fichiers explicitement Legacy jusqu'à preuve d'usage ou d'inutilisation ;
- migrations historiques ;
- assets, données, lockfiles ;
- refonte métier ou UX ;
- optimisation opportuniste ;
- déploiement Vercel.

## Conclusion

DECOMP-P0 atteint son Goal : les trois fichiers P0 ciblés sont sortis de leurs seuils de volumétrie tout en conservant les contrats fonctionnels, visuels et ORM prouvés par leurs certifications dédiées.
