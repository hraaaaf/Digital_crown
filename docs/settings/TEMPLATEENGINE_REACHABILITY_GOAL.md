# TemplateEngine backend — Goal / Reachability

Date : 2026-08-22
Repo : `hraaaaf/Digital_crown`
Statut : PREPARED — NON CERTIFIÉ

## Goal

Retirer uniquement le moteur `TemplateEngine` réellement non reachable du produit, sans supprimer ni altérer les contrats actifs `DocumentTemplate`, `/api/templates`, seeds ou générateurs PDF ReportLab.

## Succès

1. `backend/services/template_engine.py` n’existe plus.
2. `backend/tests/test_template_engine.py`, qui ne testait que ce module isolé, n’existe plus.
3. `DocumentFactory` ne référence plus `TemplateEngine`, `template_engine` ni `_get_default_template`.
4. Les routes réelles de génération continuent d’utiliser `DocumentFactory` et ses générateurs dédiés.
5. `DocumentTemplate` reste dans le modèle, le seed et le router `/api/templates`.
6. Le router templates reste monté dans `backend/main.py`.
7. La suite backend complète, les tests frontend/build et les gates downstream restent verts au HEAD exact.
8. Aucun changement UI et aucun déploiement Vercel.

## Preuve d’audit avant modification

Artifact R11 Dependency Audit du HEAD produit `453b5213f728b87bb64303cb0f06417b2b3d6fe2` :
- `TemplateEngine` hors de son propre module : uniquement import + instanciation dans `backend/services/document_factory.py` ;
- `_get_default_template` : définition seule dans `DocumentFactory`, aucun appel ;
- `/api/documents/generate` passe par les méthodes ReportLab dédiées de `DocumentFactory` ;
- `/api/templates` reste un CRUD `DocumentTemplate` actif ;
- `backend/tests/test_template_engine.py` importe seulement `SecureTemplateRenderer` et le `CSSGenerator` local du module mort ;
- le `CSSGenerator` autonome `backend/services/css_generator.py` est un autre module et reste hors scope.

## Hors scope / conservé

- `backend/models.py::DocumentTemplate` ;
- `backend/routers/templates.py` ;
- `backend/seed_templates.py` ;
- schémas/types `DocumentTemplate` ;
- `backend/services/css_generator.py` ;
- tous les générateurs ReportLab actifs ;
- toute UI Réglages existante.

## Certification requise

- garde repo-wide : aucune référence résiduelle à `TemplateEngine`, `SecureTemplateRenderer`, `backend.services.template_engine` ou `_get_default_template` dans `backend/` ;
- garde positive : `DocumentTemplate`, seed, router et montage `/api/templates` préservés ;
- `py_compile` des entrypoints documents/templates ;
- CI globale exact-HEAD verte ;
- gates downstream déclenchés par la PR verts ;
- closeout canonique puis merge/post-merge.

Aucun Vercel.
