# SETTINGS PRODUCT COMPASS — Réglages / Paramètres

Dernière mise à jour : 2026-08-22
Repo : `hraaaaf/Digital_crown`
Statut : **ROADMAP CANONIQUE FERMÉE — 15/15 CERTIFIÉS**

> Source de reprise prioritaire du chantier Réglages / Paramètres.
> Aucun déploiement Vercel sans autorisation explicite.

## Goal

Juger et améliorer chaque feature de Réglages comme un produit réel de cabinet dentaire : valeur métier, UX, robustesse, vérité backend, dette, doublons, promesses trompeuses et complexité inutile.

Décisions : **GARDER / AMÉLIORER / REFONDRE / DÉPLACER / SUPPRIMER / À PROUVER**.

## Doctrine

Pour chaque lot significatif : audit downstream → BEFORE si UI → Goal + critères → mockup/référence → implémentation → tests → AFTER mêmes viewports + score → docs canoniques → merge/post-merge.

Une preuve CI sur un parent n’est réutilisable que si le delta suivant est prouvé équivalent produit. Vercel reste interdit sans autorisation explicite.

## Lots certifiés

| Lot | Décision | Statut | Score visuel |
|---|---|---|---:|
| R1 Shell / doctrine de sauvegarde | GARDER / UNIFIER | CLOSED — MERGED (#194) | 9,5/10 |
| R2 Profil Cabinet | GARDER / SIMPLIFIER | CLOSED — MERGED (#171) | 9,6/10 |
| R3 Design & Ambiance | GARDER / CLARIFIER | CLOSED — MERGED (#173) | 9,7/10 |
| R4 Modèles documentaires | PDF réel = vérité | CLOSED — MERGED (#174) — recovery #193 | 9,2/10 |
| R5 QR documentaire | GARDER / RENDRE EXPLICITE ET TESTABLE | CLOSED — MERGED (#192) | 9,4/10 |
| R6 Catalogue Actes | GARDER architecture / REFONDRE CRUD | CLOSED — MERGED (#177) — recovery #193 | 9,6/10 |
| R7 Horaires & Agenda | GARDER / RENDRE RÉEL | CLOSED — MERGED (#178) | 9,3/10 |
| R8 Performance & Assistance | GARDER / CLARIFIER / DÉPLACER | CLOSED — MERGED (#183) | 9,5/10 |
| R9-A Journal d’Audit | GARDER / HUMANISER | CLOSED — MERGED (#185) | 9,6/10 |
| R10-A Mon Équipe / mot de passe | GARDER / ALIGNER VÉRITÉ BACKEND | CLOSED — MERGED (#188) | 9,4/10 |
| R11 TemplateBuilder legacy frontend | SUPPRIMER FRONTEND ORPHELIN / CONSERVER BACKEND | CLOSED — MERGED (#191) | n/a |
| Catalogue avancé / Catalogue connecté | GARDER / CONNECTER / FIGER HISTORIQUE | CLOSED — MERGED (#195) | 9,5/10 |
| Indicateurs patient explicables | SUPPRIMER JUGEMENTS / GARDER REPÈRES FACTUELS | CLOSED — MERGED (#199) | 9,3/10 |
| Restauration guidée | GARDER / SÉCURISER / RENDRE RÉVERSIBLE | CLOSED — CERTIFIÉE — MERGED (#213) | 9,4/10 |
| TemplateEngine backend / reachability | SUPPRIMER MOTEUR ORPHELIN / CONSERVER CONTRATS ACTIFS | CLOSED — CERTIFIÉ — MERGED (#215) | n/a |

**Avancement vérifié : 15/15 = 100 %.**

## Dernier lot fermé — TemplateEngine backend / reachability

PR #215 squash-mergée : `8120f8617bca29d7911ad2cb5fb42f58451eb89a`.

Résultat certifié :
- `backend/services/template_engine.py` supprimé après preuve de non-reachability produit ;
- import / instanciation `TemplateEngine` et `_get_default_template()` retirés de `DocumentFactory` ;
- tests batch dépendant encore du module mort nettoyés ;
- `DocumentTemplate` modèle/table conservé ;
- `/api/templates` conservé et monté ;
- seed `DocumentTemplate` conservé ;
- générateurs PDF ReportLab actifs conservés ;
- `backend/services/css_generator.py` autonome conservé ;
- aucune modification UI.

Preuves :
- HEAD produit certifié `4846fd212ab991d3902bfc0e5f1fd939b47af59a` ;
- TemplateEngine Reachability #2 `32561612304` — SUCCESS ;
- artifact `9472936525` — `sha256:b573262196f860d8e99ea8a82aea2a417dd2d0ff91afe4844b9961ef06dfe02d` ;
- zéro référence `TemplateEngine`, `SecureTemplateRenderer`, `backend.services.template_engine` ou `_get_default_template` dans le garde repo-wide ;
- `DocumentTemplate` modèle/router/seed et montage `/api/templates` prouvés présents ;
- CI #1600 `32561612377` — SUCCESS ;
- T2 #797 `32561612293` — SUCCESS ;
- P7 #96 `32561612291` — SUCCESS ;
- Catalogue #70 `32561612292` — SUCCESS ;
- R11 Dependency #11 `32561612296` — SUCCESS ;
- R11 Reachability #14 `32561612340` — SUCCESS ;
- aucun review thread ouvert ;
- closeout : `docs/settings/TEMPLATEENGINE_REACHABILITY_CLOSEOUT.md` ;
- post-merge : `docs/settings/TEMPLATEENGINE_REACHABILITY_POSTMERGE.md`.

## Roadmap restante

**Aucun lot restant dans la roadmap canonique actuelle Réglages / Paramètres.**

Le score 15/15 signifie que les 15 lots définis ont été fermés avec leurs preuves requises. Il ne signifie pas qu’aucune dette future ou nouvelle amélioration ne pourra être identifiée dans Digital Crown.

## HANDOVER FINAL

- Chantier : **Réglages — Product Review & Simplification**
- Statut : **CLOSED — 15/15 CERTIFIÉS**
- Dernier lot : **TemplateEngine backend / reachability**
- PR : #215 — MERGED
- Merge : `8120f8617bca29d7911ad2cb5fb42f58451eb89a`
- HEAD produit certifié : `4846fd212ab991d3902bfc0e5f1fd939b47af59a`
- CI #1600 : `32561612377` — SUCCESS
- T2 #797 : `32561612293` — SUCCESS
- P7 #96 : `32561612291` — SUCCESS
- Catalogue #70 : `32561612292` — SUCCESS
- Artifact reachability : `9472936525`
- Closeout : `docs/settings/TEMPLATEENGINE_REACHABILITY_CLOSEOUT.md`
- Post-merge : `docs/settings/TEMPLATEENGINE_REACHABILITY_POSTMERGE.md`
- Avancement vérifié : **15/15 = 100 %**
- Next exact : **aucune action restante dans la roadmap canonique actuelle**
- Vercel : **aucun déploiement**
