# Digital Crown — Superadmin — État canonique

Dernière mise à jour : 2026-08-30
Repo : `hraaaaf/Digital_crown`
Branche : `security/sec1-signed-licenses`
PR : #288 — SEC-1 — draft
HEAD documentaire : sera remplacé par le commit de cette mise à jour
Statut : EN COURS — code control-plane fortement durci ; CI finale et gates production encore à prouver

## Goal

Obtenir un Superadmin Digital Crown réellement cloisonné du cabinet, least-privilege, protégé par authentification forte, auditable, et incapable de dériver son autorité d'un email, d'un rôle cabinet ou d'une session mobile.

## Succès

Le chantier n'est clos que si :

1. identité Superadmin immuable et fail-closed ;
2. control-plane impossible à activer dans un runtime cabinet ;
3. session mobile/cabinet incapable de devenir session plateforme ;
4. permissions plateforme explicites et fermées ;
5. mutations critiques protégées par WebAuthn récent ;
6. preuve step-up transportée sans exposition frontend ;
7. mutations attribuables/auditées ;
8. entitlements signés réellement appliqués au runtime ;
9. réémissions de licence préservent les claims non modifiés ;
10. topologie control-plane production/HTTPS fail-closed ;
11. tests ciblés + CI verte sur le HEAD final ;
12. gates production (`SUPERADMIN_USER_ID`, OWNER, migration legacy) réellement exécutés et prouvés ;
13. toute modification UI suit le protocole BEFORE/AFTER obligatoire.

## État vérifié dans le code

### Autorité plateforme

- `SUPERADMIN_USER_ID` est l'identité immuable serveur ; `0` fail-closed.
- `SUPERADMIN_EMAIL` est neutralisé comme source d'autorité.
- `PLATFORM_CONTROL_PLANE_ENABLED` est OFF par défaut.
- un rôle cabinet `ADMIN`/`DENTISTE` n'accorde aucun droit plateforme par lui-même.
- permissions connues uniquement : `license.read`, `license.create_trial`, `license.create_paid`, `license.extend`, `license.suspend`, `license.revoke`, `license.manage_devices`, `license.change_release_channel`, `admin.read`, `admin.create`, `admin.update_permissions`, `admin.disable`, `audit.read`.
- permission inconnue : refus fail-closed.

Matrice détaillée : `docs/SUPERADMIN_RBAC_MATRIX.md`.

### Frontière web/mobile

- `/api/superadmin/*` refuse un JWT mobile comme autorité primaire, même s'il résout vers l'id owner.
- le bridge mobile backend ne propose plus Superadmin.
- `MobileSuperAdminView` est un redirect-only vers `/mobile/dashboard`.
- aucune passkey mobile n'est acceptée comme session primaire plateforme.

### Step-up WebAuthn plateforme

- credential/challenge dédiés au control-plane dans `backend/models_platform_passkey.py`.
- WebAuthn exige `user_verification=required`.
- challenge one-shot avec TTL court.
- preuve serveur dédiée `type=platform_step_up`, liée à l'id web, TTL 5 minutes.
- cookie `platform_step_up` : HttpOnly, **Secure systématique**, SameSite=Strict, path `/api/superadmin`.
- le flag Secure ne dépend plus de `request.url.scheme`, donc reste correct derrière terminaison TLS/reverse proxy.
- POST/PUT/PATCH/DELETE sous `/api/superadmin` exigent une preuve récente.
- mutation cookie-only : Origin HTTPS exacte de l'allow-list obligatoire ; absence/HTTP/origine inconnue refusées.
- Bearer explicite reste autorisé pour les clients non-CSRF.
- frontend : aucune preuve step-up persistée ; seulement une échéance non sensible en mémoire.
- avant de réutiliser cette échéance, le frontend consulte `/passkey/status.step_up_valid` ; le backend revalide réellement le cookie.

Tests dédiés :

- `backend/tests/test_superadmin_session_boundary.py`
- `backend/tests/test_superadmin_platform_passkey.py`

### Audit trail

Mutations actuellement auditées dans la même transaction DB locale :

- validation client ;
- création/révocation Trial ;
- grant/revoke licence ;
- archive/unarchive ;
- suspend/unsuspend ;
- changement de plan ;
- notes ;
- relance ;
- passkey plateforme ;
- opérateurs plateforme ;
- révocation appareil ;
- release channel.

Révocation device : cible d'audit exacte `resource_type=MobilePairedDevice`, `resource_id=device_id`; le client est contexte, pas cible substituée.

Données sensibles minimisées : code Trial, note interne, clé publique device et refresh JTI ne sont pas copiés dans les réponses/audits métier.

Dette d'observabilité restante : `AuditLog` n'a pas encore de `request_id`/résultat structuré. L'attribution acteur/action/cible existe néanmoins.

### `max_devices` réellement appliqué

Le défaut historique est corrigé :

- `LicenseService._verified_result()` conserve `max_devices` ;
- TRIAL/PAID signés exigent cryptographiquement `max_devices >= 1` ;
- `/api/mobile/claim-token` lit l'entitlement signé effectif ;
- appairage refusé si capacité atteinte ;
- appareil révoqué libère un slot ;
- entitlement absent/incomplet : fail-closed ;
- SQLite : `BEGIN IMMEDIATE` sérialise le comptage + insertion + consommation du token ;
- DB serveur : verrou tenant `FOR UPDATE`.

Preuve ciblée : `backend/tests/test_mobile_device_entitlement.py`.

### Device management plateforme

Permission `license.manage_devices` câblée :

- liste des devices et capacité signée ;
- réponse sans `client_public_key_hex` ni `refresh_jti` ;
- révocation ciblée ;
- révocation immédiatement honorée par les décodeurs access/refresh mobile ;
- audit CRITICAL.

Preuve ciblée : `backend/tests/test_superadmin_device_controls.py`.

### Release channel / invariance licence

Permission `license.change_release_channel` câblée pour `stable|beta`.

Réémissions :

- extension/révocation préservent capacité, canal et feature set ;
- changement de plan préserve capacité et canal ;
- changement de canal préserve type, expiration, capacité et feature set ;
- OWNER ne passe pas par les flows client.

`verify_license()` impose déjà les invariants de claims sur toute licence active réellement acceptée.

Preuve ciblée : `backend/tests/test_superadmin_license_claim_preservation.py`.

### Opérateurs plateforme / audit viewer

Câblés avec RBAC explicite :

- lecture opérateurs ;
- promotion d'un compte plateforme-only existant ;
- modification permissions ;
- enable/disable ;
- blocage owner immuable ;
- blocage comptes liés à un cabinet ;
- anti-escalation : un opérateur ne délègue pas une permission qu'il ne possède pas ;
- viewer audit filtré sur `SUPERADMIN_%`, pagination bornée.

Preuve ciblée : `backend/tests/test_superadmin_rbac.py`.

### Topologie control-plane

Quand `PLATFORM_CONTROL_PLANE_ENABLED=true` :

- `ENVIRONMENT=production` obligatoire ;
- `APP_PUBLIC_URL` HTTPS obligatoire ;
- `FRONTEND_URL` HTTPS obligatoire ;
- `ALLOWED_ORIGINS` uniquement HTTPS ;
- `ENVIRONMENT=cabinet` + control-plane reste interdit ;
- environnement inconnu/typo refusé par allow-list.

Preuve ciblée : `backend/tests/test_superadmin_control_plane_topology.py`.

## Surface owner-only actuelle

Restent volontairement réservés à l'identité immuable owner :

- validation initiale client ;
- archive/unarchive ;
- changement de pack ;
- notes internes ;
- relance.

Ils restent protégés par step-up sur mutation.

## UI / UX

Aucune nouvelle surface visuelle n'a été ajoutée dans ce lot, donc aucun faux score visuel n'est déclaré.

Vérifié :

- dashboard actuel expose clients/Trial/licences/pack/archive/suspension/notes/historique/relance ;
- opérateurs, viewer audit, devices et release channel sont backend-only pour l'instant ;
- `/super-admin` est dans le routeur frontend authentifié sans garde UI `is_superadmin`. Le backend refuse néanmoins données/actions non autorisées.

Cette dernière exposition de shell est une dette UX/defense-in-depth, **pas une élévation de privilège**. Sa correction est un changement de flow visuel et devra respecter BEFORE → Goal → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

## Tests / CI

Tests ciblés présents :

- `test_platform_access.py`
- `test_superadmin_session_boundary.py`
- `test_superadmin_platform_passkey.py`
- `test_superadmin_audit_trail.py`
- `test_superadmin_rbac.py`
- `test_superadmin_device_controls.py`
- `test_mobile_device_entitlement.py`
- `test_superadmin_license_claim_preservation.py`
- `test_superadmin_control_plane_topology.py`

**CI finale du HEAD documentaire actuel : à revalider.** Ne pas réutiliser les anciens verts comme preuve du HEAD final.

## Gates production encore ouverts

Selon la PR #288, restent non prouvés sur la production :

1. `SUPERADMIN_USER_ID` provisionné vers le compte owner immuable ;
2. entitlement OWNER émis puis vérifié ;
3. licences legacy existantes migrées/remplacées.

La clé privée de signature control-plane et son identité Ed25519 ont déjà une preuve historique séparée dans la PR ; cela ne ferme pas les trois gates ci-dessus.

## Séquence restante

1. laisser la CI du HEAD final s'exécuter sans attente passive ;
2. diagnostiquer/corriger tout rouge ;
3. si vert, mettre la PR #288 à jour avec le HEAD/preuves réels ;
4. effectuer le lot UI Superadmin séparé seulement avec baseline visuelle disponible ;
5. exécuter les trois gates production ci-dessus ;
6. seulement ensuite décider draft → ready/merge.

## Next exact

Revalider la CI du HEAD final après ces commits documentaires. Si rouge : diagnostiquer et corriger. Si vert : mettre à jour la PR puis s'arrêter uniquement sur les gates production/UI qui nécessitent un environnement/provisionnement réel.

## Avancement

Non chiffré : aucune pondération canonique n'a été définie. Le backend sécurité/fonctionnalités est largement couvert, mais CI finale, UI spécifique et provisioning production ne sont pas encore certifiés.
