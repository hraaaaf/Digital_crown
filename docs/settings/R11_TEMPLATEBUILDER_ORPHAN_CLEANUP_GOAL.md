# R11 — TemplateBuilder legacy : preuve d’orphelinat et nettoyage minimal

Date : 2026-08-20
Base auditée : `b0c6830ac3dc33411d25c4c821a2ed942c5670b7`
Scope : UI legacy `frontend/src/features/admin/TemplateBuilder.tsx` uniquement, sauf preuve contraire.

## Goal

Établir de façon reproductible si le `TemplateBuilder` frontend est encore atteignable ou importé. S’il est réellement orphelin, supprimer uniquement ce composant mort sans toucher au moteur/templates backend ni aux contrats encore consommés.

## Succès

1. grep repo-wide exact-HEAD : zéro référence `TemplateBuilder` hors du fichier legacy lui-même avant suppression ;
2. aucune route `App.tsx`, page Réglages, navigation Sidebar ou surface Document Hub ne pointe vers le builder ;
3. `templateApi.ts` n’est pas supprimé car `App.tsx` consomme `cabinetApi` pour l’initialisation ;
4. le router `/api/templates`, `DocumentTemplate`, `TemplateEngine` et `DocumentFactory` restent présents ;
5. si l’orphelinat est prouvé, suppression de `TemplateBuilder.tsx` seule ;
6. build/tests/CI proportionnés verts au HEAD produit ;
7. aucun changement UI observable, aucune donnée template supprimée, aucun Vercel.

## Preuve statique déjà vérifiée sur la base

- `frontend/src/main.tsx` monte uniquement `App` ;
- `frontend/src/App.tsx` ne route/import pas `TemplateBuilder` ;
- `frontend/src/pages/Settings.tsx` monte le centre Réglages actuel ;
- `SettingsContainer.tsx` ne contient aucun onglet TemplateBuilder ;
- `Sidebar.tsx` ne contient aucun lien vers le builder ;
- `DocumentHub.tsx` utilise le Document Studio actuel, sans import du builder legacy ;
- `TemplateBuilder.tsx` existe encore mais dépend de `templateApi` et attend un `templateId` de route ;
- `App.tsx` importe `cabinetApi` depuis `templateApi.ts` : le fichier de service ne peut pas être supprimé en bloc ;
- `backend/main.py` monte `templates.router` sous `/api/templates` ;
- `backend/models.py` contient `DocumentTemplate` ;
- `DocumentFactory` instancie `TemplateEngine` et le router documents instancie `DocumentFactory`.

## Décision conditionnelle

- **Si le workflow repo-wide trouve une référence externe** : aucune suppression ; analyser cette dépendance.
- **Si zéro référence externe est prouvée** : supprimer uniquement `frontend/src/features/admin/TemplateBuilder.tsx`.

## UI / UX

Aucune capture BEFORE/AFTER n’est requise si l’orphelinat est prouvé, car le composant n’est pas atteignable dans le produit. Si une route ou un import runtime est découvert, R11 bascule immédiatement en chantier UI avec protocole visuel complet avant modification.

## Hors scope

- suppression ou migration de données `document_templates` ;
- modification du router `/api/templates` ;
- modification de `TemplateEngine` / `DocumentFactory` ;
- refonte Document Studio ;
- Vercel.
