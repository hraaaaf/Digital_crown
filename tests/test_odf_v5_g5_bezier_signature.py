"""G5 LAB V2: verify doctor-signed sampled geometry AND editable handle digest.

Pure synthetic fixtures, no application bootstrap, DB, patient, or clinical rating.
"""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from sys import modules
from unittest import TestCase
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]/"backend/services"


def load(name, filename):
    spec=spec_from_file_location(name,BASE/filename)
    assert spec and spec.loader
    mod=module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v1=load("odf_g5_anatomical_signature_pure","ortho_anatomical_trace.py")
v2=load("odf_g5_bezier_profile_signature_pure","ortho_g5_bezier_profile.py")

NODES=[
    {"anchor":[200,200],"incoming":[200,200],"outgoing":[250,220]},
    {"anchor":[390,340],"incoming":[310,270],"outgoing":[430,410]},
    {"anchor":[630,690],"incoming":[580,600],"outgoing":[630,690]},
]


def signed_record():
    contours=[]
    for i,(key,minimum) in enumerate(v1.MIN_POINTS.items()):
        pts=[[100+i*120+k*8,80+i*190+k*12] for k in range(minimum+4)]
        if key=="soft_tissue_profile":
            pts=v2.sample_bezier_profile(NODES,image_size=(1935,2400))
        contours.append({"id":key,"points":pts})
    normal=v1.normalize_manual_contours(contours,image_size=(1935,2400))
    record={
        "state":"APPROVED","contract":v1.CONTOUR_CONTRACT,
        "source_mode":"CLINICIAN_MANUAL",
        "patient_id":17,"analysis_id":42,"analysis_revision":3,
        "scientific_digest":"2"*64,"image_sha256":"1"*64,
        "image_size":[1935,2400],"version":2,
        "contour_digest":normal["contour_digest"],
        "contours":contours,
        "bezier_profile_nodes":deepcopy(NODES),
        "approved_by":8,"approved_at":"2026-10-24T11:30:00Z",
    }
    record["approved_digest"]=v1.canonical_digest([
        17,42,3,"2"*64,"1"*64,2,record["contour_digest"],8,
        v1.canonical_digest(v2.canonical_bezier_profile_nodes(
            NODES,image_size=(1935,2400))),
    ])
    return record


def verify(record):
    # Inject only the pure helper into its production import namespace while
    # the V1 verifier runs, avoiding backend/__init__ and real app dependencies.
    with patch.dict(modules,{"backend.services.ortho_g5_bezier_profile":v2}):
        return v1.verify_approved_anatomical_trace(
            record,patient_id=17,analysis_id=42,revision=3,
            scientific_digest="2"*64,image_sha256="1"*64,
            image_size=(1935,2400))


class V2DentistSignedControlsContract(TestCase):
    def test_valid_authored_handles_and_v1_points_can_be_signed(self):
        self.assertIsNotNone(verify(signed_record()))

    def test_swapped_handle_changes_are_not_covered_by_prior_signature(self):
        record=signed_record()
        record["bezier_profile_nodes"][1]["incoming"][0]+=10
        self.assertIsNone(verify(record))

    def test_v1_digest_cannot_be_reused_to_authorize_unsigned_v2_controls(self):
        record=signed_record()
        record["approved_digest"]=v1.canonical_digest([
            17,42,3,"2"*64,"1"*64,2,record["contour_digest"],8,
        ])
        self.assertIsNone(verify(record))

    def test_modified_v1_samples_invalidate_signed_bezier(self):
        record=signed_record()
        profile=next(c for c in record["contours"] if c["id"]=="soft_tissue_profile")
        profile["points"][10][0]+=1
        self.assertIsNone(verify(record))

    def test_legacy_v1_signed_record_remains_readable_without_handles(self):
        record=signed_record()
        record.pop("bezier_profile_nodes")
        record["approved_digest"]=v1.canonical_digest([
            17,42,3,"2"*64,"1"*64,2,record["contour_digest"],8,
        ])
        self.assertIsNotNone(verify(record))
