"""Safe P5 backfill from legacy CabinetConfig practitioner copies to canonical User fields.

This migration is intentionally conservative:
- only fills an empty canonical User field from an unambiguous legacy practitioner field;
- never overwrites a non-empty User value;
- never classifies legacy INPE;
- never parses/moves legal IDs, contacts, footer or custom headers.

It is safe to run repeatedly at startup.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend import models


@dataclass(frozen=True)
class LegacyIdentityMigrationReport:
    scanned: int = 0
    practitioner_fr_backfilled: int = 0
    practitioner_ar_backfilled: int = 0
    practitioner_fr_conflicts: int = 0
    practitioner_ar_conflicts: int = 0
    missing_owner: int = 0

    @property
    def changed(self) -> int:
        return self.practitioner_fr_backfilled + self.practitioner_ar_backfilled


def _clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def migrate_legacy_identity_values(db: Session) -> LegacyIdentityMigrationReport:
    """Backfill only practitioner names whose canonical User target is empty.

    Legacy CabinetConfig values are deliberately preserved after a successful backfill so
    rollback and legacy document compatibility remain possible until P8 closeout. Conflicts
    are counted but never resolved automatically.
    """
    scanned = 0
    fr_backfilled = 0
    ar_backfilled = 0
    fr_conflicts = 0
    ar_conflicts = 0
    missing_owner = 0

    cabinets = db.query(models.CabinetConfig).all()
    for cabinet in cabinets:
        scanned += 1
        owner = db.query(models.User).filter(models.User.id == cabinet.owner_id).first()
        if owner is None:
            missing_owner += 1
            continue

        legacy_fr = _clean(cabinet.nom_praticien)
        canonical_fr = _clean(owner.nom_complet)
        if legacy_fr and not canonical_fr:
            owner.nom_complet = legacy_fr
            fr_backfilled += 1
        elif legacy_fr and canonical_fr and legacy_fr != canonical_fr:
            fr_conflicts += 1

        legacy_ar = _clean(cabinet.nom_praticien_ar)
        canonical_ar = _clean(getattr(owner, "nom_complet_ar", None))
        if legacy_ar and not canonical_ar:
            owner.nom_complet_ar = legacy_ar
            ar_backfilled += 1
        elif legacy_ar and canonical_ar and legacy_ar != canonical_ar:
            ar_conflicts += 1

    if fr_backfilled or ar_backfilled:
        db.commit()

    return LegacyIdentityMigrationReport(
        scanned=scanned,
        practitioner_fr_backfilled=fr_backfilled,
        practitioner_ar_backfilled=ar_backfilled,
        practitioner_fr_conflicts=fr_conflicts,
        practitioner_ar_conflicts=ar_conflicts,
        missing_owner=missing_owner,
    )
