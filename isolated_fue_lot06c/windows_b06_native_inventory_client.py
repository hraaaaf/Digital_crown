"""B06 Windows native inventory FUE run AS a separate real Windows account.

Only opaque metadata from SCM restricted-SID pipe. No patient/media bytes or
clinical activation. All user-visible markers are fixed non-PHI strings.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.imaging_gateway.native_inventory_windows_v15 import read_native_unassigned
from tools.imaging_gateway.native_inventory_protocol_v15 import NativeInventoryDenied
from isolated_fue_lot06c.scm_spool_read_b03 import PNG


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"Valid", "Tampered", "WrongKey", "Unauthorized"}:
        return 64
    pipe, expected = argv
    try:
        capture = read_native_unassigned(pipe)
    except NativeInventoryDenied:
        if expected == "Valid":
            return 65
        print("DC06_B06_NATIVE_INVENTORY_" + expected.upper() + "_DENIED_PASS")
        return 0
    if expected != "Valid" or capture is None:
        return 66
    if (capture.size != len(PNG)
            or capture.digest != hashlib.sha256(PNG).hexdigest()
            or capture.mime != "image/png"
            or capture.category != "PHOTO"
            or capture.id <= 0
            or set(vars(capture)) != {"id", "digest", "size", "mime", "category"}):
        return 67
    print("DC06_B06_NATIVE_ONE_CAPTURE_VERIFIED_NON_PATIENT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
