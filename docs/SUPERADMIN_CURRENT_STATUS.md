# Digital Crown — Superadmin — État canonique

Dernière mise à jour : 2026-08-31
Repo : `hraaaaf/Digital_crown`
Branche : `security/sec1-signed-licenses`
PR : #288 — SEC-1 — draft
Candidat code certifié avant closeout documentaire : `7b0fd65cb9bc72dc39015a96b8552a207ae54510`
Base `master` intégrée : `ead11a0e38bdefd5b3e46126ce3500e07cf14ed3`
Statut : EN COURS — code/CI/UI/package certifiés sur le candidat ; 3 gates production mutantes restent à exécuter et prouver avant merge.

## Goal

Obtenir un Superadmin Digital Crown cloisonné du cabinet, least-privilege, protégé par authentification forte, auditable, fondé sur des licences Ed25519 signées et incapable de dériver son autorité d'un email, d'un rôle cabinet ou d'une session mobile.

## Succès

Le chantier n'est clos que si :

1. identité Superadmin immuable et fail-closed ;
2. control-plane impossible à activer dans un runtime cabinet ;
3. session mobile/cabinet incapable de devenir session plateforme ;
4. permissions plateforme explicites et fermées ;
5. mutations critiques protégées par WebAuthn récent ;
6. preuve step-up non exposée au frontend ;
7. mutations attribuables/auditées ;
8. entitlements signés appliqués au runtime ;
9. réémissions préservent les claims non modifiés ;
10. topologie production/HTTPS fail-closed ;
11. CI et package verts sur le HEAD final ;
12. `SUPERADMIN_USER_ID`, OWNER et migration legacy réellement exécutés et prouvés ;
13. UI défensive certifiée BEFORE/AFTER.

## Implémentation vérifiée

### Autorité et licences

- Ed25519 signé pour TRIAL / PAID / OWNER ; vérification fail-closed.
- TRIAL/PAID exigent un `max_devices >= 1` signé.
- `release_channel` limité à `stable|beta`.
- `SUPERADMIN_USER_ID` est l'identité immuable serveur ; l'autorité historique par email est neutralisée.
- `PLATFORM_CONTROL_PLANE_ENABLED` est OFF par défaut et interdit en environnement cabinet.
- réémissions licence préservent capacité, feature set et release channel selon l'opération.

### Frontière web/mobile

- JWT mobile refusé comme session primaire `/api/superadmin/*`, même s'il résout vers l'owner.
- aucun rôle cabinet ne confère une autorité plateforme.
- bridge mobile Superadmin supprimé ; vue mobile Superadmin redirect-only.

### WebAuthn / CSRF

- passkey plateforme dédiée, `user_verification=required`.
- challenge one-shot à TTL court.
- step-up serveur lié à l'identité web, TTL 5 minutes.
- cookie `platform_step_up` HttpOnly, Secure, SameSite=Strict, path `/api/superadmin`.
- mutations Superadmin exigent step-up récent.
- mutation cookie-only : Origin HTTPS allow-listée obligatoire.
- frontend ne conserve aucune preuve sensible de step-up.

### RBAC / audit / devices

- matrice plateforme fermée documentée dans `docs/SUPERADMIN_RBAC_MATRIX.md`.
- opérateurs plateforme, permissions, enable/disable, anti-escalation et owner immuable câblés.
- audit privilégié transactionnel avec acteur/action/cible.
- devices : capacité signée, liste minimisée, révocation ciblée, slot libéré après révocation, access/refresh révoqués immédiatement.
- données sensibles de pairing non exposées dans les réponses/audits métier.

### Topologie control-plane

Quand `PLATFORM_CONTROL_PLANE_ENABLED=true` :

- `ENVIRONMENT=production` obligatoire ;
- `APP_PUBLIC_URL` HTTPS obligatoire ;
- `FRONTEND_URL` HTTPS obligatoire ;
- `ALLOWED_ORIGINS` uniquement HTTPS ;
- environnement inconnu ou cabinet : refus fail-closed.

## Correctif final M6B

Le candidat `7b0fd65c...` inclut le correctif de fixture M6B : la happy-path fixture fournit désormais le même contrat async d'entitlement PAID signé que M6A. Aucun assouplissement de l'enforcement licence production n'a été introduit.

Le candidat intègre aussi `master` `ead11a0e...` (`pywebpush` runtime dependency + test de régression).

## UI / UX certifiée

Baseline BEFORE immuable :

- run `33377233900`
- baseline `31a02d17616b31b736fa25343b26deefd4335f5f`

Control Center AFTER :

- run historique de référence `33395381972`
- rerun sur candidat `7b0fd65c...` : check `Superadmin AFTER 390/430/768/1280` SUCCESS
- viewports : 390x844, 430x932, 768x1024, 1280x800
- APIs attendues : 200
- aucun chemin manquant, aucune page error, aucun overflow horizontal
- surface câblée : clients/licences, devices, quotas, stable/beta, opérateurs/RBAC, audit, passkey plateforme
- score visuel inspecté : 8.6/10
- dette restante : densité verticale mobile de la matrice permissions ; pas un défaut d'autorisation.

## CI / package du candidat `7b0fd65c...`

État GitHub attaché au commit :

- 28 checks terminés ;
- 27 `success` ;
- 1 `skipped` attendu : `M6-I exact BEFORE / AFTER`.

Le skip M6-I n'est pas un gate SEC-1 : `.github/workflows/mobile-m6-i-cert.yml` limite explicitement ce job aux branches `mobile/m6-i-*`.

Preuves importantes `success` sur `7b0fd65c...` :

- `Tests & durcissement` ;
- `Frontend (tests & build)` ;
- `Garde production (négatif)` ;
- `Superadmin AFTER 390/430/768/1280` ;
- `Real Windows package + tamper rejection` ;
- `Native runtime + fail-closed` macOS et Windows ;
- `Runtime contract` Ubuntu, macOS et Windows ;
- gates Marketplace / Patient / T2 / bridges M4 déclenchés sur ce HEAD.

Aucun failure/cancelled/timed_out/action_required n'est présent sur la vague du candidat.

Important : le présent commit documentaire crée un nouveau HEAD. Sa CI doit être revalidée avant toute promotion/merge ; les succès ci-dessus certifient le candidat code `7b0fd65c...`, pas encore le HEAD documentaire résultant.

## Production signing déjà prouvé

- bootstrap : run `33266592807` SUCCESS ;
- validation indépendante identité : run `33267814429` SUCCESS ;
- production kid : `dc-prod-1dc019b73b23c7d3` ;
- public trust key : `pTsKHE_SrROLwY4tQ3QFaNmKceTqCEbLfRhMI7BMC18` ;
- clé privée control-plane provisionnée hors repo/client.

## Gates production encore ouverts — HUMAN GATE

Trois mutations réelles restent non prouvées :

1. `SUPERADMIN_USER_ID` provisionné vers l'owner immuable dans le vrai control plane ;
2. entitlement OWNER émis puis vérifié dans le vrai control plane ;
3. licences legacy existantes migrées/remplacées.

Les CLIs de provisioning/migration sont dry-run par défaut et nécessitent explicitement `--apply` pour modifier l'état réel. Aucun `--apply` production ne doit être exécuté sans validation humaine explicite.

## Merge

PR #288 reste draft. Ne pas merger tant que :

- le HEAD documentaire final n'a pas sa CI requise verte ;
- les trois gates production ci-dessus ne sont pas exécutés et prouvés.

Aucun déploiement Vercel n'est requis ni autorisé pour ce closeout.

## Next exact

1. revalider la vague CI créée par ce closeout documentaire ;
2. si verte, mettre la PR #288 à jour avec le HEAD documentaire final et les preuves ;
3. stopper au HUMAN GATE des trois mutations production tant qu'aucune autorisation explicite `--apply` n'est donnée ;
4. après preuve des trois gates : draft → ready, drift master, merge, puis post-merge.

## Avancement

Non chiffré : aucune pondération canonique SEC-1 n'est définie. Le code, la CI candidate, l'UI défensive et le package Windows sont certifiés ; le chantier reste ouvert à cause des trois gates production mutantes et de la CI du nouveau HEAD documentaire.
