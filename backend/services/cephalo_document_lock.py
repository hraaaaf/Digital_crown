"""Transaction boundary for one versioned cephalometric PDF archive.

The same CephaloAnalysis database row is the serialization point for PDF
creation and landmark edits. SQLite/SQLCipher need a write intent, while
PostgreSQL supports SELECT FOR UPDATE. This module never commits: its caller
must hold the transaction until the archive row is committed.
"""
from __future__ import annotations

import hashlib
import json
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


def render_payload_digest(*, clinical_data: object, ai_diagnostic: object) -> str:
    """Stable identity for all client-adjustable report rendering inputs."""
    payload = {"clinical_data": clinical_data, "ai_diagnostic": ai_diagnostic}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def already_archived_pdf(
    db: Session, *, patient_id: int, analysis_id: int, revision: int,
    payload_digest: str,
) -> tuple[Path, bytes] | None:
    """Snapshot verified PDF bytes while locked, never reopen path to stream them.

    FileResponse(path=...) would re-open an unverified file *after* rollback
    and after this SHA check: deleting/replacing it during that gap is TOCTOU.
    """
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
    # A scientific revision does not version the clinician's optional free-text
    # payload. Never silently replay a PDF whose presentation inputs differ.
    if row.clinical_data.get("cephalo_archive_payload_digest") != payload_digest:
        raise HTTPException(
            status_code=409,
            detail="Une archive existe avec un autre contexte clinique : changement de révision requis",
        )
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
    return file_path, content
