from datetime import datetime

import pytest

from backend import models
from backend.models_ngap_reference import NgapCatalogMapping
from backend.services.ngap_reference import (
    NgapReferenceStatus,
    NgapRelease,
    certify_catalog_act_ngap_mapping,
    resolve_catalog_act_ngap,
)
from backend.schemas.insurance_submission import InsuranceMappingStatus


def _pending_mapping(db):
    specialty = models.Specialty(name="NGAP certification spec")
    db.add(specialty)
    db.flush()
    act = models.CatalogAct(
        specialty_id=specialty.id,
        name="Extraction certification test",
        code="INTERNAL-EXTRACTION",
        base_price=700.0,
        is_active=True,
    )
    db.add(act)
    db.flush()
    mapping = NgapCatalogMapping(
        catalog_act_id=act.id,
        code_kind="NGAP",
        ngap_code="D713",
        coefficient=10.0,
        official_label="Extraction dentaire de test",
        reference_version="arrete-177-06-test",
        mapping_rule_id=f"arrete-177-06-test:{act.id}",
        verification_status="PRIMARY_HASH_PENDING",
        source_authority="pending",
        source_url="https://example.invalid/pending.pdf",
        source_hash=None,
    )
    db.add(mapping)
    db.flush()
    return act, mapping


def _locked_release(version="arrete-177-06-test"):
    return NgapRelease(
        version=version,
        authority="Ministere de la Sante",
        source_url="https://example.invalid/locked-primary.pdf",
        status=NgapReferenceStatus.VERIFIED_PRIMARY,
        source_hash="d" * 64,
    )


def test_certification_promotes_mapping_only_with_locked_release_and_practitioner(db, dentiste):
    act, mapping = _pending_mapping(db)
    validated_at = datetime(2026, 9, 14, 19, 30)

    certified = certify_catalog_act_ngap_mapping(
        db,
        mapping_id=mapping.id,
        locked_release=_locked_release(),
        practitioner_id=dentiste.id,
        validated_at=validated_at,
    )

    assert certified.verification_status == "VERIFIED_PRIMARY"
    assert certified.source_hash == "d" * 64
    assert certified.validated_by_practitioner_id == dentiste.id
    assert certified.validated_at == validated_at

    resolution = resolve_catalog_act_ngap(
        db,
        catalog_act_id=act.id,
        reference_version="arrete-177-06-test",
    )
    assert resolution.status == InsuranceMappingStatus.EXACT
    assert resolution.code == "D713"


def test_certification_rejects_reference_version_mismatch(db, dentiste):
    _, mapping = _pending_mapping(db)
    with pytest.raises(ValueError, match="version mismatch"):
        certify_catalog_act_ngap_mapping(
            db,
            mapping_id=mapping.id,
            locked_release=_locked_release(version="other-version"),
            practitioner_id=dentiste.id,
        )


def test_certification_rejects_unknown_practitioner(db):
    _, mapping = _pending_mapping(db)
    with pytest.raises(ValueError, match="validator not found"):
        certify_catalog_act_ngap_mapping(
            db,
            mapping_id=mapping.id,
            locked_release=_locked_release(),
            practitioner_id=999999,
        )
