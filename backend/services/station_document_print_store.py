"""LOT04.8-B2a: isolated SQLAlchemy Core store for owner print configuration.

No API, production migration, printer control, document reads or print dispatch.
The caller MUST obtain actor identity and device certification inventory from
trusted Cabinet server/DB state, not from untrusted browser request fields.
Schema is declared for isolated in-memory lab tests; CREATE ALL is NOT called
by this module and never allowed against a live Cabinet database.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from sqlalchemy import (
    CheckConstraint, Column, DateTime, ForeignKey, Integer, MetaData,
    String, Table, delete, insert, select, update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from backend.services.station_document_print_configuration import (
    PrintConfigurationRejected, TrustedPrinter, TrustedStation,
    compile_owner_print_config, default_disabled_print_config,
)
from backend.services.station_document_print_policy import CabinetPrintPolicy


# Separate from backend.models.Base.metadata until Alembic HEAD and the
# production schema/tenant ownership constraints have been audited.
schema = MetaData()
configuration = Table(
    "station_print_configurations", schema,
    Column("tenant_id", Integer, primary_key=True),
    Column("mode", String(16), nullable=False, server_default="disabled"),
    Column("revision", Integer, nullable=False),
    Column("updated_by_user_id", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("mode IN ('disabled','reception','near_station','both')", name="ck_station_print_mode"),
    CheckConstraint("revision > 0", name="ck_station_print_revision"),
)
stations = Table(
    "station_print_config_stations", schema,
    Column("tenant_id", Integer, ForeignKey("station_print_configurations.tenant_id", ondelete="CASCADE"), primary_key=True),
    Column("station_id", String(80), primary_key=True),
)
printers = Table(
    "station_print_config_printers", schema,
    Column("tenant_id", Integer, ForeignKey("station_print_configurations.tenant_id", ondelete="CASCADE"), primary_key=True),
    Column("printer_id", String(80), primary_key=True),
)
audit = Table(
    "station_print_config_audit", schema,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tenant_id", Integer, nullable=False),
    Column("revision", Integer, nullable=False),
    Column("actor_user_id", Integer, nullable=False),
    Column("mode", String(16), nullable=False),
    Column("changed_at", DateTime(timezone=True), nullable=False),
)


class PrintConfigurationConflict(ValueError):
    """A stale revision, duplicate initial insert or concurrent edit was denied."""


@dataclass(frozen=True)
class LoadedPrintConfiguration:
    policy: CabinetPrintPolicy
    revision: int
    reason: str

    @property
    def enabled(self) -> bool:
        return self.reason == "eligible" and self.policy.mode != "disabled"


def save_owner_configuration(
    engine: Engine,
    *,
    tenant_id: int,
    actor_user_id: int,
    actor_employer_id: int | None,
    expected_revision: int,
    proposal: object,
    trusted_stations: Mapping[str, TrustedStation],
    trusted_printers: Mapping[str, TrustedPrinter],
) -> int:
    """Atomic compare-and-swap save + allowlists + audit, never print activation.

    The trusted inventories are *snapshot* inputs. They MUST be queried again
    on every operational read and at the time of future job authorization.
    The absent row has virtual revision zero; first successful save has one.
    """
    if type(expected_revision) is not int or expected_revision < 0:
        raise PrintConfigurationRejected("INVALID_EXPECTED_REVISION")
    candidate = compile_owner_print_config(
        tenant_id=tenant_id, actor_user_id=actor_user_id,
        actor_employer_id=actor_employer_id, raw=proposal,
        trusted_stations=trusted_stations, trusted_printers=trusted_printers,
    )
    stamp = datetime.now(timezone.utc)
    next_revision = expected_revision + 1
    try:
        with engine.begin() as connection:
            row = connection.execute(
                select(configuration.c.revision).where(
                    configuration.c.tenant_id == tenant_id,
                ),
            ).scalar_one_or_none()
            if row is None:
                if expected_revision != 0:
                    raise PrintConfigurationConflict("STALE_REVISION")
                connection.execute(insert(configuration).values(
                    tenant_id=tenant_id, mode=candidate.mode,
                    revision=next_revision, updated_by_user_id=actor_user_id,
                    updated_at=stamp,
                ))
            else:
                if row != expected_revision:
                    raise PrintConfigurationConflict("STALE_REVISION")
                changed = connection.execute(
                    update(configuration)
                    .where(
                        configuration.c.tenant_id == tenant_id,
                        configuration.c.revision == expected_revision,
                    )
                    .values(
                        mode=candidate.mode, revision=next_revision,
                        updated_by_user_id=actor_user_id, updated_at=stamp,
                    ),
                )
                if changed.rowcount != 1:
                    raise PrintConfigurationConflict("STALE_REVISION")
            connection.execute(delete(stations).where(stations.c.tenant_id == tenant_id))
            connection.execute(delete(printers).where(printers.c.tenant_id == tenant_id))
            if candidate.allowed_stations:
                connection.execute(insert(stations), [
                    {"tenant_id": tenant_id, "station_id": station_id}
                    for station_id in candidate.allowed_stations
                ])
            if candidate.printers:
                connection.execute(insert(printers), [
                    {"tenant_id": tenant_id, "printer_id": printer.printer_id}
                    for printer in candidate.printers
                ])
            connection.execute(insert(audit).values(
                tenant_id=tenant_id, revision=next_revision,
                actor_user_id=actor_user_id, mode=candidate.mode,
                changed_at=stamp,
            ))
    except IntegrityError as exc:
        # Includes a concurrent first insert racing the unique tenant PK.
        raise PrintConfigurationConflict("CONCURRENT_WRITE") from exc
    return next_revision


def load_effective_configuration(
    engine: Engine,
    *,
    tenant_id: int,
    trusted_stations: Mapping[str, TrustedStation],
    trusted_printers: Mapping[str, TrustedPrinter],
) -> LoadedPrintConfiguration:
    """Recompile against CURRENT trusted inventory; fail closed on drift.

    Read API is for an authenticated Cabinet service, not a Station/Patient
    endpoint. DB errors deliberately propagate: future callers must deny
    printing on errors, never substitute a permissive cached decision.
    """
    disabled = default_disabled_print_config(tenant_id)
    with engine.connect() as connection:
        row = connection.execute(
            select(configuration.c.mode, configuration.c.revision)
            .where(configuration.c.tenant_id == tenant_id)
        ).one_or_none()
        if row is None:
            return LoadedPrintConfiguration(disabled, 0, "not_configured")
        raw = {
            "schemaVersion": 1,
            "mode": row.mode,
            "stationIds": list(connection.execute(
                select(stations.c.station_id)
                .where(stations.c.tenant_id == tenant_id)
                .order_by(stations.c.station_id)
            ).scalars()),
            "printerIds": list(connection.execute(
                select(printers.c.printer_id)
                .where(printers.c.tenant_id == tenant_id)
                .order_by(printers.c.printer_id)
            ).scalars()),
        }
    if row.mode == "disabled":
        if raw["stationIds"] or raw["printerIds"]:
            return LoadedPrintConfiguration(disabled, row.revision, "configuration_invalid")
        return LoadedPrintConfiguration(disabled, row.revision, "printing_disabled")
    try:
        # This owner identity is exclusively an internal validation argument,
        # never authentication: access control is required at the API boundary.
        policy = compile_owner_print_config(
            tenant_id=tenant_id, actor_user_id=tenant_id,
            actor_employer_id=None, raw=raw,
            trusted_stations=trusted_stations, trusted_printers=trusted_printers,
        )
    except PrintConfigurationRejected:
        return LoadedPrintConfiguration(disabled, row.revision, "inventory_changed")
    return LoadedPrintConfiguration(policy, row.revision, "eligible")
