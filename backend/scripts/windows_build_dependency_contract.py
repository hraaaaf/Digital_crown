from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_REQUIREMENTS = ROOT / "requirements.txt"
RUNTIME = ROOT / "backend" / "requirements.txt"
P5 = ROOT / "backend" / "requirements-p5-native.txt"
WINDOWS_BUILD = ROOT / "backend" / "requirements-windows-build.txt"

EXACT_RE = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==([^\s;]+)$")
WINDOWS_MARKER = 'platform_system == "Windows"'
NATIVE_SHARED = {"numpy", "onnx", "onnxruntime", "opencv-python-headless", "pillow", "qrcode", "reportlab", "weasyprint", "sqlcipher3", "torch", "torchvision", "torchaudio", "pydantic", "pydantic-settings", "python-dotenv"}
REQUIRED_CABINET_PACKAGES = {"alembic", "firebase-admin", "python-magic", "python-magic-bin", "sentry-sdk", "webauthn"}
FORBIDDEN_ORT_VARIANTS = {"onnxruntime-directml", "onnxruntime-gpu", "onnxruntime-qnn"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _lines(path: Path) -> list[str]:
    return [raw.strip() for raw in path.read_text(encoding="utf-8").splitlines() if raw.strip() and not raw.lstrip().startswith("#")]


def _exact_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in _lines(path):
        if line.startswith("-r "):
            continue
        requirement, separator, marker = line.partition(";")
        if separator:
            _require(marker.strip() == WINDOWS_MARKER, f"Unsupported environment marker in {path.relative_to(ROOT)}: {line}")
        match = EXACT_RE.fullmatch(requirement.strip())
        _require(match is not None, f"Non-exact dependency in {path.relative_to(ROOT)}: {line}")
        name = match.group(1).lower().replace("_", "-")
        version = match.group(2)
        _require(name not in pins, f"Duplicate dependency in {path.relative_to(ROOT)}: {name}")
        pins[name] = version
    return pins


def check_root_mirror() -> None:
    _require(_lines(ROOT_REQUIREMENTS) == _lines(RUNTIME), "Root requirements.txt must exactly mirror backend/requirements.txt for legacy CI compatibility")
    print("ROOT_REQUIREMENTS_MIRROR=OK")


def check_runtime_lock() -> dict[str, str]:
    pins = _exact_pins(RUNTIME)
    for forbidden in FORBIDDEN_ORT_VARIANTS:
        _require(forbidden not in pins, f"Conflicting ONNX Runtime variant in cabinet lock: {forbidden}")
    missing = sorted(REQUIRED_CABINET_PACKAGES - pins.keys())
    _require(not missing, f"Required cabinet runtime dependencies missing: {missing}")
    _require(pins.get("cryptography") == "49.0.0", "WebAuthn 3.0.0 contract requires cryptography==49.0.0 or newer; V1 lock freezes 49.0.0")
    _require(pins.get("webauthn") == "3.0.0", "Cabinet baseline must use webauthn==3.0.0")
    _require(pins.get("onnxruntime") == "1.25.0", "Cabinet baseline must use onnxruntime==1.25.0 CPU")
    _require(pins.get("torch") == "2.10.0", "Cabinet baseline must use torch==2.10.0")
    _require(pins.get("torchvision") == "0.25.0", "Cabinet baseline must use torchvision==0.25.0")
    _require(pins.get("torchaudio") == "2.10.0", "Cabinet baseline must use torchaudio==2.10.0")
    _require(pins.get("svglib") == "1.5.1", "PDF SVG rendering lock must use svglib==1.5.1; svglib 1.6.0 forces the optional Cairo bitmap backend into default installs")
    print(f"WINDOWS_RUNTIME_LOCK=OK ({len(pins)} exact top-level dependencies)")
    return pins


def check_p5_parity(runtime: dict[str, str]) -> None:
    p5 = _exact_pins(P5)
    missing = sorted(name for name in NATIVE_SHARED if name not in p5 or name not in runtime)
    _require(not missing, f"Native dependency missing from runtime/P5 contract: {missing}")
    drift = {name: (runtime[name], p5[name]) for name in sorted(NATIVE_SHARED) if runtime[name] != p5[name]}
    _require(not drift, f"Runtime/P5 native dependency drift: {drift}")
    print("WINDOWS_P5_NATIVE_PARITY=OK")


def check_windows_build_lock() -> None:
    lines = _lines(WINDOWS_BUILD)
    _require(lines.count("-r requirements.txt") == 1, "Windows build lock must include backend/requirements.txt exactly once")
    _require(all("../requirements.txt" not in line for line in lines), "Windows build must not include legacy root requirements.txt")
    pins = _exact_pins(WINDOWS_BUILD)
    _require(pins == {"pyinstaller": "6.22.3"}, f"Unexpected Windows build-only dependencies: {pins}")
    print("WINDOWS_BUILD_TOOLCHAIN=OK (pyinstaller==6.22.3)")


def main() -> int:
    check_root_mirror()
    runtime = check_runtime_lock()
    check_p5_parity(runtime)
    check_windows_build_lock()
    print("WINDOWS_BUILD_DEPENDENCY_CONTRACT=SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# V1-07 G9 exact-head certification trigger: no runtime behavior change.
