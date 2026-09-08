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

## Couverture attendue
### Software courant
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

### Visuel
Les artifacts AFTER déjà certifiés dans le canonique restent les références de chaque lot, avec leurs viewports et scores propres. Un changement UI futur rendrait obligatoire une nouvelle séquence BEFORE/AFTER pour le lot modifié, mais MOB-7 n'en introduit aucun.

### Physique
Non revendiqué par le gate software : Face ID, Touch ID si supporté, biométrie Android et Push réel PWA en arrière-plan/fermée.

## Succès
MOB-7 software est certifié uniquement si le gate agrégé est vert sur un seul HEAD et si aucune preuve n'est sur-déclarée au-delà de ce que les tests démontrent.

Aucun déploiement Vercel.

Statut : `REFERENCE LOCKED — CERTIFICATION RUN IN PROGRESS`.
