# DIGITAL CROWN — MOB-7 Certification globale Mobile Product — Audit

## Baseline
- master immuable de départ : `ce2d33d2f6edfd2d6fb99e1ba45b566fc4f3ac37`
- branche : `cert/mobile-product-mob7`
- aucun déploiement Vercel

## Goal
Certifier la surface logicielle mobile complète actuelle sur un même commit immuable, sans réimplémenter les harnesses des lots et sans transformer des preuves navigateur en prétendue preuve physique.

## Succès observable
Le gate software MOB-7 n'est vert que si, sur le même HEAD :
- les contrats backend mobiles historiques M6 sont verts ;
- les frontières sécurité SuperAdmin MOB-5H et Salle d'attente MOB-5I sont vertes ;
- les contrats frontend/fondations M4/M6 sont verts ;
- les contrats actuels MOB-5A à MOB-5I sont verts ;
- le contrat de routage MOB-6 est vert ;
- pairing ECDH, RBAC fail-closed, offline/sync/retry/revocation restent verts ;
- le build frontend de production est vert.

Les preuves visuelles lot par lot restent les autorités de leur UI. MOB-7 ne fabrique pas de faux remplacement de screenshots déjà certifiés.

## Audit du gate global existant
Le repo possède déjà :
- `.audit/mobile-final-certification-matrix.md` ;
- `.github/workflows/mobile-final-certification.yml`.

Le gate existant couvre les fondations M4, M6.2/M6.3/M6.4, M6-D/E/F/H/I, pairing ECDH, RBAC et build.

### Gap vérifié
Il ne rejoue pas les contrats ajoutés ensuite par la roadmap Mobile Product :
- MOB-5A Équipe ;
- MOB-5B Frontdesk ;
- MOB-5C Notifications ;
- MOB-5D Stock ;
- MOB-5E Bibliothèque ;
- MOB-5F Quick Document Studio ;
- MOB-5G Marketplace ;
- MOB-5H SuperAdmin mobile ;
- MOB-5I Salle d'attente ;
- MOB-6 routage mobile.

## Contrats dédiés réutilisables
### Frontend MOB-5A à MOB-5E
- `src/features/mobile/bridge.m5a.test.ts`
- `src/features/mobile/Dashboard/components/MobileBottomNav.test.tsx`
- `src/features/mobile/Dashboard/views/FrontdeskView.test.tsx`
- `src/features/mobile/Dashboard/views/NotificationsView.test.tsx`
- `src/features/mobile/Dashboard/views/StockView.test.tsx`
- `src/features/mobile/Dashboard/views/LibraryView.test.tsx`
- `src/features/mobile/mobileThemeHardcoding.test.ts`

### MOB-5F Documents
- `src/features/mobile/Dashboard/views/MobileQuickDocumentSheet.test.tsx`
- `src/features/mobile/Dashboard/views/MobilePatientsView.test.tsx`
- compilation + assertions de capacités sur `backend/routers/mobile_patient_cockpit.py` et le routage documentaire canonique.

### MOB-5G Marketplace
- `src/features/partnerMarketplace/data.test.ts`
- `src/features/partnerMarketplace/usePartnerMarketplace.test.tsx`
- `src/features/mobile/Dashboard/views/MarketplaceView.test.tsx`

### MOB-5H SuperAdmin
- backend : `backend/tests/test_marketplace_superadmin_security.py`
- frontend : `src/features/mobile/Dashboard/views/MobileSuperAdminView.test.tsx`
- frontend : `src/features/mobile/superadmin/useMobileSuperAdmin.test.tsx`

### MOB-5I Salle d'attente
- backend : `backend/tests/test_mobile_waiting_room.py`
- frontend : `src/features/mobile/__tests__/waitingRoomMob5i.test.tsx`

### MOB-6 Routage
- `src/features/mobile/__tests__/mobileRoutingMob6.test.ts`

## Preuves visuelles
Les runs/artifacts déjà certifiés dans le canonique restent la source de vérité, notamment : MOB-2/3/4, MOB-5A→I et MOB-6. MOB-7 valide leur cohérence documentaire mais ne prétend pas qu'un nouveau run logiciel remesure leur score visuel.

## Gates physiques séparés
Toujours non certifiables honnêtement par Ubuntu/browser CI :
1. Face ID réel ;
2. Touch ID réel si supporté ;
3. biométrie Android réelle ;
4. réception Push réelle PWA en arrière-plan/fermée.

## Conclusion audit
Le chemin minimal fiable est d'étendre le workflow global existant avec les contrats MOB-5A→I + MOB-6, de l'exécuter une seule fois sur le candidat MOB-7, puis de laisser les quatre gates physiques explicitement séparés.

Statut : `AUDIT VERIFIED — GLOBAL GATE UPDATE REQUIRED`.
