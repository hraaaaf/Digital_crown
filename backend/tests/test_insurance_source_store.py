from pathlib import Path

import fitz
import pytest

from backend.schemas.insurance_submission import InsuranceOrganization
from backend.services.insurance_source_store import (
    lock_and_store_insurance_template,
    lock_and_store_ngap_primary,
)
from backend.services.insurance_template_registry import (
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


def test_template_source_store_is_hash_addressed_and_idempotent(tmp_path):
    payload = _pdf_bytes(pages=2, text="CNSS dental template")
    locked, stored = lock_and_store_insurance_template(
        root=tmp_path,
        definition=CNSS_610_1_04,
        pdf_bytes=payload,
        source_url="cabinet://validated/CNSS-610-1-04.pdf",
    )
    assert Path(stored.pdf_path).read_bytes() == payload
    assert locked.sha256 == stored.sha256

    second_locked, second_stored = lock_and_store_insurance_template(
        root=tmp_path,
        definition=CNSS_610_1_04,
        pdf_bytes=payload,
        source_url="cabinet://validated/CNSS-610-1-04.pdf",
    )
    assert second_locked.sha256 == locked.sha256
    assert second_stored == stored


def test_template_source_store_rejects_wrong_page_count(tmp_path):
    payload = _pdf_bytes(pages=1, text="CNSS dental template")
    with pytest.raises(ValueError, match="page count mismatch"):
        lock_and_store_insurance_template(
            root=tmp_path,
            definition=CNSS_610_1_04,
            pdf_bytes=payload,
            source_url="cabinet://validated/CNSS-610-1-04.pdf",
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
