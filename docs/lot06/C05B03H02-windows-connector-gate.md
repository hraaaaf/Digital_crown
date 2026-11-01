# LOT06 C05B-03H-02 — Windows connector release gate (PROPOSED)

Date: 2026-11-01. This is a requirements checklist, NOT an implemented
Windows connector and NOT an approval to deploy.

H-02 CI on Ubuntu proves the protocol and native SQLCipher transaction but
**cannot certify Windows key custody**. The Ed25519 private key is generated
in volatile test memory. Do not claim native non-exportable Ed25519 in Windows
CNG or physical sensor attestation.

## Minimal next Windows-only engineering pass
1. Identify vendor data path (TWAIN/WIA/SDK/DICOM or watched folder) in a
   test VM. A watched folder is not proof of scanner/hardware origin.
2. Provide per-workstation DPAPI user/machine-scoped private-key encryption
   **or** a validated CNG/TPM-backed signing capability, not both by default.
   Explicitly record whether key material is exportable.
3. Test installation/uninstallation, service account, Windows user logout,
   file ACL, duplicate folders, key loss, revoked station, and restore;
   avoid secrets in logs and automatic silent re-enrollment.
4. Security check: no local HTTP endpoint accepts unsigned image metadata;
   prove tenant/station + content digest + one-shot challenge.
5. Only after Windows FUE and independent review propose an opt-in product
   migration and patient-visible confirmation UI.

STOP: PRODUCT_READY=false; CLINICAL_GO=false; READY_TO_MERGE=false.
