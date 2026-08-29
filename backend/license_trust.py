"""Public trust anchors for Digital Crown license verification.

Only Ed25519 PUBLIC keys belong here. Private signing keys must never be
committed or shipped with the desktop application.
"""

TRUSTED_LICENSE_PUBLIC_KEYS: dict[str, str] = {
    "dc-prod-1dc019b73b23c7d3": "pTsKHE_SrROLwY4tQ3QFaNmKceTqCEbLfRhMI7BMC18",
}
