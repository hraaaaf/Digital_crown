# R11 v2 — TemplateBuilder reachability & legacy cleanup

## Goal
Établir la reachability repo-wide réelle du domaine TemplateBuilder avant toute suppression, puis ne retirer que le code prouvé orphelin sans casser le domaine `DocumentTemplate`, le seed startup, le router `/api/templates` ni la génération PDF active.

## Succès
1. Inventaire exhaustif des références à `TemplateBuilder`, `templateApi`, `TemplateEngine`, `_get_default_template`, `/settings/templates` et `DocumentTemplate` sur le checkout réel.
2. Classification explicite : runtime actif / startup-DB / legacy orphelin / tests-docs.
3. Aucune suppression de modèle, table, seed ou router sans preuve d'absence de dépendance runtime.
4. Si le builder frontend est confirmé orphelin, nettoyage minimal uniquement.
5. Build/tests proportionnés après modification produit.
6. Aucun changement visuel actif attendu : le builder n'est actuellement pas routé dans `App.tsx`; si cette hypothèse est invalidée par l'audit, le lot repasse sous protocole UI BEFORE/mockup/AFTER.

## État déjà vérifié au master de départ
- `frontend/src/features/admin/TemplateBuilder.tsx` existe.
- `App.tsx` expose `/settings` mais aucune route `/settings/templates` ni import du builder dans le fichier inspecté.
- `TemplateBuilder` appelle `templateApi.update()` et `templateApi.preview()`.
- `frontend/src/services/templateApi.ts` implémente ces appels vers `PUT /templates/{id}` et `POST /templates/{id}/preview`.
- `backend/routers/templates.py` monté sous `/api/templates` ne présentait pas ces deux endpoints lors de l'audit manuel précédent.
- `backend/main.py` monte réellement le router templates et exécute `run_full_seed()` au startup.
- `DocumentTemplate` est un modèle SQLAlchemy réel et relationnel.
- `DocumentFactory` instancie `TemplateEngine`, mais ses méthodes publiques inspectées délèguent directement aux générateurs ReportLab.

## Hors scope de la phase d'audit
- suppression DB/migration destructive ;
- suppression du seed templates ;
- suppression du router `/api/templates` ;
- redesign UI ;
- Vercel.
