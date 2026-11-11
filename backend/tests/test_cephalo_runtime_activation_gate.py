"""LOT08.2-I security regression: embedded weights never imply clinical GO.

No patient files or model weights are needed for any of these tests.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.services import cephalo_runtime_gate as gate
from backend.services import sota_vision_service as sota
from backend.services import vision_service as vision


@pytest.mark.parametrize("environment", ["production", "prod", "cabinet-real", "development", "", "TESTING"])
def test_clinical_or_unclassified_environment_never_enables_auto_model(monkeypatch, environment):
    monkeypatch.setenv("ENVIRONMENT", environment)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "1")
    monkeypatch.setenv("DIGITALCROWN_CEPHALO_AUTO_ENABLED", "1")  # never trusted
    assert gate.can_run_cephalo_auto_inference() is False


@pytest.mark.parametrize("isolated", ["0", "", "false"])
def test_missing_isolation_denied_even_on_test_database(monkeypatch, isolated):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", isolated)
    assert gate.can_run_cephalo_auto_inference() is False


def test_real_clinic_sqlite_path_rejected_even_if_environment_spoofed(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///C:/Cabinet/clinical_vault.db")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert gate.can_run_cephalo_auto_inference() is False


@pytest.mark.parametrize("attribute", ["frozen", "_MEIPASS"])
def test_packaged_executable_denied_even_with_test_flags(monkeypatch, attribute):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(sys, attribute, True if attribute == "frozen" else "/synthetic/mei", raising=False)
    assert gate.can_run_cephalo_auto_inference() is False


def test_genuine_in_memory_synthetic_backend_test_is_allowed(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert gate.can_run_cephalo_auto_inference() is True


def test_github_hosted_disposable_sqlite_lab_allowed_but_non_ci_denied(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./t2-runtime-cert.db")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert gate.can_run_cephalo_auto_inference() is True
    monkeypatch.delenv("GITHUB_ACTIONS")
    assert gate.can_run_cephalo_auto_inference() is False


def test_embedded_model_path_does_not_initialize_onnx_when_clinical_hold(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./clinical_vault.db")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "0")
    # Simulate actual ONNX in frozen product: neither stat nor hashing nor
    # InferenceSession must execute before the clinical activation gate.
    monkeypatch.setattr(sota.os.path, "isfile", lambda *_: pytest.fail("asset opened before activation"))
    monkeypatch.setattr(sota, "_sha256_file", lambda *_: pytest.fail("ONNX hashed before activation"))
    class NeverORT:
        @staticmethod
        def InferenceSession(*_a, **_kw):
            pytest.fail("ONNX Runtime activated without clinical approval")
    monkeypatch.setattr(sota, "ort", NeverORT)
    engine = sota.SOTAVisionEngine(model_path="/synthetic/embedded/srpose38-tta-1024.onnx")
    assert engine.is_ready is False
    assert engine.session is None
    assert engine.predict_landmarks("/synthetic/never-read.png") is None


def test_clinical_hold_never_reads_image_or_loads_legacy_pytorch(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./clinical_vault.db")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "0")
    monkeypatch.setattr(vision.cv2, "imread", lambda *_a, **_kw: pytest.fail("patient image read after HOLD"))
    engine = vision.VisionEngine()
    monkeypatch.setattr(engine, "_initialize_legacy_engine", lambda: pytest.fail("legacy fallback activated"))
    result = engine.predict_landmarks("/synthetic/never-read.jpg")
    assert result["mode_inference"] == "FAILED"
    assert result["landmarks"] == []
    assert "désactivé" in result["warning"]
    assert "manuel" in result["warning"].lower()
    assert result["processing_time_ms"] == 0.0


def test_clinical_hold_legacy_constructor_cannot_import_torch(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./clinical_vault.db")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "0")
    engine = vision.VisionEngine()
    engine._initialize_legacy_engine()
    assert engine.legacy_init_attempted is False
    assert engine.torch is None
    assert engine.model is None


def test_blocked_cephalo_predictions_cannot_be_persisted(monkeypatch):
    from backend.services import cephalo_service

    db = MagicMock()
    service = cephalo_service.CephaloService(db)
    monkeypatch.setattr(
        cephalo_service.vision_engine,
        "predict_landmarks",
        lambda _path: {
            "landmarks": [],
            "mode_inference": "FAILED",
            "warning": gate.CEPHALO_AUTO_HOLD_REASON,
            "processing_time_ms": 0.0,
        },
    )
    with pytest.raises(ValueError, match="désactivé"):
        service.process_new_radio(123, "/never-read.jpg", "synthetic://not-persisted")
    db.query.assert_not_called()
    assert service.repo is not None


def test_synthetic_lab_still_initializes_explicitly_pinned_model_with_stub_session(monkeypatch):
    # This verifies the feature gate's interaction with SOTAVisionEngine.
    # Real weight, actual inference and model SHA are independently proven by
    # LOT08.2-H GH run #42910489876; this unit test never supplies fake pixels.
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setattr(sota.os.path, "isfile", lambda *_a: True)
    monkeypatch.setattr(sota.os.path, "getsize", lambda *_a: sota.SRPOSE38_MODEL_SIZE_BYTES)
    monkeypatch.setattr(sota, "_sha256_file", lambda *_a: sota.SRPOSE38_MODEL_SHA256)
    fake_session = SimpleNamespace(
        get_inputs=lambda: [object()],
        get_outputs=lambda: [object()],
    )
    class FakeORT:
        @staticmethod
        def InferenceSession(*args, **kwargs):
            assert kwargs["providers"] == ["CPUExecutionProvider"]
            return fake_session
    monkeypatch.setattr(sota, "ort", FakeORT)
    engine = sota.SOTAVisionEngine(model_path="/synthetic/proof/in-ephemeral-runner.onnx")
    assert engine.is_ready is True
    assert engine.session is fake_session
