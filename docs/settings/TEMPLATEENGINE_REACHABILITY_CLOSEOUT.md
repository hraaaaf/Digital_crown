# TemplateEngine backend — CLOSEOUT

Date : 2026-08-22
Repo : `hraaaaf/Digital_crown`
PR : #215

## Goal

Retirer uniquement le moteur backend `TemplateEngine` prouvé non reachable, sans supprimer ni altérer les contrats actifs `DocumentTemplate`, `/api/templates`, seeds ou générateurs PDF ReportLab.

## Résultat vérifié

- `backend/services/template_engine.py` supprimé ;
- `backend/tests/test_template_engine.py` supprimé ;
- import / instanciation `TemplateEngine` retirés de `DocumentFactory` ;
- `_get_default_template()` retiré car définition sans appel ;
- anciens tests batch qui exerçaient directement le module mort nettoyés ;
- monkeypatch Branding obsolète retiré ;
- `DocumentTemplate` modèle/table conservé ;
- `/api/templates` conservé et monté ;
- seed `DocumentTemplate` conservé ;
- `backend/services/css_generator.py` autonome conservé ;
- générateurs ReportLab actifs conservés ;
- aucune modification UI ;
- aucun déploiement Vercel.

## Historique de diagnostic

Premier HEAD produit : `d259c37f0400ae1db5d9286d66a4cd3c00c16235`.

Le premier garde repo-wide et CI #1595 ont échoué uniquement parce que plusieurs tests batch référençaient encore le module supprimé. CI #1595 avait déjà validé 1 838 tests avant le premier échec `ModuleNotFoundError` dans `test_services_unit13.py`.

Correctif consolidé final : `4846fd212ab991d3902bfc0e5f1fd939b47af59a`, parent exact `d259c37f...`, avec uniquement tests / garde / Goal et zéro nouveau changement runtime produit.

## Preuves exact-HEAD

HEAD final produit : `4846fd212ab991d3902bfc0e5f1fd939b47af59a`.

- Settings TemplateEngine Reachability Certification #2 — run `32561612304` — SUCCESS ;
- artifact `9472936525` — `sha256:b573262196f860d8e99ea8a82aea2a417dd2d0ff91afe4844b9961ef06dfe02d` ;
- preuve artifact : 0 référence `TemplateEngine`, 0 `SecureTemplateRenderer`, 0 `backend.services.template_engine`, 0 `_get_default_template` ;
- `DocumentTemplate` modèle/router/seed préservés ; router `/api/templates` monté ; 0 erreur ;
- CI #1600 — run `32561612377` — SUCCESS ;
- T2 Runtime Browser Certification #797 — run `32561612293` — SUCCESS ;
- Patient P7 Final Certification #96 — run `32561612291` — SUCCESS ;
- Catalog Connected Truth Certification #70 — run `32561612292` — SUCCESS ;
- Settings R11 TemplateBuilder Dependency Audit #11 — run `32561612296` — SUCCESS ;
- Settings R11 TemplateBuilder Reachability Audit #14 — run `32561612340` — SUCCESS ;
- aucun review thread ouvert sur PR #215 ;
- PR mergeable au HEAD certifié.

## Décision

**SUPPRIMER** le `TemplateEngine` backend orphelin, **CONSERVER** les contrats métier `DocumentTemplate`, `/api/templates`, seeds et la génération PDF ReportLab active.

Le Goal est atteint et prouvé. Le lot peut être mergé.
