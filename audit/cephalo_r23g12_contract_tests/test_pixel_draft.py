"""Only synthetic metadata; original JPEGs and browser clicks tested separately in CI."""
import copy
import unittest
from pathlib import Path
from scripts.cephalo_r23g12_public_manual_workbook import (
    PROFILE, SCHEMA, build_catalog, verify_draft, require,
)
from scripts.cephalo_r23g10_annotation_intake import G9_REL, load

ROOT = Path(__file__).resolve().parents[2]
G9 = load(ROOT / G9_REL)

def sample():
    ids=G9["identities_without_strict_mapping"]
    catalog={"profile_id": PROFILE,"required_source_ids": ids,
             "cases":[{"id":"anug","sha256":"a"*64,"width":2272,"height":1818},
                      {"id":"challiyan","sha256":"b"*64,"width":1000,"height":1255}]}
    records=[]
    for case in catalog["cases"]:
        records.append({
            "source_case":case["id"],"source_image_sha256":case["sha256"],
            "source_image_dimensions_px":{"width":case["width"],"height":case["height"]},
            "coordinate_system":"ORIGINAL_IMAGE_PIXEL_X_RIGHT_Y_DOWN",
            "landmarks":{},"missing_source_specific_ids":list(ids),
            "annotation_status":"MANUAL_DRAFT_UNVERIFIED",
            "image_orientation_verified":False,"calibration_mm_per_pixel":None,
            "is_ricketts_goldset_reference":False,
        })
    draft={"schema_version":SCHEMA,"scope":"PUBLIC_WIKIMEDIA_IMAGES_ONLY",
           "operator_token":"synthetic_operator","source_profile_id":PROFILE,
           "clinical_release":False,"independent_expert_authentication":False,
           "expert_goldset_ready":False,"atlas33_measurements_validated":0,
           "reference_group":"NO_REFERENCE",
           "note":"Manual unverified pixels only; no clinical use or expert verification",
           "cases":records}
    return draft,catalog

def add(draft,catalog,x=30.5,y=90):
    item=draft["cases"][0]
    id0=catalog["required_source_ids"][0]
    item["landmarks"][id0]={"x":x,"y":y}
    item["missing_source_specific_ids"].remove(id0)

class DraftContract(unittest.TestCase):
    def fails(self,obj,catalog):
        with self.assertRaises(ValueError):
            verify_draft(obj,catalog)

    def test_zero_point_draft_remains_nonclinical(self):
        d,c=sample()
        r=verify_draft(d,c)
        self.assertEqual(r["manual_draft_pixel_points"],0)
        self.assertFalse(r["clinical_release"])

    def test_pixel_point_does_not_become_reference(self):
        d,c=sample();add(d,c)
        r=verify_draft(d,c)
        self.assertEqual(r["manual_draft_pixel_points"],1)
        self.assertFalse(r["anatomical_expertise_verified"])

    def test_reject_clinical_or_forged_expert(self):
        for key in ("clinical_release","independent_expert_authentication","expert_goldset_ready"):
            d,c=sample();d[key]=True;self.fails(d,c)

    def test_reject_mm_calibration_or_orientation_promotions(self):
        d,c=sample();d["cases"][0]["calibration_mm_per_pixel"]=0.1;self.fails(d,c)
        d,c=sample();d["cases"][1]["image_orientation_verified"]=True;self.fails(d,c)

    def test_reject_other_dataset_ids_and_aliases(self):
        d,c=sample();d["cases"][0]["source_case"]="some_patient_case";self.fails(d,c)
        d,c=sample();d["cases"][0]["landmarks"]["Po"]={"x":22,"y":22};self.fails(d,c)

    def test_reject_wrong_hash_and_coordinates_out_of_bounds(self):
        d,c=sample();d["cases"][0]["source_image_sha256"]="f"*64;self.fails(d,c)
        for coords in [(-1,2),(2273,0),(1,float("nan")),(True,2)]:
            d,c=sample();add(d,c,*coords);self.fails(d,c)

    def test_reject_fake_complete_point_inventory(self):
        d,c=sample();add(d,c)
        d["cases"][0]["missing_source_specific_ids"]=[]
        self.fails(d,c)

    def test_reject_extra_coordinate_metadata(self):
        d,c=sample();add(d,c)
        d["cases"][0]["landmarks"][c["required_source_ids"][0]]["z"]=5
        self.fails(d,c)

    def test_reject_opaque_operator_with_personal_information(self):
        d,c=sample();d["operator_token"]="Dr Jane Doe";self.fails(d,c)

    def test_require_all_twenty_one_exact_g9_ids(self):
        d,c=sample()
        self.assertEqual(len(c["required_source_ids"]),21)
        self.assertEqual(c["required_source_ids"],sorted(set(c["required_source_ids"])))
        self.assertIn("Po_anatomic",c["required_source_ids"])
        self.assertIn("Pt_Ricketts",c["required_source_ids"])

if __name__=="__main__":
    unittest.main()
