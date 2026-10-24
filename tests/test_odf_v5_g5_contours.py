"""G5 synthetic geometry CONTRACT tests — NEVER clinical contour annotations.

These tests test software mechanics, NOT anatomy quality or clinical sign-off.
No fake polylines are inserted into the real Aariz G3 laboratory database.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from unittest import TestCase, main

from PIL import Image

from backend.services.ortho_anatomical_trace import (
    CONTOUR_CONTRACT, CONTOUR_LABELS, MIN_POINTS, ContourRejected,
    canonical_digest,normalize_manual_contours,
    verify_approved_anatomical_trace,draw_contours,
)


def artificial_polylines():
    return [
        {"id":key,"points":[[100+i*200+j*9,200+i*235+j*12]
                             for j in range(MIN_POINTS[key]+3)]}
        for i,key in enumerate(CONTOUR_LABELS)
    ]


def signed_fixture(contours):
    normalized=normalize_manual_contours(contours,image_size=(1935,2400))
    record=dict(
        state="APPROVED",contract=CONTOUR_CONTRACT,
        source_mode="CLINICIAN_MANUAL",
        patient_id=17,analysis_id=42,analysis_revision=3,
        scientific_digest="2"*64,image_sha256="1"*64,
        image_size=[1935,2400],version=2,
        contour_digest=normalized["contour_digest"],
        contours=contours,
        approved_by=8,approved_at="2026-10-24T11:30:00Z",
    )
    record["approved_digest"]=canonical_digest([
        17,42,3,"2"*64,"1"*64,2,record["contour_digest"],8,
    ])
    return record


def verify(record):
    return verify_approved_anatomical_trace(record,
        patient_id=17,analysis_id=42,revision=3,
        scientific_digest="2"*64,image_sha256="1"*64,
        image_size=(1935,2400))


class AnatomicalContourContract(TestCase):
    def test_six_manual_curves_normalize_deterministically(self):
        p=artificial_polylines()
        a=normalize_manual_contours(p,image_size=(1935,2400))
        b=normalize_manual_contours(list(reversed(p)),image_size=(1935,2400))
        self.assertEqual(a["contour_digest"],b["contour_digest"])
        self.assertEqual([x["id"] for x in a["contours"]],list(CONTOUR_LABELS))
        self.assertEqual(len(a["contours"]),6)

    def test_refuses_incomplete_and_forged_contours(self):
        p=artificial_polylines()
        cases=[
            p[:-1],
            p[:-1]+[deepcopy(p[0])],              # duplicate ID
            [{**p[0],"id":"imaginary_skull"}]+p[1:],
            [{**p[0],"points":p[0]["points"][:2]}]+p[1:],
            [{**p[0],"points":[[-1,1]]+p[0]["points"][1:]}]+p[1:],
            [{**p[0],"points":[[1935,2]]+p[0]["points"][1:]}]+p[1:],
            [{**p[0],"points":[[True,2]]+p[0]["points"][1:]}]+p[1:],
            [{**p[0],"points":[[float('nan'),2]]+p[0]["points"][1:]}]+p[1:],
            [{**p[0],"points":[[float('inf'),2]]+p[0]["points"][1:]}]+p[1:],
            [{**p[0],"points":[p[0]["points"][0]]*len(p[0]["points"])}]+p[1:],
            [{**p[0],"points":p[0]["points"],"is_ai_certified":True}]+p[1:],
        ]
        for case in cases:
            with self.subTest(case=str(case[0])[:100]):
                with self.assertRaises(ContourRejected):
                    normalize_manual_contours(case,image_size=(1935,2400))

    def test_no_approval_without_exact_study_image_and_signature(self):
        good=signed_fixture(artificial_polylines())
        self.assertIsNotNone(verify(good))
        changes=[
            {"patient_id":99},{"analysis_id":43},{"analysis_revision":4},
            {"image_sha256":"f"*64},{"scientific_digest":"f"*64},
            {"state":"DRAFT"},{"source_mode":"AI_SEGMENTATION"},
            {"approved_by":None},{"version":3},
            {"contour_digest":"f"*64},{"approved_digest":"0"*64},
            {"image_size":[2400,1935]},
        ]
        for update in changes:
            with self.subTest(update=update):
                bad={**good,**update}
                self.assertIsNone(verify(bad))
        bad=deepcopy(good)
        bad["contours"][0]["points"][1][0]+=15
        self.assertIsNone(verify(bad))

    def test_only_supplied_manual_points_are_drawn_in_both_views(self):
        curves=normalize_manual_contours(artificial_polylines(),image_size=(1935,2400))
        for white in (True,False):
            image=Image.new("RGB",(1935,2400),"white" if white else "#202830")
            draw_contours(image,curves,background_is_white=white)
            f=BytesIO();image.save(f,"PNG")
            self.assertGreater(f.tell(),15000)
            self.assertEqual(image.size,(1935,2400))

    def test_no_contours_generated_from_landmarks(self):
        with self.assertRaises(ContourRejected):
            normalize_manual_contours(
                [{"id":key,"points":[[10,15],[30,35]]}
                 for key in CONTOUR_LABELS],image_size=(1935,2400))


if __name__=="__main__":
    main()
