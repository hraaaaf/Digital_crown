# Mobile M4-A — Patient contextuel — Goal / BEFORE

Date : 2026-08-24
Statut : AUDIT ONLY — aucun changement produit
Base attendue : `master` après closeout M6.4.

## Goal

Depuis une fiche patient desktop, générer un QR opaque qui, après authentification/appairage, ouvre **ce patient précis** sur mobile sans mettre son nom, ses données médicales ni son identifiant interne dans le QR ou l'URL mobile.

## Succès

- génération autorisée uniquement à un utilisateur desktop ayant `patients` ;
- utilisateur non-admin : ciblage mobile limité à lui-même ;
- admin : peut cibler un utilisateur actif/approuvé du même cabinet ayant `patients` ;
- contexte `resource_type=patient` + `resource_id` stocké serveur-side sur le pairing ;
- QR = secret opaque éphémère uniquement ;
- après claim, user/tenant/device/permission/existence du patient sont réévalués ;
- route mobile ID-less `/mobile/context` ;
- contexte local tenant/device-bound dans IndexedDB et effacé avec la session ;
- patient supprimé / autre cabinet / permission retirée / token expiré ou révoqué => fail-closed ;
- retour mobile cohérent vers l'expérience mobile ;
- 0 overflow, 0 erreur runtime, contrôles critiques >=44 px sur 390/430/768 ;
- BEFORE → mockup → AFTER.

## Preuve attendue

E2E : fiche Patient 42 desktop → « Ouvrir sur mobile » → QR opaque → pairing mobile → `/mobile/context` → Patient 42 réellement retourné par le serveur.

Tests négatifs : autre cabinet, patient supprimé, permission `patients` retirée, credential expiré/invalide, contexte modifié localement, session/device révoqué.

## Architecture retenue

- extension additive idempotente de `zka_pairing_tokens` via la mécanique existante `database.migrate_zka_pairing_token_columns()` ;
- colonnes génériques réutilisables M4-B/C/D : `resource_type` et `resource_id` ;
- aucune donnée clinique dans le token ;
- endpoint ressource distinct du bridge Settings pour préserver le least-privilege ;
- l'autorité reste exclusivement backend.

## BEFORE à certifier

- desktop patient : 1280x900 + 768x1024 ; absence actuelle d'action de bridge patient exact ;
- mobile : 390x844 + 430x932 + 768x1024 ; expérience post-pairing générique sans contexte patient exact.

Aucun Vercel.
