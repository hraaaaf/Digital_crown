import json
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]
ROOT = FRONTEND.parent
SOURCE = ROOT / "docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json"
OUTPUT = FRONTEND / "src/features/ortho/cephaloLot06FocusRegistry.generated.ts"

source = json.loads(SOURCE.read_text(encoding="utf-8"))
registry = {}
for item in source["measurements"]:
    registry[item["measurement_id"]] = {
        "measurementId": item["measurement_id"],
        "unit": item["unit"],
        "requiredLandmarks": item["required_landmarks"],
        "requiredConstructions": item["required_constructions"],
        "sourceContracts": item["source_contracts"],
        "availabilityGate": item["availability_gate"],
        "requiresCalibration": bool(item["requires_calibration"]),
    }

body = """// AUTO-GENERATED from docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json
// Do not edit by hand. Regenerate with: python scripts/generate_cephalo_lot06_focus_registry.py

export interface CephaloCanonicalFocusDependency {
  measurementId: string;
  unit: string;
  requiredLandmarks: readonly string[];
  requiredConstructions: readonly string[];
  sourceContracts: readonly string[];
  availabilityGate: string;
  requiresCalibration: boolean;
}

export const CEPHALO_LOT06_FOCUS_REGISTRY = __REGISTRY__ as const satisfies Record<string, CephaloCanonicalFocusDependency>;

export const CEPHALO_LOT06_FOCUS_REGISTRY_SOURCE =
  'docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json' as const;
"""
body = body.replace("__REGISTRY__", json.dumps(registry, ensure_ascii=False, indent=2))
OUTPUT.write_text(body, encoding="utf-8")
print(f"generated {len(registry)} canonical focus dependencies -> {OUTPUT.relative_to(ROOT)}")
