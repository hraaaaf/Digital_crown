# R11 — TemplateBuilder legacy : audit de dépendances

Date : 2026-08-19
Scope : legacy document-template/settings UI uniquement.

## Goal
Prouver si le TemplateBuilder legacy est encore atteignable ou consommé avant toute suppression/quarantaine, puis identifier les idées réellement uniques à migrer vers les réglages documentaires actuels.

## Faits statiques déjà vérifiés

### UI / routage
- `frontend/src/App.tsx` ne déclare aucune route `TemplateBuilder` et n'importe aucun composant de ce nom.
- l'arborescence frontend courante ne contient pas de fichier nommé `TemplateBuilder` dans les résultats inspectés.
- les recherches indexées `TemplateBuilder` et `designConfig` n'ont retourné aucun composant UI actuel ; le grep repository du workflow reste la preuve exhaustive attendue avant suppression.

### Infrastructure templates encore réelle
Ne pas confondre l'ancienne UI Builder avec le système de templates :
- `frontend/src/services/templateApi.ts` expose encore un client CRUD de templates (`getById`, `create`, `update`, `delete`, `setDefault`, `preview`) ;
- `frontend/src/types/template.ts` conserve `DocumentTemplate`, `DesignConfig`, `body_html` et les contrats associés ;
- `backend/routers/templates.py` expose encore le CRUD `DocumentTemplate` ;
- `backend/main.py` monte réellement ce router sous `/api/templates`.

Donc le pré-verdict n'est **pas** « supprimer tout le système templates ».

## Pré-verdict
- **TemplateBuilder UI legacy** : probablement orphelin / non routé, à confirmer par le grep exhaustif exact-HEAD.
- **Infrastructure DocumentTemplate / templateApi / routes backend** : encore présente et potentiellement utile ; ne pas supprimer avec l'UI legacy sans audit de consommateurs et données persistées.
- **Capacités legacy potentiellement uniques à évaluer** : `body_html`, `design_config` structuré, templates personnalisés par utilisateur/cabinet, notion de template par défaut et preview dédiée.
- R3/R4 couvrent déjà palette, typographie, 5 modèles PDF, marges, header/footer, logo, letterhead et QR. Toute capacité legacy qui duplique ces réglages ne mérite pas une seconde UI.

## Succès
1. inventaire des fichiers dont le nom ou le contenu référence `TemplateBuilder`, `designConfig`, template builder / builder de modèle ;
2. graphe minimal des imports/exports et routes ;
3. preuve de reachability depuis `App.tsx`, routeurs frontend, Settings ou Document Studio ;
4. inventaire des capacités uniques encore absentes de R3/R4 ;
5. verdict : GARDER / EXTRAIRE PUIS SUPPRIMER / QUARANTAINER ;
6. aucune suppression avant preuve.

## Preuve finale attendue
Workflow grep repository complet, artefact de références exactes au HEAD. Le pré-verdict ci-dessus ne devient décision de suppression qu'après cette preuve.

Hors scope : modification du Document Studio clinique, suppression de fichier, Vercel.