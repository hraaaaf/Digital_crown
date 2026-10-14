"""LOT04.8-B — pure, fail-closed compilation of owner-proposed print settings.

No API route, persistence, PDF access or print dispatch is provided here.
Station/device inventory MUST be resolved by trusted Cabinet server code.
Never populate the verified flags from browser/client payloads.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

from backend.services.station_document_print_policy import (
    CabinetPrintPolicy,
    PrinterTarget,
)

_ALLOWED_MODES = frozenset({"disabled", "reception", "near_station", "both"})
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
_SCHEMA_VERSION = 1
_MAX_STATIONS = 50
_MAX_PRINTERS = 50


class PrintConfigurationRejected(ValueError):
    """A rejected configuration is never partially applied."""


@dataclass(frozen=True)
class TrustedStation:
    station_id: str
    tenant_id: int
    experience: str
    revoked: bool = False
    enabled: bool = True


@dataclass(frozen=True)
class TrustedPrinter:
    printer_id: str
    tenant_id: int
    location: str
    station_id: str | None = None
    enabled: bool = False
    # The following bits are sourced from an independent Cabinet-side
    # certification and operating-state registry, NEVER from settings payload.
    secure_release_verified: bool = False
    private_channel_verified: bool = False
    staff_supervised: bool = False


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and _IDENTIFIER.fullmatch(value) is not None


def _ids(value: object, *, max_count: int) -> tuple[str, ...]:
    if not isinstance(value, list) or not (1 <= len(value) <= max_count):
        raise PrintConfigurationRejected("INVALID_ALLOWLIST")
    if not all(_valid_identifier(item) for item in value):
        raise PrintConfigurationRejected("INVALID_ALLOWLIST")
    if len(set(value)) != len(value):
        raise PrintConfigurationRejected("DUPLICATE_ALLOWLIST")
    return tuple(value)


def compile_owner_print_config(
    *,
    tenant_id: int,
    actor_user_id: int,
    actor_employer_id: int | None,
    raw: object,
    trusted_stations: Mapping[str, TrustedStation],
    trusted_printers: Mapping[str, TrustedPrinter],
) -> CabinetPrintPolicy:
    """Compile a complete replacement proposal; do not store or activate it.

    Only the cabinet owner is accepted at this stage. This is deliberately
    narrower than the generic `settings` permission, which can be delegated.
    Inputs actor_* and inventory MUST come from authenticated server/DB state.
    """
    if type(tenant_id) is not int or tenant_id <= 0:
        raise PrintConfigurationRejected("INVALID_TENANT")
    if type(actor_user_id) is not int or actor_user_id != tenant_id or actor_employer_id is not None:
        raise PrintConfigurationRejected("OWNER_REQUIRED")
    if not isinstance(raw, dict) or set(raw) != {
        "schemaVersion", "mode", "stationIds", "printerIds"
    }:
        raise PrintConfigurationRejected("INVALID_SCHEMA")
    if type(raw["schemaVersion"]) is not int or raw["schemaVersion"] != _SCHEMA_VERSION:
        raise PrintConfigurationRejected("UNSUPPORTED_SCHEMA")
    mode = raw["mode"]
    if not isinstance(mode, str) or mode not in _ALLOWED_MODES:
        raise PrintConfigurationRejected("INVALID_MODE")

    # Disabling erases the allowlists by construction; a malformed or hidden
    # supplied target is not silently retained for accidental later enabling.
    if mode == "disabled":
        if raw["stationIds"] != [] or raw["printerIds"] != []:
            raise PrintConfigurationRejected("DISABLED_MUST_CLEAR_TARGETS")
        return CabinetPrintPolicy(tenant_id=tenant_id)

    station_ids = _ids(raw["stationIds"], max_count=_MAX_STATIONS)
    printer_ids = _ids(raw["printerIds"], max_count=_MAX_PRINTERS)
    for station_id in station_ids:
        station = trusted_stations.get(station_id)
        if (
            station is None or station.station_id != station_id
            or station.tenant_id != tenant_id or not station.enabled
            or station.revoked or station.experience != "station"
        ):
            raise PrintConfigurationRejected("STATION_NOT_TRUSTED")

    selected: list[PrinterTarget] = []
    locations: set[str] = set()
    for printer_id in printer_ids:
        inventory = trusted_printers.get(printer_id)
        if (
            inventory is None or inventory.printer_id != printer_id
            or inventory.tenant_id != tenant_id or not inventory.enabled
            or inventory.location not in {"near_station", "reception"}
        ):
            raise PrintConfigurationRejected("PRINTER_NOT_TRUSTED")
        if inventory.location == "near_station":
            if not inventory.station_id or inventory.station_id not in station_ids:
                raise PrintConfigurationRejected("PRINTER_STATION_MISMATCH")
            # No mode can enable a shared public printer without an audited
            # independent secure-release AND private-channel witness.
            if not (inventory.secure_release_verified and inventory.private_channel_verified):
                raise PrintConfigurationRejected("PRIVATE_RELEASE_NOT_CERTIFIED")
        else:
            if inventory.station_id is not None or not inventory.staff_supervised:
                raise PrintConfigurationRejected("RECEPTION_NOT_SUPERVISED")
        selected.append(PrinterTarget(
            printer_id=printer_id, tenant_id=tenant_id,
            location=inventory.location, station_id=inventory.station_id,
            enabled=True,
            secure_release_verified=inventory.secure_release_verified,
            private_channel_verified=inventory.private_channel_verified,
            staff_supervised=inventory.staff_supervised,
        ))
        locations.add(inventory.location)

    expected = {
        "reception": {"reception"},
        "near_station": {"near_station"},
        "both": {"reception", "near_station"},
    }[mode]
    # Do not activate an unrequested route. In both mode, *both* real,
    # already-certified destinations must exist or the draft is rejected.
    if locations != expected:
        raise PrintConfigurationRejected("DESTINATIONS_INCOMPLETE")
    return CabinetPrintPolicy(
        tenant_id=tenant_id, mode=mode,
        allowed_stations=station_ids, printers=tuple(selected),
    )


def default_disabled_print_config(tenant_id: int) -> CabinetPrintPolicy:
    """Safe fallback for missing, corrupt, not-yet-migrated configuration."""
    if type(tenant_id) is not int or tenant_id <= 0:
        raise PrintConfigurationRejected("INVALID_TENANT")
    return CabinetPrintPolicy(tenant_id=tenant_id)
