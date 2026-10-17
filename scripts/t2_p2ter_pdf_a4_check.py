"""Inspect real authenticated T2 browser PDF binaries and screenshots.

All source content is synthetic. This verifies A4 geometry, identity, expected
incomplete-label and no study A/B reference contamination. It does NOT issue a
clinical or human visual approval.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path("artifacts/p2ter-desktop")
manifest = json.loads((ROOT / "manifest.json").read_text())
assert len(manifest) == 4, "Missing authenticated viewport / analysis scenarios"
assert {(x["viewport"]["width"], x["viewport"]["height"], x["study"])
        for x in manifest} == {(w, h, case) for w,h in ((1280,900), (1600,1000)) for case in "AB"}

refs = {
    "A": "api/static/uploads/radios/t2-cephalo-seeded.png",
    "B": "api/static/uploads/radios/p2ter-synthetic-study-B.png",
}
fprints = {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k,v in refs.items()}
normal = lambda text: re.sub(r"[^0-9a-zA-Z]", "", text).lower()
results = []
for evidence in manifest:
    viewport = evidence["viewport"]
    captures = []
    for name in evidence["snapshots"]:
        image_path = ROOT / name
        assert image_path.is_file(), f"Missing screenshot {image_path}"
        with Image.open(image_path) as shot:
            assert shot.width == viewport["width"], f"Wrong browser viewport screenshot {name}"
            assert shot.height >= viewport["height"], f"Truncated browser screenshot {name}"
        captures.append(hashlib.sha256(image_path.read_bytes()).hexdigest())
    assert len(set(captures)) == 3, f"BEFORE/TARGET/AFTER snapshots identical: {evidence}"

    for kind in ("preview_pdf", "archived_pdf"):
        file = ROOT / evidence[kind]
        assert file.read_bytes().startswith(b"%PDF"), f"Not real binary PDF: {file}"
        with fitz.open(file) as pdf:
            assert len(pdf) >= 1
            whole = "\n".join(p.get_text() for p in pdf)
            patient = evidence["patient_id"]
            study_id = evidence["analysis_id"]
            assert re.search(rf"Patient ID\s*:\s*{patient}(?!\d)", whole)
            assert re.search(rf"Analysis ID\s*:\s*{study_id}(?!\d)", whole)
            assert normal(evidence["source_revision"]) in normal(whole)
            assert fprints[evidence["study"]] in normal(whole), f"Study reference fingerprint missing {file}"
            other = "B" if evidence["study"]=="A" else "A"
            assert fprints[other] not in normal(whole), f"Study contamination in {file}"
            assert "DOCUMENT CLINIQUE INCOMPLET" in whole, f"Unjustified complete-clinical label {file}"
            pages = len(pdf)
            for index, page in enumerate(pdf):
                width,height=page.rect.width,page.rect.height
                assert abs(width-595.28)<2 and abs(height-841.89)<2, (
                    f"Not A4: {file} page {index+1} {width}x{height}")
                for block in page.get_text("blocks"):
                    x0,y0,x1,y1=block[:4]
                    assert x0 >= -1 and y0 >= -1 and x1 <= width+1 and y1 <= height+1, (
                        f"Text overflows A4 page {index+1}: {file}, {block[:4]}")
            results.append({
                "study": evidence["study"],
                "viewport": viewport,
                "kind": kind,
                "pdf": evidence[kind],
                "pages": pages,
                "a4": True,
                "canonical_identity_verified": True,
                "no_cross_study_fingerprint": True,
                "incomplete_clinical_label": True,
            })
report = {"status":"PASS_PDF_CONTENT_A4_SCREENSHOT_GEOMETRY_NOT_VISUAL_APPROVAL","items":results}
(ROOT / "pdf-a4-inspection.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("P2TER_A4_AUDIT "+json.dumps(report))
