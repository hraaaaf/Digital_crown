# DIGITAL CROWN — MOB-7 Certification globale Mobile Product — Proof

## Goal
Certifier sur un même commit immuable l'ensemble des contrats logiciels mobiles actuels, tout en conservant les preuves visuelles lot par lot et en séparant les gates physiques non certifiables par CI.

## Baseline
`ce2d33d2f6edfd2d6fb99e1ba45b566fc4f3ac37`

## Gate logiciel final — VERIFIED
- workflow : `.github/workflows/mobile-final-certification.yml`
- candidat final PR : `a406d81b56e1c7b7b9a04a765391a0a32d560556`
- run global : `34234600211` — **SUCCESS**
- backend M6 + MOB-5A/F/H/I : **SUCCESS**
- frontend M4/M6 + MOB-5A→I + MOB-6 routing + build : **SUCCESS**
- aggregate `Mobile software certification gate` : **SUCCESS**

## Double-check MOB-5A — GAP FERMÉ
Le contrôle final a détecté une asymétrie réelle : la vue Équipe avait une preuve de routing/visuel, mais pas de test dédié de `DentistsView` ni du backend `/mobile/dentists`.

Correction ajoutée et certifiée :
- `backend/tests/test_mobile_team_mob5a.py`
- `frontend/src/features/mobile/Dashboard/views/DentistsView.test.tsx`
- intégration au gate global
- workflow MOB-5A dédié `34234606313` — **SUCCESS**
- artifact AFTER `10059360520`
- digest `sha256:cac6ca025db5f6b172eca67d8aa28e2f573037556a4af7348df65162d78d0659`

## CI / runtime PR final
- CI PR `34234606403` — **SUCCESS**
- T2 Runtime Browser Certification `34234606588` — **SUCCESS**
- frontend tests + build : **SUCCESS**
- backend Tests & durcissement : **SUCCESS**
- garde production : **SUCCESS**
- M4-A/B/C browser contextual bridges : **SUCCESS**

## Couverture software démontrée
- M6 backend clinical photo / scan / signature / notifications / push / passkey
- MOB-5A team backend/frontend
- MOB-5F document capability source contract
- MOB-5H SuperAdmin security boundary
- MOB-5I waiting-room backend contract
- M4 context bridges
- M6.2 offline/sync/retry/refresh/revocation et service-worker boundary
- M6.3 agenda/navigation
- M6.4 contextual bridge
- notification/push UX
- patient communication / document share / image viewport / passkey
- pairing ECDH
- RBAC fail-closed
- contrats frontend MOB-5A→I
- routage canonique MOB-6
- build production frontend

## Merge
- PR `#374`
- HEAD final `a406d81b56e1c7b7b9a04a765391a0a32d560556`
- merge exact `1316b73c70f5cc298eb1101db557d1d4abee1f85`
- post-merge master `34237128357` — en cours au moment de cette mise à jour

## Visuel
MOB-7 n'introduit pas de redesign. Les artifacts, digests, viewports et scores certifiés par les lots précédents restent les autorités visuelles. Aucun score global artificiellement recalculé n'est revendiqué.

## Gates physiques — NON REVENDIQUÉS
La CI ne certifie pas : Face ID réel, Touch ID réel si supporté, biométrie Android réelle, réception Push réelle PWA background/closed.

## Déploiement
Aucun Vercel.

Statut : `MERGED — POST-MERGE MASTER PENDING`.
