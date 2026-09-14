from datetime import datetime, timedelta
from time import perf_counter

from sqlalchemy import event

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.services.clinical_asset_service import (
    get_clinical_asset_for_patient,
    list_clinical_assets_for_patient,
)

C7_VOLUME_ASSETS = 5_000
C7_FOREIGN_ASSETS = 500
C7_PAGE_SIZE = 200
C7_DEEP_OFFSET = 4_800
C7_MAX_OPERATION_SECONDS = 2.0


def _patient(db, employer_id: int):
    patient = models.Patient(
        numero_dossier="C7-VOLUME",
        nom="Synthetic",
        prenom="Volume",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _stored_asset(*, employer_id: int, patient_id: int, index: int, marker: str = "") -> ClinicalAsset:
    captured = datetime(2026, 1, 1) + timedelta(minutes=index)
    return ClinicalAsset(
        employer_id=employer_id,
        patient_id=patient_id,
        asset_type="RADIOGRAPH" if index % 5 == 0 else "PHOTO",
        source_kind="DEVICE_CAPTURE" if index % 7 == 0 else "UPLOAD",
        source_ref=f"C7-{marker}-{index}" if marker else f"C7-{index}",
        original_filename=f"clinical-{marker}-{index}.png" if marker else f"clinical-{index}.png",
        mime_type="image/png",
        byte_size=1024,
        sha256=f"{index + employer_id:064x}"[-64:],
        storage_key=f"c7/{employer_id}/{index}.bin",
        storage_format="AESGCM_V1",
        stored_at=captured,
        timepoint=("T2" if index % 3 == 0 else "T1" if index % 3 == 1 else "T0"),
        captured_at=captured,
        created_at=captured,
    )


def _timed(callable_):
    start = perf_counter()
    result = callable_()
    elapsed = perf_counter() - start
    assert elapsed < C7_MAX_OPERATION_SECONDS, f"C7 operation took {elapsed:.3f}s"
    return result, elapsed


def test_c7_volume_pagination_search_filters_query_scaling_and_cross_tenant(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste.id)
    foreign = models.User(
        email="media-c7-foreign@cabinet.ma",
        hashed_password=dentiste.hashed_password,
        role="DENTISTE",
        nom_complet="Dr Foreign C7",
        is_active=True,
        is_licensed=True,
    )
    db.add(foreign)
    db.commit()
    db.refresh(foreign)

    rows = [_stored_asset(employer_id=dentiste.id, patient_id=patient.id, index=i) for i in range(C7_VOLUME_ASSETS)]
    rows += [_stored_asset(employer_id=foreign.id, patient_id=patient.id, index=10_000 + i, marker="FOREIGN") for i in range(C7_FOREIGN_ASSETS)]
    db.bulk_save_objects(rows)
    db.commit()

    newest, newest_elapsed = _timed(lambda: list_clinical_assets_for_patient(db, employer_id=dentiste.id, patient_id=patient.id, limit=C7_PAGE_SIZE, offset=0))
    second, second_elapsed = _timed(lambda: list_clinical_assets_for_patient(db, employer_id=dentiste.id, patient_id=patient.id, limit=C7_PAGE_SIZE, offset=C7_PAGE_SIZE))
    deep, deep_elapsed = _timed(lambda: list_clinical_assets_for_patient(db, employer_id=dentiste.id, patient_id=patient.id, limit=C7_PAGE_SIZE, offset=C7_DEEP_OFFSET))

    assert len(newest) == len(second) == len(deep) == C7_PAGE_SIZE
    assert {asset.id for asset in newest}.isdisjoint(asset.id for asset in second)
    expected_ids = [asset.id for asset in db.query(ClinicalAsset).filter(ClinicalAsset.employer_id == dentiste.id, ClinicalAsset.patient_id == patient.id).order_by(ClinicalAsset.captured_at.desc(), ClinicalAsset.id.desc()).all()]
    assert [asset.id for asset in newest + second] == expected_ids[: C7_PAGE_SIZE * 2]
    assert [asset.id for asset in deep] == expected_ids[C7_DEEP_OFFSET : C7_DEEP_OFFSET + C7_PAGE_SIZE]

    marker = db.query(ClinicalAsset).filter(ClinicalAsset.employer_id == dentiste.id, ClinicalAsset.patient_id == patient.id, ClinicalAsset.source_ref == "C7-100").one()
    marker.original_filename = "C7-UNIQUE-DEEP-MARKER.png"
    db.commit()
    searched, search_elapsed = _timed(lambda: list_clinical_assets_for_patient(db, employer_id=dentiste.id, patient_id=patient.id, limit=C7_PAGE_SIZE, search="UNIQUE-DEEP-MARKER"))
    assert [asset.id for asset in searched] == [marker.id]

    filtered, filter_elapsed = _timed(lambda: list_clinical_assets_for_patient(db, employer_id=dentiste.id, patient_id=patient.id, limit=C7_PAGE_SIZE, asset_type="RADIOGRAPH", source_kind="DEVICE_CAPTURE", timepoint="T2"))
    assert filtered
    assert all(asset.employer_id == dentiste.id and asset.asset_type == "RADIOGRAPH" and asset.source_kind == "DEVICE_CAPTURE" and asset.timepoint == "T2" for asset in filtered)

    foreign_asset = db.query(ClinicalAsset).filter(ClinicalAsset.employer_id == foreign.id, ClinicalAsset.patient_id == patient.id).first()
    assert foreign_asset is not None
    assert get_clinical_asset_for_patient(db, employer_id=dentiste.id, patient_id=patient.id, asset_id=foreign_asset.id) is None
    forbidden = client.get(f"/api/patients/{patient.id}/assets/{foreign_asset.id}/content", headers=auth_headers)
    assert forbidden.status_code == 404

    engine = db.get_bind()
    select_counts = []
    for limit in (1, C7_PAGE_SIZE):
        count = 0
        def before_cursor_execute(_conn, _cursor, statement, _params, _context, _executemany):
            nonlocal count
            if statement.lstrip().upper().startswith("SELECT"):
                count += 1
        event.listen(engine, "before_cursor_execute", before_cursor_execute)
        try:
            list_clinical_assets_for_patient(db, employer_id=dentiste.id, patient_id=patient.id, limit=limit, offset=0)
        finally:
            event.remove(engine, "before_cursor_execute", before_cursor_execute)
        select_counts.append(count)
    assert select_counts[0] == select_counts[1] == 2

    print("C7_METRICS " f"volume={C7_VOLUME_ASSETS} foreign={C7_FOREIGN_ASSETS} " f"newest={newest_elapsed:.4f}s second={second_elapsed:.4f}s deep={deep_elapsed:.4f}s " f"search={search_elapsed:.4f}s filter={filter_elapsed:.4f}s selects={select_counts[0]}")
