from __future__ import annotations

import argparse
import io
import json
import platform
import re
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "backend" / "requirements.txt"
ASSET_MANIFEST = ROOT / "backend" / "scientific_assets.json"
SOTA_SERVICE = ROOT / "backend" / "services" / "sota_vision_service.py"
VISION_SERVICE = ROOT / "backend" / "services" / "vision_service.py"
PANORAMIC_SERVICE = ROOT / "backend" / "services" / "panoramic_service.py"

OPENCV_DISTRIBUTIONS = {
    "opencv-python",
    "opencv-contrib-python",
    "opencv-python-headless",
    "opencv-contrib-python-headless",
}
EXPECTED_OPENCV = "opencv-python-headless==4.13.0.92"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _package_name(line: str) -> str:
    return re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip().lower()


def check_dependency_contract() -> None:
    lines = [
        raw.strip()
        for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if raw.strip() and not raw.lstrip().startswith("#")
    ]
    opencv_lines = [line for line in lines if _package_name(line) in OPENCV_DISTRIBUTIONS]
    _require(
        opencv_lines == [EXPECTED_OPENCV],
        f"OpenCV distribution contract violated: expected only {EXPECTED_OPENCV!r}, got {opencv_lines!r}",
    )
    print(f"DEPENDENCY_GATE=OK ({EXPECTED_OPENCV})")


def check_model_path_contract() -> None:
    source = SOTA_SERVICE.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden = ("c:\\\\users\\\\", "/users/", "\\\\users\\\\", "lenovo")
    _require(not any(marker in lowered for marker in forbidden), "Machine-bound model path detected")
    _require("AppPaths.get_model_path" in source, "Scientific model path must use AppPaths.get_model_path")
    print("MODEL_PATH_GATE=OK")


def check_scientific_scope_contract() -> None:
    data = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    _require(data.get("schema_version") == 2, "Unsupported scientific asset manifest schema")
    _require(
        data.get("p5_certification_scope") == "native-runtime-and-fail-closed",
        "P5 certification scope must stay runtime/fail-closed only",
    )
    _require(
        data.get("asset_policy") == "external-not-versioned",
        "Scientific model assets must remain external to the public source repository",
    )
    assets = data.get("assets")
    _require(isinstance(assets, list) and assets, "Scientific asset inventory must contain assets")
    seen: set[str] = set()
    for asset in assets:
        _require(isinstance(asset, dict), "Asset entry must be an object")
        asset_id = asset.get("id")
        _require(isinstance(asset_id, str) and asset_id, "Asset id is required")
        _require(asset_id not in seen, f"Duplicate asset id: {asset_id}")
        seen.add(asset_id)
        _require(asset.get("kind") == "model", f"P5 inventory contains non-model asset: {asset_id}")
        _require(asset.get("p5_required") is False, f"P5 must not require external model bytes: {asset_id}")
        _require(asset.get("lifecycle") in {"external", "deferred"}, f"Invalid lifecycle for {asset_id}")
        _require(isinstance(asset.get("next_gate"), str) and asset["next_gate"].strip(), f"next_gate required for {asset_id}")
    _require("cephalo_sota" in seen and "cephalo_legacy" in seen and "panoramic" in seen, "Scientific inventory incomplete")
    print("SCIENTIFIC_SCOPE_GATE=OK (external assets not versioned; no numerical parity claim)")


def check_fail_closed_source_contract() -> None:
    sota = SOTA_SERVICE.read_text(encoding="utf-8")
    vision = VISION_SERVICE.read_text(encoding="utf-8")
    pano = PANORAMIC_SERVICE.read_text(encoding="utf-8")
    _require("model.onnx introuvable. Mode SOTA désactivé" in sota, "SOTA missing-model fail-closed message missing")
    _require('mode_inference = "FAILED"' in vision and "Placement manuel requis" in vision, "Cephalo manual fallback contract missing")
    _require("if _is_clinical_environment():" in pano and "raise RuntimeError" in pano, "Panoramic clinical fail-closed contract missing")
    print("FAIL_CLOSED_SOURCE_GATE=OK")


def _smoke_opencv() -> None:
    import cv2
    import numpy as np

    image = np.arange(64 * 64, dtype=np.uint8).reshape(64, 64)
    resized = cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA)
    ok, encoded = cv2.imencode(".png", resized)
    _require(bool(ok), "OpenCV PNG encode failed")
    decoded = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
    _require(decoded is not None and decoded.shape == (32, 32), "OpenCV decode/resize smoke failed")


def _smoke_onnxruntime(tmp: Path) -> None:
    import numpy as np
    import onnx
    import onnxruntime as ort
    from onnx import TensorProto, helper

    model_path = tmp / "identity.onnx"
    node = helper.make_node("Identity", inputs=["x"], outputs=["y"])
    graph = helper.make_graph(
        [node],
        "digitalcrown_p5_identity",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 3])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 3])],
    )
    model = helper.make_model(graph, producer_name="digitalcrown-p5", opset_imports=[helper.make_opsetid("", 13)])
    model.ir_version = 8
    onnx.checker.check_model(model)
    onnx.save(model, model_path)
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    sample = np.array([[1.25, -2.0, 9.5]], dtype=np.float32)
    output = session.run(None, {"x": sample})[0]
    _require(np.array_equal(output, sample), "ONNX Runtime identity inference mismatch")


def _smoke_torch() -> None:
    import torch
    import torchaudio  # noqa: F401
    import torchvision  # noqa: F401

    left = torch.tensor([[1.0, 2.0], [3.0, 4.0]], device="cpu")
    right = torch.eye(2, device="cpu")
    result = torch.mm(left, right)
    _require(torch.equal(result, left), "PyTorch CPU execution mismatch")


def _smoke_sqlcipher(tmp: Path) -> None:
    from sqlcipher3 import dbapi2 as sqlcipher

    db_path = tmp / "p5_sqlcipher.db"
    key = "DigitalCrown-P5-native-cert-key"
    marker = "P5_SQLCIPHER_MARKER_9f3c2a"

    conn = sqlcipher.connect(str(db_path))
    conn.execute(f"PRAGMA key = '{key}'")
    cipher_version = conn.execute("PRAGMA cipher_version").fetchone()
    _require(cipher_version and cipher_version[0], "sqlcipher3 is not backed by SQLCipher")
    conn.execute("CREATE TABLE proof(value TEXT NOT NULL)")
    conn.execute("INSERT INTO proof(value) VALUES (?)", (marker,))
    conn.commit()
    conn.close()

    _require(marker.encode("utf-8") not in db_path.read_bytes(), "SQLCipher database leaked plaintext marker")

    reopened = sqlcipher.connect(str(db_path))
    reopened.execute(f"PRAGMA key = '{key}'")
    value = reopened.execute("SELECT value FROM proof").fetchone()
    reopened.close()
    _require(value == (marker,), "SQLCipher reopen/read failed")


def _smoke_reportlab() -> None:
    from reportlab.pdfgen import canvas

    output = io.BytesIO()
    pdf = canvas.Canvas(output)
    pdf.drawString(72, 720, "Digital Crown P5 native parity")
    pdf.save()
    _require(output.getvalue().startswith(b"%PDF"), "ReportLab PDF generation failed")


def _smoke_weasyprint() -> None:
    from weasyprint import HTML

    pdf = HTML(string="<html><body><p>Digital Crown P5 native parity</p></body></html>").write_pdf()
    _require(pdf.startswith(b"%PDF"), "WeasyPrint PDF generation failed")


def _smoke_qr_pillow() -> None:
    import qrcode
    from PIL import Image

    output = io.BytesIO()
    qrcode.make("digitalcrown:p5:native-parity").save(output, format="PNG")
    output.seek(0)
    with Image.open(output) as image:
        image.verify()
    output.seek(0)
    with Image.open(output) as image:
        _require(image.width > 0 and image.height > 0, "Pillow/QR image generation failed")


def run_native_runtime() -> None:
    with tempfile.TemporaryDirectory(prefix="digitalcrown-p5-") as temp_dir:
        tmp = Path(temp_dir)
        _smoke_opencv()
        _smoke_onnxruntime(tmp)
        _smoke_torch()
        _smoke_sqlcipher(tmp)
        _smoke_reportlab()
        _smoke_weasyprint()
        _smoke_qr_pillow()
    print(f"NATIVE_RUNTIME_GATE=OK ({platform.system()} {platform.machine()})")


def _bootstrap_backend_namespace() -> None:
    """Load scientific service modules without executing backend/__init__.py.

    P5 certifies native/scientific runtime boundaries. The application package
    initializer eagerly registers SQLAlchemy models, which is intentionally
    outside this focused dependency harness. A namespace package keeps imports
    pointed at the real backend source tree without pulling that unrelated
    application startup side effect into the certification environment.
    """
    if "backend" not in sys.modules:
        backend_pkg = types.ModuleType("backend")
        backend_pkg.__path__ = [str(ROOT / "backend")]
        backend_pkg.__package__ = "backend"
        sys.modules["backend"] = backend_pkg

    if "backend.services" not in sys.modules:
        services_pkg = types.ModuleType("backend.services")
        services_pkg.__path__ = [str(ROOT / "backend" / "services")]
        services_pkg.__package__ = "backend.services"
        sys.modules["backend.services"] = services_pkg


def run_fail_closed_runtime() -> None:
    import cv2
    import numpy as np

    _bootstrap_backend_namespace()

    from backend.services import panoramic_service as panoramic_module
    from backend.services import sota_vision_service as sota_module
    from backend.services import vision_service as vision_module

    with tempfile.TemporaryDirectory(prefix="digitalcrown-p5-failclosed-") as temp_dir:
        tmp = Path(temp_dir)
        image_path = tmp / "reference.png"
        _require(cv2.imwrite(str(image_path), np.zeros((64, 64, 3), dtype=np.uint8)), "Failed to write fail-closed fixture")

        with patch.object(sota_module.AppPaths, "get_model_path", side_effect=lambda name: tmp / "missing" / name):
            sota = sota_module.SOTAVisionEngine()
        _require(sota.is_ready is False and sota.predict_landmarks(str(image_path)) is None, "SOTA missing-model path must remain disabled")

        with (
            patch.object(vision_module.sota_vision_engine, "is_ready", False),
            patch.object(vision_module.vision_engine, "is_ready", False),
            patch.object(vision_module.vision_engine, "model", None),
        ):
            result = vision_module.vision_engine.predict_landmarks(str(image_path))
        _require(result.get("mode_inference") == "FAILED", "Cephalo missing-model path must return FAILED")
        _require(result.get("landmarks") == [], "Cephalo missing-model path must not fabricate landmarks")
        _require("manuel" in str(result.get("warning", "")).lower(), "Cephalo missing-model path must require manual placement")

        pano = panoramic_module.PanoramicEngine()
        with patch.object(panoramic_module, "_is_clinical_environment", return_value=True):
            try:
                pano.predict(str(image_path))
            except RuntimeError:
                pass
            else:
                raise AssertionError("Panoramic missing-model path must raise in clinical environment")

    print("SCIENTIFIC_FAIL_CLOSED_GATE=OK")


def check_apple_silicon() -> None:
    machine = platform.machine().lower()
    _require(platform.system() == "Darwin", "Apple Silicon gate requires macOS")
    _require(machine in {"arm64", "aarch64"}, f"Expected Apple Silicon arm64 runner, got {machine}")
    print(f"APPLE_SILICON_GATE=OK ({machine})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Digital Crown Portability P5 native/scientific certification")
    parser.add_argument("--runtime", action="store_true", help="execute real native runtime smoke checks")
    parser.add_argument("--fail-closed", action="store_true", help="execute scientific missing-asset fail-closed runtime checks")
    parser.add_argument("--expect-apple-silicon", action="store_true", help="require Darwin arm64/aarch64")
    args = parser.parse_args()

    check_dependency_contract()
    check_model_path_contract()
    check_scientific_scope_contract()
    check_fail_closed_source_contract()
    if args.runtime:
        run_native_runtime()
    if args.fail_closed:
        run_fail_closed_runtime()
    if args.expect_apple_silicon:
        check_apple_silicon()
    print("PORTABILITY_P5_CHECK=SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
