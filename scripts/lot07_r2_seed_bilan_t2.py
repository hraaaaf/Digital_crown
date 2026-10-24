"""Synthetic historical BILAN fixture for isolated Chromium DEC-R2 E2E only.

NEVER RUN against a real cabinet, Production or anything but t2-runtime-cert.db.
No app endpoint can create a BILAN: this explicitly creates a disposable
classified archive and PDF to verify that an R-only UI can read it.
"""
import os
from hashlib import sha256
from pathlib import Path

if (os.environ.get("ENVIRONMENT") != "test"
    or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1"
    or os.environ.get("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db"
    or not os.environ.get("T2_PASSWORD")
):
    raise SystemExit("REFUSED: synthetic T2 BILAN requires isolated CI and T2 password")

db_file = Path("t2-runtime-cert.db").resolve()
if not db_file.is_file() or db_file.name != "t2-runtime-cert.db":
    raise SystemExit("REFUSED: no exact disposable SQLite DB")

from backend import database, models
from backend.core.media_paths import get_media_root

with database.SessionLocal() as db:
    owner = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").one()
    patient = db.query(models.Patient).filter(
        models.Patient.employer_id == owner.id,
        models.Patient.numero_dossier == "T2-0001",
    ).one()
    assert owner.employer_id is None
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.BILAN,
    ).count() == 0, "Fresh synthetic BILAN fixture expected"

    root = (get_media_root() / "archives" / "r2-dec01-t2").resolve()
    root.mkdir(parents=True, exist_ok=True)
    pdf = b"%PDF-1.4\n1 0 obj <</Type /Catalog>> endobj\n%%EOF\n"
    target = root / "synthetic-bilan.pdf"
    target.write_bytes(pdf)
    doc = models.DocumentArchive(
        patient_id=patient.id,
        document_type=models.DocumentType.BILAN,
        original_filename="T2-historical-bilan.pdf",
        filename=target.name,
        document_group_id=f"t2-dec01-{patient.id}",
        version_number=1,
        is_latest_version=True,
        file_hash=sha256(pdf).hexdigest(),
        file_size=len(pdf),
        file_path="static/archives/r2-dec01-t2/synthetic-bilan.pdf",
        title="Bilan orthodontique T2 synthétique",
        status=models.DocumentStatus.ACTIF,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    print(f"LOT07_R2_SYNTHETIC_BILAN_SEEDED document_id={doc.id} patient_id={patient.id}")
