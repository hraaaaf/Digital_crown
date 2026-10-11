"""PostgreSQL-only adversarial concurrent authorization proof for FUE-0 04.3.

This script uses an isolated disposable CI PostgreSQL service and synthetic users,
patient and PDFs; it cannot use the production database. No pytest/conftest here,
because conftest deliberately forces SQLite.
"""
from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

url = os.environ.get("FUE_PG_URL", "")
if not url.startswith("postgresql"):
    raise SystemExit("FUE_PG_URL required: must use isolated PostgreSQL, not SQLite")
if os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true":
    raise SystemExit("DIGITALCROWN_ISOLATED_RUNTIME=true required")
if os.environ.get("ENVIRONMENT") != "test":
    raise SystemExit("ENVIRONMENT=test required")

from backend import models  # noqa: E402
from backend.models_document_provenance_p3 import install_document_provenance_p3  # noqa: E402
from backend.services.station_care_sheet import (  # noqa: E402
    AUTHORIZE_ACTION, authorize_withdrawal, record_trusted_finalization,
)

engine = create_engine(url, pool_size=10, max_overflow=3, pool_pre_ping=True)
install_document_provenance_p3()
models.Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

with SessionLocal() as db:
    owner = models.User(
        email="fue043+ci@example.invalid", hashed_password="synthetic-only",
        role=models.UserRole.DENTISTE, nom_complet="FUE 043 Synthetic",
        is_active=True, is_licensed=True,
    )
    db.add(owner)
    db.flush()
    patient = models.Patient(
        numero_dossier="FUE043-PG", nom="Test", prenom="Concurrency",
        date_naissance=datetime(1990, 1, 1), sexe="F", employer_id=owner.id,
    )
    db.add(patient)
    db.flush()
    synthetic_pdf = b"%PDF-1.4\\n% synthetic FUE PDF\\n%%EOF\\n"
    digest = hashlib.sha256(synthetic_pdf).hexdigest()
    document = models.DocumentArchive(
        patient_id=patient.id, uploaded_by_id=owner.id,
        document_type=models.DocumentType.AUTRE,
        filename="Feuille_soins_CNSS_FUE.pdf", original_filename="Feuille_soins_CNSS_FUE.pdf",
        document_group_id="fue043-postgresql-multiprocess-proof",
        version_number=1, is_latest_version=True,
        file_hash=digest, file_size=len(synthetic_pdf), file_path="static/archives/fue043.pdf",
        status=models.DocumentStatus.ACTIF,
        clinical_data={
            "kind": "INSURANCE_SUBMISSION",
            "validated_by_practitioner_id": owner.id,
            "validated_at": "2026-10-11T10:00:00",
            "draft": {"status": "VALIDATED"},
            "render_evidence": {"renderer": "PDF_OVERLAY_V1", "rendered_pdf_sha256": digest},
        },
        is_accounted=False, is_collected=False,
        payment_status=models.PaiementStatut.EN_ATTENTE,
    )
    db.add(document)
    db.commit()
    doc_id, owner_id, patient_id = document.id, owner.id, patient.id
    record_trusted_finalization(db, document, employer_id=owner_id,
                                practitioner_id=owner_id, expected_patient_id=patient_id)

workers = 8
barrier = Barrier(workers)
def authorize_one(index: int) -> dict:
    with SessionLocal() as db:
        archive = db.get(models.DocumentArchive, doc_id)
        if archive is None:
            raise AssertionError("Synthetic document vanished")
        barrier.wait(timeout=30)
        created = authorize_withdrawal(
            db, archive, employer_id=owner_id, user_id=owner_id,
            ip_address="127.0.0.1",
        )
        return {"worker": index, "created": created}

with ThreadPoolExecutor(max_workers=workers) as pool:
    results = list(pool.map(authorize_one, range(workers)))
with SessionLocal() as db:
    events = db.scalars(select(models.AuditLog).where(
        models.AuditLog.action == AUTHORIZE_ACTION,
        models.AuditLog.resource_type == "DocumentArchive",
        models.AuditLog.resource_id == str(doc_id),
    )).all()
    assert len(events) == 1, f"Expected exactly one audit event, found {len(events)}"
    assert events[0].employer_id == owner_id
    assert events[0].user_id == owner_id
    assert f"patient_id={patient_id};sha256={digest}" in events[0].details
    assert sum(bool(row["created"]) for row in results) == 1, results

report = {
    "classification": "PG_REAL_CONCURRENT_DB_TEST",
    "status": "PASS",
    "workers": workers,
    "created": sum(row["created"] for row in results),
    "deduplicated": sum(not row["created"] for row in results),
    "audit_events": len(events),
    "synthetic": True,
    "db": "PostgreSQL isolated GitHub Actions service",
    "product_head": os.environ.get("FUE_EVALUATED_SHA"),
}
print("FUE_PG_CONCURRENCY " + json.dumps(report, sort_keys=True))
out = os.environ.get("FUE_PG_REPORT")
if out:
    from pathlib import Path
    report_path = Path(out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
engine.dispose()
