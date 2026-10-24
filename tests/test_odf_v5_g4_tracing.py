"""G4 tracing hard gates; wholly artificial coordinates (not a clinical film)."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from backend.services.ortho_ceph_tracing import (
    TRACE_CONTRACT, REQUIRED_SEGMENTS, trace_geometry_from_evidence,
    draw_trace_overlay,
)
from backend.services.ortho_lab_image_integrity import (
    build_verified_aariz_research_plate,
)
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def marker_fixture():
    # These points ONLY exercise 2D mechanics and are not from any patient.
    names=[
        "S","N","A","B","Po","Or","Go","Me","Gn",
        "U1_apex","U1_incisal","L1_apex","L1_incisal",
        "ANS","PNS","Co","Ar","Li_soft","Ls_soft",
    ]
    return [
        {"landmark_id":name,"x":float(180+i*45),"y":float(350+i*83)}
        for i,name in enumerate(names)
    ]


def study_for(film,points):
    return {
        "odf_lab_image_landmark_alignment":"VERIFIED_AARIZ_EXPERT_PAIR",
        "odf_lab_dataset_image_id":"Aariz/test/Cephalograms/geometry-fixture.png",
        "odf_lab_display_png_sha256":hashlib.sha256(film.read_bytes()).hexdigest(),
        "odf_lab_source_image_sha256":"a"*64,
        "odf_lab_source_senior_sha256":"b"*64,
        "odf_lab_source_junior_sha256":"c"*64,
        EVIDENCE_GRAPH_KEY:{"landmarks":points},
    }


class SourceBoundG4TracingTests(unittest.TestCase):
    def test_clinical_plans_from_same_image_exact_endpoints(self):
        points=marker_fixture()
        model=trace_geometry_from_evidence(points,(1935,2400))
        self.assertIsNotNone(model)
        self.assertEqual(model["contract"],TRACE_CONTRACT)
        self.assertTrue(REQUIRED_SEGMENTS.issubset({s["label"] for s in model["segments"]}))
        for seg in model["segments"]:
            self.assertEqual(seg["from_xy"],list(model["landmarks"][seg["from"]]))
            self.assertEqual(seg["to_xy"],list(model["landmarks"][seg["to"]]))
        self.assertFalse(any("contour" in s["label"].lower() for s in model["segments"]))
        reversed_model=trace_geometry_from_evidence(list(reversed(points)),(1935,2400))
        self.assertEqual(model["geometry_sha256"],reversed_model["geometry_sha256"])

    def test_missing_landmark_duplicates_and_degenerate_plan_fail_closed(self):
        original=marker_fixture()
        for mutated in (
            original[:-1] + [deepcopy(original[0])],
            [p for p in original if p["landmark_id"]!="Po"],
            original+[{"landmark_id":"S","x":100.0,"y":200.0}],
        ):
            self.assertIsNone(trace_geometry_from_evidence(mutated,(1935,2400)))
        invalid=deepcopy(original)
        invalid[0]["x"]=1935.0
        self.assertIsNone(trace_geometry_from_evidence(invalid,(1935,2400)))
        invalid=deepcopy(original)
        invalid[0]["x"]=float("nan")
        self.assertIsNone(trace_geometry_from_evidence(invalid,(1935,2400)))
        invalid=deepcopy(original)
        invalid[0]["x"]=invalid[1]["x"]
        invalid[0]["y"]=invalid[1]["y"]
        self.assertIsNone(trace_geometry_from_evidence(invalid,(1935,2400)))
        invalid=deepcopy(original)
        invalid[0]["x"]=True
        self.assertIsNone(trace_geometry_from_evidence(invalid,(1935,2400)))

    def test_no_unverified_fake_contours_or_invented_paired_image(self):
        with TemporaryDirectory() as tmp:
            image_file=Path(tmp)/"trace-fixture.png"
            Image.new("RGB",(1935,2400),(25,36,44)).save(image_file)
            metadata=study_for(image_file,marker_fixture())
            plate=build_verified_aariz_research_plate(metadata,image_file)
            self.assertIsNotNone(plate)
            self.assertEqual(plate["kind"],"GEOMETRIC_CEPHALOMETRIC_TRACING")
            self.assertTrue(REQUIRED_SEGMENTS.issubset(set(plate["segments"])))
            self.assertEqual(plate["segment_count"],9)
            self.assertEqual(plate["landmark_count"],19)
            self.assertEqual(plate["source_image_sha256"],metadata["odf_lab_display_png_sha256"])
            self.assertIn("Contours anatomiques non tracés",plate["caption"])
            self.assertTrue(plate["data_uri"].startswith("data:image/jpeg;base64,"))
            from base64 import b64decode
            overlaid=Image.open(BytesIO(b64decode(plate["image_b64"])))
            self.assertEqual(overlaid.size,(1935,2400))
            # A colored pixel/overlay must be materially different from the plain image.
            self.assertNotEqual(overlaid.getpixel((180,350)),(25,36,44))
            image_file.write_bytes(b"swapped-film")
            self.assertIsNone(build_verified_aariz_research_plate(metadata,image_file))

    def test_wrong_study_graph_rejects_arbitrary_source_points(self):
        with TemporaryDirectory() as tmp:
            image_file=Path(tmp)/"another-fixture.png"
            Image.new("RGB",(1935,2400),(20,30,40)).save(image_file)
            study=study_for(image_file,marker_fixture())
            study[EVIDENCE_GRAPH_KEY]["landmarks"][0]["x"]=9999
            self.assertIsNone(build_verified_aariz_research_plate(study,image_file))
            study[EVIDENCE_GRAPH_KEY]["landmarks"]=marker_fixture()
            study["odf_lab_source_junior_sha256"]=None
            self.assertIsNone(build_verified_aariz_research_plate(study,image_file))


if __name__=="__main__":
    unittest.main()
