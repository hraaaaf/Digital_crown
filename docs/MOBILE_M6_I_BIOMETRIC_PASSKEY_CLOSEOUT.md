# Digital Crown — M6-I Biométrie / Passkey — Closeout

Date : 2026-08-27

## Goal

Verrouiller l’expérience mobile par une biométrie/passkey device-bound sans contourner l’identité, les permissions ni la révocation backend.

## Résultat certifié

M6-I est certifié sur le HEAD produit/harness `52357569dacd82604d77318fd933502368969b9f`.

Architecture certifiée : WebAuthn/passkey liée utilisateur + tenant + appareil, `userVerification: required`, challenge one-shot, credential unique par appareil, JWT UV 5 min conservé uniquement en mémoire, JWT durable fail-closed après activation, coffre PRF 32 octets + AES-GCM et révocation backend autoritaire.

## Preuves

- M6-I #10 / run `33021345021` : SUCCESS.
- CI #1915 : SUCCESS.
- T2 #1046 : SUCCESS.
- Patient P7 #345 : SUCCESS.
- Portability Runtime #66 : SUCCESS.
- Artifact final BEFORE/AFTER récupéré et inspecté.
- 390 / 430 / 768 px : zéro overflow, zéro erreur runtime.
- CTA biométrie : 52 px.
- Écran verrouillé : contenu protégé absent.
- CTA déverrouillage : 56 px.
- Score visuel final : 9,7/10.
- Aucun review/thread bloquant au moment du closeout.

## Anomalie transversale non bloquante

Catalog #319 reste rouge. Le défaut est déjà identifié comme un problème transversal du harness de dépendances : le BEFORE installe ses dépendances puis le HEAD est testé sans réinstallation. Il n’est pas attribué au produit M6-I et ne remet pas en cause les preuves exact-head dédiées ci-dessus.

## Limites terrain conservées

Face ID / Touch ID / biométrie Android réels ne sont pas simulés comme preuve physique. Ils restent des gates de la certification complète finale Mobile Full Experience, avec la réception Push réelle sur iPhone/Android.

## UI / UX

Chaîne obligatoire satisfaite : BEFORE exact-base → goal écrit → mockup → implémentation → AFTER exact-head → inspection comparative.

Score : **9,7/10**.

## Conclusion

M6-I satisfait ses critères de succès logiciels et visuels et peut être intégré. La certification physique globale Mobile reste distincte et doit encore couvrir les appareils réels et les parcours finaux de la roadmap canonique.

Aucun déploiement Vercel n’est requis ni autorisé par ce closeout.
