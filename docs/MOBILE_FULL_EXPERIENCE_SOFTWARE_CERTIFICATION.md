# Digital Crown — Mobile Full Experience — Certification logicielle

Date : 2026-08-27

## Goal

Certifier sur un candidat Git immuable les fondations Mobile et les contrats M6 rejouables en CI, sans présenter une émulation navigateur comme une preuve d'appareil physique.

## Succès logiciel

Le gate logiciel est considéré satisfait uniquement si les contrats backend ciblés, les contrats frontend/transverses ciblés et le build frontend gardé réussissent sur le même HEAD.

## Candidat certifié

- Branche benchmark : `mobile/final-certification`
- HEAD certifié : `5c1a505c94cb6e168c4c272914530616aa60cabe`
- Base produit : `master@41c1a4f894801a8ee5a1635b7ff1f457f9f852bd`
- Diff produit entre la base et le candidat : **aucun** ; seuls `.github/workflows/mobile-final-certification.yml` et `.audit/mobile-final-certification-matrix.md` sont ajoutés.

## Preuves

- Mobile Full Experience Final Certification #2, run `33056672222` : **SUCCESS**.
- Backend mobile contracts : **SUCCESS**.
- Frontend mobile foundations and M6 : **SUCCESS**.
- Build frontend gardé : **SUCCESS**.
- Mobile software certification gate : **SUCCESS**.
- CI générale post-merge M6-I #1917 sur `master` : **SUCCESS**.
- Matrice versionnée : `.audit/mobile-final-certification-matrix.md`.

Le premier run `33056384012` avait échoué avant exécution des contrats backend à cause de trois noms de fichiers de tests erronés dans le harness. Les chemins ont été vérifiés dans le repo puis corrigés ; le run #2 est la preuve canonique.

## Couverture agrégée

Le gate rejoue notamment :

- M6-A photo clinique ;
- M6-B scan documentaire ;
- M6-C signature au fauteuil ;
- M6-D1 notifications + RBAC ;
- M6-D2 Push device-bound ;
- M6-I passkey/biométrie ;
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
5. parcours critiques de la roadmap sur vrai iPhone et Android.

Aucun de ces points n'est déclaré validé par CI.

## Conclusion

**Certification logicielle : obtenue.**

**Certification globale Mobile Full Experience : ouverte sur les gates terrain.**

Aucun score global final ni pourcentage global n'est publié avant couverture terrain suffisante. Aucun déploiement Vercel n'est requis ni autorisé par ce checkpoint.
