"""Synthetic historical BILAN fixture for isolated Chromium DEC-R2 E2E only.

NEVER RUN against a real cabinet, Production or anything but t2-runtime-cert.db.
No app endpoint can create a BILAN: this explicitly creates a disposable
classified archive and PDF to verify that an R-only UI can read it.
"""
import os
import sys
from hashlib import sha256
from pathlib import Path

# Run as a script without depending on PYTHONPATH or weakening DB isolation.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
    # A well-formed one-page synthetic PDF is required for genuine Chromium
    # visual inspection. The old bytes had a PDF header but no valid page tree,
    # producing an entirely white viewer despite a successful HTTP GET.
    from io import BytesIO
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4

    buffer = BytesIO()
    canvas = Canvas(buffer, pagesize=A4, pageCompression=1)
    canvas.setTitle("BILAN T2 synthetique - test R uniquement")
    width, height = A4
    canvas.setFillColorRGB(0.055, 0.16, 0.35)
    canvas.rect(0, height - 116, width, 116, fill=1, stroke=0)
    canvas.setFillColorRGB(1, 1, 1)
    canvas.setFont("Helvetica-Bold", 21)
    canvas.drawString(45, height - 60, "BILAN CLINIQUE - SYNTHETIQUE")
    canvas.setFont("Helvetica", 11)
    canvas.drawString(45, height - 84, "Digital Crown | lecture seule R | donnees 100% fictives")
    canvas.setFillColorRGB(0.11, 0.24, 0.43)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(45, height - 159, "Compte rendu de verification visuelle")
    canvas.setFillColorRGB(0.30, 0.36, 0.44)
    canvas.setFont("Helvetica", 11)
    lines = (
        "Patient : T2 CERTIFICATION (patient de test, aucun soin reel)",
        "Dossier : T2-0001     Type archive : BILAN",
        "Objet : verifier le rendu du PDF dans MultiView R uniquement.",
        "Edition, signature, suppression et archivage : non autorises ici.",
        "Ce document est un jeu de test. Aucune conclusion clinique.",
    )
    for index, line in enumerate(lines):
        canvas.drawString(45, height - 192 - index * 28, line)
    canvas.setStrokeColorRGB(0.80, 0.87, 0.95)
    canvas.line(45, height - 360, width - 45, height - 360)
    canvas.setFont("Helvetica-Oblique", 10)
    canvas.drawString(45, height - 389, "Controle visuel E2E - PDF reel rendu par navigateur")
    canvas.setFillColorRGB(0.65, 0.69, 0.76)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(45, 42, "ENVIRONNEMENT SYNTHETIQUE ISOLE - PAS DE DONNEES PATIENT REELLES")
    canvas.showPage()
    canvas.save()
    pdf = buffer.getvalue()
    assert pdf.startswith(b"%PDF-") and b"%%EOF" in pdf and len(pdf) > 900
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
