# Digital Crown — Mobile Full Experience — Certification logicielle

Date : 2026-08-27

## Goal

Certifier sur un candidat Git immuable les fondations Mobile et les contrats M6 rejouables en CI, sans présenter une émulation navigateur comme une preuve d'appareil physique.

## Succès logiciel

Le gate logiciel est considéré satisfait uniquement si les contrats backend ciblés, les contrats frontend/transverses ciblés et le build frontend gardé réussissent sur le même HEAD.

## Candidat logiciel initial certifié

- Branche benchmark : `mobile/final-certification`
- HEAD certifié initial : `5c1a505c94cb6e168c4c272914530616aa60cabe`
- Base produit initiale : `master@41c1a4f894801a8ee5a1635b7ff1f457f9f852bd`
- Diff produit initial entre la base et le candidat : **aucun** ; seuls `.github/workflows/mobile-final-certification.yml` et `.audit/mobile-final-certification-matrix.md` étaient ajoutés.

## Preuves du checkpoint logiciel initial

- Mobile Full Experience Final Certification #2, run `33056672222` : **SUCCESS**.
- Backend mobile contracts : **SUCCESS**.
- Frontend mobile foundations and M6 : **SUCCESS**.
- Build frontend gardé : **SUCCESS**.
- Mobile software certification gate : **SUCCESS**.
- CI générale post-merge #1919, run `33057377861` : **SUCCESS**.
- Matrice versionnée : `.audit/mobile-final-certification-matrix.md`.

Le premier run `33056384012` avait échoué avant exécution des contrats backend à cause de trois noms de fichiers de tests erronés dans le harness. Les chemins ont été vérifiés dans le repo puis corrigés ; le run #2 reste la preuve canonique du checkpoint logiciel initial.

## Amendement terrain réseau — WebAuthn / QR

La préparation des preuves physiques a identifié un écart réel entre le bridge QR sécurisé et l'origin WebAuthn strictement accepté :

- le bridge contextuel pouvait ouvrir `https://digitalcrown.local:8005` ;
- M6-I impose `RP ID = digitalcrown.local` et `Origin = https://digitalcrown.local:5173` ;
- un QR ouvert directement sur `:8005` ne peut donc pas constituer une preuve WebAuthn valide pour l'origin attendu.

Correctif intégré :

- découverte QR sécurisée alignée sur `WEBAUTHN_ORIGIN` (`https://digitalcrown.local:5173`) ;
- compatibilité legacy `/zka-key-qr` alignée sur le même origin ;
- régression ajoutée au contrat canonique `backend/tests/test_mobile_m6i_passkey.py` ;
- aucun changement UI ;
- aucun déploiement Vercel.

### Preuves de l'amendement

- HEAD produit/candidat : `2f9393548e3451d4d9228ab1dc8e034c4045a74c`.
- Mobile Full Experience Final Certification #3, run `33097867532` : **SUCCESS** sur cet exact HEAD.
- Intégration canonique : `master@2f9393548e3451d4d9228ab1dc8e034c4045a74c`.
- CI générale post-intégration #1944, run `33099278506` : **SUCCESS** sur ce même HEAD.

Le correctif réseau terrain est donc logiciellement certifié et intégré.

## Couverture agrégée

Le gate rejoue notamment :

- M6-A photo clinique ;
- M6-B scan documentaire ;
- M6-C signature au fauteuil ;
- M6-D1 notifications + RBAC ;
- M6-D2 Push device-bound ;
- M6-I passkey/biométrie, y compris la régression d'origin QR/WebAuthn ;
- M4-A/B/C contextes ;
- offline/reconnect, rotation/révocation de session ;
- Agenda/navigation canonique ;
- bridge QR allowlisté ;
- pairing ECDH ;
- RBAC fail-closed ;
- communication patient, partage documentaire, imagerie plein écran ;
- build frontend.

Les preuves visuelles lot par lot restent canoniques. M6-I conserve notamment : 390/430/768 sans overflow ni erreur runtime, CTA biométrie 52 px, contenu protégé absent en état verrouillé, CTA déverrouillage 56 px, score visuel 9,7/10.

## Gates terrain encore ouverts

La certification **globale** Mobile Full Experience n'est pas close. Restent à prouver sur appareils physiques pris en charge :

1. Face ID sur iPhone compatible ;
2. Touch ID si un appareil Touch ID fait partie du parc supporté ;
3. biométrie Android réelle ;
4. réception Push réelle PWA en arrière-plan/fermée avec payload écran verrouillé générique puis réouverture authentifiée ;
5. parcours critiques de la roadmap sur vrai iPhone et Android ;
6. offline/reconnect et révocation fail-closed sur appareils physiques.

Aucun de ces points n'est déclaré validé par CI.

## Conclusion

**Certification logicielle : obtenue et amendement réseau terrain certifié/intégré sur `master@2f9393548e3451d4d9228ab1dc8e034c4045a74c`.**

**Certification globale Mobile Full Experience : ouverte uniquement sur les gates terrain physiques.**

Aucun score global final ni pourcentage global n'est publié avant couverture terrain suffisante. Aucun déploiement Vercel n'est requis ni autorisé par ce checkpoint.
