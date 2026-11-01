# H05 — Cross-identity Windows DPAPI denial, isolated only

Real Windows-2022 lab probe runs as built-in LocalService (SID S-1-5-19) through a transient on-demand Task Scheduler task. It must fail direct read of a vault DACL locked to current owner and SYSTEM, AND must fail the native DPAPI CurrentUser unseal of separately conveyed synthetic ciphertext and entropy. Test verifies true service identity SID; owner still signs. Task and shared ephemeral non-PHI files must be removed; H05 FUE checks Scheduler task absence and exchange directory deletion before writing a PASS artifact. No created account or password.

LocalService is not a second interactive human Windows account. This is a Windows service identity isolation FUE, not an OS reboot, real installed service, hardware key/TPM, imaging adapter, server-side revocation, clinic validation, or deployment. Any unavailable scheduling privilege fails the test, not a simulated green.

PRODUCT_READY=false; CLINICAL_GO=false; ready_to_merge=false.
