"""Persistent, fully fictional dental demo cabinet; manual isolated-lab seed only.

Run only against a disposable, pre-migrated SQLite DB. No real patient data.
Example:
 ENVIRONMENT=test DIGITALCROWN_ISOLATED_RUNTIME=1 \
 DATABASE_URL=sqlite:////tmp/digital-crown-demo-only.db \
 DIGITALCROWN_DEMO_ROOT=/tmp/digital-crown-demo-media \
 DIGITALCROWN_DEMO_PASSWORD='<generated-secret>' \
 python -m scripts.seed_demo_cabinet_reference

Never run against production or a database with any pre-existing non-demo users.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas


MARKER = "FICTIF - DEMONSTRATION - SANS VALEUR MEDICALE"
EMAIL = "reference-demo@digitalcrown.invalid"
CABINET = "Cabinet Digital Crown - DEMONSTRATION"
PATIENTS = (
    ("El Amrani", "Yasmine", 1998, "F", "Consultation"),
    ("Bennani", "Omar", 1984, "M", "Controle"),
    ("Idrissi", "Salma", 2001, "F", "Orthodontie"),
    ("Tazi", "Adam", 2012, "M", "Controle pediatrique"),
    ("Fassi", "Lina", 1993, "F", "Detartrage"),
    ("Alaoui", "Mehdi", 1976, "M", "Prothese"),
    ("Berrada", "Nour", 2004, "F", "Consultation"),
    ("Chraibi", "Ilyas", 1990, "M", "Endodontie"),
    ("Kettani", "Sara", 1988, "F", "Orthodontie"),
    ("Lahlou", "Rayan", 2010, "M", "Controle pediatrique"),
    ("Mansouri", "Ines", 1995, "F", "Controle"),
    ("Zerouali", "Anas", 1969, "M", "Prothese"),
)
DOCS = (
    ("ORDONNANCE", "Ordonnance DEMO"),
    ("CERTIFICAT", "Certificat DEMO"),
    ("NOTE_HONORAIRES", "Note honoraires DEMO"),
)

def _pdf(title: str, patient: str, dossier: str) -> bytes:
    output = io.BytesIO()
    page = canvas.Canvas(output, pagesize=A5)
    page.setTitle("DOCUMENT FICTIF - " + title)
    page.setFont("Helvetica-Bold", 14)
    page.drawString(35, 550, "DIGITAL CROWN - DEMO")
    page.setFont("Helvetica-Bold", 11)
    page.drawString(35, 518, title)
    page.setFont("Helvetica", 10)
    page.drawString(35, 480, "Patient fictif : " + patient)
    page.drawString(35, 459, "Dossier : " + dossier)
    page.drawString(35, 430, "Document synthetique, aucun acte reel prescrit.")
    page.setFont("Helvetica-Bold", 10)
    page.drawString(35, 80, MARKER)
    page.showPage()
    page.save()
    return output.getvalue()

def _verify_existing_fixture(db, models, owner, root: Path) -> None:
    """Never treat a partial or corrupted fixture as successfully seeded."""
    patients = db.query(models.Patient).all()
    expected = {f"DEMO-{i:04d}" for i in range(1, len(PATIENTS) + 1)}
    if len(patients) != len(PATIENTS) or {p.numero_dossier for p in patients} != expected:
        raise RuntimeError("DEMO_REFUSED: patient fixture incomplete")
    if any(p.employer_id != owner.id for p in patients):
        raise RuntimeError("DEMO_REFUSED: unexpected patient ownership")
    ids = {p.id for p in patients}
    appointments = db.query(models.Appointment).all()
    if len(appointments) != len(PATIENTS) * 3 or any(
        a.employer_id != owner.id or a.patient_id not in ids for a in appointments
    ) or any(sum(a.patient_id == p.id for a in appointments) != 3 for p in patients):
        raise RuntimeError("DEMO_REFUSED: appointment fixture incomplete")
    docs = db.query(models.DocumentArchive).all()
    if len(docs) != len(PATIENTS) * len(DOCS):
        raise RuntimeError("DEMO_REFUSED: archive fixture incomplete")
    expected_types = {models.DocumentType[name] for name, _ in DOCS}
    for patient in patients:
        patient_docs = [doc for doc in docs if doc.patient_id == patient.id]
        if len(patient_docs) != len(DOCS) or {doc.document_type for doc in patient_docs} != expected_types:
            raise RuntimeError("DEMO_REFUSED: patient archives incomplete")
    for doc in docs:
        if doc.uploaded_by_id != owner.id or not doc.file_path:
            raise RuntimeError("DEMO_REFUSED: archive owner/path mismatch")
        relative = Path(doc.file_path)
        if relative.is_absolute() or ".." in relative.parts or relative.parts[:2] != ("static", "archives"):
            raise RuntimeError("DEMO_REFUSED: untrusted archive path")
        target = root / relative
        if target.is_symlink() or not target.resolve().is_relative_to(root) or not target.is_file():
            raise RuntimeError("DEMO_REFUSED: archived PDF absent or unsafe")
        data = target.read_bytes()
        if len(data) != doc.file_size or hashlib.sha256(data).hexdigest() != doc.file_hash:
            raise RuntimeError("DEMO_REFUSED: archive size/hash mismatch")


def main() -> None:
    if os.getenv("ENVIRONMENT") != "test" or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
        raise RuntimeError("DEMO_REFUSED: isolated test environment required")
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith("sqlite:////") or "demo" not in url.lower():
        raise RuntimeError("DEMO_REFUSED: absolute demo-named SQLite path required")
    raw_db_path = Path(url.removeprefix("sqlite:///"))
    if raw_db_path.is_symlink():
        raise RuntimeError("DEMO_REFUSED: database symlink")
    db_path = raw_db_path.resolve()
    if not db_path.is_file() or "demo" not in str(db_path).lower():
        raise RuntimeError("DEMO_REFUSED: pre-migrated isolated demo database required")
    root_value = os.getenv("DIGITALCROWN_DEMO_ROOT", "")
    raw_root = Path(root_value) if root_value else None
    if raw_root is None or not raw_root.is_absolute() or raw_root.is_symlink():
        raise RuntimeError("DEMO_REFUSED: absolute non-symlink media root required")
    root = raw_root.resolve()
    if "demo" not in str(root).lower():
        raise RuntimeError("DEMO_REFUSED: isolated demo media root required")
    password = os.getenv("DIGITALCROWN_DEMO_PASSWORD", "")
    if len(password) < 16 or password == "DemoCrown2026!":
        raise RuntimeError("DEMO_REFUSED: supply a unique secret >=16 chars via environment")
    from backend import models
    from backend.database import SessionLocal, engine
    from backend.security import get_password_hash
    if engine.url.get_backend_name() != "sqlite" or Path(engine.url.database).resolve() != db_path:
        raise RuntimeError("DEMO_REFUSED: DB engine mismatch")
    # Never seed into a database containing any other tenant or patient.
    with SessionLocal() as db:
        existing = db.query(models.User).all()
        if any(u.email != EMAIL for u in existing):
            raise RuntimeError("DEMO_REFUSED: existing non-demo users")
        owner = db.query(models.User).filter_by(email=EMAIL).first()
        if owner and db.query(models.Patient).filter(models.Patient.employer_id != owner.id).first():
            raise RuntimeError("DEMO_REFUSED: non-demo patients present")
        if owner and db.query(models.Patient).filter_by(employer_id=owner.id).count() == len(PATIENTS):
            if len(existing) != 1:
                raise RuntimeError("DEMO_REFUSED: multiple owners")
            _verify_existing_fixture(db, models, owner, root)
            print("DEMO_REFERENCE_ALREADY_SEEDED; integrity verified, no changes")
            return
        if (owner or db.query(models.Patient).count() or db.query(models.Appointment).count()
                or db.query(models.DocumentArchive).count() or db.query(models.CabinetConfig).count()
                or db.query(models.AgendaResource).count()):
            raise RuntimeError("DEMO_REFUSED: partial fixture or existing data; do not overwrite")
        owner = models.User(
            email=EMAIL, hashed_password=get_password_hash(password),
            role=models.UserRole.DENTISTE, nom_complet="Dr Amine Bensaid - DEMO",
            is_active=True, is_licensed=True,
        )
        db.add(owner)
        db.flush()
        db.add(models.CabinetConfig(
            owner_id=owner.id, nom_cabinet=CABINET,
            nom_praticien="Dr Amine Bensaid - DEMO",
            header_lines_fr=["Digital Crown - DEMO", MARKER],
            is_initialized=True,
        ))
        db.add(models.AgendaResource(
            employer_id=owner.id, name="Fauteuil DEMO 1", resource_type="CHAIR",
        ))
        db.flush()
        chair = db.query(models.AgendaResource).filter_by(employer_id=owner.id).one()
        tz = ZoneInfo("Africa/Casablanca")
        today = datetime.now(tz).date()
        monday = today - timedelta(days=today.weekday())
        planned_files = []
        for index, (last, first, year, sex, reason) in enumerate(PATIENTS, start=1):
            number = f"DEMO-{index:04d}"
            patient = models.Patient(
                numero_dossier=number, nom=last, prenom=first,
                date_naissance=datetime(year, (index % 12) + 1, 12),
                sexe=sex, employer_id=owner.id,
                motif_consultation=f"{reason} - {MARKER}",
                antecedents_medicaux=MARKER,
                assurance="AUCUNE",
            )
            db.add(patient)
            db.flush()
            for week in (-1, 0, 1):
                day = monday + timedelta(days=(index - 1) % 5 + 7 * week)
                at = datetime.combine(day, time(9 + ((index - 1) % 7), (index % 2) * 30))
                db.add(models.Appointment(
                    patient_id=patient.id, employer_id=owner.id, resource_id=chair.id,
                    datetime_start=at, duration_minutes=30,
                    motif=f"{reason} - DEMO",
                    status=(models.AppointmentStatus.TERMINE if week < 0
                            else models.AppointmentStatus.CONFIRME if week == 0
                            else models.AppointmentStatus.PREVU),
                    notes=MARKER, source="internal",
                ))
            for doc_name, title in DOCS:
                doc_type = models.DocumentType[doc_name]
                data = _pdf(title, first + " " + last, number)
                name = f"{number}-{doc_type.value.lower()}.pdf"
                relative = Path("static/archives") / str(patient.id) / doc_type.value / "2026" / "10" / name
                target = root / relative
                if target.exists():
                    raise RuntimeError("DEMO_REFUSED: existing media target")
                planned_files.append((target, data))
                db.add(models.DocumentArchive(
                    patient_id=patient.id, uploaded_by_id=owner.id,
                    document_type=doc_type, filename=name, original_filename=name,
                    document_group_id=f"synthetic-{number}-{doc_type.value}",
                    version_number=1, is_latest_version=True,
                    file_hash=hashlib.sha256(data).hexdigest(),
                    file_size=len(data), file_path=relative.as_posix(),
                    title=title + " - DEMO", description=MARKER,
                    tags=["DEMO", "FICTIF"],
                ))
        written = []
        try:
            for target, data in planned_files:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as handle:
                    handle.write(data)
                written.append(target)
            db.commit()
        except Exception:
            db.rollback()
            for target in written:
                target.unlink(missing_ok=True)
            raise
        print(f"DEMO_REFERENCE_CREATED owner={EMAIL} patients={len(PATIENTS)} "
              f"appointments={len(PATIENTS)*3} documents={len(planned_files)}")
        print("DEMO_ONLY: no clinical validity; credentials not printed")

if __name__ == "__main__":
    main()
