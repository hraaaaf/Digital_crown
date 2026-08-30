# Digital Crown — Superadmin RBAC Matrix

Dernière mise à jour : 2026-08-30

Source d'autorité : `backend/platform_access.py`.

## Matrice permission → backend → preuve

| Permission | Surface backend actuelle | État code | Preuve ciblée | UI actuelle |
|---|---|---|---|---|
| `license.read` | GET `/clients`, GET `/trial-codes`, GET `/clients/{id}/license-history` | CÂBLÉ | `test_superadmin_rbac.py` | clients/Trial/historique présents |
| `license.create_trial` | POST `/trial-codes` | CÂBLÉ | RBAC + step-up + audit | présente |
| `license.create_paid` | POST `/clients/{id}/grant-license?action=1m|3m|6m|1y` si entitlement signé non-PAID | CÂBLÉ | `test_superadmin_rbac.py`, `test_superadmin_license_claim_preservation.py` | présente |
| `license.extend` | même endpoint si entitlement signé PAID actif | CÂBLÉ | sélection depuis vérité signée + préservation claims | présente |
| `license.suspend` | PATCH `/clients/{id}/suspend` | CÂBLÉ | positif/négatif RBAC + audit | présente |
| `license.revoke` | POST `/trial-codes/{id}/revoke`, `grant-license?action=revoke` | CÂBLÉ | permission avant mutation + OWNER refusé | présente |
| `license.manage_devices` | GET `/platform-admins/clients/{id}/devices`, POST `/platform-admins/clients/{id}/devices/{device_id}/revoke` | CÂBLÉ | `test_superadmin_device_controls.py` + `test_mobile_device_entitlement.py` | NON CÂBLÉE |
| `license.change_release_channel` | PATCH `/clients/{id}/release-channel?channel=stable|beta` | CÂBLÉ | `test_superadmin_license_claim_preservation.py` | NON CÂBLÉE |
| `admin.read` | GET `/platform-admins` | CÂBLÉ | `test_superadmin_rbac.py` | NON CÂBLÉE |
| `admin.create` | POST `/platform-admins/{user_id}` | CÂBLÉ | plateforme-only + anti-escalation | NON CÂBLÉE |
| `admin.update_permissions` | PATCH `/platform-admins/{user_id}/permissions` | CÂBLÉ | allow-list stricte + owner immuable + anti-escalation | NON CÂBLÉE |
| `admin.disable` | PATCH `/platform-admins/{user_id}/enabled` | CÂBLÉ | owner immuable + audit | NON CÂBLÉE |
| `audit.read` | GET `/audit?limit=&offset=` | CÂBLÉ | `test_superadmin_rbac.py`, filtre `SUPERADMIN_%` | NON CÂBLÉE |

## Opérations volontairement owner-only

Ces actions utilisent l'identité immuable `SUPERADMIN_USER_ID` plutôt qu'une permission délégable :

- POST `/clients/{id}/validate` ;
- PATCH `/clients/{id}/archive` ;
- PATCH `/clients/{id}/plan` ;
- PATCH `/clients/{id}/notes` ;
- POST `/clients/{id}/send-renewal-email`.

Elles restent soumises au step-up WebAuthn pour toute mutation.

## Invariants de sécurité

- L'identité `SUPERADMIN_USER_ID` conserve toutes les permissions de la liste fermée.
- Un opérateur plateforme non-owner doit avoir la permission exacte à `true` dans `User.permissions`.
- Les rôles cabinet `ADMIN`/`DENTISTE` n'accordent aucune permission plateforme par eux-mêmes.
- Un compte rattaché à un cabinet ne peut pas devenir opérateur plateforme.
- L'owner immuable ne peut pas être modifié/désactivé via les routes opérateurs.
- Un opérateur non-owner ne peut déléguer que des permissions qu'il possède déjà.
- Toute mutation `/api/superadmin/*` exige un step-up WebAuthn plateforme récent.
- Le step-up est un JWT séparé `type=platform_step_up`, lié à l'utilisateur web, TTL 5 minutes, cookie HttpOnly + Secure + SameSite=Strict + scope `/api/superadmin`.
- Une mutation Superadmin utilisant l'autorité ambiante des cookies exige une Origin HTTPS exacte de l'allow-list control-plane. Un Bearer explicite reste possible pour les clients non-CSRF.
- Le frontend ne stocke jamais la preuve step-up ; son timer mémoire est désormais recroisé avec `/passkey/status.step_up_valid` avant réutilisation.

## `max_devices` — runtime réellement appliqué

Le claim `max_devices` :

1. est obligatoire et validé cryptographiquement pour TRIAL/PAID ;
2. est conservé par `LicenseService._verified_result()` ;
3. est lu à l'appairage `/api/mobile/claim-token` ;
4. borne le nombre de `MobilePairedDevice` actifs ;
5. ignore correctement les appareils révoqués ;
6. est réservé transactionnellement avant création du device.

SQLite, runtime cabinet canonique, utilise `BEGIN IMMEDIATE` avant le comptage + insertion + consommation du token. Deux claims concurrents ne peuvent donc pas réserver le même dernier slot. Les bases serveur utilisent un verrou tenant `FOR UPDATE`.

Preuve ciblée : `backend/tests/test_mobile_device_entitlement.py`.

## Réémission de licence — invariants

Une réémission modifie uniquement le claim demandé :

- extension/révocation préservent `max_devices`, `release_channel`, `feature_set` ;
- changement de plan préserve `max_devices` et `release_channel` ;
- changement de release channel préserve capacité, feature set, type et expiration.

Pour une licence active réellement vérifiée, `verify_license()` exige déjà `max_devices >= 1` (hors OWNER) et `release_channel ∈ {stable,beta}` ; une preuve active corrompue est donc refusée avant ces flows.

Preuve ciblée : `backend/tests/test_superadmin_license_claim_preservation.py`.

## État UI

Le dashboard existant câble clients, Trial, grant/revoke, pack, archive, suspension, notes, historique et relance.

Restent backend-only à ce stade :

- opérateurs plateforme ;
- viewer audit ;
- gestion des appareils ;
- release channel.

Aucune modification visuelle de ces surfaces n'est appliquée sans le protocole UI obligatoire BEFORE → Goal → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

La route frontend `/super-admin` reste montée dans le routeur authentifié sans garde visuel `is_superadmin`; le backend refuse néanmoins toute donnée/action non autorisée. C'est une dette UX/defense-in-depth, pas une élévation d'autorité.

## Validation courante

Les tests ciblés sont présents dans le repo. La CI du HEAD documentaire final doit encore être revalidée avant de déclarer le lot code clos.
