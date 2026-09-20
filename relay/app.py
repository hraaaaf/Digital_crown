from __future__ import annotations

import os

from relay.service import create_relay_app


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _allowed_origins() -> tuple[str, ...]:
    raw = _required("DC_RELAY_ALLOWED_ORIGINS")
    origins = tuple(item.strip() for item in raw.split(",") if item.strip())
    if not origins or "*" in origins:
        raise RuntimeError("DC_RELAY_ALLOWED_ORIGINS must be an explicit non-wildcard allowlist")
    if any(not origin.startswith("https://") for origin in origins):
        raise RuntimeError("relay allowed origins must use https")
    return origins


database_url = _required("DC_RELAY_DATABASE_URL")
if database_url.startswith("sqlite"):
    raise RuntimeError("SQLite is test-only for the remote relay; production requires a managed SQL database")

bootstrap_secret = _required("DC_RELAY_BOOTSTRAP_SECRET")
if len(bootstrap_secret.encode("utf-8")) < 32:
    raise RuntimeError("DC_RELAY_BOOTSTRAP_SECRET must be at least 32 bytes")

app = create_relay_app(
    database_url=database_url,
    bootstrap_secret=bootstrap_secret,
    allowed_origins=_allowed_origins(),
    create_schema=False,
)
