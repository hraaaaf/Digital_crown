# Desktop startup blocked by a patient upload — 2026-10-01

The cabinet launcher correctly refuses a release whose file set differs from its
certificate. Imaging uploads were stored under `backend/static/uploads` inside
the release, so an ordinary upload invalidated the next startup.

The correction stores new radio and panoramic uploads under the configured
`MEDIA_ROOT/uploads`, outside the release. Authenticated, tenant-aware URLs remain
unchanged. Reads first use external storage and then the legacy upload directory
to preserve access to existing images. No clinical calculation changes.

## Activation

1. Merge the reviewed correction and certify the exact current master SHA using
   the cabinet release workflow. Compose an INSTALLABLE_CERTIFIED release using
   `backend/scripts/create_release.ps1`.
2. Follow the cabinet backup runbook for database and all legacy/external media.
3. Copy existing legacy `radios` and `panoramic` files to `MEDIA_ROOT/uploads`
   without overwriting different bytes. Compare SHA-256 hashes. Keep the originals
   until authenticated reads and backup preservation have been verified. Database
   URLs do not require modification.
4. Stop the previous runtime and start the newly composed release through its
   controlled launcher, without reload. Verify health, compiled frontend delivery,
   anonymous rejection and an authenticated image read.
5. Point the desktop launcher at the newly composed release. Do not choose releases
   by lexicographic SHA order; select the intended composed release explicitly.

Never delete the unexpected patient file, edit a release certificate, add an
upload exception to the code verifier, or use the development reloader to bypass
the startup failure.
