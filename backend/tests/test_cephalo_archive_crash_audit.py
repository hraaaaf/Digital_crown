"""Operator-only crash recovery audit: real process kill, no automatic media mutation."""
from datetime import datetime
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest
from sqlalchemy.exc import OperationalError

from backend import models
from backend.services.archive_service import audit_cephalo_archive_after_crash

DATE = ("2026", "10")


def _make_path(root: Path, patient_id=17, name="synthetic-case.pdf") -> Path:
    folder = root / str(patient_id) / "RAPPORT_CEPHALO" / DATE[0] / DATE[1]
    folder.mkdir(parents=True, exist_ok=True)
    return folder / name


def test_real_sigkill_after_disk_sync_is_detected_read_only(db, tmp_path):
    """Killed writer may leave bytes absent from SQL; audit must find and preserve."""
    root = tmp_path / "archives"
    target = _make_path(root)
    program = (
        "import os, signal, sys\n"
        "with open(sys.argv[1], 'xb') as out:\n"
        "    out.write(b'%PDF-1.4\\nSYNTHETIC CRASH FIXTURE\\n')\n"
        "    out.flush()\n"
        "    os.fsync(out.fileno())\n"
        "os.kill(os.getpid(), signal.SIGKILL)\n"
    )
    result = subprocess.run([sys.executable, "-c", program, str(target)],
                            check=False, capture_output=True, timeout=15)
    assert result.returncode == -signal.SIGKILL, result.stderr.decode(errors="replace")[:200]
    expected=target.read_bytes()
    past=time.time()-7200
    os.utime(target, (past, past))

    report=audit_cephalo_archive_after_crash(db, archive_root=root, minimum_age_seconds=3600)
    assert report["mode"] == "READ_ONLY"
    assert report["automatic_deletions"] == 0
    assert report["suspected_count"] == 1
    assert report["suspected_orphans"][0]["relative_path"].endswith("synthetic-case.pdf")
    assert report["suspected_orphans"][0]["bytes"] == len(expected)
    assert len(report["suspected_orphans"][0]["sha256"]) == 64
    assert target.read_bytes() == expected
    # Rerun is idempotent; the audit never moves or removes evidence.
    again=audit_cephalo_archive_after_crash(db, archive_root=root, minimum_age_seconds=3600)
    assert again == report


def test_recent_uncommitted_pdf_is_not_prematurely_classified(db, tmp_path):
    root = tmp_path / "archives"
    target = _make_path(root)
    target.write_bytes(b"%PDF-1.4\nNEW_SYNTHETIC\n")
    report=audit_cephalo_archive_after_crash(db, archive_root=root)
    assert report["suspected_count"] == 0
    assert target.is_file()


def test_committed_pdf_is_not_orphan_and_unknown_non_ceph_files_preserved(db, dentiste, tmp_path):
    root = tmp_path / "archives"
    patient=models.Patient(
        nom="SYNTHETIQUE", prenom="Audit", date_naissance=datetime(1990,1,1),
        sexe="M", employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    target=_make_path(root,patient_id=patient.id)
    target.write_bytes(b"%PDF-1.4\nPERSISTED\n")
    other=_make_path(root,patient_id=patient.id,name="offscope.txt")
    other.write_text("untouched")
    now=time.time()-7200
    os.utime(target,(now,now))
    db.add(models.DocumentArchive(
        patient_id=patient.id,
        uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.RAPPORT_CEPHALO,
        filename=target.name,
        original_filename=target.name,
        document_group_id="synthetic-committed-group",
        file_hash="dummy-synthetic-sha",
        file_size=target.stat().st_size,
        file_path="static/archives/"+target.relative_to(root).as_posix(),
    ))
    db.commit()
    data=audit_cephalo_archive_after_crash(db,archive_root=root)
    assert data["suspected_count"] == 0
    assert data["missing_referenced_count"] == 0
    assert target.read_bytes().startswith(b"%PDF")
    assert other.read_text() == "untouched"


def test_missing_db_cannot_be_mistaken_for_unreferenced_files(tmp_path):
    root=tmp_path/"archives"
    _make_path(root).write_bytes(b"%PDF")
    class Disconnected:
        rollback_called=False
        def query(self,*_):
            raise OperationalError("SELECT", {}, Exception("synthetic DB outage"))
        def rollback(self):
            self.rollback_called=True
    db=Disconnected()
    with pytest.raises(OperationalError):
        audit_cephalo_archive_after_crash(db,archive_root=root,minimum_age_seconds=1)
    assert db.rollback_called
    assert (root/"17/RAPPORT_CEPHALO/2026/10/synthetic-case.pdf").exists()


def test_missing_committed_pdf_and_symlink_are_flagged_without_mutation(db, dentiste, tmp_path):
    """Disaster recovery must also spot SQL rows whose referenced media vanished."""
    root = tmp_path / "archives"
    patient = models.Patient(
        nom="SYNTHETIQUE", prenom="Missing", date_naissance=datetime(1990, 1, 1),
        sexe="M", employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    missing = _make_path(root, patient_id=patient.id, name="missing-synthetic.pdf")
    symlink = _make_path(root, patient_id=patient.id, name="linked-synthetic.pdf")
    outside = tmp_path / "outside-synthetic.pdf"
    outside.write_bytes(b"%PDF-1.4\\nOUTSIDE_NEVER_READ\\n")
    symlink.symlink_to(outside)
    before = outside.read_bytes()
    for i, file_path in enumerate((
        "static/archives/" + missing.relative_to(root).as_posix(),
        "static/archives/" + symlink.relative_to(root).as_posix(),
        "static/documents/legacy-synthetic.pdf",
        "static/archives/999/RAPPORT_CEPHALO/2026/10/wrong-patient.pdf",
    )):
        db.add(models.DocumentArchive(
            patient_id=patient.id,
            uploaded_by_id=dentiste.id,
            document_type=models.DocumentType.RAPPORT_CEPHALO,
            filename=f"synthetic-{i}.pdf",
            original_filename=f"synthetic-{i}.pdf",
            document_group_id=f"synthetic-missing-group-{i}",
            file_hash=f"synthetic-sha-{i}",
            file_size=24,
            file_path=file_path,
        ))
    db.commit()
    report = audit_cephalo_archive_after_crash(db, archive_root=root, minimum_age_seconds=1)
    assert report["mode"] == "READ_ONLY"
    assert report["automatic_deletions"] == 0
    assert report["suspected_count"] == 0
    assert report["missing_referenced_count"] == 2
    assert {item["reason"] for item in report["missing_referenced"]} == {"missing", "symlink"}
    assert report["unverifiable_references_count"] == 2  # legacy + wrong patient path
    assert not missing.exists()
    assert symlink.is_symlink()
    assert outside.read_bytes() == before
