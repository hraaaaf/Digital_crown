from __future__ import annotations

from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Float, Boolean, Text,
    ForeignKey, UniqueConstraint, select, insert, update
)
from sqlalchemy.orm import Session

from backend import models

metadata = MetaData()

specialties = Table(
    "cabinet_specialties", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("employer_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("name", String(100), nullable=False),
    Column("color", String(20), nullable=True),
    UniqueConstraint("employer_id", "name", name="uq_cabinet_specialty_name"),
)

pathologies = Table(
    "cabinet_pathologies", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("employer_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("specialty_id", Integer, ForeignKey("cabinet_specialties.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("name", String(255), nullable=False),
    Column("description", Text, nullable=True),
    Column("is_active", Boolean, nullable=False, default=True),
    UniqueConstraint("employer_id", "specialty_id", "name", name="uq_cabinet_pathology_name"),
)

acts = Table(
    "cabinet_catalog_acts", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("employer_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("specialty_id", Integer, ForeignKey("cabinet_specialties.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("name", String(255), nullable=False),
    Column("code", String(50), nullable=True),
    Column("base_price", Float, nullable=False, default=0.0),
    Column("color", String(20), nullable=True),
    Column("is_active", Boolean, nullable=False, default=True),
    UniqueConstraint("employer_id", "code", name="uq_cabinet_act_code"),
)


def ensure_schema(db: Session) -> None:
    metadata.create_all(bind=db.get_bind(), tables=[specialties, pathologies, acts])


def _root_owners(db: Session) -> list[int]:
    rows = db.query(models.User.id).filter(models.User.employer_id.is_(None)).all()
    return [int(r[0]) for r in rows]


def claim_legacy_if_unambiguous(db: Session) -> None:
    """Copy legacy global catalog only when exactly one root cabinet exists.

    With several cabinets ownership is unknowable, so legacy rows remain untouched
    and are not exposed through the tenant-scoped API.
    """
    ensure_schema(db)
    owners = _root_owners(db)
    if len(owners) != 1:
        return
    employer_id = owners[0]
    existing = db.execute(select(specialties.c.id).limit(1)).first()
    if existing:
        return

    id_map: dict[int, int] = {}
    for legacy in db.query(models.Specialty).order_by(models.Specialty.id).all():
        res = db.execute(insert(specialties).values(
            employer_id=employer_id, name=legacy.name, color=legacy.color
        ))
        new_id = int(res.inserted_primary_key[0])
        id_map[int(legacy.id)] = new_id

    for legacy in db.query(models.Pathology).order_by(models.Pathology.id).all():
        new_specialty = id_map.get(int(legacy.specialty_id))
        if new_specialty is None:
            continue
        db.execute(insert(pathologies).values(
            employer_id=employer_id,
            specialty_id=new_specialty,
            name=legacy.name,
            description=legacy.description,
            is_active=bool(legacy.is_active),
        ))

    for legacy in db.query(models.CatalogAct).order_by(models.CatalogAct.id).all():
        new_specialty = id_map.get(int(legacy.specialty_id))
        if new_specialty is None:
            continue
        db.execute(insert(acts).values(
            employer_id=employer_id,
            specialty_id=new_specialty,
            name=legacy.name,
            code=legacy.code,
            base_price=float(legacy.base_price or 0.0),
            color=legacy.color,
            is_active=bool(legacy.is_active),
        ))
    db.commit()


def list_catalog(db: Session, employer_id: int) -> list[dict]:
    claim_legacy_if_unambiguous(db)
    specs = db.execute(
        select(specialties).where(specialties.c.employer_id == employer_id).order_by(specialties.c.id)
    ).mappings().all()
    result = []
    for spec in specs:
        sid = int(spec["id"])
        paths = db.execute(select(pathologies).where(
            pathologies.c.employer_id == employer_id,
            pathologies.c.specialty_id == sid,
        )).mappings().all()
        catalog_acts = db.execute(select(acts).where(
            acts.c.employer_id == employer_id,
            acts.c.specialty_id == sid,
        )).mappings().all()
        result.append({
            "id": sid,
            "name": spec["name"],
            "color": spec["color"],
            "pathologies": [dict(x) for x in paths],
            "acts": [dict(x) for x in catalog_acts],
        })
    return result


def get_owned(db: Session, table: Table, row_id: int, employer_id: int):
    ensure_schema(db)
    return db.execute(select(table).where(
        table.c.id == row_id, table.c.employer_id == employer_id
    )).mappings().first()


def create_specialty(db: Session, employer_id: int, payload: dict) -> dict:
    ensure_schema(db)
    res = db.execute(insert(specialties).values(employer_id=employer_id, **payload))
    db.commit()
    return dict(get_owned(db, specialties, int(res.inserted_primary_key[0]), employer_id))


def create_pathology(db: Session, employer_id: int, specialty_id: int, payload: dict) -> dict | None:
    if not get_owned(db, specialties, specialty_id, employer_id):
        return None
    res = db.execute(insert(pathologies).values(employer_id=employer_id, specialty_id=specialty_id, **payload))
    db.commit()
    return dict(get_owned(db, pathologies, int(res.inserted_primary_key[0]), employer_id))


def create_act(db: Session, employer_id: int, specialty_id: int, payload: dict) -> dict | None:
    if not get_owned(db, specialties, specialty_id, employer_id):
        return None
    res = db.execute(insert(acts).values(employer_id=employer_id, specialty_id=specialty_id, **payload))
    db.commit()
    return dict(get_owned(db, acts, int(res.inserted_primary_key[0]), employer_id))


def update_owned(db: Session, table: Table, row_id: int, employer_id: int, payload: dict) -> dict | None:
    if not get_owned(db, table, row_id, employer_id):
        return None
    if payload:
        db.execute(update(table).where(
            table.c.id == row_id, table.c.employer_id == employer_id
        ).values(**payload))
        db.commit()
    row = get_owned(db, table, row_id, employer_id)
    return dict(row) if row else None
