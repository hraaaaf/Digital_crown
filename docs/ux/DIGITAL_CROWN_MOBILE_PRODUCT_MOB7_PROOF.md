# DIGITAL CROWN — MOB-7 Certification globale Mobile Product — Proof

## Goal
Certifier sur un même commit immuable l'ensemble des contrats logiciels mobiles actuels, tout en conservant les preuves visuelles lot par lot et en séparant les gates physiques non certifiables par CI.

## Baseline
`ce2d33d2f6edfd2d6fb99e1ba45b566fc4f3ac37`

## Preuves visuelles réutilisées
Le canonique conserve les runs, artifacts, digests et scores visuels certifiés des lots MOB-2 à MOB-6. MOB-7 ne remplace pas ces preuves par des captures artificielles et ne recalcule pas un score visuel global fictif.

## Gate logiciel final — VERIFIED
- workflow : `.github/workflows/mobile-final-certification.yml` ;
- run : `34232326289` ;
- candidat logiciel immuable : `f4f59fa9d069ec4301c3665a5428d772772854fa` ;
- backend mobile contracts M6 + MOB-5F/H/I : **SUCCESS** ;
- frontend M4/M6 + MOB-5A→I + MOB-6 routing : **SUCCESS** ;
- guarded frontend build : **SUCCESS** ;
- aggregate `Mobile software certification gate` : **SUCCESS**.

### Couverture software démontrée
- M6 backend clinical photo / scan / signature / notifications / push / passkey ;
- MOB-5H SuperAdmin security boundary ;
- MOB-5I waiting-room backend contract ;
- MOB-5F document capability source contract ;
- M4 context bridges ;
- M6.2 offline/sync/retry/refresh/revocation et service-worker boundary ;
- M6.3 agenda/navigation ;
- M6.4 contextual bridge ;
- notification/push UX ;
- patient communication / document share / image viewport / passkey ;
- pairing ECDH ;
- RBAC fail-closed ;
- contrats frontend MOB-5A→I ;
- routage canonique MOB-6 ;
- build production frontend.

## Gates physiques — NON REVENDIQUÉS
Le run software ne certifie pas :
1. Face ID réel ;
2. Touch ID réel si supporté ;
3. biométrie Android réelle ;
4. réception Push réelle PWA background/closed.

Ces quatre gates restent séparés et ne doivent pas être requalifiés en preuve CI.

## Déploiement
Aucun Vercel.

## Gate restant
MOB-7 n'est pas encore `CLOSED` : PR, CI/T2 du HEAD final, merge et post-merge master restent requis.

Statut : `SOFTWARE CERTIFIED — PRE-MERGE CLOSEOUT IN PROGRESS`.
