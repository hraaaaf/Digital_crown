"""Generate deterministic LOT07-G synthetic export evidence.

Uses the canonical LOT06 engine/evidence builders. No production patient data.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace

from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.ortho_workbench_export import OrthoWorkbenchExportRequest, build_ortho_workbench_export
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "audits" / "fixtures" / "ortho_workbench_export_v1.synthetic.json"
RECORDED_AT = datetime(2026, 10, 3, 10, 0, tzinfo=timezone.utc)
EXPORTED_AT = datetime(2026, 10, 3, 10, 30, tzinfo=timezone.utc)
PATIENT_ID = 907001
ANALYSIS_ID = 907071
CASE_ID = "cephalo:lot07g-export-fixture"


class _EmptyAssetQuery:
    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return []


class _EmptyMediaDb:
    def query(self, *_args, **_kwargs):
        return _EmptyAssetQuery()


def main() -> None:
    landmarks = [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]
    points = {item["id"]: (item["x"], item["y"]) for item in landmarks}
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(points)
    angles = result.model_dump()
    angles[EVIDENCE_GRAPH_KEY] = build_cephalo_runtime_evidence_payload(
        patient_id=PATIENT_ID,
        image_record_id="synthetic://lot07g/lateral-cephalogram",
        result=result,
        landmarks=landmarks,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=RECORDED_AT,
    )
    analysis = SimpleNamespace(
        id=ANALYSIS_ID,
        patient_id=PATIENT_ID,
        image_original_path="synthetic://lot07g/lateral-cephalogram",
        angles_data=angles,
    )
    request = OrthoWorkbenchExportRequest.model_validate(
        {
            "timepoint": "T0",
            "layer_visibility": {
                "landmarks": True,
                "plans": True,
                "hard_tissue": False,
                "teeth": True,
                "soft_tissue": True,
                "measurements": True,
                "t1": False,
                "t2": False,
            },
            "layer_opacity": {
                "landmarks": 1.0,
                "plans": 1.0,
                "hard_tissue": 0.85,
                "teeth": 1.0,
                "soft_tissue": 0.9,
                "measurements": 1.0,
                "t1": 0.5,
                "t2": 0.5,
            },
            "traced_structures": [],
            "session_edit_audit": [],
        }
    )
    exported = build_ortho_workbench_export(
        _EmptyMediaDb(),
        analysis=analysis,
        employer_id=1,
        request=request,
        exported_at=EXPORTED_AT,
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(exported, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(f"landmarks={len(exported['landmarks']['items'])}")
    print(f"constructions={len(exported['lot06_scientific_refs']['construction_refs'])}")
    print(f"measurements={len(exported['lot06_scientific_refs']['measurement_refs'])}")
    print(f"canonical_measurements={len(exported['lot06_scientific_refs']['canonical_measurements'])}")


if __name__ == "__main__":
    main()
