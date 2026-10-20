"""P2ter++ / synthetic only: SIGKILL after PDF write and before SQL COMMIT.

This is deliberately a release-gate regression, not a mocked commit exception.
The child does the real ArchiveService filesystem write, flushes its SQL INSERT,
and is SIGKILLed before commit. A completely fresh interpreter then retries.
No clinic DB, media, external runtime, or real patient information is involved.
"""
from __future__ import annotations

import hashlib
import os
import signal
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


_CHILD = r"""
import os
import signal
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend import models
from backend.services import archive_service

mode, db_file, root_dir, cut_marker = sys.argv[1:]
archive_root = Path(root_dir)
archive_service.ARCHIVE_BASE_DIR = archive_root
engine = create_engine("sqlite:///" + db_file, connect_args={"timeout": 10})
models.DocumentArchive.__table__.create(engine, checkfirst=True)
session = Session(engine)

if mode == "crash":
    def kill_after_sql_flush():
        # SQL was written into an *uncommitted* transaction: SIGKILL means
        # SQL rollback on SQLite reconnect, while PDF bytes remain on disk.
        session.flush()
        marker = Path(cut_marker)
        marker.write_text("PDF_WRITTEN_SQL_FLUSHED_BEFORE_COMMIT", encoding="ascii")
        os.kill(os.getpid(), signal.SIGKILL)

    session.commit = kill_after_sql_flush

archive_service.ArchiveService(session).archive_document(
    patient_id=97531,
    analysis_id=86420,
    file_content=b"%PDF-1.4\\n% T2 ONLY - NO PATIENT DATA\\n%%EOF\\n",
    filename="t2-ceph-crash-recovery.pdf",
    doc_type=models.DocumentType.RAPPORT_CEPHALO,
    clinical_data={
        "cephalo_analysis_id": 86420,
        "cephalo_analysis_revision": 1,
        "cephalo_archive_payload_digest": "synthetic",
    },
)
session.close()
engine.dispose()
"""


@pytest.mark.skipif(sys.platform != "linux", reason="SIGKILL process semantics tested on Linux CI")
def test_real_sigkill_restart_leaves_no_unindexed_official_pdf(tmp_path):
    """Crash + restart/retry must not strand patient-class PDF bytes outside SQL."""
    db_path = tmp_path / "synthetic-recovery.sqlite"
    archive_root = tmp_path / "isolated-archives"
    cut_marker = tmp_path / "cut-marker"
    repo_root = Path(__file__).resolve().parents[2]
    environment = {
        **os.environ,
        "DATABASE_URL": "sqlite:///:memory:",
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "TELEMETRY_ENABLED": "false",
        "CLOUD_AI_ENABLED": "false",
        "CABINET_MASTER_KEY_HEX": "00" * 32,
    }

    def invoke(mode):
        return subprocess.run(
            [
                sys.executable, "-c", _CHILD,
                mode, str(db_path), str(archive_root), str(cut_marker),
            ],
            cwd=repo_root, env=environment,
            capture_output=True, text=True, timeout=90, check=False,
        )

    cut = invoke("crash")
    assert cut.returncode == -signal.SIGKILL, (
        f"Crash injection did not reach SIGKILL: code={cut.returncode} "
        f"stdout={cut.stdout[-800:]} stderr={cut.stderr[-1500:]}"
    )
    assert cut_marker.read_text(encoding="ascii") == "PDF_WRITTEN_SQL_FLUSHED_BEFORE_COMMIT"

    from backend import models

    table = models.DocumentArchive.__tablename__

    def sql_rows():
        with sqlite3.connect(db_path) as conn:
            return conn.execute(f"SELECT file_path, file_hash FROM {table}").fetchall()

    # Verify the actual SQLite recovery outcome after a fresh open, not the
    # in-process SQLAlchemy session that was killed.
    assert sql_rows() == [], "Uncommitted official archive row survived SIGKILL"
    disk_before = list(archive_root.rglob("*.pdf"))
    assert len(disk_before) == 1, "Crash window was not reached after PDF write"
    assert disk_before[0].read_bytes().startswith(b"%PDF")

    restarted = invoke("restart")
    assert restarted.returncode == 0, (
        f"Restart/retry failed: stdout={restarted.stdout[-800:]} "
        f"stderr={restarted.stderr[-1500:]}"
    )
    rows = sql_rows()
    assert len(rows) == 1, f"Expected one official SQL archive after retry; got {rows!r}"
    disk_after = set(archive_root.rglob("*.pdf"))
    referenced = {
        archive_root / path.removeprefix("static/archives/")
        for path, _ in rows
    }
    assert referenced <= disk_after, "SQL references an absent PDF"
    for path, sha256 in rows:
        actual = (archive_root / path.removeprefix("static/archives/")).read_bytes()
        assert hashlib.sha256(actual).hexdigest() == sha256

    # Successful recovery must close its private pending-journal entry.
    assert not list((archive_root / ".cephalo-pending").rglob("*.json"))
    orphans = disk_after - referenced
    assert not orphans, (
        "CRASH RECOVERY BLOCKER: post-SIGKILL restart/retry left unindexed "
        f"official PDF(s) on disk: {len(orphans)} orphan(s), "
        f"{len(rows)} committed SQL row(s), {len(disk_after)} PDF(s). "
        "SQL exception cleanup tests do not cover this process-death window."
    )



def test_verified_pending_pdf_reused_despite_second_render_timestamp(tmp_path):
    """An aborted transaction must adopt its hash-verified original, not a fresh draft."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend import models
    from backend.services.cephalo_archive_recovery import (
        finish_official_pdf, prepare_official_pdf,
    )

    root = tmp_path / "archives"
    proposed = root / "97531" / models.DocumentType.RAPPORT_CEPHALO.value / "2026" / "10" / "first.pdf"
    proposed.parent.mkdir(parents=True)
    second = proposed.with_name("second-timestamp.pdf")
    engine = create_engine(f"sqlite:///{tmp_path / 'recovery.db'}")
    models.DocumentArchive.__table__.create(engine)
    first = b"%PDF-1.4\nORIGINAL-T2\n"
    fresh = b"%PDF-1.4\nDIFFERENT-TIMESTAMP-T2\n"
    try:
        with Session(engine) as db:
            pending = prepare_official_pdf(
                db, root=root, proposed_path=proposed, patient_id=97531,
                analysis_id=86420, revision=2, payload_digest="t2-digest",
                content=first,
            )
            assert pending.newly_written is True
            db.rollback()
        with Session(engine) as db:
            resumed = prepare_official_pdf(
                db, root=root, proposed_path=second, patient_id=97531,
                analysis_id=86420, revision=2, payload_digest="t2-digest",
                content=fresh,
            )
            assert resumed.newly_written is False
            assert resumed.path == proposed
            assert resumed.content == first
            assert not second.exists()
            finish_official_pdf(resumed)
        assert not list((root / ".cephalo-pending").rglob("*.json"))
    finally:
        engine.dispose()


def test_tampered_or_wrong_identity_pending_journal_refuses_without_deletion(tmp_path):
    """A journal alone is never authority to overwrite or trust mismatched bytes."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend import models
    from backend.services.cephalo_archive_recovery import prepare_official_pdf

    root = tmp_path / "archives"
    proposed = root / "97531" / models.DocumentType.RAPPORT_CEPHALO.value / "2026" / "10" / "pending.pdf"
    proposed.parent.mkdir(parents=True)
    engine = create_engine(f"sqlite:///{tmp_path / 'tampered.db'}")
    models.DocumentArchive.__table__.create(engine)
    try:
        with Session(engine) as db:
            prepare_official_pdf(
                db, root=root, proposed_path=proposed, patient_id=97531,
                analysis_id=86420, revision=1, payload_digest="original",
                content=b"%PDF-1.4 T2-VERIFIED",
            )
            db.rollback()
            with pytest.raises(RuntimeError, match="conflit"):
                prepare_official_pdf(
                    db, root=root, proposed_path=proposed, patient_id=97531,
                    analysis_id=86420, revision=1, payload_digest="OTHER",
                    content=b"%PDF-1.4 T2-VERIFIED",
                )
            assert proposed.read_bytes() == b"%PDF-1.4 T2-VERIFIED"
            proposed.write_bytes(b"%PDF-1.4 altered")
            with pytest.raises(RuntimeError, match="modifié/incomplet"):
                prepare_official_pdf(
                    db, root=root, proposed_path=proposed, patient_id=97531,
                    analysis_id=86420, revision=1, payload_digest="original",
                    content=b"%PDF-1.4 T2-VERIFIED",
                )
            assert proposed.read_bytes() == b"%PDF-1.4 altered"
    finally:
        engine.dispose()


def test_pending_journal_without_pdf_recovers_with_new_verified_bytes(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend import models
    from backend.services.cephalo_archive_recovery import prepare_official_pdf

    root = tmp_path / "archives"
    proposed = root / "97531" / models.DocumentType.RAPPORT_CEPHALO.value / "2026" / "10" / "old.pdf"
    proposed.parent.mkdir(parents=True)
    engine = create_engine(f"sqlite:///{tmp_path / 'missing.db'}")
    models.DocumentArchive.__table__.create(engine)
    try:
        with Session(engine) as db:
            pending = prepare_official_pdf(
                db, root=root, proposed_path=proposed, patient_id=97531,
                analysis_id=86420, revision=1, payload_digest="original",
                content=b"%PDF-1.4 T2-OLD",
            )
            pending.path.unlink()
            recovered = prepare_official_pdf(
                db, root=root, proposed_path=proposed.with_name("new.pdf"),
                patient_id=97531, analysis_id=86420, revision=1,
                payload_digest="original", content=b"%PDF-1.4 T2-NEW",
            )
            assert recovered.newly_written is True
            assert recovered.path == proposed
            assert recovered.content == b"%PDF-1.4 T2-NEW"
            assert list(root.rglob("*.pdf")) == [proposed]
    finally:
        engine.dispose()
