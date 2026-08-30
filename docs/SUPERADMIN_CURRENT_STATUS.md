# Digital Crown — Superadmin — État canonique

Dernière mise à jour : 2026-08-30
Repo : `hraaaaf/Digital_crown`
Branche : `security/sec1-signed-licenses`
PR : #288 — SEC-1
HEAD de départ audité : `7c902592ab9f091c1a970289771417499aea67d5`
Statut : EN COURS — non certifié

## Goal

Obtenir un Superadmin Digital Crown réellement sûr, cloisonné du cabinet, exploitable et auditable, avec une autorité plateforme impossible à obtenir par rôle/email local et des actions critiques protégées proportionnellement à leur risque.

## Succès

Le lot est clos uniquement si :

1. l'identité Superadmin est immuable et fail-closed ;
2. le control plane est impossible à activer sur un runtime cabinet ;
3. une licence cabinet expirée/révoquée ne bloque pas l'autorité plateforme légitime ;
4. une session mobile/cabinet ordinaire ne peut pas devenir une session plateforme privilégiée ;
5. les permissions plateforme sont explicites et séparées des permissions cabinet ;
6. les mutations critiques exigent une assurance renforcée proportionnée au risque ;
7. toute mutation Superadmin est attribuable à un acteur exact et historisée ;
8. suppression/purge cabinet est protégée contre l'erreur et la compromission ;
9. reset password utilise un mécanisme court, révocable et one-shot ;
10. métriques et états de licence affichés correspondent à la vérité métier ;
11. tests négatifs et positifs couvrent les frontières d'autorisation ;
12. la surface UI Superadmin est auditée séparément avec BEFORE/AFTER si elle est modifiée.

## Preuves déjà vérifiées

### Autorité plateforme

- `SUPERADMIN_USER_ID` est l'identité immuable serveur ; `0` fail-closed.
- `SUPERADMIN_EMAIL` est neutralisé par validator et ne peut pas redevenir une racine d'autorité.
- `PLATFORM_CONTROL_PLANE_ENABLED` est OFF par défaut.
- `ENVIRONMENT=cabinet` + control plane activé est rejeté par validation de configuration.
- `is_platform_superadmin()` exige : control plane actif + user actif/non archivé/non suspendu + id exact.
- les permissions plateforme sont une allow-list distincte des permissions cabinet.
- le Superadmin configuré reçoit les permissions plateforme via son identité immuable ; les autres utilisateurs doivent posséder une permission explicite.

### Chaîne d'auth actuelle

`/api/superadmin/*` utilise `get_current_user()` puis `is_platform_superadmin()` ou `has_platform_permission()`.

`get_current_user()` :
- accepte JWT `access` et `mobile` ;
- vérifie signature, type, JTI blacklist et utilisateur actif ;
- applique le runtime signed-license gate sur les mutations ordinaires ;
- exclut explicitement `/api/superadmin` du signed-license gate afin d'éviter une boucle de bootstrap licence.

Conséquence vérifiée : le risque précédemment suspecté « Superadmin dépend d'une licence cabinet valide » n'est PAS présent sur le HEAD audité.

### Tokens

- access token : 30 minutes par défaut ;
- refresh token : 30 jours par défaut ;
- cookies HttpOnly, SameSite=Lax ; Secure seulement si `ENVIRONMENT=production`.

### Recherche MFA

Aucune implémentation trouvée via recherche repo pour `mfa`, `totp`, `2fa`, `passkey`, `webauthn` associée au Superadmin. Absence à confirmer par inspection des flows d'auth complets avant conclusion finale.

## Risques ouverts

### P1 — session privilégiée insuffisamment distinguée

`get_current_user()` accepte les tokens `access` ET `mobile`, et les dépendances Superadmin se basent ensuite sur l'identité utilisateur.

Risque à confirmer : un token mobile appartenant au `SUPERADMIN_USER_ID` pourrait satisfaire les guards plateforme. Une session mobile ne doit jamais devenir automatiquement une session Superadmin.

**Goal :** seuls des tokens/sessions explicitement autorisés pour le control plane peuvent appeler les routes Superadmin.

**Preuve attendue :** tests négatifs token mobile → Superadmin 401/403 ; access token plateforme légitime → succès.

### P1 — step-up / MFA opérations critiques

Aucune preuve actuelle d'un MFA ou d'une réauthentification récente spécifique aux mutations Superadmin critiques.

**Goal :** compromission d'un simple access token ne suffit pas pour une purge cabinet, révocation massive, reset sensible ou changement d'autorité.

**Preuve attendue :** contrôle backend + tests négatifs/positifs.

### P1 — suppression cabinet

La suppression complète d'un client est une opération potentiellement irréversible.

**Goal :** permission dédiée, confirmation structurée, raison obligatoire, audit exact et stratégie restore/soft-delete ou purge en deux phases.

### P2 — reset password

Le flux Superadmin doit être vérifié pour TTL, usage unique, invalidation et changement obligatoire.

### P2 — audit trail

Toute mutation doit conserver au minimum : `actor_user_id`, `action`, `target_type`, `target_id`, `reason`, `timestamp`, `request_id`, `result`.

### P2 — métriques

Vérifier que `active_subscriptions`, états licence/trial/revoked/expired et statistiques dashboard reposent sur la vérité métier et non un proxy approximatif.

### P2 — environnement/cookies

Le cookie `Secure` dépend de `ENVIRONMENT == production`. Vérifier les valeurs réellement autorisées et fail-closed en cas de typo ou environnement control-plane dédié.

## Séquence restante

1. P1 Auth Superadmin : isoler token plateforme des tokens mobile/cabinet.
2. Ajouter/adapter tests d'autorisation négatifs et positifs.
3. P1 Step-up/MFA pour mutations critiques.
4. P1 suppression cabinet sûre.
5. P2 audit trail exact.
6. P2 reset password one-shot.
7. P2 métriques et états métier.
8. Audit frontend Superadmin + baseline UI si surface existante.
9. Tests backend/frontend ciblés.
10. CI SEC-1.
11. Mise à jour du présent fichier avec preuves et HEAD.
12. Closeout seulement si tous les gates sont prouvés.

## Next exact

Inspecter la création/validation des sessions mobile et web, prouver si un token mobile du `SUPERADMIN_USER_ID` peut atteindre `/api/superadmin/*`, puis corriger fail-closed et ajouter les tests correspondants si le risque est réel.

## Avancement

Non chiffré : audit initial effectué, correction P1 auth pas encore prouvée. Ne pas convertir en pourcentage sans critères pondérés explicites.
