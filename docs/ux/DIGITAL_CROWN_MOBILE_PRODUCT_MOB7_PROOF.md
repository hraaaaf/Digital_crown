# DIGITAL CROWN — MOB-7 Certification globale Mobile Product — Proof

## Goal
Certifier sur un même commit immuable l'ensemble des contrats logiciels mobiles actuels, tout en conservant les preuves visuelles lot par lot et en séparant les gates physiques non certifiables par CI.

## Baseline
`ce2d33d2f6edfd2d6fb99e1ba45b566fc4f3ac37`

## Preuves déjà acquises et réutilisées
Le canonique conserve les runs, artifacts, digests et scores visuels des lots MOB-2 à MOB-6. MOB-7 ne les remplace pas par des captures artificielles.

## Gate logiciel candidat
Le workflow canonique à étendre est `.github/workflows/mobile-final-certification.yml`.

Le run final devra prouver sur son HEAD exact :
- backend M6 + sécurité MOB-5H + Salle d'attente MOB-5I ;
- contrat capacités documentaires MOB-5F ;
- frontend M4/M6 + MOB-5A→I + MOB-6 ;
- offline/sync/retry/revocation ;
- pairing ECDH ;
- RBAC fail-closed ;
- build frontend production.

## Gates physiques
Ils restent explicitement hors gate software : Face ID, Touch ID si supporté, biométrie Android, Push réel PWA background/closed.

## Déploiement
Aucun Vercel.

## État
Aucun run MOB-7 final n'est encore revendiqué. Le fichier sera complété uniquement avec le run, le HEAD et le verdict réellement observés.

Statut : `PREPARED — SOFTWARE CERTIFICATION NOT YET RUN`.
