from datetime import datetime

import pytest

from backend import models
from backend.models_ngap_reference import NgapCatalogMapping
from backend.schemas.insurance_submission import (
    InsuranceDraftStatus,
    InsuranceMappingStatus,
    InsuranceOrganization,
)
from backend.services.insurance_submission import (
    apply_ngap_reference_to_draft,
    build_draft_from_honoraires_snapshot,
)


def _catalog_act(db, *, name):
    specialty = models.Specialty(name=f"Spec {name}")
    db.add(specialty)
    db.flush()
    act = models.CatalogAct(
        specialty_id=specialty.id,
        name=name,
        code=f"INTERNAL-{name}",
        base_price=500.0,
        is_active=True,
    )
    db.add(act)
    db.flush()
    return act


def _draft(act_ids):
    payments = [
        {
            "date": "2026-09-14",
            "acte": f"Acte {index}",
            "dent": "11",
            "montant": 500.0 + index,
            "catalog_act_id": act_id,
            "source_line_uid": f"00000000-0000-0000-0000-{index + 1:012d}",
        }
        for index, act_id in enumerate(act_ids)
    ]
    return build_draft_from_honoraires_snapshot(
        patient_id=1,
        organization=InsuranceOrganization.CNSS,
        honoraires_document_id=42,
        payments=payments,
        template_version="CNSS-610-1-04",
    )


def _mapping(act, *, status, source_hash, code="D713", validator_id=None):
    return NgapCatalogMapping(
        catalog_act_id=act.id,
        code_kind="NGAP",
        ngap_code=code,
        coefficient=10.0,
        official_label=f"NGAP {code}",
        reference_version="arrete-177-06-test",
        mapping_rule_id=f"arrete-177-06-test:{act.id}",
        verification_status=status,
        source_authority="Ministere de la Sante",
        source_url="https://example.invalid/arrete.pdf",
        source_hash=source_hash,
        validated_by_practitioner_id=validator_id,
        validated_at=(datetime(2026, 9, 14, 19, 0) if validator_id is not None else None),
    )


def test_pending_reference_keeps_draft_incomplete(db):
    act = _catalog_act(db, name="Pending draft")
    db.add(_mapping(act, status="PRIMARY_HASH_PENDING", source_hash=None))
    db.flush()

    result = apply_ngap_reference_to_draft(
        db,
        draft=_draft([act.id]),
        reference_version="arrete-177-06-test",
    )

    assert result.status == InsuranceDraftStatus.INCOMPLETE
    assert result.lines[0].mapping_status == InsuranceMappingStatus.OUTDATED
    assert result.reference.ngap_reference_version == "arrete-177-06-test"
    assert result.reference.ngap_reference_hash is None
    assert "lines[0].ngap:OUTDATED" in result.unresolved_fields


def test_verified_reference_promotes_complete_draft_to_review(db, dentiste):
    act = _catalog_act(db, name="Verified draft")
    db.add(_mapping(
        act,
        status="VERIFIED_PRIMARY",
        source_hash="c" * 64,
        validator_id=dentiste.id,
    ))
    db.flush()

    result = apply_ngap_reference_to_draft(
        db,
        draft=_draft([act.id]),
        reference_version="arrete-177-06-test",
    )

    assert result.status == InsuranceDraftStatus.READY_FOR_REVIEW
    assert result.unresolved_fields == []
    assert result.lines[0].mapping_status == InsuranceMappingStatus.EXACT
    assert result.lines[0].ngap_code == "D713"
    assert result.lines[0].mapping_rule_id == f"arrete-177-06-test:{act.id}"
    assert result.reference.ngap_reference_hash == "c" * 64


def test_mixed_hashes_for_same_reference_version_are_rejected(db, dentiste):
    first = _catalog_act(db, name="Hash A")
    second = _catalog_act(db, name="Hash B")
    db.add(_mapping(
        first,
        status="VERIFIED_PRIMARY",
        source_hash="a" * 64,
        code="D713",
        validator_id=dentiste.id,
    ))
    db.add(_mapping(
        second,
        status="VERIFIED_PRIMARY",
        source_hash="b" * 64,
        code="D714",
        validator_id=dentiste.id,
    ))
    db.flush()

    with pytest.raises(ValueError, match="plusieurs hashes"):
        apply_ngap_reference_to_draft(
            db,
            draft=_draft([first.id, second.id]),
            reference_version="arrete-177-06-test",
        )
