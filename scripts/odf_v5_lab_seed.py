"""ODF V5 first-user LAB: public cephalogram + wholly synthetic cabinet and case.

THIS IS NOT A CLINICAL STUDY. The public lateral radiograph is an authentic
reusable *illustration*. Pre-existing T2 synthetic landmark coordinates are
NOT traced from it and MUST NOT be represented as measurements of its subject.
No patient identity or Angle class is inferred from image pixels.

Operates solely against the disposable CI T2 SQLite, never cabinet production.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE_URL = "https://upload.wikimedia.org/wikipedia/commons/6/66/Cephalometric_radiograph.JPG"
SOURCE_SHA1 = "2a284993c666790a72d0c004044b35a92534ce9d"
SOURCE_PAGE = "https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG"
COPYRIGHT = "ANUG, Cephalometric radiograph.JPG (2014), CC BY-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"


def guard() -> Path:
    if os.environ.get("ENVIRONMENT") != "test" or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
        raise RuntimeError("LAB_REQUIRES_TEST_ISOLATION")
    if os.environ.get("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db":
        raise RuntimeError("LAB_DATABASE_ALLOWLIST_MISMATCH")
    if os.environ.get("T2_PASSWORD") is None:
        raise RuntimeError("LAB_TEST_PASSWORD_MISSING")
    p = (ROOT / "t2-runtime-cert.db").resolve()
    if not p.is_file() or p.name != "t2-runtime-cert.db" or p.parent != ROOT:
        raise RuntimeError("LAB_DISPOSABLE_DATABASE_MISSING")
    if any(x in str(p).lower() for x in ("production", "patient_data", "cabinet.sqlite", "app.db")):
        raise RuntimeError("LAB_PATH_REFUSED")
    return p


def public_film(out: Path):
    from PIL import Image, ImageOps, ImageDraw
    from io import BytesIO
    out.mkdir(parents=True, exist_ok=True)
    # A reproducible license-bound download, never a private radiology upload.
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "DigitalCrown-ODF-TestLab/1.0 (synthetic research fixture)"},
    )
    with urllib.request.urlopen(request, timeout=25) as handle:
        raw = handle.read(2_000_000)
    if hashlib.sha1(raw).hexdigest() != SOURCE_SHA1 or len(raw) != 399879:
        raise RuntimeError("PUBLIC_FILM_CHECKSUM_MISMATCH")
    image = Image.open(BytesIO(raw))
    image.load()
    if image.size != (2272, 1818):
        raise RuntimeError("PUBLIC_FILM_UNEXPECTED_DIMENSIONS")
    # Convert to pixels without EXIF metadata. Letterboxing preserves geometry.
    image = image.convert("RGB")
    ref = out / "public-cephalo-ANUG-original.jpg"
    ref.write_bytes(raw)
    display = ImageOps.pad(image, (1935, 2400), color=(16, 21, 29), centering=(0.5, 0.5))
    media = ROOT / "backend/static/uploads/radios/t2-cephalo-seeded.png"
    media.parent.mkdir(parents=True, exist_ok=True)
    display.save(media, format="PNG")
    # A visible LAB stamp explicitly rejects clinical image diagnosis.
    proof = display.copy()
    draw = ImageDraw.Draw(proof)
    draw.rectangle((0, 0, 1935, 80), fill="#101b2b")
    draw.text((24, 28), "ODF LAB / IMAGE PUBLIQUE / POINTS NON TRACES SUR CE FILM", fill="white")
    proof.save(out / "radiographie-profil-lab-apercu.png")
    (out / "RADIO_SOURCE_ET_LICENCE.txt").write_text(
        COPYRIGHT + "\n" + SOURCE_PAGE + "\n" + LICENSE_URL + "\n"
        + "Original 2272x1818 JPG, sha1=" + SOURCE_SHA1 + "\n"
        + "Display: resized with padding (no anatomical inference); no EXIF in derivative.\n"
        + "IMPORTANT: T2 study landmarks are artificial and DO NOT align with this film.\n"
        + "Angle classification is an INDEPENDENT SIMULATED CAST EXAM, not an X-ray diagnosis.\n",
        encoding="utf8",
    )
    return media


def seed():
    guard()
    out = ROOT / "artifacts/ortho-v5-first-user-lab"
    media = public_film(out)

    # Small original synthetic lab logo; no real clinic branding or identities.
    from PIL import Image, ImageDraw
    logo = Image.new("RGB", (240, 240), "white")
    mark = ImageDraw.Draw(logo)
    mark.ellipse((18,18,222,222), fill="#213d59")
    mark.ellipse((40,40,200,200), fill="#eaf1f5")
    mark.text((75,105),"ODF", fill="#213d59")
    logo_file = ROOT / "backend/static/uploads/radios/odf-lab-logo.png"
    logo_file.parent.mkdir(parents=True, exist_ok=True)
    logo.save(logo_file)
    logo.save(out / "logo-cabinet-fictif.png")

    from backend import models, database
    with database.SessionLocal() as db:
        dentist = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").one()
        assert dentist.role == models.UserRole.DENTISTE and dentist.get_employer_id() == dentist.id
        dentist.nom_complet = "Dr Salma Atlas - LAB TEST"
        cfg = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == dentist.id).one()
        cfg.nom_cabinet = "Cabinet Atlas - LABORATOIRE FICTIF"
        cfg.nom_praticien = "Dr Salma Atlas - LAB TEST"
        cfg.logo_path = "radios/odf-lab-logo.png"
        cfg.header_customized = True
        cfg.header_lines_fr = [
            "Dr Salma Atlas - LAB TEST",
            "Chirurgienne-dentiste - Orthodontie",
            "Orthopédie dento-faciale (démonstration)",
        ]
        cfg.header_lines_ar = []
        cfg.specialty_ids = ["ortho"]
        cfg.footer_address = "24 avenue de l'Exemple, Rabat - ADRESSE FICTIVE"
        cfg.footer_phones = "06 00 00 00 00"
        cfg.contacts_json = {"mobile": {"enabled": True, "value": "06 00 00 00 00"}}
        cfg.qr_code_enabled = True
        cfg.qr_code_type = models.QRCodeType.WEBSITE
        cfg.qr_code_value = "https://example.org/digital-crown-lab"
        cfg.qr_code_label = "LAB FICTIF"
        cfg.qr_code_style = "classic"
        cfg.selected_template = "heritage"
        cfg.hide_header = False
        cfg.hide_footer = False
        patient = db.query(models.Patient).filter(
            models.Patient.numero_dossier == "T2-0001",
            models.Patient.employer_id == dentist.id,
        ).one()
        patient.nom = "ESSAI-ODF"
        patient.prenom = "Maya-SYNTHETIQUE"
        patient.telephone = None
        patient.email = None
        patient.date_naissance = __import__("datetime").datetime(2013, 4, 20)
        studies = db.query(models.CephaloAnalysis).filter(
            models.CephaloAnalysis.patient_id == patient.id
        ).all()
        # Only the T2 seeded synthetic study may reference this *public* image.
        for study in studies:
            if study.image_original_path == "api/static/uploads/radios/t2-cephalo-seeded.png":
                assert isinstance(study.landmarks_data, list)
        db.commit()
        result = {
            "lab": "ODF_V5_FIRST_USER_LAB_NONCLINICAL",
            "cabinet": cfg.nom_cabinet, "dentiste": dentist.nom_complet,
            "patient": patient.nom + " " + patient.prenom,
            "patient_id": patient.id, "source_media": "PUBLIC_REAL_LATERAL_CEPH_CC_BY_SA",
            "source_sha1": SOURCE_SHA1, "media_path": str(media.relative_to(ROOT)),
            "preexisting_synthetic_studies": [s.id for s in studies],
            "angle_class": "I BILATERALE (moulages fictifs seulement)",
            "clinical_authority": "NEVER_FROM_FILM",
            "scientific_snapshot": "SYNTHETIC_COORDINATES_NOT_TRACED",
        }
        (out / "lab-manifest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")
        print("ODF_LAB_READY=" + json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    seed()
