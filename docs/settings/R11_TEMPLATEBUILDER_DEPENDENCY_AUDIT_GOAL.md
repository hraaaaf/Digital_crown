# R11 — TemplateBuilder legacy : audit de dépendances

Date : 2026-08-19
Scope : legacy document-template/settings UI uniquement.

## Goal
Prouver si le TemplateBuilder legacy est encore atteignable ou consommé avant toute suppression/quarantaine, puis identifier les idées réellement uniques à migrer vers les réglages documentaires actuels.

## Succès
1. inventaire des fichiers dont le nom ou le contenu référence `TemplateBuilder`, `designConfig`, template builder / builder de modèle ;
2. graphe minimal des imports/exports et routes ;
3. preuve de reachability depuis `App.tsx`, routeurs frontend, Settings ou Document Studio ;
4. inventaire des capacités uniques encore absentes de R3/R4 ;
5. verdict : GARDER / EXTRAIRE PUIS SUPPRIMER / QUARANTAINER ;
6. aucune suppression avant preuve.

## Preuve
Workflow grep repository complet, artefact de références exactes au HEAD.

Hors scope : modification du Document Studio clinique, suppression de fichier, Vercel.
