from __future__ import annotations

import os

import pytest

from backend.services.patient_companion_key_protection import (
    OsKeyProtectionUnavailable,
    protect_os_bound,
    unprotect_os_bound,
)


@pytest.mark.skipif(os.name == "nt", reason="non-Windows only")
def test_remote_key_protection_fails_closed_off_windows():
    with pytest.raises(OsKeyProtectionUnavailable):
        protect_os_bound(b"test-key-material")


@pytest.mark.skipif(os.name != "nt", reason="Windows DPAPI certification")
def test_windows_dpapi_remote_key_roundtrip():
    clear = b"Digital Crown remote key test material"
    protected = protect_os_bound(clear)
    assert protected != clear
    assert clear not in protected
    assert unprotect_os_bound(protected) == clear
