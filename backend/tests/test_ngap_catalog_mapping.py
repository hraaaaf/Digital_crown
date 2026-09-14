from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from backend import models
from backend.models_ngap_reference import NgapCatalogMapping
from backend.schemas.insurance_submission import InsuranceMappingStatus
from backend.services.ngap_reference import resolve_catalog_act_ngap


def _catalog_act(db, *, name="NGAP test act"):
    specialty = models.Specialty(name=f"Spec {name}")
    db.add(specialty)
    db.flush()
    act = models.CatalogAct(
        specialty_id=specialty.id,
        name=name,
        code="LEGACY-MIXED-CODE",
        base_price=500.0,
        is_active=True,
    )
    db.add(act)
    db.flush()
    return act


def _mapping(act, **overrides):
    values = {
        "catalog_act_id": act.id,
        "code_kind": "NGAP",
        "ngap_code": "D713",
        "coefficient": 10.0,
        "official_label": "Extraction dentaire de test",
        "requires_prior_approval": False,
        "requires_radiograph": False,
        "reference_version": "arrete-177-06-test",
        "mapping_rule_id": f"arrete-177-06-test:{act.id}",
        "verification_status": "PRIMARY_HASH_PENDING",
        "source_authority": "Ministere de la Sante",
        "source_url": "https://example.invalid/arrete.pdf",
        "source_hash": None,
        "validated_by_practitioner_id": None,
        "validated_at": None,
    }
    values.update(overrides)
    return NgapCatalogMapping(**values)


def test_pending_primary_mapping_fails_closed_as_outdated(db):
    act = _catalog_act(db, name="Pending")
    db.add(_mapping(act))
    db.flush()

    resolution = resolve_catalog_act_ngap(
        db,
        catalog_act_id=act.id,
        reference_version="arrete-177-06-test",
    )
    assert resolution.status == InsuranceMappingStatus.OUTDATED
    assert resolution.code is None


def test_verified_primary_mapping_resolves_exact_by_catalog_id_only(db, dentiste):
    act = _catalog_act(db, name="Verified")
    db.add(_mapping(
        act,
        verification_status="VERIFIED_PRIMARY",
        source_hash="a" * 64,
        requires_radiograph=True,
        validated_by_practitioner_id=dentiste.id,
        validated_at=datetime(2026, 9, 14, 19, 0),
    ))
    db.flush()

    resolution = resolve_catalog_act_ngap(
        db,
        catalog_act_id=act.id,
        reference_version="arrete-177-06-test",
    )
    assert resolution.status == InsuranceMappingStatus.EXACT
    assert resolution.code == "D713"
    assert resolution.coefficient == 10.0
    assert resolution.release_hash == "a" * 64
    assert resolution.requires_radiograph is True
    assert act.code == "LEGACY-MIXED-CODE"


def test_non_ngap_classification_never_becomes_exact(db, dentiste):
    act = _catalog_act(db, name="Internal")
    db.add(_mapping(
        act,
        code_kind="INTERNAL",
        ngap_code=None,
        coefficient=None,
        verification_status="VERIFIED_PRIMARY",
        source_hash="b" * 64,
        validated_by_practitioner_id=dentiste.id,
        validated_at=datetime(2026, 9, 14, 19, 0),
    ))
    db.flush()

    resolution = resolve_catalog_act_ngap(
        db,
        catalog_act_id=act.id,
        reference_version="arrete-177-06-test",
    )
    assert resolution.status == InsuranceMappingStatus.NO_MATCH


def test_database_rejects_verified_primary_mapping_without_sha256(db, dentiste):
    act = _catalog_act(db, name="Bad hash")
    db.add(_mapping(
        act,
        verification_status="VERIFIED_PRIMARY",
        source_hash=None,
        validated_by_practitioner_id=dentiste.id,
        validated_at=datetime(2026, 9, 14, 19, 0),
    ))

    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_database_rejects_verified_primary_mapping_without_practitioner_validation(db):
    act = _catalog_act(db, name="No validation")
    db.add(_mapping(
        act,
        verification_status="VERIFIED_PRIMARY",
        source_hash="c" * 64,
    ))

    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
