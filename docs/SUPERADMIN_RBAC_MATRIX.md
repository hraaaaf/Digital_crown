# Digital Crown — Superadmin RBAC Matrix

Dernière mise à jour : 2026-09-01
Source d'autorité : `backend/platform_access.py`.
HEAD produit/certification de référence : `89d86dcce8bc572826f2e8bd34d08a950f56cd21`.

## Matrice permission → backend → preuve → UI

| Permission | Surface backend | État | Preuve ciblée | UI |
|---|---|---|---|---|
| `license.read` | GET `/clients`, `/trial-codes`, `/clients/{id}/license-history` | CÂBLÉ | `test_superadmin_rbac.py` | CÂBLÉE |
| `license.create_trial` | POST `/trial-codes` | CÂBLÉ | RBAC + step-up + audit | CÂBLÉE |
| `license.create_paid` | POST `/clients/{id}/grant-license?action=1m|3m|6m|1y` | CÂBLÉ | RBAC + claim preservation | CÂBLÉE |
| `license.extend` | même endpoint sur PAID actif signé | CÂBLÉ | vérité signée + claim preservation | CÂBLÉE |
| `license.suspend` | PATCH `/clients/{id}/suspend` | CÂBLÉ | RBAC positif/négatif + audit | CÂBLÉE |
| `license.revoke` | revoke trial / `grant-license?action=revoke` | CÂBLÉ | permission avant mutation + OWNER refusé | CÂBLÉE |
| `license.manage_devices` | GET devices + POST revoke ciblé | CÂBLÉ | `test_superadmin_device_controls.py`, `test_mobile_device_entitlement.py` | CÂBLÉE — devices/quota/révocation |
| `license.change_release_channel` | PATCH `/clients/{id}/release-channel?channel=stable|beta` | CÂBLÉ | `test_superadmin_license_claim_preservation.py` | CÂBLÉE — stable/beta |
| `admin.read` | GET `/platform-admins` | CÂBLÉ | `test_superadmin_rbac.py` | CÂBLÉE — opérateurs |
| `admin.create` | POST `/platform-admins/{user_id}` | CÂBLÉ | plateforme-only + anti-escalation | CÂBLÉE |
| `admin.update_permissions` | PATCH `/platform-admins/{user_id}/permissions` | CÂBLÉ | allow-list + owner immuable + anti-escalation | CÂBLÉE — matrice RBAC |
| `admin.disable` | PATCH `/platform-admins/{user_id}/enabled` | CÂBLÉ | owner immuable + audit | CÂBLÉE |
| `audit.read` | GET `/audit?limit=&offset=` | CÂBLÉ | `test_superadmin_rbac.py`, filtre `SUPERADMIN_%` | CÂBLÉE — viewer audit |

## Opérations volontairement owner-only

Ces actions utilisent l'identité immuable `SUPERADMIN_USER_ID` plutôt qu'une permission délégable :

- POST `/clients/{id}/validate` ;
- PATCH `/clients/{id}/archive` ;
- PATCH `/clients/{id}/plan` ;
- PATCH `/clients/{id}/notes` ;
- POST `/clients/{id}/send-renewal-email`.

Toutes les mutations restent soumises au step-up WebAuthn plateforme récent.

## Invariants de sécurité

- `SUPERADMIN_USER_ID` conserve la liste fermée des permissions owner ;
- un opérateur non-owner doit posséder explicitement la permission demandée ;
- les rôles cabinet `ADMIN` / `DENTISTE` ne donnent aucune permission plateforme ;
- un compte rattaché à un cabinet ne peut pas devenir opérateur plateforme ;
- l'owner immuable ne peut pas être désactivé/modifié via les routes opérateurs ;
- un non-owner ne peut déléguer que des permissions qu'il possède ;
- un JWT mobile/cabinet est refusé comme session primaire `/api/superadmin/*` ;
- `/mobile/superadmin` exige une connexion plateforme séparée avant d'exposer le workspace ;
- la Tour mobile exige frontend/API plateforme same-origin et refuse une API plateforme cross-origin ;
- un control-plane HTTP distant est refusé ; `localhost`/`127.0.0.1` sont réservés au dev/cert ;
- toute mutation exige un step-up WebAuthn récent ;
- le step-up est séparé (`type=platform_step_up`), TTL 5 min, cookie HttpOnly + Secure + SameSite=Strict + path `/api/superadmin` ;
- les mutations cookie-only exigent une Origin HTTPS exacte de l'allow-list ;
- le frontend ne persiste jamais la preuve step-up ;
- la clé privée Ed25519 n'est présente ni dans le frontend mobile, ni dans le package cabinet.

## `max_devices` — runtime appliqué

Le claim `max_devices` :

1. est obligatoire et vérifié cryptographiquement pour TRIAL/PAID ;
2. est conservé par `LicenseService._verified_result()` ;
3. est lu lors de l'appairage mobile ;
4. borne les `MobilePairedDevice` actifs ;
5. ignore les appareils révoqués ;
6. libère le slot après révocation ;
7. est réservé transactionnellement avant création du device.

SQLite utilise `BEGIN IMMEDIATE` avant comptage + insertion + consommation du token. Les bases serveur utilisent un verrou tenant `FOR UPDATE`.

Preuves :

- `backend/tests/test_license_security.py` ;
- `backend/tests/test_mobile_device_entitlement.py` ;
- `backend/tests/test_superadmin_device_controls.py`.

## Réémission de licence — invariants

Une réémission modifie uniquement le claim demandé :

- extension/révocation préservent `max_devices`, `release_channel`, `feature_set` ;
- changement de plan préserve `max_devices` et `release_channel` ;
- changement de release channel préserve capacité, feature set, type et expiration.

Une preuve active corrompue est refusée avant ces flows.

Preuve : `backend/tests/test_superadmin_license_claim_preservation.py`.

## État UI actuel

Le Control Center câble désormais :

- clients / Trial / grant / revoke / pack / archive / suspension / notes / historique / relance ;
- devices, quota et révocation ciblée ;
- release channel stable/beta ;
- opérateurs plateforme ;
- création/activation/désactivation opérateur ;
- matrice permissions RBAC ;
- viewer audit ;
- état et step-up passkey plateforme.

Il n'existe plus, pour les permissions listées dans cette matrice, de surface volontairement backend-only.

La route desktop `/super-admin` utilise une frontière d'autorité plateforme dédiée (`SuperAdminAccessBoundary`) : un refus backend n'ouvre plus un shell Superadmin vide comme mécanisme d'accès.

La route `/mobile/superadmin` utilise la même autorité backend mais une session plateforme mobile distincte du JWT cabinet. La PWA cabinet effectue un handoff explicite vers l'origine plateforme si elle est différente.

Dette UX restante : la matrice opérateurs est longue verticalement sur 390/430 px. Elle reste fonctionnelle, sans overflow horizontal ni défaut RBAC.

## Validation exacte

HEAD produit/certification : `89d86dcce8bc572826f2e8bd34d08a950f56cd21`.

- CI #2491 / run `33439854797` — SUCCESS ;
- Mobile Superadmin #39 / run `33439854639` — SUCCESS ;
- targeted mobile/Superadmin tests : 6 fichiers, 16 tests PASS ;
- visual contract : 10/10 automatisé à 390x844 et 430x932 ;
- 0 overflow horizontal ; 0 page error ;
- 7 requêtes plateforme authentifiées et 0 requête API cabinet par viewport ;
- Superadmin Control Center AFTER #58 — SUCCESS ;
- Superadmin Denied AFTER #76 — SUCCESS ;
- Windows Package #171 / run `33439854745` — SUCCESS.

Sur le HEAD de référence, 19 workflows sont SUCCESS et le seul skip observé est M6-I contextuel à cette branche SEC-1.
