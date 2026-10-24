"""Guard rails for G5 MedSAM research-only source and mask prompts."""
from __future__ import annotations
import json
import os
from pathlib import Path
import pytest
from scripts import odf_v5_g5_medsam_poc as poc

BOXES = Path(__file__).resolve().parents[1] / "scripts/g5_medsam_boxes_research_only.json"

def boxes():
    return json.loads(BOXES.read_text(encoding="utf-8"))

def test_six_roi_prompts_no_clinical_authority():
    payload=boxes()
    poc.validate_boxes(payload)
    assert set(payload["boxes"])==set(poc.IDS)
    assert payload["approved"] is False and payload["clinical_validation"] is False
    assert payload["source"]=="UNVERIFIED_ASSISTED_DRAFT_BOX_SUGGESTIONS"

def test_guard_refuses_false_approval_and_missing_anatomy():
    original=boxes()
    for field in ("clinical_validation","approved"):
        with pytest.raises(ValueError,match="G5_ROI_CONTRACT_REFUSED"):
            poc.validate_boxes({**original,field:True})
    incomplete={**original,"boxes":original["boxes"].copy()}
    incomplete["boxes"].pop("maxilla")
    with pytest.raises(ValueError,match="G5_ROI_CONTRACT_REFUSED"):
        poc.validate_boxes(incomplete)

def test_guard_refuses_outside_image_and_fake_weights(tmp_path):
    payload=boxes()
    invalid={**payload,"boxes":{**payload["boxes"],"mandible":[0,0,1935,2400]}}
    with pytest.raises(ValueError,match="G5_BAD_PROMPT_BOX_mandible"):
        poc.validate_boxes(invalid)
    fake=tmp_path/"fake.pth"
    fake.write_bytes(b"not-the-official-model")
    from PIL import Image
    with pytest.raises(ValueError,match="CHECKPOINT_NOT_OFFICIAL_ZENODO_MD5"):
        poc.research_inference(Image.new("RGB",poc.EXPECTED_SIZE),payload["boxes"],fake,tmp_path)

def test_sha_locked_public_image_in_CI(tmp_path):
    filename=os.getenv("G5_POC_SOURCE_IMAGE")
    if not filename:
        pytest.skip("Aariz public research image exists only in CI artifact")
    path=Path(filename)
    assert poc.load_public_film(source_image=path).size==poc.EXPECTED_SIZE
    tampered=tmp_path/"corrupt.png"
    tampered.write_bytes(path.read_bytes()+b"corruption")
    with pytest.raises(ValueError,match="G5_PUBLIC_SOURCE_SHA256_MISMATCH"):
        poc.load_public_film(source_image=tampered)
