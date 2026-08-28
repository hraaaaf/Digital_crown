# Digital Crown — Mobile Full Experience — Certification terrain

Date de préparation : 2026-08-28
Dernière mise à jour vérifiée : 2026-08-28

## État du chantier

**STANDBY — attente certification terrain physique.**

Aucun lot produit/code restant n'est identifié par la roadmap canonique. Le chantier n'est pas CLOSED : sa fermeture dépend exclusivement des preuves physiques sur vrai iPhone + Android listées ci-dessous, puis du closeout global.

Condition de reprise : accès au poste cabinet réel + iPhone réel + Android réel pour exécuter la matrice terrain.

## Goal

Fermer les preuves physiques restantes de Mobile Full Experience sur vrai iPhone et Android sans confondre simulation, Preview Vercel et comportement cabinet réel.

## Succès

Aucun P0/P1 et preuves physiques reproductibles pour les gates ci-dessous sur le produit réel.

## Gates terrain obligatoires

### 1. Pairing sécurisé réel
- QR Desktop → Mobile depuis le cabinet réel.
- Code 6 chiffres réel.
- Device binding conservé.
- Expiration et refus d'un contexte invalide.
- Aucun PHI dans le QR/token visible.

### 2. Biométrie physique
- iPhone : Face ID ou Touch ID selon appareil.
- Android : biométrie physique disponible sur l'appareil.
- Refus/annulation biométrique gérés sans bypass.
- Révocation backend rend l'accès biométrique inutilisable.

### 3. Push OS réel
- Réception iPhone réelle.
- Réception Android réelle.
- App au premier plan puis arrière-plan/verrouillée selon capacités OS.
- Payload sans PHI.
- Révocation/permission refusée gérées proprement.

### 4. Offline → reconnect
- Session valide en ligne.
- Perte réseau réelle.
- UI indique honnêtement l'état offline.
- Aucune action non supportée n'est présentée comme synchronisée.
- Reconnexion et reprise sans doublon/corruption.

### 5. Révocation / expiration / permissions
- Révocation appareil/session réelle.
- Token/contexte expiré refusé.
- Permission insuffisante refusée.
- Retour vers un état sûr et compréhensible.

### 6. Parcours critiques finaux
Sur iPhone et Android :
- navigation/session ;
- Patient ;
- Agenda/RDV ;
- imagerie ;
- documents ;
- paiements/Finance selon rôle ;
- réglages/sécurité ;
- contexte QR exact et retour arrière.

## Matrice de preuve

Pour chaque gate : appareil + OS/version + build/commit exact + étape + résultat + capture/vidéo/log pertinent + anomalie P0/P1/P2/P3.

## Règle de clôture

Le chantier Mobile Full Experience ne peut être déclaré globalement CLOSED que lorsque tous les gates physiques ci-dessus sont prouvés sur vrai iPhone + Android, qu'aucun P0/P1 n'est ouvert et que la roadmap/closeout final sont cohérents.

## Point de départ vérifié

Preview Demo Isolation est fermé via PR #287, merge `8afbfd87864ffef5059aefd825950050a31d1429`, closeout `docs/MOBILE_PREVIEW_DEMO_ISOLATION_CLOSEOUT.md`. La Preview reste hors crédit terrain.

Roadmap canonique réalignée le 2026-08-28 sur `master` : Preview Demo Isolation CLOSED et certification terrain devenue le premier gate restant.

## Reprise exacte — terrain iPhone

Premier gate à exécuter à la reprise : **1. Pairing sécurisé réel**.

Chemin produit vérifié dans `OnboardingScanner.tsx` :

1. ouvrir **Sécurité Mobile** sur le poste cabinet réel et générer le pont QR ;
2. ouvrir le **Compagnon Mobile installé** sur l'iPhone ;
3. scanner le QR depuis l'app installée ; le code 6 chiffres reste le fallback ;
4. le client génère une paire ECDH, appelle `/api/mobile/claim-token`, refuse toute réponse contenant un `masterKey` en clair et exige `server_public_key_hex`, `encrypted_master_key_hex`, `access_token`, `refresh_token` et `device_id` ;
5. après succès, vérifier l'ouverture de la destination mobile exacte puis conserver une capture de l'état appairé.

Preuve physique encore requise : exécution réelle de ce parcours sur l'iPhone cabinet. Aucun résultat terrain n'est crédité avant cette preuve.
