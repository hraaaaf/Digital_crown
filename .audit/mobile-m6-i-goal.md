# M6-I — Biométrie / passkey — Goal

## Goal
Ajouter un verrou biométrique/passkey optionnel à la PWA mobile déjà appairée, lié à l'utilisateur, au tenant et au `MobilePairedDevice`, sans remplacer le QR d'appairage, la révocation backend ni l'autorité serveur.

## Contraintes sécurité
- WebAuthn RP ID stable : `digitalcrown.local` ; origine : `https://digitalcrown.local:5173`.
- `userVerification: required` ; challenge court, one-shot et scoped user/tenant/device/purpose.
- Une passkey active ne peut pas être remplacée par le JWT durable ; désactivation après step-up UV obligatoire.
- Après activation, le JWT mobile durable seul est refusé sur les routes mobiles protégées (`423 MOBILE_BIOMETRIC_LOCKED`).
- Session UV courte (5 min) et conservée uniquement en mémoire.
- `masterKey`, snapshot, contexte bridge et queue offline sont scellés localement en AES-GCM depuis le PRF WebAuthn ; aucune copie plaintext persistante lorsque le coffre existe.
- Hors réseau, la biométrie peut uniquement ouvrir le coffre local ; aucune route serveur n'est déverrouillée sans session UV serveur.
- La révocation du `MobilePairedDevice` reste autoritaire.

## Goal visuel
Conserver strictement l'identité Digital Crown déjà certifiée M6-G0/G1 : fond clair, tokens `--glass-bg` / `--glass-border`, palette et hiérarchie existantes. Aucun redesign sombre/néon.

Modification visuelle autorisée uniquement :
- ajout de la carte `Verrouillage biométrique` à sa place logique dans la page Sécurité existante ;
- davantage de profondeur du verre ;
- reflets blancs internes très discrets ;
- ombres multicouches douces ;
- CTA primaire conforme au bleu existant.

## Succès observable
- BEFORE et AFTER exacts sur 390×844, 430×932, 768×1024 dans un même run, mêmes surfaces et même shell mobile réel.
- BEFORE : aucune carte M6-I.
- AFTER : carte M6-I visible, CTA activation >=52 px, reflets glass présents, aucun overflow horizontal, aucune erreur runtime.
- Écran verrouillé AFTER : contenu protégé absent, CTA Déverrouiller >=56 px, zéro overflow/erreur.
- Tests backend : durable JWT -> 423 après activation ; UV JWT -> accepté ; enable exige UV ; remplacement actif refusé ; challenge one-shot/device-scoped.
- Tests frontend : token UV memory-only, PRF requis, coffre AES-GCM, données sensibles retirées du stockage plaintext, 423 fail-closed.
- Build frontend et suite backend globale verts au HEAD exact avant merge.
- Aucun Vercel.

## Limite de certification
Le harness Chromium certifie les contrats, états UI et frontières d'autorisation. La présentation réelle de Face ID / empreinte sur iPhone et Android reste un gate terrain de la certification finale Mobile Full Experience.
