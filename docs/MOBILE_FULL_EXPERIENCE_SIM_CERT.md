# Digital Crown — Mobile Full Experience — SIM-CERT iOS + Android

Date : 2026-08-27

## Goal

Ajouter une couche de certification mobile simulée plus proche du terrain avant les preuves physiques finales, sans confondre émulation et matériel réel.

## Succès

Le gate SIM-CERT est vert uniquement si le même HEAD obtient :

1. un WebAuthn platform authenticator virtuel fonctionnel sur l'origin exact `https://digitalcrown.local:5173` ;
2. un vrai iOS Simulator démarré, MobileSafari ouvert sur Digital Crown via le host bridge HTTPS, certificat de test approuvé dans le simulateur et screenshot produit ;
3. un vrai Android Emulator démarré, Chrome réellement au premier plan sur Digital Crown, screenshot produit et commande d'injection fingerprint `adb emu finger touch` réussie ;
4. le contrat frontend M6-I rejoué sur le même candidat ;
5. un aggregate gate qui refuse tout résultat partiel.

## Certification obtenue — 2026-08-27

**État : SIM-CERT ACQUISE dans son périmètre simulé.**

Candidat exact certifié : `1cf26729223b6ecee5ce886d218ef33550e9a6fc`.

Workflow `Mobile OS Simulation Certification` : run #4 `33110537395` ✅ SUCCESS.

Matrice certifiée sur le même HEAD :

- WebAuthn exact-origin virtual authenticator ✅ SUCCESS ;
- iOS Simulator / MobileSafari OS channel ✅ SUCCESS ;
- Android Emulator / Chrome / fingerprint channel ✅ SUCCESS ;
- Mobile SIM-CERT aggregate gate ✅ SUCCESS.

Preuves inspectées :

- `mobile-sim-webauthn` : origin `https://digitalcrown.local:5173`, `secureContext=true`, création puis assertion `public-key` sur le même credential ;
- `mobile-sim-ios` : iPhone Simulator booté, CA host-bridge approuvée, MobileSafari lancé et Digital Crown réellement rendu ; la capture contient uniquement un coachmark Safari de premier lancement, sans défaut produit ;
- `mobile-sim-android` : Android 15/API 35, Chrome confirmé au premier plan par `dumpsys` (`state: cur=TOP`, `top-activity`), URL Digital Crown ouverte et `adb emu finger touch 1` → `OK` ; la capture contient un popup Chrome de premier lancement et n'est donc créditée que comme preuve OS/browser, pas comme certification visuelle produit.

Intégration : PR #284 ✅ squash-merged vers `master@222beb22f3be983655c5209386a2a9b787914c13`.

Aucun code produit/UI existant n'a été modifié par ce lot ; seuls le workflow SIM-CERT, son script WebAuthn virtuel et cette documentation ont été ajoutés. Aucun Vercel.

## Preuves attendues

Artifacts GitHub Actions :

- `mobile-sim-webauthn`
  - résultat JSON exact-origin ;
  - screenshot 390 px ;
- `mobile-sim-ios`
  - modèle/runtime simulator ;
  - screenshot MobileSafari ;
  - certificat host bridge approuvé ;
  - `simctl help` et état de disponibilité du canal biométrique CLI ;
- `mobile-sim-android`
  - modèle/API Android ;
  - browser handler ;
  - Chrome repris au premier plan ;
  - screenshot ;
  - résultat `adb emu finger touch`.

## Ce que SIM-CERT peut créditer

- démarrage d'un OS mobile simulé ;
- ouverture réelle de la surface web dans MobileSafari et Chrome sur simulateur/émulateur ;
- comportement mobile et environnement tactile simulé ;
- exact-origin HTTPS + WebAuthn avec authenticator plateforme virtuel ;
- disponibilité du canal fingerprint Android emulator ;
- preuve complémentaire avant terrain.

## Limitation iOS biométrique

Le runner macOS/Xcode 26 utilisé par GitHub Actions expose `simctl` mais **pas** de sous-commande `biometric`.

La simulation Face ID/Touch ID reste disponible via les contrôles interactifs du Simulator, mais elle n'est pas créditée par ce workflow headless. Le gate ne remplace donc pas IOS-01/IOS-02 sur un appareil réel.

Cette limitation est volontairement fail-honest : aucune API privée ou commande non documentée n'est utilisée pour fabriquer une preuve biométrique iOS.

## Ce que SIM-CERT ne peut jamais créditer

SIM-CERT n'est pas une preuve de :

- vrai Face ID ;
- vrai Touch ID ;
- capteur biométrique Android physique ;
- stockage matériel réel des passkeys ;
- réception Push PWA réelle sur téléphone verrouillé/fermé ;
- comportement radio/Wi-Fi/batterie/mémoire d'un appareil réel.

Ces points restent des gates physiques et doivent être testés sur les appareils réellement supportés.

## Relation avec la certification logicielle

Le produit mobile certifié avant SIM-CERT est `2f9393548e3451d4d9228ab1dc8e034c4045a74c`.

Preuves logicielles déjà acquises :

- Mobile Full Experience Final Certification #3 / `33097867532` : SUCCESS sur `2f939354...` ;
- CI générale produit #1944 / `33099278506` : SUCCESS sur `2f939354...` ;
- closeout documentaire terrain PR #282 : merge `fbce07965932a06671e9460b696a55583cee7cd8` ;
- CI post-merge docs #1946 / `33100809075` : SUCCESS.

SIM-CERT a ensuite été certifiée sur le candidat `1cf267292...` puis intégrée via PR #284 sur `master@222beb22...`.

## Règle de conclusion

- SIM-CERT vert = **certification simulée acquise** dans le périmètre ci-dessus.
- SIM-CERT vert ne ferme pas Mobile Full Experience.
- Mobile Full Experience ne peut être CLOSED qu'après les gates physiques iPhone + Android applicables, Push réel, offline/reconnect et révocation fail-closed, sans P0/P1 ouvert.

Aucun déploiement Vercel n'est requis ni autorisé par ce gate.
