# DIGITAL CROWN — MOB-7 Certification globale Mobile Product — Référence

## Référence de certification
MOB-7 est un lot de certification globale, pas un redesign. Aucune nouvelle surface UI n'est créée par ce lot.

## Doctrine
- un HEAD immuable pour tous les contrats logiciels rejoués ;
- un build production sur ce même HEAD ;
- réutilisation des preuves visuelles certifiées par chaque lot ;
- aucune régénération de screenshots uniquement pour fabriquer une apparence de fraîcheur ;
- T2/CI PR restent des gates transverses indépendants ;
- les comportements physiques restent des gates humains séparés.

## Couverture certifiée software
- backend mobile M6 ;
- MOB-5F capacité documentaire ;
- MOB-5H sécurité SuperAdmin ;
- MOB-5I waiting room ;
- M4 context bridges ;
- offline/sync/retry/revocation ;
- routing/navigation ;
- notification/push contracts ;
- pairing ECDH ;
- RBAC fail-closed ;
- MOB-5A→I frontend contracts ;
- MOB-6 canonical routing ;
- build production.

Gate logiciel : run `34232326289` — SUCCESS sur candidat immuable `f4f59fa9d069ec4301c3665a5428d772772854fa`.

## Visuel
Les artifacts AFTER déjà certifiés dans le canonique restent les références de chaque lot, avec leurs viewports et scores propres. Un changement UI futur rendrait obligatoire une nouvelle séquence BEFORE/AFTER pour le lot modifié, mais MOB-7 n'en introduit aucun.

## Physique
Non revendiqué par le gate software : Face ID, Touch ID si supporté, biométrie Android et Push réel PWA en arrière-plan/fermée.

## Succès
La référence software est satisfaite par le gate agrégé vert sur un seul HEAD. MOB-7 reste non CLOSED tant que la PR, CI/T2, merge et post-merge ne sont pas terminés.

Aucun déploiement Vercel.

Statut : `REFERENCE LOCKED — SOFTWARE CERTIFIED — PRE-MERGE`.
