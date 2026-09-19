from datetime import datetime

import pytest

from backend import models
from backend.services.cephalo_superimposition_source import (
    SuperimpositionSourceError,
    resolve_superimposition_pair,
)


def _seed_pair(
    db,
    dentiste,
    *,
    birth_date=datetime(1990, 1, 1),
    calibrated_from=True,
    calibrated_to=True,
):
    patient = models.Patient(
        nom="F5",
        prenom="Source",
        date_naissance=birth_date,
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=True))

    case = models.OrthoCase(
        employer_id=dentiste.id,
        patient_id=patient.id,
        started_at=datetime(2025, 1, 1, 9, 0, 0),
        lifecycle_status="ACTIVE",
        current_phase_key="ALIGNEMENT",
        created_by=dentiste.id,
    )
    db.add(case)
    db.flush()

    t0 = models.OrthoTimepoint(
        ortho_case_id=case.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        ordinal=0,
        occurred_at=datetime(2025, 1, 10, 9, 0, 0),
        created_by=dentiste.id,
    )
    t1 = models.OrthoTimepoint(
        ortho_case_id=case.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        ordinal=1,
        occurred_at=datetime(2026, 1, 10, 9, 0, 0),
        created_by=dentiste.id,
    )
    db.add_all([t0, t1])
    db.flush()

    a0 = models.CephaloAnalysis(
        patient_id=patient.id,
        image_original_path="media/cephalo/f5-t0.png",
        landmarks_data={},
        angles_data={},
        is_calibrated=calibrated_from,
        mm_per_pixel=0.1 if calibrated_from else None,
        calibration_data={"method": "MANUAL_TWO_POINT"} if calibrated_from else None,
    )
    a1 = models.CephaloAnalysis(
        patient_id=patient.id,
        image_original_path="media/cephalo/f5-t1.png",
        landmarks_data={},
        angles_data={},
        is_calibrated=calibrated_to,
        mm_per_pixel=0.1 if calibrated_to else None,
        calibration_data={"method": "MANUAL_TWO_POINT"} if calibrated_to else None,
    )
    db.add_all([a0, a1])
    db.flush()

    e0 = models.OrthoTimepointEvidence(
        ortho_timepoint_id=t0.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        cephalo_analysis_id=a0.id,
        created_by=dentiste.id,
    )
    e1 = models.OrthoTimepointEvidence(
        ortho_timepoint_id=t1.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        cephalo_analysis_id=a1.id,
        created_by=dentiste.id,
    )
    db.add_all([e0, e1])
    db.commit()
    return patient, case, t0, t1, a0, a1


def test_resolver_returns_two_canonical_adult_cephalo_sources(db, dentiste):
    patient, case, t0, t1, a0, a1 = _seed_pair(db, dentiste)

    pair = resolve_superimposition_pair(
        db,
        patient_id=patient.id,
        case_id=case.id,
        employer_id=dentiste.id,
        from_timepoint_id=t0.id,
        to_timepoint_id=t1.id,
    )

    assert pair.from_source.cephalo_analysis_id == a0.id
    assert pair.to_source.cephalo_analysis_id == a1.id
    assert pair.from_source.image_original_path.endswith("f5-t0.png")
    assert pair.to_source.image_original_path.endswith("f5-t1.png")
    assert pair.quantitative_mm_allowed is True
    assert pair.applicability_status == "ADULT_ENGINEERING_SCOPE_ONLY"


def test_uncalibrated_source_allows_visual_source_resolution_but_blocks_mm(db, dentiste):
    patient, case, t0, t1, _, _ = _seed_pair(
        db,
        dentiste,
        calibrated_from=False,
        calibrated_to=True,
    )

    pair = resolve_superimposition_pair(
        db,
        patient_id=patient.id,
        case_id=case.id,
        employer_id=dentiste.id,
        from_timepoint_id=t0.id,
        to_timepoint_id=t1.id,
    )

    assert pair.quantitative_mm_allowed is False
    assert pair.from_source.is_calibrated is False
    assert pair.from_source.mm_per_pixel is None


def test_growing_patient_fails_closed(db, dentiste):
    patient, case, t0, t1, _, _ = _seed_pair(
        db,
        dentiste,
        birth_date=datetime(2010, 1, 1),
    )

    with pytest.raises(SuperimpositionSourceError) as error:
        resolve_superimposition_pair(
            db,
            patient_id=patient.id,
            case_id=case.id,
            employer_id=dentiste.id,
            from_timepoint_id=t0.id,
            to_timepoint_id=t1.id,
        )

    assert error.value.code == "POPULATION_NOT_VALIDATED"


def test_multiple_cephalo_evidences_are_ambiguous_and_fail_closed(db, dentiste):
    patient, case, t0, t1, _, _ = _seed_pair(db, dentiste)
    extra = models.CephaloAnalysis(
        patient_id=patient.id,
        image_original_path="media/cephalo/f5-extra.png",
        landmarks_data={},
        angles_data={},
        is_calibrated=False,
    )
    db.add(extra)
    db.flush()
    db.add(
        models.OrthoTimepointEvidence(
            ortho_timepoint_id=t0.id,
            employer_id=dentiste.id,
            patient_id=patient.id,
            cephalo_analysis_id=extra.id,
            created_by=dentiste.id,
        )
    )
    db.commit()

    with pytest.raises(SuperimpositionSourceError) as error:
        resolve_superimposition_pair(
            db,
            patient_id=patient.id,
            case_id=case.id,
            employer_id=dentiste.id,
            from_timepoint_id=t0.id,
            to_timepoint_id=t1.id,
        )

    assert error.value.code == "CEPHALO_EVIDENCE_AMBIGUOUS"


def test_invalid_calibration_provenance_fails_closed(db, dentiste):
    patient, case, t0, t1, a0, _ = _seed_pair(db, dentiste)
    a0.mm_per_pixel = None
    a0.is_calibrated = True
    db.commit()

    with pytest.raises(SuperimpositionSourceError) as error:
        resolve_superimposition_pair(
            db,
            patient_id=patient.id,
            case_id=case.id,
            employer_id=dentiste.id,
            from_timepoint_id=t0.id,
            to_timepoint_id=t1.id,
        )

    assert error.value.code == "INVALID_CALIBRATION"


def test_wrong_timepoint_direction_fails_closed(db, dentiste):
    patient, case, t0, t1, _, _ = _seed_pair(db, dentiste)

    with pytest.raises(SuperimpositionSourceError) as error:
        resolve_superimposition_pair(
            db,
            patient_id=patient.id,
            case_id=case.id,
            employer_id=dentiste.id,
            from_timepoint_id=t1.id,
            to_timepoint_id=t0.id,
        )

    assert error.value.code == "TIMEPOINT_ORDER_INVALID"


def test_same_timepoint_fails_closed(db, dentiste):
    patient, case, t0, _, _, _ = _seed_pair(db, dentiste)

    with pytest.raises(SuperimpositionSourceError) as error:
        resolve_superimposition_pair(
            db,
            patient_id=patient.id,
            case_id=case.id,
            employer_id=dentiste.id,
            from_timepoint_id=t0.id,
            to_timepoint_id=t0.id,
        )

    assert error.value.code == "SAME_TIMEPOINT"
