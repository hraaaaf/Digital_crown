"""LOT06-P proof: actual Digital Crown FastAPI lifespan starts/joins LAB worker.

Isolated fake image only. All optional external observers are patched out;
no real camera, patient attachment, cloud calls, Windows service or installer.
"""
from contextlib import ExitStack, closing, contextmanager
import asyncio
import pytest
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import time
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.main import app, lifespan
from backend.models_media_core import ClinicalAsset
from tools.imaging_gateway.bridge_background_lab import (
    start_if_enabled as real_start, stop_bridge_lab as real_stop,
)

FAKE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)


@contextmanager
def _real_backend_lifespan():
    """Same isolation stubs as backend/tests/conftest.py::client.

    The actual FastAPI lifespan runs; only unrelated side effects outside
    this synthetic lab are replaced by inert in-process doubles.
    """
    with ExitStack() as stack:
        stack.enter_context(patch("backend.main.panoramic_engine.initialize", new_callable=AsyncMock))
        stack.enter_context(patch("backend.main.run_full_seed", return_value=None))
        stack.enter_context(patch("backend.main.seed_clinical_data", return_value=None))
        stack.enter_context(patch("backend.main.seed_admin_user", return_value=None))
        stack.enter_context(patch("backend.main.sync_manager.start_listening", return_value=None))
        stack.enter_context(patch("backend.main._sync_all_licenses_from_firebase", new_callable=AsyncMock))
        stack.enter_context(patch("backend.services.daily_scheduler.start_daily_scheduler", return_value=None))
        stack.enter_context(patch("backend.services.fts_indexer.bulk_index_unindexed_patients", return_value=None))
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client


def _lab_root(root: Path) -> Path:
    (root / ".digitalcrown-imaging-lab-only").write_text(
        "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n", encoding="utf-8",
    )
    incoming = root / "incoming"
    incoming.mkdir()
    return incoming


def _fake_photo(path: Path) -> None:
    path.write_bytes(FAKE_PNG)
    path.with_name(path.name + ".ready").write_text(
        json.dumps({
            "version": 1, "size": len(FAKE_PNG),
            "sha256": hashlib.sha256(FAKE_PNG).hexdigest(),
        }), encoding="utf-8",
    )


def test_full_fastapi_lifespan_launches_and_joins_synthetic_bridge(monkeypatch, db):
    with tempfile.TemporaryDirectory(prefix="dc-bridge-lifespan-") as tmp:
        root = Path(tmp)
        incoming = _lab_root(root)
        monkeypatch.setenv("DC_V15_06_BRIDGE_LAB", "1")
        monkeypatch.setenv("DC_V15_06_BRIDGE_LAB_ROOT", str(root))
        monkeypatch.setenv("DC_V15_06_BRIDGE_LAB_KEY_HEX", (b"k" * 32).hex())
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")

        before = db.query(ClinicalAsset).count()
        source = incoming / "fake_lifespan.png"
        _fake_photo(source)
        with patch("tools.imaging_gateway.bridge_background_lab.start_if_enabled",
                   wraps=real_start) as start_spy, patch(
                       "tools.imaging_gateway.bridge_background_lab.stop_bridge_lab",
                       wraps=real_stop) as stop_spy:
            with _real_backend_lifespan() as client:
                assert start_spy.call_count == 1
                assert client.get("/openapi.json").status_code == 200
                db_path = root / "private" / "acquisitions.sqlite3"
                deadline = time.monotonic() + 8
                state = None
                while time.monotonic() < deadline:
                    if db_path.exists():
                        with closing(sqlite3.connect(db_path)) as connection:
                            item = connection.execute(
                                "SELECT state FROM items"
                            ).fetchone()
                        if item is not None:
                            state = item[0]
                            break
                    time.sleep(0.05)
                assert state == "PENDING_CONFIRMATION", state
                assert source.read_bytes() == FAKE_PNG
                assert db.query(ClinicalAsset).count() == before
            # TestClient exiting must run the actual application's shutdown.
            assert stop_spy.await_count == 1
            handle = stop_spy.await_args.args[0]
            assert handle.task.done()
        # TEMP cleanup is part of the test, not swallowed by skip/ignore.
        assert db.query(ClinicalAsset).count() == before


def test_full_fastapi_lifespan_does_not_start_bridge_without_opt_in(monkeypatch, db):
    monkeypatch.delenv("DC_V15_06_BRIDGE_LAB", raising=False)
    monkeypatch.delenv("DC_V15_06_BRIDGE_LAB_ROOT", raising=False)
    monkeypatch.delenv("DC_V15_06_BRIDGE_LAB_KEY_HEX", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    with patch("tools.imaging_gateway.bridge_background_lab.start_if_enabled",
               side_effect=AssertionError("LAB_WAS_STARTED_WHEN_DISABLED")) as start_spy:
        with _real_backend_lifespan() as client:
            assert client.get("/openapi.json").status_code == 200
        start_spy.assert_not_called()


def test_actual_fastapi_lifespan_finally_stops_bridge_on_exception(monkeypatch, db):
    with tempfile.TemporaryDirectory(prefix="dc-abnormal-lifespan-") as tmp:
        root = Path(tmp)
        _lab_root(root)
        monkeypatch.setenv("DC_V15_06_BRIDGE_LAB", "1")
        monkeypatch.setenv("DC_V15_06_BRIDGE_LAB_ROOT", str(root))
        monkeypatch.setenv("DC_V15_06_BRIDGE_LAB_KEY_HEX", (b"k" * 32).hex())
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
        async def exercise_failure():
            async with lifespan(app):
                raise RuntimeError("SYNTHETIC_LIFESPAN_ABORT")

        with ExitStack() as stack:
            stack.enter_context(patch("backend.main.panoramic_engine.initialize", new_callable=AsyncMock))
            stack.enter_context(patch("backend.main.run_full_seed", return_value=None))
            stack.enter_context(patch("backend.main.seed_clinical_data", return_value=None))
            stack.enter_context(patch("backend.main.seed_admin_user", return_value=None))
            stack.enter_context(patch("backend.main.sync_manager.start_listening", return_value=None))
            stack.enter_context(patch("backend.main._sync_all_licenses_from_firebase", new_callable=AsyncMock))
            stack.enter_context(patch("backend.services.daily_scheduler.start_daily_scheduler", return_value=None))
            stack.enter_context(patch("backend.services.fts_indexer.bulk_index_unindexed_patients", return_value=None))
            spy = stack.enter_context(patch(
                "tools.imaging_gateway.bridge_background_lab.stop_bridge_lab", wraps=real_stop
            ))
            with pytest.raises(RuntimeError, match="SYNTHETIC_LIFESPAN_ABORT"):
                asyncio.run(exercise_failure())
            assert spy.await_count == 1
            assert spy.await_args.args[0].task.done()
