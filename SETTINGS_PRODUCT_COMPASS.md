# SETTINGS PRODUCT COMPASS — Réglages / Paramètres

Dernière mise à jour : 2026-08-22
Repo : `hraaaaf/Digital_crown`
Statut : **BOUSSOLE CANONIQUE ACTIVE**

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

**Avancement vérifié : 14/15 = 93,3 %.**

## Dernier lot fermé — Restauration guidée

PR #213 squash-mergée : `83d7dcda0e8e364f00fa7f2847bcbe65cf6dfe38`.

Résultat certifié :
- préflight sans mutation ;
- intégrité archive + schéma Digital Crown ;
- étape explicite « Préparer la restauration » ;
- secours DB vérifié avant bascule ;
- DB + WAL protégés ;
- médias protégés par empreinte et renommage atomique ;
- apply hors-processus ;
- redémarrage + smoke check ;
- rollback automatique DB + médias ;
- audit persistant ;
- jobs scopés au cabinet.

Preuves :
- HEAD produit certifié `453b5213f728b87bb64303cb0f06417b2b3d6fe2` ;
- BEFORE #22 `32529921293` — SUCCESS ;
- AFTER #3 `32559882456` — SUCCESS ;
- artifact `9472491713` — `sha256:adb6a3ef4b5ab0f8848dcbf7ba442f150b5a0160a64adadb0ef66066d77c2dc8` ;
- CI #1590 `32559882536`, Security #10, RBAC #146, T2 #789, Catalogue #62, P7 #88, R11 #8 — SUCCESS ;
- AFTER 5/5, 0 overflow, 0 page error, 0 HTTP 5xx, 0 request failure ;
- score visuel **9,4/10** ;
- closeout : `docs/settings/GUIDED_RESTORE_CLOSEOUT.md` ;
- post-merge : `docs/settings/GUIDED_RESTORE_POSTMERGE.md`.

Dette non bloquante : le format historique des médias reste un payload Fernet monolithique ; une évolution streaming/chunked serait préférable pour des archives gigantesques, sans remettre en cause la sûreté transactionnelle certifiée.

## Roadmap restante

Un seul axe reste non crédité :

1. **Dette backend TemplateEngine / reachability restante** — audit downstream exhaustif, preuve d’usage/référencement, décision GARDER / RÉDUIRE / SUPPRIMER uniquement sur preuve ; aucune suppression spéculative.

## HANDOVER COURANT

- Chantier : **Réglages — Product Review & Simplification**
- Dernier lot fermé : **Restauration guidée**
- PR : #213 — MERGED
- Merge : `83d7dcda0e8e364f00fa7f2847bcbe65cf6dfe38`
- HEAD produit certifié : `453b5213f728b87bb64303cb0f06417b2b3d6fe2`
- AFTER #3 : `32559882456` — SUCCESS
- CI #1590 : `32559882536` — SUCCESS
- Artifact AFTER : `9472491713`
- Score : **9,4/10**
- Avancement vérifié : **14/15 = 93,3 %**
- Next exact : **Dette backend TemplateEngine / reachability restante → audit code/routes/imports/usages/tests/docs, aucune modification produit avant cartographie downstream**
- Vercel : **aucun déploiement**
