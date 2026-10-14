"""LOT04.8-B2c: resolve enrolled Stations from authoritative Cabinet DB.

Fail-closed integration seam, intentionally NO printer inventory: field-certified
printer records do not yet exist. Empty printers means the B1 compiler cannot
offer even reception until an independent physical certification registry ships.

Never accept browser-supplied device, tenant or certification flags here.
No Station PDF route and no print dispatch.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

from backend.services.station_document_print_configuration import (
    TrustedStation,
    TrustedPrinter,
    PrintConfigurationRejected,
)


def enrolled_stations_for_tenant(
    connection: Connection,
    *,
    tenant_id: int,
) -> dict[str, TrustedStation]:
    """Read only current enrolled Station identities from trusted DB.

    Schema/DB errors propagate: callers MUST treat errors as disabled, never
    fall back to a user-supplied inventory or a previously cached allowlist.
    """
    if type(tenant_id) is not int or tenant_id <= 0:
        raise PrintConfigurationRejected("INVALID_TENANT")
    rows = connection.execute(text("""
        SELECT id, employer_id, default_experience, revoked_at
        FROM workstation_modes
        WHERE employer_id = :tenant_id
    """), {"tenant_id": tenant_id}).mappings().all()
    inventory: dict[str, TrustedStation] = {}
    for row in rows:
        station_id = str(row["id"])
        if not station_id or station_id in inventory:
            raise PrintConfigurationRejected("INVALID_STATION_INVENTORY")
        inventory[station_id] = TrustedStation(
            station_id=station_id,
            tenant_id=int(row["employer_id"]),
            experience=str(row["default_experience"] or ""),
            revoked=row["revoked_at"] is not None,
            enabled=row["revoked_at"] is None,
        )
    return inventory


def independently_certified_printers_for_tenant(
    connection: Connection,
    *,
    tenant_id: int,
) -> dict[str, TrustedPrinter]:
    """No physical certification store yet, so every destination is unavailable.

    Do not substitute printers detected by a browser, by an unverified Windows
    spool listing, or by owner preference; commissioning requires independent
    operator witness and a Cabinet-only, audited registry with revocation.
    """
    if type(tenant_id) is not int or tenant_id <= 0:
        raise PrintConfigurationRejected("INVALID_TENANT")
    return {}
