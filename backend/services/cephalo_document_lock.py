"""Transaction boundary for one versioned cephalometric PDF archive.

The same CephaloAnalysis database row is the serialization point for PDF
creation and landmark edits. SQLite/SQLCipher need a write intent, while
PostgreSQL supports SELECT FOR UPDATE. This module never commits: its caller
must hold the transaction until the archive row is committed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend import models


def lock_selected_cephalo_for_archive(db: Session, *, patient_id: int, analysis_id: int) -> None:
    """Acquire a DB-level lock before selecting/rendering; never rely on process locks."""
    try:
        if db.get_bind().dialect.name == "sqlite":
            # A rendering transaction may legitimately hold the single SQLite
            # writer lock longer than SQLite's 5s default busy timeout.
            # Bounded wait permits idempotent replay instead of spurious 409.
            db.connection().exec_driver_sql("PRAGMA busy_timeout = 30000")
            # SQLite ignores SELECT FOR UPDATE. A no-op write obtains its unique
            # writer lock across connections and processes, including SQLCipher.
            # The existing image path is unchanged; no scientific data is mutated.
            outcome = db.execute(
                update(models.CephaloAnalysis)
                .where(
                    models.CephaloAnalysis.id == analysis_id,
                    models.CephaloAnalysis.patient_id == patient_id,
                )
                .values(image_original_path=models.CephaloAnalysis.image_original_path)
            )
            if outcome.rowcount != 1:
                raise HTTPException(status_code=404, detail="Analyse introuvable pour ce patient")
        else:
            # PostgreSQL row lock serializes only this analysis, not unrelated patients.
            selected = (
                db.query(models.CephaloAnalysis.id)
                .filter(
                    models.CephaloAnalysis.id == analysis_id,
                    models.CephaloAnalysis.patient_id == patient_id,
                )
                .with_for_update()
                .first()
            )
            if selected is None:
                raise HTTPException(status_code=404, detail="Analyse introuvable pour ce patient")
        # This session may already have read the study during authorization.
        # Force fresh evidence AFTER obtaining the lock.
        db.expire_all()
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Étude occupée : recommencez l'archivage après synchronisation",
        ) from exc


def already_archived_pdf(
    db: Session, *, patient_id: int, analysis_id: int, revision: int,
) -> Path | None:
    """Idempotent replay for one active study/revision, with fail-closed file integrity."""
    from backend.services import archive_service

    rows = (
        db.query(models.DocumentArchive)
        .filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.analysis_id == analysis_id,
            models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
            models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        )
        .order_by(models.DocumentArchive.id.asc())
        .all()
    )
    matching = [
        row for row in rows
        if isinstance(row.clinical_data, dict)
        and type(row.clinical_data.get("cephalo_analysis_revision")) is int
        and row.clinical_data["cephalo_analysis_revision"] == revision
        and row.clinical_data.get("cephalo_analysis_id") == analysis_id
    ]
    if not matching:
        return None
    if len(matching) != 1:
        raise HTTPException(status_code=409, detail="Archives concurrentes ambiguës : intervention nécessaire")
    row = matching[0]
    prefix = "static/archives/"
    if not row.file_path or not row.file_path.startswith(prefix):
        raise HTTPException(status_code=409, detail="Chemin d'archive incohérent")
    root = archive_service.ARCHIVE_BASE_DIR.resolve()
    file_path = (root / row.file_path[len(prefix):]).resolve()
    if not file_path.is_relative_to(root) or not file_path.is_file():
        raise HTTPException(status_code=409, detail="Fichier archivé manquant ou interdit")
    content = file_path.read_bytes()
    if (
        not content.startswith(b"%PDF")
        or len(content) != row.file_size
        or hashlib.sha256(content).hexdigest() != row.file_hash
    ):
        raise HTTPException(status_code=409, detail="Intégrité du PDF archivé non vérifiée")
    return file_path
