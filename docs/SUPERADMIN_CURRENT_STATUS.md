# Digital Crown — Superadmin — État canonique

Dernière mise à jour : 2026-09-01
Repo : `hraaaaf/Digital_crown`
Branche : `security/sec1-signed-licenses`
PR : #288 — SEC-1 — draft
HEAD produit/certification certifié : `89d86dcce8bc572826f2e8bd34d08a950f56cd21`
Base `master` intégrée : `843bc6d752f865d04cb8b87cd8c3a4b81cad2ca2`
Statut : EN COURS — code, CI, package Windows et Tour de contrôle mobile certifiés sur `89d86dcc...`; les 3 mutations production SEC-1 sont autorisées mais non exécutées faute d'accès au runtime control-plane réel. Le commit documentaire de closeout doit encore être revalidé avant promotion.

## Goal

Obtenir un control-plane Digital Crown signé, cloisonné du cabinet, least-privilege, auditable et administrable depuis mobile sans transférer l'autorité cryptographique au téléphone.

La Tour de contrôle mobile est une interface d'administration plateforme. Elle ne doit jamais dériver son autorité d'un email mutable, d'un rôle cabinet, d'un JWT mobile/cabinet ou d'une clé privée présente sur l'appareil.

## Succès

Le chantier SEC-1 n'est clos que si :

1. identité Superadmin immuable et fail-closed ;
2. control-plane impossible à activer dans un runtime cabinet ;
3. session mobile/cabinet incapable de devenir session plateforme ;
4. Tour de contrôle mobile accessible via une session plateforme distincte ;
5. frontend et API plateforme utilisent la même origine HTTPS en production ;
6. permissions plateforme explicites et fermées ;
7. mutations critiques protégées par WebAuthn récent ;
8. preuve step-up non persistée dans le frontend ;
9. mutations attribuables/auditées ;
10. entitlements signés appliqués au runtime ;
11. réémissions préservent les claims non modifiés ;
12. CI et package verts sur le HEAD final ;
13. `SUPERADMIN_USER_ID`, OWNER et migration legacy réellement exécutés et prouvés ;
14. UI desktop et mobile certifiées BEFORE/AFTER.

## Implémentation vérifiée

### Autorité et licences

- licences Ed25519 signées pour TRIAL / PAID / OWNER ; vérification fail-closed ;
- TRIAL/PAID exigent un `max_devices >= 1` signé ;
- `release_channel` limité à `stable|beta` ;
- `SUPERADMIN_USER_ID` est l'identité immuable serveur ; l'autorité historique par email est neutralisée ;
- `PLATFORM_CONTROL_PLANE_ENABLED` est OFF par défaut et interdit en environnement cabinet ;
- réémissions de licence préservent capacité, feature set et release channel selon l'opération ;
- clé privée Ed25519 conservée hors repo, hors package cabinet et hors téléphone.

### Frontière cabinet / mobile / plateforme

- JWT mobile refusé comme session primaire `/api/superadmin/*`, même s'il résout vers l'owner ;
- aucun rôle cabinet ne confère une autorité plateforme ;
- `/mobile/superadmin` est une vraie surface Tour de contrôle, mais exige une connexion plateforme séparée ;
- la PWA cabinet ouvre explicitement l'origine plateforme lorsque celle-ci est distincte ;
- la session cabinet n'est jamais promue ni réutilisée comme session Superadmin ;
- le test visuel final prouve `7` requêtes Superadmin authentifiées vers l'API plateforme et `0` requête vers l'API cabinet à chacun des viewports 390 et 430 px.

### Topologie mobile control-plane

Pour la Tour de contrôle :

- frontend plateforme + API plateforme doivent partager la même origine en production ;
- cette origine doit être HTTPS ;
- une API plateforme cross-origin est refusée ;
- un control-plane HTTP distant est refusé ;
- `localhost` / `127.0.0.1` restent autorisés uniquement pour développement/certification ;
- `VITE_PLATFORM_APP_URL` permet le handoff depuis la PWA cabinet ;
- `VITE_PLATFORM_API_URL` désigne l'API plateforme ;
- aucune dépendance implicite à l'API cabinet n'est tolérée dans la Tour de contrôle.

### WebAuthn / CSRF

- passkey plateforme dédiée avec `user_verification=required` ;
- challenge one-shot à TTL court ;
- step-up serveur lié à l'identité plateforme, TTL 5 minutes ;
- cookie `platform_step_up` HttpOnly, Secure, SameSite=Strict, path `/api/superadmin` ;
- mutations Superadmin exigent un step-up récent ;
- mutation cookie-only : Origin HTTPS allow-listée obligatoire ;
- le frontend ne persiste aucune preuve sensible de step-up ;
- les chemins WebAuthn plateforme sont unifiés afin d'éviter des cérémonies concurrentes/doubles.

### RBAC / audit / devices

- matrice fermée : `docs/SUPERADMIN_RBAC_MATRIX.md` ;
- clients/licences, devices, quotas, stable/beta, opérateurs/RBAC, audit et passkey sont câblés dans le Control Center ;
- opérateurs plateforme : permissions explicites, enable/disable, anti-escalation et owner immuable ;
- audit privilégié transactionnel avec acteur/action/cible ;
- devices : capacité signée, liste minimisée, révocation ciblée, slot libéré après révocation, access/refresh révoqués ;
- données sensibles de pairing non exposées dans les réponses/audits métier.

## Preuve UI / UX

### Control Center desktop / responsive historique

- BEFORE immuable : run `33377233900`, baseline `31a02d17616b31b736fa25343b26deefd4335f5f` ;
- AFTER historique : run `33395381972` ;
- reruns SEC-1 ultérieurs : `Superadmin Control Center AFTER` verts ;
- viewports : 390x844, 430x932, 768x1024, 1280x800 ;
- dette connue : densité verticale de la matrice de permissions sur mobile, sans défaut d'autorisation.

### Tour de contrôle mobile — preuve finale

- BEFORE réel : `1937169b7d28b361cc0b946026fd9c6402e46e7f`, vue redirect-only vers `/mobile/dashboard` ;
- AFTER / HEAD produit certifié : `89d86dcce8bc572826f2e8bd34d08a950f56cd21` ;
- workflow : Mobile Superadmin Certification #39, run `33439854639` — SUCCESS ;
- viewports : 390x844 et 430x932 ;
- tests ciblés : 6 fichiers / 16 tests — PASS ;
- build test : PASS ;
- score contractuel automatisé : 10/10 sur les deux viewports ;
- overflow horizontal : aucun ;
- page errors : aucune ;
- requêtes plateforme authentifiées : 7 par viewport ;
- requêtes API cabinet : 0 par viewport ;
- artefact : `9775861037` ;
- digest : `sha256:e2fe364b99c089d7f058e2d684e76feef3818eb7cd06756fe0e69e76e9cd0cc8` ;
- inspection visuelle : interface propre et exploitable ; dette restante limitée à la longueur verticale de la matrice opérateurs.

## CI / package exact HEAD `89d86dcc...`

Vague PR attachée au commit :

- 20 workflows observés ;
- 19 `success` ;
- 1 `skipped` contextuel : M6-I Biometric Passkey Certification #385 ;
- 0 failure / cancelled / timed_out / action_required.

Preuves principales :

- CI #2491 / run `33439854797` — SUCCESS ;
  - `Tests & durcissement` ✅
  - `Frontend (tests & build)` ✅
  - `Garde production (négatif)` ✅
  - M4-A / M4-B / M4-C ✅
- Mobile Superadmin Certification #39 / run `33439854639` — SUCCESS ;
- SEC-1 Windows Package Certification #171 / run `33439854745` — SUCCESS ;
  - real Windows PyInstaller package ✅
  - frozen signed-license tamper rejection ✅
  - package boundary evidence ✅
- Superadmin Control Center AFTER #58 ✅ ;
- Superadmin Denied AFTER #76 ✅ ;
- T2 Runtime Browser #1585 ✅ ;
- Portability Runtime #446 ✅ ;
- Portability P5 Native Dependency #337 ✅ ;
- Catalog #858 ✅ ; Patient P7 #884 ✅ ; Marketplace #66 ✅.

Le skip M6-I n'est pas un gate SEC-1 de cette branche. La preuve biométrique mobile canonique existe déjà dans le chantier Mobile ; la certification physique Face ID/Touch ID/Android reste un gate terrain global distinct.

## Production signing déjà prouvé

- bootstrap : run `33266592807` — preuve historique SUCCESS ;
- validation indépendante identité : run `33267814429` — preuve historique SUCCESS ;
- production kid : `dc-prod-1dc019b73b23c7d3` ;
- public trust key : `pTsKHE_SrROLwY4tQ3QFaNmKceTqCEbLfRhMI7BMC18` ;
- clé privée control-plane provisionnée hors repo/client.

Les anciens runs peuvent ne plus être récupérables via l'API GitHub ; cela n'annule pas les preuves historiques déjà retenues et documentées.

## Gates production encore ouverts — autorisation acquise

L'autorisation humaine des trois mutations SEC-1 a été explicitement accordée. Aucune clé USB n'est requise.

Restent non exécutés/non prouvés :

1. provisionner `SUPERADMIN_USER_ID` vers l'owner réel et immuable du control-plane ;
2. émettre puis vérifier l'entitlement OWNER réel ;
3. inventorier puis migrer/remplacer les licences legacy non signées.

### Blocage réel

`BLOQUÉ EXTERNE — ACCÈS CONTROL-PLANE PRODUCTION ABSENT`

Les outils disponibles dans ce chantier n'exposent actuellement ni shell/SSH vers le runtime de production, ni accès Firebase/Firestore direct. GitHub Actions ne possède pas de workflow de provisioning/migration production vérifié.

L'exécution exige un runtime réel disposant de :

- la DB/control-plane production ;
- `backend/core/firebase_creds.json` ;
- la clé privée Ed25519 de signature ;
- la configuration d'environnement production.

### Séquence autorisée dès que l'accès existe

1. identifier l'owner réel en lecture seule, sans le deviner ;
2. provisionner `SUPERADMIN_USER_ID=<ID vérifié>` ;
3. OWNER dry-run : `python -m backend.owner_license_provisioning --owner-user-id <ID>` ;
4. OWNER apply : `python -m backend.owner_license_provisioning --owner-user-id <ID> --apply` puis read-back ;
5. inventaire legacy ;
6. construire le manifest explicite depuis la vérité métier, sans inférence SQLite ;
7. migration dry-run : `python -m backend.legacy_license_migration --issuer-user-id <ID> --manifest <manifest.json>` ;
8. si rapport propre, apply avec `--apply` puis read-back de chaque licence.

La création d'un nouvel owner si aucun compte n'existe serait une mutation distincte et ne doit pas être improvisée.

## Merge

PR #288 reste draft tant que les trois gates production ne sont pas prouvés.

Avant merge :

1. CI verte du HEAD documentaire final ;
2. trois gates production prouvés ;
3. PR mise à jour ;
4. drift `master` recontrôlé ;
5. draft → ready ;
6. merge ;
7. post-merge sur `master`.

Aucun déploiement Vercel n'est requis ni autorisé pour SEC-1.

## Next exact

1. revalider la CI du commit documentaire de closeout ;
2. mettre la PR #288 en cohérence avec ce HEAD et les preuves si la CI est verte ;
3. obtenir un accès vérifié au runtime control-plane production ;
4. exécuter la séquence des trois mutations déjà autorisées ;
5. closeout → ready → drift → merge → post-merge.

## Avancement

Aucun pourcentage SEC-1 n'est publié : aucune pondération canonique n'est définie. Le produit, la Tour mobile, la CI et le package sont certifiés sur `89d86dcc...`; le chantier reste ouvert sur la CI du HEAD documentaire puis les trois mutations production.
