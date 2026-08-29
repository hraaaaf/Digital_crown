import hashlib
import json
from pathlib import Path

import pytest

from backend.core.paths import AppPaths
from backend.services.update_engine import UpdateEngine, UpdatePreparationError
from backend.services.update_recovery import UpdateRecoveryService


JOB_ID = "b" * 32


def _patch_data(monkeypatch, tmp_path: Path) -> Path:
    data = tmp_path / "user-data"
    data.mkdir()
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: data))
    return data


def _recovery_job(data: Path, *, job_id: str = JOB_ID, status: str = "applying") -> tuple[Path, Path]:
    job_dir = data / "updates" / "jobs" / job_id
    worker_dir = job_dir / "worker"
    worker_dir.mkdir(parents=True)
    recovery = worker_dir / "windows_update_recovery.ps1"
    recovery.write_text("# recovery worker\n", encoding="utf-8")
    payload = {
        "schema": 1,
        "job_id": job_id,
        "status": status,
        "platform": "windows",
        "worker_contract": "windows-inno-v1",
        "recovery_contract": "windows-interruption-v1",
        "apply_certified": True,
        "worker_recovery_filename": "worker/windows_update_recovery.ps1",
        "windows_update_recovery.ps1_sha256": hashlib.sha256(recovery.read_bytes()).hexdigest(),
    }
    job_path = job_dir / "job.json"
    job_path.write_text(json.dumps(payload), encoding="utf-8")
    return job_path, recovery


def test_startup_recovery_schedules_only_recovery_worker(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    job_path, recovery = _recovery_job(data)
    monkeypatch.setattr(UpdateRecoveryService, "runtime_recovery_supported", staticmethod(lambda: True))
    monkeypatch.setattr(UpdateRecoveryService, "_powershell51", staticmethod(lambda: Path("C:/Windows/powershell.exe")))
    monkeypatch.delenv("DIGITALCROWN_RESTORE_RESTART", raising=False)

    launched = []

    class DummyProcess:
        pass

    def fake_popen(args, **kwargs):
        launched.append((args, kwargs))
        return DummyProcess()

    monkeypatch.setattr("backend.services.update_recovery.subprocess.Popen", fake_popen)

    result = UpdateRecoveryService.schedule_startup_recovery(4321)

    assert result == {"job_id": JOB_ID, "status": "applying", "recovery": "scheduled"}
    assert len(launched) == 1
    args = launched[0][0]
    kwargs = launched[0][1]
    assert str(recovery) in args
    assert str(job_path) in args
    assert "4321" in args
    assert all("DigitalCrownSetup" not in str(value) for value in args)
    assert "env" not in kwargs
    # Scheduling itself must not mutate job.json without worker.lock. The
    # PowerShell recovery worker records ownership only after it acquires the lock.
    persisted = json.loads(job_path.read_text(encoding="utf-8"))
    assert "recovery_parent_pid" not in persisted
    assert "recovery_scheduled_at" not in persisted


def test_startup_recovery_refuses_tampered_worker(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    _, recovery = _recovery_job(data)
    recovery.write_text("tampered", encoding="utf-8")
    monkeypatch.setattr(UpdateRecoveryService, "runtime_recovery_supported", staticmethod(lambda: True))
    monkeypatch.delenv("DIGITALCROWN_RESTORE_RESTART", raising=False)

    with pytest.raises(UpdatePreparationError, match="UPDATE_RECOVERY_WORKER_SHA256_MISMATCH"):
        UpdateRecoveryService.schedule_startup_recovery(4321)


def test_startup_recovery_fails_closed_on_multiple_active_jobs(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    _recovery_job(data, job_id="b" * 32, status="applying")
    _recovery_job(data, job_id="c" * 32, status="health_pending")
    monkeypatch.setattr(UpdateRecoveryService, "runtime_recovery_supported", staticmethod(lambda: True))
    monkeypatch.delenv("DIGITALCROWN_RESTORE_RESTART", raising=False)

    with pytest.raises(UpdatePreparationError, match="UPDATE_RECOVERY_MULTIPLE_ACTIVE_JOBS"):
        UpdateRecoveryService.schedule_startup_recovery(4321)


def test_worker_controlled_runtime_never_schedules_recovery(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    _recovery_job(data, status="health_pending")
    monkeypatch.setattr(UpdateRecoveryService, "runtime_recovery_supported", staticmethod(lambda: True))
    monkeypatch.setenv("DIGITALCROWN_RESTORE_RESTART", "1")
    assert UpdateRecoveryService.schedule_startup_recovery(4321) is None


def test_legacy_job_without_recovery_contract_is_not_auto_recovered(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    job_path, _ = _recovery_job(data)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload.pop("recovery_contract")
    job_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(UpdateRecoveryService, "runtime_recovery_supported", staticmethod(lambda: True))
    monkeypatch.delenv("DIGITALCROWN_RESTORE_RESTART", raising=False)
    assert UpdateRecoveryService.schedule_startup_recovery(4321) is None


def test_interrupted_download_stale_partial_is_replaced_from_scratch(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    job_id = "d" * 32
    job_dir = data / "updates" / "jobs" / job_id
    job_dir.mkdir(parents=True)
    stale = job_dir / "update.bin.partial"
    stale.write_bytes(b"stale-partial-corruption")
    payload = b"fresh-authenticated-payload"
    verified = {
        "target": {
            "filename": "update.bin",
            "url": "https://updates.example.invalid/update.bin",
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    }

    class FakeResponse:
        status = 200

        def __init__(self):
            self._sent = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def geturl(self):
            return "https://updates.example.invalid/update.bin"

        def read(self, size):
            if self._sent:
                return b""
            self._sent = True
            return payload

    monkeypatch.setattr("backend.services.update_engine.urllib.request.urlopen", lambda request, timeout=60: FakeResponse())

    final = UpdateEngine.download_target(verified, job_id)

    assert final.read_bytes() == payload
    assert not stale.exists()
    assert hashlib.sha256(final.read_bytes()).hexdigest() == verified["target"]["sha256"]


def test_windows_entry_waits_only_for_direct_wrapper_process():
    entry = Path(__file__).resolve().parents[2] / "scripts" / "windows_update_worker_entry.ps1"
    source = entry.read_text(encoding="utf-8")

    assert "$child.WaitForExit()" in source
    assert " -Wait" not in source


def test_windows_recovery_path_separators_are_char_safe():
    recovery = Path(__file__).resolve().parents[2] / "scripts" / "windows_update_recovery.ps1"
    source = recovery.read_text(encoding="utf-8")

    assert ".TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)" in source
    assert ".TrimStart([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)" in source
    assert ".Replace([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)" in source
    assert r"TrimEnd('\\', '/')" not in source
    assert r"TrimStart('\\', '/')" not in source
    assert r"Replace('\\', '/')" not in source
