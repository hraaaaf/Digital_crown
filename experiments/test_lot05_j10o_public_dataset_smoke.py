"""LOT05/J10O — source-grounded, offline validation tests for two public corpora.

Only fake HTML and a synthetically generated JPEG are used in unit tests.
Live CI jobs contact the public pages separately; no patient materials committed.
"""
from __future__ import annotations

from io import BytesIO
import importlib.util
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,HERE/path)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

r=module("j10o_roboflow","lot05_j10o_roboflow_fdi_public_metadata.py")
m=module("j10o_tunisia","lot05_j10o_tunisia_public_opg_sample.py")
WORKFLOW=HERE.parent / ".github/workflows/lot05-j10o-public-panoramic-research-qa.yml"

def project_text():
    classes=" ".join(map(str,r.FDI))
    return (
        "Panoramic-Dental-Xray-FDI Dataset "
        "License:CC BY 4.0 Overview Images 1,577 "
        "Classes (32) "+classes+" Tags Object Detection "
        "About Panoramic-Dental-Xray-FDI Dataset "
        "A description for this project has not been published yet"
    )

def version_text():
    return ("Stretch & Rotate v1 3503 "
            "3503 Total Images Train Set 87% 3032 Images "
            "Valid Set 9% 315 Images Test Set 4% 156 Images "
            "Preprocessing Resize: Stretch to 1280x1280 "
            "Augmentations Outputs per training example: 3 "
            "90° Rotate: Clockwise, Counter-Clockwise, Upside Down")

class TestPublishedFDIMetadata(unittest.TestCase):
    def test_expected_public_data_contract(self):
        out=r.parse_pages(project_text(),version_text())
        self.assertEqual(out["fdi_class_count"],32)
        self.assertEqual(out["class_labels"],[q*10+i for q in (1,2,3,4) for i in range(1,9)])
        self.assertEqual(out["source_image_count_reported"],1577)
        self.assertEqual(out["public_version_augmented_count"],3503)
        self.assertEqual(out["train_augmented_examples"]+out["validation_augmented_examples"]+out["test_augmented_examples"],3503)
        self.assertFalse(out["patient_group_leakage_audited"])
        self.assertFalse(out["cloud_commercial_training_authorized"])

    def test_fdi_class_label_corruption_blocked(self):
        for old,new in ((" 18 "," 19 "),(" 36 "," 35 "),(" 48 "," 88 ")):
            with self.subTest(old=old),self.assertRaises(r.DatasetMetadataError):
                r.parse_pages(project_text().replace(old,new),version_text())

    def test_project_without_license_declared_is_not_auto_go(self):
        with self.assertRaises(r.DatasetMetadataError):
            r.parse_pages(project_text().replace("CC BY 4.0","CC BY-NC 4.0"),version_text())

    def test_augmentation_changes_require_reviewer(self):
        for corrupt in ("90° Rotate", "3503", "3032", "315", "156"):
            with self.subTest(corrupt=corrupt),self.assertRaises(r.DatasetMetadataError):
                r.parse_pages(project_text(),version_text().replace(corrupt,"deleted"))

    def test_missing_clinic_provenance_gets_manual_review(self):
        with self.assertRaises(r.DatasetMetadataError):
            r.parse_pages(project_text().replace("A description for this project has not been published yet","Hospital source available"),version_text())

    def test_roboflow_domain_is_not_arbitrary(self):
        with self.assertRaises(r.DatasetMetadataError):
            r.public_text("https://other.roboflow.com/patient.png")


class TestAcademicPublicJPEG(unittest.TestCase):
    def test_mendeley_explicit_ccby_and_version(self):
        result=m._dataset_check({"version":3,"name":"Panoramic Dental Xray Dataset",
                                 "data_licence":{"short_name":"CC BY 4.0"}})
        self.assertEqual(result["dataset_version"],3)

    def test_wrong_license_or_version_fails(self):
        for field,value in (("version",2),("data_licence",{"short_name":"CC BY-NC 4.0"}),
                            ("name","Financial data dataset")):
            d={"version":3,"name":"Panoramic Dental Xray Dataset",
               "data_licence":{"short_name":"CC BY 4.0"}}
            d[field]=value
            with self.subTest(field=field),self.assertRaises(m.PublicSampleError):
                m._dataset_check(d)

    def test_sample_file_bounded_public_origin(self):
        public="https://api.data.mendeley.com/datasets/73n3kz2k4k/files"
        allowed=[{"filename":"100.jpg","size":250000,
                  "content_details":{"download_url":public}},
                 {"filename":"42.jpg","size":5_000_000,
                  "content_details":{"download_url":"https://example.com/xyz"}}]
        sample=m._candidate(allowed)
        self.assertEqual(sample["filename"],"100.jpg")
        self.assertTrue(m._public_domain(sample["source_url"]))

    def test_private_or_untrusted_image_urls_never_fetched(self):
        for url in ("file:///patient.dcm",
                    "http://api.data.mendeley.com/file",
                    "https://169.254.169.254/latest/meta-data",
                    "https://mendeley.com.evil.org/foo.jpg",
                    "https://evil.s3.amazonaws.com/whatever",
                    "https://user:password@api.data.mendeley.com/foo"):
            with self.subTest(url=url),self.assertFalse(m._public_domain(url))

    def test_no_image_file_in_list_is_not_success(self):
        with self.assertRaises(m.PublicSampleError):
            m._candidate([{"filename":"case001.dcm","size":8000,
                           "content_details":{"download_url":"https://api.data.mendeley.com/"}}])

    def test_small_valid_synthetic_jpeg_decodes(self):
        from PIL import Image, ImageDraw
        pic=Image.new("L",(900,400),color=80)
        d=ImageDraw.Draw(pic)
        d.rectangle((20,20,480,290),fill=210)
        buf=BytesIO()
        pic.save(buf,format="JPEG")
        report=m._decode_image(buf.getvalue())
        self.assertEqual(report["channels_after_preprocessing"],3)
        self.assertEqual(report["rgb_resized_width"],640)
        self.assertTrue(report["decode_and_grayscale_preprocessing_pass"])

    def test_fake_nonjpeg_is_rejected(self):
        with self.assertRaises(m.PublicSampleError):
            m._decode_image(b"not-a-dental-jpeg")

    def test_public_records_cannot_promote_dental_fdi_accuracy(self):
        for s in ("dental_fdi_accuracy_validated\":True",
                  "clinical_release_approved\":True",
                  "model.save_pretrained(", "torch.save("):
            self.assertNotIn(s,(HERE/"lot05_j10o_tunisia_public_opg_sample.py").read_text())

    def test_workflow_pins_no_upload_of_clinical_images(self):
        content=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("rights-before-tests",content)
        self.assertIn("ubuntu-24.04",content)
        self.assertIn("windows-2025",content)
        self.assertIn("reports/j10o-",content)
        self.assertIn("actions/upload-artifact@",content)
        for banned in ("roboflow download", "gh release create", "vercel deploy",
                       "datasets download", "patient_image.jpg", "model.onnx"):
            self.assertNotIn(banned,content.lower())


if __name__=="__main__":
    unittest.main()
