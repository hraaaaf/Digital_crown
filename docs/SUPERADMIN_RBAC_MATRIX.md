# Digital Crown — Superadmin RBAC Matrix

Dernière mise à jour : 2026-08-30

Source d'autorité : `backend/platform_access.py`.

| Permission | Surface actuelle | État | Preuve / dette |
|---|---|---|---|
| `license.read` | GET `/clients`, GET `/trial-codes`, GET `/clients/{id}/license-history` | CÂBLÉ | permission explicite; tests délégués dédiés |
| `license.create_trial` | POST `/trial-codes` | CÂBLÉ | permission explicite + step-up mutation |
| `license.create_paid` | POST `/clients/{id}/grant-license?action=1m|3m|6m|1y` si entitlement signé non-PAID | CÂBLÉ | choix basé sur `get_effective_license()`, pas `is_licensed`; tests de sélection/deny |
| `license.extend` | même endpoint si entitlement signé PAID actif | CÂBLÉ | choix basé sur vérité signée; tests de sélection/deny |
| `license.suspend` | PATCH `/clients/{id}/suspend` | IMPLÉMENTÉ — CI À PROUVER | permission explicite + step-up + audit; tests positif/négatif ajoutés |
| `license.revoke` | POST `/trial-codes/{id}/revoke` + `grant-license?action=revoke` | CÂBLÉ | permission contrôlée avant lookup cible + step-up; OWNER refusé par flow client |
| `license.manage_devices` | aucune surface Superadmin | BLOQUÉ PAR RUNTIME | `max_devices` est signé/vérifié mais le flow `/api/mobile/claim-token` crée `MobilePairedDevice` sans lire la limite ni compter les devices actifs; exposer une mutation serait trompeur tant que l'enforcement manque |
| `license.change_release_channel` | aucune surface Superadmin vérifiée | MANQUANT | claim signé et allow-list `stable/beta` existent; réémission doit préserver tous les autres claims, dont `max_devices` |
| `admin.read` | GET `/platform-admins` | IMPLÉMENTÉ — CI À PROUVER | liste owner + opérateurs explicites uniquement |
| `admin.create` | POST `/platform-admins/{user_id}` | IMPLÉMENTÉ — CI À PROUVER | promeut seulement un compte plateforme-only existant; aucun mot de passe temporaire; non-escalation |
| `admin.update_permissions` | PATCH `/platform-admins/{user_id}/permissions` | IMPLÉMENTÉ — CI À PROUVER | allow-list stricte, owner immuable, un opérateur ne délègue pas une permission qu'il ne possède pas |
| `admin.disable` | PATCH `/platform-admins/{user_id}/enabled` | IMPLÉMENTÉ — CI À PROUVER | owner immuable; mutation step-up + audit |
| `audit.read` | GET `/audit` | CÂBLÉ | lecture bornée 1..100, pagination offset, filtre strict `SUPERADMIN_%`; tests positif/négatif |

## Règles de délégation

- L'identité `SUPERADMIN_USER_ID` conserve toutes les permissions de la liste fermée.
- Un utilisateur plateforme non-SuperAdmin doit avoir la permission exacte à `true` dans `User.permissions`.
- Un rôle cabinet `ADMIN` ou `DENTISTE` ne donne aucune permission plateforme par lui-même.
- Toute mutation sous `/api/superadmin` conserve le step-up WebAuthn plateforme de cinq minutes.
- Création/extension PAID est choisie depuis l'entitlement signé effectif : PAID actif → `license.extend`; TRIAL/inactif → `license.create_paid`.
- Un entitlement OWNER ne peut pas être remplacé/révoqué via le flow licence client.
- La suspension client est délégable uniquement via `license.suspend`.
- La délégation `admin.*` ne crée aucun credential : elle transforme seulement un compte plateforme-only existant en opérateur explicite.
- Un compte lié à un cabinet (`employer_id` ou `CabinetConfig.owner_id`) est refusé comme opérateur plateforme.
- L'owner immuable ne peut être modifié/désactivé par les routes opérateurs.
- Un opérateur non-owner ne peut déléguer que les permissions qu'il possède déjà.

## Dette P1 — limite appareils non appliquée

Preuve actuelle : `backend/license_security.py` valide le claim signé `max_devices`, mais `backend/routers/mobile_legacy.py::claim_pairing_token()` ajoute directement un `MobilePairedDevice` après le handshake sans consulter l'entitlement et sans vérifier le nombre d'appareils actifs.

Conséquence : `license.manage_devices` ne doit pas être exposée comme fonctionnalité Superadmin tant que la limite signée n'est pas réellement appliquée au runtime d'appairage.

## Next exact

Valider la CI du lot RBAC/opérateurs. En parallèle, concevoir puis appliquer `max_devices` au runtime d'appairage mobile de façon fail-closed et résistante aux claims concurrents. Seulement ensuite exposer `license.manage_devices`. Puis traiter `license.change_release_channel` en préservant l'intégralité des claims signés.
