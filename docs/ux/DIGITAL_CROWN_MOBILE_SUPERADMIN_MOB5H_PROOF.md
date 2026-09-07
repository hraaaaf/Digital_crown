# DIGITAL CROWN MOBILE — MOB-5H SUPERADMIN PROOF

Status: PRE-MERGE CERTIFIED
Branch: `ux/mobile-superadmin-mob5h`
Baseline BEFORE: `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`
Certified product candidate: `307899e74114c3b6c7ed7d1f089f662ff48e9da7`

## Goal

Donner au SuperAdmin mobile toutes les prérogatives SuperAdmin actives de Digital Crown sans créer un SuperAdmin lite ni affaiblir la sécurité serveur.

## Success / preuve observable

### Parité

Les cinq domaines sont présents sur mobile:

1. Vue globale
2. Clients
3. Essais
4. Marketplace
5. Opérations

La matrice exhaustive endpoint → mobile est maintenue dans `DIGITAL_CROWN_MOBILE_SUPERADMIN_MOB5H_AUDIT.md`.

### BEFORE

Artifact GitHub Actions: `9997848118`
Baseline exact: `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`

Viewports:
- 390×844
- 430×932
- 768×1024

Résultat:
- HTTP 200 aux 3 viewports
- 0 page error
- 0 console error
- 0 overflow horizontal
- capacités observées: clients/recherche, pack, extension licence, suspend/reactivate seulement

### AFTER

Run GitHub Actions: `34139199751` — SUCCESS
Artifact: `10025281786`
Digest: `sha256:595a430c22dd8f82a3887b30b01192d6061dfc6a8857eb0cd3961694e253793a`
Product HEAD capturé: `307899e74114c3b6c7ed7d1f089f662ff48e9da7`

Report `report.json` vérifié:
- `baselineBefore = 6eb93c75...`
- `beforeArtifactId = 9997848118`
- 3 captures valides
- 390: scrollWidth 390 / innerWidth 390
- 430: scrollWidth 430 / innerWidth 430
- 768: scrollWidth 768 / innerWidth 768
- `invalidCount = 0`
- `unexpectedApiRequests = []`
- `blockedExternalRequests = []`
- `realExternalEgressAllowed = false`
- pageErrors = [] aux 3 viewports
- consoleErrors = [] aux 3 viewports

Capacités observées aux 3 viewports:
- client: revoke, archive, suspend, history, renewal
- Marketplace: suppliers, catalogue, incidents, audit
- opérations: dispatch, procurement, invoice, receipt

### Tests / build

Run `34139199751`:
- job `SuperAdmin WebAuthn boundary` ✅
- job `SuperAdmin frontend contracts + build` ✅
- job `SuperAdmin AFTER 390 430 768` ✅

Contrats ciblés exécutés:
- `MobileSuperAdminView.test.tsx`
- `useMobileSuperAdmin.test.tsx`
- `backend/tests/test_marketplace_superadmin_security.py`
- build production frontend

### Sécurité

Vérifié dans le code et la CI:
- `verify_superadmin` reste l'autorité core;
- `require_marketplace_superadmin` reste l'autorité P10;
- mobile P10 ordinaire refusé;
- mobile WebAuthn UV court admis au guard métier;
- même backend, même DB, même RBAC;
- pas d'écriture directe DB/Supabase depuis le mobile;
- preview fictive et isolée du réseau réel;
- aucun Vercel.

## Inspection visuelle

AFTER inspecté manuellement sur 390×844 pour la vue globale, le détail client et le détail opération, et le report automatisé couvre les trois viewports.

Constat:
- hiérarchie lisible;
- actions destructives regroupées et séparées;
- contrôle-plane compact plutôt qu'empilement de boutons;
- sheets adaptées aux actions denses;
- aucune collision/overflow observée.

Score visuel pré-merge: **9,3/10**.

Le score reste inférieur à un 10 artificiel: les écrans opérationnels sont volontairement denses et privilégient la sécurité/complétude à l'esthétique décorative.

## Gate restant

MOB-5H n'est pas CLOSED à ce stade. Reste:
1. PR;
2. CI de PR;
3. merge si vert;
4. post-merge CI;
5. mise à jour du canonique.
