from datetime import date

from backend.schemas.insurance_submission import InsuranceMappingStatus
from backend.services.ngap_reference import (
    DENTAL_NGAP_PRIMARY_PENDING,
    NgapCodeKind,
    NgapEntry,
    NgapReferenceStatus,
    NgapRelease,
    resolve_ngap_code,
)


def test_real_pending_primary_release_never_resolves_exact():
    result = resolve_ngap_code(
        catalog_code="D713",
        code_kind=NgapCodeKind.NGAP,
        release=DENTAL_NGAP_PRIMARY_PENDING,
        on_date=date(2026, 9, 14),
    )
    assert result.status == InsuranceMappingStatus.OUTDATED
    assert result.code is None


def test_internal_code_is_never_interpreted_as_ngap():
    release = NgapRelease(
        version="test-v1",
        authority="test",
        source_url="https://example.invalid/reference.pdf",
        status=NgapReferenceStatus.VERIFIED_PRIMARY,
        source_hash="a" * 64,
        entries={
            "D713": NgapEntry(
                code="D713",
                coefficient=10,
                official_label="Extraction test",
                mapping_rule_id="test-v1:D713",
            )
        },
    )
    result = resolve_ngap_code(
        catalog_code="D713",
        code_kind=NgapCodeKind.INTERNAL,
        release=release,
    )
    assert result.status == InsuranceMappingStatus.NO_MATCH


def test_verified_locked_release_can_resolve_only_exact_code():
    release = NgapRelease(
        version="test-v1",
        authority="test",
        source_url="https://example.invalid/reference.pdf",
        status=NgapReferenceStatus.VERIFIED_PRIMARY,
        source_hash="b" * 64,
        valid_from=date(2026, 1, 1),
        entries={
            "D713": NgapEntry(
                code="D713",
                coefficient=10,
                official_label="Extraction test",
                mapping_rule_id="test-v1:D713",
            )
        },
    )

    exact = resolve_ngap_code(
        catalog_code="d713",
        code_kind=NgapCodeKind.NGAP,
        release=release,
        on_date=date(2026, 9, 14),
    )
    assert exact.status == InsuranceMappingStatus.EXACT
    assert exact.code == "D713"
    assert exact.coefficient == 10
    assert exact.mapping_rule_id == "test-v1:D713"
    assert exact.release_hash == "b" * 64

    missing = resolve_ngap_code(
        catalog_code="D999",
        code_kind=NgapCodeKind.NGAP,
        release=release,
        on_date=date(2026, 9, 14),
    )
    assert missing.status == InsuranceMappingStatus.NO_MATCH
    assert missing.code is None


def test_expired_release_fails_closed_as_outdated():
    release = NgapRelease(
        version="test-expired",
        authority="test",
        source_url="https://example.invalid/reference.pdf",
        status=NgapReferenceStatus.VERIFIED_PRIMARY,
        source_hash="c" * 64,
        valid_to=date(2025, 12, 31),
        entries={
            "D713": NgapEntry(
                code="D713",
                coefficient=10,
                official_label="Extraction test",
                mapping_rule_id="test-expired:D713",
            )
        },
    )
    result = resolve_ngap_code(
        catalog_code="D713",
        code_kind=NgapCodeKind.NGAP,
        release=release,
        on_date=date(2026, 9, 14),
    )
    assert result.status == InsuranceMappingStatus.OUTDATED
    assert result.code is None
