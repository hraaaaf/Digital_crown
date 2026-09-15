import hashlib
from pathlib import Path

import pytest

from backend.services import medication_dict, medication_rcp_manifest


CURRENT_SOURCE_ID = "ammps-medications-current-2026-09-15"
OFFICIAL_SOURCE_PAGE = "https://www.ammps.gov.ma/recherche-medicaments?page=42"


def test_rcp_manifest_covers_exact_current_amoxicillin_regulatory_ids():
    current_rows = [
        row
        for row in medication_dict.search_regulatory_presentations("AMOXICILLINE", limit=100)
        if row["source"]["id"] == CURRENT_SOURCE_ID
    ]
    expected_ids = {row["regulatory_presentation_id"] for row in current_rows}

    assert len(expected_ids) == 8
    manifest_ids = {
        entry["regulatory_presentation_id"]
        for entry in medication_rcp_manifest._load_manifest()["entries"]
    }
    assert manifest_ids == expected_ids


def test_all_initial_rcp_entries_are_pending_and_fail_closed():
    entries = medication_rcp_manifest._load_manifest()["entries"]
    assert len(entries) == 8

    for entry in entries:
        assert entry["capture_status"] == "PENDING_DOWNLOAD"
        assert medication_rcp_manifest.entry_is_fail_closed(entry) is True
        assert medication_rcp_manifest.snapshot_is_verified(entry) is False
        assert entry["rcp_sha256"] is None
        assert entry["rcp_checked_at"] is None
        assert entry["local_artifact_path"] is None
        assert entry["extracted_clinical_fields"] == {}


def test_rcp_reader_has_no_historical_fallback():
    historical = medication_dict.search("DISPAMOX", limit=5)
    assert historical
    assert historical[0]["source"]["id"] == "cnops-open-data-medications"

    regulatory_id = historical[0]["regulatory_presentation_id"]
    assert medication_rcp_manifest.get_rcp_evidence(regulatory_id) is None


def test_snapshot_verified_requires_complete_hash_official_provenance_and_safe_path():
    incomplete = {
        "capture_status": "SNAPSHOT_VERIFIED",
        "source_page_url": OFFICIAL_SOURCE_PAGE,
        "rcp_url": "https://www.ammps.gov.ma/example.pdf",
        "rcp_sha256": None,
        "rcp_checked_at": "2026-09-15",
        "local_artifact_path": "backend/data/rcp/example.pdf",
        "extracted_clinical_fields": {},
    }
    assert medication_rcp_manifest.snapshot_is_verified(incomplete) is False
    assert medication_rcp_manifest.entry_is_fail_closed(incomplete) is False

    complete = {
        **incomplete,
        "rcp_sha256": "a" * 64,
    }
    assert medication_rcp_manifest.snapshot_is_verified(complete) is True
    assert medication_rcp_manifest.entry_is_fail_closed(complete) is True

    non_official = {
        **complete,
        "rcp_url": "https://example.com/rcp.pdf",
    }
    assert medication_rcp_manifest.snapshot_is_verified(non_official) is False
    assert medication_rcp_manifest.entry_is_fail_closed(non_official) is False

    unsafe_path = {
        **complete,
        "local_artifact_path": "../../etc/passwd",
    }
    assert medication_rcp_manifest.snapshot_is_verified(unsafe_path) is False
    assert medication_rcp_manifest.entry_is_fail_closed(unsafe_path) is False


def test_unavailable_verified_requires_explicit_official_absence_and_no_artifact():
    valid = {
        "capture_status": "UNAVAILABLE_VERIFIED",
        "source_page_url": OFFICIAL_SOURCE_PAGE,
        "rcp_url": None,
        "rcp_sha256": None,
        "rcp_checked_at": "2026-09-15",
        "local_artifact_path": None,
        "unavailability_evidence": "OFFICIAL_SOURCE_EXPLICIT_NO_RCP",
        "extracted_clinical_fields": {},
    }
    assert medication_rcp_manifest.entry_is_fail_closed(valid) is True

    missing_proof = {
        **valid,
        "unavailability_evidence": None,
    }
    assert medication_rcp_manifest.entry_is_fail_closed(missing_proof) is False

    fake_artifact = {
        **valid,
        "rcp_sha256": "b" * 64,
        "local_artifact_path": "backend/data/rcp/ghost.pdf",
    }
    assert medication_rcp_manifest.entry_is_fail_closed(fake_artifact) is False


def test_missing_link_is_not_promoted_to_unavailable_verified():
    entries = medication_rcp_manifest._load_manifest()["entries"]
    clamoxyl = [entry for entry in entries if entry["nom"] == "CLAMOXYL"]
    assert clamoxyl
    assert all(entry["rcp_link_observed"] is False for entry in clamoxyl)
    assert all(entry["capture_status"] == "PENDING_DOWNLOAD" for entry in clamoxyl)


def test_prepare_verified_snapshot_entry_hashes_pdf_without_mutating_source():
    original = medication_rcp_manifest._load_manifest()["entries"][0]
    original_copy = dict(original)
    pdf_bytes = b"%PDF-1.7\nRCP test fixture without clinical content\n%%EOF"
    rcp_url = "https://www.ammps.gov.ma/sites/default/files/rcp/example.pdf"

    prepared = medication_rcp_manifest.prepare_verified_snapshot_entry(
        original,
        pdf_bytes=pdf_bytes,
        rcp_url=rcp_url,
        checked_at="2026-09-15",
        local_artifact_path="backend/data/rcp/example.pdf",
    )

    assert original == original_copy
    assert original["capture_status"] == "PENDING_DOWNLOAD"
    assert prepared["capture_status"] == "SNAPSHOT_VERIFIED"
    assert prepared["rcp_url"] == rcp_url
    assert prepared["rcp_sha256"] == hashlib.sha256(pdf_bytes).hexdigest()
    assert prepared["rcp_checked_at"] == "2026-09-15"
    assert prepared["local_artifact_path"] == "backend/data/rcp/example.pdf"
    assert prepared["extracted_clinical_fields"] == {}
    assert medication_rcp_manifest.entry_is_fail_closed(prepared) is True


@pytest.mark.parametrize(
    ("pdf_bytes", "rcp_url", "checked_at", "local_artifact_path"),
    [
        (b"not-a-pdf", "https://www.ammps.gov.ma/rcp/example.pdf", "2026-09-15", "backend/data/rcp/example.pdf"),
        (b"%PDF-1.7\n%%EOF", "https://example.com/rcp.pdf", "2026-09-15", "backend/data/rcp/example.pdf"),
        (b"%PDF-1.7\n%%EOF", "https://www.ammps.gov.ma/rcp/example.pdf", "15/09/2026", "backend/data/rcp/example.pdf"),
        (b"%PDF-1.7\n%%EOF", "https://www.ammps.gov.ma/rcp/example.pdf", "20260915", "backend/data/rcp/example.pdf"),
        (b"%PDF-1.7\n%%EOF", "https://www.ammps.gov.ma/rcp/example.pdf", "2026-09-15", "../../example.pdf"),
        (b"%PDF-1.7\n%%EOF", "https://www.ammps.gov.ma/rcp/example.pdf", "2026-09-15", "backend/data/rcp/example.txt"),
    ],
)
def test_prepare_verified_snapshot_entry_rejects_invalid_capture_inputs(
    pdf_bytes,
    rcp_url,
    checked_at,
    local_artifact_path,
):
    original = medication_rcp_manifest._load_manifest()["entries"][0]

    with pytest.raises(ValueError):
        medication_rcp_manifest.prepare_verified_snapshot_entry(
            original,
            pdf_bytes=pdf_bytes,
            rcp_url=rcp_url,
            checked_at=checked_at,
            local_artifact_path=local_artifact_path,
        )


def test_prepare_verified_snapshot_entry_requires_clean_pending_source_entry():
    original = medication_rcp_manifest._load_manifest()["entries"][0]
    polluted = {
        **original,
        "extracted_clinical_fields": {"dose": "forbidden in capture layer"},
    }

    with pytest.raises(ValueError):
        medication_rcp_manifest.prepare_verified_snapshot_entry(
            polluted,
            pdf_bytes=b"%PDF-1.7\n%%EOF",
            rcp_url="https://www.ammps.gov.ma/rcp/example.pdf",
            checked_at="2026-09-15",
            local_artifact_path="backend/data/rcp/example.pdf",
        )


def test_rcp_manifest_metadata_is_documentary_only():
    metadata = medication_rcp_manifest.manifest_metadata()
    assert metadata == {
        "schema_version": "m1b-rcp.1",
        "verified_at": "2026-09-15",
        "authority": "AMMPS",
        "entry_count": 8,
        "available": True,
    }


def test_rcp_manifest_is_packaged_in_desktop_build():
    root = Path(__file__).resolve().parents[2]
    spec = (root / "DigitalCrown.spec").read_text(encoding="utf-8")
    assert "backend/data/medications_ma_ammps_rcp_manifest_2026.json" in spec
