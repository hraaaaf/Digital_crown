"""Collision-resistant PDF destination for local, on-premise document generation.

Legacy generators used a patient name and a second-resolution timestamp,
which could silently overwrite a different document in the same second.
Create a fresh output file *exclusively* before a ReportLab renderer opens it:
the OS guarantees we never claim an already-existing filename. The renderer
writes only to this newly reserved path. Interrupted builds may leave an
incomplete owned file, which must be reviewed rather than replayed/deleted.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

_UNSAFE_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def reserve_generated_pdf_path(directory: str | os.PathLike[str], filename: str) -> str:
    """Return an exclusively created PDF path; never reuse an existing file.

    The display-oriented filename stem survives (including its document
    category and timestamp) with a cryptographically random suffix. File
    creation is atomic even under concurrent same-patient generation.
    """
    if not isinstance(filename, str) or not filename.lower().endswith(".pdf"):
        raise ValueError("Nom PDF invalide pour génération locale")
    stem = _UNSAFE_NAME.sub("_", filename[:-4]).strip(" .")
    if not stem:
        raise ValueError("Nom PDF invalide pour génération locale")
    # Preserve the category and timestamp even with long patient names.
    if len(stem) > 185:
        stem = stem[:126] + "_" + stem[-48:]
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix=stem + "_", suffix=".pdf", dir=str(root))
    os.close(fd)
    return path
