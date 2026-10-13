"""04.8-B parallel LAB: owner-owned catalogue of UNVERIFIED printers.

An inventory draft is never a certificate. Nothing in this module turns a
printer on, releases paper, enables print policy or contacts a device.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import (
    CheckConstraint, Column, DateTime, Integer, MetaData, String, Table,
    insert, select, update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from backend.services.station_document_print_configuration import TrustedPrinter

SCHEMA = MetaData()
draft_printers = Table(
    "station_print_printer_drafts_lab", SCHEMA,
    Column("tenant_id", Integer, primary_key=True),
    Column("printer_id", String(80), primary_key=True),
    Column("location", String(16), nullable=False),
    Column("station_id", String(80), nullable=True),
    Column("revision", Integer, nullable=False),
    Column("updated_by", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("location IN ('reception','near_station')", name="ck_print_draft_location"),
    CheckConstraint("revision > 0", name="ck_print_draft_revision"),
    CheckConstraint(
        "(location = 'reception' AND station_id IS NULL) OR "
        "(location = 'near_station' AND station_id IS NOT NULL)",
        name="ck_print_draft_station_binding",
    ),
)
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")


class PrinterDraftRejected(ValueError):
    pass


class PrinterDraftConflict(ValueError):
    pass


@dataclass(frozen=True)
class PrinterDraft:
    tenant_id: int
    printer_id: str
    location: str
    station_id: str | None
    revision: int
    certification: str = "unverified"
    enabled: bool = False


def _validate_owner(tenant_id: object, actor_id: object, employer_id: object) -> None:
    if (
        type(tenant_id) is not int or tenant_id <= 0
        or type(actor_id) is not int or actor_id != tenant_id
        or employer_id is not None
    ):
        raise PrinterDraftRejected("OWNER_REQUIRED")


def register_unverified_draft(
    engine: Engine,
    *,
    tenant_id: int,
    actor_user_id: int,
    actor_employer_id: int | None,
    printer_id: str,
    location: str,
    station_id: str | None,
    expected_revision: int,
) -> int:
    """Atomic per-tenant optimistic-write draft; never accepts any attestations."""
    _validate_owner(tenant_id, actor_user_id, actor_employer_id)
    if (
        type(printer_id) is not str or not IDENTIFIER.fullmatch(printer_id)
        or location not in ("reception", "near_station")
        or (location == "reception" and station_id is not None)
        or (location == "near_station" and (
            type(station_id) is not str or not IDENTIFIER.fullmatch(station_id)
        ))
    ):
        raise PrinterDraftRejected("INVALID_PRINTER_DRAFT")
    if type(expected_revision) is not int or expected_revision < 0:
        raise PrinterDraftRejected("INVALID_REVISION")
    rev = expected_revision + 1
    now = datetime.now(timezone.utc)
    try:
        with engine.begin() as conn:
            if expected_revision == 0:
                conn.execute(insert(draft_printers).values(
                    tenant_id=tenant_id, printer_id=printer_id,
                    location=location, station_id=station_id,
                    revision=rev, updated_by=actor_user_id, updated_at=now,
                ))
            else:
                changed = conn.execute(
                    update(draft_printers)
                    .where(
                        draft_printers.c.tenant_id == tenant_id,
                        draft_printers.c.printer_id == printer_id,
                        draft_printers.c.revision == expected_revision,
                    )
                    .values(
                        location=location, station_id=station_id, revision=rev,
                        updated_by=actor_user_id, updated_at=now,
                    )
                )
                if changed.rowcount != 1:
                    raise PrinterDraftConflict("STALE_REVISION")
    except IntegrityError as exc:
        raise PrinterDraftConflict("DUPLICATE_OR_CONCURRENT") from exc
    return rev


def list_unverified_drafts(engine: Engine, *, tenant_id: int) -> tuple[PrinterDraft, ...]:
    if type(tenant_id) is not int or tenant_id <= 0:
        raise PrinterDraftRejected("INVALID_TENANT")
    with engine.connect() as conn:
        rows = conn.execute(
            select(draft_printers)
            .where(draft_printers.c.tenant_id == tenant_id)
            .order_by(draft_printers.c.printer_id)
        ).mappings().all()
    return tuple(PrinterDraft(
        tenant_id=tenant_id, printer_id=row["printer_id"],
        location=row["location"], station_id=row["station_id"],
        revision=row["revision"],
    ) for row in rows)


def unverified_drafts_are_never_trusted(drafts: tuple[PrinterDraft, ...]) -> dict[str, TrustedPrinter]:
    """Even existing draft records cannot self-certify through the owner UI."""
    inventory = {}
    for draft in drafts:
        if draft.printer_id in inventory:
            raise PrinterDraftRejected("DUPLICATE_INVENTORY")
        inventory[draft.printer_id] = TrustedPrinter(
            printer_id=draft.printer_id, tenant_id=draft.tenant_id,
            location=draft.location, station_id=draft.station_id,
            enabled=False, secure_release_verified=False,
            private_channel_verified=False, staff_supervised=False,
        )
    return inventory
