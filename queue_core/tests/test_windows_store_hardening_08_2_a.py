"""08.2-A SEC: no privileged filesystem mutations; mocks target temp paths."""
from __future__ import annotations

from pathlib import Path
import os
import stat
from types import SimpleNamespace

import pytest

from queue_core.security import windows_cli
from queue_core.security.windows_console import LocalConsoleRequired


def test_dangling_reparse_point_is_rejected_even_when_exists_is_false(monkeypatch, tmp_path):
    link = tmp_path / "dangling"
    monkeypatch.setattr(Path, "lstat", lambda _self: SimpleNamespace(
        st_mode=stat.S_IFLNK, st_file_attributes=0x400
    ))
    monkeypatch.setattr(Path, "exists", lambda _self: False)
    with pytest.raises(LocalConsoleRequired, match="REPARSE_POINT_FORBIDDEN"):
        windows_cli._no_reparse(link)


def test_trusted_sddl_owner_and_required_aces_are_explicit():
    assert windows_cli._DIR_SDDL.startswith("O:BA")
    assert windows_cli._FILE_SDDL.startswith("O:BA")
    for item in (windows_cli._DIR_SDDL, windows_cli._FILE_SDDL):
        assert "D:P" in item and ";;;SY)" in item and ";;;BA)" in item


def test_acl_template_checks_owner_and_distinct_required_identities(monkeypatch, tmp_path):
    captured = []
    monkeypatch.setattr(windows_cli, "_ps", captured.append)
    windows_cli._verify_acl(tmp_path, allow_inherited=False)
    assert len(captured) == 1
    script = captured[0]
    assert "Untrusted owner" in script
    assert "Missing required identity" in script
    assert "$seen -contains $sid" in script
    assert "S-1-5-18" in script and "S-1-5-32-544" in script


@pytest.mark.skipif(os.name != "nt", reason="Windows ACL semantics")
def test_untrusted_temp_directory_owner_acl_is_rejected(tmp_path):
    # This test only READS ACL on pytest temporary directory; no Set-Acl.
    with pytest.raises(LocalConsoleRequired, match="AUTH_STORE_ACL_UNVERIFIED"):
        windows_cli._verify_acl(tmp_path)


def test_existing_insecure_directory_is_never_repaired_automatically(monkeypatch, tmp_path):
    def never_create(*_args, **_kwargs):
        pytest.fail("Do not replace ACL silently on pre-existing directory")

    monkeypatch.setattr(windows_cli, "_secure_win32_create", never_create)
    monkeypatch.setattr(windows_cli, "_verify_acl",
                        lambda *_args, **_kwargs: (_ for _ in ()).throw(
                            LocalConsoleRequired("AUTH_STORE_ACL_UNVERIFIED")
                        ))
    with pytest.raises(LocalConsoleRequired, match="AUTH_STORE_ACL_UNVERIFIED"):
        windows_cli._create_private_dir(tmp_path)


def test_private_store_creation_calls_secure_win32_creation_for_both_objects(
    monkeypatch, tmp_path,
):
    created = []

    def fake_secure_create(path, *, directory):
        created.append((Path(path).name, directory))
        if directory:
            Path(path).mkdir()
        else:
            Path(path).touch()

    monkeypatch.setattr(windows_cli, "require_local_windows_admin_console", lambda: None)
    monkeypatch.setattr(windows_cli, "_programdata", lambda: tmp_path)
    monkeypatch.setattr(windows_cli, "_secure_win32_create", fake_secure_create)
    monkeypatch.setattr(windows_cli, "_verify_acl", lambda *_args, **_kwargs: None)
    db = windows_cli._database_path(initialize=True)
    assert db.is_file()
    assert created == [
        ("DigitalCrownQueueCore", True), ("local_auth.sqlite", False)
    ]


def test_console_required_fails_closed_in_redirected_context(monkeypatch):
    from queue_core.security import windows_console
    monkeypatch.setattr(windows_console.sys.stdin, "isatty", lambda: False)
    with pytest.raises(LocalConsoleRequired, match="INTERACTIVE_CONSOLE_REQUIRED"):
        windows_console.require_local_windows_admin_console()



@pytest.mark.skipif(os.name != "nt", reason="Win32 security descriptors")
def test_windows_sddl_security_descriptors_parse_without_mutating_system():
    import ctypes
    from ctypes import wintypes

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    parse = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
    parse.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD),
    ]
    parse.restype = wintypes.BOOL
    free = kernel.LocalFree
    free.argtypes = [ctypes.c_void_p]
    free.restype = ctypes.c_void_p
    for candidate in (windows_cli._DIR_SDDL, windows_cli._FILE_SDDL):
        ptr = ctypes.c_void_p()
        length = wintypes.DWORD()
        try:
            assert parse(candidate, 1, ctypes.byref(ptr), ctypes.byref(length))
            assert ptr.value is not None and length.value > 0
        finally:
            if ptr.value:
                free(ptr)



@pytest.mark.skipif(os.name != "nt", reason="Windows PowerShell static parser")
def test_powershell_acl_verifier_template_parses_without_execution(monkeypatch, tmp_path):
    import base64
    import subprocess

    scripts = []
    monkeypatch.setattr(windows_cli, "_ps", scripts.append)
    windows_cli._verify_acl(tmp_path)
    assert len(scripts) == 1
    body = base64.b64encode(scripts[0].encode("utf-16-le")).decode("ascii")
    parser = (
        "$s=[Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('"
        + body
        + "'));$tk=$null;$err=$null;"
        "[System.Management.Automation.Language.Parser]::ParseInput($s,[ref]$tk,[ref]$err)|Out-Null;"
        "if($err.Count){$err | ForEach-Object {Write-Output $_.Message};exit 7};Write-Output 'PARSE_OK'"
    )
    encoded = base64.b64encode(parser.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0
    assert "PARSE_OK" in result.stdout
