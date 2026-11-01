C05B-03H-04 — Windows ACL FUE only. Status: LAB, no clinical GO.

The isolated Windows DPAPI Ed25519 vault now restricts its test keystore directory and private ciphertext file ACLs before writing the encrypted seed. Current owner SID and Windows SYSTEM are the only principals permitted, with inherited ACEs removed. Every signing request re-checks the protected ACL: an injected Everyone ACE on either file or folder is refused. GitHub Windows CI verifies both negative cases and restored-owner signing. No medical identifiers, installer or patient data.

IMPORTANT: The true second-Windows-user logon and cross-SID DPAPI unseal tests are NOT executed by this pass. A protected ACL with precise principals does not certify a separate account execution. Full OS reboot, service identity, Windows profile recovery, physical RVG/TWAIN/WIA/DICOM device, remote revocation integration, TPM nonexportability and real clinical UI remain untested.

No backend/main.py edit, no product Alembic, merge or deployment. PRODUCT_READY=false; CLINICAL_GO=false; ready_to_merge=false.
