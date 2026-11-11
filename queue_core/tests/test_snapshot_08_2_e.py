"""LOT08.2-E isolated FUE: real cross-process OS gate, coherent 3-file synthetic SQLite.

NOT a production backup protocol, Windows Desktop service deployment, or power
loss test. No patient information, external network or clinic resources.
"""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest

from scripts.quality.lot08_2_e_snapshot_lab import (
    CrossProcessGate,
    FILES,
    MANIFEST,
    SnapshotLabError,
    create_synthetic_fixture,
    restore_synthetic,
    snapshot_synthetic,
    transition_synthetic,
    verify_bundle,
)


@pytest.fixture
def sources(tmp_path):
    folder = tmp_path / "synthetic-origin"
    create_synthetic_fixture(folder)
    return folder


def _events(path: Path) -> tuple[int, int]:
    with sqlite3.connect(path) as db:
        epoch = db.execute("SELECT epoch FROM lab_epoch WHERE id=1").fetchone()[0]
        count = db.execute("SELECT count(*) FROM synthetic_events").fetchone()[0]
    return epoch, count


def test_consistent_archive_restore_and_refuse_overwrite(sources, tmp_path):
    transition_synthetic(sources, 1)
    transition_synthetic(sources, 2)
    bundle = tmp_path / "synthetic-archive"
    assert snapshot_synthetic(sources, bundle) == 2
    assert verify_bundle(bundle) == 2
    target = tmp_path / "synthetic-restored"
    assert restore_synthetic(bundle, target) == 2
    assert all(_events(target / name) == (2, 2) for name in FILES)
    for path in (target / name for name in FILES):
        with sqlite3.connect(path) as db:
            assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    with pytest.raises(SnapshotLabError, match="LAB_RESTORE_REFUSE_OVERWRITE"):
        restore_synthetic(bundle, target)
    assert all(_events(target / name) == (2, 2) for name in FILES)


def test_partial_multi_database_commit_must_fail_closed(sources, tmp_path):
    with pytest.raises(SnapshotLabError, match="LAB_INJECTED_PARTIAL_COMMIT"):
        transition_synthetic(sources, 1, fail_after=1)
    bundle = tmp_path / "should-not-exist"
    with pytest.raises(SnapshotLabError, match="LAB_CROSS_STORE_EPOCH_DIVERGED"):
        snapshot_synthetic(sources, bundle)
    assert not bundle.exists()
    assert not list(tmp_path.glob(".08e-snapshot-staging-*"))
    assert [_events(sources / name)[0] for name in FILES] == [1, 0, 0]


def test_incomplete_snapshot_staging_is_deleted(sources, tmp_path):
    target = tmp_path / "should-not-exist"
    with pytest.raises(SnapshotLabError, match="LAB_INJECTED_SNAPSHOT_INTERRUPTION"):
        snapshot_synthetic(sources, target, fail_after=2)
    assert not target.exists()
    assert not list(tmp_path.glob(".08e-snapshot-staging-*"))
    assert snapshot_synthetic(sources, target) == 0


def test_tampered_and_missing_backups_rejected_without_overwrite(sources, tmp_path):
    bundle = tmp_path / "synthetic-archive"
    snapshot_synthetic(sources, bundle)
    dest = tmp_path / "refused"
    with (bundle / FILES[0]).open("r+b") as target:
        target.seek(110)
        target.write(b"CHANGED-BY-NEGATIVE-TEST")
    with pytest.raises(SnapshotLabError, match="LAB_HASH_MISMATCH"):
        restore_synthetic(bundle, dest)
    assert not dest.exists()
    (bundle / FILES[1]).unlink()
    with pytest.raises(SnapshotLabError, match="LAB_BUNDLE_CONTENTS"):
        restore_synthetic(bundle, dest)
    assert not dest.exists()


def test_manifest_epoch_and_extra_file_refused(sources, tmp_path):
    bundle = tmp_path / "synthetic-archive"
    snapshot_synthetic(sources, bundle)
    manifest = bundle / MANIFEST
    content = json.loads(manifest.read_text(encoding="utf-8"))
    content["epoch"] = 99
    manifest.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(SnapshotLabError, match="LAB_CROSS_STORE_EPOCH_DIVERGED"):
        restore_synthetic(bundle, tmp_path / "refused")
    content["epoch"] = 0
    manifest.write_text(json.dumps(content), encoding="utf-8")
    (bundle / "intruder.txt").write_text("NO_PATIENT_DATA", encoding="utf-8")
    with pytest.raises(SnapshotLabError, match="LAB_BUNDLE_CONTENTS"):
        verify_bundle(bundle)


def test_cooperating_second_process_writes_during_snapshots(sources, tmp_path):
    """The writer is a REAL second Python process, sharing an OS file lock."""
    ready = tmp_path / "writer-ready"
    code = (
        "from pathlib import Path\n"
        "import sys,time\n"
        "from scripts.quality.lot08_2_e_snapshot_lab import transition_synthetic\n"
        "root,ready=map(Path,sys.argv[1:3])\n"
        "for epoch in range(1, 41):\n"
        "    transition_synthetic(root, epoch, delay=0.004)\n"
        "    if epoch==1: ready.write_text('ready')\n"
        "    time.sleep(0.005)\n"
    )
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ, PYTHONPATH=str(repo_root))
    worker = subprocess.Popen(
        [sys.executable, "-c", code, str(sources), str(ready)],
        env=env, cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    seen_in_flight = False
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and worker.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists(), "BACKGROUND_WRITER_DID_NOT_START"
        for i in range(5):
            if worker.poll() is None:
                seen_in_flight = True
            bundle = tmp_path / ("snapshot-%d" % i)
            revision = snapshot_synthetic(sources, bundle)
            assert verify_bundle(bundle) == revision
            assert all(_events(bundle / name) == (revision, revision) for name in FILES)
            dest = tmp_path / ("restore-%d" % i)
            assert restore_synthetic(bundle, dest) == revision
            assert all(_events(dest / name) == (revision, revision) for name in FILES)
        stdout, stderr = worker.communicate(timeout=20)
        assert worker.returncode == 0, (stdout[-300:], stderr[-500:])
        assert seen_in_flight, "CONCURRENCY_NOT_OBSERVED"
        assert all(_events(sources / name) == (40, 40) for name in FILES)
    finally:
        if worker.poll() is None:
            worker.kill()
            worker.communicate(timeout=10)


def test_existing_clinical_destination_is_never_modified(sources, tmp_path):
    bundle = tmp_path / "snapshot"
    snapshot_synthetic(sources, bundle)
    protected = tmp_path / "do-not-touch"
    protected.mkdir()
    protected_file = protected / "existing-clinic-database.sqlite"
    protected_file.write_bytes(b"UNTOUCHABLE")
    with pytest.raises(SnapshotLabError, match="LAB_RESTORE_REFUSE_OVERWRITE"):
        restore_synthetic(bundle, protected)
    assert protected_file.read_bytes() == b"UNTOUCHABLE"
