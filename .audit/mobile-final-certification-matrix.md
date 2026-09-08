# Mobile Full Experience — Final certification matrix

## Goal
Certify the complete current Mobile Product software surface on one immutable candidate without re-implementing lot-specific visual harnesses and without pretending that browser CI can prove physical-device behavior.

## Success
The software gate is green only if every selected backend contract, every selected frontend/foundation/product contract, and the guarded frontend build succeed on the exact same Git commit.

Lot-level visual proofs remain authoritative for their UI. Global Mobile closeout additionally requires the physical-only human gates below; a green software run MUST NOT be recorded as proof of those physical behaviors.

## Automated software matrix

### Backend contracts — foundations/M6
- M6-A clinical photo: `backend/tests/test_mobile_m6a_clinical_photo.py`
- M6-B document scan: `backend/tests/test_mobile_m6b_document_scan.py`
- M6-C chairside signature hardening: `backend/tests/test_mobile_m6c_signature_hardening.py`
- M6-D1 in-app notifications + RBAC: `backend/tests/test_mobile_m6d_notifications.py`
- M6-D2 device-bound Web Push: `backend/tests/test_mobile_m6d2_push.py`
- M6-I passkey/biometric backend contract: `backend/tests/test_mobile_m6i_passkey.py`

### Backend contracts — current Mobile Product
- MOB-5H SuperAdmin WebAuthn boundary: `backend/tests/test_marketplace_superadmin_security.py`
- MOB-5I waiting-room tenant/status contract: `backend/tests/test_mobile_waiting_room.py`
- MOB-5F Quick Document capability source: compile and explicit permission/source assertions against `backend/routers/mobile_patient_cockpit.py` and `backend/routers/documents.py`

### Frontend foundations and M6 contracts
- M4-A patient contextual bridge: `frontend/src/test/mobileM4APatientContext.test.ts`
- M4-B panoramic contextual bridge: `frontend/src/test/mobileM4BPanoramicContext.test.ts`
- M4-C document contextual bridge: `frontend/src/test/mobileM4CDocumentContext.test.ts`
- M6.2 scoped offline queue, retry, refresh and revocation: `frontend/src/test/mobileM62Behavior.test.ts`
- M6.2 offline truth / service-worker boundary: `frontend/src/test/mobileM62OfflineTruth.test.ts`
- M6.3 canonical agenda/navigation contract: `frontend/src/test/mobileM63CanonicalAgenda.test.ts`
- M6.4 contextual QR bridge allowlist and server-resolved destination: `frontend/src/test/mobileM64ContextualBridge.test.ts`
- M6-D1 notification UX: `frontend/src/test/mobileM6D1Notifications.test.tsx`
- M6-D2 Push UX: `frontend/src/test/mobileM6D2Push.test.ts`
- M6-E patient communication: `frontend/src/test/mobileM6EPatientCommunication.test.ts`
- M6-F document share: `frontend/src/test/mobileM6FDocumentShare.test.ts`
- M6-H image viewport: `frontend/src/test/mobileM6HImageViewport.test.ts`
- M6-I passkey/biometric: `frontend/src/test/mobileM6IPasskey.test.ts`
- Pairing ECDH encrypted master-key flow: `frontend/src/services/zka/ecdhPairing.test.ts`
- Canonical RBAC fail-closed matrix: `frontend/src/utils/accessControl.test.ts`

### Frontend current Mobile Product contracts — MOB-5A→I + MOB-6
- shared mobile bridge: `frontend/src/features/mobile/bridge.m5a.test.ts`
- canonical bottom nav: `frontend/src/features/mobile/Dashboard/components/MobileBottomNav.test.tsx`
- runtime theme hardcoding guard: `frontend/src/features/mobile/mobileThemeHardcoding.test.ts`
- MOB-5B Frontdesk: `frontend/src/features/mobile/Dashboard/views/FrontdeskView.test.tsx`
- MOB-5C Notifications: `frontend/src/features/mobile/Dashboard/views/NotificationsView.test.tsx`
- MOB-5D Stock: `frontend/src/features/mobile/Dashboard/views/StockView.test.tsx`
- MOB-5E Library: `frontend/src/features/mobile/Dashboard/views/LibraryView.test.tsx`
- MOB-5F Quick Document: `frontend/src/features/mobile/Dashboard/views/MobileQuickDocumentSheet.test.tsx`
- MOB-5F Patient integration: `frontend/src/features/mobile/Dashboard/views/MobilePatientsView.test.tsx`
- MOB-5G shared Marketplace data: `frontend/src/features/partnerMarketplace/data.test.ts`
- MOB-5G Marketplace hook: `frontend/src/features/partnerMarketplace/usePartnerMarketplace.test.tsx`
- MOB-5G mobile Marketplace: `frontend/src/features/mobile/Dashboard/views/MarketplaceView.test.tsx`
- MOB-5H SuperAdmin view: `frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.test.tsx`
- MOB-5H SuperAdmin hook: `frontend/src/features/mobile/superadmin/useMobileSuperAdmin.test.tsx`
- MOB-5I waiting room: `frontend/src/features/mobile/__tests__/waitingRoomMob5i.test.tsx`
- MOB-6 canonical mobile routing: `frontend/src/features/mobile/__tests__/mobileRoutingMob6.test.ts`
- Guarded frontend production-safe build: `npm run build`

## Runtime and visual evidence
MOB-7 does not manufacture replacement screenshots. Existing lot-level BEFORE/AFTER artifacts remain authoritative for their UI claims, including canonical 390 / 430 / 768 evidence for the Mobile Product lots and the certified MOB-6 routing comparison.

The current candidate must still pass the software runtime boundaries encoded by offline/service-worker, routing, pairing, RBAC, notification/push and build contracts. PR-level T2 remains an independent browser/runtime regression gate when triggered.

## Physical-only human gates
These cannot be truthfully certified by Ubuntu/browser CI and remain explicit before any claim about physical behavior:
1. Face ID unlock on a supported iPhone.
2. Touch ID unlock on a supported Apple device if part of the supported device set.
3. Android biometric unlock on a supported Android device.
4. Real Push notification reception while the installed PWA is backgrounded/closed, with generic lock-screen payload and authenticated deep-link reopening.

## Deployment
None. This certification does not authorize or perform a Vercel deployment.
