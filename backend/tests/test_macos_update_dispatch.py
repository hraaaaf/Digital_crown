import pytest

from backend.services.macos_update_apply import MacOSUpdateApplyService
from backend.services.update_apply import CONFIRMATION_TOKEN, UpdateApplyService
from backend.services.update_dispatch import UpdateApplyDispatchService
from backend.services.update_engine import UpdateEngine, UpdatePreparationError


def test_windows_dispatch_bypasses_macos_preflight(monkeypatch):
    monkeypatch.setattr(UpdateEngine, "get_job", classmethod(lambda cls, job_id: {"platform": "windows", "version": "0.0.1"}))
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "runtime_apply_supported",
        staticmethod(lambda: (_ for _ in ()).throw(AssertionError("macOS preflight must not run for Windows"))),
    )
    monkeypatch.setattr(
        UpdateApplyService,
        "request_apply",
        classmethod(lambda cls, job_id, confirmation: {"path": "windows"}),
    )
    assert UpdateApplyDispatchService.request_apply("a" * 32, CONFIRMATION_TOKEN) == {"path": "windows"}


def test_macos_downgrade_is_rejected_before_apply(monkeypatch):
    monkeypatch.setattr(UpdateEngine, "get_job", classmethod(lambda cls, job_id: {"platform": "macos", "version": "1.0.0"}))
    monkeypatch.setattr(MacOSUpdateApplyService, "runtime_apply_supported", staticmethod(lambda: True))
    monkeypatch.setattr(MacOSUpdateApplyService, "_current_version", classmethod(lambda cls: "1.0.1"))
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "request_apply",
        classmethod(lambda cls, job_id, confirmation: (_ for _ in ()).throw(AssertionError("downgrade must not reach apply"))),
    )
    with pytest.raises(UpdatePreparationError, match="UPDATE_VERSION_NOT_NEWER"):
        UpdateApplyDispatchService.request_apply("b" * 32, CONFIRMATION_TOKEN)


def test_macos_unwritable_install_parent_is_rejected_before_parent_exit(monkeypatch, tmp_path):
    install_app = tmp_path / "Applications" / "DigitalCrown.app"
    install_app.parent.mkdir()
    monkeypatch.setattr(UpdateEngine, "get_job", classmethod(lambda cls, job_id: {"platform": "macos", "version": "1.0.1"}))
    monkeypatch.setattr(MacOSUpdateApplyService, "runtime_apply_supported", staticmethod(lambda: True))
    monkeypatch.setattr(MacOSUpdateApplyService, "_current_version", classmethod(lambda cls: "1.0.0"))
    monkeypatch.setattr(MacOSUpdateApplyService, "_installed_app", staticmethod(lambda: install_app))
    monkeypatch.setattr("backend.services.update_dispatch.os.access", lambda path, mode: False)
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "request_apply",
        classmethod(lambda cls, job_id, confirmation: (_ for _ in ()).throw(AssertionError("unwritable install must not reach apply"))),
    )
    with pytest.raises(UpdatePreparationError, match="UPDATE_MACOS_INSTALL_PARENT_NOT_WRITABLE"):
        UpdateApplyDispatchService.request_apply("e" * 32, CONFIRMATION_TOKEN)


def test_macos_invalid_confirmation_keeps_apply_error_ordering(monkeypatch):
    monkeypatch.setattr(UpdateEngine, "get_job", classmethod(lambda cls, job_id: {"platform": "macos", "version": "0.0.1"}))
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "runtime_apply_supported",
        staticmethod(lambda: (_ for _ in ()).throw(AssertionError("runtime preflight must not run before confirmation"))),
    )

    def reject_confirmation(cls, job_id, confirmation):
        raise ValueError(f"Confirmation exacte requise : {CONFIRMATION_TOKEN}")

    monkeypatch.setattr(MacOSUpdateApplyService, "request_apply", classmethod(reject_confirmation))
    with pytest.raises(ValueError, match="METTRE_A_JOUR"):
        UpdateApplyDispatchService.request_apply("c" * 32, "NON")


def test_macos_runtime_gate_keeps_apply_error_ordering(monkeypatch):
    monkeypatch.setattr(UpdateEngine, "get_job", classmethod(lambda cls, job_id: {"platform": "macos", "version": "0.0.1"}))
    monkeypatch.setattr(MacOSUpdateApplyService, "runtime_apply_supported", staticmethod(lambda: False))
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_current_version",
        classmethod(lambda cls: (_ for _ in ()).throw(AssertionError("version preflight must not run when runtime is unsupported"))),
    )

    def reject_runtime(cls, job_id, confirmation):
        raise UpdatePreparationError("UPDATE_RUNTIME_APPLY_UNSUPPORTED")

    monkeypatch.setattr(MacOSUpdateApplyService, "request_apply", classmethod(reject_runtime))
    with pytest.raises(UpdatePreparationError, match="UPDATE_RUNTIME_APPLY_UNSUPPORTED"):
        UpdateApplyDispatchService.request_apply("d" * 32, CONFIRMATION_TOKEN)
