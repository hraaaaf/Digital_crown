# R11 — TemplateBuilder legacy cleanup

## Goal
Retirer l'interface `TemplateBuilder` non atteignable et son client API frontend fantôme, sans modifier les templates backend réellement persistés ni le moteur documentaire actif.

## Faits vérifiés sur master `b0c6830ac3dc33411d25c4c821a2ed942c5670b7`
- `TemplateBuilder.tsx` n'est exposé ni par `App.tsx`, ni par `Sidebar.tsx`, ni par le conteneur Réglages inspecté.
- Le builder dépend de contrats frontend absents du backend réel : `GET /clinics/{id}/templates`, `PUT /templates/{id}`, `POST /templates/{id}/preview`.
- `backend/routers/templates.py` est monté sous `/api/templates` et expose list/get/create/set-default/delete.
- `DocumentTemplate` reste un modèle persistant réel.
- `seed_system_templates(db)` est exécuté via `run_full_seed(db)` au démarrage.
- La génération documentaire active inspectée passe par `DocumentFactory`/ReportLab et `CabinetConfig`.

## Périmètre
### Retirer
- `frontend/src/features/admin/TemplateBuilder.tsx`.
- Les imports/types et l'objet `templateApi` devenus sans consommateur dans `frontend/src/services/templateApi.ts`.

### Préserver
- `cabinetApi` et ses contrats actifs.
- `backend/routers/templates.py`.
- `DocumentTemplate`, la table et les seeds.
- `backend/services/template_engine.py` dans ce lot : son orphelinage paraît probable, mais il n'est pas supprimé sans preuve plus forte.
- Tout rendu documentaire actif.

## Succès observable
1. Le frontend compile après suppression : aucune référence résiduelle au builder ou à `templateApi` ne casse TypeScript/build.
2. Aucun fichier backend, modèle, seed ou migration DB n'est modifié.
3. `cabinetApi` reste inchangé fonctionnellement.
4. Les tests/CI proportionnés au lot sont verts au HEAD exact.
5. Aucun changement visuel d'une surface atteignable : pas de certification UI obligatoire pour ce dead-code cleanup.

## Preuve attendue
- diff exact master → HEAD limité au Goal, au builder supprimé et au nettoyage du service frontend ;
- frontend build/typecheck/tests verts ;
- CI/T2 pertinents verts au HEAD exact ;
- vérification finale qu'aucun backend/migration n'a changé.

## Non-goals
- supprimer l'API templates backend ;
- supprimer `DocumentTemplate` ou ses seeds ;
- modifier le rendu des ordonnances/documents ;
- migration DB ;
- redesign ou nouvelle feature ;
- déploiement Vercel.
