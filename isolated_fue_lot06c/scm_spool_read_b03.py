"""LOT06 B03 disposable Windows SCM subprocess: actual HotFolder AES read.

Process must run as LocalService (token of the SCM service), no patient binding.
No product install, no patient data, no key on argv, no API, no media output.
"""
from __future__ import annotations
import base64
import os
from pathlib import Path
import secrets
import sys

# -I Python isolated mode prevents PYTHONPATH injection; only repo-owned
# source path is inserted. Not an arbitrary user-writable module directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.imaging_gateway import Config, HotFolder
from tools.imaging_gateway.unassigned_queue_v15 import read_unassigned

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)

def run(argv: list[str]) -> int:
    if os.name != "nt" or len(argv) != 5 or argv[0] not in ("seed", "read"):
        return 4
    mode, incoming, private, keyfile = argv[0], Path(argv[1]), Path(argv[2]), Path(argv[3])
    # Fourth user arg reserved, fixed for LAB only; never configurable tenant.
    if argv[4] != "DC06B03_SYNTHETIC_ONLY":
        return 4
    if "DC06R-LAB-" not in str(private):
        return 4
    stage = 1  # 1 key-open, 2 Config, 3 HotFolder, 4 verify queue
    try:
        key = keyfile.read_bytes()
        if len(key) != 32 or not incoming.is_dir() or not private.is_dir():
            raise ValueError("BAD_LAB_KEY_OR_PATH")
        stage = 2
        cfg = Config(
            cabinet="DC06B03CAB", workstation="DC06B03WS",
            watch=incoming, private=private, key=key, category="PHOTO",
        )
        if mode == "seed":
            source = incoming / "synthetic-no-patient.png"
            source.write_bytes(PNG)
            collector = HotFolder(cfg)
            assert collector.scan_once()["unstable"] == 1
            assert collector.scan_once()["staged"] == 1
            assert len(read_unassigned(collector)) == 1
            return 0
        # Reopen the real SQLite DB, then decrypt and validate the actual
        # spool ciphertext and media. Full validation fails closed on tamper.
        stage = 3
        collector = HotFolder(cfg)
        stage = 4
        captures = read_unassigned(collector, limit=9)
        if len(captures) > 9:
            return 5
        # Fixed two-byte ASCII response, no patient/filename/digest/media.
        os.write(1, b"S" + str(len(captures)).encode("ascii"))
        return 0
    except OSError as error:
        # B03 LAB only: encode fixed call-site families, never path/exception,
        # OS errno, patient, ciphertext, key or traceback in IPC output.
        category = str(stage)
        if stage == 3:
            trace = error.__traceback__
            seen = set()
            while trace is not None:
                seen.add(trace.tb_frame.f_code.co_name)
                trace = trace.tb_next
            for name, code in (
                ("_open_root", "R"),
                ("open_relative_read", "L"),
                ("_seal_continuity_marker", "M"),
                ("directory_identity", "I"),
                ("_directory_identity", "D"),
                ("_decrypt", "C"),
            ):
                if name in seen:
                    category = code
                    break
            else:
                category = "Z"
        if mode == "read": os.write(1, ("E" + category).encode("ascii"))
        return 5
    except Exception:
        if mode == "read": os.write(1, b"E2")
        return 5

if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
