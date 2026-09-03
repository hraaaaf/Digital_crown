# Digital Crown — Superadmin — État canonique

Dernière mise à jour : 2026-09-01
Repo : `hraaaaf/Digital_crown`
Branche : `security/sec1-signed-licenses`
PR : #288 — draft

## État vérifié

HEAD produit/certification final : `f2eba90a0f99aa3cdeca299092f99b7d3800c49c`
Base `master` intégrée : `a8dde5b8bd233fe2c8e0b2c914b63aeeffac445c`

Le graphe Git vérifié place la branche à 0 commit derrière `master@a8dde5b8...`. Les commits postérieurs à `f2eba90a...` sont documentaires uniquement ; le produit certifié n'a pas changé.

Statut : **EN COURS — produit, CI, package Windows et Tour de contrôle mobile certifiés. Les seuls gates SEC-1 non prouvés sont les trois mutations production déjà autorisées, bloquées par l'absence vérifiée de credentials/runtime production accessibles depuis les outils disponibles.**

## Goal

Obtenir un control-plane Digital Crown signé, cloisonné du cabinet, least-privilege, auditable et administrable depuis mobile sans transférer l'autorité cryptographique au téléphone.

## Certification produit finale

HEAD : `f2eba90a0f99aa3cdeca299092f99b7d3800c49c`

- CI #2505 / `33519045582` : **SUCCESS**
  - Tests & durcissement ✅
  - Frontend tests + build ✅
  - Garde production ✅
  - M4-A / M4-B / M4-C ✅
- SEC-1 Windows Package #176 / `33519045581` : **SUCCESS**
- Mobile Superadmin #44 / `33519046196` : **SUCCESS**
- Superadmin Control Center AFTER #62 / `33519046070` : **SUCCESS**
- Superadmin Denied AFTER #80 / `33519045504` : **SUCCESS**
- T2 Runtime Browser #1594 : **SUCCESS**
- Marketplace Final #75 : **SUCCESS**
- Portability P5 Native Dependency #344 : **SUCCESS**
- Patient P7 Final #893 : **SUCCESS**
- M6-I #394 : SKIPPED contextuel attendu

Aucun échec critique SEC-1 n'est démontré sur le HEAD produit final.

## Tour de contrôle mobile

BEFORE immuable : `1937169b7d28b361cc0b946026fd9c6402e46e7f` — redirect-only vers `/mobile/dashboard`.

Preuve AFTER initiale : Mobile Superadmin #39 / `33439854639` — SUCCESS.

- 390x844 + 430x932
- 16 tests ciblés + build PASS
- score contractuel 10/10
- 0 overflow horizontal
- 0 page error
- 7 requêtes plateforme authentifiées / 0 requête cabinet par viewport
- artefact `9775861037`
- digest `sha256:e2fe364b99c089d7f058e2d684e76feef3818eb7cd06756fe0e69e76e9cd0cc8`

Recertification finale : Mobile Superadmin #44 — SUCCESS.

## Sécurité vérifiée

- licences Ed25519 signées TRIAL / PAID / OWNER, validation fail-closed ;
- `SUPERADMIN_USER_ID` immuable ; autorité historique par email neutralisée ;
- `PLATFORM_CONTROL_PLANE_ENABLED` OFF par défaut côté cabinet ;
- JWT mobile/cabinet refusé comme session primaire Superadmin ;
- Tour mobile avec session plateforme distincte ;
- frontend + API plateforme same-origin HTTPS en production ;
- cross-origin API / HTTP distant refusés ;
- passkey plateforme dédiée avec `user_verification=required` ;
- step-up serveur 5 min ; cookie HttpOnly + Secure + SameSite=Strict ;
- aucune preuve sensible de step-up persistée côté JS ;
- RBAC fermé, audit privilégié transactionnel, devices/quota/revocation câblés ;
- clé privée Ed25519 hors repo, hors package cabinet, hors téléphone.

## Sync `master` OAuth / HTTPS

`master@a8dde5b8bd233fe2c8e0b2c914b63aeeffac445c` est intégré.

- conflit `backend/routers/auth.py` résolu en conservant les gardes SEC-1 ;
- contrat Google OAuth HTTPS de `master` intégré ;
- test de non-régression : `backend/tests/test_google_oauth_https_runtime_contract.py` ;
- merge `5283154c1c5750c7dcd5d696a3af953f50eebc55` ;
- sync #2 / `33518369216` : SUCCESS ;
- workflows temporaires supprimés du tree final.

## Production signing déjà prouvé

- bootstrap `33266592807` — preuve historique SUCCESS ;
- validation indépendante identité `33267814429` — preuve historique SUCCESS ;
- production kid `dc-prod-1dc019b73b23c7d3` ;
- public trust key `pTsKHE_SrROLwY4tQ3QFaNmKceTqCEbLfRhMI7BMC18` ;
- clé privée control-plane historiquement provisionnée hors repo/client.

## Gates production encore ouverts — autorisation acquise

Les trois mutations SEC-1 ont été explicitement autorisées. Aucune clé USB n'est requise.

Restent non exécutés/non prouvés :

1. provisionner `SUPERADMIN_USER_ID` vers l'owner réel et immuable ;
2. émettre puis vérifier l'entitlement OWNER réel ;
3. inventorier puis migrer/remplacer les licences legacy non signées.

### Probe d'accès production — preuve actuelle

Probe GitHub Actions isolé : `SEC-1 Production Secret Probe` run `33523651514` — **SUCCESS**.

Le probe n'a imprimé aucune valeur ; il a vérifié uniquement présence/absence. Résultat : **MISSING** pour toutes les briques testées au niveau repo :

- secret `DATABASE_URL` ;
- secret `DIGITALCROWN_LICENSE_SIGNING_PRIVATE_KEY_B64URL` ;
- secret `DIGITALCROWN_LICENSE_SIGNING_KEY_ID` ;
- secret `SUPERADMIN_USER_ID` ;
- secrets Firebase usuels `FIREBASE_CREDENTIALS_JSON`, `FIREBASE_CREDS_JSON`, `GOOGLE_APPLICATION_CREDENTIALS_JSON` ;
- secret `SECRET_KEY` ;
- vars `DATABASE_URL`, `DIGITALCROWN_LICENSE_SIGNING_KEY_ID`, `SUPERADMIN_USER_ID`, `APP_PUBLIC_URL`, `FRONTEND_URL`, `ALLOWED_ORIGINS`, `PLATFORM_CONTROL_PLANE_ENABLED`.

Les branches temporaires de probe ont ensuite été repointées sur le checkpoint SEC-1 ; aucun workflow de probe ne reste actif à leur HEAD.

### Blocage réel

`BLOQUÉ EXTERNE — ACCÈS CONTROL-PLANE PRODUCTION ABSENT`

Aucun outil disponible n'expose actuellement un shell/SSH vers le runtime production, Firebase/Firestore direct, ni des secrets/vars GitHub repo permettant de reconstruire ce runtime.

L'exécution exige encore :

- DB/control-plane production ;
- `backend/core/firebase_creds.json` ou équivalent service-account vérifié ;
- clé privée Ed25519 de signature ;
- configuration environnement production ;
- identité owner réelle et inventaire legacy vérifiés.

### Séquence autorisée dès que l'accès existe

1. identifier l'owner réel en lecture seule ;
2. provisionner `SUPERADMIN_USER_ID=<ID vérifié>` ;
3. OWNER dry-run : `python -m backend.owner_license_provisioning --owner-user-id <ID>` ;
4. OWNER apply : ajouter `--apply`, puis read-back ;
5. inventorier les licences legacy ;
6. construire un manifest explicite depuis la vérité métier ;
7. migration dry-run : `python -m backend.legacy_license_migration --issuer-user-id <ID> --manifest <manifest.json>` ;
8. si rapport propre, apply `--apply` puis read-back de chaque licence.

`backend/seed_user.py` ne doit pas être lancé à l'aveugle : créer un owner absent serait une mutation distincte.

## Merge

PR #288 reste draft tant que les trois gates production ne sont pas prouvés.

Avant merge :

1. trois mutations production prouvées ;
2. canonique mis à jour avec leurs preuves ;
3. drift `master` recontrôlé ;
4. draft → ready ;
5. merge ;
6. post-merge sur `master`.

Aucun déploiement Vercel requis ni autorisé.

## Next exact

Fournir un accès vérifié au runtime control-plane production ou injecter les credentials nécessaires dans un canal sécurisé exploitable ; ensuite exécuter immédiatement owner read-only → OWNER dry-run/apply/read-back → inventaire legacy → migration dry-run/apply/read-back.

## Avancement

Aucun pourcentage SEC-1 n'est publié : aucune pondération canonique n'est définie.

Le produit, la Tour mobile, la CI et le package Windows sont certifiés. Le chantier reste ouvert uniquement sur les trois mutations production et leur closeout/merge.
