"""Pure tests for view-only Focus provenance, no application/DB bootstrap."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as Obj

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "cephalo_r23g3_runtime_focus", ROOT / "backend/services/cephalo_runtime_focus.py"
)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
derive = MOD.derive_active_runtime_focus


def landmark(landmark_id):
    return Obj(landmark_id=landmark_id, evidence_id="active:" + landmark_id,
               availability_status="AVAILABLE")


def measurement(*, refs=None, state="AVAILABLE", value=3.5, method="AUTH:MCNAMARA"):
    return Obj(measurement_id="m:1", method_id=method, value=value, unit="mm",
               availability_status=state,
               landmark_refs=refs if refs is not None else ["active:Co_anatomic", "active:A"],
               construction_refs=[], requires_calibration=True, calibration_ref="cal:verified")


def canonical(**changes):
    source = {"canonical_measurement_id": "M_CO_A_MM_V1", "value": 3.5,
              "unit": "mm", "availability_status": "AVAILABLE",
              "measurement_refs": ["m:1"],
              "value_authority_method_id": "AUTH:MCNAMARA"}
    return {**source, **changes}


def project(m=None, landmarks=None, row=None, constructions=None):
    return derive(
        [row or canonical()],
        measurements={"m:1": m or measurement()},
        landmarks=landmarks or {k: landmark(k) for k in ["Co_anatomic", "A"]},
        constructions=constructions or {},
    )


def test_only_exact_active_measured_landmark_ids_are_focused():
    item = project()["M_CO_A_MM_V1"]
    assert item["landmark_ids"] == ["Co_anatomic", "A"]
    assert "Co" not in item["landmark_ids"]
    assert item["construction_ids"] == []
    assert item["authority"] == "ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1"


def test_refuses_unverified_source_and_formula_aliases():
    assert project(row=canonical(availability_status="NOT_COMPUTABLE", value=None)) == {}
    assert project(row=canonical(value=999)) == {}
    assert project(m=measurement(method="WRONG:MCNAMARA")) == {}
    assert project(m=measurement(refs=["active:Co", "active:A"])) == {}
    assert project(m=measurement(state="NOT_COMPUTABLE", value=None)) == {}
    assert project(m=measurement(refs=["active:Co_anatomic", "active:A"]),
                   landmarks={"A": landmark("A")}) == {}
    broken_calibration = measurement()
    broken_calibration.calibration_ref = None
    assert project(m=broken_calibration) == {}


def test_exact_active_construction_ref_is_needed_without_guessing_geometry():
    pair = {k: landmark(k) for k in ["Po_anatomic", "Or"]}
    f = measurement(refs=["active:Po_anatomic", "active:Or"])
    f.construction_refs = ["FH_PO_OR_V1"]
    c = Obj(construction_id="FH_PO_OR_V1", availability_status="AVAILABLE")
    assert project(m=f, landmarks=pair) == {}
    valid = project(m=f, landmarks=pair, constructions={"FH_PO_OR_V1": c})
    assert valid["M_CO_A_MM_V1"]["landmark_ids"] == ["Po_anatomic", "Or"]
    assert valid["M_CO_A_MM_V1"]["construction_ids"] == ["FH_PO_OR_V1"]
