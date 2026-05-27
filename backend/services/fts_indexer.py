import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend import models

logger = logging.getLogger(__name__)


def index_patient(patient_id: int, db: Session) -> None:
    """
    Index all available clinical content for a patient into the FTS5 table.
    Clears existing entries before re-indexing to keep data fresh.
    """
    if db.bind.dialect.name != "sqlite":
        return

    try:
        # Clear existing entries for this patient
        db.execute(text("DELETE FROM patient_fts WHERE patient_id = :pid"), {"pid": patient_id})

        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            return

        entries: list[tuple[int, str, str, str]] = []

        # Medical history
        if patient.antecedents_medicaux:
            entries.append((patient_id, patient.antecedents_medicaux, "antecedent", ""))

        # Clinical acts
        acts = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).all()
        for a in acts:
            entries.append((patient_id, a.libelle, "acte", a.date_debut.strftime("%Y-%m-%d")))

        # Panoramic findings
        panoramics = (
            db.query(models.PanoramicAnalysis)
            .filter(models.PanoramicAnalysis.patient_id == patient_id)
            .all()
        )
        for p in panoramics:
            detections = (p.detections_data or {}).get("detections", [])
            for d in detections:
                label = d.get("class_name") or d.get("label", "")
                if label:
                    entries.append((patient_id, label, "panoramic", p.created_at.strftime("%Y-%m-%d")))

        if entries:
            db.execute(
                text(
                    "INSERT INTO patient_fts (patient_id, content, content_type, date_str) "
                    "VALUES (:pid, :content, :ctype, :dstr)"
                ),
                [{"pid": pid, "content": c, "ctype": ct, "dstr": ds} for pid, c, ct, ds in entries],
            )

        # Mark as indexed
        db.execute(
            text(
                "INSERT OR REPLACE INTO patient_fts_indexed (patient_id, indexed_at) "
                "VALUES (:pid, :now)"
            ),
            {"pid": patient_id, "now": datetime.now().isoformat()},
        )
        db.commit()
        logger.debug("FTSIndexer: indexed %d entries for patient %d", len(entries), patient_id)
    except Exception as e:
        logger.warning("FTSIndexer: failed for patient %d: %s", patient_id, e)
        db.rollback()


def search_patient(query: str, patient_id: int, db: Session, limit: int = 5) -> list[str]:
    """Full-text search within a patient's indexed clinical content."""
    if db.bind.dialect.name != "sqlite":
        return []

    try:
        rows = db.execute(
            text(
                "SELECT content FROM patient_fts "
                "WHERE patient_fts MATCH :q AND patient_id = :pid "
                "ORDER BY rank LIMIT :lim"
            ),
            {"q": query, "pid": patient_id, "lim": limit},
        ).fetchall()
        return [r[0] for r in rows]
    except Exception as e:
        logger.warning("FTSIndexer: search failed: %s", e)
        return []


def bulk_index_unindexed_patients(db: Session) -> None:
    """Index all patients that have never been indexed (background startup task)."""
    if db.bind.dialect.name != "sqlite":
        logger.debug("FTSIndexer: PostgreSQL detected, skipping FTS5 indexing.")
        return

    try:
        result = db.execute(
            text(
                "SELECT id FROM patients WHERE id NOT IN "
                "(SELECT patient_id FROM patient_fts_indexed)"
            )
        ).fetchall()
        for row in result:
            index_patient(row[0], db)
        logger.info("FTSIndexer: bulk-indexed %d patients", len(result))
    except Exception as e:
        logger.warning("FTSIndexer: bulk index failed: %s", e)
