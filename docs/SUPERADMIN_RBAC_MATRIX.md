# Digital Crown — Superadmin RBAC Matrix

Dernière mise à jour : 2026-08-30

Source d'autorité : `backend/platform_access.py`.

| Permission | Surface actuelle | État | Preuve / dette |
|---|---|---|---|
| `license.read` | GET `/clients`, GET `/trial-codes`, GET `/clients/{id}/license-history` | CÂBLÉ | permission explicite; tests délégués dédiés |
| `license.create_trial` | POST `/trial-codes` | CÂBLÉ | permission explicite + step-up mutation |
| `license.create_paid` | POST `/clients/{id}/grant-license?action=1m|3m|6m|1y` si entitlement signé non-PAID | CÂBLÉ | choix basé sur `get_effective_license()`, pas `is_licensed`; tests de sélection/deny |
| `license.extend` | même endpoint si entitlement signé PAID actif | CÂBLÉ | choix basé sur vérité signée; tests de sélection/deny |
| `license.suspend` | aucune route déléguée | MANQUANT | `/clients/{id}/suspend` reste SuperAdmin immuable uniquement |
| `license.revoke` | POST `/trial-codes/{id}/revoke` + `grant-license?action=revoke` | CÂBLÉ | permission contrôlée avant lookup cible + step-up; OWNER refusé par flow client |
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
- Création/extension PAID est choisie depuis l'entitlement signé effectif : PAID actif → `license.extend`; TRIAL/inactif → `license.create_paid`.
- Un entitlement OWNER ne peut pas être remplacé/révoqué via le flow licence client.
- Les fonctions sans permission métier claire restent volontairement SuperAdmin immuable uniquement au lieu d'être ouvertes par approximation.

## Next exact

Câbler `license.suspend` sur la suspension client avec tests négatifs/positifs, puis auditer `license.manage_devices` et `license.change_release_channel` contre les claims signés existants avant d'exposer une mutation.
