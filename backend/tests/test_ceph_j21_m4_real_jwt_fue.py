"""J2.1-M4 genuine service adapter: synthetic patient and encrypted media only.

A real FastAPI/JWT media import and DC-DOS-05 read are used inside an
isolated test session; the candidate route is mounted transiently and removed.
No patient data, production table migration or clinical release.
"""
from __future__ import annotations

from io import BytesIO
import hashlib

import pytest
from PIL import Image

from backend.models_media_core import ClinicalAsset
from backend.main import app
from backend.routers.cephalo_study_media_binding import router as candidate_router
from backend.services.ceph_premium_scene_source_lab import (
    SceneSourceRejected, verify_via_dc_dos05,
)
from backend.services.srpose38_contract import SOTA_LANDMARKS_MAPPING, SRPOSE38_MODEL_SHA256
from backend.schemas.cephalo_premium_scene_contract import CephaloPremiumSceneDraft
from backend.tests.p2ter_bridge_synthetic_support import _case, _read, _jwt
from backend.tests.conftest import make_user


def _real_encrypted_test_png():
    buf=BytesIO()
    Image.new("RGB",(800,600),(80,117,143)).save(buf,format="PNG")
    return buf.getvalue()


def _scene_for_binding(user,patient,study,revision,asset,data):
    return CephaloPremiumSceneDraft.model_validate({
        "schema_version":"CEPH_PREMIUM_SCENE_V1_DRAFT",
        "identity":{
            "employer_id":user.get_employer_id(),"patient_id":patient.id,
            "study_id":study.id,"original_asset_id":asset["id"],
            "original_sha256":hashlib.sha256(data).hexdigest(),
            "original_width":800,"original_height":600,
            "scientific_revision":revision,"scientific_digest":"b"*64,
            "scene_revision":1,"parent_scene_sha256":None,
            "coordinate_system":"SOURCE_IMAGE_PIXELS_TOP_LEFT",
            "detector_model":"srpose38-tta-1024.onnx",
            "detector_sha256":SRPOSE38_MODEL_SHA256,
            "detector_mapping_authority":"LEGACY_LOCAL_UNVERIFIED"
        },
        "landmarks":[
            {"id":name,"x":float(25+i*5),"y":float(35+i*4),
             "origin":"SRPOSE38_AUTO","score_status":"NOT_EMITTED"}
            for i,name in SOTA_LANDMARKS_MAPPING.items()
        ],
        "contours":[],"measurements":[],"constructions":[],
        "document_status":"NONCLINICAL_DRAFT","clinical_release":False
    })


def test_m4_real_authenticated_dc_dos05_encrypted_original_read(
    client,db,dentiste,auth_headers,monkeypatch,tmp_path
):
    monkeypatch.setenv("DC_DOS05_FUE_ONLY","1")
    monkeypatch.setenv("ENVIRONMENT","test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME","true")
    monkeypatch.setenv("SECRET_KEY","j21-m4-test-only-media-encryption-never-production")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root",lambda:tmp_path)
    routes=list(app.router.routes)
    app.include_router(candidate_router,prefix="/api/ia")
    try:
        patient,study,_=_case(db,dentiste)
        _,science=_read(client,study.id,auth_headers)
        revision=science["revision"]
        original=_real_encrypted_test_png()
        uploaded=client.post(
            f"/api/patients/{patient.id}/assets/import",headers=auth_headers,
            data={"asset_type":"RADIOGRAPH","source_kind":"UPLOAD","timepoint":"T0"},
            files={"file":("j21-m4-only-fictitious.png",original,"image/png")}
        )
        assert uploaded.status_code==201,uploaded.text[:500]
        asset=uploaded.json()
        asset_row=db.get(ClinicalAsset,asset["id"])
        assert asset_row.storage_format=="AESGCM_V1"
        assert asset_row.storage_key and asset_row.sha256==hashlib.sha256(original).hexdigest()
        ciphertext_file=tmp_path.joinpath(*asset_row.storage_key.split("/"))
        encrypted=ciphertext_file.read_bytes()
        assert encrypted.startswith(b"DCM1")
        assert encrypted!=original and original not in encrypted
        assert len(encrypted)>len(original)
        scene=_scene_for_binding(dentiste,patient,study,revision,asset,original)
        with pytest.raises(ValueError):
            verify_via_dc_dos05(
                db,scene=scene,
                actor_employer_id=dentiste.get_employer_id(),
                actor_patient_id=patient.id,actor_study_id=study.id)
        bonded=client.post(
            f"/api/ia/analyses/{study.id}/media-bindings/RADIO_SOURCE",
            headers=auth_headers,
            json={"patient_id":patient.id,"asset_id":asset["id"],
                  "expected_revision":revision},
        )
        assert bonded.status_code==201,bonded.text[:500]
        endpoint=f"/api/ia/analyses/{study.id}/media-bindings"
        # Login uses both bearer and session cookie; clear the cookie to test anonymous access.
        client.cookies.clear()
        assert client.get(endpoint,params={"patient_id":patient.id}).status_code==401
        outsider=make_user(db,email="j21-m4-unauthorized@cabinet.invalid")
        outsider_jwt=_jwt(client,outsider)
        assert client.get(endpoint,headers=outsider_jwt,params={"patient_id":patient.id}).status_code==403
        att=verify_via_dc_dos05(
            db,scene=scene,actor_employer_id=dentiste.get_employer_id(),
            actor_patient_id=patient.id,actor_study_id=study.id,
        )
        assert att["image_sha256"]==hashlib.sha256(original).hexdigest()
        assert (att["source_width"],att["source_height"])==(800,600)
        assert att["study_revision"]==revision
        assert att["clinical_release"] is False
        assert att["image_used_by_srpose38_inference_verified"] is False
        for forged in (
            (dentiste.get_employer_id(),patient.id+1,study.id),
            (dentiste.get_employer_id(),patient.id,study.id+1),
            (dentiste.get_employer_id()+100,patient.id,study.id),
        ):
            with pytest.raises(SceneSourceRejected):
                verify_via_dc_dos05(
                    db,scene=scene,actor_employer_id=forged[0],
                    actor_patient_id=forged[1],actor_study_id=forged[2])
        damaged=scene.model_copy(update={
            "identity":scene.identity.model_copy(update={"original_sha256":"f"*64})
        })
        with pytest.raises(SceneSourceRejected):
            verify_via_dc_dos05(
                db,scene=damaged,actor_employer_id=dentiste.get_employer_id(),
                actor_patient_id=patient.id,actor_study_id=study.id)
        modified=bytearray(encrypted)
        modified[-1]^=1
        ciphertext_file.write_bytes(modified)
        with pytest.raises(ValueError,match="Media ciphertext/integrity verification failed"):
            verify_via_dc_dos05(db,scene=scene,actor_employer_id=dentiste.get_employer_id(),
                               actor_patient_id=patient.id,actor_study_id=study.id)
        ciphertext_file.write_bytes(encrypted)
        assert verify_via_dc_dos05(db,scene=scene,actor_employer_id=dentiste.get_employer_id(),
                                   actor_patient_id=patient.id,actor_study_id=study.id)["image_sha256"]==asset_row.sha256
    finally:
        app.router.routes=routes
