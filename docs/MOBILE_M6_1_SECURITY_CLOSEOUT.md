# Mobile M6.1 — Security-first pairing & device sessions — CLOSEOUT

Date: 2026-08-24
Status: CLOSED

## Goal

Durcir l’expérience mobile avant les travaux offline/UX : l’appairage doit représenter un utilisateur réel du cabinet, chaque session doit être liée à un appareil révocable, les permissions et la licence doivent rester source-of-truth backend, et la rotation/révocation doit échouer fermée.

## Résultat livré

- Appairage QR ciblable vers un utilisateur actif et approuvé du même cabinet.
- Secret QR haute entropie (`secrets.token_urlsafe(24)`) et code manuel 6 chiffres séparé.
- `ZKAPairingToken` lié à `user_id`; anciens tokens sans identité utilisateur rejetés fail-closed.
- Nouvelle identité de session mobile : `sub=user_id`, `tenant_id`, `device_id`, rôle relu depuis la DB.
- `MobilePairedDevice` persistant et révocable.
- Access token mobile 24 h et refresh token 30 jours liés au device.
- Rotation du refresh; replay d’un ancien refresh => révocation du device.
- Access token refusé si le device a été révoqué.
- Révocation cabinet : pairings en attente + devices mobiles invalidés.
- Permissions mobile backend appliquées à Agenda / Patients / Finance.
- Finance snapshot fail-closed : aucune interrogation comptable sans permission.
- Middleware licence compatible avec `sub=user_id`; un collaborateur hérite de la licence du cabinet owner tout en restant bloqué s’il est suspendu/archivé.
- `Permissions-Policy`: caméra same-origin autorisée, microphone et géolocalisation interdits.
- Stockage mobile durable de `access_token`, `refresh_token`, `device_id`.
- Création RDV mobile corrigée : aucun champ ORM `datetime_end` inexistant; `patient_id` fourni est validé dans le tenant et réellement persisté; RDV rapide legacy sans ID conservé jusqu’à M6.3.

## Preuves exactes

- Branche produit : `mobile/m6-security-first`.
- HEAD produit certifié : `1015cbe9eb22ee7b7b30c0ae9f4430a55db3eead`.
- Tree produit : `c95c2392e2dba1947ce41867194c35d3d4e394c4`.
- Parent produit : `2bf0f639b198b5aacdd1f797f62ea9ac11aa9cff`.
- PR : #229.
- Intégrité avant merge : ahead 1 / behind 0, 1 commit, 15 fichiers.
- CI exact-head : run `32706228540` — SUCCESS.
- Backend : **2774 passed, 8 skipped, 4 warnings, 0 failed**.
- Frontend tests + build : SUCCESS.
- Garde production négative : SUCCESS.
- Certifications exact-head complémentaires : Settings Dependency Audit, Settings TemplateEngine Reachability, Portability Runtime, Settings Reachability Audit, Catalog Connected Truth, T2 Runtime Browser et Patient P7 Final — toutes SUCCESS.
- Merge commit master : `4b58a05b2e3bba7006747befe4d7a9b46f45ef3b`.
- Aucun déploiement Vercel.

## Corrections trouvées pendant certification

La certification n’a pas été considérée verte tant que ces défauts n’étaient pas prouvés corrigés :

1. JWT mobile interprété comme email par le middleware licence sur les mutations.
2. `Permissions-Policy: camera=()` bloquant le scanner QR.
3. Endpoint admin de révocation ne révoquant pas réellement les devices/tokens.
4. Collaborateurs Team créés `is_licensed=False` alors que la licence est portée par le cabinet owner.
5. Tests historiques fabriquant des JWT mobiles sans device après passage au contrat device-bound.
6. Route mobile de création RDV construisant `Appointment(datetime_end=...)` alors que le modèle ne possède pas ce champ.

Aucun de ces défauts n’a été masqué en assouplissant les contrôles de sécurité.

## UI/UX

M6.1 ne modifie pas la composition visuelle des écrans mobiles. Les captures BEFORE/AFTER visuelles ne constituent donc pas un gate de ce lot sécurité/backend.

## Dettes connues, hors M6.1

- Transport LAN d’appairage encore en HTTP selon la configuration locale actuelle.
- `master_key` reste stockée en clair dans la ligne de pairing héritée.
- Deux Service Workers / deux mécanismes offline existent encore au moment du merge M6.1.
- Queue offline historique non tenant/device-scoped.
- Certaines mutations mobile ne vérifient pas encore correctement `response.ok`.
- Déplacement RDV mobile reste non canonique jusqu’à M6.3.
- Le contrat patient/RDV complet par ID + DOB/sexe + duplicate handling reste M6.3.

## Next exact — M6.2 Offline Truth

1. Un seul Service Worker Workbox pour le shell statique; zéro cache API dans le SW.
2. Supprimer `frontend/public/sw.js` et son IndexedDB `sync-db`.
3. Une seule queue applicative `MobileStorage`, scoped cabinet + device.
4. Queue uniquement sur vraie panne réseau; HTTP 4xx/5xx = erreur réelle.
5. Replay : suppression de queue uniquement après `response.ok`.
6. Action ID stable (`X-Mobile-Action-Id`) pour status/delete; DELETE tenant-scoped idempotent.
7. Aucun déplacement RDV mis en queue avant M6.3.
8. Refresh mobile partagé via `/api/mobile/refresh-token`, jamais `/auth/refresh`.
9. Labo : statut `SENT` uniquement après persistance backend réussie.
10. Tests ciblés puis certification runtime/visuelle proportionnée aux changements d’état visibles.

M6.1 est fermé sur la base des preuves ci-dessus. M6.2 démarre sur le master post-merge, sans Vercel.
