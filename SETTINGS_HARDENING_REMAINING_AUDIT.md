# Settings Hardening — Remaining Audit

Date: 2026-08-17
Base audited: `085df0daf6d5e7f6b9ad079a3427af2c4a57a6b1`

## Goal
Reprendre le chantier sans inventer de lots ni de pourcentage et identifier uniquement les écarts encore présents sur le master courant.

## Fermé mais absent du premier closeout
- S2 local-first patient/Firebase : PR #124 mergée.
- S3 backup SQLCipher restaurable/vérifiable : PR #125 mergée.
- P1-3 whitelist stricte CabinetConfigUpdate : PR #151 mergée.
- P1-4 doublons patients tenant-scopés : PR #152 mergée.
- P1-2 historique #14 : fermé comme supersédé par S7A #147.

## S12B — licence fail-closed, gap vérifié
`backend/main.py::get_user_license_status()` contient encore un fail-open explicite : si la lecture DB de l'état de licence échoue, le résultat devient `(True, "DB_ERROR_FAIL_OPEN")`. Le middleware peut donc laisser passer une requête sans preuve positive de licence.

Goal : une erreur de lecture de licence ne doit jamais produire `is_ok=True`.

Succès : DB licence inaccessible → état non autorisé/fail-closed ; aucune mutation sans preuve positive ; contrat superadmin explicitement conservé si voulu ; tests ciblés + CI exact-head + T2 exact-head.

## S6C — persistance thème, gap vérifié
`useSettingsStore.applyTheme()` écrit `digitalcrown_theme` dans `localStorage` dès la prévisualisation. `updateProfile()` appelle `applyTheme()` avant sauvegarde backend. Un thème peut donc rester durable localement après échec de `PUT /clinics/me`.

Goal : conserver exactement la preview existante, mais ne persister `digitalcrown_theme` qu'après succès backend ou chargement d'un profil déjà persisté.

Référence visuelle : baseline S1 réelle `admin-branding` aux viewports 1440/1024/768/430/390. Aucun design ou mockup inventé.

Succès : preview inchangée ; save KO → aucune nouvelle valeur durable ; save OK → valeur durable alignée ; captures après conformes à la baseline réelle ; CI/T2 + certification visuelle exact-head.

## Priorité
1. S12B sécurité/licence fail-closed.
2. S6C vérité de persistance thème sans changement visuel.
3. Re-audit ciblé upload/delete/switch cabinet et Branding/Profile avant fermeture finale.

## Pourcentage
Aucun nouveau pourcentage : aucun dénominateur canonique exhaustif vérifiable n'existe encore dans le dépôt.

## Déploiement
Aucun déploiement Vercel autorisé ou requis.
