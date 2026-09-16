from pathlib import Path

import fitz
import pytest

from backend.schemas.insurance_submission import InsuranceOrganization
from backend.services.insurance_source_store import (
    load_stored_insurance_source,
    lock_and_store_insurance_template,
    lock_and_store_ngap_primary,
)
from backend.services.insurance_template_registry import (
    CNOPS_DENTAL_CABINET_2026_09_16,
    CNSS_610_1_04,
    InsuranceTemplateDefinition,
    InsuranceTemplateTrust,
)
from backend.services.ngap_reference import DENTAL_NGAP_PRIMARY_PENDING


def _pdf_bytes(*, pages: int, text: str = "") -> bytes:
    document = fitz.open()
    for index in range(pages):
        page = document.new_page()
        if text:
            page.insert_text((72, 72), f"{text} page {index + 1}")
    payload = document.tobytes()
    document.close()
    return payload


def _stored_cnss(tmp_path):
    payload = _pdf_bytes(pages=2, text="CNSS dental template")
    locked, stored = lock_and_store_insurance_template(
        root=tmp_path,
        definition=CNSS_610_1_04,
        pdf_bytes=payload,
        source_url="cabinet://validated/CNSS-610-1-04.pdf",
        cabinet_validated_by="Dr Test",
    )
    return payload, locked, stored


def test_template_source_store_requires_validator_for_cabinet_trust(tmp_path):
    payload = _pdf_bytes(pages=2, text="CNSS dental template")
    with pytest.raises(ValueError, match="validator identity"):
        lock_and_store_insurance_template(
            root=tmp_path,
            definition=CNSS_610_1_04,
            pdf_bytes=payload,
            source_url="cabinet://validated/CNSS-610-1-04.pdf",
        )


def test_template_source_store_is_hash_addressed_and_idempotent(tmp_path):
    payload, locked, stored = _stored_cnss(tmp_path)
    assert Path(stored.pdf_path).read_bytes() == payload
    assert locked.sha256 == stored.sha256

    second_locked, second_stored = lock_and_store_insurance_template(
        root=tmp_path,
        definition=CNSS_610_1_04,
        pdf_bytes=payload,
        source_url="cabinet://validated/CNSS-610-1-04.pdf",
        cabinet_validated_by="Dr Test",
    )
    assert second_locked.sha256 == locked.sha256
    assert second_stored == stored

    loaded = load_stored_insurance_source(
        root=tmp_path,
        namespace="template-cnss",
        version=CNSS_610_1_04.version,
        sha256=locked.sha256,
    )
    assert loaded.pdf_bytes == payload
    assert loaded.manifest["trust"] == "CABINET_VALIDATED_BINARY"
    assert loaded.manifest["cabinet_validated_by"] == "Dr Test"


def test_cnops_template_source_requires_validator_and_preserves_provenance(tmp_path):
    payload = _pdf_bytes(pages=2, text="CNOPS dental cabinet validated template")
    with pytest.raises(ValueError, match="validator identity"):
        lock_and_store_insurance_template(
            root=tmp_path,
            definition=CNOPS_DENTAL_CABINET_2026_09_16,
            pdf_bytes=payload,
            source_url="cabinet://validated/CNOPS-dental.pdf",
        )

    locked, stored = lock_and_store_insurance_template(
        root=tmp_path,
        definition=CNOPS_DENTAL_CABINET_2026_09_16,
        pdf_bytes=payload,
        source_url="cabinet://validated/CNOPS-dental.pdf",
        cabinet_validated_by="Dr Test",
    )
    loaded = load_stored_insurance_source(
        root=tmp_path,
        namespace="template-cnops",
        version=CNOPS_DENTAL_CABINET_2026_09_16.version,
        sha256=locked.sha256,
    )
    assert loaded.pdf_bytes == payload
    assert loaded.manifest["organization"] == "CNOPS"
    assert loaded.manifest["trust"] == "CABINET_VALIDATED_BINARY"
    assert loaded.manifest["cabinet_validated_by"] == "Dr Test"
    assert loaded.manifest["source_url"] == "cabinet://validated/CNOPS-dental.pdf"
    assert Path(stored.pdf_path).read_bytes() == payload


def test_source_store_read_rejects_pdf_tampering(tmp_path):
    _, locked, stored = _stored_cnss(tmp_path)
    Path(stored.pdf_path).write_bytes(b"%PDF-1.4\ntampered")
    with pytest.raises(ValueError, match="PDF SHA-256 mismatch"):
        load_stored_insurance_source(
            root=tmp_path,
            namespace="template-cnss",
            version=CNSS_610_1_04.version,
            sha256=locked.sha256,
        )


def test_source_store_read_rejects_manifest_identity_tampering(tmp_path):
    _, locked, stored = _stored_cnss(tmp_path)
    manifest_path = Path(stored.manifest_path)
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace(
            '"version": "CNSS-610-1-04"',
            '"version": "OTHER"',
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="manifest version mismatch"):
        load_stored_insurance_source(
            root=tmp_path,
            namespace="template-cnss",
            version=CNSS_610_1_04.version,
            sha256=locked.sha256,
        )


def test_template_source_store_rejects_wrong_page_count(tmp_path):
    payload = _pdf_bytes(pages=1, text="CNSS dental template")
    with pytest.raises(ValueError, match="page count mismatch"):
        lock_and_store_insurance_template(
            root=tmp_path,
            definition=CNSS_610_1_04,
            pdf_bytes=payload,
            source_url="cabinet://validated/CNSS-610-1-04.pdf",
            cabinet_validated_by="Dr Test",
        )


def test_ngap_source_store_requires_legal_identity_markers(tmp_path):
    bad = _pdf_bytes(pages=1, text="unrelated document")
    with pytest.raises(ValueError, match="identity markers"):
        lock_and_store_ngap_primary(
            root=tmp_path,
            release=DENTAL_NGAP_PRIMARY_PENDING,
            pdf_bytes=bad,
            source_url="cabinet://official/177-06.pdf",
        )


def test_ngap_source_store_locks_validated_binary(tmp_path):
    payload = _pdf_bytes(
        pages=2,
        text="Arrete 177-06 Nomenclature generale des actes professionnels",
    )
    locked, stored = lock_and_store_ngap_primary(
        root=tmp_path,
        release=DENTAL_NGAP_PRIMARY_PENDING,
        pdf_bytes=payload,
        source_url="cabinet://official/177-06.pdf",
    )
    assert locked.source_hash == stored.sha256
    assert Path(stored.pdf_path).read_bytes() == payload


def test_store_namespace_contract_handles_other_insurers(tmp_path):
    definition = InsuranceTemplateDefinition(
        organization=InsuranceOrganization.CNOPS,
        version="CNOPS-TEST-2P",
        label="CNOPS test",
        trust=InsuranceTemplateTrust.SECONDARY_REFERENCE,
        expected_page_count=2,
    )
    _, stored = lock_and_store_insurance_template(
        root=tmp_path,
        definition=definition,
        pdf_bytes=_pdf_bytes(pages=2, text="CNOPS"),
        source_url="cabinet://reference/cnops.pdf",
    )
    assert "template-cnops" in stored.pdf_path
