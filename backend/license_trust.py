"""Public trust anchors for Digital Crown license verification.

Only Ed25519 PUBLIC keys belong here. Private signing keys must never be
committed or shipped with the desktop application.

SEC-1 deliberately fails closed while this mapping is empty. Production key
provisioning is a release gate, not something generated into source code.
"""

TRUSTED_LICENSE_PUBLIC_KEYS: dict[str, str] = {}
