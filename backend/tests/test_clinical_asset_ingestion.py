from datetime import datetime
from io import BytesIO
from pathlib import PurePosixPath

import fitz
import pytest
from PIL import Image

from backend.models import Patient, User
from backend.models_media_core import ClinicalAsset
from backend.security import get_password_hash
from backend.services.clinical_asset_ingestion import (
    ClinicalAssetIngestionError,
    ingest_clinical_asset_bytes,
    validate_clinical_import_payload,
)
from backend.services.clinical_asset_storage import read_clinical_asset_bytes


def _make_owner_patient(db, suffix: str):
    owner = User(
        email=f"media-c3-{suffix}@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet=f"Dr C3 {suffix}",
        is_active=True,
        is_licensed=True,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    patient = Patient(
        numero_dossier=f"C3-{suffix}",
        nom="Synthetic",
        prenom="Media",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return owner, patient


def _png_bytes(width=900, height=600):
    image = Image.new("RGB", (width, height), (120, 80, 40))
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def _jpeg_bytes(width=640, height=480):
    image = Image.new("RGB", (width, height), (10, 30, 90))
    out = BytesIO()
    image.save(out, format="JPEG", quality=90)
    return out.getvalue()


def _pdf_bytes():
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 96), "Synthetic C3 document")
    data = document.tobytes()
    document.close()
    return data


def _stored_path(root, storage_key: str):
    return root.joinpath(*PurePosixPath(storage_key).parts)


def test_validate_image_uses_content_not_client_metadata():
    content = _png_bytes()
    validated = validate_clinical_import_payload(
        content,
        claimed_mime_type="image/png",
        original_filename="photo.png",
    )
    assert validated.mime_type == "image/png"
    assert validated.format_name == "PNG"
    assert validated.width == 900
    assert validated.height == 600
    assert validated.thumbnail_jpeg.startswith(b"\xff\xd8\xff")

    with pytest.raises(ClinicalAssetIngestionError, match="claimed MIME"):
        validate_clinical_import_payload(content, claimed_mime_type="image/jpeg")

    with pytest.raises(ClinicalAssetIngestionError, match="extension"):
        validate_clinical_import_payload(content, original_filename="photo.pdf")


def test_unrecognized_or_corrupt_content_is_rejected_before_storage():
    with pytest.raises(ClinicalAssetIngestionError, match="unsupported or unrecognized"):
        validate_clinical_import_payload(b"MZ-not-a-clinical-file")

    corrupt_png = b"\x89PNG\r\n\x1a\n" + b"broken"
    with pytest.raises(ClinicalAssetIngestionError, match="parser validation"):
        validate_clinical_import_payload(corrupt_png, claimed_mime_type="image/png")


def test_image_ingestion_creates_encrypted_original_and_controlled_thumbnail(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "c3-test-secret-key-material")
    owner, patient = _make_owner_patient(db, "image")
    content = _jpeg_bytes(1200, 800)

    result = ingest_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
        content=content,
        original_filename="portrait.jpg",
        claimed_mime_type="image/jpeg",
        timepoint="T0",
        created_by=owner.id,
        media_root=tmp_path,
    )
    db.commit()

    assert result.asset.mime_type == "image/jpeg"
    assert result.asset.provenance_json["validated_format"] == "JPEG"
    assert result.asset.provenance_json["width"] == 1200
    assert result.asset.provenance_json["height"] == 800
    assert result.thumbnail_asset is not None
    assert result.thumbnail_asset.parent_asset_id == result.asset.id
    assert result.thumbnail_asset.source_kind == "DERIVED"
    assert result.thumbnail_asset.source_ref == "C3_THUMBNAIL_V1"
    assert result.thumbnail_asset.provenance_json["derivative_kind"] == "THUMBNAIL"

    original_on_disk = _stored_path(tmp_path, result.asset.storage_key).read_bytes()
    assert original_on_disk != content
    assert original_on_disk.startswith(b"DCM1")

    original_plaintext = read_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_id=result.asset.id,
        media_root=tmp_path,
    )
    assert original_plaintext == content

    thumbnail = read_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_id=result.thumbnail_asset.id,
        media_root=tmp_path,
    )
    with Image.open(BytesIO(thumbnail)) as image:
        assert image.format == "JPEG"
        assert max(image.size) <= 512
        assert image.getexif() == {}


def test_pdf_ingestion_validates_page_count_and_creates_first_page_thumbnail(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "c3-test-secret-key-material")
    owner, patient = _make_owner_patient(db, "pdf")
    content = _pdf_bytes()

    result = ingest_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_type="DOCUMENT",
        source_kind="IMPORT",
        content=content,
        original_filename="scan.pdf",
        claimed_mime_type="application/pdf; charset=binary",
        media_root=tmp_path,
    )
    db.commit()

    assert result.asset.mime_type == "application/pdf"
    assert result.asset.provenance_json["validated_format"] == "PDF"
    assert result.asset.provenance_json["page_count"] == 1
    assert result.thumbnail_asset is not None
    assert result.thumbnail_asset.mime_type == "image/jpeg"


def test_asset_type_must_match_validated_content(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "c3-test-secret-key-material")
    owner, patient = _make_owner_patient(db, "type")

    with pytest.raises(ClinicalAssetIngestionError, match="requires DOCUMENT"):
        ingest_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_type="PHOTO",
            source_kind="UPLOAD",
            content=_pdf_bytes(),
            original_filename="doc.pdf",
            media_root=tmp_path,
        )

    with pytest.raises(ClinicalAssetIngestionError, match="PHOTO or RADIOGRAPH"):
        ingest_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_type="DOCUMENT",
            source_kind="UPLOAD",
            content=_png_bytes(),
            original_filename="image.png",
            media_root=tmp_path,
        )


def test_external_caller_cannot_claim_derived_source_kind(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "c3-test-secret-key-material")
    owner, patient = _make_owner_patient(db, "derived")

    with pytest.raises(ClinicalAssetIngestionError, match="not externally ingestible"):
        ingest_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_type="PHOTO",
            source_kind="DERIVED",
            content=_png_bytes(),
            original_filename="image.png",
            media_root=tmp_path,
        )


def test_validation_failure_creates_no_asset_and_no_blob(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "c3-test-secret-key-material")
    owner, patient = _make_owner_patient(db, "fail")
    before = db.query(ClinicalAsset).count()

    with pytest.raises(ClinicalAssetIngestionError):
        ingest_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_type="PHOTO",
            source_kind="UPLOAD",
            content=b"not-media",
            original_filename="malware.jpg",
            claimed_mime_type="image/jpeg",
            media_root=tmp_path,
        )

    assert db.query(ClinicalAsset).count() == before
    assert list(tmp_path.rglob("*.dcm")) == []


def test_size_limit_fails_before_parser_or_storage(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "c3-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_ingestion.MAX_IMPORT_BYTES", 8)
    owner, patient = _make_owner_patient(db, "size")
    before = db.query(ClinicalAsset).count()

    with pytest.raises(ClinicalAssetIngestionError, match="size limit"):
        ingest_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_type="PHOTO",
            source_kind="UPLOAD",
            content=b"0123456789",
            original_filename="x.jpg",
            media_root=tmp_path,
        )

    assert db.query(ClinicalAsset).count() == before
    assert list(tmp_path.rglob("*.dcm")) == []
