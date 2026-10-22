"""J10M rights evidence regression, public metadata mocked (never download images)."""
from __future__ import annotations

import base64
import copy
import importlib.util
import json
from pathlib import Path
import unittest

P = Path(__file__).with_name("lot05_j10m_public_license_probe.py")
spec = importlib.util.spec_from_file_location("j10m_public_license_probe", P)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/lot05-j10m-fdi-public-license-metadata.yml"


def official_readme():
    return """# DENTEX

## License
The data is provided under the [CC BY-NC-SA 4.0 License](https://creativecommons.org/licenses/by-nc-sa/4.0/), allowing non-commercial use.
The rest of this repository is under the [MIT License](https://choosealicense.com/licenses/mit/).
"""


def github_json():
    return {
        "path": "README.md",
        "encoding": "base64",
        "sha": m.EXPECTED_GITHUB_README_BLOB_SHA,
        "content": base64.b64encode(official_readme().encode()).decode(),
    }


def hf_json():
    return {
        "id": "ibrahimhamamci/DENTEX",
        "sha": "ab" * 20,
        "cardData": {"license": m.EXPECTED_NONCOMMERCIAL_LICENSE},
        "tags": ["medical", "license:" + m.EXPECTED_NONCOMMERCIAL_LICENSE],
    }


def matrix():
    return json.loads(m.MATRIX.read_text(encoding="utf-8"))


class LicenceMetadataTests(unittest.TestCase):
    def test_exact_official_data_license_separate_from_code_license(self):
        r = m.verify_github_owner_license(github_json())
        self.assertEqual(r["publisher_declared_data_license"], "cc-by-nc-sa-4.0")
        self.assertEqual(r["publisher_declared_non_data_code_license"], "MIT")

    def test_live_metadata_does_not_conflate_mit_software_with_data(self):
        obj = github_json()
        body = official_readme().replace(
            "CC BY-NC-SA 4.0 License", "CC BY-SA 4.0 License"
        )
        obj["content"] = base64.b64encode(body.encode()).decode()
        with self.assertRaises(m.LicenseEvidenceError):
            m.verify_github_owner_license(obj)

    def test_changed_upstream_readme_fails_closed(self):
        obj = github_json()
        obj["sha"] = "deadbeef" * 5
        with self.assertRaises(m.LicenseEvidenceError):
            m.verify_github_owner_license(obj)

    def test_huggingface_dataset_card_both_fields_must_be_nc(self):
        self.assertEqual(
            m.verify_hf_dataset_license(hf_json())["huggingface_declared_data_license"],
            "cc-by-nc-sa-4.0",
        )
        for prop in ("license", "tag", "id"):
            obj = hf_json()
            if prop == "license":
                obj["cardData"]["license"] = "cc-by-4.0"
            elif prop == "tag":
                obj["tags"] = ["medical", "license:cc-by-4.0"]
            else:
                obj["id"] = "untrusted/Fake"
            with self.subTest(prop=prop), self.assertRaises(m.LicenseEvidenceError):
                m.verify_hf_dataset_license(obj)

    def test_all_seven_candidate_commercial_decisions_blocked(self):
        r = m.review_matrix(matrix())
        self.assertEqual(r["candidate_count"], 7)
        self.assertEqual(r["commercial_approvals"], 0)

    def test_no_permission_via_manifest_override(self):
        for field in ("commercial_training_approval", "real_patient_radiographs_cloud_approved"):
            obj = matrix()
            obj[field] = True
            with self.subTest(field=field), self.assertRaises(m.LicenseEvidenceError):
                m.review_matrix(obj)
        obj = matrix()
        obj["candidates"][0]["commercial_use_approved"] = True
        with self.assertRaises(m.LicenseEvidenceError):
            m.review_matrix(obj)

    def test_no_candidate_can_be_declared_clear_by_mutating_decision(self):
        obj = matrix()
        obj["candidates"][0]["commercial_decision"] = "COMMERCIAL_APPROVED"
        with self.assertRaises(m.LicenseEvidenceError):
            m.review_matrix(obj)

    def test_unknown_source_and_short_evidence_are_rejected(self):
        obj = matrix()
        obj["candidates"][0]["source"] = "file:///secret/patient.dcm"
        with self.assertRaises(m.LicenseEvidenceError):
            m.review_matrix(obj)
        obj = matrix()
        obj["candidates"][1]["evidence"] = "Public domain"
        with self.assertRaises(m.LicenseEvidenceError):
            m.review_matrix(obj)

    def test_arbitrary_data_urls_can_never_be_fetched(self):
        for url in ("https://kaggle.com/datasets/raw/images.zip", "file:///patient.dcm",
                    "https://universe.roboflow.com/a/b"):
            with self.subTest(url=url), self.assertRaises(m.LicenseEvidenceError):
                m.load_public_json(url)

    def test_fixture_live_probe_records_no_clinical_permission(self):
        def mocked_fetch(url):
            return github_json() if url == m.GITHUB_API else hf_json()
        old = m.load_public_json
        try:
            m.load_public_json = mocked_fetch
            out = m.probe()
        finally:
            m.load_public_json = old
        self.assertEqual(out["status"], "PUBLIC_METADATA_CONFIRMS_FDI_COMMERCIAL_HOLD")
        self.assertFalse(out["real_data_training_authorized"])
        self.assertEqual(out["data_images_downloaded"], 0)

    def test_ci_artifacts_json_only_and_no_dataset_or_weights(self):
        wf = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("ubuntu-24.04", wf)
        self.assertIn("windows-2025", wf)
        self.assertIn("actions/upload-artifact@", wf)
        self.assertIn("reports/j10m-", wf)
        self.assertIn("PUBLIC_METADATA_CONFIRMS_FDI_COMMERCIAL_HOLD", wf)
        for bad in ("gh release create", "vercel deploy", "kaggle datasets download",
                    "roboflow download", "model.safetensors", "patient.dcm"):
            self.assertNotIn(bad, wf.lower())
        src = P.read_text(encoding="utf-8")
        self.assertNotIn("Image.open(", src)
        self.assertNotIn("snapshot_download(", src)


if __name__ == "__main__":
    unittest.main()
