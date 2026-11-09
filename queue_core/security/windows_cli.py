"""Offline first-admin Windows CLI for an isolated Queue Core auth store.

No --db parameter or network endpoints. Only a physically local elevated
server console may create the initial administrator or rotate the offline
recovery secret. Directory and initial DB file are created with protected
Windows security descriptors atomically; existing objects are verified and
NEVER silently re-ACL'd if ownership or grants are not trusted.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import getpass
import os
from pathlib import Path
import stat
import subprocess
import sys

from .local_auth import LocalIdentityError, LocalIdentityStore
from .windows_console import (
    LocalConsoleRequired, require_local_windows_admin_console,
)

_SYSTEM = "S-1-5-18"
_ADMINS = "S-1-5-32-544"
# Owner=BUILTIN Administrators, Group=BUILTIN Administrators, protected DACL.
_DIR_SDDL = "O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)"
_FILE_SDDL = "O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)"


def _programdata() -> Path:
    """HKLM-controlled Common AppData, never a caller-modifiable env var."""
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    ) as key:
        folder, _ = winreg.QueryValueEx(key, "Common AppData")
    return Path(folder)


def _no_reparse(path: Path) -> None:
    """lstat, NOT exists(): dangling symlinks and junctions must be detected."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if (stat.S_ISLNK(info.st_mode)
            or getattr(info, "st_file_attributes", 0) & 0x400):
        raise LocalConsoleRequired("REPARSE_POINT_FORBIDDEN")


def _secure_win32_create(path: Path, *, directory: bool) -> None:
    """Atomic CreateDirectoryW/CreateFileW with explicit owner + protected DACL.

    The directory/file must not be created first with inheritable broad ACLs.
    Reparse-point following is disabled for opening/creating the file. A
    collision (including pre-existing objects) is verified separately and
    rejected unless it has the exact trusted security boundary.
    """
    if os.name != "nt":
        raise LocalConsoleRequired("WINDOWS_REQUIRED")
    from ctypes import wintypes

    class SecurityAttributes(ctypes.Structure):
        _fields_ = [
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        ]

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    from_sddl = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
    from_sddl.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD),
    ]
    from_sddl.restype = wintypes.BOOL
    sd = ctypes.c_void_p()
    sd_size = wintypes.DWORD()
    if not from_sddl(
        _DIR_SDDL if directory else _FILE_SDDL,
        1, ctypes.byref(sd), ctypes.byref(sd_size)
    ):
        raise LocalConsoleRequired("SECURE_SECURITY_DESCRIPTOR_FAILED")
    sa = SecurityAttributes(ctypes.sizeof(SecurityAttributes), sd, 0)
    try:
        if directory:
            create_dir = kernel.CreateDirectoryW
            create_dir.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(SecurityAttributes)]
            create_dir.restype = wintypes.BOOL
            created = bool(create_dir(str(path), ctypes.byref(sa)))
            if not created:
                if ctypes.get_last_error() != 183:  # ERROR_ALREADY_EXISTS
                    raise LocalConsoleRequired("SECURE_DIRECTORY_CREATE_FAILED")
        else:
            create_file = kernel.CreateFileW
            create_file.argtypes = [
                wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                ctypes.POINTER(SecurityAttributes), wintypes.DWORD,
                wintypes.DWORD, wintypes.HANDLE,
            ]
            create_file.restype = wintypes.HANDLE
            # CREATE_NEW, GENERIC_READ|WRITE, FILE_FLAG_OPEN_REPARSE_POINT.
            handle = create_file(
                str(path), 0xC0000000, 0, ctypes.byref(sa), 1,
                0x80 | 0x00200000, None,
            )
            if handle == ctypes.c_void_p(-1).value:
                if ctypes.get_last_error() != 80:  # ERROR_FILE_EXISTS
                    raise LocalConsoleRequired("SECURE_AUTH_FILE_CREATE_FAILED")
            else:
                close = kernel.CloseHandle
                close.argtypes = [wintypes.HANDLE]
                close.restype = wintypes.BOOL
                if not close(handle):
                    raise LocalConsoleRequired("AUTH_FILE_HANDLE_CLOSE_FAILED")
    finally:
        local_free = kernel.LocalFree
        local_free.argtypes = [ctypes.c_void_p]
        local_free.restype = ctypes.c_void_p
        local_free(sd)


def _ps(script: str) -> None:
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive",
         "-EncodedCommand", encoded],
        stdin=subprocess.DEVNULL, capture_output=True, text=True,
        timeout=30, check=False,
    )
    if proc.returncode != 0 or "ACL_VERIFIED" not in proc.stdout:
        # Never disclose caller-controlled paths, secrets or PowerShell details.
        raise LocalConsoleRequired("AUTH_STORE_ACL_UNVERIFIED")


def _verify_acl(path: Path, *, allow_inherited: bool = False) -> None:
    """Validate trusted owner AND exactly one ACE per mandatory SID."""
    quoted = str(path).replace("'", "''")
    script = """
$ErrorActionPreference = 'Stop'
$p = '%s'
$info = Get-Acl -LiteralPath $p
$owner = $info.Owner
try {
  $ownerSid = (New-Object System.Security.Principal.NTAccount($owner)).Translate(
    [System.Security.Principal.SecurityIdentifier]).Value
} catch {
  $ownerSid = $owner
}
$required = @('S-1-5-18','S-1-5-32-544')
if ($ownerSid -notin $required) { throw 'Untrusted owner' }
$seen = @()
$access = @($info.Access)
if ($access.Count -ne 2) { throw 'Unexpected grant count' }
foreach ($rule in $access) {
  $sid = $rule.IdentityReference.Translate(
    [System.Security.Principal.SecurityIdentifier]).Value
  if ($sid -notin $required -or $seen -contains $sid -or
      ($rule.IsInherited -and -not %s) -or
      $rule.AccessControlType -ne 'Allow' -or
      (($rule.FileSystemRights -band
        [System.Security.AccessControl.FileSystemRights]::FullControl) -ne
        [System.Security.AccessControl.FileSystemRights]::FullControl)) {
    throw 'Untrusted ACE'
  }
  $seen += $sid
}
if ((@($seen | Sort-Object) -join ',') -ne
    (@($required | Sort-Object) -join ',')) {
  throw 'Missing required identity'
}
Write-Output 'ACL_VERIFIED'
""" % (quoted, "$true" if allow_inherited else "$false")
    _ps(script)


def _create_private_dir(path: Path) -> None:
    _no_reparse(path.parent)
    _no_reparse(path)
    if not path.exists():
        _secure_win32_create(path, directory=True)
    _no_reparse(path)
    if not path.is_dir():
        raise LocalConsoleRequired("AUTH_DIR_INVALID")
    _verify_acl(path)


def _database_path(*, initialize: bool) -> Path:
    require_local_windows_admin_console()
    base = _programdata() / "DigitalCrownQueueCore"
    # status/enroll/recover must never create a previously absent store.
    _no_reparse(base.parent)
    _no_reparse(base)
    if initialize:
        _create_private_dir(base)
    elif base.exists():
        if not base.is_dir():
            raise LocalConsoleRequired("AUTH_DIR_INVALID")
        _verify_acl(base)
    else:
        return base / "local_auth.sqlite"
    database = base / "local_auth.sqlite"
    _no_reparse(database)
    if initialize and not database.exists():
        _secure_win32_create(database, directory=False)
    _no_reparse(database)
    if database.exists():
        if not database.is_file():
            raise LocalConsoleRequired("AUTH_FILE_INVALID")
        _verify_acl(database, allow_inherited=True)
    return database


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Queue Core first Admin — LOCAL ELEVATED WINDOWS CONSOLE ONLY"
    )
    parser.add_argument("action", choices=("issue", "enroll", "recover", "status"))
    args = parser.parse_args(argv)

    try:
        path = _database_path(initialize=args.action == "issue")
        store = LocalIdentityStore(path)
        if args.action == "issue":
            token = store.begin_bootstrap()
            print("One-time bootstrap code (expires in 10 minutes):")
            print(token)
            print("Run 'enroll' at the same physical server console.")
        elif args.action == "enroll":
            challenge = getpass.getpass("Bootstrap code: ")
            username = input("New local Admin username (3-64 ASCII chars): ")
            pw = getpass.getpass("New password (14-128 chars): ")
            confirm = getpass.getpass("Repeat new password: ")
            if pw != confirm:
                raise LocalIdentityError("PASSWORD_CONFIRMATION_FAILED")
            recovery = store.enroll_first_admin(challenge, username, pw)
            print("Store this recovery secret OFFLINE, outside the server and backups.")
            print("It will not be displayed again:")
            print(recovery)
        elif args.action == "recover":
            recovery = getpass.getpass("Offline recovery secret: ")
            pw = getpass.getpass("New password: ")
            confirm = getpass.getpass("Repeat new password: ")
            if pw != confirm:
                raise LocalIdentityError("PASSWORD_CONFIRMATION_FAILED")
            replacement = store.recover_admin(recovery, pw)
            print("Previous sessions and recovery secret revoked.")
            print("Store this NEW secret OFFLINE; it will not be displayed again:")
            print(replacement)
        elif args.action == "status":
            print("NOT_INITIALIZED" if not path.exists() else
                  ("INITIALIZED" if store.is_initialized() else "NOT_INITIALIZED"))
        return 0
    except (LocalIdentityError, LocalConsoleRequired) as error:
        print("Queue Core local administration refused: " + str(error),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
