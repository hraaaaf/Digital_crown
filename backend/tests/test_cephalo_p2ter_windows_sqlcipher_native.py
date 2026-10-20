"""P2ter++ Windows NTFS + SQLCipher native process-kill recovery certification.

Only disposable synthetic T2 records. Not a power-loss / UPS / storage-failure test.
Explicitly proves that a real Windows process is TerminateProcess-killed in both
commit windows, then independently reopens an encrypted SQLCipher database.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import time

import pytest

PATIENT_ID = 97531
ANALYSIS_ID = 86420
REVISION = 7
DIGEST = "p2ter-t2-windows-native"
FILENAME = "ceph-t2-windows-native.pdf"
PDF = b"%PDF-1.4\n% T2 synthetic only (NO PATIENT INFORMATION)\n%%EOF\n"


def _make_engine(db_path: Path, key: str):
    """Use SQLAlchemy's actual pysqlcipher dialect and the real sqlcipher3 driver."""
    import sqlcipher3
    sys.modules["pysqlcipher3"] = sqlcipher3
    from sqlalchemy import create_engine
    from sqlalchemy.engine import URL
    from sqlalchemy.pool import NullPool

    url = URL.create(
        "sqlite+pysqlcipher", password=key, database=str(db_path)
    )
    return create_engine(
        url, poolclass=NullPool, connect_args={"timeout": 10}
    )


def _check_encrypted(engine, db_path: Path) -> None:
    with engine.connect() as conn:
        version = conn.exec_driver_sql("PRAGMA cipher_version").scalar()
        assert version and isinstance(version, str), "SQLCipher driver not active"
        assert conn.exec_driver_sql("PRAGMA integrity_check").scalar() == "ok"
        journal = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
        assert str(journal).lower() == "wal", f"Expected native WAL, got {journal!r}"
    if db_path.is_file():
        assert db_path.read_bytes()[:16] != b"SQLite format 3\x00", (
            "Encrypted DB has SQLite plaintext header"
        )
        try:
            with sqlite3.connect(db_path) as plaintext:
                plaintext.execute("SELECT name FROM sqlite_master").fetchall()
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("Native SQLite could read the encrypted cabinet fixture")


def _setup_engine(db_path: Path, key: str):
    engine = _make_engine(db_path, key)
    from backend import models
    models.DocumentArchive.__table__.create(engine, checkfirst=True)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        mode = conn.exec_driver_sql("PRAGMA journal_mode=WAL").scalar()
        assert str(mode).lower() == "wal", f"SQLCipher WAL unavailable: {mode!r}"
        conn.exec_driver_sql("PRAGMA synchronous=NORMAL")
    _check_encrypted(engine, db_path)
    return engine


def _journal(root: Path) -> Path:
    return root / ".cephalo-pending" / str(PATIENT_ID) / str(ANALYSIS_ID) / f"{REVISION}.json"


def _rows(engine):
    from sqlalchemy.orm import Session
    from backend import models
    with Session(engine) as session:
        return [
            (d.file_path, d.file_hash, d.file_size, d.clinical_data)
            for d in session.query(models.DocumentArchive).all()
        ]


def _child(mode: str, db_arg: str, archive_arg: str, marker_arg: str):
    from sqlalchemy.orm import Session
    from backend import models
    from backend.services import archive_service
    from backend.services.cephalo_document_lock import already_archived_pdf

    db_path, root, marker = Path(db_arg), Path(archive_arg), Path(marker_arg)
    engine = _setup_engine(db_path, os.environ["P2TER_NATIVE_SQLCIPHER_TEST_KEY"])
    archive_service.ARCHIVE_BASE_DIR = root
    try:
        with Session(engine) as session:
            if mode == "replay":
                value = already_archived_pdf(
                    session, patient_id=PATIENT_ID, analysis_id=ANALYSIS_ID,
                    revision=REVISION, payload_digest=DIGEST,
                )
                assert value is not None and value[1] == PDF
                assert not _journal(root).exists()
                return
            if mode in ("kill-before", "kill-after"):
                original_commit = session.commit

                def interrupted_commit():
                    if mode == "kill-before":
                        session.flush()
                    else:
                        original_commit()
                    # Native-process control proves whether Windows removes
                    # *any* child-created, closed+fsynced file on hard exit,
                    # independently of the cephalometric archive code.
                    child_control = root / ".native-child-created-control"
                    with child_control.open("wb") as stream:
                        stream.write(b"T2-CHILD-FILE-DURABLE")
                        stream.flush()
                        os.fsync(stream.fileno())
                    # Adjacent controls match both archive file-creation modes
                    # and parent directories. This distinguishes generic x-mode
                    # or directory effects from product-specific file handling.
                    saved_pdf = next(root.rglob("*.pdf"))
                    saved_journal = next(root.rglob("*.json"))
                    adjacent_xb = saved_pdf.with_name(".native-adjacent-xb-control")
                    with adjacent_xb.open("xb") as stream:
                        stream.write(b"T2-ADJACENT-EXCLUSIVE-CONTROL")
                        stream.flush()
                        os.fsync(stream.fileno())
                    adjacent_osopen = saved_journal.with_name(".native-adjacent-osopen-control")
                    fd = os.open(adjacent_osopen, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(b"T2-ADJACENT-OSOPEN-CONTROL")
                        stream.flush()
                        os.fsync(stream.fileno())
                    # Matched-extension controls in the *same folders*, with
                    # real PDF/JSON suffixes. Their survival distinguishes a
                    # suffix-level cleanup from archive-specific disappearance.
                    pdf_suffix_control = saved_pdf.with_name(".native-matched.pdf")
                    with pdf_suffix_control.open("xb") as stream:
                        stream.write(PDF)
                        stream.flush()
                        os.fsync(stream.fileno())
                    journal_suffix_control = saved_journal.with_name(".native-matched.json")
                    fd = os.open(journal_suffix_control, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(b'{"test_only":true}\\n')
                        stream.flush()
                        os.fsync(stream.fileno())
                    # Observe *before* TerminateProcess, while the archive
                    # writer is still alive. The marker is proof of the state
                    # actually reached, never a fabricated outcome.
                    checkpoint = {
                        "mode": mode,
                        "expected_root": str(root.resolve()),
                        "service_root": str(archive_service.ARCHIVE_BASE_DIR.resolve()),
                        "archive_root_exists": root.exists(),
                        "child_control_exists": child_control.is_file(),
                        "adjacent_xb_exists": adjacent_xb.is_file(),
                        "adjacent_osopen_exists": adjacent_osopen.is_file(),
                        "pdf_suffix_control": pdf_suffix_control.is_file(),
                        "journal_suffix_control": journal_suffix_control.is_file(),
                        "pdf_files": sorted(str(p.relative_to(root)) for p in root.rglob("*.pdf") if p.name == FILENAME),
                        "journal_files": sorted(str(p.relative_to(root)) for p in root.rglob("*.json") if p.name == f"{REVISION}.json"),
                        "root_entries": sorted(p.name for p in root.iterdir()) if root.exists() else [],
                    }
                    marker.write_text(json.dumps(checkpoint, sort_keys=True), encoding="utf-8")
                    with marker.open("rb") as stream:
                        os.fsync(stream.fileno())
                    # Parent must invoke actual Windows TerminateProcess; no
                    # exceptions or Python finalizers may run in the child.
                    while True:
                        time.sleep(2)
                session.commit = interrupted_commit

            archive_service.ArchiveService(session).archive_document(
                patient_id=PATIENT_ID,
                analysis_id=ANALYSIS_ID,
                file_content=PDF,
                filename=FILENAME,
                doc_type=models.DocumentType.RAPPORT_CEPHALO,
                title="SYNTHETIC T2 WINDOWS",
                clinical_data={
                    "cephalo_analysis_id": ANALYSIS_ID,
                    "cephalo_analysis_revision": REVISION,
                    "cephalo_archive_payload_digest": DIGEST,
                },
            )
    finally:
        engine.dispose()


def _run_child(mode: str, db: Path, root: Path, marker: Path, env: dict, kill: bool):
    repo_root = Path(__file__).resolve().parents[2]
    # Running this file by path normally sets sys.path[0] to backend/tests,
    # not to the repository root. Keep imports deterministic in the child.
    child_env = {**env, "PYTHONPATH": str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")}
    cmd = [sys.executable, str(Path(__file__).resolve()), "--child",
           mode, str(db), str(root), str(marker)]
    if not kill:
        done = subprocess.run(cmd, cwd=repo_root,
                              env=child_env, capture_output=True, text=True, timeout=70)
        assert done.returncode == 0, (
            f"Native {mode} child failed (exit {done.returncode}): "
            f"{done.stderr[-1500:]} {done.stdout[-700:]}"
        )
        return
    process = subprocess.Popen(
        cmd, cwd=repo_root,
        env=child_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        cutoff = time.monotonic() + 50
        while not marker.exists() and process.poll() is None and time.monotonic() < cutoff:
            time.sleep(0.1)
        if not marker.exists():
            if process.poll() is None:
                process.kill()
            output, errors = process.communicate(timeout=15)
            secret = env["P2TER_NATIVE_SQLCIPHER_TEST_KEY"]
            sanitized = (errors[-2500:] + "\n" + output[-800:]).replace(secret, "[REDACTED_KEY]")
            raise AssertionError(
                "Native child failed before interruption window: "
                f"returncode={process.returncode}, diagnostics={sanitized}"
            )
        checkpoint = json.loads(marker.read_text(encoding="utf-8"))
        assert checkpoint["mode"] == mode
        assert process.poll() is None, "Child ended before native termination"
        assert checkpoint["service_root"] == checkpoint["expected_root"], checkpoint
        # The archive must exist *before* we kill the Windows process.
        # This detects a wrongly directed test fixture instead of treating
        # a missing PDF as a valid crash-recovery result.
        assert len(checkpoint["pdf_files"]) == 1 and len(checkpoint["journal_files"]) == 1, (
            "Archive missing before TerminateProcess: " + json.dumps(checkpoint, sort_keys=True)
        )
        process.kill()  # Windows API TerminateProcess, not os._exit or fake exception
        process.communicate(timeout=15)
        assert process.returncode != 0, "TerminateProcess unexpectedly succeeded as normal exit"
        after_kill = {
            "root_exists": root.exists(),
            "pdf_files": sorted(str(p.relative_to(root)) for p in root.rglob("*.pdf") if p.name == FILENAME),
            "journal_files": sorted(str(p.relative_to(root)) for p in root.rglob("*.json") if p.name == f"{REVISION}.json"),
            "root_entries": sorted(p.name for p in root.iterdir()) if root.exists() else [],
            "control_exists": (root / ".native-test-control").is_file(),
            "child_control_exists": (root / ".native-child-created-control").is_file(),
            "adjacent_xb_exists": (root / checkpoint["pdf_files"][0]).with_name(".native-adjacent-xb-control").is_file(),
            "adjacent_osopen_exists": (root / checkpoint["journal_files"][0]).with_name(".native-adjacent-osopen-control").is_file(),
            "pdf_suffix_control": (root / checkpoint["pdf_files"][0]).with_name(".native-matched.pdf").is_file(),
            "journal_suffix_control": (root / checkpoint["journal_files"][0]).with_name(".native-matched.json").is_file(),
            "direct_pdf_exists": (root / checkpoint["pdf_files"][0]).is_file(),
            "direct_journal_exists": (root / checkpoint["journal_files"][0]).is_file(),
            "pdf_parent_entries": sorted(p.name for p in (root / checkpoint["pdf_files"][0]).parent.iterdir()),
            "journal_parent_entries": sorted(p.name for p in (root / checkpoint["journal_files"][0]).parent.iterdir()),
        }
        assert after_kill["pdf_files"] == checkpoint["pdf_files"] and after_kill["journal_files"] == checkpoint["journal_files"], (
            "Native NTFS process-kill persistence discrepancy: "
            + json.dumps({"before": checkpoint, "after": after_kill}, sort_keys=True)
        )
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=15)


def _volume_fs(path: Path) -> str:
    volume = str(path.anchor)
    fs = ctypes.create_unicode_buffer(128)
    kernel32 = ctypes.windll.kernel32
    kernel32.GetVolumeInformationW.argtypes = [
        ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_wchar_p, ctypes.c_uint,
    ]
    kernel32.GetVolumeInformationW.restype = ctypes.c_int
    ok = kernel32.GetVolumeInformationW(
        volume, None, 0, None, None, None, fs, len(fs)
    )
    assert ok, "Windows GetVolumeInformationW failed"
    return fs.value


@pytest.mark.skipif(sys.platform != "win32", reason="Requires actual Windows TerminateProcess and NTFS")
@pytest.mark.parametrize("phase", ["kill-before", "kill-after"])
def test_sqlcipher_ntfs_kill_restart_derived_archive_integrity(tmp_path, phase):
    assert _volume_fs(tmp_path) == "NTFS", "Not a native Windows NTFS volume"
    db = tmp_path / "t2-encrypted-vault.db"
    root = tmp_path / "private-t2-archives"
    root.mkdir(parents=True, exist_ok=True)
    # Independent OS file-control: distinguish generic NTFS temp cleanup from
    # product-specific PDF/journal behavior after TerminateProcess.
    with (root / ".native-test-control").open("wb") as stream:
        stream.write(b"T2-NTFS-CONTROL")
        stream.flush()
        os.fsync(stream.fileno())
    marker = tmp_path / "child-reached-window"
    key = secrets.token_hex(32)  # Synthetic only; never print or upload actual secret
    env = {
        **os.environ,
        "P2TER_NATIVE_SQLCIPHER_TEST_KEY": key,
        "DATABASE_URL": "sqlite:///:memory:",
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "TELEMETRY_ENABLED": "false",
        "CLOUD_AI_ENABLED": "false",
        "CABINET_MASTER_KEY_HEX": "00" * 32,
        "MEDIA_ROOT": str(tmp_path / "unused-media"),
    }

    _run_child(phase, db, root, marker, env, kill=True)
    # Remove *only* the explicitly test-owned probe files from the fixture
    # before the single-official-PDF accounting assertions. The official PDF
    # and its pending recovery journal are never touched by this cleanup.
    for probe in (
        root / str(PATIENT_ID) / "RAPPORT_CEPHALO",
        root / ".cephalo-pending" / str(PATIENT_ID) / str(ANALYSIS_ID),
    ):
        if probe.exists():
            for name in (".native-matched.pdf", ".native-matched.json"):
                # PDF is nested by year/month; cleanup happens below.
                (probe / name).unlink(missing_ok=True)
    for probe in root.rglob(".native-matched.pdf"):
        probe.unlink()
    for probe in root.rglob(".native-matched.json"):
        probe.unlink()

    # A new independent interpreter (not the parent session) must see
    # encrypted SQLCipher data before the restart/retry.
    engine = _make_engine(db, key)
    try:
        _check_encrypted(engine, db)
        existing = _rows(engine)
    finally:
        engine.dispose()
    pdfs = list(root.rglob("*.pdf"))
    assert len(pdfs) == 1, (
        "Archive vanished between TerminateProcess and SQLCipher reopen: "
        f"root_exists={root.exists()} "
        f"root_entries={[p.name for p in root.iterdir()] if root.exists() else []}"
    )
    assert (root / ".native-test-control").read_bytes() == b"T2-NTFS-CONTROL"
    assert pdfs[0].read_bytes() == PDF
    assert _journal(root).is_file()
    assert json.loads(_journal(root).read_text(encoding="utf-8"))["sha256"] == hashlib.sha256(PDF).hexdigest()

    if phase == "kill-before":
        assert not existing, "A SQL row survived an uncommitted TerminateProcess"
        _run_child("retry", db, root, marker, env, kill=False)
    else:
        assert len(existing) == 1, "Committed SQL row lost before journal cleanup"
        _run_child("replay", db, root, marker, env, kill=False)

    engine = _make_engine(db, key)
    try:
        _check_encrypted(engine, db)
        current = _rows(engine)
    finally:
        engine.dispose()
    assert len(current) == 1, current
    db_path, db_sha, db_size, clinical = current[0]
    assert clinical["cephalo_analysis_id"] == ANALYSIS_ID
    assert clinical["cephalo_analysis_revision"] == REVISION
    assert clinical["cephalo_archive_payload_digest"] == DIGEST
    referenced = root / db_path.removeprefix("static/archives/")
    assert db_path.startswith("static/archives/")
    assert referenced.is_file()
    assert referenced.read_bytes() == PDF
    assert db_size == len(PDF) and db_sha == hashlib.sha256(PDF).hexdigest()
    assert set(root.rglob("*.pdf")) == {referenced}, "Orphan/duplicate PDF after native restart"
    assert not _journal(root).exists(), "Pending intent persisted after safe recovery"
    print("P2TER_WINDOWS_SQLCIPHER_NTFS_TERMINATEPROCESS_PASS", phase,
          "sql_rows=1 pdf_count=1 pending=0 plaintext_read=denied")



# Independent native-Windows negative control: no import or use of the cabinet
# archive service, SQLCipher, SQLAlchemy, journaling code or production backend.
# Identical file names and creation APIs must survive the same TerminateProcess.
_RAW_WINDOWS_BASELINE_CHILD = r"""
import os
import sys
import time
from pathlib import Path
root, marker = map(Path, sys.argv[1:3])
pdf = root / "97531" / "RAPPORT_CEPHALO" / "2026" / "10" / "ceph-t2-windows-native.pdf"
journal = root / ".cephalo-pending" / "97531" / "86420" / "7.json"
pdf.parent.mkdir(parents=True, exist_ok=True)
journal.parent.mkdir(parents=True, exist_ok=True)
with pdf.open("xb") as stream:
    stream.write(b"%PDF-1.4\n% T2 only\n%%EOF\n")
    stream.flush()
    os.fsync(stream.fileno())
fd = os.open(journal, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
with os.fdopen(fd, "wb") as stream:
    stream.write(b'{"test_only":true}\n')
    stream.flush()
    os.fsync(stream.fileno())
with marker.open("wb") as stream:
    stream.write(b"BASELINE_READY")
    stream.flush()
    os.fsync(stream.fileno())
while True:
    time.sleep(2)
"""


@pytest.mark.skipif(sys.platform != "win32", reason="Requires actual Windows native NTFS")
def test_windows_plain_python_same_paths_survive_real_terminateprocess(tmp_path):
    """If this fails, the raw Windows runner itself can delete these files."""
    assert _volume_fs(tmp_path) == "NTFS"
    root = tmp_path / "private-t2-archives"
    marker = tmp_path / "plain-baseline-marker"
    pdf = root / str(PATIENT_ID) / "RAPPORT_CEPHALO" / "2026" / "10" / FILENAME
    journal = _journal(root)
    child = subprocess.Popen(
        [sys.executable, "-c", _RAW_WINDOWS_BASELINE_CHILD, str(root), str(marker)],
        cwd=Path(__file__).resolve().parents[2],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        cutoff = time.monotonic() + 30
        while not marker.is_file() and child.poll() is None and time.monotonic() < cutoff:
            time.sleep(0.1)
        if not marker.is_file():
            if child.poll() is None:
                child.kill()
            stdout, stderr = child.communicate(timeout=15)
            raise AssertionError(
                f"Raw native Windows baseline never reached checkpoint; exit={child.returncode} "
                f"stderr={stderr[-1200:]} stdout={stdout[-500:]}"
            )
        assert marker.read_bytes() == b"BASELINE_READY"
        assert pdf.is_file() and journal.is_file()
        assert pdf.read_bytes().startswith(b"%PDF")
        assert journal.read_bytes().startswith(b"{")
        assert child.poll() is None
        child.kill()  # Same Windows TerminateProcess API, no exception/finalizer.
        child.communicate(timeout=15)
        assert child.returncode != 0
        assert pdf.is_file() and journal.is_file(), (
            "RAW_WINDOWS_NATIVE_FILES_DISAPPEARED_AFTER_TERMINATEPROCESS: "
            f"pdf={pdf.is_file()} json={journal.is_file()} "
            f"root_entries={[p.name for p in root.iterdir()]}"
        )
        print("P2TER_WINDOWS_RAW_BASELINE_PASS files=2 after=TerminateProcess")
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=15)


if __name__ == "__main__" and len(sys.argv) >= 6 and sys.argv[1] == "--child":
    _child(*sys.argv[2:6])
