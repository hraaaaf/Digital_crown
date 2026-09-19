from __future__ import annotations

import json
import sys

import pytest

from backend.services.windows_dpapi import protect_for_current_user, unprotect_for_current_user


@pytest.mark.skipif(sys.platform != "win32", reason="Windows DPAPI certification")
def test_windows_dpapi_current_user_roundtrip_and_tamper_rejection():
    clear = b'{"private":"cabinet-key-material"}'
    protected = protect_for_current_user(clear)
    assert protected != clear
    assert b"cabinet-key-material" not in protected
    assert unprotect_for_current_user(protected) == clear

    damaged = bytearray(protected)
    damaged[len(damaged) // 2] ^= 0x01
    with pytest.raises(OSError):
        unprotect_for_current_user(bytes(damaged))


def test_dpapi_source_does_not_use_local_machine_scope():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "services" / "windows_dpapi.py").read_text(encoding="utf-8")
    assert "CRYPTPROTECT_LOCAL_MACHINE" not in source
    assert "CRYPTPROTECT_UI_FORBIDDEN" in source
