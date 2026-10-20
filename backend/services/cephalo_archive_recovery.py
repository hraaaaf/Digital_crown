"""P2ter++ official cephalometric archive crash journal.

A durable sidecar identifies *only* an uncommitted official PDF for one
(patient, study, scientific revision, client payload). The study SQL writer
lock must be held by the caller across prepare / file / SQL commit. No startup
sweep, broad filesystem deletion, generic-document mutation or clinical logic.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from backend import models


@dataclass(frozen=True)
class PendingOfficialPDF:
    path: Path
    content: bytes
    journal: Path
    newly_written: bool


def _sync_parent(path: Path) -> None:
    """Best-effort directory sync; unsupported directory handles remain an OS limit."""
    # Not all supported filesystems expose directory fsync (notably Windows).
    # Do not branch directly on the host OS outside the portability abstraction.
    try:
        fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        try:
            os.fsync(fd)
        except OSError:
            pass
    finally:
        os.close(fd)


def _journal_path(root: Path, patient_id: int, analysis_id: int, revision: int) -> Path:
    if any(type(value) is not int or value <= 0 for value in (patient_id, analysis_id, revision)):
        raise ValueError("Identité de récupération céphalométrique invalide")
    return root / ".cephalo-pending" / str(patient_id) / str(analysis_id) / f"{revision}.json"


def _safe_target(root: Path, relative: str, patient_id: int) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Journal d'archive : chemin invalide")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or rel.parts[:2] != (str(patient_id), models.DocumentType.RAPPORT_CEPHALO.value):
        raise ValueError("Journal d'archive : destination extérieure au patient/type")
    target = root / rel
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Journal d'archive : traversée de chemin")
    return target


def _write_journal(path: Path, data: dict, *, exclusive: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data_bytes = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if exclusive:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data_bytes)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            # Only a failed in-process journal write is cleaned up here.
            path.unlink(missing_ok=True)
            raise
    else:
        temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
        with open(temporary, "xb") as stream:
            stream.write(data_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    _sync_parent(path.parent)


def prepare_official_pdf(
    db: Session, *, root: Path, proposed_path: Path, patient_id: int,
    analysis_id: int, revision: int, payload_digest: str, content: bytes,
) -> PendingOfficialPDF:
    """Create or recover an *authenticated-by-journal*, uncommitted PDF.

    The caller holds the existing per-study SQL lock. Any mismatching journal,
    unexpected existing row, or modified file fails closed; no deletion.
    """
    if not isinstance(payload_digest, str) or not payload_digest:
        raise ValueError("Empreinte de contexte clinique absente")
    root = root.resolve()
    journal = _journal_path(root, patient_id, analysis_id, revision)
    expected_rel = str(proposed_path.relative_to(root)).replace("\\", "/")
    _safe_target(root, expected_rel, patient_id)
    fresh = {
        "version": 1, "patient_id": patient_id, "analysis_id": analysis_id,
        "revision": revision, "payload_digest": payload_digest,
        "relative_path": expected_rel, "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    if journal.exists():
        if journal.is_symlink():
            raise RuntimeError("Journal de récupération redirigé : refus")
        try:
            record = json.loads(journal.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError("Journal de récupération illisible : intervention requise") from exc
        for field in ("version", "patient_id", "analysis_id", "revision", "payload_digest"):
            if record.get(field) != fresh[field]:
                raise RuntimeError("Journal en conflit avec l'étude/révision : intervention requise")
        target = _safe_target(root, record.get("relative_path"), patient_id)
        relative = record["relative_path"]
        sql_path = "static/archives/" + relative
        referenced = db.query(models.DocumentArchive.id).filter(
            models.DocumentArchive.file_path == sql_path
        ).first()
        if referenced is not None:
            raise RuntimeError("Journal lié à une archive SQL existante : reprise interdite")
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_file():
                raise RuntimeError("Fichier de reprise non régulier : refus")
            saved = target.read_bytes()
            if (
                not saved.startswith(b"%PDF")
                or len(saved) != record.get("size")
                or hashlib.sha256(saved).hexdigest() != record.get("sha256")
            ):
                raise RuntimeError("PDF en attente modifié/incomplet : intervention requise")
            # The same study revision/payload may generate a different timestamp.
            # Preserve and commit the EXACT previously rendered, verified PDF.
            return PendingOfficialPDF(target, saved, journal, False)
        # Journal survived but file did not (crash before file creation).
        # The old expected bytes no longer exist; atomically bind new bytes.
        fresh["relative_path"] = relative
        _write_journal(journal, fresh, exclusive=False)
        target.parent.mkdir(parents=True, exist_ok=True)
    else:
        target = _safe_target(root, expected_rel, patient_id)
        if target.exists() or target.is_symlink():
            raise RuntimeError("Fichier déjà présent sans journal : refus d'écrasement")
        _write_journal(journal, fresh, exclusive=True)

    # Journal is durable before the PDF is created. No silent overwrite.
    with open(target, "xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    _sync_parent(target.parent)
    return PendingOfficialPDF(target, content, journal, True)


def finish_official_pdf(pending: PendingOfficialPDF) -> None:
    """After SQL commit only; stale journal after a crash is recoverable."""
    pending.journal.unlink(missing_ok=True)
    _sync_parent(pending.journal.parent)


def abort_official_pdf(pending: PendingOfficialPDF) -> None:
    """Only clean files created by this failed in-process transaction."""
    if pending.newly_written:
        pending.path.unlink(missing_ok=True)
        pending.journal.unlink(missing_ok=True)
        _sync_parent(pending.path.parent)
        _sync_parent(pending.journal.parent)
