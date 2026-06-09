"""
Script de récupération des 101 documents orphelins.
Régénère les PDFs depuis la clinical_data stockée en DB,
met à jour file_path, et archive proprement dans la nouvelle structure.

Usage :
    python -m backend.scripts.recover_documents [--dry-run]
"""
import sys
import os
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Ajouter le répertoire racine au path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.database import SessionLocal
from backend import models, schemas
from backend.services.document_factory import DocumentFactory
from backend.services.archive_service import ArchiveService, ARCHIVE_BASE_DIR
from backend.core.paths import AppPaths

MEDIA_DIR = AppPaths.get_user_data_dir() / "media"

SCHEMA_MAP = {
    models.DocumentType.ORDONNANCE:     schemas.OrdonnanceData,
    models.DocumentType.CERTIFICAT:     schemas.CertificatData,
    models.DocumentType.NOTE_HONORAIRES: schemas.HonorairesData,
    models.DocumentType.DEVIS:          schemas.DevisData,
    models.DocumentType.DOCUMENT_LIBRE: schemas.LibreData,
}

FACTORY_METHOD_MAP = {
    models.DocumentType.ORDONNANCE:      "create_ordonnance",
    models.DocumentType.CERTIFICAT:      "create_certificat",
    models.DocumentType.NOTE_HONORAIRES: "create_note_honoraires",
    models.DocumentType.DEVIS:           "create_devis",
    models.DocumentType.DOCUMENT_LIBRE:  "create_document_libre",
}


def recover(dry_run: bool = False):
    db = SessionLocal()
    try:
        orphans = (
            db.query(models.DocumentArchive)
            .filter(
                models.DocumentArchive.status == models.DocumentStatus.ACTIF,
                models.DocumentArchive.file_path.like("%Benmoussa%"),
            )
            .order_by(models.DocumentArchive.id)
            .all()
        )
        logger.info(f"Documents orphelins trouvés : {len(orphans)}")

        doc_factory = DocumentFactory(
            output_dir=str(MEDIA_DIR / "documents"),
            static_dir=str(MEDIA_DIR),
        )

        ok, failed, skipped = 0, 0, 0

        for doc in orphans:
            patient = db.query(models.Patient).filter(
                models.Patient.id == doc.patient_id
            ).first()
            if not patient:
                logger.warning(f"  [SKIP] Doc {doc.id} — patient {doc.patient_id} introuvable")
                skipped += 1
                continue

            schema_cls = SCHEMA_MAP.get(doc.document_type)
            method_name = FACTORY_METHOD_MAP.get(doc.document_type)

            if not schema_cls or not method_name:
                logger.warning(f"  [SKIP] Doc {doc.id} — type non supporté : {doc.document_type}")
                skipped += 1
                continue

            if not doc.clinical_data:
                logger.warning(f"  [SKIP] Doc {doc.id} — clinical_data vide")
                skipped += 1
                continue

            try:
                # Construire le schéma Pydantic depuis clinical_data
                data_obj = schema_cls.model_validate(doc.clinical_data)
            except Exception as e:
                logger.warning(f"  [SKIP] Doc {doc.id} ({doc.document_type.value}) — schéma invalide : {e}")
                skipped += 1
                continue

            logger.info(
                f"  [{'DRY' if dry_run else 'GEN'}] {doc.id} | {doc.document_type.value} | "
                f"{patient.prenom} {patient.nom} | {doc.created_at.strftime('%Y-%m-%d')}"
            )

            if dry_run:
                ok += 1
                continue

            try:
                method = getattr(doc_factory, method_name)
                user_id = doc.uploaded_by_id or 1
                new_pdf_path = method(patient, data_obj, db, user_id)

                # Lire le PDF généré
                with open(new_pdf_path, "rb") as f:
                    pdf_content = f.read()

                # Archiver proprement dans la nouvelle structure
                archive_svc = ArchiveService(db)
                storage_path = archive_svc._get_storage_path(
                    patient.id, doc.document_type,
                    os.path.basename(new_pdf_path)
                )
                with open(storage_path, "wb") as f:
                    f.write(pdf_content)

                # Mettre à jour le file_path en DB
                new_relative = ("static/archives/" + str(
                    storage_path.relative_to(ARCHIVE_BASE_DIR)
                )).replace("\\", "/")

                doc.file_path = new_relative
                db.add(doc)
                db.commit()

                # Nettoyer le PDF temporaire
                try:
                    os.remove(new_pdf_path)
                except OSError:
                    pass

                logger.info(f"    ✓ → {new_relative}")
                ok += 1

            except Exception as e:
                logger.error(f"  [FAIL] Doc {doc.id} — {e}")
                db.rollback()
                failed += 1

        logger.info(f"\n{'[DRY-RUN] ' if dry_run else ''}Résultat : {ok} récupérés | {failed} échecs | {skipped} ignorés")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Récupère les documents orphelins")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()
    recover(dry_run=args.dry_run)
