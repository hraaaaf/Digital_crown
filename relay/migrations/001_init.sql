-- Digital Crown Patient Companion opaque relay — schema v1
-- Separate deployment/database. No cabinet clinical tables or foreign keys.

CREATE TABLE IF NOT EXISTS relay_mailboxes (
    id VARCHAR(36) PRIMARY KEY,
    read_capability_hash VARCHAR(64) NOT NULL,
    write_capability_hash VARCHAR(64) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS relay_envelopes (
    envelope_id VARCHAR(36) PRIMARY KEY,
    mailbox_id VARCHAR(36) NOT NULL REFERENCES relay_mailboxes(id) ON DELETE CASCADE,
    blob TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_relay_envelopes_mailbox_id
    ON relay_envelopes(mailbox_id);

CREATE INDEX IF NOT EXISTS ix_relay_envelopes_created_at
    ON relay_envelopes(created_at);

CREATE INDEX IF NOT EXISTS ix_relay_envelopes_expires_at
    ON relay_envelopes(expires_at);
