"""G3 offline tests: pair matching, source scope, expert coordinates.

No image generated here is passed off as a real cephalogram, and no data are
downloaded. The live HTTP range/MD5 path is verified separately in G3 CI.
"""
import json
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from backend.services.ortho_lab_image_integrity import (
    verified_aariz_display_image_pair, build_verified_aariz_research_plate,
)
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from PIL import Image
from scripts.odf_v5_g3_aariz_matched_pair import _paired_names, _landmarks, AARIZ_TO_DC

def _case(prefix, stem="029"):
    return [
        f"{prefix}/Cephalograms/{stem}.png",
        f"{prefix}/Annotations/Cephalometric Landmarks/Junior Orthodontists/{stem}.json",
        f"{prefix}/Annotations/Cephalometric Landmarks/Senior Orthodontists/{stem}.json",
    ]

class AarizMatchedSourceContract(unittest.TestCase):
    def test_image_byte_change_revokes_paired_expert_results(self):
        with TemporaryDirectory() as tmp:
            file=Path(tmp)/"trace-paired-demo.png"
            file.write_bytes(b"synthetic-bytes-not-an-image")
            data={
                "odf_lab_image_landmark_alignment":"VERIFIED_AARIZ_EXPERT_PAIR",
                "odf_lab_dataset_image_id":"Aariz/Valid/Cephalograms/029.png",
                "odf_lab_display_png_sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
                "odf_lab_source_image_sha256":"1"*64,
                "odf_lab_source_senior_sha256":"2"*64,
                "odf_lab_source_junior_sha256":"3"*64,
            }
            self.assertTrue(verified_aariz_display_image_pair(data,file))
            file.write_bytes(b"swapped-image")
            self.assertFalse(verified_aariz_display_image_pair(data,file))
            data["odf_lab_image_landmark_alignment"]="UNVERIFIED"
            self.assertFalse(verified_aariz_display_image_pair(data,file))

    def test_research_plate_is_evidence_bound_and_never_uses_an_arbitrary_image(self):
        # Only synthetic pixels in this test. The end-to-end lab separately
        # proves actual source-matched Aariz expert annotation provenance.
        from base64 import b64decode
        with TemporaryDirectory() as tmp:
            film=Path(tmp)/"demo.png"
            Image.new("RGB",(1935,2400),(18,27,33)).save(film)
            symbols=("S","N","A","B","Po","Or","Go","Me","Gn",
                     "U1_incisal","L1_incisal","U1_apex","L1_apex",
                     "ANS","PNS","Co","Ar","Li_soft","Ls_soft")
            points=[{"landmark_id":name,"x":200+i*30,"y":400+i*53}
                    for i,name in enumerate(symbols)]
            evidence={
                "odf_lab_image_landmark_alignment":"VERIFIED_AARIZ_EXPERT_PAIR",
                "odf_lab_dataset_image_id":"Aariz/test/Cephalograms/demo.png",
                "odf_lab_display_png_sha256":hashlib.sha256(film.read_bytes()).hexdigest(),
                "odf_lab_source_image_sha256":"a"*64,
                "odf_lab_source_senior_sha256":"b"*64,
                "odf_lab_source_junior_sha256":"c"*64,
                EVIDENCE_GRAPH_KEY:{"landmarks":points},
            }
            plate=build_verified_aariz_research_plate(evidence,film)
            self.assertIsNotNone(plate)
            self.assertIn("Aariz",plate["caption"])
            self.assertTrue(b64decode(plate["image_b64"]).startswith(bytes((255, 216))))
            film.write_bytes(b"forged-bytes")
            self.assertIsNone(build_verified_aariz_research_plate(evidence,film))
            Image.new("RGB",(1935,2400),(18,27,33)).save(film)
            evidence[EVIDENCE_GRAPH_KEY]["landmarks"][0]["x"]=999999
            self.assertIsNone(build_verified_aariz_research_plate(evidence,film))

    def test_requires_exact_film_id_and_two_expert_files(self):
        names=_case("Aariz/Train","013")+_case("Aariz/Valid","029")
        image,senior,junior=_paired_names(names)
        self.assertIn("/Valid/",image)
        self.assertTrue(senior.endswith("/029.json"))
        self.assertTrue(junior.endswith("/029.json"))

    def test_rejects_film_without_its_own_annotations(self):
        names=["Aariz/Valid/Cephalograms/029.png"]
        names += _case("Aariz/Train","013")[1:]
        with self.assertRaisesRegex(RuntimeError,"NO_SINGLE_IMAGE_PAIRED"):
            _paired_names(names)

    def test_expert_symbols_have_known_explicit_mapping(self):
        for symbol,dc in {
            "S":"S", "N":"N", "A":"A", "B":"B", "UIT":"U1_incisal",
            "LIT":"L1_incisal", "UIA":"U1_apex", "LIA":"L1_apex",
        }.items():
            self.assertEqual(AARIZ_TO_DC[symbol],dc)

    def test_rejects_duplicate_expert_markers(self):
        data={"landmarks":[{"symbol":"S","value":{"x":21,"y":34}},
                           {"symbol":"S","value":{"x":22,"y":35}}]}
        with self.assertRaisesRegex(ValueError,"DUPLICATE_ANNOTATION"):
            _landmarks(json.dumps(data).encode())

    def test_unrecognized_json_does_not_create_fabricated_marks(self):
        valid={"landmarks":[{"symbol":"S","value":{"x":22.0,"y":33.0}},
                            {"symbol":"INVENTED","value":{"x":10,"y":8}}]}
        self.assertEqual(_landmarks(json.dumps(valid).encode()),{"S":(22.0,33.0)})
        for data in ([],{},{"landmarks":"this is not an annotation"}):
            with self.assertRaises(ValueError):
                _landmarks(json.dumps(data).encode())

if __name__=="__main__":
    unittest.main()
