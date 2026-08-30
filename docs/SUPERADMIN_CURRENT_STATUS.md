# Digital Crown — Superadmin — État canonique

Dernière mise à jour : 2026-08-30
Repo : `hraaaaf/Digital_crown`
Branche : `security/sec1-signed-licenses`
PR : #288 — SEC-1
HEAD vérifié avant cette mise à jour documentaire : `edd979614d29f1d05ba2843a02cc1ee562040540`
Statut : EN COURS — backend/frontière de sécurité fortement durcie, audit fonctionnel non clos

## Goal

Obtenir un Superadmin Digital Crown réellement sûr, cloisonné du cabinet, exploitable et auditable, avec une autorité plateforme impossible à obtenir par rôle/email local et des actions critiques protégées proportionnellement à leur risque.

## Succès

Le lot est clos uniquement si :

1. identité Superadmin immuable et fail-closed ;
2. control plane impossible à activer sur runtime cabinet ;
3. licence cabinet expirée/révoquée sans effet sur l'autorité plateforme légitime ;
4. session mobile/cabinet incapable de devenir session plateforme ;
5. permissions plateforme explicites et séparées du cabinet ;
6. mutations Superadmin protégées par step-up récent ;
7. mutations Superadmin attribuables et historisées ;
8. environnement sécurité fail-closed ;
9. surface fonctionnelle/RBAC cohérente avec les permissions déclarées ;
10. frontend Superadmin compatible avec le step-up sans stocker la preuve sensible ;
11. tests positifs/négatifs + CI verte ;
12. UI auditée séparément si modification visuelle.

## Preuves vérifiées

### Autorité plateforme

- `SUPERADMIN_USER_ID` est l'identité immuable serveur ; `0` fail-closed.
- `SUPERADMIN_EMAIL` est neutralisé et ne constitue plus une autorité.
- `PLATFORM_CONTROL_PLANE_ENABLED` est OFF par défaut.
- `ENVIRONMENT=cabinet` + control plane activé est rejeté.
- `is_platform_superadmin()` exige control plane actif + utilisateur actif/non archivé/non suspendu + id exact.
- permissions plateforme explicitement séparées des permissions cabinet.

### Frontière web/mobile

- `/api/superadmin/*` exige désormais une session web `access` pour l'autorité primaire.
- un JWT `mobile`, même associé au `SUPERADMIN_USER_ID`, est rejeté sur la surface Superadmin.
- destination Superadmin supprimée du bridge mobile backend.
- route frontend historique `/mobile/superadmin` ne mène plus à une console mobile privilégiée.
- le composant `MobileSuperAdminView` historique n'est plus une voie d'accès autorisée au control-plane.

### Step-up WebAuthn plateforme

- nouveau modèle dédié : `backend/models_platform_passkey.py`.
- nouveau routeur dédié : `backend/routers/superadmin_passkey.py`.
- passkey plateforme distincte de la passkey mobile et liée au SuperAdmin web.
- WebAuthn exige `user_verification=required` et l'origine stable HTTPS `https://digitalcrown.local:5173`.
- challenges one-shot avec TTL court.
- après vérification, backend émet une preuve JWT `type=platform_step_up`, TTL 5 minutes.
- preuve transportée en cookie HttpOnly dédié, scoped `/api/superadmin`, jamais utilisée comme Authorization primaire.
- le frontend ne persiste pas la preuve ; il ne conserve qu'une expiration non sensible en mémoire pour éviter de redemander WebAuthn à chaque clic pendant la fenêtre active.
- toutes les mutations POST/PUT/PATCH/DELETE `/api/superadmin/*` exigent ce step-up.

### Audit trail

Les mutations actuelles ajoutent des `AuditLog` transactionnels dans la même transaction DB que la mutation locale :

- validation client ;
- création/révocation Trial ;
- grant/revoke licence ;
- archive/unarchive ;
- suspend/unsuspend ;
- changement de plan ;
- mise à jour notes ;
- demande de relance ;
- enregistrement passkey plateforme.

Les événements enregistrent acteur, action, cible, sévérité et détails minimisés. Le contenu des notes internes et le code Trial ne sont pas copiés dans l'audit.

Limite actuelle du schéma : pas de `request_id`/`result` structurés dans `AuditLog`. Ce point reste une amélioration d'observabilité, pas une absence d'audit.

### Environnement

- `ENVIRONMENT` est désormais validé sur une allow-list explicite (`development`, `local`, `test`, `cabinet`, `production`) : une typo ne peut plus faire tomber silencieusement les invariants production.
- les invariants production/cabinet restent appliqués au démarrage.

### Tests / CI

Tests dédiés ajoutés/migrés :

- `backend/tests/test_superadmin_session_boundary.py`
- `backend/tests/test_superadmin_audit_trail.py`
- `backend/tests/test_superadmin_platform_passkey.py`
- test frontend du service passkey plateforme.

Preuve actuelle :
- HEAD code vérifié : `edd979614d29f1d05ba2843a02cc1ee562040540`
- CI #2225 — run `33309963668` : SUCCESS.
- SEC-1 Windows Package Certification #40 — run `33309963712` : SUCCESS.

## Corrections d'hypothèses anciennes

Les risques suivants étaient basés sur une surface plus ancienne et ne sont pas présents dans le routeur Superadmin actuel :

- suppression/purge cabinet directe : aucune route Superadmin actuelle vérifiée ;
- reset password Superadmin : aucune route actuelle vérifiée ;
- ancienne route `/stats` Superadmin : non présente dans le routeur actuel.

Ils ne doivent donc plus être traités comme défauts actifs sans nouvelle preuve.

## Gaps fonctionnels / RBAC encore ouverts

`PLATFORM_LICENSE_PERMISSIONS` déclare notamment :

- `license.create_paid`
- `license.extend`
- `license.suspend`
- `license.manage_devices`
- `license.change_release_channel`
- `admin.read`
- `admin.create`
- `admin.update_permissions`
- `admin.disable`
- `audit.read`

Le routeur Superadmin actuel expose principalement clients/licences/Trial/historique/notes et n'expose pas encore de surface vérifiée pour plusieurs permissions déclarées ci-dessus, notamment gestion d'administrateurs plateforme, viewer d'audit, gestion devices et release channel.

=> Risque principal restant : **écart entre RBAC déclaré et fonctionnalités réellement exposées/testées**.

## UX/UI

Aucune refonte visuelle Superadmin n'a été appliquée dans ce lot. Le wiring step-up utilise le prompt WebAuthn natif du navigateur ; il n'ajoute pas de nouvelle modal custom. Pas de claim de score visuel sans captures BEFORE/AFTER.

## Séquence restante

1. établir la matrice exacte `permission -> route -> test -> UI` ;
2. décider/implémenter les fonctionnalités plateforme manquantes réellement nécessaires : admins plateforme, audit viewer, device/release management ;
3. vérifier la protection d'accès frontend `/super-admin` côté routing pour éviter une simple exposition visuelle aux non-SuperAdmin ;
4. compléter les tests frontend ciblés sur retry step-up/403 ;
5. revalider CI sur HEAD final ;
6. mettre à jour ce canonique avec la matrice et les preuves finales ;
7. fermer seulement les gates réellement satisfaits.

## Next exact

Construire la matrice RBAC/fonctionnalités réelle du control-plane, puis implémenter le premier gap critique prouvé plutôt que d'ajouter des permissions fantômes.

## Avancement

Non chiffré. Le socle sécurité auth/mobile/step-up/audit est prouvé par CI, mais le périmètre fonctionnel Superadmin complet n'est pas encore certifié.
