"""Privileged offline Windows console entry point for Queue Core's first admin.

The CLI deliberately has NO --db or LAN option. It always targets a dedicated,
ACL-locked ProgramData folder discovered from HKLM rather than user-controlled
environment variables. No clinical database, Firebase or network access.
DO NOT run this tool as part of 08.2-A automated tests or on a real cabinet.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import os
from pathlib import Path
import subprocess
import sys

from .local_auth import LocalIdentityError, LocalIdentityStore
from .windows_console import (
    LocalConsoleRequired, require_local_windows_admin_console,
)


def _programdata() -> Path:
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    ) as key:
        folder, _ = winreg.QueryValueEx(key, "Common AppData")
    return Path(folder)


def _no_reparse(path: Path) -> None:
    if path.exists() and path.stat(follow_symlinks=False).st_file_attributes & 0x400:
        raise LocalConsoleRequired("REPARSE_POINT_FORBIDDEN")


def _ps(script: str) -> None:
    command = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive",
         "-EncodedCommand", command],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        check=False,
    )
    if result.returncode != 0 or "ACL_VERIFIED" not in result.stdout:
        # Do not disclose potentially sensitive machine path details.
        raise LocalConsoleRequired("LOCAL_AUTH_ACL_UNVERIFIED")


def _verify_acl(path: Path, *, allow_inherited: bool = False) -> None:
    quoted = str(path).replace("'", "''")
    script = """
$ErrorActionPreference = 'Stop'
$p = '%s'
$a = (Get-Acl -LiteralPath $p).Access
$required = @('S-1-5-18','S-1-5-32-544')
if ($a.Count -ne 2) { throw 'ACL has unexpected grants' }
foreach ($rule in $a) {
  $sid = $rule.IdentityReference.Translate(
    [System.Security.Principal.SecurityIdentifier]).Value
  if ($sid -notin $required -or ( $rule.IsInherited -and -not %s ) -or
      $rule.AccessControlType -ne 'Allow' -or
      (($rule.FileSystemRights -band
        [System.Security.AccessControl.FileSystemRights]::FullControl) -ne
        [System.Security.AccessControl.FileSystemRights]::FullControl)) {
    throw 'ACL not private'
  }
}
Write-Output 'ACL_VERIFIED'
""" % (quoted, "$true" if allow_inherited else "$false")
    _ps(script)


def _create_private_dir(path: Path) -> None:
    parent = path.parent
    _no_reparse(parent)
    _no_reparse(path)
    if path.exists():
        _verify_acl(path)
        return
    path.mkdir(exist_ok=False)
    quoted = str(path).replace("'", "''")
    script = """
$ErrorActionPreference = 'Stop'
$p = '%s'
$acl = New-Object System.Security.AccessControl.DirectorySecurity
$acl.SetAccessRuleProtection($true,$false)
foreach ($identity in @('S-1-5-18','S-1-5-32-544')) {
  $sid = New-Object System.Security.Principal.SecurityIdentifier($identity)
  $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $sid, 'FullControl', 'ContainerInherit,ObjectInherit','None','Allow')
  $acl.AddAccessRule($rule)
}
Set-Acl -LiteralPath $p -AclObject $acl
Write-Output 'ACL_VERIFIED'
""" % quoted
    _ps(script)
    _verify_acl(path)


def _database_path() -> Path:
    require_local_windows_admin_console()
    base = _programdata() / "DigitalCrownQueueCore"
    _create_private_dir(base)
    database = base / "local_auth.sqlite"
    _no_reparse(database)
    if database.exists():
        _verify_acl(database, allow_inherited=True)
    return database


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Queue Core first Admin — LOCAL ELEVATED WINDOWS CONSOLE ONLY"
    )
    parser.add_argument("action", choices=("issue", "enroll", "recover", "status"))
    args = parser.parse_args(argv)

    try:
        path = _database_path()
        store = LocalIdentityStore(path)
        if args.action == "issue":
            token = store.begin_bootstrap()
            # Display once on a physically local admin console only.
            print("One-time bootstrap code (expires in 10 minutes):")
            print(token)
            print("Run 'enroll' at this same local server console.")
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
        # Never log supplied challenge, password, recovery secret, or session.
        print("Queue Core local administration refused: " + str(error),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
