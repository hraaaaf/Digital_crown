# P10 — Cross-platform Update Engine

**Status:** ACTIVE — secure-core + post-install truth candidate. **0 EP credited.**

## Goal

Install only an authentic, fresh, strictly newer Digital Crown release, with a verified rescue point before mutation and automatic post-update health/rollback once the P6/P7 installers are certified.

## Secure-core contract

P10 does not treat HTTPS or a SHA-256 alone as update authentication.

A release manifest is a detached Ed25519-signed envelope. The client:

1. verifies the signature against the configured production public key;
2. requires a monotonic positive `sequence`;
3. remembers the highest accepted sequence + canonical signed-metadata hash;
4. rejects lower sequence (`UPDATE_ROLLBACK_BLOCKED`);
5. permits an exact retry of the same sequence only for identical signed metadata;
6. rejects same-sequence conflicting metadata (`UPDATE_REPLAY_CONFLICT`);
7. requires timezone-aware issuance/expiration and rejects expired metadata;
8. persists a monotonic `last_trusted_time` so a local clock rollback cannot move trust time backwards;
9. selects exactly one OS/architecture target;
10. requires HTTPS and verifies exact artifact size + SHA-256 before promotion from `.partial`;
11. creates and verifies a local encrypted DB rescue point, then copies that rescue inside the immutable update job before it can become `prepared`;
12. stages the artifact under the filename signed by the manifest;
13. persists only non-secret update state atomically.

The production **private key is never committed, bundled, downloaded by the client, or persisted by this service**. Only its Ed25519 public key is trusted by the client. Production public-key pinning plus rotation/revocation remain P10 closure gates.

## Post-install truth contract

P10 now has a platform-independent verification boundary for the package after an installer has run, without pretending the platform apply itself is already certified.

The verifier cross-checks two independent truths:

1. the installed executable runs its existing `--package-self-test`, which reads the root canonical `VERSION` bundled by `DigitalCrown.spec`; the self-test must prove the **exact manifest version**, a frozen executable, no missing/forbidden assets, no unqualified scientific weights and `FAIL_CLOSED_NO_WEIGHTS`;
2. only after package truth passes, the verifier accepts the loopback `/health` endpoint when both runtime and DB report `ok`.

The HTTP health gate is restricted to loopback. Git metadata, installer display labels and remote HTTP endpoints are not accepted as the installed-version source of truth.

This closes the previously identified frozen-version observability gap while keeping apply/rollback fail-closed.

## Packaging boundary

P6/P7 own the exact signed installers/packages and their platform installation semantics. Until those artifacts are certified:

- P10 can authenticate metadata, download/verify an artifact, create a rescue-backed immutable update job, and verify an installed package/runtime candidate;
- `apply_certified=false`;
- any attempt to cross the platform-apply boundary fails closed as `UPDATE_PLATFORM_APPLY_NOT_CERTIFIED`.

This is deliberate. A secure updater must not turn an uncertified installer into an automatic production mutation.

## Remaining gates before P10 closure

- P6 exact Windows installer certified and wired to update apply;
- P7 exact signed/notarized macOS package certified and wired to update apply;
- install current → update next → package self-test exact `VERSION` + runtime `/health`;
- migration failure and application-start failure drills;
- automatic package rollback;
- database restore only when migration rollback requires it;
- interrupted download/apply recovery;
- production public-key pinning plus signing-key rotation/revocation procedure;
- Windows + macOS clean-machine certification.

No Vercel.
