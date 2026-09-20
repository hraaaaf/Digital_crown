# Digital Crown Opaque Relay

Separate deployment unit for Patient Companion remote transport.

## Security boundary

This service is a mailbox broker, not a clinical API.

It must:
- store only opaque JWE blobs;
- know no patient/tenant/access/resource identifiers;
- have no cabinet database or media credentials;
- never import `backend.*`;
- never decrypt clinical content.

## Production start contract

Required environment configuration:
- `DC_RELAY_DATABASE_URL` — managed SQL database; SQLite is rejected by the production entrypoint;
- `DC_RELAY_BOOTSTRAP_SECRET` — cabinet infrastructure provisioning secret, >=32 bytes, injected from the deployment secret manager;
- `DC_RELAY_ALLOWED_ORIGINS` — comma-separated explicit HTTPS origins; wildcard is rejected.

ASGI application:
`relay.app:app`

Apply `relay/migrations/001_init.sql` before start. Runtime does not auto-create production schema.

## Required ingress controls

Before any production deployment:
- TLS only;
- HSTS at the public edge;
- request-body limit slightly above the 256 KiB protocol blob limit;
- IP/request rate limiting;
- access logs must redact Authorization and X-Relay-Bootstrap headers;
- response bodies must never be logged;
- database encryption/backups appropriate to opaque ciphertext + capability hashes;
- health endpoint may be public but reveals only `{"status":"ok"}`.

## Capabilities

Each mailbox gets independent 256-bit read and write capabilities.

Only SHA-256 hashes are persisted.

Raw capabilities exist only in the one-time provisioning response and endpoint vault/configuration.

## Non-goals

- no decryption;
- no clinical business logic;
- no appointment scheduling logic;
- no patient identity database;
- no notifications content;
- no direct cabinet reachability;
- no Firebase clinical transport.

## Deployment status

NOT DEPLOYED.
A production deployment is a separate human gate.
