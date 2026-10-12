"""03B.3c EXPERIMENTAL: Run the pinned actual SRPose38 ONNX on two public films.

This is a processing/integration smoke, NOT landmark accuracy certification.
No invented ruler calibration, no diagnosis, no reference-point comparison.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

from PIL import Image

MANIFEST=Path(__file__).resolve().parents[2] / "frontend/scripts/fixtures/dc-ceph03b3c-public-cephalograms.json"
EXPECTED_MODEL_SHA256="a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
EXPECTED_MODEL_SIZE=267484931


def main():
    assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
    assert os.environ.get("ENVIRONMENT") == "test"
    model=Path(__file__).resolve().parents[1] / "ai_models/srpose38-tta-1024.onnx"
    assert model.is_file() and model.stat().st_size == EXPECTED_MODEL_SIZE
    assert hashlib.sha256(model.read_bytes()).hexdigest() == EXPECTED_MODEL_SHA256
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    directory=Path(os.environ["DC_CEPH03B3C_RADIO_DIR"])

    # Import AFTER model provisioning, as the engine fail-closes if it is absent.
    from backend.services.sota_vision_service import sota_vision_engine
    assert sota_vision_engine.is_ready, "The exact certified SRPose38 model must be loaded"
    results=[]
    for info in manifest["images"]:
        filename=directory / info["file_name"]
        raw=filename.read_bytes()
        assert hashlib.sha1(raw).hexdigest()==info["sha1"]
        with Image.open(filename) as source:
            assert source.size==(info["width"],info["height"])
        result=sota_vision_engine.predict_landmarks(str(filename))
        assert result and result.get("mode_inference")=="SOTA_ONNX_38", (info["id"],result)
        pts=result.get("landmarks")
        assert isinstance(pts,list) and len(pts)==38,(info["id"],len(pts) if pts else 0)
        ids=[p["id"] for p in pts]
        assert len(set(ids))==38
        assert all(math.isfinite(float(p["x"])) and math.isfinite(float(p["y"])) for p in pts)
        # This is not an accuracy judgement; it only ensures output is finite.
        results.append({
            "radio":info["id"],
            "image_sha1":info["sha1"],
            "landmark_count":len(pts),
            "runtime_provider":result.get("runtime_provider"),
            "inference_mode":result.get("mode_inference"),
            "source":info["source_page"],
            "clinical_accuracy_evaluated":False,
        })
    print(json.dumps({"gate":"EXPERIMENTAL", "model_sha256":EXPECTED_MODEL_SHA256,
                      "results":results,"clinical_accuracy_evaluated":False},indent=2))
    print("DC_CEPH03B3C_TWO_REAL_XRAYS_SRPOSE38_38_POINTS_EACH_PASS")


if __name__=="__main__":
    main()
