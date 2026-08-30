# Digital Crown — Superadmin RBAC Matrix

Dernière mise à jour : 2026-08-30

Source d'autorité : `backend/platform_access.py`.

| Permission | Surface actuelle | État | Preuve / dette |
|---|---|---|---|
| `license.read` | GET `/clients`, GET `/trial-codes`, GET `/clients/{id}/license-history` | CÂBLÉ | `require_platform_permission("license.read")`; tests délégués dédiés |
| `license.create_trial` | POST `/trial-codes` | CÂBLÉ | permission explicite + step-up mutation |
| `license.create_paid` | aucune route dédiée | MANQUANT | l'ancien endpoint combiné `grant-license` reste SuperAdmin immuable uniquement |
| `license.extend` | aucune route dédiée | MANQUANT | `grant-license` prolonge une licence mais n'est pas encore délégué par permission |
| `license.suspend` | aucune route déléguée | MANQUANT | `/clients/{id}/suspend` reste SuperAdmin immuable uniquement |
| `license.revoke` | POST `/trial-codes/{id}/revoke` | PARTIEL | révocation Trial déléguée; révocation licence client reste dans `grant-license` SuperAdmin-only |
| `license.manage_devices` | aucune surface Superadmin vérifiée | MANQUANT | à concevoir contre la vérité device/signature |
| `license.change_release_channel` | aucune surface Superadmin vérifiée | MANQUANT | à concevoir sans affaiblir l'entitlement signé |
| `admin.read` | aucune surface opérateurs plateforme | MANQUANT | pas de liste dédiée des administrateurs plateforme |
| `admin.create` | aucune surface opérateurs plateforme | MANQUANT | création d'opérateur non implémentée |
| `admin.update_permissions` | aucune surface opérateurs plateforme | MANQUANT | mutation `User.permissions` non exposée au control-plane |
| `admin.disable` | aucune surface opérateurs plateforme | MANQUANT | désactivation d'opérateur non implémentée |
| `audit.read` | GET `/audit` | CÂBLÉ | lecture bornée 1..100, pagination offset, filtre strict `SUPERADMIN_%`; tests positif/négatif |

## Règles de délégation vérifiées

- L'identité `SUPERADMIN_USER_ID` conserve toutes les permissions de la liste fermée.
- Un utilisateur plateforme non-SuperAdmin doit avoir la permission exacte à `true` dans `User.permissions`.
- Un rôle cabinet `ADMIN` ou `DENTISTE` ne donne aucune permission plateforme par lui-même.
- Toute mutation sous `/api/superadmin` conserve le step-up WebAuthn plateforme de cinq minutes.
- Les fonctions sans permission métier claire restent volontairement SuperAdmin immuable uniquement au lieu d'être ouvertes par approximation.

## Next exact

Séparer l'endpoint combiné `grant-license` en autorisations explicites : `license.create_paid`, `license.extend` et `license.revoke`, avec tests positifs/négatifs et conservation du step-up + audit transactionnel.
