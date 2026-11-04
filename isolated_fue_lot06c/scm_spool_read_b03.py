"""LOT06 B03 disposable Windows SCM subprocess: actual HotFolder AES read.

Process must run as LocalService (token of the SCM service), no patient binding.
No product install, no patient data, no key on argv, no API, no media output.
"""
from __future__ import annotations
import base64
import hashlib
import os
from pathlib import Path
import secrets
import sys
import zlib

# -I Python isolated mode prevents PYTHONPATH injection; only repo-owned
# source path is inserted. Not an arbitrary user-writable module directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.imaging_gateway import Config, HotFolder
from tools.imaging_gateway.unassigned_queue_v15 import read_unassigned
from tools.imaging_gateway.native_inventory_protocol_v15 import encode_inventory
from tools.imaging_gateway.native_media_protocol_v15 import (
    NativeInventoryDenied, decode_request, encode_response, DENIED as MEDIA_DENIED,
)

_BASE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)


def _synthetic_multichunk_png() -> bytes:
    """Valid 2×2 synthetic PNG with a safe, uncompressed ancillary text chunk.

    Purpose: exercise 4+ actual Win32 pipe fragments, not a simulated unit
    split. No clinical pixel data, no patient identity or source filesystem.
    """
    assert _BASE_PNG[-8:-4] == b"IEND"
    content = b"Comment\\x00" + b"SYNTHETIC-NOT-PATIENT-" * 310
    label = b"tEXt"
    chunk = (len(content).to_bytes(4, "big") + label + content
             + (zlib.crc32(label + content) & 0xffffffff).to_bytes(4, "big"))
    media = _BASE_PNG[:-12] + chunk + _BASE_PNG[-12:]
    assert 6144 < len(media) <= 16384
    return media


PNG = _synthetic_multichunk_png()

def run(argv: list[str]) -> int:
    if (os.name != "nt" or len(argv) not in (5, 9)
            or argv[0] not in ("seed", "read", "inventory", "media")
            or (argv[0] == "media") != (len(argv) == 9)):
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
        # TEST ONLY: classify Native Win32 root preflight by coarse phase,
        # before opening the actual SQLite and cipher files. Never emit paths.
        from tools.imaging_gateway.windows_scoped_read_lab import directory_identity
        for stage, root in (("W", incoming), ("P", private), ("S", private / "spool")):
            directory_identity(root)
        stage = 3
        collector = HotFolder(cfg)
        stage = 4
        if mode == "inventory":
            # One integrity-checked unassigned capture, no patient/media/filename.
            captures = read_unassigned(collector, limit=1)
            os.write(1, encode_inventory(captures[0] if captures else None))
            return 0
        if mode == "media":
            # Only a real Windows LocalService fixture can open the service
            # SID-protected spool key. No item id accepted without a verified
            # pending AES-GCM spool record with the same SHA-256.
            item, digest, offset, count = decode_request(
                ("M" + "".join(argv[5:9])).encode("ascii")
            )
            captures = read_unassigned(collector, limit=1)
            if not captures or captures[0].id != item or captures[0].digest != digest:
                raise NativeInventoryDenied("NATIVE_MEDIA_NOT_PENDING_OR_MISMATCH")
            capture = captures[0]
            if capture.size > 16384 or offset + count > capture.size:
                raise NativeInventoryDenied("NATIVE_MEDIA_LAB_LIMIT_DENIED")
            plaintext = collector.read_verified(item)
            if (len(plaintext) != capture.size
                    or hashlib.sha256(plaintext).hexdigest() != digest
                    or read_unassigned(collector, limit=1)[0] != capture):
                raise NativeInventoryDenied("NATIVE_MEDIA_CHANGED_DURING_READ")
            os.write(1, encode_response(plaintext[offset:offset + count]))
            return 0
        captures = read_unassigned(collector, limit=9)
        if len(captures) > 9:
            return 5
        # Existing two-byte count response, no patient/filename/media.
        os.write(1, b"S" + str(len(captures)).encode("ascii"))
        return 0
    except OSError as error:
        # LAB-only two-byte allowlisted code: A-D = Win32 ERROR_ACCESS_DENIED(5),
        # E-H = ERROR_SHARING_VIOLATION(32), I-L = PATH_NOT_FOUND(3),
        # M-P = FILE_NOT_FOUND(2), Z = other. Each group is
        # watch/private/spool/inside HotFolder respectively. No native error
        # string, path, key, filename or captured data is returned.
        phases = {"W": 0, "P": 1, "S": 2, 3: 3}
        errno = error.args[0] if error.args and type(error.args[0]) is int else None
        group = {5: 0, 32: 1, 3: 2, 2: 3}.get(errno)
        if group is not None and stage in phases:
            category = chr(ord("A") + group * 4 + phases[stage])
        elif stage == 3:
            # OSError("static code") from the native handle-relative boundary
            # has no numeric errno. Match ONLY exact audited constant strings.
            # Never relay exception text, NTSTATUS, path or filename to IPC.
            constants = {
                "IMAGING_WINDOWS_RELATIVE_OPEN_DENIED": "N",
                "IMAGING_WINDOWS_FILE_ID_FAILED": "I",
                "IMAGING_WINDOWS_REPARSE_ROOT_REJECTED": "R",
                "IMAGING_WINDOWS_WATCH_ID_CHANGED": "Q",
                "IMAGING_WINDOWS_ROOT_OPEN_FAILED": "O",
                "IMAGING_INVALID_RELATIVE_LEAF": "L",
            }
            marker = error.args[0] if error.args and type(error.args[0]) is str else None
            category = constants.get(marker, "Z")
        else:
            category = "Z"
        if mode == "media":
            os.write(1, MEDIA_DENIED)
        elif mode in ("read", "inventory"):
            os.write(1, ("E" + category).encode("ascii"))
        return 5
    except Exception:
        if mode == "media": os.write(1, MEDIA_DENIED)
        elif mode in ("read", "inventory"): os.write(1, b"E2")
        return 5

if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
